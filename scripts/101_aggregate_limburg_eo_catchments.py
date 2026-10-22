"""Aggregate verified EO patch sequences using exact observed catchment area.

Patch embeddings are contextual feature proxies, not pixel-level physical
measurements. Fixed native patch extents and missing coverage stay visible.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_event_inputs import aggregate_vectors, observed_patch_area, pixel_area_weights
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output, validate_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preparation", type=Path, default=ROOT / "results/eo_comparison_preparation"
    )
    parser.add_argument(
        "--sequences", type=Path, default=ROOT / "data/processed/limburg_eo_sequences"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results/eo_catchment_representations")
    parser.add_argument(
        "--engineering",
        action="store_true",
        help="Explicitly separate test fixtures; never join these to event analysis",
    )
    parser.add_argument("--model")
    parser.add_argument("--run-directory", type=Path, help="One explicitly selected extraction run")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Label incomplete/error-bearing input as partial; never complete",
    )
    args = parser.parse_args()
    args.preparation = args.preparation.resolve()
    args.sequences = args.sequences.resolve()
    args.out = args.out.resolve()
    target = args.out / ("engineering" if args.engineering else "census")
    target.parent.mkdir(parents=True, exist_ok=True)
    with (target.parent / ("." + target.name + ".lock")).open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with fresh_output(target) as stage:
            return aggregate(args, stage)


def aggregate(args, target):
    catchment_path = args.preparation / "catchments.gpkg"
    catchments = gpd.read_file(catchment_path)
    if str(catchments.crs) != "EPSG:32632":
        raise ValueError("Projected 32632 catchments required")
    geometry_hash = sha256(catchment_path)
    cache = ROOT / "data/processed/eo_pixel_area_weights" / geometry_hash
    cache.mkdir(parents=True, exist_ok=True)
    groups = {}
    source_hashes = {}
    errors = []
    patch_areas = []
    accepted = []
    rejected = []
    contracts = {}
    context_path = args.preparation / "contexts.json"
    expected_contexts = (
        [c["context_id"] for c in json.loads(context_path.read_text())]
        if context_path.exists()
        else None
    )
    context_windows = (
        {
            c["context_id"]: [w["id"] for w in c["windows"]]
            for c in json.loads(context_path.read_text())
        }
        if context_path.exists()
        else {}
    )
    candidates = (
        [args.run_directory.resolve() / "manifest.json"]
        if args.run_directory
        else sorted(args.sequences.glob("*/*/manifest.json"))
    )
    for manifest in candidates:
        saved = json.loads(manifest.read_text())
        if args.model and saved["model"] != args.model:
            continue
        if (saved["purpose"] == "engineering") != args.engineering:
            continue
        try:
            if args.engineering:
                if any(
                    not (ROOT / p).exists() or sha256(ROOT / p) != digest
                    for p, digest in saved["code"].items()
                ):
                    raise ValueError("Engineering source code changed")
                status = {}
            else:
                saved, status = validate_run(
                    ROOT,
                    manifest.parent,
                    model=args.model,
                    expected_contexts=expected_contexts,
                    allow_partial=args.allow_partial,
                )
        except (ValueError, FileNotFoundError) as exc:
            rejected.append({"manifest": str(manifest), "reason": str(exc)})
            continue
        if saved["model"] in contracts:
            raise ValueError("Multiple valid runs for one model; use --run-directory")
        contracts[saved["model"]] = {
            "run": manifest.parent.name,
            "status": status,
            "mask_policy": saved.get("mask_policy", "native_pixel_mask_v1"),
            "input_population": saved.get("input_population"),
            "legacy_scope": "status context count checked; input-ledger hashes were not recorded at extraction"
            if not saved.get("input_population")
            else None,
        }
        accepted.append(manifest)
    if not accepted:
        raise ValueError(
            "No accepted extraction runs; existing outputs were not changed: "
            + json.dumps(rejected)
        )
    for manifest in accepted:
        saved = json.loads(manifest.read_text())
        model = saved["model"]
        if args.model and model != args.model:
            continue
        if (saved["purpose"] == "engineering") != args.engineering:
            continue
        # Stale adapters never silently mingle with current representations.
        if any(
            not (ROOT / p).exists() or sha256(ROOT / p) != digest
            for p, digest in saved["code"].items()
        ):
            continue
        source_hashes[str(manifest.relative_to(ROOT))] = sha256(manifest)
        for receipt in sorted(manifest.parent.glob("*/*/*.json")):
            r = json.loads(receipt.read_text())
            path = receipt.with_suffix(".npz")
            if r.get("status") != "finite_sequence":
                continue
            try:
                if sha256(path) != r["sha256"]:
                    raise ValueError("Embedding checksum differs")
                meta = r["identity"]
                frames = meta["frames"]
                first = frames[0]
                if meta["run"] != manifest.parent.name:
                    raise ValueError("Patch belongs to a different extraction run")
                if not args.engineering and context_windows:
                    if (
                        meta["context_id"] not in context_windows
                        or [f["window"]["id"] for f in frames]
                        != context_windows[meta["context_id"]]
                    ):
                        raise ValueError("Patch context differs from intended input population")
                with np.load(path) as data:
                    vector = data["embedding"].copy()
                    valid = data["valid"].copy()
                if (
                    valid.ndim != 3
                    or valid.shape[0] != len(frames)
                    or not np.isfinite(vector).all()
                ):
                    raise ValueError("Invalid sequence arrays")
                # Exact source-tile support excludes padding outside that tile.
                source = first["sources"][0]["relative_path"]
                # Metadata patch bounds can extend beyond the tile; mask already
                # excludes padding. Construct only the finite tile grid here.
                tile_id = Path(source).stem
                tile_x, tile_y = map(int, tile_id.split("_"))
                bounds = [tile_x, tile_y, tile_x + 9600, tile_y + 9600]
                for c in catchments.itertuples():
                    if not c.geometry.intersects(box(*first["bounds"])):
                        continue
                    key = (model, manifest.parent.name, meta["context_id"], c.gauge)
                    if key not in groups:
                        groups[key] = {
                            "vectors": [],
                            "weights": [],
                            "areas": np.zeros(len(frames)),
                            "common_area": 0.0,
                            "full_area": c.geometry.area,
                            "kind": meta["kind"],
                            "readout": meta["temporal_readout"],
                            "window_ids": [f["window"]["id"] for f in frames],
                            "patches": set(),
                        }
                    group = groups[key]
                    if tuple(group["window_ids"]) != tuple(f["window"]["id"] for f in frames):
                        raise ValueError("Mismatched context slots")
                    token = (tile_id, first["row"], first["col"])
                    if token in group["patches"]:
                        raise ValueError("Duplicate spatial patch support")
                    weightfile = cache / f"{c.gauge}_{tile_id}_{int(first['resolution_m'])}.npz"
                    if weightfile.exists():
                        with np.load(weightfile) as data:
                            weights = data["area_m2"]
                    else:
                        weights = pixel_area_weights(c.geometry, bounds, first["resolution_m"])
                        np.savez_compressed(weightfile, area_m2=weights)
                    per_frame = np.array(
                        [observed_patch_area(weights, m, first["row"], first["col"]) for m in valid]
                    )
                    common = observed_patch_area(weights, valid.all(0), first["row"], first["col"])
                    mean = float(per_frame.mean())
                    if mean == 0:
                        continue
                    group["patches"].add(token)
                    group["vectors"].append(vector)
                    group["weights"].append(mean)
                    group["areas"] += per_frame
                    group["common_area"] += common
                    patch_areas.append(
                        {
                            "model": model,
                            "run": manifest.parent.name,
                            "context_id": meta["context_id"],
                            "gauge": c.gauge,
                            "tile": tile_id,
                            "row": first["row"],
                            "col": first["col"],
                            "observed_mean_area_m2": mean,
                            "common_area_m2": common,
                        }
                    )
                    source_hashes[str(receipt.relative_to(ROOT))] = sha256(receipt)
            except Exception as e:
                errors.append({"path": str(receipt), "error": f"{type(e).__name__}: {e}"})
    coverage = []
    representations = {}
    for (model, run, context, gauge), g in groups.items():
        if not g["vectors"]:
            continue
        vector, fraction = aggregate_vectors(g["vectors"], g["weights"], g["full_area"])
        if (g["areas"] > g["full_area"] * (1 + 1e-7)).any():
            raise ValueError("Frame coverage exceeds catchment area")
        status = (
            "available_partial_or_full_area"
            if (g["areas"] > 0).all()
            else "some_frame_no_catchment_observation"
        )
        coverage.append(
            {
                "model": model,
                "run": run,
                "context_id": context,
                "catchment_gauge": gauge,
                "kind": g["kind"],
                "status": status,
                "temporal_readout": g["readout"],
                "n_frames": len(g["areas"]),
                "patches": len(g["vectors"]),
                "observed_mean_fraction": fraction,
                "observed_min_fraction": float(g["areas"].min() / g["full_area"]),
                "observed_common_fraction": g["common_area"] / g["full_area"],
                "frame_area_m2": g["areas"].tolist(),
                "window_ids": g["window_ids"],
            }
        )
        if status == "available_partial_or_full_area":
            representations.setdefault(model, []).append(
                {
                    "run": run,
                    "context_id": context,
                    "catchment_gauge": gauge,
                    "kind": g["kind"],
                    "observed_mean_fraction": fraction,
                    **{f"e{i:04d}": float(v) for i, v in enumerate(vector)},
                }
            )
    if not representations:
        raise ValueError("No usable representations; existing outputs were not changed")
    if errors and not args.allow_partial:
        raise ValueError(
            "Aggregation errors; existing outputs were not changed: " + json.dumps(errors[:5])
        )
    for model, rows in representations.items():
        pd.DataFrame(rows).to_parquet(target / f"{model}.parquet", index=False)
    pd.DataFrame(coverage).to_parquet(target / "coverage.parquet", index=False)
    pd.DataFrame(patch_areas).to_parquet(target / "patch_areas.parquet", index=False)
    outputs = {p.name: sha256(p) for p in target.glob("*.parquet")}
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "engineering": args.engineering,
        "partial": bool(args.allow_partial),
        "selected_runs": contracts,
        "rejected_runs": rejected,
        "outputs_sha256": outputs,
        "catchments_sha256": geometry_hash,
        "contexts_by_model": {m: len(v) for m, v in representations.items()},
        "source_sha256": source_hashes,
        "errors": errors,
        "weighting": "Mean observed area across fixed calendar slots; per-frame and common-area coverage retained. Full catchment remains denominator.",
        "interpretation": "Contextual patch-feature proxy: pixels outside a catchment can influence its overlapping patch vector.",
    }
    (target / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "source_sha256"}, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
