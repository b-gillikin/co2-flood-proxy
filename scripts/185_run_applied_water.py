"""Profile or fit one named spatial-water task on explicit event-held-out rows.

Training is never inferred from a successful backbone load. Profile uses real
source imagery but is an engineering check, not an accuracy result. Full fits
retain every eligible test chip, including valid dry patches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import resource
import shutil
import subprocess
import sys
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)

import numpy as np
import pandas as pd
import rasterio
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

from applied_spatial_models import (
    CompactUNet,
    GalileoRadar,
    GalileoSpatialProbe,
    prithvi,
    terramind,
)
from applied_water import (
    PRITHVI_S2,
    audit_partitions,
    class_scores,
    confusion,
    galileo_radar_norm,
    valid_labels,
)

DATA = ROOT / "data/raw/limburg_applied_tasks/sen1floods11"
PARTITIONS = ROOT / "results/applied_study_v1/evaluation"
TM_S2_MEAN = [
    2357.089,
    2137.385,
    2018.788,
    2082.986,
    2295.651,
    2854.537,
    3122.849,
    3040.560,
    3306.481,
    1473.847,
    506.070,
    2472.825,
    1838.929,
]
TM_S2_STD = [
    1624.683,
    1675.806,
    1557.708,
    1833.702,
    1823.738,
    1733.977,
    1732.131,
    1679.732,
    1727.26,
    1024.687,
    442.165,
    1331.411,
    1160.419,
]


def standardize(x, mean, std):
    return (x - np.array(mean, dtype=np.float32)[:, None, None]) / np.array(std, dtype=np.float32)[
        :, None, None
    ]


@lru_cache(maxsize=2)
def read_chip(chip, task=None):
    result = []
    for layer in ["LabelHand", "S1Hand", "S2Hand"]:
        if (task == "galileo" and layer == "S2Hand") or (task == "prithvi" and layer == "S1Hand"):
            result.append(None)
            continue
        with rasterio.open(DATA / layer / f"{chip}_{layer}.tif") as ds:
            result.append(ds.read())
    return result[0][0], result[1], result[2]


class Chips(Dataset):
    def __init__(self, rows, task, augment=False, feature_cache=None):
        self.rows, self.task, self.augment = rows.reset_index(drop=True), task, augment
        self.parts = 64 if task == "galileo" else 1
        self.feature_cache = feature_cache
        if feature_cache:
            index = json.loads((feature_cache / "index.json").read_text())
            self.feature_records = {r["chip"]: r for r in index["files"]}

    def __len__(self):
        return len(self.rows) * self.parts

    def __getitem__(self, index):
        row = self.rows.iloc[index // self.parts]
        if self.task == "galileo":
            from applied_io_cache import galileo_features, galileo_source

            part = index % 64
            top, left = (part // 8) * 64, (part % 8) * 64
            label, raw = galileo_source(str(DATA), row.chip)
            item = dict(
                y=torch.from_numpy(label[top : top + 64, left : left + 64].astype(np.int64)),
                chip=row.chip,
                event=row.event,
                part=part,
                month=datetime.strptime(row.s1_date.replace("/", "-"), "%Y-%m-%d").month - 1,
            )
            if self.feature_cache:
                item.update(
                    x=torch.empty(0),
                    features=torch.from_numpy(
                        galileo_features(str(self.feature_cache), row.chip)[part].copy()
                    ),
                )
            else:
                item["x"] = torch.from_numpy(raw[:, top : top + 64, left : left + 64].copy())
            return item
        label, s1, s2 = read_chip(row.chip, self.task)
        if self.task == "terramind":
            y = valid_labels(label, s1=s1, s2=s2)
            x = np.concatenate(
                [
                    standardize(s2, TM_S2_MEAN, TM_S2_STD),
                    standardize(s1, [-12.599, -20.293], [5.195, 5.890]),
                ]
            )
        elif self.task == "galileo":
            y = valid_labels(label, s1=s1)
            x = galileo_radar_norm(s1)
        else:
            optical = s2[PRITHVI_S2]
            y = valid_labels(label, s2=optical)
            # Equivalent to source scaling .0001 then normalization using the
            # correspondingly scaled Prithvi V2 means/stds.
            x = standardize(
                optical, [1087, 1342, 1433, 2734, 1958, 1363], [2248, 2179, 2178, 1850, 1242, 1049]
            )
        part = index % self.parts
        top, left = (part // 8) * 64, (part % 8) * 64
        if self.parts > 1:
            x = x[:, top : top + 64, left : left + 64]
            y = y[top : top + 64, left : left + 64]
        fill = 0.5 if self.task == "galileo" else 0
        x = np.nan_to_num(x, nan=fill, posinf=fill, neginf=fill)
        if self.augment:
            k = random.randrange(4)
            x = np.rot90(x, k, axes=(-2, -1))
            y = np.rot90(y, k)
            if random.random() < 0.5:
                x = x[..., ::-1]
                y = y[..., ::-1]
        x = torch.from_numpy(x.copy()).float()
        y = torch.from_numpy(y.copy()).long()
        if self.task == "prithvi":
            x = F.interpolate(x[None], size=(224, 224), mode="bilinear", align_corners=False)[0]
        date = row.s2_date if self.task == "prithvi" else row.s1_date
        d = datetime.strptime(date.replace("/", "-"), "%Y-%m-%d")
        temporal = torch.tensor([[d.year, d.timetuple().tm_yday]], dtype=torch.float32)
        location = torch.tensor(
            [(row.top + row.bottom) / 2, (row.left + row.right) / 2], dtype=torch.float32
        )
        return dict(
            x=x,
            y=y,
            chip=row.chip,
            event=row.event,
            part=part,
            month=d.month - 1,
            temporal=temporal,
            location=location,
        )


def forward(model, batch, task, learner, device):
    x = batch["x"].to(device)
    if learner != "native":
        return model(x)
    if task == "terramind":
        model.encoder.eval()
        return model({"S2L1C": x[:, :13], "S1GRD": x[:, 13:]}).output
    if task == "galileo":
        if "features" in batch:
            return model(batch["features"].to(device))
        return model(x, batch["month"].to(device))
    return model(
        x,
        temporal_coords=batch["temporal"].to(device),
        location_coords=batch["location"].to(device),
    ).output


def loss_for(logits, label, task, learner):
    if logits.shape[-2:] != label.shape[-2:]:
        label = F.interpolate(label[:, None].float(), size=logits.shape[-2:], mode="nearest")[
            :, 0
        ].long()
    if not (label >= 0).any():
        return None
    if task == "terramind" and learner == "native":
        import segmentation_models_pytorch as smp

        return smp.losses.DiceLoss("multiclass", ignore_index=-1)(logits, label)
    return F.cross_entropy(logits, label, ignore_index=-1)


def score(model, loader, args, device, destination=None):
    model.eval()
    matrices = {}
    predictions = {}
    losses = []
    with torch.no_grad():
        for batch in loader:
            logits = forward(model, batch, args.task, args.learner, device)
            loss = loss_for(logits, batch["y"].to(device), args.task, args.learner)
            if loss is not None:
                losses.append(float(loss))
            logits = F.interpolate(
                logits, size=batch["y"].shape[-2:], mode="bilinear", align_corners=False
            )
            predicted = logits.argmax(1).cpu().numpy()
            for i, event in enumerate(batch["event"]):
                label = batch["y"][i].numpy()
                matrices.setdefault(event, np.zeros((2, 2), dtype=np.int64))
                matrices[event] += confusion(label, predicted[i])
                if destination is not None:
                    chip = batch["chip"][i]
                    part = int(batch["part"][i])
                    top, left = (part // 8) * 64, (part % 8) * 64
                    predictions.setdefault(chip, np.full((512, 512), 255, dtype=np.uint8))
                    if args.task == "galileo":
                        predictions[chip][top : top + 64, left : left + 64] = np.where(
                            label >= 0, predicted[i], 255
                        )
                    else:
                        predictions[chip] = np.where(label >= 0, predicted[i], 255).astype(np.uint8)
    if destination is not None:
        destination.mkdir(parents=True, exist_ok=True)
        for chip, prediction in predictions.items():
            np.savez_compressed(
                destination / f"{chip}.npz", prediction=prediction, unknown_code=255
            )
    scores = {
        e: (float(v) if np.isfinite(v) else None)
        for e, m in matrices.items()
        if (v := class_scores(m)["iou"][1]) is not None
    }
    finite = [v for v in scores.values() if v is not None]
    return dict(
        event_water_iou=scores,
        mean_event_water_iou=float(np.mean(finite)) if finite else None,
        mean_batch_loss=float(np.mean(losses)) if losses else None,
        confusion={e: m.tolist() for e, m in matrices.items()},
    )


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--task", choices=["terramind", "galileo", "prithvi"], required=True)
    p.add_argument("--learner", choices=["native", "unet", "linear"], default="native")
    p.add_argument("--mode", choices=["profile", "train"], default="profile")
    p.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    p.add_argument("--fold")
    p.add_argument("--budget", type=float, choices=[1.0, 0.2, 0.05], default=1.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int)
    p.add_argument("--lr", type=float)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument(
        "--feature-cache", type=Path, help="Completed native Galileo float32 spatial-token cache"
    )
    p.add_argument(
        "--profile-batches",
        type=int,
        default=3,
        help="0 profiles a complete training epoch, retaining no fitted model",
    )
    args = p.parse_args()
    if args.feature_cache:
        if args.task != "galileo" or args.learner != "native":
            p.error("Cached spatial tokens belong to native Galileo only")
        index = json.loads((args.feature_cache / "index.json").read_text())
        if index["status"] != "completed" or index["completed"] != 446:
            raise ValueError("Incomplete spatial token cache")
        for name, digest in index["source_hashes"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Feature cache source changed: " + name)
        for row in index["files"]:
            path = args.feature_cache / f"{row['chip']}.npy"
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError("Feature cache bytes changed")
        args.feature_cache = str(args.feature_cache.resolve())
    if args.task == "prithvi" and args.learner == "native" and args.batch_size < 2:
        p.error(
            "Prithvi UperNet training uses BatchNorm on pooled 1x1 features; use batch-size >=2"
        )
    if args.mode == "train" and not args.fold:
        p.error("Choose a named prepared held-event fold for training")
    torch.set_num_threads(1)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    inventory = pd.read_parquet(PARTITIONS / "sen1-chip-inventory.parquet")
    folds = pd.read_parquet(PARTITIONS / "sen1-grouped-folds.parquet")
    audit_partitions(folds)
    args.fold = args.fold or sorted(folds.fold.unique())[0]
    if args.fold not in set(folds.fold):
        p.error("Unknown held-event fold")
    subset = pd.read_parquet(PARTITIONS / "sen1-label-subsets.parquet")
    selected = set(
        subset.loc[
            (subset.fold == args.fold)
            & (subset.seed == args.seed)
            & (subset.budget == args.budget),
            "chip",
        ]
    )
    if not selected:
        raise ValueError("Empty or unprepared training subset")
    parts = {}
    for role in ["train", "valid", "test"]:
        ids = set(folds.loc[(folds.fold == args.fold) & (folds.role == role), "chip"])
        if role == "train":
            ids &= selected
        parts[role] = inventory.loc[inventory.chip.isin(ids)].copy()
    out = (
        ROOT
        / "results/applied_study_v1"
        / ("profiles" if args.mode == "profile" else "fits")
        / f"{args.task}-{args.learner}-{args.fold}-{args.budget:g}-{args.seed}-{args.device}-b{args.batch_size}"
    )
    out.mkdir(parents=True, exist_ok=True)
    if (out / "complete.json").exists():
        prior = json.loads((out / "manifest.json").read_text())
        if prior["arguments"] != vars(args):
            raise RuntimeError(
                "Existing run arguments differ; preserve it and choose a separate run directory"
            )
        for name, digest in prior["source_hashes"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError(
                    "Existing run used different sources; do not reuse its completion marker"
                )
        print("Already complete:", out)
        return
    if (out / "manifest.json").exists():
        raise RuntimeError(
            "Incomplete earlier run retained here; inspect rather than overwrite its provenance/checkpoints"
        )
    if args.device == "mps":
        active = json.loads(
            (ROOT / "results/limburg_individual_experiments_v1/queue/progress.json").read_text()
        )
        if any(
            t["status"] == "running" and t.get("resource") == "mps"
            for t in active["tasks"].values()
        ):
            raise RuntimeError("Existing MPS worker retains device ownership")
    if shutil.disk_usage(ROOT).free < 55 * 1024**3:
        raise RuntimeError("Insufficient working headroom above reserve")
    device = torch.device(args.device)
    start = time.perf_counter()
    if args.learner == "native":
        model = (
            GalileoSpatialProbe()
            if args.feature_cache
            else {"terramind": terramind, "galileo": GalileoRadar, "prithvi": prithvi}[args.task]()
        )
    else:
        channels = {"terramind": 15, "galileo": 2, "prithvi": 6}[args.task]
        model = CompactUNet(channels) if args.learner == "unet" else nn.Conv2d(channels, 2, 1)
    model = model.to(device)
    model_setup_s = time.perf_counter() - start
    epochs = args.epochs or (100 if args.task == "terramind" else 50)
    lr = args.lr or {"terramind": 2e-5, "galileo": 1e-3, "prithvi": 5e-5}[args.task]
    optimizer = torch.optim.AdamW(
        [v for v in model.parameters() if v.requires_grad],
        lr=lr,
        weight_decay=0.05 if args.task == "prithvi" else 0.01,
    )
    scheduler = (
        torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=5)
        if args.task == "terramind"
        else torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        if args.task == "prithvi"
        else None
    )
    train = DataLoader(
        Chips(
            parts["train"],
            args.task,
            augment=args.task != "galileo",
            feature_cache=Path(args.feature_cache) if args.feature_cache else None,
        ),
        batch_size=args.batch_size,
        num_workers=0,
        shuffle=True,
        drop_last=args.task == "prithvi" and args.batch_size > 1,
    )
    weight = {
        "terramind": "models/terramind/TerraMind_v1_tiny.pt",
        "galileo": "models/galileo/models/nano/encoder.pt",
        "prithvi": "models/prithvi/Prithvi_EO_V2_tiny_TL.pt",
    }[args.task]
    source_files = [
        Path(__file__),
        ROOT / "src/applied_spatial_models.py",
        ROOT / "src/applied_water.py",
        PARTITIONS / "sen1-grouped-folds.parquet",
        PARTITIONS / "sen1-label-subsets.parquet",
        ROOT / "results/applied_study_v1/acquisition/sen1-files.jsonl",
    ]
    if args.learner == "native":
        source_files.append(ROOT / "data/raw/limburg_dynamic_model_weights" / weight)
    if args.feature_cache:
        source_files.append(Path(args.feature_cache) / "index.json")
    manifest = dict(
        arguments=vars(args),
        epochs=epochs,
        lr=lr,
        parameters=sum(v.numel() for v in model.parameters()),
        trainable_parameters=sum(v.numel() for v in model.parameters() if v.requires_grad),
        partitions={
            k: dict(chips=len(v), events=sorted(v.event.unique())) for k, v in parts.items()
        },
        source_hashes={
            str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in source_files
        },
        python=sys.version,
        torch=torch.__version__,
        device=str(device),
        precision="float32",
        git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        engineering_only=args.mode == "profile",
        concurrency_note="Existing extraction may compete; this is not an isolated speed benchmark",
        model_setup_s=model_setup_s,
        feature_extraction_cost_record=str(Path(args.feature_cache) / "index.json")
        if args.feature_cache
        else None,
    )
    manifest["training_drop_last"] = args.task == "prithvi" and args.batch_size > 1
    manifest["evaluation_drop_last"] = False
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    times = []
    best = -float("inf")
    steps = 0
    max_sampled_mps_bytes = 0
    training_started = time.perf_counter()
    for epoch in range(1 if args.mode == "profile" else epochs):
        model.train()
        for i, batch in enumerate(train):
            if args.task == "galileo":
                progress = epoch + i / len(train)
                warmup = epochs * 0.1
                rate = (
                    lr * progress / warmup
                    if progress < warmup
                    else 1e-5
                    + (lr - 1e-5)
                    * 0.5
                    * (1 + math.cos(math.pi * (progress - warmup) / (epochs - warmup)))
                )
                for group in optimizer.param_groups:
                    group["lr"] = rate
            t = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            loss = loss_for(
                forward(model, batch, args.task, args.learner, device),
                batch["y"].to(device),
                args.task,
                args.learner,
            )
            if args.device == "mps":
                max_sampled_mps_bytes = max(
                    max_sampled_mps_bytes, torch.mps.current_allocated_memory()
                )
            if loss is None:
                continue
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            if args.device == "mps":
                max_sampled_mps_bytes = max(
                    max_sampled_mps_bytes, torch.mps.current_allocated_memory()
                )
            if args.device == "mps":
                torch.mps.synchronize()
            times.append(time.perf_counter() - t)
            steps += 1
            if (
                args.mode == "profile"
                and args.profile_batches > 0
                and steps >= args.profile_batches
            ):
                break
        if args.mode == "profile":
            break
        validation = score(
            model,
            DataLoader(
                Chips(
                    parts["valid"],
                    args.task,
                    feature_cache=Path(args.feature_cache) if args.feature_cache else None,
                ),
                batch_size=1,
            ),
            args,
            device,
        )
        val = validation["mean_event_water_iou"]
        if scheduler is not None:
            if args.task == "terramind":
                scheduler.step(validation["mean_batch_loss"])
            else:
                scheduler.step()
        record = dict(epoch=epoch + 1, validation=validation, elapsed_s=time.perf_counter() - start)
        with (out / "epochs.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")
        torch.save(model.state_dict(), out / "last.pt")
        if val is not None and val > best:
            best = val
            torch.save(model.state_dict(), out / "best.pt")
        if shutil.disk_usage(ROOT).free < 52 * 1024**3:
            raise RuntimeError("Disk reserve approached; checkpoint retained")
    result = dict(
        status="engineering_profile_complete" if args.mode == "profile" else "fit_complete",
        steps=steps,
        batch_seconds=times if args.mode == "profile" else None,
        elapsed_s=time.perf_counter() - start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        fit_or_profile_loop_elapsed_s=time.perf_counter() - training_started,
        max_sampled_mps_allocated_bytes=max_sampled_mps_bytes if args.device == "mps" else None,
        mps_memory_interpretation="sampled after forward/loss and optimizer step; not guaranteed backend peak",
        interpretation="No accuracy claim from engineering profile"
        if args.mode == "profile"
        else "Single named held-event fit; consolidate paired event comparisons before chapter-level conclusions",
    )
    if args.mode == "profile":
        model.eval()
        batch = next(
            iter(
                DataLoader(
                    Chips(
                        parts["valid"],
                        args.task,
                        feature_cache=Path(args.feature_cache) if args.feature_cache else None,
                    ),
                    batch_size=args.batch_size,
                )
            )
        )
        t = time.perf_counter()
        with torch.no_grad():
            forward(model, batch, args.task, args.learner, device)
        if args.device == "mps":
            torch.mps.synchronize()
        result["inference_batch_seconds"] = time.perf_counter() - t
        result["inference_batch_size"] = len(batch["chip"])
        result["inference_stage"] = (
            "cached frozen tokens to map" if args.feature_cache else "prepared image tensors to map"
        )
        result["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if args.mode == "train":
        model.load_state_dict(torch.load(out / "best.pt", map_location=device, weights_only=True))
        result["test"] = score(
            model,
            DataLoader(
                Chips(
                    parts["test"],
                    args.task,
                    feature_cache=Path(args.feature_cache) if args.feature_cache else None,
                ),
                batch_size=1,
            ),
            args,
            device,
            out / "predictions",
        )
    (out / "complete.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
