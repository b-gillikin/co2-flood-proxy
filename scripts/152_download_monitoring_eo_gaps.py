#!/usr/bin/env python3
"""Download/audit only the new monitoring-clock EO windows; no inference."""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "results/monitoring_acquisition_2026_10_28"
DEST = ROOT / "data/raw/limburg_monitoring_eo"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--workers", type=int, choices=[1, 2], default=2)
    parser.add_argument("--project", default="limburg-511403")
    args = parser.parse_args()
    primary = load("96_acquire_limburg_compact_eo.py")
    supplemental = load("114_expand_limburg_eo_acquisition.py")
    audit = load("127_audit_eo_expansion_pixels.py")
    jobs_path = PLAN / "eo-new-window-jobs.json"
    jobs = json.loads(jobs_path.read_text())
    report = json.loads((PLAN / "eo-gap-inventory.json").read_text())
    print(
        json.dumps(
            {
                "jobs": len(jobs),
                "raw_upper_bound_gib": report["raw_tile_upper_bound_bytes"] / 2**30,
                "free_gib": shutil.disk_usage(ROOT).free / 2**30,
                "destination": str(DEST),
            }
        ),
        flush=True,
    )
    if not args.download:
        return
    import ee

    ee.Initialize(project=args.project)
    region = ee.Geometry(json.loads((ROOT / "data/raw/limburg_compact_eo/roi.geojson").read_text()))
    DEST.mkdir(parents=True, exist_ok=True)
    lock = (DEST / ".download.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    identity = {
        "jobs_sha256": primary.ARCHIVE.digest(jobs_path),
        "primary_helper_sha256": primary.ARCHIVE.digest(
            ROOT / "scripts/96_acquire_limburg_compact_eo.py"
        ),
        "supplemental_helper_sha256": primary.ARCHIVE.digest(
            ROOT / "scripts/114_expand_limburg_eo_acquisition.py"
        ),
        "audit_sha256": primary.ARCHIVE.digest(ROOT / "scripts/127_audit_eo_expansion_pixels.py"),
    }
    identity_path = DEST / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError("Existing EO pull identity differs; preserve it and version a new pull")
    primary.ARCHIVE.write_json(identity_path, identity)
    completed, failed = {}, {}
    counts = {"downloaded": 0, "existing": 0}

    def save(status):
        primary.ARCHIVE.write_json(
            DEST / "progress.json",
            {
                "status": status,
                "pid": os.getpid(),
                "updated_utc": datetime.now(timezone.utc).isoformat(),
                "planned_files": len(jobs),
                "validated_files": len(completed),
                "percent_complete": round(100 * len(completed) / len(jobs), 2) if jobs else 100,
                **counts,
                "validated_bytes": sum(r["bytes"] for r in completed.values()),
                "failed_jobs": failed,
                "identity": identity,
                "scope": "Source acquisition and tile validation only, not new embeddings or scientific scores.",
            },
        )

    def acquire(job):
        helper = primary if job["product"] in primary.PRODUCTS else supplemental
        image = helper.composite(ee, job)
        status = primary.ARCHIVE.download_job(job, DEST, 60, region, image)
        checked = audit.inspect(job, base=DEST)
        checked["bytes"] = (DEST / job["relative_path"]).stat().st_size
        return status, checked

    save("running")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(acquire, job): job for job in jobs}
        for future in as_completed(pending):
            job = pending[future]
            key = job["relative_path"]
            try:
                state, checked = future.result()
                counts[state] += 1
                completed[key] = checked
                print(f"validated {len(completed)}/{len(jobs)} {key}", flush=True)
            except Exception as exc:
                message = re.sub(r"https?://\S+", "[provider URL]", str(exc))[:500]
                failed[key] = {"type": type(exc).__name__, "message": message}
                print(f"failed {key}: {type(exc).__name__}: {message}", flush=True)
            save("running")
    primary.ARCHIVE.write_json(DEST / "pixel-audit.json", list(completed.values()))
    save("completed" if not failed else "completed_with_failures")
    if failed:
        raise SystemExit(f"{len(failed)} source jobs need review/retry; validated files retained")


if __name__ == "__main__":
    main()
