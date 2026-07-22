"""Normalize delivered groundwater/mine-water tables to the locked daily contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.io_groundwater import normalize_groundwater, validate_series_metadata

DAILY_PATH = Path("data/interim/groundwater_daily.csv")
METADATA_PATH = Path("data/interim/groundwater_series.csv")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readings", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--source-timezone", default="UTC")
    parser.add_argument("--daily-output", type=Path, default=DAILY_PATH)
    parser.add_argument("--metadata-output", type=Path, default=METADATA_PATH)
    args = parser.parse_args()

    readings = pd.read_csv(args.readings)
    metadata = validate_series_metadata(pd.read_csv(args.metadata))
    daily = normalize_groundwater(readings, metadata, source_timezone=args.source_timezone)
    args.daily_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(args.daily_output, index=False)
    metadata.to_csv(args.metadata_output, index=False)
    print(f"wrote {args.daily_output} ({len(daily)} observed series-days; no interpolation)")
    print(f"wrote {args.metadata_output} ({len(metadata)} series)")


if __name__ == "__main__":
    main()
