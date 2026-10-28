"""Same intact-cluster bootstrap as eo_followup, with reusable draw counts."""

from __future__ import annotations

from functools import lru_cache

import numpy as np


@lru_cache(maxsize=16)
def draw_counts(clusters, draws, seed):
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, clusters, size=(draws, clusters))
    offsets = np.arange(draws, dtype=np.int64)[:, None] * clusters
    counts = np.bincount((picks + offsets).ravel(), minlength=draws * clusters)
    out = counts.reshape(draws, clusters).astype(float)
    out.setflags(write=False)
    return out


def joint_intervals(frame, cluster, columns, draws=9999, seed=20261013):
    if frame.empty or frame[columns].isna().any().any() or frame[cluster].isna().any():
        raise ValueError("Complete paired differences and labels required")
    grouped = frame.groupby(cluster, sort=True)[columns].sum()
    sizes = frame.groupby(cluster, sort=True).size().to_numpy()
    means = frame[columns].mean().to_numpy()
    n = len(grouped)
    if n < 2:
        return {
            c: dict(
                difference=float(means[i]),
                query_count=len(frame),
                cluster_count=n,
                draws=0,
                finite_draws=0,
                lower=np.nan,
                upper=np.nan,
            )
            for i, c in enumerate(columns)
        }
    counts = draw_counts(n, draws, seed)
    values = (counts @ grouped.to_numpy()) / (counts @ sizes)[:, None]
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite bootstrap draw; nothing dropped")
    bounds = np.quantile(values, [0.025, 0.975], axis=0)
    return {
        c: dict(
            difference=float(means[i]),
            query_count=len(frame),
            cluster_count=n,
            draws=draws,
            finite_draws=draws,
            lower=float(bounds[0, i]),
            upper=float(bounds[1, i]),
        )
        for i, c in enumerate(columns)
    }
