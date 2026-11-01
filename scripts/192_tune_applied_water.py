"""Validation-only equal-trial tuning, followed optionally by ONE selected test fit.

Use the same fold, chip-label budget, seed, batch size and epoch ceiling for
all learners within a task. Existing profile jobs are unchanged. Never call
185's train CLI for a learning-rate search: that CLI scores test after each fit.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import random
import resource
import shutil
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_evaluation import CompleteBatches, label_accounting
from applied_selection import learning_rates, select_trial


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--task", choices=["terramind", "galileo", "prithvi", "copernicus"], required=True
    )
    p.add_argument(
        "--learner", choices=["native", "unet", "unet_standard", "linear"], required=True
    )
    p.add_argument("--fold", required=True)
    p.add_argument("--budget", type=float, choices=[1.0, 0.2, 0.05], default=1.0)
    p.add_argument("--seed", type=int, choices=[42, 1729, 31415], default=42)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    p.add_argument("--epochs", type=int, help="Must be identical for all task learners")
    p.add_argument("--feature-cache", type=Path)
    p.add_argument("--output-root", type=Path, default=ROOT / "results/applied_study_v2/tuning")
    p.add_argument("--run", action="store_true", help="Without this, print the plan only")
    p.add_argument(
        "--evaluate-selected", action="store_true", help="Test only the validation winner"
    )
    a = p.parse_args()
    epochs = a.epochs if a.epochs is not None else (100 if a.task == "terramind" else 50)
    if epochs < 1 or a.batch_size < 2:
        p.error("Use positive epochs and batch-size >=2 for common task support")
    rates = learning_rates(a.task, a.learner)
    print(
        json.dumps(
            dict(
                task=a.task,
                learner=a.learner,
                rates=rates,
                epochs=epochs,
                candidate_test_evaluations=0,
                selected_test_evaluations=int(a.evaluate_selected),
            )
        )
    )
    if not a.run:
        return
    import numpy as np
    import pandas as pd
    import torch
    from torch import nn
    from torch.utils.data import DataLoader

    from applied_spatial_models import (
        CompactUNet,
        GalileoRadar,
        GalileoSpatialProbe,
        prithvi,
        terramind,
    )
    from applied_unet import StandardUNet
    from applied_water import audit_partitions

    spec = importlib.util.spec_from_file_location(
        "water_task", ROOT / "scripts/185_run_applied_water.py"
    )
    w = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(w)
    if a.task == "copernicus":
        import applied_change_task as w
        from applied_copernicus import CopernicusRadarChange
    torch.set_num_threads(1)
    if a.device == "mps":
        for queue in [
            "results/limburg_individual_experiments_v1/queue/progress.json",
            "results/applied_study_v1/profile_queue/progress.json",
        ]:
            state = json.loads((ROOT / queue).read_text())
            tasks = state.get("tasks", {})
            tasks = list(tasks.values()) if isinstance(tasks, dict) else tasks
            jobs = state.get("jobs", [])
            if any(
                t.get("status") == "running" and t.get("resource") == "mps" for t in tasks
            ) or any(t.get("status") == "running" for t in jobs):
                raise RuntimeError("Use the existing device queue; another worker may own MPS")
    if a.feature_cache:
        if (a.task, a.learner) != ("galileo", "native"):
            p.error("Cached features are for native Galileo only")
        index = json.loads((a.feature_cache / "index.json").read_text())
        if index["status"] != "completed" or index["completed"] != 446:
            raise ValueError("Incomplete feature cache")
        for name, digest in index["source_hashes"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Changed feature source: " + name)
        for row in index["files"]:
            if (
                hashlib.sha256((a.feature_cache / f"{row['chip']}.npy").read_bytes()).hexdigest()
                != row["sha256"]
            ):
                raise ValueError("Changed cached feature bytes")
    prefix = "radar-change" if a.task == "copernicus" else "sen1"
    inventory_name = (
        "radar-change-inventory.parquet"
        if a.task == "copernicus"
        else "sen1-chip-inventory.parquet"
    )
    inv = pd.read_parquet(w.PARTITIONS / inventory_name).rename(columns={"record": "chip"})
    folds = pd.read_parquet(w.PARTITIONS / f"{prefix}-grouped-folds.parquet")
    audit_partitions(folds)
    if a.fold not in set(folds.fold):
        raise ValueError("Unknown fold")
    subsets = pd.read_parquet(w.PARTITIONS / f"{prefix}-label-subsets.parquet")
    selected = set(
        subsets.loc[
            (subsets.fold == a.fold) & (subsets.seed == a.seed) & (subsets.budget == a.budget),
            "chip",
        ]
    )
    if not selected:
        raise ValueError("Empty training subset")
    rows = {}
    for role in ["train", "valid", "test"]:
        ids = set(folds.loc[(folds.fold == a.fold) & (folds.role == role), "chip"])
        rows[role] = inv[inv.chip.isin(ids & selected if role == "train" else ids)].copy()
    out = (
        a.output_root
        / f"{a.task}-{a.learner}-{a.fold}-{a.budget:g}-{a.seed}-{a.device}-b{a.batch_size}-e{epochs}"
    )
    out.mkdir(parents=True, exist_ok=False)
    sources = [
        Path(__file__),
        ROOT / "src/applied_selection.py",
        ROOT / "src/applied_evaluation.py",
        ROOT / "src/applied_unet.py",
        ROOT / "scripts/185_run_applied_water.py",
        ROOT / "src/applied_spatial_models.py",
        ROOT / "src/applied_water.py",
        *[
            w.PARTITIONS / n
            for n in [
                inventory_name,
                f"{prefix}-grouped-folds.parquet",
                f"{prefix}-label-subsets.parquet",
            ]
        ],
        ROOT
        / (
            "results/applied_study_v1/evaluation/radar-change-audit.json"
            if a.task == "copernicus"
            else "results/applied_study_v1/acquisition/sen1-files.jsonl"
        ),
    ]
    weights = {
        "terramind": "terramind/TerraMind_v1_tiny.pt",
        "galileo": "galileo/models/nano/encoder.pt",
        "prithvi": "prithvi/Prithvi_EO_V2_tiny_TL.pt",
        "copernicus": "copernicus_fm/CopernicusFM_ViT_base_varlang_e100.pth",
    }
    if a.task == "copernicus":
        sources += [
            ROOT / "src/applied_change_task.py",
            ROOT / "src/applied_copernicus.py",
            ROOT / "config/limburg_applied_tasks_v1.json",
        ]
    if a.learner == "native":
        sources.append(ROOT / "data/raw/limburg_dynamic_model_weights/models" / weights[a.task])
    if a.feature_cache:
        sources.append(a.feature_cache / "index.json")
    manifest = dict(
        arguments={k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()},
        rates=rates,
        epochs=epochs,
        selection="validation equal-event target-class IoU; first-trial tie",
        source_hashes={
            str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources
        },
        partitions={k: sorted(v.chip) for k, v in rows.items()},
        torch=torch.__version__,
        precision="float32",
        training_drop_last=False,
        batching="Complete shuffled batches; merge final singleton into preceding batch",
        label_accounting=label_accounting(
            rows,
            int(((folds.fold == a.fold) & (folds.role == "train")).sum()),
            len(rows["train"]) * (64 if a.task == "galileo" else 1),
        ),
        device=a.device,
        resource_caveat="Concurrent work affects wall time; process RSS is a cumulative high-water mark, not per-trial isolated peak",
        evaluation_drop_last=False,
        engineering_only=epochs != (100 if a.task == "terramind" else 50),
        epoch_budget_note="Nondefault epochs are a bounded engineering run, not the final comparison",
        loss="TerraMind Dice for all; Galileo/Prithvi CE; Copernicus native CE+.4aux, controls CE",
    )
    pixel_column = {
        "terramind": "paired_valid_labeled",
        "galileo": "radar_valid_labeled",
        "prithvi": "optical_valid_labeled",
        "copernicus": "valid_pixels",
    }[a.task]
    manifest["label_accounting"]["source_grid_labeled_pixels"] = {
        k: int(v[pixel_column].sum()) for k, v in rows.items()
    }
    manifest["label_accounting"]["pixel_note"] = (
        "Source-grid counts, not independent labels or annotation hours; Prithvi training targets are resampled"
    )
    if a.feature_cache:
        manifest["shared_feature_preparation"] = {
            k: index.get(k)
            for k in [
                "elapsed_s",
                "feature_seconds",
                "bytes",
                "peak_rss_bytes",
                "device",
                "threads",
            ]
        }
        manifest["shared_feature_cost_note"] = (
            "One-time frozen extraction across446 chips; do not multiply per head fit or omit from cold-start comparison. Held timing was measured under contention."
        )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    device = torch.device(a.device)
    args = SimpleNamespace(task=a.task, learner=a.learner)

    def loader(role, augment=False, epoch=0):
        dataset = w.Chips(rows[role], a.task, augment=augment, feature_cache=a.feature_cache)
        if role == "train":
            return DataLoader(
                dataset,
                batch_sampler=CompleteBatches(len(dataset), a.batch_size, a.seed + epoch),
                num_workers=0,
            )
        return DataLoader(
            dataset,
            batch_size=1,
            shuffle=False,
            drop_last=False,
            num_workers=0,
            generator=torch.Generator().manual_seed(a.seed + epoch),
        )

    def make_model():
        if a.learner == "native":
            if a.task == "copernicus":
                return CopernicusRadarChange()
            return (
                GalileoSpatialProbe()
                if a.feature_cache
                else {"terramind": terramind, "galileo": GalileoRadar, "prithvi": prithvi}[a.task]()
            )
        channels = {"terramind": 15, "galileo": 2, "prithvi": 6, "copernicus": 4}[a.task]
        classes = 3 if a.task == "copernicus" else 2
        if a.learner == "linear":
            return nn.Conv2d(channels, classes, 1)
        if a.learner == "unet_standard":
            return StandardUNet(channels, classes)
        model = CompactUNet(channels)
        model.head = nn.Conv2d(16, classes, 1)
        return model

    trials = []
    for i, lr in enumerate(rates):
        if shutil.disk_usage(ROOT).free < 55 * 1024**3:
            raise RuntimeError("Preserve disk reserve; completed candidates remain recorded")
        random.seed(a.seed)
        np.random.seed(a.seed)
        torch.manual_seed(a.seed)
        setup_start = time.perf_counter()
        try:
            model = make_model()
        except (ValueError, RuntimeError, ImportError) as exc:
            trials.append(
                dict(
                    trial=i,
                    lr=lr,
                    status="failed",
                    validation_iou=None,
                    error=f"{type(exc).__name__}: {exc}",
                    phase="model_initialization",
                    elapsed_s=time.perf_counter() - setup_start,
                )
            )
            (out / "trials.json").write_text(json.dumps(trials, indent=2))
            continue
        initial = hashlib.sha256()
        for parameter in model.parameters():
            if parameter.requires_grad:
                initial.update(parameter.detach().cpu().numpy().tobytes())
        initial_hash = initial.hexdigest()
        previous_initial = [
            r["initial_trainable_sha256"] for r in trials if "initial_trainable_sha256" in r
        ]
        if previous_initial and initial_hash != previous_initial[0]:
            raise ValueError("LR candidates have different initial trainable parameters")
        torch.manual_seed(a.seed)
        model.to(device)
        opt = torch.optim.AdamW(
            [v for v in model.parameters() if v.requires_grad],
            lr=lr,
            weight_decay=0.05 if a.task == "prithvi" else 0.01,
        )
        # Task-specific schedule family retained for every matched learner.
        # TerraMind plateau uses common validation IoU, avoiding incomparable
        # training-loss scales; this adaptation is recorded in the methods.
        scheduler = (
            torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=5)
            if a.task == "terramind"
            else torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
            if a.task in {"prithvi", "copernicus"}
            else None
        )
        record = dict(
            trial=i,
            lr=lr,
            status="running",
            validation_iou=None,
            initial_trainable_sha256=initial_hash,
            trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
            parameters=sum(p.numel() for p in model.parameters()),
            setup_s=time.perf_counter() - setup_start,
        )
        start = time.perf_counter()
        try:
            for epoch in range(epochs):
                model.train()
                random.seed(a.seed + epoch)
                np.random.seed(a.seed + epoch)
                training = loader("train", augment=a.task != "galileo", epoch=epoch)
                epoch_start = time.perf_counter()
                examples, updates, skipped_examples, loss_sum = 0, 0, 0, 0.0
                for step, batch in enumerate(training):
                    examples += len(batch["chip"])
                    if a.task == "galileo":
                        progress = epoch + step / len(training)
                        warmup = epochs * 0.1
                        rate = (
                            lr * progress / warmup
                            if progress < warmup
                            else 1e-5
                            + (lr - 1e-5)
                            * 0.5
                            * (1 + math.cos(math.pi * (progress - warmup) / (epochs - warmup)))
                        )
                        for group in opt.param_groups:
                            group["lr"] = rate
                    opt.zero_grad(set_to_none=True)
                    loss = w.loss_for(
                        w.forward(model, batch, a.task, a.learner, device),
                        batch["y"].to(device),
                        a.task,
                        "native" if a.task == "terramind" else a.learner,
                    )
                    if loss is None:
                        skipped_examples += len(batch["chip"])
                        continue
                    if not torch.isfinite(loss):
                        raise ValueError("Nonfinite loss")
                    loss.backward()
                    opt.step()
                    updates += 1
                    loss_sum += float(loss.detach())
                training_s = time.perf_counter() - epoch_start
                validation_start = time.perf_counter()
                v = w.score(model, loader("valid"), args, device)
                validation_s = time.perf_counter() - validation_start
                value = v[
                    "mean_event_flood_iou" if a.task == "copernicus" else "mean_event_water_iou"
                ]
                with (out / "validation.jsonl").open("a") as f:
                    f.write(
                        json.dumps(
                            dict(
                                trial=i,
                                epoch=epoch + 1,
                                validation=v,
                                training_examples=examples,
                                expected_examples=len(training.dataset),
                                optimizer_updates=updates,
                                no_valid_label_examples=skipped_examples,
                                mean_training_batch_loss=loss_sum / updates if updates else None,
                                training_s=training_s,
                                validation_s=validation_s,
                                learning_rate=opt.param_groups[0]["lr"],
                            )
                        )
                        + "\n"
                    )
                if examples != len(training.dataset):
                    raise RuntimeError("Training epoch did not retain every selected example")
                if value is not None and (
                    record["validation_iou"] is None or value > record["validation_iou"]
                ):
                    record.update(validation_iou=value, epoch=epoch + 1)
                    torch.save(model.state_dict(), out / f"trial-{i}.pt")
                if scheduler is not None:
                    if a.task == "terramind":
                        if value is None:
                            raise ValueError("Undefined validation IoU")
                        scheduler.step(1 - value)
                    else:
                        scheduler.step()
                if shutil.disk_usage(ROOT).free < 52 * 1024**3:
                    raise RuntimeError("Disk reserve approached; checkpoints retained")
            record["status"] = "completed"
        except (ValueError, RuntimeError) as exc:
            record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        record["elapsed_s"] = time.perf_counter() - start
        record["process_peak_rss_raw"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        record["rss_units"] = "bytes on macOS; KiB on Linux"
        record["best_epoch_at_ceiling"] = record.get("epoch") == epochs
        checkpoint = out / f"trial-{i}.pt"
        if checkpoint.exists():
            record["checkpoint_sha256"] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        trials.append(record)
        (out / "trials.json").write_text(json.dumps(trials, indent=2))
        del model, opt, scheduler
    winner = select_trial(trials)
    winner = dict(winner, learning_rate_grid_boundary=winner["trial"] in {0, len(rates) - 1})
    (out / "selection.json").write_text(json.dumps(winner, indent=2))
    if a.evaluate_selected:
        if (
            hashlib.sha256((out / f"trial-{winner['trial']}.pt").read_bytes()).hexdigest()
            != winner["checkpoint_sha256"]
        ):
            raise ValueError("Selected checkpoint changed")
        model = make_model()
        model.load_state_dict(
            torch.load(out / f"trial-{winner['trial']}.pt", map_location="cpu", weights_only=True)
        )
        model.to(device)
        start = time.perf_counter()
        result = w.score(model, loader("test"), args, device, out / "predictions")
        result["test_scoring_wall_s"] = time.perf_counter() - start
        (out / "selected-test.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
