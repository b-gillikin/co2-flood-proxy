"""Cache exact normalized source tensors once, before any random augmentation.

All records/labels/metadata retained, split selection stays in the runner. Raw
Prithvi stays512px so rotations/flips precede its224px interpolation exactly.
"""

import argparse
import hashlib
import importlib.util
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

from applied_execution import atomic, sha
from applied_io_cache import galileo_source
from applied_water import PRITHVI_S2, valid_labels


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--task", choices=["terramind", "prithvi", "galileo", "copernicus"], required=True
    )
    a = p.parse_args()
    out = ROOT / "data/processed/limburg_tensor_cache_v1" / a.task
    out.mkdir(parents=True, exist_ok=True)
    progress = ROOT / "results/applied_optimization_2026_11_02" / f"{a.task}-tensor-cache.json"
    spec = importlib.util.spec_from_file_location(
        "water", ROOT / "scripts/185_run_applied_water.py"
    )
    w = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(w)
    if a.task == "copernicus":
        import applied_change_task as w
    invpath = w.PARTITIONS / (
        "radar-change-inventory.parquet"
        if a.task == "copernicus"
        else "sen1-chip-inventory.parquet"
    )
    frame = pd.read_parquet(invpath).rename(columns={"record": "chip"})
    sourcefiles = [
        Path(__file__),
        ROOT / "scripts/185_run_applied_water.py",
        ROOT / "src/applied_water.py",
        ROOT / "src/applied_io_cache.py",
        ROOT / "src/applied_change_task.py",
        ROOT / "src/applied_copernicus.py",
        invpath,
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sourcefiles}
    if (out / "index.json").exists():
        index = json.loads((out / "index.json").read_text())
        if index["source_hashes"] != hashes:
            raise ValueError("Cache source version differs")
        if index["status"] == "complete":
            print("Already complete", a.task)
            return
    n = len(frame)
    c = {"terramind": 15, "prithvi": 6, "galileo": 2, "copernicus": 4}[a.task]
    side = 224 if a.task == "copernicus" else 512
    x = np.lib.format.open_memmap(
        out / "x.npy", mode="w+", dtype="float32", shape=(n, c, side, side)
    )
    y = np.lib.format.open_memmap(out / "y.npy", mode="w+", dtype="int8", shape=(n, side, side))
    rows = []
    dataset = w.Chips(frame, a.task, augment=False)
    torch.set_num_threads(1)
    began = time.perf_counter()
    for i, row in enumerate(frame.itertuples()):
        if a.task == "galileo":
            target, raw = galileo_source(str(w.DATA), row.chip)
            meta = dict(month=pd.Timestamp(row.s1_date.replace("/", "-")).month - 1)
        else:
            item = dataset[i]
            target = item["y"].numpy()
            raw = item["x"].numpy()
            meta = {k: item[k].tolist() for k in ["temporal", "location", "metadata"] if k in item}
            if a.task == "prithvi":
                label, _, s2 = w.read_chip(row.chip, "prithvi")
                optical = s2[PRITHVI_S2]
                target = valid_labels(label, s2=optical)
                raw = w.standardize(
                    optical,
                    [1087, 1342, 1433, 2734, 1958, 1363],
                    [2248, 2179, 2178, 1850, 1242, 1049],
                )
        if not set(np.unique(target)) <= ({-1, 0, 1, 2} if a.task == "copernicus" else {-1, 0, 1}):
            raise ValueError("Unexpected target")
        fill = 0.5 if a.task == "galileo" else 0
        x[i] = np.nan_to_num(raw, nan=fill, posinf=fill, neginf=fill)
        y[i] = target.astype(np.int8)
        rows.append(dict(chip=row.chip, event=row.event, position=i, **meta))
        if i % 100 == 0:
            atomic(
                progress,
                dict(
                    status="running",
                    task=a.task,
                    done=i + 1,
                    total=n,
                    elapsed_s=time.perf_counter() - began,
                ),
            )
            print(a.task, i + 1, n, flush=True)
    x.flush()
    y.flush()
    result = dict(
        status="complete",
        task=a.task,
        records=n,
        rows=rows,
        source_hashes=hashes,
        x_shape=list(x.shape),
        y_shape=list(y.shape),
        array_hashes={name: sha(out / name) for name in ["x.npy", "y.npy"]},
        elapsed_s=time.perf_counter() - began,
        bytes=sum((out / name).stat().st_size for name in ["x.npy", "y.npy"]),
        meaning="Exact normalized inputs and signed targets before augmentation; no learned transformation, source or sample removal.",
    )
    atomic(out / "index.json", result)
    atomic(progress, {k: v for k, v in result.items() if k != "rows"})


if __name__ == "__main__":
    main()
