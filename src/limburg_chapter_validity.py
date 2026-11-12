"""Post-result validity diagnostics; never change labels or acquisition selection."""

from __future__ import annotations

import numpy as np


def compare_geometry(first: dict, second: dict) -> dict:
    """Check metadata compatibility, without claiming equal pixel incidence angles.

    Different constellation platforms may share a relative track. Platform equality
    is reported separately, not required for cross-platform track compatibility.
    Missing fields never count as matched. A known contradiction takes precedence.
    """
    fields = ("relative_orbit", "pass_direction", "mode", "polarizations", "look")
    missing, mismatched = [], []
    for field in fields:
        a, b = first.get(field), second.get(field)
        if not a or not b:
            missing.append(field)
        elif a != b:
            mismatched.append(field)
    return {
        "status": "mismatch" if mismatched else "unknown" if missing else "compatible",
        "missing": ",".join(missing),
        "mismatched": ",".join(mismatched),
        "same_platform": bool(
            first.get("platform") and first.get("platform") == second.get("platform")
        ),
    }


def label_transition_counts(
    label: np.ndarray, alternative: np.ndarray, support: np.ndarray
) -> np.ndarray:
    """Compare two fixed target constructions, preserving unknown as its own class."""
    y, z, v = np.asarray(label), np.asarray(alternative), np.asarray(support, dtype=bool)
    if y.shape != z.shape or y.shape != v.shape:
        raise ValueError("Target construction grids differ")
    for a in (y, z):
        if not np.isin(a[v], [0, 1, 2, 255]).all():
            raise ValueError("Unknown target encoding")
    a = np.where(y[v] == 255, 3, y[v]).astype(np.int16)
    b = np.where(z[v] == 255, 3, z[v]).astype(np.int16)
    return np.bincount(4 * a + b, minlength=16).reshape(4, 4)
