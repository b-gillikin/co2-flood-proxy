"""Audit every staged supplemental raster; resumable, no fabricated model inputs."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/limburg_eo_expansion"
OUT = ROOT / "results/eo_expansion_audit"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def inspect(job, base=BASE):
    path = base / job["relative_path"]
    receipt = json.loads(path.with_suffix(".receipt.json").read_text())
    for key in ("relative_path", "bands", "bounds", "window", "asset_ids", "acquisition_ms"):
        if receipt[key] != job[key]:
            raise ValueError("Receipt mismatch: " + key)
    if digest(path) != receipt["sha256"]:
        raise ValueError("Data checksum mismatch")
    start = datetime.fromisoformat(job["window"]["start"]).timestamp() / 86400
    end = datetime.fromisoformat(job["window"]["end"]).timestamp() / 86400
    if any(not start * 86400000 <= t < end * 86400000 for t in job["acquisition_ms"]):
        raise ValueError("Catalogue acquisition outside UTC window")
    with rasterio.open(path) as ds:
        if str(ds.crs) != "EPSG:32632" or ds.transform.b or ds.transform.d:
            raise ValueError("Unexpected CRS/grid")
        if not np.allclose(ds.bounds, job["bounds"], atol=1e-6, rtol=0):
            raise ValueError("Bounds mismatch")
        if ds.count != len(job["bands"]) + 1:
            raise ValueError("Band count mismatch")
        if any(ds.descriptions) and list(ds.descriptions) != job["bands"] + ["valid_bits"]:
            raise ValueError("Band descriptions mismatch")
        data = ds.read()
        bits = data[-1].astype(np.uint32)
        masks = np.stack([(bits & (1 << i)) != 0 for i in range(len(job["bands"]))])
        masks &= np.isfinite(data[:-1])
        d = job["bands"].index("acquired_day")
        dates = data[d][masks[d]]
        if dates.size and (dates.min() < np.floor(start) or dates.max() >= end):
            raise ValueError("Observed date outside UTC window")
        spectral = [
            i
            for i, b in enumerate(job["bands"])
            if b not in {"acquired_day", "angle", "QA_PIXEL", "QA_RADSAT", "QA60", "sensor_id"}
        ]
        valid = masks[spectral].all(axis=0) & masks[d]
        return {
            "relative_path": job["relative_path"],
            "sha256": receipt["sha256"],
            "product": job["product"],
            "window_id": job["window"]["id"],
            "pixels": int(valid.size),
            "joint_valid_pixels": int(valid.sum()),
            "observed_day_min": float(dates.min()) if dates.size else None,
            "observed_day_max": float(dates.max()) if dates.size else None,
            "catalogue_scene_count": len(job["asset_ids"]),
            "scope": "tile pixels; not catchment coverage or model eligibility",
        }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs_path = BASE / "jobs.json"
    jobs = json.loads(jobs_path.read_text())
    stage = json.loads((BASE / "staging-progress.json").read_text())
    if stage["status"] != "completed" or stage["verified_files"] != len(jobs):
        raise ValueError("Full staging must complete before full pixel audit")
    ledger = OUT / "pixels.jsonl"
    identity = {"jobs_sha256": digest(jobs_path), "audit_code_sha256": digest(Path(__file__))}
    identity_path = OUT / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError(
            "Audit inputs/code changed; preserve old audit and use a new output directory"
        )
    identity_path.write_text(json.dumps(identity, indent=2) + "\n")
    done = {}
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            row = json.loads(line)
            done[row["relative_path"]] = row

    def save(status, failures):
        counts = Counter(r["product"] for r in done.values())
        state = {
            "status": status,
            "pid": os.getpid(),
            "updated_utc": datetime.now(timezone.utc).isoformat(),
            "planned_files": len(jobs),
            "audited_files": len(done),
            "products": dict(counts),
            "jobs_sha256": digest(jobs_path),
            "failures": failures,
            "model_extraction_status": "pending compatible input adapters; no new empirical scores",
        }
        temp = OUT / "progress.partial"
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(OUT / "progress.json")

    failures = []
    save("running", failures)
    with ledger.open("a") as output:
        for job in jobs:
            if job["relative_path"] in done:
                continue
            try:
                row = inspect(job)
                output.write(json.dumps(row) + "\n")
                output.flush()
                done[row["relative_path"]] = row
            except Exception as exc:
                failures.append({"path": job["relative_path"], "error": str(exc)})
            if (len(done) + len(failures)) % 100 == 0:
                save("running", failures)
    save("completed" if not failures else "completed_with_failures", failures)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
