"""Native-grid map agreement on explicit known support."""

from __future__ import annotations

import numpy as np


def score_tile(label: np.ndarray, prediction: np.ndarray, radar_valid: np.ndarray,
               pixel_area_m2: float = 100.0) -> dict:
    """Score flooded/permanent/background classes; 255 and invalid are unknown."""
    y = np.asarray(label)
    p = np.asarray(prediction)
    v = np.asarray(radar_valid, dtype=bool)
    if y.shape != p.shape or y.shape != v.shape:
        raise ValueError("Target, prediction and support grids differ")
    if pixel_area_m2 <= 0:
        raise ValueError("Pixel area must be positive")
    known = v & (y != 255)
    if not set(np.unique(y[known]).tolist()) <= {0, 1, 2} or not set(np.unique(p[known]).tolist()) <= {0, 1, 2}:
        raise ValueError("Unexpected class on scored support")
    counts = np.bincount((3 * y[known] + p[known]).astype(np.int64), minlength=9).reshape(3, 3)
    true_flood = counts[2].sum()
    predicted_flood = counts[:, 2].sum()
    true_positive = counts[2, 2]
    false_positive = predicted_flood - true_positive
    false_negative = true_flood - true_positive
    union = true_positive + false_positive + false_negative
    return {
        "confusion": counts.tolist(), "known_pixels": int(known.sum()),
        "target_flood_pixels": int(true_flood), "predicted_flood_pixels": int(predicted_flood),
        "flood_iou": float(true_positive / union) if union else None,
        "permanent_as_flood_pixels": int(counts[1, 2]),
        "flood_as_permanent_pixels": int(counts[2, 1]),
        "false_flood_km2": float(false_positive * pixel_area_m2 / 1e6),
        "missed_flood_km2": float(false_negative * pixel_area_m2 / 1e6),
        "target_flood_km2": float(true_flood * pixel_area_m2 / 1e6),
    }


def paired_support(label: np.ndarray, valid_p0: np.ndarray, valid_p1: np.ndarray) -> np.ndarray:
    """The within-tile reference contrast is only on identically assessable pixels."""
    if label.shape != valid_p0.shape or label.shape != valid_p1.shape:
        raise ValueError("Paired support grids differ")
    return (label != 255) & valid_p0 & valid_p1
