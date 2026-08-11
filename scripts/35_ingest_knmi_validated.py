#!/usr/bin/env python3
"""Download and normalize the validated KNMI hourly sensitivity series."""

import hashlib
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

STATIONS = {377: "Ell", 380: "Maastricht Airport", 391: "Arcen"}
DECADES = ["2001-2010", "2011-2020", "2021-2030"]
BASE_URL = "https://cdn.knmi.nl/knmi/map/page/klimatologie/gegevens/uurgegevens"
RAW_DIR = Path("data/raw/knmi/validated_hourly")
OUTPUT = Path("data/interim/knmi_validated_hourly.parquet")
MANIFEST = RAW_DIR / "manifest.csv"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(station, decade):
    """Cache one source ZIP without replacing a completed download."""
    name = f"uurgeg_{station}_{decade}.zip"
    path = RAW_DIR / name
    if path.exists() and path.stat().st_size:
        print(f"keep {path}")
        return path

    url = f"{BASE_URL}/{name}"
    partial = path.with_suffix(".zip.part")
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with partial.open("wb") as target:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    target.write(chunk)
    partial.replace(path)
    print(f"downloaded {path}")
    return path


def read_archive(path):
    """Read the four retained fields from one documented KNMI text export."""
    with zipfile.ZipFile(path) as archive:
        member = archive.namelist()[0]
        text = archive.read(member).decode("latin-1")

    lines = text.splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith("# STN,"))
    lines[header_index] = lines[header_index].removeprefix("# ")
    frame = pd.read_csv(io.StringIO("\n".join(lines[header_index:])), skipinitialspace=True)
    frame.columns = frame.columns.str.strip()

    # KNMI HH labels the end of the UTC hour: HH=1 is 01:00 and HH=24 is
    # midnight on the following date. This differs from the old loader's
    # interval-start convention and is kept explicit here.
    base = pd.to_datetime(frame["YYYYMMDD"].astype(str), format="%Y%m%d", errors="coerce")
    timestamp = (base + pd.to_timedelta(frame["HH"], unit="h")).dt.tz_localize("UTC")
    return pd.DataFrame(
        {
            "knmi_station": frame["STN"].map(lambda value: f"06{int(value):03d}"),
            "timestamp_utc": timestamp,
            "knmi_temperature_c": pd.to_numeric(frame["T"], errors="coerce") * 0.1,
            "knmi_relative_humidity_pct": pd.to_numeric(frame["U"], errors="coerce"),
            "knmi_pressure_msl_hpa": pd.to_numeric(frame["P"], errors="coerce") * 0.1,
            "source_file": path.name,
        }
    )


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths = [download(station, decade) for station in STATIONS for decade in DECADES]

    weather = pd.concat([read_archive(path) for path in paths], ignore_index=True)
    weather = weather.loc[weather.timestamp_utc.between("2001-01-01", "2025-12-31 23:59:59")]
    weather = weather.drop_duplicates(["knmi_station", "timestamp_utc"], keep="last")
    weather = weather.sort_values(["knmi_station", "timestamp_utc"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    weather.to_parquet(OUTPUT, index=False)

    pd.DataFrame(
        [
            {
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "official_url": f"{BASE_URL}/{path.name}",
            }
            for path in paths
        ]
    ).to_csv(MANIFEST, index=False)
    print(f"wrote {OUTPUT} ({len(weather):,} rows) and {MANIFEST}")


if __name__ == "__main__":
    main()
