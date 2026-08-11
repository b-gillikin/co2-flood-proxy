#!/usr/bin/env python3
"""Download the fixed ERA5-Land weather extract used by the event study.

The monthly NetCDF files retain the rectangular Limburg grid because selecting
points before the catchment cohort is fixed would pre-empt the later
spatial-assignment check.
"""

import argparse
import calendar
import hashlib
from pathlib import Path

import pandas as pd
import xarray as xr

DATASET = "reanalysis-era5-land"
VARIABLES = ["2m_temperature", "2m_dewpoint_temperature", "surface_pressure"]
AREA = [52.0, 5.0, 50.5, 6.7]  # north, west, south, east
HOURS = [f"{hour:02d}:00" for hour in range(24)]


def request_for_month(year, month):
    """Return one complete calendar-month request for the fixed extract."""
    return {
        "variable": VARIABLES,
        "year": [str(year)],
        "month": [f"{month:02d}"],
        "day": [f"{day:02d}" for day in range(1, calendar.monthrange(year, month)[1] + 1)],
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


def validate_netcdf(path, year, month):
    """Check timestamps, variables, physical units and missing grid cells."""
    final_day = calendar.monthrange(year, month)[1]
    expected_hours = 24 * final_day
    with xr.open_dataset(path) as dataset:
        required = {"t2m": "K", "d2m": "K", "sp": "Pa"}
        if not set(required) <= set(dataset.data_vars):
            missing = set(required) - set(dataset.data_vars)
            raise ValueError(f"{path} is missing {sorted(missing)}")
        if dataset.sizes.get("valid_time") != expected_hours:
            raise ValueError(f"{path} does not contain {expected_hours} hourly timestamps")

        observed = pd.DatetimeIndex(dataset.valid_time.values)
        expected = pd.date_range(
            pd.Timestamp(year, month, 1), pd.Timestamp(year, month, final_day, 23), freq="h"
        )
        if not observed.equals(expected):
            raise ValueError(f"{path} is not a complete regular UTC month")

        for variable, unit in required.items():
            if dataset[variable].attrs.get("units") != unit:
                raise ValueError(f"{path}: expected {variable} in {unit}")
            if dataset[variable].isnull().any().item():
                raise ValueError(f"{path}: {variable} contains missing grid cells")


def fetch_month(client, year, month, raw_dir):
    """Download one month atomically and leave a valid file untouched."""
    target = raw_dir / f"era5_land_limburg_{year}_{month:02d}.nc"
    if target.exists() and target.stat().st_size:
        validate_netcdf(target, year, month)
        print(f"keep {target}")
        return target

    partial = target.with_suffix(".nc.part")
    if partial.exists():
        partial.unlink()
    print(f"download {year}-{month:02d} -> {target}")
    client.retrieve(DATASET, request_for_month(year, month), str(partial))
    partial.replace(target)
    validate_netcdf(target, year, month)
    return target


def write_manifest(raw_dir):
    """Validate and hash every monthly source file."""
    rows = []
    for path in sorted(raw_dir.glob("era5_land_limburg_????_??.nc")):
        year, month = map(int, path.stem.rsplit("_", 2)[-2:])
        validate_netcdf(path, year, month)
        rows.append(
            {
                "dataset": DATASET,
                "year": year,
                "month": month,
                "expected_hours": 24 * calendar.monthrange(year, month)[1],
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
    parser.add_argument("--month", type=int, choices=range(1, 13))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.start_year > args.end_year:
        parser.error("--start-year must not exceed --end-year")

    periods = [
        (year, month)
        for year in range(args.start_year, args.end_year + 1)
        for month in ([args.month] if args.month else range(1, 13))
    ]
    if args.dry_run:
        for year, month in periods:
            print(f"{year}-{month:02d}", request_for_month(year, month))
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

    for year, month in periods:
        fetch_month(client, year, month, raw_dir)
    write_manifest(raw_dir)
    print(f"completed {len(periods)} requested months and {raw_dir / 'manifest.csv'}")


if __name__ == "__main__":
    main()
