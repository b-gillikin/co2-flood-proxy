"""Exclude patches where CROMA's publisher sample-SD transform is undefined.

Raw observations remain unchanged. The validity mask here is encoder-usable
support, with counts of actually observed but unsupported pixels in provenance.
"""

import numpy as np

from src.eo_expansion_inputs import POLICY as POLICY
from src.eo_expansion_inputs import read_coherent_tile as original_tile

SUPPORT_POLICY = "croma_sample_sd_defined_per_native_patch_v1"


def usable_support(values, valid, size=120):
    import torch

    supported = valid.copy()
    counts = {
        "one_pixel_patches": 0,
        "constant_channel_patches": 0,
        "unsupported_observed_pixels": 0,
    }
    for row in range(0, valid.shape[0], size):
        for col in range(0, valid.shape[1], size):
            mask = valid[row : row + size, col : col + size]
            count = int(mask.sum())
            if not count:
                continue
            reason = None
            if count < 2:
                reason = "one_pixel_patches"
            else:
                x = np.ascontiguousarray(values[:, row : row + size, col : col + size][:, mask])
                std = torch.from_numpy(x).float().std(1).numpy()
                if np.any(std <= 0) or not np.isfinite(std).all():
                    reason = "constant_channel_patches"
            if reason:
                supported[row : row + size, col : col + size] = False
                counts[reason] += 1
                counts["unsupported_observed_pixels"] += count
    return supported, counts


def read_coherent_tile(root, job, companions):
    tile = original_tile(root, job, companions)
    if job["product"] != "s1_ascending":
        raise ValueError("Sample-SD support wrapper is restricted to CROMA SAR")
    observed = int(tile.valid.sum())
    tile.valid, counts = usable_support(tile.values, tile.valid)
    for source in tile.sources:
        source.update(
            encoder_support_policy=SUPPORT_POLICY,
            raw_joint_observed_pixels=observed,
            encoder_usable_pixels=int(tile.valid.sum()),
            normalization_unsupported=counts,
        )
    return tile
