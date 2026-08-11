#!/usr/bin/env python3
"""Download the fixed ERA5-Land weather extract used by the event study.

The annual NetCDF files cover Limburg plus a small cross-border margin.  They
are deliberately kept as a rectangular grid: catchment centroids do not exist
yet, so selecting point series now would silently pre-empt the later cohort and
spatial-assignment checks.
"""

import argparse
import calendar
import hashlib
from pathlib import Path

import pandas as pd

DATASET = "reanalysis-era5-land"
VARIABLES = ["2m_temperature", "2m_dewpoint_temperature", "surface_pressure"]
AREA = [52.0, 5.0, 50.5, 6.7]  # north, west, south, east
HOURS = [f"{hour:02d}:00" for hour in range(24)]


def request_for_year(year):
    """Return one complete calendar-year request for the fixed extract."""
    return {
        "variable": VARIABLES,
        "year": [str(year)],
        "month": [f"{month:02d}" for month in range(1, 13)],
        "day": [f"{day:02d}" for day in range(1, 32)],
        "time": HOURS,
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": AREA,
    }


def sha256(path):
    """Hash a downloaded source file without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_year(client, year, raw_dir):
    """Download one year atomically and leave an existing file untouched."""
    target = raw_dir / f"era5_land_limburg_{year}.nc"
    if target.exists() and target.stat().st_size:
        print(f"keep {target}")
        return target

    partial = target.with_suffix(".nc.part")
    if partial.exists():
        partial.unlink()
    print(f"download {year} -> {target}")
    client.retrieve(DATASET, request_for_year(year), str(partial))
    partial.replace(target)
    return target


def write_manifest(paths, raw_dir):
    """Record the exact local files; variable/unit QA follows after download."""
    rows = []
    for path in paths:
        year = int(path.stem.rsplit("_", 1)[1])
        rows.append(
            {
                "dataset": DATASET,
                "year": year,
                "expected_hours": 24 * (366 if calendar.isleap(year) else 365),
                "north": AREA[0],
                "west": AREA[1],
                "south": AREA[2],
                "east": AREA[3],
                "variables": ";".join(VARIABLES),
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    pd.DataFrame(rows).to_csv(raw_dir / "manifest.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2001)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.start_year > args.end_year:
        parser.error("--start-year must not exceed --end-year")

    years = range(args.start_year, args.end_year + 1)
    if args.dry_run:
        for year in years:
            print(year, request_for_year(year))
        return

    try:
        import cdsapi
    except ImportError as exc:
        raise SystemExit(
            "cdsapi is missing; update the conda environment from environment.yml"
        ) from exc

    raw_dir = Path("data/raw/era5_land")
    raw_dir.mkdir(parents=True, exist_ok=True)
    try:
        client = cdsapi.Client()
    except Exception as exc:
        raise SystemExit(
            "CDS credentials are missing. Log in at "
            "https://cds.climate.copernicus.eu/how-to-api, accept the "
            "ERA5-Land licence, and copy the displayed url/key lines to "
            "~/.cdsapirc."
        ) from exc
    paths = [fetch_year(client, year, raw_dir) for year in years]
    write_manifest(paths, raw_dir)
    print(f"wrote {len(paths)} files and {raw_dir / 'manifest.csv'}")


if __name__ == "__main__":
    main()
