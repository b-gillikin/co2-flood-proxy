"""Real training-input profiles for the seven missing learned comparisons.

Engineering only: no test records, retained fitted heads or accuracy scores.
Uses complete-batch policy; profile-batches0 means a full training epoch.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader

from applied_evaluation import CompleteBatches
from applied_unet import StandardUNet


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--task", choices=["terramind", "galileo", "prithvi", "copernicus"], required=True
    )
    p.add_argument(
        "--learner", choices=["native", "unet", "unet_standard", "linear"], required=True
    )
    p.add_argument("--device", choices=["cpu", "mps"], required=True)
    p.add_argument("--batch-size", type=int, required=True)
    p.add_argument("--profile-batches", type=int, default=3)
    a = p.parse_args()
    if a.batch_size < 2 or a.profile_batches < 0:
        p.error("Batch>=2; nonnegative profile batches")
    if a.task != "copernicus" and a.learner != "unet_standard":
        p.error("Original nine profiles remain in their protected queue")
    if a.device == "mps":
        for name in [
            "results/limburg_individual_experiments_v1/queue/progress.json",
            "results/applied_study_v1/profile_queue/progress.json",
        ]:
            state = json.loads((ROOT / name).read_text())
            if any(
                t.get("status") == "running" and t.get("resource") == "mps"
                for t in state.get("tasks", {}).values()
            ) or any(j.get("status") == "running" for j in state.get("jobs", [])):
                raise RuntimeError("Existing MPS owner/profile remains active")
    torch.set_num_threads(1)
    torch.manual_seed(42)
    spec = importlib.util.spec_from_file_location(
        "held_water", ROOT / "scripts/185_run_applied_water.py"
    )
    w = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(w)
    if a.task == "copernicus":
        import applied_change_task as w
        from applied_copernicus import CopernicusRadarChange
    prefix = "radar-change" if a.task == "copernicus" else "sen1"
    ipath = w.PARTITIONS / (
        "radar-change-inventory.parquet"
        if a.task == "copernicus"
        else "sen1-chip-inventory.parquet"
    )
    fpath = w.PARTITIONS / f"{prefix}-grouped-folds.parquet"
    inventory = pd.read_parquet(ipath).rename(columns={"record": "chip"})
    folds = pd.read_parquet(fpath)
    fold = sorted(folds.fold.unique())[0]
    ids = set(folds.loc[(folds.fold == fold) & (folds.role == "train"), "chip"])
    dataset = w.Chips(inventory[inventory.chip.isin(ids)], a.task, augment=False)
    sampler = CompleteBatches(len(dataset), a.batch_size, 42)
    loader = DataLoader(dataset, batch_sampler=sampler, num_workers=0)
    out = (
        ROOT
        / "results/applied_study_v2/supplemental-profiles"
        / f"{a.task}-{a.learner}-{a.device}-b{a.batch_size}"
    )
    out.mkdir(parents=True, exist_ok=False)
    sourcefiles = [
        Path(__file__),
        ROOT / "src/applied_unet.py",
        ROOT / "src/applied_evaluation.py",
        ROOT / "scripts/185_run_applied_water.py",
        ROOT / "src/applied_water.py",
        ROOT / "src/applied_spatial_models.py",
        ROOT / "src/applied_change_task.py",
        ROOT / "src/applied_copernicus.py",
        ipath,
        fpath,
    ]
    hashes = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sourcefiles
    }
    (out / "manifest.json").write_text(
        json.dumps(
            dict(
                arguments=vars(a),
                source_hashes=hashes,
                fold=str(fold),
                training_chips=len(ids),
                training_examples=len(dataset),
                engineering_only=True,
                torch=torch.__version__,
                test_accessed=False,
            ),
            indent=2,
        )
    )
    start = time.perf_counter()
    channels = {"terramind": 15, "galileo": 2, "prithvi": 6, "copernicus": 4}[a.task]
    classes = 3 if a.task == "copernicus" else 2
    if a.learner == "native":
        model = CopernicusRadarChange()
    elif a.learner == "unet_standard":
        model = StandardUNet(channels, classes)
    elif a.learner == "linear":
        model = nn.Conv2d(channels, classes, 1)
    else:
        from applied_spatial_models import CompactUNet

        model = CompactUNet(channels)
        model.head = nn.Conv2d(16, classes, 1)
    device = torch.device(a.device)
    model.to(device)
    setup = time.perf_counter() - start
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=0.001)
    timings = []
    examples = 0

    def sync():
        if a.device == "mps":
            torch.mps.synchronize()

    model.train()
    for batch in loader:
        sync()
        start = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        outputs = w.forward(model, batch, a.task, a.learner, device)
        loss = w.loss_for(
            outputs, batch["y"].to(device), a.task, "native" if a.task == "terramind" else a.learner
        )
        if loss is None or not torch.isfinite(loss):
            raise ValueError("No finite engineering loss")
        loss.backward()
        if not all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None):
            raise ValueError("Nonfinite gradients")
        optimizer.step()
        sync()
        timings.append(time.perf_counter() - start)
        examples += len(batch["chip"])
        if a.profile_batches and len(timings) >= a.profile_batches:
            break
    statebytes = sum(t.numel() * t.element_size() for t in model.state_dict().values())
    trainbytes = sum(p.numel() * p.element_size() for p in model.parameters() if p.requires_grad)
    report = dict(
        status="completed",
        task=a.task,
        learner=a.learner,
        device=a.device,
        batch_size=a.batch_size,
        sampled_batches=len(timings),
        training_batches=len(sampler),
        examples_profiled=examples,
        full_training_epoch_profiled=len(timings) == len(sampler),
        batch_seconds=timings,
        estimated_epoch_s=float(np.mean(timings)) * len(sampler),
        model_setup_s=setup,
        model_state_bytes=statebytes,
        trainable_parameter_bytes=trainbytes,
        optimizer_moments_lower_bound_bytes=2 * trainbytes,
        three_candidate_checkpoint_tensor_bytes=3 * statebytes,
        process_peak_rss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        rss_units="bytes on macOS; KiB on Linux",
        caveat="Training engineering sample; timings include first-step overhead and contention, no comparative latency/accuracy claim; epoch extrapolation excludes validation/checkpoint I/O.",
    )
    (out / "complete.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
