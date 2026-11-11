#!/usr/bin/env python3
"""Stream full native-grid external predictions from six frozen final states.

No external labels are read or scored here. All three seeds of one pipeline
share each image read; native heads share the frozen encoder pass. Completed
tile products are hash-receipted and archived to Azure with readback.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_copernicus import CopernicusRadarChange, normalize_radar
from applied_unet import StandardUNet
from limburg_chapter_grid import patch_metadata, stitch_probabilities, windows

OUT = ROOT / "results/limburg_chapter_sized_v1/external"
FINAL = ROOT / "results/limburg_chapter_sized_v1/final_source"
AUDIT = ROOT / "data/processed/limburg_chapter_geoid_audit_v1/tile_audit.parquet"
TRIPLET_AUDIT = ROOT / "data/processed/limburg_chapter_triplet_audit_v1/tile_status.parquet"
SEEDS = (42, 1729, 31415)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tile_io():
    spec = importlib.util.spec_from_file_location("chapter_tile_io", ROOT / "scripts/232_chapter_tile_infer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed_models(kind: str) -> dict[int, Path]:
    paths = {}
    for seed in SEEDS:
        folder = FINAL / f"{kind}-{seed}"
        model = folder / "model.pt"
        record = json.loads((folder / "complete.json").read_text())
        if record["model_sha256"] != sha256(model) or record["manifest_sha256"] != sha256(folder / "manifest.json"):
            raise ValueError(f"Unverified final source state: {kind}-{seed}")
        paths[seed] = model
    return paths


def load_models(kind: str, checkpoints: dict[int, Path], device: str):
    models = {}
    for seed, path in checkpoints.items():
        model = CopernicusRadarChange() if kind == "native" else StandardUNet(4, 3)
        state = torch.load(path, map_location="cpu", weights_only=True)
        result = model.load_state_dict(state, strict=kind != "native")
        if kind == "native":
            if result.unexpected_keys or any(not k.startswith("encoder.") for k in result.missing_keys):
                raise ValueError(f"Native head state invalid: {seed}")
            if seed != SEEDS[0]:
                model.encoder = torch.nn.Identity()  # all heads share seed-42's identical frozen encoder
        model.eval()
        model.to(device)
        if kind == "native" and seed == SEEDS[0]:
            model.encoder.cpu()
        models[seed] = model
    return models


def predict(raw: np.ndarray, transform, crs, times, kind: str, models: dict,
            device: str) -> tuple[dict[int, np.ndarray], np.ndarray]:
    normalized, valid = normalize_radar(raw)
    positions = windows(raw.shape[1], raw.shape[2])
    batch_size = 1 if kind == "native" else 4
    pieces = {seed: [] for seed in SEEDS}
    with torch.inference_mode():
        for start in range(0, len(positions), batch_size):
            group = positions[start:start+batch_size]
            array = np.stack([normalized[:, top:top+224, left:left+224] for top, left in group])
            x = torch.from_numpy(array).to(device)
            if kind == "native":
                meta = np.stack([patch_metadata(transform, crs, top, left, 224, *times) for top, left in group])
                features = models[SEEDS[0]].frozen_features(x, torch.from_numpy(meta).to(device))
            for seed, model in models.items():
                logits = model.forward_features(features)[0] if kind == "native" else model(x)
                values = torch.softmax(logits, dim=1).cpu().numpy()
                for (top, left), prob in zip(group, values, strict=True):
                    prob[:, ~valid[top:top+224, left:left+224]] = np.nan
                    pieces[seed].append((top, left, prob))
    result = {}
    for seed, parts in pieces.items():
        probabilities, coverage = stitch_probabilities(parts, raw.shape[1], raw.shape[2])
        if not np.array_equal(coverage, valid):
            raise ValueError("Stitched support differs from radar support")
        result[seed] = probabilities
    return result, valid


def archived_index() -> dict[str, str]:
    records = {}
    for path in (OUT / "archives").glob("*.json"):
        record = json.loads(path.read_text())
        if record.get("status") != "remote_readback_verified":
            raise ValueError(f"Unverified Azure archive: {path}")
        for name, digest in record["members"].items():
            if name in records and records[name] != digest:
                raise ValueError(f"Conflicting archive membership: {name}")
            records[name] = digest
    return records


def verified_receipt(path: Path, archive: dict[str, str], expected: dict | None = None) -> bool:
    if not path.exists():
        return False
    receipt = json.loads(path.read_text())
    if expected is not None and any(receipt.get(key) != value for key, value in expected.items()):
        raise ValueError(f"Prediction receipt belongs to different inputs/model: {path}")
    if not receipt.get("files"):
        raise ValueError(f"Empty prediction receipt: {path}")
    for name, digest in receipt["files"].items():
        local = OUT / name
        if local.exists():
            if sha256(local) != digest:
                raise ValueError(f"Changed prediction: {local}")
        elif archive.get(name) != digest:
            raise ValueError(f"Prediction missing locally and from verified archive: {name}")
    return True


def save_one(name: str, probabilities: np.ndarray, valid: np.ndarray) -> str:
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if probabilities.shape != (3, *valid.shape):
        raise ValueError("Three-class probability map and valid grid differ")
    if not np.isfinite(probabilities[:, valid]).all():
        raise ValueError("Nonfinite probabilities on radar-valid pixels")
    if np.isfinite(probabilities[:, ~valid]).any():
        raise ValueError("Unknown pixels carry finite probabilities")
    if np.any(np.abs(probabilities[:, valid].sum(axis=0) - 1) > 1e-3):
        raise ValueError("Class probabilities do not sum to one")
    predicted = np.where(valid, probabilities.argmax(axis=0), 255).astype(np.uint8)
    partial = target.with_suffix(".partial.npz")
    np.savez_compressed(partial, probability=probabilities.astype(np.float16),
                        prediction=predicted, radar_valid=valid)
    partial.replace(target)
    return sha256(target)


def offload(max_groups: int = 100) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/238_archive_chapter_predictions.py"),
                    "--max-groups", str(max_groups)], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["native", "unet"], required=True)
    parser.add_argument("--device", choices=["mps", "cpu"], default="mps")
    parser.add_argument("--limit", type=int, help="Bounded engineering run; never a reported event sample")
    args = parser.parse_args()
    torch.set_num_threads(2)
    checkpoints = completed_models(args.model)
    checkpoint_hashes = {str(seed): sha256(path) for seed, path in checkpoints.items()}
    audit = pd.read_parquet(AUDIT)
    pairs = pd.read_parquet(TRIPLET_AUDIT)
    if len(audit) != 1301 or len(pairs) != 915 or (pairs.status == "verified").sum() != 913:
        raise ValueError("Target acquisition census changed")
    delivered = [("delivered", f"{r.event_id}-{r.tile_id}-{r.bbox_id}", ["p0"])
                 for r in audit.itertuples()]
    harmonized = [("ee", row.key, ["p0", "p1"])
                  for row in pairs.itertuples() if row.status == "verified"]
    jobs = delivered + harmonized
    if args.limit is not None:
        jobs = jobs[:args.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / "results/applied_study_v3/.mps-owner.lock").open("a")
    if args.device == "mps":
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    models = load_models(args.model, checkpoints, args.device)
    source = tile_io()
    archive = archived_index()
    total = len(jobs)
    for completed, (dataset, key, references) in enumerate(jobs, 1):
        event_id = key.split("-")[0]
        receipt_path = OUT / "receipts" / args.model / dataset / event_id / f"{key}.json"
        expected = {"model": args.model, "key": key, "dataset": dataset,
                    "references": references, "seeds": list(SEEDS),
                    "checkpoint_sha256": checkpoint_hashes}
        if verified_receipt(receipt_path, archive, expected):
            continue
        if shutil.disk_usage(ROOT).free < 55 * 1024**3:
            offload()
            archive = archived_index()
            if shutil.disk_usage(ROOT).free < 55 * 1024**3:
                raise RuntimeError("Disk reserve remains too low after Azure offload")
        files = {}
        coverages = {}
        inputs = {}
        for reference in references:
            raw, transform, crs, times, provenance = source.input_tile(key, dataset, reference)
            outputs, valid = predict(raw, transform, crs, times, args.model, models, args.device)
            coverages[reference] = int(valid.sum())
            inputs[reference] = provenance
            for seed, probabilities in outputs.items():
                name = f"predictions/{args.model}/{dataset}/{event_id}/{key}-{reference}-{seed}.npz"
                files[name] = save_one(name, probabilities, valid)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt = {"status": "complete_unscored", "key": key, "dataset": dataset,
                   "model": args.model, "seeds": list(SEEDS), "references": references,
                   "coverage_pixels": coverages, "inputs": inputs,
                   "checkpoint_sha256": checkpoint_hashes,
                   "files": files, "windows_per_reference": 25,
                   "runner_sha256": sha256(Path(__file__)), "completed_unix": time.time()}
        partial = receipt_path.with_suffix(".partial")
        partial.write_text(json.dumps(receipt, indent=2) + "\n")
        partial.replace(receipt_path)
        if completed % 25 == 0 or completed == total:
            print(json.dumps({"model": args.model, "completed": completed,
                              "total": total, "dataset": dataset, "key": key,
                              "free_gib": round(shutil.disk_usage(ROOT).free / 1024**3, 2)}), flush=True)
        if completed % 100 == 0 or shutil.disk_usage(ROOT).free < 80 * 1024**3:
            offload()
            archive = archived_index()
    if args.limit is None:
        offload()
        archive = archived_index()
        if sum(1 for dataset, key, _ in jobs if verified_receipt(
            OUT / "receipts" / args.model / dataset / key.split("-")[0] / f"{key}.json", archive)) != total:
            raise ValueError("Incomplete external prediction census")
        (OUT / f"{args.model}-complete.json").write_text(json.dumps({
            "status": "full_external_predictions_complete", "jobs": total,
            "checkpoints": {seed: sha256(path) for seed, path in checkpoints.items()},
            "verified_archives": len(list((OUT / "archives").glob("*.json")))} , indent=2) + "\n")


if __name__ == "__main__":
    main()
