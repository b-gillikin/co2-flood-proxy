#!/usr/bin/env python3
"""Run the source-selected raw-SAR physical rule over the full external census."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_sar import raw_sar_db

CALIBRATION = ROOT / "results/limburg_chapter_sized_v1/physical/calibration.json"
OUT = ROOT / "results/limburg_chapter_sized_v1/physical_external"
AUDIT = ROOT / "data/processed/limburg_chapter_geoid_audit_v1/tile_audit.parquet"
TRIPLET_AUDIT = ROOT / "data/processed/limburg_chapter_triplet_audit_v1/tile_status.parquet"


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    calibration = json.loads(CALIBRATION.read_text())
    if calibration["status"] != "source_only_selected":
        raise ValueError("Physical threshold was not selected on source data")
    selected = calibration["selected"]
    candidate = ((0 if selected["polarization"] == "VV" else 1),
                 selected["threshold_db"], selected["drop_db"])
    physical = load_script("chapter_physical", ROOT / "scripts/234_calibrate_chapter_physical.py")
    io = load_script("chapter_io", ROOT / "scripts/232_chapter_tile_infer.py")
    source = pd.read_parquet(AUDIT)
    pairs = pd.read_parquet(TRIPLET_AUDIT)
    if len(source) != 1301 or (pairs.status == "verified").sum() != 913:
        raise ValueError("External cohort changed")
    jobs = [("delivered", f"{r.event_id}-{r.tile_id}-{r.bbox_id}", "p0") for r in source.itertuples()]
    jobs += [("ee", r.key, ref) for r in pairs.itertuples() if r.status == "verified" for ref in ("p0", "p1")]
    OUT.mkdir(parents=True, exist_ok=True)
    for done, (dataset, key, ref) in enumerate(jobs, 1):
        event = key.split("-")[0]
        target = OUT / "maps" / dataset / event / f"{key}-{ref}.npz"
        receipt = OUT / "receipts" / dataset / event / f"{key}-{ref}.json"
        if receipt.exists():
            record = json.loads(receipt.read_text())
            if target.exists() and record["output_sha256"] == sha256(target):
                continue
            raise ValueError(f"Physical map or receipt changed: {key}/{ref}")
        if shutil.disk_usage(ROOT).free < 52 * 1024**3:
            raise RuntimeError("Disk reserve approached during physical census")
        raw, transform, crs, times, provenance = io.input_tile(key, dataset, ref)
        db, valid = raw_sar_db(raw)
        mapped = physical.predict_classes(db, valid, candidate)
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(".partial.npz")
        np.savez_compressed(partial, prediction=mapped, radar_valid=valid)
        partial.replace(target)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        record = {"status": "complete_unscored", "key": key, "dataset": dataset,
                  "reference": ref, "selected": selected, "calibration_sha256": sha256(CALIBRATION),
                  "input": provenance, "valid_pixels": int(valid.sum()),
                  "output_sha256": sha256(target), "completed_unix": time.time()}
        temporary = receipt.with_suffix(".partial")
        temporary.write_text(json.dumps(record, indent=2) + "\n")
        temporary.replace(receipt)
        if done % 100 == 0 or done == len(jobs):
            print(json.dumps({"done": done, "total": len(jobs), "free_gib":
                round(shutil.disk_usage(ROOT).free / 1024**3, 2)}), flush=True)
    (OUT / "complete.json").write_text(json.dumps({"status": "full_unscored_physical_census_complete",
        "jobs": len(jobs), "source_calibration_sha256": sha256(CALIBRATION)}, indent=2) + "\n")


if __name__ == "__main__":
    main()
