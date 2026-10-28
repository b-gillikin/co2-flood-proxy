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
import signal
import sys
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


class DownloadPaused(BaseException):
    """Interrupt waiting/transfer without letting client retries swallow the pause."""


def failure_details(exc):
    """Classify service-wide failures without exposing credentials/signed URLs."""
    code = getattr(getattr(exc, "response", None), "status_code", None)
    message = re.sub(r"https?://\S+", "[provider URL]", str(exc))[:500]
    if code in {401, 403}:
        kind = "account_or_policy"
    elif code in {400, 422}:
        kind = "invalid_request"
    elif code == 429 or (code is not None and code >= 500):
        kind = "provider_throttle_or_outage"
    elif isinstance(exc, ValueError):
        kind = "source_validation"
    else:
        kind = "transfer_or_runtime"
    return {"type": type(exc).__name__, "kind": kind, "http_status": code, "message": message}


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


def configure_projection():
    """Use the existing environment's PROJ database when invoked from the venv."""
    candidate = Path(sys.base_prefix) / "share/proj"
    if "PROJ_DATA" not in os.environ and (candidate / "proj.db").is_file():
        os.environ["PROJ_DATA"] = str(candidate)


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
        try:
            result = client.client.get_remote(job["request_id"])
            status = result.status
        except Exception as exc:
            if getattr(getattr(exc, "response", None), "status_code", None) != 404:
                raise
            status = "expired"
        if status in {"failed", "rejected", "expired"}:
            result = client.retrieve(DATASET, request)
    else:
        result = client.retrieve(DATASET, request)

    def record_remote():
        prior = json.loads(job_path.read_text()) if job_path.exists() else {}
        previous_ids = prior.get("previous_request_ids", [])
        if prior.get("request_id") and prior["request_id"] != result.request_id:
            previous_ids = [*previous_ids, prior["request_id"]]
        write_json(
            job_path,
            {
                "dataset": DATASET,
                "request": request,
                "request_id": result.request_id,
                "previous_request_ids": previous_ids,
                "saved_utc": stamp(),
            },
        )

    record_remote()
    try:
        result.download(str(partial))
    except Exception as exc:
        # Results can expire while the laptop is paused. Renew once, never loop
        # on permissions, terms, invalid syntax or provider rate limiting.
        if getattr(getattr(exc, "response", None), "status_code", None) != 404:
            raise
        result = client.retrieve(DATASET, request)
        record_remote()
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


def run_downloads(periods, area, destination, plan_path, fetch=fetch_one):
    """Sequential service requests; preserve complete progress across a restart."""
    manifest_path = destination / "manifest.json"
    if manifest_path.exists():
        history = destination / "run-history"
        history.mkdir(exist_ok=True)
        snapshot = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        (history / f"{snapshot}.json").write_bytes(manifest_path.read_bytes())
    receipts, failures = {}, {}
    existing_count = 0
    resumed_at = stamp()

    def save(status, active=None):
        write_json(
            manifest_path,
            {
                "status": status,
                "updated_utc": stamp(),
                "resumed_utc": resumed_at,
                "pid": os.getpid(),
                "workers": 1,
                "active_month": active,
                "planned_months": len(periods),
                "completed_months": len(receipts),
                "existing_months_verified": existing_count,
                "completed_bytes": sum(r["bytes"] for r in receipts.values()),
                "percent_complete": round(100 * len(receipts) / len(periods), 2),
                "pending_months": [
                    f"{y}-{m:02d}" for y, m in periods if f"{y}-{m:02d}" not in receipts
                ],
                "plan_sha256": digest(plan_path),
                "runner_sha256": digest(Path(__file__)),
                "receipts": list(receipts.values()),
                "failures": failures,
                "concurrency_note": "One CDS request at a time per ECMWF's 22 October 2026 service guidance; local work may run alongside it.",
            },
        )

    active = None
    try:
        # Verify every completed source first, so a policy/transport failure in
        # the next month does not reset the public count from 58 to 1.
        for y, m in periods:
            if (destination / f"era5_land_monitoring_{y}_{m:02d}.nc").exists():
                active = f"{y}-{m:02d}"
                receipts[active] = fetch(y, m, area, destination)
                existing_count += 1
        save("running")
        for y, m in periods:
            active = f"{y}-{m:02d}"
            if active in receipts:
                continue
            save("running", active)
            receipts[active] = fetch(y, m, area, destination)
            print(f"validated {active}: {len(receipts)}/{len(periods)}", flush=True)
            save("running")
        save("completed")
    except (DownloadPaused, KeyboardInterrupt):
        save("paused", active)
        print("Paused; verified sources and remote request IDs retained.", flush=True)
        return
    except Exception as exc:
        details = failure_details(exc)
        failures[active or "initialization"] = details
        save(
            "blocked" if details["kind"] == "account_or_policy" else "stopped_with_failure", active
        )
        raise SystemExit(f"Stopped at {active}: {details['kind']}: {details['message']}") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--start-year", type=int, default=2009)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--workers",
        type=int,
        choices=[1],
        default=1,
        help="CDS currently requests sequential submissions; local CPU work is independent",
    )
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    if args.start_year > args.end_year:
        parser.error("start year must not exceed end year")
    configure_projection()
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
    # Acquire the writer lock before changing progress or the plan.
    lock = None
    if args.download:
        import fcntl

        lock = (destination / ".download.lock").open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan_path = destination / "download-plan.json"
    if plan_path.exists():
        old = json.loads(plan_path.read_text())
        for key in ["area_nwse", "variables", "months", "hours", "geometry_sha256"]:
            if old[key] != plan[key]:
                raise ValueError(f"Existing plan differs in {key}; use a new versioned destination")
        plan = old  # Preserve the immutable original acquisition plan on resume.
    else:
        write_json(plan_path, plan)
    print(json.dumps(plan, indent=2), flush=True)
    if not args.download:
        return

    def pause(_signum, _frame):
        raise DownloadPaused()

    previous_handler = signal.signal(signal.SIGTERM, pause)
    try:
        run_downloads(periods, area, destination, plan_path)
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
        lock.close()


if __name__ == "__main__":
    main()
