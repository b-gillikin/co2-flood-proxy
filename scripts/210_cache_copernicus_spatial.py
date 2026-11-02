"""Cache exact frozen before/after encoder differences for all5000 records.

One CPU thread; no training/selection or input substitution. Full-image spatial
features retain four levels, channels and14x14 grids, not catchment averages.
"""

import argparse
import fcntl
import hashlib
import json
import os
import resource
import shutil
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

from applied_change_task import Chips
from applied_copernicus import CopernicusRadarChange


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--output", type=Path, default=ROOT / "data/processed/limburg_copernicus_spatial_v1"
    )
    p.add_argument(
        "--progress-root", type=Path, default=ROOT / "results/applied_study_v2/copernicus-cache"
    )
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    a.progress_root.mkdir(parents=True, exist_ok=True)
    lock = (a.progress_root / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    paths = [
        Path(__file__),
        ROOT / "src/applied_copernicus.py",
        ROOT / "src/applied_change_task.py",
        ROOT / "src/applied_mps_pool.py",
        ROOT / "results/applied_study_v1/evaluation/radar-change-inventory.parquet",
        ROOT
        / "data/raw/limburg_dynamic_model_weights/models/copernicus_fm/CopernicusFM_ViT_base_varlang_e100.pth",
    ]
    vendor = (
        ROOT
        / "data/raw/limburg_dynamic_model_weights/code/copernicus_fm/Copernicus-Bench/src/foundation_models"
    )
    paths += list(vendor.rglob("*.py"))
    paths += list(
        (ROOT / "data/raw/limburg_dynamic_model_weights/models/copernicus_fm/varname_embed").glob(
            "*.pt"
        )
    )
    hashes = {str(x.relative_to(ROOT)): sha(x) for x in paths}
    index = a.output / "index.json"
    if index.exists() and json.loads(index.read_text())["source_hashes"] != hashes:
        raise ValueError("Changed cache contract; choose new version")
    frame = pd.read_parquet(paths[4]).rename(columns={"record": "chip"})
    assert len(frame) == 5000 and frame.chip.is_unique
    torch.set_num_threads(1)
    torch.manual_seed(42)
    model = CopernicusRadarChange().eval()
    dataset = Chips(frame, "copernicus")
    records = []
    began = time.perf_counter()
    times = 0
    for i, row in enumerate(frame.itertuples()):
        out = a.output / f"{row.chip}.npy"
        receipt = out.with_suffix(".receipt.json")
        folder = (
            ROOT
            / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1/data"
            / row.source_path
        )
        inputs = {
            str(x.relative_to(ROOT)): sha(x)
            for prefix in ["SL1_IVV", "SL1_IVH", "MS1_IVV", "MS1_IVH"]
            for x in folder.glob(prefix + "*.tif")
        }
        if out.exists():
            r = json.loads(receipt.read_text())
            if r["input_hashes"] != inputs or r["sha256"] != sha(out):
                raise ValueError("Changed feature/source")
        else:
            if shutil.disk_usage(ROOT).free < 53 * 1024**3:
                raise RuntimeError("Cache paused before disk reserve; resume same verified version")
            item = dataset[i]
            t = time.perf_counter()
            with torch.no_grad():
                features = model.frozen_features(item["x"][None], item["metadata"][None])
            array = torch.stack([x[0] for x in features]).cpu().numpy().astype(np.float32)
            if array.shape != (4, 768, 14, 14) or not np.isfinite(array).all():
                raise ValueError("Feature contract changed")
            tmp = out.with_suffix(".partial")
            with tmp.open("wb") as f:
                np.save(f, array, allow_pickle=False)
            tmp.replace(out)
            r = dict(
                chip=row.chip,
                sha256=sha(out),
                bytes=out.stat().st_size,
                input_hashes=inputs,
                feature_seconds=time.perf_counter() - t,
            )
            atomic(receipt, r)
        times += r["feature_seconds"]
        records.append(r)
        state = dict(
            status="running",
            completed=len(records),
            total=5000,
            bytes=sum(r["bytes"] for r in records),
            elapsed_s=time.perf_counter() - began,
            feature_seconds=times,
            device="cpu",
            threads=1,
            source_hashes=hashes,
            labels_enter_encoder=False,
            shape=[4, 768, 14, 14],
        )
        atomic(index, state)
        atomic(a.progress_root / "progress.json", state)
        if i % 25 == 0:
            print(
                json.dumps({k: state[k] for k in ["completed", "total", "bytes", "elapsed_s"]}),
                flush=True,
            )
    state.update(
        status="completed",
        files=records,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    atomic(index, state)
    atomic(a.progress_root / "complete.json", {k: v for k, v in state.items() if k != "files"})
    atomic(a.progress_root / "progress.json", {k: v for k, v in state.items() if k != "files"})


if __name__ == "__main__":
    main()
