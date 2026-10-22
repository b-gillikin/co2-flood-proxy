"""Versioned S2 loader: retain only pixels whose 10m/20m bands share a UTC day.

This checks day coherence, not exact scene identity (held dates are day-quantized).
The original loader remains immutable for active and historical extractions.
"""

from __future__ import annotations

import numpy as np
from rasterio.enums import Resampling
from rasterio.warp import reproject

from src.eo_inputs import S2_BANDS, Tile, read_product, read_tile

POLICY = "s2_same_utc_day_mask_v2"


def s2_components(root, job, companions):
    """Read verified products once and align reflectance, validity and dates."""
    a, am, affine, crs, ar = read_product(root, job)
    other = companions[(job["window"]["id"], tuple(job["bounds"]), "s2_20m")]
    b, bm, bt, bc, br = read_product(root, other)
    bidx = [other["bands"].index(k) for k in ["B5", "B6", "B7", "B8A", "B11", "B12"]]
    bday = other["bands"].index("acquired_day")
    aday = job["bands"].index("acquired_day")
    up = np.empty((len(bidx) + 2, *a.shape[1:]), dtype=np.float32)
    coarse = [*b[bidx], b[bday], (bm[bidx].all(0) & bm[bday]).astype("float32")]
    for i, values in enumerate(coarse):
        reproject(
            values,
            up[i],
            src_transform=bt,
            src_crs=bc,
            dst_transform=affine,
            dst_crs=crs,
            resampling=Resampling.nearest,
        )
    aidx = [job["bands"].index(k) for k in ["B2", "B3", "B4", "B8"]]
    common = am[aidx].all(0) & am[aday] & up[-1].astype(bool)
    days_a, days_b = a[aday], up[-2]
    same = common & (days_a == days_b)
    values = np.concatenate([a[aidx], up[: len(bidx)]])
    names = ["B2", "B3", "B4", "B8", "B5", "B6", "B7", "B8A", "B11", "B12"]
    values = values[[names.index(k) for k in S2_BANDS]]
    return values, common, same, days_a, days_b, affine, crs, [ar, br]


def read_coherent_tile(root, job, companions):
    if job["product"] != "s2_10m":
        return read_tile(root, job, companions)
    values, common, same, da, db, affine, crs, sources = s2_components(root, job, companions)
    # Preserve raw arrays; explicit validity controls encoding and area accounting.
    for source in sources:
        source["joined_band_day_policy"] = POLICY
    observed = da[same]
    if observed.size:
        from datetime import datetime

        start = datetime.fromisoformat(job["window"]["start"]).timestamp() / 86400
        end = datetime.fromisoformat(job["window"]["end"]).timestamp() / 86400
        if observed.min() < np.floor(start) or observed.max() >= end:
            raise ValueError("Observed acquisition falls outside its completed UTC window")
    return Tile(values, same, da, S2_BANDS.copy(), affine, str(crs), sources, job["window"])
