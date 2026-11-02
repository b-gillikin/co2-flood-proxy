"""Validation-only equal-trial tuning, followed optionally by ONE selected test fit.

Use the same fold, chip-label budget, seed, batch size and epoch ceiling for
all learners within a task. Existing profile jobs are unchanged. Never call
185's train CLI for a learning-rate search: that CLI scores test after each fit.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import random
import resource
import shutil
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_evaluation import CompleteBatches, label_accounting
from applied_execution import atomic, verify_completed
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
    p.add_argument(
        "--fixed-lr-from",
        type=Path,
        help="Verified full-label seed42 fit; repeat full-label seeds only",
    )
    p.add_argument("--tensor-cache", type=Path)
    p.add_argument("--evaluation-dir", type=Path)
    p.add_argument("--physical-root", type=Path)
    p.add_argument("--shared-label-mask", action="store_true")
    p.add_argument("--early-stop-patience", type=int, default=0)
    p.add_argument("--early-stop-min-epochs", type=int, default=0)
    p.add_argument("--early-stop-min-delta", type=float, default=0.0001)
    p.add_argument("--eval-batch-size", type=int, default=1)
    p.add_argument("--data-workers", type=int, default=0)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--foreach", action="store_true")
    p.add_argument("--precision", choices=["float32", "float16", "bfloat16"], default="float32")
    p.add_argument("--on-device-pool", action="store_true")
    p.add_argument("--output-root", type=Path, default=ROOT / "results/applied_study_v2/tuning")
    p.add_argument("--run", action="store_true", help="Without this, print the plan only")
    p.add_argument(
        "--evaluate-selected", action="store_true", help="Test only the validation winner"
    )
    a = p.parse_args()
    for field in [
        "tensor_cache",
        "feature_cache",
        "output_root",
        "fixed_lr_from",
        "evaluation_dir",
        "physical_root",
    ]:
        value = getattr(a, field)
        if value is not None:
            setattr(a, field, value.resolve())
    epochs = a.epochs if a.epochs is not None else (100 if a.task == "terramind" else 50)
    if epochs < 1 or a.batch_size < 2:
        p.error("Use positive epochs and batch-size >=2 for common task support")
    rates = learning_rates(a.task, a.learner)
    print(
        json.dumps(
            dict(
                task=a.task,
                learner=a.learner,
                rates=None if a.fixed_lr_from else rates,
                fixed_lr_from=str(a.fixed_lr_from) if a.fixed_lr_from else None,
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
    if a.evaluation_dir:
        w.PARTITIONS = a.evaluation_dir
    torch.set_num_threads(a.threads)
    if a.tensor_cache:
        from applied_fast_data import CachedChips, EpochBatches, cached_terramind_forward, fast_loss

        legacy_forward = w.forward

        def accelerated_forward(model, batch, task, learner, device):
            if task == "terramind" and learner == "native" and "features" in batch:
                model.encoder.eval()
                return cached_terramind_forward(model, batch["features"].to(device))
            return legacy_forward(model, batch, task, learner, device)

        w.forward = accelerated_forward
    if a.device == "mps":
        ownership = ROOT / "results/applied_study_v3/.mps-owner.lock"
        ownership.parent.mkdir(parents=True, exist_ok=True)
        device_lock = ownership.open("a")
        fcntl.flock(device_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for queue in [
            "results/limburg_individual_experiments_v1/queue/progress.json",
            "results/applied_study_v1/profile_queue/progress.json",
            "results/applied_study_v2/supplemental-profile-queue/progress.json",
        ]:
            if not (ROOT / queue).exists():
                continue
            state = json.loads((ROOT / queue).read_text())
            tasks = state.get("tasks", {})
            tasks = list(tasks.values()) if isinstance(tasks, dict) else tasks
            jobs = state.get("jobs", [])
            if any(
                t.get("status") == "running" and t.get("resource") == "mps" for t in tasks
            ) or any(t.get("status") == "running" for t in jobs):
                raise RuntimeError("Use the existing device queue; another worker may own MPS")
    if a.feature_cache:
        if a.task not in {"galileo", "copernicus", "terramind"} or a.learner != "native":
            p.error("Cached features are for frozen native Galileo/Copernicus/TerraMind encoders")
        index = json.loads((a.feature_cache / "index.json").read_text())
        if index["status"] != "completed" or index["completed"] != (
            5000 if a.task == "copernicus" else 446
        ):
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
            (subsets.fold == a.fold)
            & (subsets.seed == (42 if a.shared_label_mask else a.seed))
            & (subsets.budget == a.budget),
            "chip",
        ]
    )
    if not selected:
        raise ValueError("Empty training subset")
    rows = {}
    for role in ["train", "valid", "test"]:
        ids = set(folds.loc[(folds.fold == a.fold) & (folds.role == role), "chip"])
        rows[role] = inv[inv.chip.isin(ids & selected if role == "train" else ids)].copy()
    tuning_reuse = None
    if a.fixed_lr_from:
        from applied_tuning_reuse import fixed_learning_rate

        rate, tuning_reuse = fixed_learning_rate(
            a.fixed_lr_from,
            {k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()},
            {k: sorted(v.chip) for k, v in rows.items()},
            epochs,
        )
        rates = [rate]
    out = (
        a.output_root
        / f"{a.task}-{a.learner}-{a.fold}-{a.budget:g}-{a.seed}-{a.device}-b{a.batch_size}-e{epochs}"
    )
    out.mkdir(parents=True, exist_ok=False)
    sources = [
        Path(__file__),
        ROOT / "src/applied_selection.py",
        ROOT / "src/applied_evaluation.py",
        ROOT / "src/applied_execution.py",
        ROOT / "src/applied_unet.py",
        ROOT / "scripts/185_run_applied_water.py",
        ROOT / "src/applied_spatial_models.py",
        ROOT / "src/applied_mps_pool.py",
        ROOT / "src/applied_io_cache.py",
        ROOT / "src/applied_fast_data.py",
        ROOT / "src/applied_fast_pool.py",
        ROOT / "src/applied_tuning_reuse.py",
        ROOT / "src/applied_grouped_protocol.py",
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
    if a.tensor_cache:
        sources.append(a.tensor_cache / "index.json")
    manifest = dict(
        arguments={k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()},
        rates=rates,
        stopping_policy=dict(
            patience=a.early_stop_patience,
            minimum_epochs=a.early_stop_min_epochs,
            min_delta=a.early_stop_min_delta,
            metric="validation equal-event target-class IoU; test never read",
        ),
        tuning_reuse=tuning_reuse,
        epochs=epochs,
        selection="validation equal-event target-class IoU; first-trial tie",
        source_hashes={
            str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources
        },
        partitions={k: sorted(v.chip) for k, v in rows.items()},
        torch=torch.__version__,
        precision=a.precision,
        mixed_precision_note="Float32 source tensors, master weights, optimizer state and final evaluation; autocast training only with dynamic scaling for float16",
        on_device_pool=a.on_device_pool,
        backend_policy=(
            "Prithvi decoder uses exact CPU non-divisible adaptive pooling on MPS; BatchNorm input/gradient layout made contiguous. Same parameters, state keys and mathematical operations."
            if a.task == "prithvi" and a.learner == "native"
            else "standard task backend"
        ),
        training_augmentation=(
            "none: fixed frozen spatial cache / radar-change protocol"
            if a.task in {"galileo", "copernicus"}
            else "matched90-degree rotations and horizontal flips"
        ),
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
        checkpoint_policy="omit_frozen_encoder_only"
        if a.tensor_cache and a.learner == "native" and a.task in {"terramind", "copernicus"}
        else "full_state",
        execution_optimization="memory-mapped exact tensors, persistent workers, batched evaluation, deferred loss readback"
        if a.tensor_cache
        else "legacy",
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
            "One-time frozen extraction across the full task inventory; do not multiply per head fit or omit from cold-start comparison. Held timing was measured under contention."
        )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    device = torch.device(a.device)
    args = SimpleNamespace(task=a.task, learner=a.learner)

    persistent_loaders = {}

    def loader(role, augment=False, epoch=0):
        if a.tensor_cache:
            if role not in persistent_loaders:
                dataset = CachedChips(
                    rows[role],
                    a.task,
                    a.tensor_cache,
                    feature_cache=a.feature_cache,
                    augment=role == "train" and augment,
                    seed=a.seed,
                )
                options = dict(
                    num_workers=a.data_workers, generator=torch.Generator().manual_seed(a.seed)
                )
                if a.data_workers:
                    options.update(
                        persistent_workers=True, prefetch_factor=2, multiprocessing_context="spawn"
                    )
                if role == "train":
                    persistent_loaders[role] = DataLoader(
                        dataset,
                        batch_sampler=EpochBatches(
                            len(dataset), a.batch_size, a.seed, dataset.epoch
                        ),
                        **options,
                    )
                else:
                    persistent_loaders[role] = DataLoader(
                        dataset,
                        batch_size=a.eval_batch_size,
                        shuffle=False,
                        drop_last=False,
                        **options,
                    )
            persistent_loaders[role].dataset.set_epoch(epoch)
            return persistent_loaders[role]
        dataset = w.Chips(rows[role], a.task, augment=augment, feature_cache=a.feature_cache)
        if role == "train":
            return DataLoader(
                dataset,
                batch_sampler=CompleteBatches(len(dataset), a.batch_size, a.seed + epoch),
                num_workers=0,
            )
        return DataLoader(
            dataset,
            batch_size=a.eval_batch_size,
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
                if a.task == "galileo" and a.feature_cache
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
        persistent_loaders = {}
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
        if a.on_device_pool:
            from applied_fast_pool import install_on_device_pools

            install_on_device_pools(model)
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
        if a.tensor_cache and a.feature_cache and hasattr(model, "encoder"):
            model.encoder.cpu()  # Frozen cache encoder need not occupy GPU memory.
        opt = torch.optim.AdamW(
            [v for v in model.parameters() if v.requires_grad],
            lr=lr,
            weight_decay=0.05 if a.task == "prithvi" else 0.01,
            foreach=True if a.foreach else None,
        )
        from applied_fast_data import make_scaler

        scaler = make_scaler(torch, a.device, a.precision)
        step_counter = [0]
        opt.register_step_post_hook(
            lambda *args, counter=step_counter: counter.__setitem__(0, counter[0] + 1)
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
        from applied_grouped_protocol import ValidationStop

        stopping = ValidationStop(
            a.early_stop_patience, a.early_stop_min_epochs, a.early_stop_min_delta
        )
        record.update(termination="epoch_ceiling", epochs_run=0)
        start = time.perf_counter()
        try:
            for epoch in range(epochs):
                model.train()
                random.seed(a.seed + epoch)
                np.random.seed(a.seed + epoch)
                training = loader("train", augment=a.task != "galileo", epoch=epoch)
                epoch_start = time.perf_counter()
                examples, updates, skipped_examples, loss_sum = 0, 0, 0, 0.0
                initial_step_count = step_counter[0]
                epoch_loss = torch.zeros((), device=device)
                invalid_loss = torch.zeros((), device=device, dtype=torch.bool)
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
                    context = (
                        torch.autocast(
                            a.device,
                            dtype=torch.float16 if a.precision == "float16" else torch.bfloat16,
                        )
                        if a.precision != "float32"
                        else nullcontext()
                    )
                    with context:
                        if a.tensor_cache:
                            if int(batch["valid_label_pixels"].sum()) == 0:
                                skipped_examples += len(batch["chip"])
                                continue
                            loss = fast_loss(
                                w.forward(model, batch, a.task, a.learner, device),
                                batch["loss_y"].to(device),
                                a.task,
                                a.learner,
                            )
                        else:
                            loss = w.loss_for(
                                w.forward(model, batch, a.task, a.learner, device),
                                batch["y"].to(device),
                                a.task,
                                "native" if a.task == "terramind" else a.learner,
                            )
                    if loss is None:
                        skipped_examples += len(batch["chip"])
                        continue
                    if a.tensor_cache:
                        invalid_loss.logical_or_(~torch.isfinite(loss.detach()))
                    elif not torch.isfinite(loss):
                        raise ValueError("Nonfinite loss")
                    scaler.scale(loss).backward()
                    scaler.step(opt)
                    scaler.update()
                    updates += 1
                    if a.tensor_cache:
                        epoch_loss.add_(loss.detach() / len(training))
                    else:
                        loss_sum += float(loss.detach())
                if a.tensor_cache:
                    if bool(invalid_loss):
                        raise ValueError("Nonfinite training loss; deferred epoch check")
                    loss_sum = float(epoch_loss) * len(training)
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
                                optimizer_updates=step_counter[0] - initial_step_count,
                                eligible_gradient_batches=updates,
                                amp_skipped_updates=updates
                                - (step_counter[0] - initial_step_count),
                                amp_loss_scale=scaler.get_scale(),
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
                    state = model.state_dict()
                    if manifest["checkpoint_policy"] == "omit_frozen_encoder_only":
                        state = {k: v for k, v in state.items() if not k.startswith("encoder.")}
                    torch.save(state, out / f"trial-{i}.pt")
                if scheduler is not None:
                    if a.task == "terramind":
                        if value is None:
                            raise ValueError("Undefined validation IoU")
                        scheduler.step(1 - value)
                    else:
                        scheduler.step()
                record["epochs_run"] = epoch + 1
                if stopping.update(epoch + 1, value):
                    record["termination"] = "validation_plateau"
                    break
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
    winner = dict(
        winner,
        learning_rate_grid_boundary=(winner["trial"] in {0, len(rates) - 1})
        if len(rates) > 1
        else None,
        fixed_learning_rate_from_validation=tuning_reuse is not None,
    )
    (out / "selection.json").write_text(json.dumps(winner, indent=2))
    if a.evaluate_selected:
        if (
            hashlib.sha256((out / f"trial-{winner['trial']}.pt").read_bytes()).hexdigest()
            != winner["checkpoint_sha256"]
        ):
            raise ValueError("Selected checkpoint changed")
        model = make_model()
        if a.on_device_pool:
            from applied_fast_pool import install_on_device_pools

            install_on_device_pools(model)
        state = torch.load(
            out / f"trial-{winner['trial']}.pt", map_location="cpu", weights_only=True
        )
        if manifest["checkpoint_policy"] == "omit_frozen_encoder_only":
            loaded = model.load_state_dict(state, strict=False)
            if loaded.unexpected_keys or any(
                not k.startswith("encoder.") for k in loaded.missing_keys
            ):
                raise ValueError("Task checkpoint omitted non-encoder state")
        else:
            model.load_state_dict(state, strict=True)
        model.to(device)
        if a.tensor_cache and a.feature_cache and hasattr(model, "encoder"):
            model.encoder.cpu()
        start = time.perf_counter()
        result = w.score(model, loader("test"), args, device, out / "predictions")
        result["test_scoring_wall_s"] = time.perf_counter() - start
        (out / "selected-test.json").write_text(json.dumps(result, indent=2))
        atomic(out / "complete.json", verify_completed(out))


if __name__ == "__main__":
    main()
