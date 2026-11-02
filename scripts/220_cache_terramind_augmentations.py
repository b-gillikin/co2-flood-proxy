"""Exact frozen TerraMind encoder cache for all8 existing augmentations.

Cache only selected frozen layers2/5/8/11 before the trainable neck/decoder.
No new image, label, resampling, augmentation or trainable-layer cache.
"""

import argparse
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
import torch

from applied_execution import atomic, sha
from applied_spatial_models import terramind


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--device", default="cpu")
    a = p.parse_args()
    raw = ROOT / "data/processed/limburg_tensor_cache_v1/terramind"
    rawindex = json.loads((raw / "index.json").read_text())
    if rawindex["status"] != "complete":
        raise ValueError("Tensor cache incomplete")
    out = ROOT / "data/processed/limburg_terramind_encoder_v1"
    out.mkdir(parents=True, exist_ok=True)
    files = [
        Path(__file__),
        ROOT / "src/applied_spatial_models.py",
        ROOT / "src/applied_mps_pool.py",
        ROOT / "data/raw/limburg_dynamic_model_weights/models/terramind/TerraMind_v1_tiny.pt",
        raw / "index.json",
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    if (out / "index.json").exists() and json.loads((out / "index.json").read_text())[
        "source_hashes"
    ] != hashes:
        raise ValueError("Changed source; version cache")
    x = np.load(raw / "x.npy", mmap_mode="r")
    torch.set_num_threads(2)
    model = terramind().to(a.device).eval()
    began = time.perf_counter()
    records = []
    for row in rawindex["rows"]:
        path = out / f"{row['chip']}.npy"
        receipt = path.with_suffix(".receipt.json")
        if path.exists():
            record = json.loads(receipt.read_text())
            if sha(path) != record["sha256"]:
                raise ValueError("Feature file changed")
        else:
            source = x[row["position"]]
            aug = np.stack(
                [
                    np.rot90(source, k, axes=(-2, -1))[..., ::-1]
                    if flip
                    else np.rot90(source, k, axes=(-2, -1))
                    for flip in [False, True]
                    for k in range(4)
                ]
            ).astype(np.float32)
            images = torch.from_numpy(aug).to(a.device)
            start = time.perf_counter()
            with torch.no_grad():
                features = model.encoder({"S2L1C": images[:, :13], "S1GRD": images[:, 13:]})
            array = torch.stack([features[i] for i in [2, 5, 8, 11]], dim=1).cpu().numpy()
            if array.shape != (8, 4, 1024, 192) or not np.isfinite(array).all():
                raise ValueError("Unexpected frozen feature contract")
            tmp = path.with_suffix(".partial")
            with tmp.open("wb") as f:
                np.save(f, array, allow_pickle=False)
            tmp.replace(path)
            record = dict(
                chip=row["chip"],
                sha256=sha(path),
                bytes=path.stat().st_size,
                feature_seconds=time.perf_counter() - start,
            )
            atomic(receipt, record)
        records.append(record)
        state = dict(
            status="running",
            completed=len(records),
            total=446,
            source_hashes=hashes,
            bytes=sum(r["bytes"] for r in records),
            feature_seconds=sum(r["feature_seconds"] for r in records),
            elapsed_s=time.perf_counter() - began,
            shape_per_chip=[8, 4, 1024, 192],
            device=a.device,
            threads=2,
            augmentation_order="rotation k+4*horizontal_flip",
            selected_layers=[2, 5, 8, 11],
        )
        atomic(out / "index.json", state)
        atomic(ROOT / "results/applied_optimization_2026_11_02/terramind-frozen-cache.json", state)
        if len(records) % 20 == 0:
            print(
                json.dumps({k: state[k] for k in ["completed", "total", "elapsed_s"]}), flush=True
            )
    state.update(status="completed", files=records)
    atomic(out / "index.json", state)
    atomic(
        ROOT / "results/applied_optimization_2026_11_02/terramind-frozen-cache.json",
        {k: v for k, v in state.items() if k != "files"},
    )


if __name__ == "__main__":
    main()
