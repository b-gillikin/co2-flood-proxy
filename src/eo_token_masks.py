"""Observation-only block masks for encoders requiring block-consistent masks."""

import numpy as np


def token_observations(valid, stride):
    """Keep a token only when every pixel it consumes is observed.

    This is a native input-support rule, not a catchment coverage threshold.
    Missing pixels are never promoted to observations. Padded edges stay absent.
    """
    valid = np.asarray(valid, dtype=bool)
    h, w = valid.shape[-2:]
    if h % stride or w % stride:
        raise ValueError("Spatial dimensions must be divisible by token stride")
    blocks = valid.reshape(*valid.shape[:-2], h // stride, stride, w // stride, stride)
    supported = blocks.all(axis=(-3, -1))
    return supported.repeat(stride, axis=-2).repeat(stride, axis=-1)
