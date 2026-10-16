"""Event/window linkage and area accounting for held EO inputs; no event fitting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely import area, box, intersection

GERMAN_GAUGES = {"2828300000200": "herzogenrath_1", "2828900000200": "randerath"}
SEQUENCES = {"monthly_snapshot": 1, "monthly": 12, "recent": 4}
NATIVE_TEMPORAL = {"olmoearth", "galileo", "anysat", "prithvi", "presto"}


def completed_windows(cutoff, kind):
    cutoff = pd.Timestamp(cutoff)
    if cutoff.tzinfo is None:
        raise ValueError("Aware UTC cutoff required")
    cutoff = cutoff.tz_convert("UTC")
    end = (
        cutoff.normalize().replace(day=1)
        if kind.startswith("monthly")
        else cutoff.normalize() - pd.Timedelta(days=cutoff.weekday())
    )
    windows = []
    for _ in range(SEQUENCES[kind]):
        start = end - (
            pd.DateOffset(months=1) if kind.startswith("monthly") else pd.Timedelta(days=7)
        )
        windows.append(
            {
                "id": f"{'monthly' if kind.startswith('monthly') else kind}_{start:%Y%m%d}_{end:%Y%m%d}",
                "kind": kind,
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        )
        end = start
    return windows[::-1]


def context_id(kind, windows):
    return (
        kind
        + "_"
        + hashlib.sha256(json.dumps([w["id"] for w in windows]).encode()).hexdigest()[:20]
    )


def pixel_area_weights(geometry, bounds, resolution):
    """Exact polygon/pixel intersections; rasterization only locates boundary cells.

    Interior cells have full area. Boundary cells (including holes) are clipped
    exactly. Never renormalize the catchment to the downloaded spatial subset.
    """
    xmin, ymin, xmax, ymax = bounds
    width, height = round((xmax - xmin) / resolution), round((ymax - ymin) / resolution)
    affine = from_origin(xmin, ymax, resolution, resolution)
    clipped = geometry.intersection(box(*bounds))
    if clipped.is_empty:
        return np.zeros((height, width), dtype=np.float64)
    weights = (
        rasterize(
            [(clipped, 1)], out_shape=(height, width), transform=affine, dtype="uint8"
        ).astype(np.float64)
        * resolution**2
    )
    boundary = rasterize(
        [(clipped.boundary, 1)],
        out_shape=(height, width),
        transform=affine,
        all_touched=True,
        dtype="uint8",
    )
    rows, cols = np.nonzero(boundary)
    cells = box(
        xmin + cols * resolution,
        ymax - (rows + 1) * resolution,
        xmin + (cols + 1) * resolution,
        ymax - rows * resolution,
    )
    weights[rows, cols] = area(intersection(cells, clipped))
    if not np.isclose(weights.sum(), clipped.area, rtol=1e-8, atol=1e-5):
        raise ValueError("Pixel weights do not conserve polygon area")
    return weights


def observed_patch_area(weights, valid, row, col):
    h, w = valid.shape
    subset = weights[row : row + h, col : col + w]
    if not subset.size:
        return 0.0
    return float((subset * valid[: subset.shape[0], : subset.shape[1]]).sum())


def aggregate_vectors(vectors, weights, full_area):
    """Observed-area-weighted patch-feature proxy, with untruncated denominator."""
    vectors = np.asarray(vectors, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if vectors.ndim != 2 or weights.shape != (len(vectors),) or not np.isfinite(vectors).all():
        raise ValueError("Finite aligned vectors required")
    if full_area <= 0 or not np.isfinite(weights).all() or (weights < 0).any():
        raise ValueError("Invalid areas")
    observed = float(weights.sum())
    if observed > full_area * (1 + 1e-7):
        raise ValueError("Overlapping/double-counted patch support")
    if observed == 0:
        return None, 0.0
    return np.average(vectors, axis=0, weights=weights), observed / full_area


def load_contexts(path):
    return {c["context_id"]: c for c in json.loads(Path(path).read_text())}
