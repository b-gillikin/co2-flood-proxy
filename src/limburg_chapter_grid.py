"""Native-grid windows and probability stitching for 1024px flood tiles."""

from __future__ import annotations

from datetime import datetime
import math

import numpy as np
from pyproj import Transformer
from rasterio.transform import xy


def starts(length: int, patch: int = 224, overlap: int = 24) -> list[int]:
    if length < patch or patch <= overlap or overlap < 0:
        raise ValueError("Tile must fit a patch and overlap must be smaller than patch")
    count = math.ceil((length - patch) / (patch - overlap)) + 1
    return sorted(set(int(round(i * (length - patch) / (count - 1))) for i in range(count))) if count > 1 else [0]


def windows(height: int, width: int, patch: int = 224, overlap: int = 24) -> list[tuple[int, int]]:
    return [(row, col) for row in starts(height, patch, overlap) for col in starts(width, patch, overlap)]


def stitch_probabilities(
    pieces: list[tuple[int, int, np.ndarray]], height: int, width: int, classes: int = 3
) -> tuple[np.ndarray, np.ndarray]:
    """Average overlapping valid patch probabilities, retaining unknown pixels."""
    total = np.zeros((classes, height, width), dtype=np.float32)
    count = np.zeros((height, width), dtype=np.uint16)
    for top, left, values in pieces:
        x = np.asarray(values, dtype=np.float32)
        if x.ndim != 3 or x.shape[0] != classes or not (0 <= top <= height - x.shape[1] and 0 <= left <= width - x.shape[2]):
            raise ValueError("Patch shape or position does not fit target grid")
        good = np.all(np.isfinite(x), axis=0)
        view = total[:, top : top + x.shape[1], left : left + x.shape[2]]
        view += np.where(good[None], x, 0)
        count[top : top + x.shape[1], left : left + x.shape[2]] += good.astype(np.uint16)
    valid = count > 0
    total[:, valid] /= count[valid]
    total[:, ~valid] = np.nan
    return total, valid


def patch_metadata(transform, crs, top: int, left: int, patch: int,
                   pre_time: datetime, post_time: datetime, pixel_metres: float = 10.0) -> np.ndarray:
    """Use each crop's actual centre, sensing dates and model token area."""
    x, y = xy(transform, top + (patch - 1) / 2, left + (patch - 1) / 2)
    lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(x, y)
    epoch = datetime(1970, 1, 1, tzinfo=pre_time.tzinfo)
    return np.array([
        [lon, lat, (pre_time - epoch).days, (16 * pixel_metres / 1000) ** 2],
        [lon, lat, (post_time - epoch).days, (16 * pixel_metres / 1000) ** 2],
    ], dtype=np.float32)
