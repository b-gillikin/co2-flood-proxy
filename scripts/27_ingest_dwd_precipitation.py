"""Fetch DWD hourly station precipitation for a point-rainfall sensitivity.

DWD publishes hourly station precipitation as open data with no key and no
registration, and there are roughly ninety stations inside the study box:

    https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/

The chapter's primary exposure is hourly 1-km RADOLAN rainfall averaged over
verified catchment polygons. These station series do not satisfy that gate;
they are retained to check whether conclusions depend on the radar exposure.

Each station is published in two parts, both fetched here: a `_hist` archive
ending at some past date, and an `_akt` archive covering roughly the last
eighteen months. Filenames for the historical part embed the record's own date
range, so the directory index is read rather than guessed.

Format, confirmed against a downloaded file rather than assumed: semicolon
separated with padded fields, latin-1, `MESS_DATUM` as `YYYYMMDDHH` in UTC,
precipitation in `R1` as mm, and **-999 for missing**, which must be blanked
rather than summed.

Do not substitute this output for `radolan_catchment_hourly.csv`.
"""

from __future__ import annotations

import argparse
import io
import re
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pandas as pd

BASE = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
    "hourly/precipitation"
)
STATION_LIST = f"{BASE}/historical/RR_Stundenwerte_Beschreibung_Stationen.txt"
RAW_DIR = Path("data/raw/precipitation/dwd")
SERIES_PATH = Path("data/interim/dwd_precip_hourly.csv")
INVENTORY_PATH = Path("data/interim/dwd_stations.csv")

# Study box: South Limburg and the Dutch-German border catchments, south to
# Monschau in the upper Rur and north past the Niers.
BBOX = (50.4, 52.0, 5.2, 7.0)  # lat_min, lat_max, lon_min, lon_max

MISSING = -999


def fetch(url, timeout=300, retries=3):
    """GET one URL as bytes, retrying transient failures."""
    for attempt in range(1, retries + 1):
        try:
            with urlopen(url, timeout=timeout) as response:
                return response.read()
        except (TimeoutError, URLError, ConnectionError) as exc:
            if attempt == retries:
                raise
            print(f"    retry {attempt} after {type(exc).__name__}")
        except HTTPError:
            raise
    return None


def stations_in_box(bbox):
    """Parse the fixed-width station description and keep those inside the box."""
    text = fetch(STATION_LIST).decode("latin-1")
    lat_min, lat_max, lon_min, lon_max = bbox
    rows = []
    for line in text.splitlines()[2:]:
        # id, from, to, height, lat, lon, name, state — name may contain spaces,
        # so the split is anchored on the numeric prefix.
        match = re.match(
            r"(\d{5})\s+(\d{8})\s+(\d{8})\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+(.+?)\s{2,}(.+?)\s*$",
            line,
        )
        if not match:
            continue
        station, start, end, height, lat, lon, name, state = match.groups()
        lat, lon = float(lat), float(lon)
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            rows.append(
                {
                    "station_id": station,
                    "name": name.strip(),
                    "state": state.strip(),
                    "latitude": lat,
                    "longitude": lon,
                    "elevation_m": int(height),
                    "listed_start": start,
                    "listed_end": end,
                }
            )
    return pd.DataFrame(rows)


def archive_index(kind):
    """Map station id to the archive filenames published for it."""
    html = fetch(f"{BASE}/{kind}/").decode("utf-8", errors="replace")
    index: dict[str, list[str]] = {}
    for name in re.findall(r'href="(stundenwerte_RR_[^"]+\.zip)"', html):
        station = name.split("_")[2]
        index.setdefault(station, []).append(name)
    return index


def read_archive(blob):
    """One DWD zip to a precipitation series, missing values blanked."""
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        members = [n for n in archive.namelist() if n.startswith("produkt")]
        if not members:
            return None
        frame = pd.read_csv(
            io.BytesIO(archive.read(members[0])),
            sep=";",
            encoding="latin-1",
            skipinitialspace=True,
        )
    frame.columns = [c.strip() for c in frame.columns]
    if "R1" not in frame or "MESS_DATUM" not in frame:
        return None
    stamp = pd.to_datetime(frame["MESS_DATUM"], format="%Y%m%d%H", utc=True)
    values = pd.to_numeric(frame["R1"], errors="coerce")
    # -999 is the missing marker. Summed as a number it would silently destroy
    # any rainfall total it entered.
    values = values.where(values > MISSING)
    return pd.Series(values.values, index=stamp).sort_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Re-download cached archives")
    parser.add_argument("--from-year", type=int, default=0, help="Trim output to this year onward")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stations = stations_in_box(BBOX)
    print(f"stations inside {BBOX}: {len(stations)}")

    indexes = {kind: archive_index(kind) for kind in ("historical", "recent")}

    series, kept = {}, []
    for row in stations.itertuples(index=False):
        parts = []
        for kind, index in indexes.items():
            for name in index.get(row.station_id, []):
                path = RAW_DIR / name
                if not path.exists() or args.refresh:
                    try:
                        path.write_bytes(fetch(f"{BASE}/{kind}/{name}"))
                    except HTTPError as exc:
                        print(f"  {row.station_id} {name}: HTTP {exc.code}")
                        continue
                part = read_archive(path.read_bytes())
                if part is not None and len(part):
                    parts.append(part)
        if not parts:
            continue
        joined = pd.concat(parts).sort_index()
        joined = joined[~joined.index.duplicated(keep="last")]  # recent supersedes historical
        observed = joined.dropna()
        if observed.empty:
            continue
        label = f"dwd_{row.station_id}"
        series[label] = joined
        kept.append(
            {
                **row._asdict(),
                "gauge": label,
                "start": observed.index.min(),
                "end": observed.index.max(),
                "n_hours": len(observed),
                "years": round((observed.index.max() - observed.index.min()).days / 365.25, 1),
                "annual_mm": round(observed.sum() / max(len(observed) / 8766, 1e-9), 1),
            }
        )
        print(f"  {label} {row.name[:26]:28} {len(observed):8,} h  {observed.index.max():%Y-%m-%d}")

    if not series:
        raise SystemExit("no stations parsed")

    combined = pd.DataFrame(series).sort_index()
    if args.from_year:
        combined = combined[combined.index.year >= args.from_year]
    SERIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(SERIES_PATH, index_label="timestamp_utc")

    inventory = pd.DataFrame(kept).sort_values("years", ascending=False)
    inventory.to_csv(INVENTORY_PATH, index=False)

    print(f"\nwrote {SERIES_PATH} ({len(combined):,} hours, {combined.shape[1]} stations)")
    print(f"wrote {INVENTORY_PATH}")
    print(f"span {combined.index.min():%Y-%m-%d} to {combined.index.max():%Y-%m-%d}")

    # Sanity check: annual totals. South Limburg and the Eifel foreland run
    # roughly 700-1000 mm/yr, so anything far outside that is a unit or
    # missing-value error rather than a wet station.
    plausible = inventory[inventory["annual_mm"].between(400, 1600)]
    print(
        f"\nannual totals: median {inventory['annual_mm'].median():.0f} mm/yr, "
        f"{len(plausible)}/{len(inventory)} within a plausible 400-1600 mm/yr"
    )
    current = inventory[inventory["end"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta("60d")]
    print(f"stations current within 60 days: {len(current)}")
    flood = combined[(combined.index >= "2021-07-13") & (combined.index < "2021-07-16")]
    if len(flood):
        totals = flood.sum().sort_values(ascending=False)
        print(f"\n13-15 July 2021 totals, {totals.notna().sum()} reporting stations:")
        for label, value in totals.head(8).items():
            name = inventory.loc[inventory["gauge"] == label, "name"]
            print(f"  {label}  {name.iloc[0][:30]:32} {value:6.1f} mm")


if __name__ == "__main__":
    main()
