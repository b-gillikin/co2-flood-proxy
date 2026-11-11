#!/usr/bin/env python3
"""Resume a source-only final flood fit at epoch boundaries, never reading target labels."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import pickle
import random
import shutil
import sys
import time

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_copernicus import CopernicusRadarChange
from applied_evaluation import CompleteBatches
from applied_fast_data import CachedChips, fast_loss
from applied_unet import StandardUNet

CONFIG = ROOT / "config/limburg_chapter_final_fit_v1.json"
OUTPUT = ROOT / "results/limburg_chapter_sized_v1/final_source"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def trainable_state(model, kind: str):
    state = model.state_dict()
    if kind == "native":
        state = {k: v for k, v in state.items() if not k.startswith("encoder.")}
    return {key: value.detach().cpu() for key, value in state.items()}


def restore_state(model, state: dict, kind: str) -> None:
    result = model.load_state_dict(state, strict=kind != "native")
    if kind == "native" and (result.unexpected_keys or any(not k.startswith("encoder.") for k in result.missing_keys)):
        raise ValueError("Native resume state omitted non-encoder weights")


def checkpoint(path: Path, state: dict) -> None:
    partial = path.with_suffix(".partial")
    previous = path.with_name("checkpoint-previous.pt")
    torch.save(state, partial)
    if path.exists():
        path.replace(previous)
    partial.replace(path)


def resume(path: Path, manifest_sha: str) -> dict | None:
    for candidate in (path, path.with_name("checkpoint-previous.pt")):
        if not candidate.exists():
            continue
        try:
            state = torch.load(candidate, map_location="cpu", weights_only=False)
            if state["manifest_sha256"] == manifest_sha and state["completed_epoch"] >= 0:
                return state
        except (OSError, ValueError, KeyError, RuntimeError, pickle.UnpicklingError, EOFError):
            continue
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["native", "unet"], required=True)
    parser.add_argument("--seed", type=int, choices=[42, 1729, 31415], required=True)
    parser.add_argument("--device", choices=["mps", "cpu"], default="mps")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    torch.set_num_threads(2)
    cfg = json.loads(CONFIG.read_text())
    spec = cfg["models"][args.model]
    tensor_cache = ROOT / cfg["tensor_cache"]
    feature_cache = ROOT / spec["feature_cache"] if spec["feature_cache"] else None
    tensor_index = json.loads((tensor_cache / "index.json").read_text())
    if tensor_index["status"] != "complete" or len(tensor_index["rows"]) != 5000:
        raise ValueError("Incomplete pinned source tensor cache")
    if feature_cache:
        index = json.loads((feature_cache / "index.json").read_text())
        if index["status"] != "completed" or index["completed"] != 5000:
            raise ValueError("Incomplete frozen Copernicus feature cache")
    else:
        index = None
    rows = pd.read_parquet(ROOT / cfg["source_inventory"]).rename(columns={"record": "chip"})
    if len(rows) != 5000 or rows.chip.nunique() != 5000 or rows.event.nunique() != 20:
        raise ValueError("Source cohort changed")
    if set(rows.chip) != {r["chip"] for r in tensor_index["rows"]}:
        raise ValueError("Source and tensor cache identities differ")
    output = OUTPUT / f"{args.model}-{args.seed}"
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "model": args.model, "seed": args.seed, "device": args.device,
        "runner_sha256": sha256(Path(__file__)),
        "copernicus_adapter_sha256": sha256(ROOT / "src/applied_copernicus.py"),
        "unet_adapter_sha256": sha256(ROOT / "src/applied_unet.py"),
        "fast_data_sha256": sha256(ROOT / "src/applied_fast_data.py"),
        "config_sha256": sha256(CONFIG),
        "source_inventory_sha256": sha256(ROOT / cfg["source_inventory"]),
        "tensor_cache_index_sha256": sha256(tensor_cache / "index.json"),
        "feature_cache_index_sha256": sha256(feature_cache / "index.json") if feature_cache else None,
        "source_count": len(rows), "event_count": rows.event.nunique(),
        "source_only": True, "batch_size": cfg["batch_size"], "workers": args.workers,
        "torch": torch.__version__, "epochs": spec["epochs"],
        "learning_rate": spec["learning_rate"], "schedule_T_max": cfg["learning_rate_schedule_T_max"],
    }
    manifest_path = output / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("Existing final fit has a different manifest")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    manifest_sha = sha256(manifest_path)
    if shutil.disk_usage(ROOT).free < 52 * 1024**3:
        raise RuntimeError("Disk reserve approached before source fit")
    lock = (ROOT / "results/applied_study_v3/.mps-owner.lock").open("a")
    if args.device == "mps":
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    model = CopernicusRadarChange() if args.model == "native" else StandardUNet(4, 3)
    model.to(args.device)
    if args.model == "native":
        model.encoder.cpu()
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=spec["learning_rate"], weight_decay=cfg["weight_decay"], foreach=True,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg["learning_rate_schedule_T_max"])
    current = output / "checkpoint-current.pt"
    state = resume(current, manifest_sha)
    start_epoch = 0
    if state:
        restore_state(model, state["model"], args.model)
        optimizer.load_state_dict(state["optimizer"])
        scheduler.load_state_dict(state["scheduler"])
        start_epoch = state["completed_epoch"]
    dataset = CachedChips(rows, "copernicus", tensor_cache, feature_cache=feature_cache,
                          augment=False, seed=args.seed)
    loader = DataLoader(dataset, batch_sampler=CompleteBatches(len(dataset), cfg["batch_size"], args.seed),
                        num_workers=args.workers, persistent_workers=args.workers > 0,
                        multiprocessing_context="spawn" if args.workers else None)
    for epoch in range(start_epoch, spec["epochs"]):
        if shutil.disk_usage(ROOT).free < 52 * 1024**3:
            raise RuntimeError("Disk reserve approached; full-state checkpoint retained")
        random.seed(args.seed + epoch)
        np.random.seed(args.seed + epoch)
        torch.manual_seed(args.seed + epoch)
        model.train()
        dataset.set_epoch(epoch)
        # CompleteBatches is recreated for each epoch to match the source-CV
        # seed+epoch order; no examples are dropped.
        loader.batch_sampler.seed = args.seed + epoch
        started = time.perf_counter()
        examples = updates = skipped = 0
        loss_accumulator = torch.zeros((), device=args.device)
        invalid_loss = torch.zeros((), device=args.device, dtype=torch.bool)
        for batch in loader:
            examples += len(batch["chip"])
            if int(batch["valid_label_pixels"].sum()) == 0:
                skipped += len(batch["chip"])
                continue
            optimizer.zero_grad(set_to_none=True)
            if args.model == "native":
                result = model.forward_features(batch["features"].unbind(1))
            else:
                result = model(batch["x"].to(args.device))
            loss = fast_loss(result, batch["loss_y"].to(args.device), "copernicus", args.model)
            invalid_loss.logical_or_(~torch.isfinite(loss.detach()))
            loss.backward()
            optimizer.step()
            updates += 1
            loss_accumulator.add_(loss.detach() / len(loader))
        if examples != 5000:
            raise ValueError("Final source fit skipped examples")
        if bool(invalid_loss):
            raise ValueError(f"Nonfinite source loss at epoch {epoch + 1}")
        scheduler.step()
        record = {
            "manifest_sha256": manifest_sha, "completed_epoch": epoch + 1,
            "model": trainable_state(model, args.model),
            "optimizer": optimizer.state_dict(), "scheduler": scheduler.state_dict(),
            "torch_rng": torch.random.get_rng_state(),
            "numpy_rng": np.random.get_state(), "python_rng": random.getstate(),
        }
        checkpoint(current, record)
        progress = {"completed_epoch": epoch + 1, "total_epochs": spec["epochs"],
                    "examples": examples, "updates": updates, "skipped_examples": skipped,
                    "mean_batch_loss": float(loss_accumulator) * len(loader) / updates if updates else None,
                    "elapsed_epoch_s": time.perf_counter() - started,
                    "checkpoint_sha256": sha256(current)}
        (output / "progress.json").write_text(json.dumps(progress, indent=2) + "\n")
        print(json.dumps(progress), flush=True)
    final = output / "model.pt"
    if not final.exists():
        temp = final.with_suffix(".partial")
        torch.save(trainable_state(model, args.model), temp)
        temp.replace(final)
    (output / "complete.json").write_text(json.dumps({"model_sha256": sha256(final),
        "completed_epochs": spec["epochs"], "manifest_sha256": manifest_sha}, indent=2) + "\n")


if __name__ == "__main__":
    main()
