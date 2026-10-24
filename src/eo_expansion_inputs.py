"""Supplemental input views preserve native product identities in source receipts.

S2 TOA is a separate sensitivity, never relabelled as surface reflectance.
Missing QA60 does not establish clear sky; radar orbits are never pooled.
"""

import numpy as np
from rasterio.enums import Resampling
from rasterio.warp import reproject

from src.eo_coherent_inputs import read_coherent_tile as original_tile
from src.eo_inputs import read_product

POLICY = "s2_toa_same_utc_day_qa60_clear_v1"


def clear_mask(qa, qa_valid, qa_day, reflectance_day):
    flags = qa.astype(np.uint16)
    return qa_valid & (qa_day == reflectance_day) & ((flags & ((1 << 10) | (1 << 11))) == 0)


def read_coherent_tile(root, job, companions):
    tile = original_tile(root, job, companions)
    if job["product"] != "s2_10m":
        return tile
    other = companions[(job["window"]["id"], tuple(job["bounds"]), "s2_toa_qa60")]
    values, masks, affine, crs, receipt = read_product(root, other)
    q = other["bands"].index("QA60")
    d = other["bands"].index("acquired_day")
    aligned = np.zeros((3, *tile.valid.shape), dtype=np.float32)
    for i, source in enumerate([values[q], values[d], (masks[q] & masks[d]).astype(np.float32)]):
        reproject(
            source,
            aligned[i],
            src_transform=affine,
            src_crs=crs,
            dst_transform=tile.transform,
            dst_crs=tile.crs,
            resampling=Resampling.nearest,
        )
    tile.valid &= clear_mask(aligned[0], aligned[2].astype(bool), aligned[1], tile.days)
    receipt["joined_band_day_policy"] = POLICY
    tile.sources.append(receipt)
    for source in tile.sources:
        source["reflectance_level"] = "TOA"
        source["supplemental_input_policy"] = POLICY
    return tile
