#!/usr/bin/env python3
"""Validate local ERA5-Land months and write the Blob manifest used at handoff."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from era5_common import MANIFEST_COLUMNS, manifest_row, period_from_name, validate_netcdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    for path in sorted(args.source_dir.glob("era5_land_limburg_????_??.nc")):
        period = period_from_name(path.name)
        if period is None:
            continue
        year, month = period
        validate_netcdf(path, year, month)
        rows.append(manifest_row(path, year, month))

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(args.manifest, index=False)
    print(f"validated {len(rows)} monthly files; wrote {args.manifest}")


if __name__ == "__main__":
    main()
