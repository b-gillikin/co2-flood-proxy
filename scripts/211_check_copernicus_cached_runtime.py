"""Verify frozen-feature cache equivalence and sustained cached-head training."""

import json
import os
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

from applied_change_task import Chips, loss_for
from applied_copernicus import CopernicusRadarChange
from applied_execution import atomic, sha


def main():
    cache = ROOT / "data/processed/limburg_copernicus_spatial_v1"
    index = json.loads((cache / "index.json").read_text())
    if index["status"] != "completed" or index["completed"] != 5000:
        raise ValueError("Cache incomplete")
    for n, h in index["source_hashes"].items():
        if sha(ROOT / n) != h:
            raise ValueError("Cache source drift")
    rows = pd.read_parquet(
        ROOT / "results/applied_study_v1/evaluation/radar-change-inventory.parquet"
    ).rename(columns={"record": "chip"})
    # Training-only records for output/gradient engineering checks.
    folds = pd.read_parquet(
        ROOT / "results/applied_study_v1/evaluation/radar-change-grouped-folds.parquet"
    )
    fold = sorted(folds.fold.unique())[0]
    rows = rows[
        rows.chip.isin(set(folds.loc[(folds.fold == fold) & (folds.role == "train"), "chip"]))
    ].reset_index(drop=True)
    ds = Chips(rows, "copernicus")
    torch.set_num_threads(1)
    torch.manual_seed(42)
    model = CopernicusRadarChange().eval().to("mps")
    errors = []
    for i in [0, len(ds) // 2, len(ds) - 1]:
        item = ds[i]
        saved = torch.from_numpy(np.load(cache / f"{item['chip']}.npy", allow_pickle=False))
        features = model.frozen_features(item["x"][None], item["metadata"][None])
        fresh = torch.stack([f[0] for f in features])
        torch.testing.assert_close(saved, fresh, rtol=0, atol=0)
        with torch.no_grad():
            direct = model(item["x"][None].to("mps"), item["metadata"][None].to("mps"))
            cached = model.forward_features(saved[None].unbind(1))
        for a, b in zip(direct, cached, strict=True):
            torch.testing.assert_close(a, b, rtol=0, atol=0)
            errors.append(float((a - b).abs().max()))
    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=0.001)
    times = []
    for i in range(12):
        records = [ds[2 * i], ds[2 * i + 1]]
        features = torch.stack(
            [
                torch.from_numpy(np.load(cache / f"{r['chip']}.npy", allow_pickle=False))
                for r in records
            ]
        )
        y = torch.stack([r["y"] for r in records]).to("mps")
        t = time.perf_counter()
        opt.zero_grad(set_to_none=True)
        output = model.forward_features(features.unbind(1))
        loss = loss_for(output, y, "copernicus", "native")
        loss.backward()
        if not torch.isfinite(loss) or not all(
            torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None
        ):
            raise ValueError("Nonfinite training")
        opt.step()
        torch.mps.synchronize()
        times.append(time.perf_counter() - t)
    out = ROOT / "results/applied_study_v3/preparation"
    out.mkdir(parents=True, exist_ok=True)
    result = dict(
        status="passed",
        cache_records=5000,
        training_fold=fold,
        cache_features_bit_identical=3,
        head_eval_outputs_max_abs_error=max(errors),
        training_batches=12,
        training_finite=True,
        batch_seconds=times,
        median_steady_batch_seconds=float(np.median(times[2:])),
        cache_index_sha256=sha(cache / "index.json"),
        source_sha256=sha(Path(__file__)),
        interpretation="Training-only engineering verification. No held-test scoring or comparative accuracy claim. Cold encoder extraction cost remains reportable.",
    )
    atomic(out / "copernicus-cached-runtime.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
