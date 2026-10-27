"""Read-only follow-up contracts for completed retrospective analogue comparisons."""

from __future__ import annotations

import numpy as np
import pandas as pd

METRICS = [
    "mean_peak_scaled_shape_rmse",
    "mean_donor_peak_absolute_error",
    "ensemble_curve_level_rmse",
    "mean_peak_time_difference_h",
    "duration_estimate_absolute_error_h",
    "final_24h_level_absolute_error",
]


def feature_complete(sample, feature_columns):
    """Require the predictors actually used, not an inherited longer rain window."""
    return sample.complete_scoring_sample.astype(bool) & sample[feature_columns].notna().all(axis=1)


def eligible_archive(population, query, scenario, policy, quality):
    frame = population[population.complete_scoring_sample.astype(bool)].copy()
    if quality:
        frame = frame[~frame.measurement_concern.astype(bool)]
    frame = frame[
        (frame.onset_utc + pd.Timedelta(hours=72) <= query.onset_utc)
        & (frame.onset_utc < query.onset_utc)
        & frame.storm_id.ne(query.storm_id)
        & frame.event_id.ne(query.event_id)
    ]
    if scenario == "other_rivers":
        frame = frame[frame.physical_river_group.ne(query.physical_river_group)]
    elif scenario != "all_rivers":
        raise ValueError("Unknown river policy")
    if policy == "domestic":
        frame = frame[frame.country.eq(query.country)]
    elif policy == "foreign":
        frame = frame[frame.country.ne(query.country)]
    elif policy != "pooled":
        raise ValueError("Unknown country policy")
    return frame


def archive_metrics(query, candidates, groups):
    """Equal storm mass; retain individual similarity versus aggregate-estimate distinction."""
    q = np.asarray(query, float)
    a = np.asarray(candidates, float)
    g = pd.Series(np.asarray(groups))
    if q.shape != (72,) or a.ndim != 2 or a.shape[1] != 72 or len(a) != len(g) or not len(a):
        raise ValueError("Complete nonempty matched responses required")
    if (
        not np.isfinite(q).all()
        or not np.isfinite(a).all()
        or g.isna().any()
        or q.max() <= 0
        or (a.max(1) <= 0).any()
    ):
        raise ValueError("Finite positive peaks and storm IDs required")
    weights = 1 / g.map(g.value_counts()).to_numpy(float) / g.nunique()
    curve = weights @ a
    peaks = a.max(1)
    return {
        "mean_peak_scaled_shape_rmse": float(
            weights @ np.sqrt(((a / peaks[:, None] - q / q.max()) ** 2).mean(1))
        ),
        "mean_donor_peak_absolute_error": float(abs(weights @ peaks - q.max())),
        "ensemble_curve_level_rmse": float(np.sqrt(((curve - q) ** 2).mean())),
        "mean_peak_time_difference_h": float(weights @ np.abs(a.argmax(1) - q.argmax())),
        "duration_estimate_absolute_error_h": float(
            abs(weights @ (a >= 1).sum(1) - (q >= 1).sum())
        ),
        "final_24h_level_absolute_error": float(abs(curve[-24:].mean() - q[-24:].mean())),
    }


def review_input_note(contract):
    """Describe actual immutable input routes; make no blanket reuse assertion."""
    routes = []
    supplement = False
    for model, item in sorted(contract.items()):
        location = (item.get("input_population") or {}).get("jobs_location", {}).get("path", "")
        policy = item.get("input_policy", "native product / legacy extraction")
        if "eo_expansion_input_views" in location:
            route = location.split("eo_expansion_input_views/", 1)[1].split("/", 1)[0]
            supplement = True
        else:
            route = "original compact archive"
        routes.append(f"{model}: {route}; {policy}")
    prefix = (
        "Includes supplemental Azure-acquired imagery; source routes and usable populations differ. "
        if supplement
        else "Original compact-archive representations, with their selected extraction policies. "
    )
    return (
        prefix
        + " ".join(routes)
        + " No architecture-only or isolated reflectance-effect claim is implied."
    )


def cluster_intervals_multi(frame, cluster, columns, draws=9999, seed=20261013):
    """Same intact-cluster bootstrap for several differences, sharing random draws.

    Chunking bounds memory; the estimator and RNG sequence match the established
    scalar routine. This changes computation cost, not resampling units.
    """
    if frame.empty or frame[columns].isna().any().any() or frame[cluster].isna().any():
        raise ValueError("Complete differences and cluster labels required")
    grouped = frame.groupby(cluster, sort=True)[columns].sum()
    sizes = frame.groupby(cluster, sort=True).size().to_numpy()
    means = frame[columns].mean().to_numpy()
    n = len(grouped)
    if n < 2:
        return {
            column: {
                "difference": float(means[i]),
                "query_count": len(frame),
                "cluster_count": n,
                "draws": 0,
                "finite_draws": 0,
                "lower": np.nan,
                "upper": np.nan,
            }
            for i, column in enumerate(columns)
        }
    rng = np.random.default_rng(seed)
    values = np.empty((draws, len(columns)))
    sums = grouped.to_numpy()
    for start in range(0, draws, 256):
        stop = min(start + 256, draws)
        picks = rng.integers(0, n, size=(stop - start, n))
        values[start:stop] = sums[picks].sum(axis=1) / sizes[picks].sum(axis=1)[:, None]
    bounds = np.quantile(values, [0.025, 0.975], axis=0)
    return {
        column: {
            "difference": float(means[i]),
            "query_count": len(frame),
            "cluster_count": n,
            "draws": draws,
            "finite_draws": int(np.isfinite(values[:, i]).sum()),
            "lower": float(bounds[0, i]),
            "upper": float(bounds[1, i]),
        }
        for i, column in enumerate(columns)
    }
