"""Fixed ERA5-Land request and validation definitions for the cloud backfill."""

from __future__ import annotations

import calendar
import hashlib
import re
from pathlib import Path

import pandas as pd
import xarray as xr

DATASET = "reanalysis-era5-land"
VARIABLES = ["2m_temperature", "2m_dewpoint_temperature", "surface_pressure"]
AREA = [52.0, 5.0, 50.5, 6.7]  # north, west, south, east
HOURS = [f"{hour:02d}:00" for hour in range(24)]
START_YEAR = 2001
END_YEAR = 2025
SOURCE_PREFIX = "source/"

MONTH_PATTERN = re.compile(r"era5_land_limburg_(\d{4})_(\d{2})\.nc$")
MANIFEST_COLUMNS = [
    "dataset",
    "year",
    "month",
    "expected_hours",
    "north",
    "west",
    "south",
    "east",
    "variables",
    "blob",
    "bytes",
    "sha256",
]


def expected_periods():
    """Return the fixed 300-month acquisition sequence."""
    return [(year, month) for year in range(START_YEAR, END_YEAR + 1) for month in range(1, 13)]


def request_for_month(year, month):
    """Return one complete calendar-month CDS request."""
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


def filename(year, month):
    return f"era5_land_limburg_{year}_{month:02d}.nc"


def blob_name(year, month):
    return f"{SOURCE_PREFIX}{filename(year, month)}"


def period_from_name(name):
    """Parse a source filename/blob name, returning None for unrelated files."""
    match = MONTH_PATTERN.search(str(name))
    if not match:
        return None
    year, month = map(int, match.groups())
    if (year, month) not in set(expected_periods()):
        return None
    return year, month


def validate_netcdf(path, year, month):
    """Require the expected variables, units, hours and complete grid cells."""
    final_day = calendar.monthrange(year, month)[1]
    expected_hours = 24 * final_day
    with xr.open_dataset(path) as dataset:
        required = {"t2m": "K", "d2m": "K", "sp": "Pa"}
        missing = set(required) - set(dataset.data_vars)
        if missing:
            raise ValueError(f"{path} is missing {sorted(missing)}")
        if dataset.sizes.get("valid_time") != expected_hours:
            raise ValueError(f"{path} does not contain {expected_hours} hourly timestamps")

        observed = pd.DatetimeIndex(dataset.valid_time.values)
        expected = pd.date_range(
            pd.Timestamp(year, month, 1),
            pd.Timestamp(year, month, final_day, 23),
            freq="h",
        )
        if not observed.equals(expected):
            raise ValueError(f"{path} is not a complete regular UTC month")

        for variable, unit in required.items():
            if dataset[variable].attrs.get("units") != unit:
                raise ValueError(f"{path}: expected {variable} in {unit}")
            if dataset[variable].isnull().any().item():
                raise ValueError(f"{path}: {variable} contains missing grid cells")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_row(path, year, month, target_blob=None):
    """Return the provenance row written only after validation."""
    path = Path(path)
    return {
        "dataset": DATASET,
        "year": year,
        "month": month,
        "expected_hours": 24 * calendar.monthrange(year, month)[1],
        "north": AREA[0],
        "west": AREA[1],
        "south": AREA[2],
        "east": AREA[3],
        "variables": ";".join(VARIABLES),
        "blob": target_blob or blob_name(year, month),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
