"""Explicit spatial-water data and evaluation conventions (not discharge inputs)."""

from __future__ import annotations

import numpy as np

PRITHVI_S2 = [1, 2, 3, 8, 11, 12]  # B2,B3,B4,B8A,B11,B12 in 13-band L1C


def valid_labels(label, s1=None, s2=None):
    """Unknown stays unknown; a valid dry pixel is retained, including dry chips."""
    if not set(np.unique(label).tolist()) <= {-1, 0, 1}:
        raise ValueError("Unexpected water label")
    result = label.astype(np.int64, copy=True)
    valid = label >= 0
    if s1 is not None:
        valid &= np.isfinite(s1).all(axis=0)
    if s2 is not None:
        valid &= np.isfinite(s2).all(axis=0) & (s2 != 0).any(axis=0)
    result[~valid] = -1
    return result


def galileo_radar_norm(s1):
    """Native eval.py default: OURS_S1, norm_no_clip, std_multiplier=2.

    This is mean +/- 2 std mapped to [0,1], without clipping. It is not z-score
    standardization and not the dataset-statistics normalization alternative.
    """
    means = np.array([-11.728724389184965, -18.85558188024017], dtype=np.float32)[:, None, None]
    stds = np.array([4.887145774840316, 5.730270320384293], dtype=np.float32)[:, None, None]
    return (s1 - (means - 2 * stds)) / (4 * stds)


def confusion(label, prediction, classes=2, ignore=-1):
    """Rows reference, columns prediction. No pixel accuracy masquerading as IoU."""
    y, p = np.asarray(label), np.asarray(prediction)
    if y.shape != p.shape:
        raise ValueError("Prediction/reference grids differ")
    valid = y != ignore
    if np.any((y[valid] < 0) | (y[valid] >= classes)) or np.any(
        (p[valid] < 0) | (p[valid] >= classes)
    ):
        raise ValueError("Invalid class on evaluated support")
    return np.bincount(
        classes * y[valid].astype(int) + p[valid].astype(int), minlength=classes**2
    ).reshape(classes, classes)


def class_scores(matrix):
    """Undefined denominators remain NaN, not perfect performance on dry terrain."""
    m = np.asarray(matrix, dtype=np.float64)
    tp = np.diag(m)
    fp, fn = m.sum(0) - tp, m.sum(1) - tp

    def ratio(a, b):
        return np.divide(a, b, out=np.full_like(a, np.nan), where=b > 0)

    return dict(
        iou=ratio(tp, tp + fp + fn),
        precision=ratio(tp, tp + fp),
        recall=ratio(tp, tp + fn),
        f1=ratio(2 * tp, 2 * tp + fp + fn),
        false_positive_pixels=fp,
        missed_pixels=fn,
        evaluated_pixels=int(m.sum()),
    )


def audit_partitions(frame):
    """Require disjoint whole events and a complete once-only held-event census."""
    roles = {"train", "valid", "test"}
    tested = []
    for fold, rows in frame.groupby("fold"):
        if set(rows.role) != roles or rows.chip.duplicated().any():
            raise ValueError("Incomplete roles or duplicated chip: " + str(fold))
        if (rows.groupby("event").role.nunique() != 1).any():
            raise ValueError("Event leakage: " + str(fold))
        tested.extend(rows.loc[rows.role == "test", "chip"])
    expected = set(frame.chip)
    if len(tested) != len(expected) or set(tested) != expected:
        raise ValueError("Held-event test rows do not cover the census exactly once")
