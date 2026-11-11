"""Fixed support and counting conventions for the completed flood-map census."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path

import numpy as np
from rasterio.warp import reproject, Resampling

from limburg_chapter_scores import score_tile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/limburg_chapter_sized_v1/evaluation"
PACKETS = OUT / "support/tiles"
BITS = {"delivered_p0": 1, "ee_p0": 2, "ee_p1": 4, "ee_common": 8}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def remove_prior_coverage(eligible, transform, crs, previous):
    """Assign overlap using eligible support, including holes and different CRSs."""
    covered = np.zeros_like(eligible, dtype=np.uint8)
    for prior, old_transform, old_crs in previous:
        projected = np.zeros_like(eligible, dtype=np.uint8)
        reproject(prior, projected, src_transform=old_transform, src_crs=old_crs,
                  dst_transform=transform, dst_crs=crs,
                  resampling=Resampling.nearest, src_nodata=0, dst_nodata=0,
                  num_threads=1)
        covered |= projected
    return eligible & np.bitwise_not(covered)


@lru_cache(maxsize=8)
def packet(key):
    with np.load(PACKETS / f"{key}.npz", allow_pickle=False) as data:
        return {name: data[name] for name in data.files}


def score_prediction(key, dataset, reference, model, seed, prediction, valid):
    data = packet(key)
    expected_bit = BITS[f"{dataset}_{reference}"]
    expected_valid = (data["radar"] & expected_bit) != 0
    if not np.array_equal(valid, expected_valid):
        raise ValueError(f"Prediction support differs from checked input support: {key}/{dataset}/{reference}/{model}")
    if prediction.shape != valid.shape or prediction.dtype != np.uint8:
        raise ValueError(f"Invalid prediction grid/type: {key}")
    if np.any(prediction[~valid] != 255):
        raise ValueError(f"Unknown input has a predicted class: {key}")
    support_modes = [("full", expected_bit)]
    if dataset == "ee":
        support_modes.append(("paired", BITS["ee_common"]))
    rows = []
    for support, bit in support_modes:
        owned = (data["owner"] & bit) != 0
        for variant in ("composed", "mask_composition", "strict_validity", "boundary_interior"):
            if dataset == "ee" and support == "full" and variant != "composed":
                continue
            label = data["mask_label"] if variant == "mask_composition" else data["label"]
            known = owned.copy()
            if variant == "strict_validity":
                known &= data["strict_validity"]
            if variant == "boundary_interior":
                known &= data["boundary_interior"]
            result = score_tile(label, prediction, known)
            confusion = result.pop("confusion")
            rows.append({"key": key, "event": key.split("-")[0], "dataset": dataset,
                         "reference": reference, "model": model, "seed": seed,
                         "support": support, "variant": variant, **result,
                         **{f"c{i}{j}": confusion[i][j] for i in range(3) for j in range(3)}})
    return rows
