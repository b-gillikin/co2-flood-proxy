"""Bounded exact Galileo input caching; no learned transformations or new labels.

At446 chips each cache is under1GiB. Avoid repeated GeoTIFF opening for every
64px subpatch in every epoch. Raw controls receive the same source arrays.
"""

from functools import lru_cache
from pathlib import Path

import numpy as np
import rasterio

from applied_water import galileo_radar_norm, valid_labels


@lru_cache(maxsize=446)
def galileo_source(data, chip):
    data = Path(data)
    with rasterio.open(data / "LabelHand" / f"{chip}_LabelHand.tif") as src:
        label = src.read(1)
    with rasterio.open(data / "S1Hand" / f"{chip}_S1Hand.tif") as src:
        radar = src.read()
    target = valid_labels(label, s1=radar).astype(np.int8)
    raw = np.nan_to_num(galileo_radar_norm(radar), nan=0.5, posinf=0.5, neginf=0.5).astype(
        np.float32
    )
    return target, raw


@lru_cache(maxsize=446)
def galileo_features(directory, chip):
    return np.load(Path(directory) / f"{chip}.npy", allow_pickle=False)
