"""Observed-only raw controls and streaming weighted feature moments.

These functions never inspect discharge/outcomes. Empty support stays missing;
weights are physical area or explicitly named context-proxy weights.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Moments:
    weight: np.ndarray
    mean: np.ndarray
    m2: np.ndarray

    @classmethod
    def empty(cls, dimension):
        return cls(np.zeros(dimension), np.zeros(dimension), np.zeros(dimension))

    def add(self, values, weights):
        x = np.asarray(values, float).reshape(-1, len(self.mean))
        w = np.broadcast_to(np.asarray(weights, float).reshape(-1, 1), x.shape).copy()
        if (w < 0).any() or not np.isfinite(w).all():
            raise ValueError("Invalid area weights")
        w[~np.isfinite(x)] = 0
        total = w.sum(0)
        mean = np.divide(
            (np.where(np.isfinite(x), x, 0) * w).sum(0),
            total,
            out=np.zeros_like(total),
            where=total > 0,
        )
        m2 = (w * np.where(np.isfinite(x), (x - mean) ** 2, 0)).sum(0)
        self.merge(Moments(total, mean, m2))

    def merge(self, other):
        total = self.weight + other.weight
        delta = other.mean - self.mean
        ratio = np.divide(other.weight, total, out=np.zeros_like(total), where=total > 0)
        self.mean += delta * ratio
        self.m2 += other.m2 + delta**2 * np.divide(
            self.weight * other.weight, total, out=np.zeros_like(total), where=total > 0
        )
        self.weight = total

    def output(self):
        mean = np.where(self.weight > 0, self.mean, np.nan)
        variance = np.divide(
            self.m2, self.weight, out=np.full_like(mean, np.nan), where=self.weight > 0
        )
        return np.concatenate([mean, np.sqrt(np.maximum(variance, 0))])

    def arrays(self):
        return np.stack([self.weight, self.mean, self.m2])

    @classmethod
    def from_arrays(cls, arrays):
        return cls(*(np.array(a, float, copy=True) for a in arrays))


def channel_features(values, bands):
    """Raw bands plus only physically available named contrasts; no fake RGB."""
    values = np.asarray(values, float)
    out = [*values]
    names = list(bands)
    index = {b: i for i, b in enumerate(bands)}
    if "nir" in index:
        combos = [("NDVI", "nir", "red"), ("NDMI", "nir", "swir1"), ("MNDWI", "green", "swir1")]
    else:
        combos = [
            ("NDVI", "B8", "B4"),
            ("NDMI", "B8", "B11"),
            ("MNDWI", "B3", "B11"),
            ("NDRE", "B8", "B5"),
        ]
    for name, a, b in combos:
        if a in index and b in index:
            den = values[index[a]] + values[index[b]]
            out.append(
                np.divide(
                    values[index[a]] - values[index[b]],
                    den,
                    out=np.full_like(den, np.nan),
                    where=np.abs(den) > 1e-12,
                )
            )
            names.append(name)
    if "VV" in index and "VH" in index:
        out.append(values[index["VV"]] - values[index["VH"]])
        names.append("VV_minus_VH_dB")
    return np.stack(out), names


def texture(values, valid, area):
    """Masked adjacent-pixel contrast/correlation; undefined constants remain NaN."""
    values = np.asarray(values, float)
    valid = np.asarray(valid, bool)
    area = np.asarray(area, float)
    out = []
    for image in values:
        for axis in (0, 1):
            a = [slice(None)] * 2
            b = a.copy()
            a[axis] = slice(None, -1)
            b[axis] = slice(1, None)
            a, b = tuple(a), tuple(b)
            keep = valid[a] & valid[b] & np.isfinite(image[a]) & np.isfinite(image[b])
            w = np.minimum(area[a], area[b]) * keep
            if w.sum() == 0:
                out.extend([np.nan, np.nan])
                continue
            w = w / w.sum()
            x = image[a]
            y = image[b]
            x = np.where(keep, x, 0)
            y = np.where(keep, y, 0)
            mx, my = (x * w).sum(), (y * w).sum()
            vx, vy = ((x - mx) ** 2 * w).sum(), ((y - my) ** 2 * w).sum()
            corr = (
                (((x - mx) * (y - my) * w).sum() / np.sqrt(vx * vy))
                if vx > 0 and vy > 0
                else np.nan
            )
            out.extend([float(((x - y) ** 2 * w).sum()), float(corr)])
    return np.asarray(out)


def grid_weights(area, shape):
    """Sum native pixel area inside exact nonoverlapping token footprints."""
    area = np.asarray(area, float)
    h, w = shape
    if area.shape[0] % h or area.shape[1] % w:
        raise ValueError("Token grid does not divide input footprint")
    dy, dx = area.shape[0] // h, area.shape[1] // w
    return area.reshape(h, dy, w, dx).sum(axis=(1, 3))


def temporal_summary(frames):
    """Ordered levels and adjacent differences, retaining missing steps as NaN."""
    x = np.asarray(frames, float)
    return np.concatenate((x.reshape(-1), np.diff(x, axis=0).reshape(-1)))
