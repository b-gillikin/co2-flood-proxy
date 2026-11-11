#!/usr/bin/env python3
"""Select a raw-linear-SAR physical change rule using source labels only."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_sar import raw_sar_db

INVENTORY = ROOT / "results/applied_study_v5/evaluation/radar-change-inventory.parquet"
CACHE = ROOT / "data/processed/limburg_tensor_cache_v1/copernicus"
SOURCE = ROOT / "data/raw/limburg_applied_tasks/flood_s1/extracted/flood_s1/data"
OUT = ROOT / "results/limburg_chapter_sized_v1/physical"
THRESHOLDS = (-24.0, -21.0, -18.0, -15.0, -12.0)
DROPS = (0.0, 3.0, 6.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidates():
    return [(pol, threshold, drop) for pol in (0, 1) for threshold in THRESHOLDS for drop in DROPS]


def predict_flood(db: np.ndarray, candidate) -> np.ndarray:
    pol, threshold, drop = candidate
    before, after = db[pol], db[pol + 2]
    return (before >= threshold) & (after < threshold) & ((before - after) >= drop)


def predict_classes(db: np.ndarray, valid: np.ndarray, candidate) -> np.ndarray:
    pol, threshold, drop = candidate
    before, after = db[pol], db[pol + 2]
    output = np.zeros(before.shape, dtype=np.uint8)
    output[(before < threshold) & (after < threshold) & valid] = 1
    output[predict_flood(db, candidate) & valid] = 2
    output[~valid] = 255
    return output


def raw_pair(folder: Path) -> np.ndarray:
    bands = []
    grid = None
    for prefix in ("SL1_IVV", "SL1_IVH", "MS1_IVV", "MS1_IVH"):
        paths = list(folder.glob(prefix + "*.tif"))
        if len(paths) != 1:
            raise ValueError(f"Expected one {prefix} in {folder}")
        with rasterio.open(paths[0]) as ds:
            signature = (ds.shape, ds.transform, ds.crs)
            if grid is not None and grid != signature:
                raise ValueError(f"Source SAR grid mismatch in {folder}")
            grid = signature
            bands.append(ds.read(1))
    return np.stack(bands)


def main() -> None:
    rows = pd.read_parquet(INVENTORY).rename(columns={"record": "chip"})
    index = json.loads((CACHE / "index.json").read_text())
    if len(rows) != 5000 or rows.chip.nunique() != 5000 or rows.event.nunique() != 20:
        raise ValueError("Source cohort changed")
    lookup = {r["chip"]: r["position"] for r in index["rows"]}
    if set(rows.chip) != set(lookup):
        raise ValueError("Source labels and raw radar identities differ")
    labels = np.load(CACHE / "y.npy", mmap_mode="r", allow_pickle=False)
    choices = candidates()
    counts = defaultdict(lambda: np.zeros((len(choices), 3), dtype=np.int64))
    for n, row in enumerate(rows.itertuples(), 1):
        db, valid = raw_sar_db(raw_pair(SOURCE / row.source_path))
        label = labels[lookup[row.chip]]
        support = valid & (label >= 0)
        positive = support & (label == 2)
        negative = support & (label != 2)
        for i, choice in enumerate(choices):
            predicted = predict_flood(db, choice)
            counts[row.event][i] += (
                int(np.count_nonzero(predicted & positive)),
                int(np.count_nonzero(predicted & negative)),
                int(np.count_nonzero(~predicted & positive)),
            )
        if n % 500 == 0:
            print(json.dumps({"source_chips": n, "total": len(rows)}), flush=True)
    scores = []
    for i, choice in enumerate(choices):
        event_iou = {}
        for event, matrix in counts.items():
            tp, fp, fn = matrix[i]
            union = tp + fp + fn
            event_iou[event] = float(tp / union) if union else None
        values = [x for x in event_iou.values() if x is not None]
        scores.append({"polarization": ("VV", "VH")[choice[0]],
                       "threshold_db": choice[1], "drop_db": choice[2],
                       "mean_event_flood_iou": float(np.mean(values)) if values else None,
                       "defined_events": len(values), "event_iou": event_iou})
    winner = max(scores, key=lambda x: (x["mean_event_flood_iou"] or -1,
                                         -x["threshold_db"], -x["drop_db"], x["polarization"]))
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"status": "source_only_selected", "source_records": len(rows),
              "source_events": rows.event.nunique(), "raw_linear_to_db": True,
              "source_inventory_sha256": sha256(INVENTORY),
              "source_label_index_sha256": sha256(CACHE / "index.json"),
              "runner_sha256": sha256(Path(__file__)), "selected": winner,
              "candidates": scores,
              "note": "All 30 prespecified rules use raw un-clipped linear backscatter and source labels; no target data or labels calibrate thresholds."}
    (OUT / "calibration.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"selected": winner, "candidates": len(scores)}, indent=2))


if __name__ == "__main__":
    main()
