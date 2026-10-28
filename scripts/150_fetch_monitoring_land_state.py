#!/usr/bin/env python3
"""Resumable, small CDS soil/snow extract for the monitoring-loss comparison.

Keeps native covering-grid fields and input receipts, separately from the
existing temperature/dewpoint/pressure archive. No model scores or imputation.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/limburg_monitoring_land_state"
GEOMETRY = ROOT / "data/interim/foundation_model_catchments.gpkg"
DATASET = "reanalysis-era5-land"
VARIABLES = [
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "snow_depth_water_equivalent",
]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def covering_area(bounds):
    """Cover all polygons, plus one regular 0.1-degree cell on each side."""
    west, south, east, north = bounds
    return [
        round(math.ceil(north * 10) / 10 + 0.1, 1),
        round(math.floor(west * 10) / 10 - 0.1, 1),
        round(math.floor(south * 10) / 10 - 0.1, 1),
        round(math.ceil(east * 10) / 10 + 0.1, 1),
    ]


def request_for_month(year, month, area):
    return {
        "variable": VARIABLES,
        "year": [str(year)],
        "month": [f"{month:02d}"],
        "day": [f"{d:02d}" for d in range(1, calendar.monthrange(year, month)[1] + 1)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": area,
    }


def expected_times(year, month):
    return pd.date_range(
        pd.Timestamp(year, month, 1),
        pd.Timestamp(year, month, calendar.monthrange(year, month)[1], 23),
        freq="h",
    )


def validate(path, year, month, area):
    with xr.open_dataset(path) as ds:
        time_name = "valid_time" if "valid_time" in ds else "time"
        if not pd.DatetimeIndex(ds[time_name].values).equals(expected_times(year, month)):
            raise ValueError("Downloaded field timestamps are not the complete UTC month")
        required = {"swvl1", "swvl2", "sd"}
        if not required <= set(ds.data_vars):
            raise ValueError(f"Missing requested fields: {required - set(ds.data_vars)}")
        nlat = round((area[0] - area[2]) * 10) + 1
        nlon = round((area[3] - area[1]) * 10) + 1
        if ds.sizes["latitude"] != nlat or ds.sizes["longitude"] != nlon:
            raise ValueError("Unexpected covering-grid dimensions")
        if not np.allclose(ds.latitude, np.linspace(area[0], area[2], nlat)):
            raise ValueError("Unexpected latitude grid")
        if not np.allclose(ds.longitude, np.linspace(area[1], area[3], nlon)):
            raise ValueError("Unexpected longitude grid")
        stats = {}
        for name in sorted(required):
            v = ds[name]
            units = v.attrs.get("units", "")
            if name.startswith("swvl") and units not in {"m**3 m**-3", "m3 m-3", "m^3 m^-3"}:
                raise ValueError(f"Unexpected {name} units: {units}")
            if name == "sd" and units not in {"m", "m of water equivalent"}:
                raise ValueError(f"Unexpected snow-water units: {units}")
            a = v.to_numpy()
            if not np.isfinite(a).all():
                raise ValueError(f"Missing/nonfinite covering-grid values: {name}")
            if a.min() < -1e-5 or (name.startswith("swvl") and a.max() > 1.00001):
                raise ValueError(f"Physically inconsistent {name} range")
            stats[name] = {
                "units": units,
                "minimum": float(a.min()),
                "maximum": float(a.max()),
                "shape": list(a.shape),
            }
        return {"hours": len(ds[time_name]), "fields": stats, "grid_cells": nlat * nlon}


def fetch_one(year, month, area, destination):
    import cdsapi

    request = request_for_month(year, month, area)
    target = destination / f"era5_land_monitoring_{year}_{month:02d}.nc"
    receipt_path = target.with_suffix(".receipt.json")
    if target.exists():
        if not receipt_path.exists():
            raise ValueError(f"Existing file without receipt: {target.name}")
        receipt = json.loads(receipt_path.read_text())
        if receipt["request"] != request or digest(target) != receipt["sha256"]:
            raise ValueError(f"Existing source identity mismatch: {target.name}")
        validate(target, year, month, area)
        return receipt
    partial = target.with_suffix(".nc.partial")
    # A partial transfer is not a source delivery; the CDS result is re-downloadable.
    partial.unlink(missing_ok=True)
    client = cdsapi.Client(
        quiet=True,
        progress=False,
        timeout=120,
        retry_max=3,
        sleep_max=10,
        wait_until_complete=False,
    )
    job_path = target.with_suffix(".request.json")
    if job_path.exists():
        job = json.loads(job_path.read_text())
        if job["request"] != request:
            raise ValueError("Cached remote request differs from requested month")
        result = client.client.get_remote(job["request_id"])
        if result.status in {"failed", "rejected"}:
            result = client.retrieve(DATASET, request)
    else:
        result = client.retrieve(DATASET, request)
    write_json(
        job_path,
        {
            "dataset": DATASET,
            "request": request,
            "request_id": result.request_id,
            "saved_utc": stamp(),
        },
    )
    result.download(str(partial))
    stats = validate(partial, year, month, area)
    receipt = {
        "dataset": DATASET,
        "request": request,
        "request_id": getattr(result, "request_id", None),
        "year": year,
        "month": month,
        "file": target.name,
        "bytes": partial.stat().st_size,
        "sha256": digest(partial),
        "downloaded_utc": stamp(),
        "validation": stats,
        "interpretation": "Native modeled land states; sd is metres water equivalent, not snow thickness.",
    }
    partial.replace(target)
    write_json(receipt_path, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--start-year", type=int, default=2009)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--workers", type=int, choices=[1, 2], default=2)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    if args.start_year > args.end_year:
        parser.error("start year must not exceed end year")
    import geopandas as gpd

    frame = gpd.read_file(GEOMETRY)
    area = covering_area(frame.to_crs(4326).total_bounds)
    periods = [(y, q) for y in range(args.start_year, args.end_year + 1) for q in range(1, 13)]
    hours = sum(len(expected_times(y, q)) for y, q in periods)
    cells = (round((area[0] - area[2]) * 10) + 1) * (round((area[3] - area[1]) * 10) + 1)
    plan = {
        "created_utc": stamp(),
        "dataset": DATASET,
        "variables": VARIABLES,
        "area_nwse": area,
        "months": len(periods),
        "hours": hours,
        "grid_cells": cells,
        "estimated_float32_value_bytes": hours * cells * 3 * 4,
        "estimate_scope": "Uncompressed value payload, excluding metadata; actual encoding/compression varies.",
        "geometry_sha256": digest(GEOMETRY),
        "catchments": frame.gauge.tolist(),
        "source_code_sha256": digest(Path(__file__)),
        "purpose": "Supporting soil/snow control in the monitoring-loss study; no new outcome/model.",
    }
    destination = args.output_dir
    destination.mkdir(parents=True, exist_ok=True)
    plan_path = destination / "download-plan.json"
    if plan_path.exists():
        old = json.loads(plan_path.read_text())
        for key in ["area_nwse", "variables", "months", "hours", "geometry_sha256"]:
            if old[key] != plan[key]:
                raise ValueError(f"Existing plan differs in {key}; use a new versioned destination")
    write_json(plan_path, plan)
    print(json.dumps(plan, indent=2), flush=True)
    if not args.download:
        return
    import fcntl

    # Avoid duplicate writers when a persistent job is resumed from another shell.
    lock = (destination / ".download.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    receipts, failures = {}, {}
    manifest_path = destination / "manifest.json"

    def save(status):
        write_json(
            manifest_path,
            {
                "status": status,
                "updated_utc": stamp(),
                "pid": os.getpid(),
                "planned_months": len(periods),
                "completed_months": len(receipts),
                "completed_bytes": sum(r["bytes"] for r in receipts.values()),
                "percent_complete": round(100 * len(receipts) / len(periods), 2),
                "plan_sha256": digest(plan_path),
                "receipts": list(receipts.values()),
                "failures": failures,
            },
        )

    save("running")
    # Validate one real source before filling the provider queue with the plan.
    first_year, first_month = periods[0]
    try:
        receipts[f"{first_year}-{first_month:02d}"] = fetch_one(
            first_year, first_month, area, destination
        )
    except Exception as exc:
        failures["initial_source_check"] = {"type": type(exc).__name__}
        save("initial_source_check_failed")
        raise
    save("running")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, y, q, area, destination): (y, q) for y, q in periods[1:]}
        for future in as_completed(futures):
            y, q = futures[future]
            key = f"{y}-{q:02d}"
            try:
                receipts[key] = future.result()
                print(f"validated {key}: {len(receipts)}/{len(periods)}", flush=True)
            except Exception as exc:
                # Do not persist credentials or signed URL query strings in failures.
                message = re.sub(r"https?://\S+", "[provider URL]", str(exc))[:500]
                failures[key] = {"type": type(exc).__name__, "message": message}
                print(f"failed {key}: {type(exc).__name__}: {message}", flush=True)
            save("running")
    save("completed" if not failures else "completed_with_failures")
    if failures:
        raise SystemExit(f"{len(failures)} months need retry; validated sources preserved")


if __name__ == "__main__":
    main()
