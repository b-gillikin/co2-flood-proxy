"""Fixed retrospective assessment helpers; outcome values never enter retrieval."""

from __future__ import annotations

import numpy as np

from src.analogue_distributions import score_distribution
from src.eo_followup import archive_metrics


def pair_scale(values):
    a = np.unique(np.asarray(values, float), axis=0)
    scale = np.sqrt(2 * len(a) / (len(a) - 1) * a.var(axis=0).sum()) if len(a) > 1 else 0
    return float(scale) if scale > 0 else 1.0


def normalized_block(prior, query, robust=False):
    p, q = np.asarray(prior, float), np.asarray(query, float)
    if not np.isfinite(p).all() or not np.isfinite(q).all() or not len(p):
        raise ValueError("Finite prior-only block and query required")
    if robust:
        median = np.median(p, axis=0)
        iqr = np.quantile(p, 0.75, axis=0) - np.quantile(p, 0.25, axis=0)
        iqr = np.where(iqr == 0, 1.0, iqr)
        p, q = (p - median) / iqr, (q - median) / iqr
    return p, q


def baseline_distance(prior, query, conventional=None, temporal=None, state=None):
    """Return unchanged conventional or TTM/state distance and its pair RMS."""
    if conventional is not None:
        p, q = normalized_block(conventional.loc[prior], conventional.loc[query], True)
    else:
        blocks, queries = [], []
        for f, robust in [(temporal, False), (state, True)]:
            p, q = normalized_block(f.loc[prior], f.loc[query], robust)
            scale = pair_scale(p)
            blocks.append(p / scale / np.sqrt(2))
            queries.append(q / scale / np.sqrt(2))
        p, q = np.hstack(blocks), np.concatenate(queries)
    return np.linalg.norm(p - q, axis=1), pair_scale(p)


def add_context(base_distance, base_scale, prior, query):
    p, q = normalized_block(prior, query, True)
    scale = pair_scale(p)
    d = np.linalg.norm(p - q, axis=1)
    augmented = np.sqrt(0.5 * (base_distance / base_scale) ** 2 + 0.5 * (d / scale) ** 2)
    return augmented, d, scale


def selected_rows(candidates, distances, limit=10):
    """Stable existing tie rules and one completed event per regional group."""
    return (
        candidates.assign(distance=distances)
        .sort_values(["distance", "onset_utc", "event_id"])
        .drop_duplicates("storm_id")
        .head(limit)
    )


def scores(query, members, weights=None):
    a, q = np.asarray(members, float), np.asarray(query, float)
    if weights is None:
        weights = np.ones(len(a)) / len(a)
    w = np.asarray(weights, float)
    # Distinct selected storms imply equal-member weighting; archive may be grouped.
    groups = np.arange(len(a))
    metrics = archive_metrics(q, a, groups) if np.allclose(w, 1 / len(a)) else {}
    if not metrics:
        curve = w @ a
        peaks = a.max(axis=1)
        metrics = dict(
            mean_peak_scaled_shape_rmse=float(
                w @ np.sqrt(((a / peaks[:, None] - q / q.max()) ** 2).mean(1))
            ),
            mean_donor_peak_absolute_error=float(abs(w @ peaks - q.max())),
            ensemble_curve_level_rmse=float(np.sqrt(((curve - q) ** 2).mean())),
            mean_peak_time_difference_h=float(w @ abs(a.argmax(1) - q.argmax())),
            duration_estimate_absolute_error_h=float(abs(w @ (a >= 1).sum(1) - (q >= 1).sum())),
            final_24h_level_absolute_error=float(abs(curve[-24:].mean() - q[-24:].mean())),
        )
    hourly = score_distribution(q[:24], a[:, :24], w)
    for field in ["crps", "coverage80", "width80", "above80", "below80"]:
        metrics[field + "_mean_24h"] = float(hourly[field].mean())
        for h in [6, 12, 24]:
            metrics[f"{field}_h{h}"] = float(hourly.iloc[h - 1][field])
    return metrics


def decompose(full, restricted, augmented):
    if not np.isfinite([full, restricted, augmented]).all():
        raise ValueError("Paired finite scores required")
    return dict(
        archive_difference=restricted - full,
        representation_difference=augmented - restricted,
        total_difference=augmented - full,
    )


def fallback_choice(query_complete, restricted_donors):
    return "augmented" if query_complete and restricted_donors > 0 else "full_baseline"
