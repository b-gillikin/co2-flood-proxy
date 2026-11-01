"""Real-data native-head CPU forward/backward check; no accuracy claim."""

import hashlib
import json
import os
import sys
import time
from datetime import datetime
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

from applied_copernicus import WEIGHT, CopernicusRadarChange, change_loss, normalize_radar


def main():
    torch.set_num_threads(1)
    start = time.perf_counter()
    data = ROOT / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1/data"
    inventory = pd.read_parquet(
        ROOT / "results/applied_study_v1/evaluation/radar-change-inventory.parquet"
    )
    batch, targets, metas, files = [], [], [], []
    for row in inventory.head(2).itertuples():
        folder = data / row.source_path
        arrays = []
        for prefix in ["SL1_IVV", "SL1_IVH", "MS1_IVV", "MS1_IVH", "MK0_MLU", "MK0_MNA"]:
            (path,) = folder.glob(prefix + "*.tif")
            with rasterio.open(path) as ds:
                arrays.append(ds.read(1))
            files.append(path)
        x, valid = normalize_radar(np.stack(arrays[:4]))
        y = np.where(valid & (arrays[5] == 1), arrays[4], 3)
        batch.append(x)
        targets.append(y)
        # Match author loader: center of the central POST raster pixel,
        # transformed to lon/lat (not a polygon-centroid approximation).
        from rasterio.warp import transform

        with rasterio.open(files[-4]) as source:
            cx, cy = source.xy(source.height // 2, source.width // 2)
            lon, lat = transform(source.crs, "EPSG:4326", [cx], [cy])
        dates = [row.pre_date, row.post_date]
        metas.append(
            [
                [
                    lon[0],
                    lat[0],
                    (datetime.fromisoformat(d) - datetime(1970, 1, 1)).days,
                    0.0256,
                ]
                for d in dates
            ]
        )
    model = CopernicusRadarChange().train()
    outputs = model(torch.from_numpy(np.stack(batch)), torch.tensor(metas, dtype=torch.float32))
    loss = change_loss(outputs, torch.from_numpy(np.stack(targets)).long())
    if loss is None or not torch.isfinite(loss):
        raise ValueError("No finite real-data training loss")
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
    if not grads or not all(torch.isfinite(g).all() for g in grads):
        raise ValueError("Missing/nonfinite head gradients")
    model.eval()
    with torch.no_grad():
        single = model(
            torch.from_numpy(batch[0][None]), torch.tensor(metas[:1], dtype=torch.float32)
        )
    if not all(torch.isfinite(t).all() for t in single):
        raise ValueError("Nonfinite batch-one evaluation")
    sources = [Path(__file__), ROOT / "src/applied_copernicus.py", WEIGHT, *files]
    report = dict(
        status="native_cpu_forward_backward_passed",
        device="cpu",
        torch=torch.__version__,
        training_batch=2,
        evaluation_batch=1,
        output_shapes=[list(t.shape) for t in outputs],
        loss=float(loss.detach()),
        finite_head_gradients=len(grads),
        encoder_gradients=any(p.grad is not None for p in model.encoder.parameters()),
        load_report=model.load_report,
        elapsed_s=time.perf_counter() - start,
        hashes={
            str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sources
        },
        interpretation="Engineering compatibility only; untrained head, no accuracy estimate; MPS not tested while occupied",
    )
    out = ROOT / "results/applied_study_v1/runtime/copernicus-native-check.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
