"""Fetch Maas main-stem discharge from the Rijkswaterstaat Waterwebservices API.

Rijkswaterstaat serves validated 10-minute discharge for the Maas main stem back
to roughly 2000, under CC0. That includes July 2021: Borgharen peaks at
**3,284 m3/s on 2021-07-15 21:10 UTC**, against 2,017 m3/s for the largest event
in the chapter's two-year Waterschap window.

    https://ddapi20-waterwebservices.rijkswaterstaat.nl

The old ``waterwebservices.rijkswaterstaat.nl`` host now 301s to a project page;
this is the current endpoint.

Two behaviours of the endpoint the code has to absorb, both found by running it
rather than by reading documentation. A year of 10-minute data is a ~16 MB
chunked response and the connection drops often enough that requests must be
retried — an unretried timeout killed a 50-minute pull on its 78th request. And
the feed runs **ahead of the present**, returning expected values a couple of
days into the future, which are filtered out rather than stored as observations.

**Scope, and what this source is not.** RWS carries the main stem, not the
tributaries. The chapter's Dutch tributary gauges — Eyserbeek, Gulp, Selzerbeek,
Voer, Vlootbeek, Geul at Hommerich and Meerssen, Geleenbeek, Worm at Rimburg —
do not appear anywhere in the RWS catalogue of 2,635 locations. EStreams
attributes them to ``NL_RWS``, but that attribution does not match what RWS
publishes; Waterschap Limburg is the holder. See ``docs/data-requests.md``.

The one South Limburg tributary gauge RWS does carry is **Geul at Cottessen**,
and only as a rolling real-time feed: every request before roughly late 2025
returns HTTP 204, and the values that do return are flagged ``Ongecontroleerd``.
It is fetched anyway, because it is the gauge that returns nothing at all
through the Waterschap endpoint, so this is a route to it going forward.

So this script gives the chapter scale context and a validated flood hydrograph,
not tributary data. The tributaries need the request in ``docs/data-requests.md``.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

BASE = "https://ddapi20-waterwebservices.rijkswaterstaat.nl"
CATALOGUE_URL = f"{BASE}/METADATASERVICES/OphalenCatalogus"
OBSERVATIONS_URL = f"{BASE}/ONLINEWAARNEMINGENSERVICES/OphalenWaarnemingen"

RAW_DIR = Path("data/raw/discharge/rws")
CATALOGUE_PATH = RAW_DIR / "rws_catalogue.json"
SERIES_PATH = Path("data/interim/rws_maas_hourly.csv")
INVENTORY_PATH = Path("data/interim/rws_stations.csv")

# Maas main stem plus the one Geul gauge RWS carries. Labels follow the repo's
# existing `river_place` convention so these join to the Waterschap columns.
STATIONS = {
    "eijsden.grens": "maas_eijsden_grens",
    "maastricht.sintpieter": "maas_sint_pieter",
    "maastricht.borgharen.maas.beneden": "maas_borgharen",
    "venlo": "maas_venlo",
    "megen.maas": "maas_megen",
    "lith": "maas_lith",
    "epen.geul.cottessen": "geul_cottessen",
}

# The API returns this in place of a missing value rather than omitting the row.
MISSING = 999999999.0


def post(url, payload, timeout=600, retries=4):
    """POST one JSON request. Returns None on 204 (no data for the period).

    Retries transient network failures with backoff. A year of 10-minute data is
    a ~16 MB chunked response, and the endpoint drops one often enough that a
    single unretried timeout will kill an hour-long pull.
    """
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status == 204:
                    return None
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as exc:
            if exc.code == 204:
                return None
            if attempt == retries or exc.code < 500:
                raise
        except (TimeoutError, URLError, ConnectionError, json.JSONDecodeError) as exc:
            if attempt == retries:
                raise
            print(f"    retry {attempt}/{retries - 1} after {type(exc).__name__}")
        time.sleep(5 * attempt)
    return None


def catalogue(refresh=False):
    """Station metadata, cached. 6.5 MB, so fetched once."""
    if CATALOGUE_PATH.exists() and not refresh:
        return json.loads(CATALOGUE_PATH.read_text())
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("fetching RWS catalogue")
    payload = post(
        CATALOGUE_URL,
        {"CatalogusFilter": {"Grootheden": True, "Parameters": True, "Compartimenten": True}},
    )
    CATALOGUE_PATH.write_text(json.dumps(payload))
    return payload


def coordinates(cat):
    """Map station code to (lon, lat). The API wants these as X and Y."""
    frame = pd.DataFrame(cat["LocatieLijst"])
    frame = frame[frame["Code"].isin(STATIONS)]
    return {
        row.Code: (float(row.Lon), float(row.Lat))
        for row in frame.itertuples()
        if pd.notna(row.Lon) and pd.notna(row.Lat)
    }


def fetch_year(code, point, year, refresh=False):
    """One station-year of 10-minute discharge, cached as raw JSON."""
    path = RAW_DIR / f"{code}_{year}.json"
    if path.exists() and not refresh:
        text = path.read_text()
        return json.loads(text) if text.strip() else None
    payload = {
        "Locatie": {"Code": code, "X": point[0], "Y": point[1]},
        "AquoPlusWaarnemingMetadata": {
            "AquoMetadata": {"Compartiment": {"Code": "OW"}, "Grootheid": {"Code": "Q"}}
        },
        "Periode": {
            "Begindatumtijd": f"{year}-01-01T00:00:00.000+00:00",
            "Einddatumtijd": f"{year + 1}-01-01T00:00:00.000+00:00",
        },
    }
    result = post(OBSERVATIONS_URL, payload)
    path.write_text(json.dumps(result) if result else "")
    time.sleep(0.5)
    return result


def to_series(payload):
    """Observation payload to a 10-minute series, sentinel values dropped."""
    if not payload or not payload.get("WaarnemingenLijst"):
        return None, set()
    stamps, values, statuses = [], [], set()
    for block in payload["WaarnemingenLijst"]:
        for row in block.get("MetingenLijst", []):
            value = row.get("Meetwaarde", {}).get("Waarde_Numeriek")
            if value is None or value >= MISSING:
                continue
            stamps.append(row["Tijdstip"])
            values.append(value)
            statuses.add(row.get("WaarnemingMetadata", {}).get("Statuswaarde"))
    if not stamps:
        return None, statuses
    index = pd.to_datetime(pd.Series(stamps), format="mixed", utc=True)
    series = pd.Series(values, index=index).sort_index()
    # The feed runs ahead of the present: expected/forecast values appear with
    # timestamps up to a couple of days out. They are not observations.
    return series[series.index <= pd.Timestamp.now(tz="UTC")], statuses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-year", type=int, default=2000)
    parser.add_argument("--to-year", type=int, default=date.today().year)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    points = coordinates(catalogue(refresh=args.refresh))
    missing = [c for c in STATIONS if c not in points]
    if missing:
        print(f"not in catalogue, skipping: {', '.join(missing)}")

    series, status_by_gauge = {}, {}
    for code, label in STATIONS.items():
        if code not in points:
            continue
        parts, statuses, empty = [], set(), 0
        for year in range(args.from_year, args.to_year + 1):
            payload = fetch_year(code, points[code], year, refresh=args.refresh)
            part, found = to_series(payload)
            statuses |= {s for s in found if s}
            if part is None:
                empty += 1
                continue
            parts.append(part)
        if not parts:
            print(f"  {label:22} no data in {args.from_year}-{args.to_year}")
            continue
        joined = pd.concat(parts).sort_index()
        joined = joined[~joined.index.duplicated(keep="first")]
        series[label] = joined.resample("h").mean()
        status_by_gauge[label] = statuses
        print(
            f"  {label:22} {len(joined):9,} readings  "
            f"{joined.index.min():%Y-%m-%d} to {joined.index.max():%Y-%m-%d}  "
            f"({empty} empty years)  {'/'.join(sorted(statuses))}"
        )

    if not series:
        raise SystemExit("no series fetched")

    combined = pd.DataFrame(series).sort_index()
    SERIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(SERIES_PATH, index_label="timestamp_utc")

    rows = []
    for label, values in series.items():
        observed = values.dropna()
        july = observed[(observed.index >= "2021-07-10") & (observed.index < "2021-07-25")]
        rows.append(
            {
                "gauge": label,
                "start": observed.index.min(),
                "end": observed.index.max(),
                "n_hours": len(observed),
                "median_q": observed.median(),
                "max_q": observed.max(),
                "july_2021_peak": july.max() if len(july) else None,
                "status": "/".join(sorted(status_by_gauge.get(label, {"?"}))),
            }
        )
    pd.DataFrame(rows).to_csv(INVENTORY_PATH, index=False)

    print(f"\nwrote {SERIES_PATH} ({len(combined):,} hours, {combined.shape[1]} gauges)")
    print(f"wrote {INVENTORY_PATH}")
    covered = [r for r in rows if r["july_2021_peak"]]
    if covered:
        print("\nJuly 2021 peaks:")
        for row in sorted(covered, key=lambda r: -r["july_2021_peak"]):
            print(
                f"  {row['gauge']:22} {row['july_2021_peak']:8.0f} m3/s   "
                f"record max {row['max_q']:8.0f}   median {row['median_q']:7.1f}"
            )


if __name__ == "__main__":
    main()
