"""Available-information analogue assessment under declared local feed loss.

No p99 scaling, future-rain predictors, outcome-dependent ranking or training.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analogue_distributions import distribution_parameters, normalized_weights

HOUR = pd.Timedelta(hours=1)
OFFSETS = [0, 6, 12, 24]
DELAYS = [0, 1, 3, 6, 12, 24]
METRICS = [
    "crps",
    "crps_h6",
    "crps_h12",
    "crps_h24",
    "rmse",
    "peak_error",
    "peak_time_error_h",
    "coverage80",
    "width80",
]


def information_states(offset):
    """Unique permitted time caps plus the scenario labels sharing each cap."""
    states = {}
    for delay in DELAYS:
        states.setdefault(offset - delay, []).append(f"delay_{delay}")
    states.setdefault(0, []).append("outage")
    states.setdefault(-6, []).append("early_outage")
    return states


def last_observed_positions(values):
    a = np.asarray(values, float)
    return np.maximum.accumulate(np.where(np.isfinite(a), np.arange(len(a)), -1))


def q_signature(values, position, cap, latest_positions):
    """Read only a real observed prefix; true zero is valid, no gap filling."""
    end = position + cap
    if end < 0 or end >= len(values):
        return np.full(6, np.nan), -1
    s = int(latest_positions[end])
    if s < 24:
        return np.full(6, np.nan), s
    x = np.asarray(values)[[s, s - 6, s - 24]]
    return np.array([*x, x[0] - x[1], x[0] - x[2], position - s]), s


def prior_distances(prior, query, *, robust=True):
    """Prior-only robust scale and unique-prior RMS pair-distance scale."""
    p, q = np.asarray(prior, float), np.asarray(query, float)
    if p.ndim != 2 or q.shape != (p.shape[1],) or not len(p):
        raise ValueError("Nonempty prior feature rows and one matching query required")
    if not np.isfinite(p).all() or not np.isfinite(q).all():
        raise ValueError("Only finite permitted features can set distances")
    if robust:
        center = np.median(p, axis=0)
        iqr = np.quantile(p, 0.75, axis=0) - np.quantile(p, 0.25, axis=0)
        iqr[iqr == 0] = 1
        p, q = (p - center) / iqr, (q - center) / iqr
    unique = np.unique(p, axis=0)
    scale = (
        np.sqrt(2 * len(unique) / (len(unique) - 1) * unique.var(axis=0).sum())
        if len(unique) > 1
        else 0
    )
    return np.linalg.norm(p - q, axis=1), float(scale) if scale > 0 else 1.0


def eligible_donors(meta, query, offset, *, other_rivers=False):
    """Whole-storm exclusion, completed labels and known closed donor episodes."""
    issue = query.cutoff_utc + offset * HOUR
    mask = meta.cutoff_utc + (offset + 24) * HOUR <= issue
    mask &= meta.end_utc.add(12 * HOUR).le(issue)
    mask &= meta.storm_id.ne(query.storm_id)
    if other_rivers:
        mask &= meta.physical_river.ne(query.physical_river)
    else:
        mask &= meta.gauge.eq(query.gauge)
    return mask.to_numpy()


def select_distinct(indices, distances, storms, limit=10):
    """Stable input-row tie break, one representative per regional donor storm."""
    order = np.lexsort((indices, distances))
    chosen, seen = [], set()
    for i in indices[order]:
        if storms[i] in seen:
            continue
        chosen.append(int(i))
        seen.add(storms[i])
        if len(chosen) == limit:
            break
    return chosen


def native_members(responses, indices, areas, query_area):
    """Area-based transfer; within-gauge ratios are exactly one."""
    return responses[indices] * (query_area / areas[indices, None])


def ensemble_metrics(query, members, weights=None):
    """Native-unit 24h scores, allowing dry/flat nonresponses without peak gates."""
    y, a = np.asarray(query, float), np.asarray(members, float)
    if y.shape != (24,) or a.ndim != 2 or a.shape[1] != 24 or not np.isfinite(y).all():
        raise ValueError("Complete 24-hour query and member trajectories required")
    w = normalized_weights(np.ones(len(a)) if weights is None else weights, len(a))
    p = distribution_parameters(a, w)
    crps = w @ np.abs(a - y) - p["half_pair_distance"]
    if not np.isfinite(crps).all() or np.any(crps < -1e-10):
        raise ValueError("Invalid empirical CRPS")
    mean = p["mean"]
    # Flat/nonresponsive series have no identifiable peak time. Tied nonflat
    # maxima are sets, not an arbitrary first-hour timing claim.
    timing = np.nan
    if np.ptp(y) > 0 and np.ptp(mean) > 0:
        yp, mp = np.flatnonzero(y == y.max()), np.flatnonzero(mean == mean.max())
        timing = float(np.abs(yp[:, None] - mp).min())
    return dict(
        crps=float(np.maximum(crps, 0).mean()),
        crps_h6=float(max(crps[5], 0)),
        crps_h12=float(max(crps[11], 0)),
        crps_h24=float(max(crps[23], 0)),
        rmse=float(np.sqrt(np.mean((mean - y) ** 2))),
        peak_error=float(abs(mean.max() - y.max())),
        peak_time_error_h=timing,
        coverage80=float(((y >= p["lower80"]) & (y <= p["upper80"])).mean()),
        width80=float((p["upper80"] - p["lower80"]).mean()),
    )


def score_rows(query, members, *, areascale, weights=None):
    metrics = ensemble_metrics(query, members, weights)
    for name in ["crps", "crps_h6", "crps_h12", "crps_h24", "rmse", "peak_error", "width80"]:
        metrics[name + "_specific"] = metrics[name] * areascale
    return metrics
