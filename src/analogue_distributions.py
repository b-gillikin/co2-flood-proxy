"""Scores for specified finite analogue distributions, without fitting or retrieval."""

from __future__ import annotations

import numpy as np
import pandas as pd


def normalized_weights(weights, count):
    weights = np.asarray(weights, dtype=float)
    if (
        weights.shape != (count,)
        or count == 0
        or not np.isfinite(weights).all()
        or (weights < 0).any()
        or weights.sum() <= 0
    ):
        raise ValueError("Finite nonnegative member weights with positive mass required")
    return weights / weights.sum()


def group_weights(groups):
    """Equal group mass; equal member mass within each group."""
    groups = pd.Series(np.asarray(groups))
    if groups.empty or groups.isna().any():
        raise ValueError("Nonempty named groups required")
    return 1.0 / groups.map(groups.value_counts()).to_numpy(float) / groups.nunique()


def distribution_parameters(members, weights):
    """Precompute means, inverse-CDF quantiles and half the pairwise distance.

    Members are rows, leads columns. No verification observation is accepted.
    The quantile is the smallest value with CDF >= p (tolerance 1e-14).
    Sorting costs O(m log m), avoiding the archive's O(m**2) pairwise array.
    """
    x = np.asarray(members, dtype=float)
    if x.ndim != 2 or not x.shape[1] or not np.isfinite(x).all():
        raise ValueError("Complete two-dimensional member trajectories required")
    w = normalized_weights(weights, len(x))
    order = np.argsort(x, axis=0, kind="stable")
    sx = np.take_along_axis(x, order, axis=0)
    sw = np.broadcast_to(w[:, None], x.shape)
    sw = np.take_along_axis(sw, order, axis=0)
    cumulative = np.cumsum(sw, axis=0)
    cumulative[-1] = 1.0
    quantiles = {}
    for name, probability in [
        ("lower80", 0.1),
        ("lower50", 0.25),
        ("median", 0.5),
        ("upper50", 0.75),
        ("upper80", 0.9),
    ]:
        positions = (cumulative >= probability - 1e-14).argmax(axis=0)
        quantiles[name] = sx[positions, np.arange(x.shape[1])]
    return {
        "mean": w @ x,
        "half_pair_distance": (sw * sx * (2 * cumulative - sw - 1)).sum(axis=0),
        **quantiles,
    }


def score_distribution(query, members, weights, parameters=None):
    """Exact CRPS and pointwise interval diagnostics of the empirical measure.

    This is not an iid-sample correction or a claim of calibrated probability.
    Closed interval coverage includes ties at either boundary.
    """
    x = np.asarray(members, dtype=float)
    y = np.asarray(query, dtype=float)
    if x.ndim != 2 or y.shape != (x.shape[1],) or not np.isfinite(y).all():
        raise ValueError("One finite verification value per lead required")
    w = normalized_weights(weights, len(x))
    p = distribution_parameters(x, w) if parameters is None else parameters
    crps = w @ np.abs(x - y) - p["half_pair_distance"]
    if not np.isfinite(crps).all() or (crps < -1e-12).any():
        raise ValueError("Invalid CRPS")
    result = pd.DataFrame(
        {
            "lead_hour": np.arange(1, len(y) + 1),
            "observed": y,
            "mean": p["mean"],
            "median": p["median"],
            "crps": np.maximum(crps, 0),
            "median_absolute_error": np.abs(p["median"] - y),
            "mean_squared_error": (p["mean"] - y) ** 2,
        }
    )
    for level in [50, 80]:
        lower, upper = p[f"lower{level}"], p[f"upper{level}"]
        result[f"lower{level}"] = lower
        result[f"upper{level}"] = upper
        result[f"coverage{level}"] = (y >= lower) & (y <= upper)
        result[f"width{level}"] = upper - lower
        result[f"below{level}"] = y < lower
        result[f"above{level}"] = y > upper
    return result


def eligible_archive(pool, query, other_rivers=False):
    """A prefiltered original cohort; outcomes never rank or select its members."""
    prior = pool.loc[
        pool.onset_utc.lt(query.onset_utc)
        & pool.onset_utc.add(pd.Timedelta(hours=72)).le(query.onset_utc)
        & pool.storm_id.ne(query.storm_id)
        & pool.event_id.ne(query.event_id)
    ]
    if other_rivers:
        prior = prior.loc[prior.physical_river_group.ne(query.physical_river_group)]
    return prior.sort_values("event_id")


def cluster_intervals(differences, labels, draws=9999, seed=20261013):
    """Joint bootstrap of intact query clusters for several paired endpoints.

    Fixed-size chunks bound memory. Returns all finite draws for an audit to
    verify rather than silently discard failures. Columns are arbitrary metrics.
    """
    values = np.asarray(differences, dtype=float)
    labels = pd.Series(np.asarray(labels))
    if values.ndim != 2 or len(values) != len(labels) or not len(values):
        raise ValueError("Nonempty paired rows and matching cluster labels required")
    if not np.isfinite(values).all() or labels.isna().any() or draws < 1:
        raise ValueError("Finite differences, named clusters and positive draws required")
    codes, unique = pd.factorize(labels, sort=True)
    if len(unique) < 2:
        return None
    sums = np.zeros((len(unique), values.shape[1]))
    np.add.at(sums, codes, values)
    sizes = np.bincount(codes)
    rng = np.random.default_rng(seed)
    samples = np.empty((draws, values.shape[1]))
    for first in range(0, draws, 256):
        picks = rng.integers(0, len(unique), size=(min(256, draws - first), len(unique)))
        samples[first : first + len(picks)] = (
            sums[picks].sum(axis=1) / sizes[picks].sum(axis=1)[:, None]
        )
    if not np.isfinite(samples).all():
        raise ValueError("Nonfinite bootstrap draw; no draws have been dropped")
    return samples
