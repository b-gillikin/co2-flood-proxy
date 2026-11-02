"""Versioned full-training-epoch Prithvi profile after exact MPS pool recovery.

No test/validation labels or accuracy evaluation. CPU/MPS forward comparison
uses the same initial weights and first real training batch in evaluation mode.
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
from torch.utils.data import DataLoader

from applied_evaluation import CompleteBatches
from applied_mps_pool import MPSCompatibleAdaptiveAvgPool2d
from applied_spatial_models import prithvi


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--detect-anomaly", action="store_true")
    a = p.parse_args()
    for name in [
        "results/limburg_individual_experiments_v1/queue/progress.json",
        "results/applied_study_v1/profile_queue/progress.json",
        "results/applied_study_v2/supplemental-profile-queue/progress.json",
    ]:
        state = json.loads((ROOT / name).read_text())
        if any(
            x.get("status") == "running" and x.get("resource") == "mps"
            for x in state.get("tasks", {}).values()
        ) or any(x.get("status") == "running" for x in state.get("jobs", [])):
            raise RuntimeError("MPS still owned by earlier queue")
    a.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location(
        "water", ROOT / "scripts/185_run_applied_water.py"
    )
    w = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(w)
    torch.autograd.set_detect_anomaly(a.detect_anomaly)
    torch.set_num_threads(1)
    torch.manual_seed(42)
    inv = pd.read_parquet(w.PARTITIONS / "sen1-chip-inventory.parquet")
    folds = pd.read_parquet(w.PARTITIONS / "sen1-grouped-folds.parquet")
    fold = sorted(folds.fold.unique())[0]
    ids = set(folds.loc[(folds.fold == fold) & (folds.role == "train"), "chip"])
    dataset = w.Chips(inv[inv.chip.isin(ids)], "prithvi", augment=False)
    sampler = CompleteBatches(len(dataset), 2, 42)
    loader = DataLoader(dataset, batch_sampler=sampler, num_workers=0)
    sources = [
        Path(__file__),
        ROOT / "src/applied_mps_pool.py",
        ROOT / "src/applied_spatial_models.py",
        ROOT / "scripts/185_run_applied_water.py",
        ROOT / "src/applied_water.py",
        ROOT / "src/applied_evaluation.py",
        w.PARTITIONS / "sen1-chip-inventory.parquet",
        w.PARTITIONS / "sen1-grouped-folds.parquet",
        ROOT / "data/raw/limburg_dynamic_model_weights/models/prithvi/Prithvi_EO_V2_tiny_TL.pt",
    ]
    manifest = dict(
        source_hashes={
            str(x.relative_to(ROOT)): hashlib.sha256(x.read_bytes()).hexdigest() for x in sources
        },
        fold=fold,
        training_chips=sorted(ids),
        torch=torch.__version__,
        device="mps_with_exact_cpu_nondivisible_adaptive_pool",
        batch=2,
        test_accessed=False,
        validation_accessed=False,
    )
    (a.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    model = prithvi()
    model.eval()
    pools = sum(isinstance(m, MPSCompatibleAdaptiveAvgPool2d) for m in model.modules())
    batch = next(iter(loader))
    with torch.no_grad():
        cpu = w.forward(model, batch, "prithvi", "native", torch.device("cpu"))
        model.to("mps")
        gpu = w.forward(model, batch, "prithvi", "native", torch.device("mps")).cpu()
    torch.testing.assert_close(gpu, cpu, rtol=1e-3, atol=1e-3)
    difference = float((gpu - cpu).abs().max())
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5, weight_decay=0.05)
    seconds = []
    examples = 0
    began = time.perf_counter()
    for i, batch in enumerate(loader):
        t = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        logits = w.forward(model, batch, "prithvi", "native", torch.device("mps"))
        loss = w.loss_for(logits, batch["y"].to("mps"), "prithvi", "native")
        if loss is None or not torch.isfinite(loss):
            raise ValueError("Invalid loss")
        loss.backward()
        gradients = [p.grad for p in model.parameters() if p.grad is not None]
        if not gradients or not all(torch.isfinite(g).all() for g in gradients):
            raise ValueError("Invalid gradients")
        optimizer.step()
        torch.mps.synchronize()
        seconds.append(time.perf_counter() - t)
        examples += len(batch["chip"])
        if i % 10 == 0:
            print(
                json.dumps(dict(batches_done=i + 1, batches_total=len(loader), examples=examples)),
                flush=True,
            )
    if examples != len(dataset):
        raise ValueError("Incomplete training census")
    report = dict(
        status="completed",
        full_training_epoch_profiled=True,
        batches=len(seconds),
        examples=examples,
        training_chips=len(ids),
        cpu_mps_forward_max_abs_error=difference,
        equivalence_rtol=0.001,
        equivalence_atol=0.001,
        adaptive_pool_modules=pools,
        finite_gradients_all_batches=True,
        epoch_seconds=time.perf_counter() - began,
        median_batch_seconds=float(np.median(seconds)),
        batch_seconds=seconds,
        model_state_bytes=sum(x.numel() * x.element_size() for x in model.state_dict().values()),
        rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        interpretation="Engineering equivalence and full-epoch feasibility; no test scores, comparative speed or scientific fit claim.",
    )
    (a.output / "complete.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "batch_seconds"}), flush=True)


if __name__ == "__main__":
    main()
