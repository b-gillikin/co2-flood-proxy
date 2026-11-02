"""Verify actual runtime prefetch and frozen TerraMind output/gradient parity.

Uses held training inputs only; no fitted checkpoints or test selection.
"""

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from applied_evaluation import CompleteBatches
from applied_execution import atomic
from applied_fast_data import CachedChips, EpochBatches, cached_terramind_forward


def main():
    torch.set_num_threads(2)
    began = time.perf_counter()
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)
        np.save(path / "x.npy", np.zeros((5, 6, 8, 8), dtype=np.float32))
        np.save(path / "y.npy", np.zeros((5, 8, 8), dtype=np.int8))
        rows = [dict(chip=str(i), event="event", position=i) for i in range(5)]
        (path / "index.json").write_text(json.dumps(dict(status="complete", rows=rows)))
        dataset = CachedChips(pd.DataFrame(rows), "prithvi", path, augment=True)
        loader = DataLoader(
            dataset,
            batch_sampler=EpochBatches(5, 2, 42, dataset.epoch),
            num_workers=2,
            persistent_workers=True,
            multiprocessing_context="spawn",
        )
        for epoch in [0, 1]:
            dataset.set_epoch(epoch)
            found = [chip for batch in loader for chip in batch["chip"]]
            expected = [str(i) for batch in CompleteBatches(5, 2, 42 + epoch) for i in batch]
            assert found == expected
        del loader
    from applied_spatial_models import terramind

    torch.manual_seed(42)
    raw = ROOT / "data/processed/limburg_tensor_cache_v1/terramind"
    row = json.loads((raw / "index.json").read_text())["rows"][0]
    x = torch.from_numpy(np.load(raw / "x.npy", mmap_mode="r")[row["position"]].copy())[None]
    f = torch.from_numpy(
        np.load(
            ROOT / "data/processed/limburg_terramind_encoder_v1" / f"{row['chip']}.npy",
            mmap_mode="r",
        )[0].copy()
    )[None]
    model = terramind().eval()
    a = model({"S2L1C": x[:, :13], "S1GRD": x[:, 13:]}).output
    a.square().mean().backward()
    grads = {n: p.grad.clone() for n, p in model.named_parameters() if p.grad is not None}
    model.zero_grad(set_to_none=True)
    b = cached_terramind_forward(model, f)
    b.square().mean().backward()
    errors = []
    for n, p in model.named_parameters():
        if n in grads:
            torch.testing.assert_close(p.grad, grads[n], atol=1e-6, rtol=2e-4)
            errors.append(float((p.grad - grads[n]).abs().max()))
    torch.testing.assert_close(a, b, atol=2e-5, rtol=2e-4)
    atomic(
        ROOT / "results/applied_optimization_2026_11_02/fast-runtime-verification.json",
        dict(
            status="passed",
            two_persistent_workers="Two epochs complete ordered census",
            terramind_output_max_abs=float((a - b).abs().max().detach()),
            terramind_gradient_max_abs=max(errors),
            trainable_parameters_checked=len(errors),
            elapsed_s=time.perf_counter() - began,
            torch=torch.__version__,
        ),
    )


if __name__ == "__main__":
    main()
