"""Fetch the LANUK NRW verified discharge archive for the Rur and Niers catchments.

North Rhine-Westphalia publishes its full verified discharge archive as open
data, no key and no registration, under Datenlizenz Deutschland Zero 2.0:

    https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/oberflaechengewaesser/hydro/q/

This matters because the Waterschap Limburg endpoint the chapter has been using
is a rolling two-year window, and two years contains no event approaching July
2021. The NRW archive is **15-minute resolution back to 1950** and covers the
German half of the study area, including the Wurm — the donor catchment.

Two catchments are pulled by default:

- ``Rureinzugsgebiet`` — the Rur/Roer and the Wurm/Worm. 30 gauges, including
  Randerath and Stah (already in the chapter's set) and Herzogenrath 1 and 2,
  Honsdorf, Haaren and Kalkofen on the Wurm itself.
- ``Niers-u-Schwalmeinzugsgebiet`` — covers ``niers_kessel`` and ``swalm_grens``.

Together about 114 MB of zipped CSV, cached under ``data/raw/discharge/lanuk/``.

**Worm at Rimburg is not here.** It is the Dutch border gauge operated by WVER,
and its public feed is a rolling 10-day window. Herzogenrath 2 sits immediately
upstream and Randerath downstream, so the Wurm is covered either way.

**Gauges failed during the 2021 flood.** Randerath's record stops on
2021-07-01 and Herzogenrath 2 has no July 2021 values. That is survivorship in
the gauge network, not a fetch error, and the coverage report prints it rather
than hiding it.

Format quirks, all confirmed against the files rather than assumed: semicolon
separated, **UTF-8** encoded despite looking latin-1 at a glance, ``NA`` for
missing, and timestamps carrying mixed UTC offsets across the DST boundary.
Reading them as latin-1 silently mangles the station names that become the
gauge labels, so the encoding is load-bearing.
"""

from __future__ import annotations

import argparse
import io
import re
import zipfile
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

BASE = "https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/oberflaechengewaesser/hydro/q"
RAW_DIR = Path("data/raw/discharge/lanuk")
SERIES_PATH = Path("data/interim/lanuk_discharge_hourly.csv")
INVENTORY_PATH = Path("data/interim/lanuk_stations.csv")

CATCHMENTS = ("Rureinzugsgebiet", "Niers-u-Schwalmeinzugsgebiet")


# German transliteration, applied before slugifying so umlauts survive as
# letters rather than becoming underscores. This matches the convention LANUK
# itself uses in the archive filenames (Jülich -> Juelich, Gemünd -> Gemuend).
UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def slugify(name):
    """Station name to a column label matching the repo's existing convention."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower().translate(UMLAUTS)).strip("_")


def decade_files(catchment):
    """List the decade archives published for one catchment."""
    with urlopen(f"{BASE}/index.json", timeout=120) as response:
        index = pd.read_json(io.BytesIO(response.read()))
    for dataset in index["datasets"]:
        if dataset["name"].startswith(catchment):
            return [f["name"] for f in dataset["files"]]
    raise SystemExit(f"catchment {catchment!r} not found in the NRW index")


def download(filename):
    """Fetch one decade archive, cached."""
    path = RAW_DIR / filename
    if path.exists():
        return path
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {filename}")
    with urlopen(f"{BASE}/{filename}", timeout=900) as response:
        path.write_bytes(response.read())
    return path


def read_member(archive, member):
    """One gauge-decade CSV to an hourly mean series."""
    frame = pd.read_csv(
        io.BytesIO(archive.read(member)),
        sep=";",
        encoding="utf-8",
        names=["station_name", "station_no", "timestamp", "value"],
        header=0,
        dtype={"station_no": str},
    )
    # 'NA' strings and the occasional blank; never interpolated.
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="mixed", utc=True)
    frame = frame.dropna(subset=["value", "timestamp"])
    if frame.empty:
        return None, None
    name = str(frame["station_name"].iloc[0])
    hourly = frame.set_index("timestamp")["value"].sort_index().resample("h").mean()
    return name, hourly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catchments", default=",".join(CATCHMENTS))
    parser.add_argument("--from-year", type=int, default=0, help="Skip decades before this year")
    args = parser.parse_args()

    collected: dict[str, list[pd.Series]] = {}
    names: dict[str, str] = {}
    for catchment in args.catchments.split(","):
        catchment = catchment.strip()
        if not catchment:
            continue
        print(f"{catchment}:")
        for filename in decade_files(catchment):
            decade = re.search(r"-Q_(\d{4})-", filename)
            if decade and int(decade.group(1)) + 9 < args.from_year:
                continue
            path = download(filename)
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if not member.endswith(".csv"):
                        continue
                    name, hourly = read_member(archive, member)
                    if hourly is None:
                        continue
                    label = slugify(name)
                    collected.setdefault(label, []).append(hourly)
                    names[label] = name
            span = decade.group(0).strip("-Q_") if decade else "?"
            print(f"    {span}s  {len(collected)} gauges so far")

    if not collected:
        raise SystemExit("no series parsed")

    # One series per gauge, decades concatenated. Duplicate hours can appear at
    # decade boundaries; keep the first.
    series = {}
    for label, parts in collected.items():
        joined = pd.concat(parts).sort_index()
        series[label] = joined[~joined.index.duplicated(keep="first")]

    combined = pd.DataFrame(series).sort_index()
    SERIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(SERIES_PATH, index_label="timestamp_utc")

    rows = []
    for label, values in series.items():
        observed = values.dropna()
        july2021 = observed[(observed.index >= "2021-07-10") & (observed.index < "2021-07-25")]
        rows.append(
            {
                "gauge": label,
                "station_name": names[label],
                "start": observed.index.min(),
                "end": observed.index.max(),
                "n_hours": len(observed),
                "years": round((observed.index.max() - observed.index.min()).days / 365.25, 1),
                "median_q": observed.median(),
                "max_q": observed.max(),
                "july_2021_hours": len(july2021),
                "july_2021_peak": july2021.max() if len(july2021) else None,
            }
        )
    inventory = pd.DataFrame(rows).sort_values("years", ascending=False)
    inventory.to_csv(INVENTORY_PATH, index=False)

    print(f"\nwrote {SERIES_PATH} ({len(combined):,} hours, {combined.shape[1]} gauges)")
    print(f"wrote {INVENTORY_PATH}")
    print(f"\nrecord spans {combined.index.min():%Y-%m-%d} to {combined.index.max():%Y-%m-%d}")
    covered = inventory[inventory["july_2021_hours"] > 0]
    print(f"gauges with July 2021 coverage: {len(covered)} of {len(inventory)}")
    if len(covered):
        top = covered.nlargest(8, "july_2021_peak")
        print("\nJuly 2021 peaks:")
        for row in top.itertuples():
            ratio = row.july_2021_peak / row.median_q if row.median_q else float("nan")
            print(
                f"  {row.station_name[:28]:30} {row.july_2021_peak:8.1f} m3/s  "
                f"{ratio:6.0f}x median  ({row.years:.0f} yr record)"
            )
    missing = inventory[(inventory["july_2021_hours"] == 0) & (inventory["end"] < "2021-08-01")]
    if len(missing):
        print("\ngauges whose record ends at or before the flood (failed, not missing):")
        for row in missing.itertuples():
            print(f"  {row.station_name[:28]:30} ends {row.end:%Y-%m-%d}")


if __name__ == "__main__":
    main()
