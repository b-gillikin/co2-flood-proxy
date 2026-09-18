"""Area-average hourly radar rainfall over each catchment (protocol §6).

The product is operational RADOLAN RW by default (see `37_fetch_radar.py` for
why RADKLIM cannot serve the cohort); `--product radklim` builds the RADKLIM
series for comparison only, written to the report folder, never spliced.

Each 1 km radar cell is weighted by the area it shares with the catchment,
computed in the radar's own polar-stereographic grid. An hour is missing when
any cell with positive weight is missing: no missing code becomes zero and no
gap is filled.

Time labels: DWD stamps the end of a 60-minute accumulation at HH:50 UTC.
The accumulation ending HH:50 is labelled HH+1:00, so rainfall labelled t
covers (t - 70 min, t - 10 min] and never extends past its label. With the
discharge convention (the hour labelled t is the mean over (t - 1 h, t]),
rainfall at lag 1 therefore ends before the onset hour begins.

Also writes exposure-only quality checks for the D2 coverage decision: missing
hours per catchment and annual catchment totals.

Example: python scripts/41_radar_catchment_rainfall.py --product radolan
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
RADAR = {"radolan": ROOT / "data/raw/radolan_rw", "radklim": ROOT / "data/raw/radklim"}
CATCHMENTS = ROOT / "data/interim/event_study_catchments.gpkg"
OUTPUT = ROOT / "data/interim/radolan_catchment_hourly.csv"
REPORT = ROOT / "results/radar"


def crop_bounds(manifest):
    """Projected crop bounds; older RADKLIM manifests store grid rows and columns."""
    if "crop_bounds_m" in manifest:
        return manifest["crop_bounds_m"]
    x0, y0 = manifest["grid_lower_left_m"]
    size = manifest["cell_m"]
    row0, row1 = manifest["crop_rows_from_south"]
    col0, col1 = manifest["crop_cols_from_west"]
    return [x0 + col0 * size, y0 + row0 * size, x0 + col1 * size, y0 + row1 * size]


def cell_weights(manifest):
    """(catchment x cell) area weights on the cropped radar grid."""
    xmin, ymin, xmax, ymax = crop_bounds(manifest)
    size = manifest["cell_m"]
    n_rows, n_cols = round((ymax - ymin) / size), round((xmax - xmin) / size)
    rows, cols = np.meshgrid(np.arange(n_rows), np.arange(n_cols), indexing="ij")
    cells = gpd.GeoDataFrame(
        {"row": rows.ravel(), "col": cols.ravel()},
        geometry=[
            box(xmin + c * size, ymin + r * size, xmin + (c + 1) * size, ymin + (r + 1) * size)
            for r, c in zip(rows.ravel(), cols.ravel(), strict=True)
        ],
        crs=manifest["crs"],
    )
    catchments = gpd.read_file(CATCHMENTS).to_crs(manifest["crs"])
    weights = {}
    for item in catchments.itertuples():
        shared = cells.geometry.intersection(item.geometry).area.to_numpy()
        grid = np.zeros((n_rows, n_cols))
        grid[cells.row, cells.col] = shared / 1e6
        if not np.isclose(grid.sum(), item.geometry.area / 1e6, rtol=1e-6):
            raise ValueError(f"{item.watercourse} extends beyond the radar crop")
        weights[item.watercourse] = grid
    return weights


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--product", choices=sorted(RADAR), default="radolan")
    args = parser.parse_args()
    radar = RADAR[args.product]
    manifest = json.loads((radar / "manifest.json").read_text())
    weights = cell_weights(manifest)
    names = list(weights)
    stacked = np.stack([weights[name] for name in names])  # (catchment, row, col)
    positive = stacked > 0
    total = stacked.sum(axis=(1, 2))

    frames = []
    for path in sorted((radar / "crops").glob("*_rw_*.npz")):
        with np.load(path) as data:
            end = pd.DatetimeIndex(data["end_utc"]).tz_localize("UTC")
            rain = data["rain_0p1mm"].astype(float)
        missing = rain < 0
        rain = np.where(missing, 0.0, rain) / 10.0
        values = np.einsum("trc,krc->tk", rain, stacked) / total
        incomplete = np.einsum("trc,krc->tk", missing.astype(float), positive.astype(float)) > 0
        values[incomplete] = np.nan
        label = end.ceil("h")
        frames.append(pd.DataFrame(values, index=label, columns=names))
    rainfall = pd.concat(frames).sort_index()
    if rainfall.index.has_duplicates:
        raise ValueError("Duplicate radar hours after labelling")
    grid = pd.date_range(rainfall.index.min(), rainfall.index.max(), freq="h")
    rainfall = rainfall.reindex(grid).round(3)
    rainfall.index.name = "timestamp_utc"
    out = rainfall.reset_index()
    out["timestamp_utc"] = out.timestamp_utc.dt.strftime("%Y-%m-%dT%H:%MZ")
    REPORT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT if args.product == "radolan" else REPORT / "radklim_catchment_hourly.csv"
    out.to_csv(target, index=False)
    equal_area = gpd.read_file(CATCHMENTS).set_index("watercourse").to_crs("EPSG:3035").area / 1e6
    quality = pd.DataFrame(
        {
            "catchment_km2": equal_area.reindex(names).round(2),
            "radar_cells": pd.Series(positive.sum(axis=(1, 2)), index=names),
            "first_hour": rainfall.index.min(),
            "last_hour": rainfall.index.max(),
            "missing_share": rainfall.isna().mean().round(4),
        }
    )
    quality.to_csv(REPORT / f"{args.product}_catchment_rainfall_quality.csv")
    annual = rainfall.groupby(rainfall.index.year).agg(lambda column: column.sum(min_count=1))
    annual_missing = rainfall.isna().groupby(rainfall.index.year).mean()
    annual.round(1).to_csv(REPORT / f"{args.product}_annual_catchment_totals_mm.csv")
    annual_missing.round(4).to_csv(REPORT / f"{args.product}_annual_missing_share.csv")
    print(quality.to_string())
    print(annual.round(0).to_string())


if __name__ == "__main__":
    sys.exit(main())
