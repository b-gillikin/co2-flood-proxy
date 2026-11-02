"""Copernicus radar-change task adapter for validation-only matched tuning."""

from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
import torch
from rasterio.warp import transform
from torch.nn import functional as F
from torch.utils.data import Dataset

from applied_copernicus import change_loss, normalize_radar
from applied_water import class_scores, confusion

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1/data"
PARTITIONS = ROOT / "results/applied_study_v1/evaluation"


class Chips(Dataset):
    def __init__(self, rows, task, augment=False, feature_cache=None):
        if task != "copernicus":
            raise ValueError("This adapter requires radar-change inputs")
        self.feature_cache = feature_cache
        self.rows = rows.reset_index(drop=True)
        # Retain the published pre/post temporal pairing and source scale.
        # No new augmentation policy is introduced for this task.

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        row = self.rows.iloc[i]
        folder = DATA / row.source_path
        arrays = []
        grid = None
        for prefix in ["SL1_IVV", "SL1_IVH", "MS1_IVV", "MS1_IVH", "MK0_MLU", "MK0_MNA"]:
            (path,) = folder.glob(prefix + "*.tif")
            with rasterio.open(path) as ds:
                current = (ds.shape, tuple(ds.transform), str(ds.crs))
                if grid is not None and current != grid:
                    raise ValueError("Pre/post/target grid mismatch")
                grid = current
                arrays.append(ds.read(1))
                if prefix == "MS1_IVV":
                    cx, cy = ds.xy(ds.height // 2, ds.width // 2)
                    lon, lat = transform(ds.crs, "EPSG:4326", [cx], [cy])
        x, valid = normalize_radar(np.stack(arrays[:4]))
        y = arrays[4].astype(np.int64)
        if not set(np.unique(y)) <= {0, 1, 2, 3}:
            raise ValueError("Unknown reference class")
        y[~valid | (arrays[5] != 1) | (y == 3)] = -1
        metadata = [
            [lon[0], lat[0], (datetime.fromisoformat(d) - datetime(1970, 1, 1)).days, 0.0256]
            for d in [row.pre_date, row.post_date]
        ]
        item = dict(
            x=torch.from_numpy(x),
            y=torch.from_numpy(y),
            metadata=torch.tensor(metadata, dtype=torch.float32),
            chip=row.chip,
            event=row.event,
            part=0,
        )
        if self.feature_cache:
            item["features"] = torch.from_numpy(
                np.load(self.feature_cache / f"{row.chip}.npy", allow_pickle=False)
            )
        return item


def forward(model, batch, task, learner, device):
    if learner == "native" and "features" in batch:
        return model.forward_features(batch["features"].unbind(1))
    x = batch["x"].to(device)
    return model(x, batch["metadata"].to(device)) if learner == "native" else model(x)


def loss_for(outputs, labels, task, learner):
    if not (labels >= 0).any():
        return None
    if learner == "native":
        return change_loss(outputs, torch.where(labels < 0, 3, labels))
    return F.cross_entropy(outputs, labels, ignore_index=-1)


def score(model, loader, args, device, destination=None):
    model.eval()
    matrices = {}
    if destination:
        destination.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        for batch in loader:
            output = forward(model, batch, args.task, args.learner, device)
            logits = output[0] if args.learner == "native" else output
            predictions = logits.argmax(1).cpu().numpy()
            for i, event in enumerate(batch["event"]):
                label = batch["y"][i].numpy()
                matrices.setdefault(event, np.zeros((3, 3), dtype=np.int64))
                matrices[event] += confusion(label, predictions[i], classes=3)
                if destination:
                    np.savez_compressed(
                        destination / f"{batch['chip'][i]}.npz",
                        prediction=np.where(label >= 0, predictions[i], 255).astype(np.uint8),
                        unknown_code=255,
                    )
    values = {e: class_scores(m)["iou"][2] for e, m in matrices.items()}
    finite = [float(v) for v in values.values() if np.isfinite(v)]
    return dict(
        event_flood_iou={e: float(v) if np.isfinite(v) else None for e, v in values.items()},
        mean_event_flood_iou=float(np.mean(finite)) if finite else None,
        confusion={e: m.tolist() for e, m in matrices.items()},
    )
