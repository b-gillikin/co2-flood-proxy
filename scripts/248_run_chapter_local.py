#!/usr/bin/env python3
"""Map every assessable held local radar case with the fixed three pipelines."""

from __future__ import annotations

import fcntl
import gc
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import torch
from rasterio.transform import array_bounds
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import atomic_json, remove_prior_coverage, sha256
from limburg_chapter_sar import raw_sar_db
from limburg_chapter_scores import score_tile

INPUT = ROOT / "data/raw/limburg_chapter_local_triplets_v1"
OUT = ROOT / "results/limburg_chapter_sized_v1/local"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def acquired(scene):
    return datetime.strptime(scene.split("_")[4], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)


def read_triplet(job):
    path = INPUT / "tiles" / job["aoi"] / f"{job['key']}.tif"
    record = json.loads(path.with_suffix(".receipt.json").read_text())
    if record["job"] != job or sha256(path) != record["sha256"]:
        raise ValueError("Changed local triplet/provenance")
    with rasterio.open(path) as ds:
        return ds.read(), ds.transform, ds.crs, record["sha256"]


def prepare_support(jobs):
    frame = pd.read_parquet(
        ROOT / "results/applied_study_v1/local_references/scoring/scene-reference-pairs.parquet"
    ).set_index("path")
    previous = {}
    rows = []
    order = sorted(jobs, key=lambda row: (abs(row["reference_offset_hours"]), row["key"]))
    for job in order:
        post = frame.loc[job["post_path"]]
        case = f"{job['aoi']}__{acquired(job['products']['post']).date()}__orbit{int(post.relative_orbit)}_{post.orbit_pass}"
        raw, transform, crs, digest = read_triplet(job)
        valid_p0 = np.all(np.isfinite(raw[[0, 1, 4, 5]]) & (raw[[0, 1, 4, 5]] > 0), axis=0)
        valid_p1 = np.all(np.isfinite(raw[[2, 3, 4, 5]]) & (raw[[2, 3, 4, 5]] > 0), axis=0)
        valid = valid_p0 & valid_p1
        label_path = ROOT / job["reference_path"]
        if sha256(label_path) != job["reference_sha256"]:
            raise ValueError("Changed local reference")
        with rasterio.open(label_path) as ds:
            if ds.shape != raw.shape[1:] or ds.transform != transform or ds.crs != crs:
                raise ValueError("Local reference and imagery grids differ")
            reference = ds.read(1)
        if not set(np.unique(reference)) <= {0, 1, 255}:
            raise ValueError("Unexpected local flood-proxy coding")
        label = np.where(reference == 1, 2, np.where(reference == 255, 255, 0)).astype(np.uint8)
        eligible = (valid & (label != 255)).astype(np.uint8)
        extent = box(*array_bounds(*valid.shape, transform))
        prior = [
            (mask, old_transform, old_crs)
            for mask, old_transform, old_crs, bounds in previous.setdefault(case, [])
            if bounds.intersection(extent).area > 0
        ]
        owned = remove_prior_coverage(eligible, transform, crs, prior).astype(bool)
        previous[case].append((eligible, transform, crs, extent))
        path = OUT / "support" / f"{job['key']}.npz"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            with np.load(path) as existing:
                if not all(
                    np.array_equal(existing[name], value)
                    for name, value in [("label", label), ("owner", owned), ("common_valid", valid)]
                ):
                    raise ValueError("Local support changed; preserve existing results and review")
        else:
            partial = path.with_suffix(".partial.npz")
            np.savez_compressed(partial, label=label, owner=owned, common_valid=valid)
            partial.replace(path)
        rows.append(
            {
                "key": job["key"],
                "case": case,
                "aoi": job["aoi"],
                "triplet_sha256": digest,
                "support_sha256": sha256(path),
                "updated": job["updated"],
                "reference_offset_hours": job["reference_offset_hours"],
                "reference_dependence": job["reference_dependence"],
                "eligible_pixels": int(eligible.sum()),
                "owned_pixels": int(owned.sum()),
                "p0_radar_pixels": int(valid_p0.sum()),
                "p1_radar_pixels": int(valid_p1.sum()),
                "p0_labeled_pixels": int((valid_p0 & (label != 255)).sum()),
                "p1_labeled_pixels": int((valid_p1 & (label != 255)).sum()),
            }
        )
    return rows


def main():
    complete = json.loads((INPUT / "complete.json").read_text())
    inventory_path = INPUT / "inventory.json"
    if complete["inventory_sha256"] != sha256(inventory_path):
        raise ValueError("Local acquisition inventory changed")
    jobs = [
        row for row in json.loads(inventory_path.read_text())["jobs"] if row["status"] == "prepared"
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / "results/applied_study_v3/.mps-owner.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    torch.set_num_threads(2)
    engine = load("mapping_engine", ROOT / "scripts/237_run_chapter_external.py")
    physical = load("physical", ROOT / "scripts/234_calibrate_chapter_physical.py")
    calibration_path = ROOT / "results/limburg_chapter_sized_v1/physical/calibration.json"
    calibration = json.loads(calibration_path.read_text())["selected"]
    candidate = (
        0 if calibration["polarization"] == "VV" else 1,
        calibration["threshold_db"],
        calibration["drop_db"],
    )
    coverage = prepare_support(jobs)
    pd.DataFrame(coverage).to_parquet(OUT / "coverage.parquet", index=False)
    info = {row["key"]: row for row in coverage}
    all_rows = []
    for kind in ("physical", "unet", "native"):
        models = None
        if kind == "physical":
            model_hashes = {"0": sha256(calibration_path)}
        else:
            states = engine.completed_models(kind)
            model_hashes = {str(seed): sha256(path) for seed, path in states.items()}
            models = engine.load_models(kind, states, "mps")
        for count, job in enumerate(jobs, 1):
            key = job["key"]
            receipt_path = OUT / "receipts" / kind / f"{key}.json"
            expected = {
                "model_hashes": model_hashes,
                "triplet_sha256": info[key]["triplet_sha256"],
                "support_sha256": info[key]["support_sha256"],
            }
            if receipt_path.exists():
                receipt = json.loads(receipt_path.read_text())
                if any(receipt.get(k) != v for k, v in expected.items()):
                    raise ValueError("Local map resume changed model/input/support")
                if not all(
                    sha256(OUT / name) == digest for name, digest in receipt["files"].items()
                ):
                    raise ValueError("Changed local prediction")
                all_rows.extend(receipt["rows"])
                continue
            if shutil.disk_usage(ROOT).free < 55 * 1024**3:
                raise RuntimeError("Local mapping approached disk reserve")
            raw, transform, crs, _ = read_triplet(job)
            with np.load(OUT / "support" / f"{key}.npz") as values:
                label, owned = values["label"], values["owner"]
            files, score_rows = {}, []
            previous_outputs = None
            for reference, indices in [("p0", [0, 1, 4, 5]), ("p1", [2, 3, 4, 5])]:
                current = raw[indices]
                if reference == "p1" and not job["updated"]:
                    if not np.array_equal(current, raw[[0, 1, 4, 5]], equal_nan=True):
                        raise ValueError("Unchanged local reference has different raster values")
                    outputs, valid = previous_outputs
                elif kind == "physical":
                    db, valid = raw_sar_db(current)
                    outputs = {0: physical.predict_classes(db, valid, candidate)}
                else:
                    times = acquired(job["products"][reference]), acquired(job["products"]["post"])
                    outputs, valid = engine.predict(
                        current, transform, crs, times, kind, models, "mps"
                    )
                previous_outputs = outputs, valid
                for seed, values in outputs.items():
                    prediction = (
                        values
                        if kind == "physical"
                        else np.where(valid, values.argmax(axis=0), 255).astype(np.uint8)
                    )
                    if np.any(owned & ~valid):
                        raise ValueError("Local owned target has no valid model input")
                    name = f"predictions/{kind}/{key}-{reference}-{seed}.npz"
                    path = OUT / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    temporary = path.with_suffix(".partial.npz")
                    payload = {"prediction": prediction, "radar_valid": valid}
                    if kind != "physical":
                        payload["probability"] = values.astype(np.float16)
                    np.savez_compressed(temporary, **payload)
                    temporary.replace(path)
                    files[name] = sha256(path)
                    result = score_tile(label, prediction, owned)
                    matrix = result.pop("confusion")
                    score_rows.append(
                        {
                            **info[key],
                            "model": kind,
                            "seed": seed,
                            "reference": reference,
                            **result,
                            **{f"c{i}{j}": matrix[i][j] for i in range(3) for j in range(3)},
                        }
                    )
            atomic_json(
                receipt_path,
                {
                    **expected,
                    "files": files,
                    "rows": score_rows,
                    "runner_sha256": sha256(Path(__file__)),
                },
            )
            all_rows.extend(score_rows)
            if count % 10 == 0 or count == len(jobs):
                print(
                    json.dumps({"model": kind, "completed": count, "total": len(jobs)}), flush=True
                )
        if models is not None:
            del models
            gc.collect()
            torch.mps.empty_cache()
    scores = pd.DataFrame(all_rows)
    scores.to_parquet(OUT / "tile_scores.parquet", index=False)
    columns = [f"c{i}{j}" for i in range(3) for j in range(3)] + ["known_pixels"]
    grouped = scores.groupby(["case", "aoi", "model", "seed", "reference"], as_index=False)[
        columns
    ].sum()
    union = grouped.c20 + grouped.c21 + grouped.c22 + grouped.c02 + grouped.c12
    grouped["flood_iou"] = grouped.c22 / union.replace(0, np.nan)
    grouped.to_parquet(OUT / "case_scores.parquet", index=False)
    atomic_json(
        OUT / "complete.json",
        {
            "status": "local_mapping_and_reference_agreement_complete",
            "input_jobs": len(jobs),
            "cases": int(grouped.case.nunique()),
            "tile_score_rows": len(scores),
            "updated_input_jobs": sum(row["updated"] for row in jobs),
            "physical_flood_episodes": 1,
            "inventory_sha256": sha256(inventory_path),
            "score_sha256": sha256(OUT / "case_scores.parquet"),
            "interpretation": "Previously inspected mapped proxies, not independently confirmed dry negatives or independent NL/DE floods. Unknown, hydrography and trace-only areas remain excluded. Chronology is actual imagery-versus-reference offset.",
        },
    )


if __name__ == "__main__":
    main()
