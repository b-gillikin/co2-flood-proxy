"""Source-fixed SAR contracts for the chapter-sized flood-mapping study.

Scene selection uses acquisition/processing metadata only. Reference labels and
model scores never enter this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class SARScene:
    scene_id: str
    acquired: datetime
    platform: str
    relative_orbit: int
    pass_direction: str
    processing_contract: str
    covers_tile: bool


def updated_reference(delivered: SARScene, candidates: list[SARScene], onset: datetime) -> SARScene:
    """Return the latest compatible pre-onset scene, or the delivered P0 scene.

    `processing_contract` must describe calibration, correction, filtering,
    resampling and grid preparation together. A matching product name alone is
    insufficient evidence of compatibility.
    """
    if not delivered.acquired < onset:
        raise ValueError("Delivered reference must precede the event onset")
    eligible = [
        scene
        for scene in candidates
        if delivered.acquired < scene.acquired < onset
        and scene.platform == delivered.platform
        and scene.relative_orbit == delivered.relative_orbit
        and scene.pass_direction == delivered.pass_direction
        and scene.processing_contract == delivered.processing_contract
        and scene.covers_tile
    ]
    return max(eligible, key=lambda scene: (scene.acquired, scene.scene_id), default=delivered)


def raw_sar_db(raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert raw linear VV/VH pre/post backscatter to dB without model clipping.

    Caller must establish radiometric identity and common grid first. Nonpositive
    and nonfinite pixels remain invalid rather than becoming very dark water.
    """
    x = np.asarray(raw, dtype=np.float32)
    if x.ndim != 3 or x.shape[0] != 4:
        raise ValueError("Expected pre VV,VH followed by post VV,VH")
    valid = np.all(np.isfinite(x) & (x > 0), axis=0)
    out = np.full(x.shape, np.nan, dtype=np.float32)
    np.log10(x, out=out, where=np.broadcast_to(valid, x.shape))
    out *= 10
    return out, valid
