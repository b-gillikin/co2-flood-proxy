"""Diagnostic readouts and seasonal controls; no encoder updates or future fitting."""

from __future__ import annotations

import numpy as np
from scipy.linalg import eigh
from scipy.stats import rankdata


def transform_pair(train, test):
    """Train-only imputation, standardization and variable missing indicators.

    Raw model-specific embeddings enter here, not a universal L2 unit vector.
    The downstream transformation is fitted separately for each model/fold.
    """
    train, test = np.asarray(train, float), np.asarray(test, float)
    count = np.isfinite(train).sum(axis=0)
    mean = np.divide(
        np.where(np.isfinite(train), train, 0).sum(axis=0),
        count,
        out=np.zeros(train.shape[1]),
        where=count > 0,
    )
    filled = np.where(np.isfinite(train), train, mean)
    sd = filled.std(axis=0)
    keep = (count > 0) & (sd > 1e-10)
    a = (filled[:, keep] - mean[keep]) / sd[keep]
    b = (np.where(np.isfinite(test), test, mean)[:, keep] - mean[keep]) / sd[keep]
    missing = (~np.isfinite(train)).astype(float)
    variable = missing.std(axis=0) > 1e-10
    if variable.any():
        mu, sigma = missing[:, variable].mean(axis=0), missing[:, variable].std(axis=0)
        a = np.column_stack([a, (missing[:, variable] - mu) / sigma])
        b = np.column_stack([b, ((~np.isfinite(test[:, variable])).astype(float) - mu) / sigma])
    scale = np.sqrt(max(a.shape[1], 1))
    return a / scale, b / scale


def kernels(ground, eo, train, test):
    a, b = transform_pair(ground[train], ground[test])
    e, f = transform_pair(eo[train], eo[test])
    return a @ a.T, b @ a.T, e @ e.T, f @ e.T


def kernel_predictions(parts, y, weights, alphas):
    """Separate multi-output ridge fits; alpha multiplies mean-loss objective."""
    kg, tg, ke, te = parts
    mean = y.mean(axis=0)
    centered = y - mean
    out = {}
    for weight in weights:
        vals, vecs = eigh(kg + weight * ke, check_finite=False)
        vals = np.maximum(vals, 0)
        projected = vecs.T @ centered
        cross = (tg + weight * te) @ vecs
        for alpha in alphas:
            pred = cross @ (projected / (vals[:, None] + len(y) * alpha)) + mean
            out[(float(weight), float(alpha))] = np.maximum(pred, 0)
    return out


def seasonal_sources(train, test, quarter, *, seed):
    """Whole-vector permutations within training quarters; test draws from train.

    No source from the held-out test year is used. Training permutations are a
    negative control, not purported physical observation histories.
    """
    rng = np.random.default_rng(seed)
    permuted = np.asarray(train).copy()
    for value in np.unique(quarter[train]):
        where = np.flatnonzero(quarter[train] == value)
        permuted[where] = rng.permutation(permuted[where])
    sources, relaxed = [], []
    for i in test:
        candidates = train[quarter[train] == quarter[i]]
        relax = len(candidates) == 0
        if relax:
            difference = np.abs(quarter[train] - quarter[i])
            candidates = train[
                np.minimum(difference, 4 - difference)
                == np.minimum(difference, 4 - difference).min()
            ]
        sources.append(int(rng.choice(candidates)))
        relaxed.append(relax)
    return permuted, np.asarray(sources), np.asarray(relaxed)


def shuffled_kernels(ground, eo, train, test, quarter, *, seed):
    permuted, sources, relaxed = seasonal_sources(train, test, quarter, seed=seed)
    # Permutation preserves train mean/SD; ground data and Y stay in place.
    a, b = transform_pair(ground[train], ground[test])
    e, f = transform_pair(eo[permuted], eo[sources])
    return (a @ a.T, b @ a.T, e @ e.T, f @ e.T), sources, relaxed, permuted


def choose_parameters(ground, eo, y, validation, weights, alphas, quarter, *, seed=None):
    """Select on strictly earlier validation years, never on outer test labels."""
    totals = {(float(w), float(a)): [0.0, 0] for w in weights for a in alphas}
    for fold, (train, test) in enumerate(validation):
        if seed is None:
            parts = kernels(ground, eo, train, test)
        else:
            parts = shuffled_kernels(ground, eo, train, test, quarter, seed=seed + fold * 1009)[0]
        for parameter, pred in kernel_predictions(parts, y[train], weights, alphas).items():
            totals[parameter][0] += float(np.abs(pred - y[test]).sum())
            totals[parameter][1] += y[test].size
    available = [(error / count, w, a) for (w, a), (error, count) in totals.items() if count]
    if not available:
        return (0.0, 1.0), 0
    # Ties favor less EO influence and stronger shrinkage.
    _, w, a = min(available, key=lambda item: (item[0], item[1], -item[2]))
    return (w, a), sum(len(test) for _, test in validation)


def chronology(times, ends, boundary):
    """Closed label/input episodes before a fixed year boundary, in explicit ns."""
    import pandas as pd

    hour = pd.Timedelta(hours=1).value
    t = np.array([pd.Timestamp(x).value for x in times])
    end = np.array([pd.Timestamp(x).value for x in ends])
    limit = pd.Timestamp(boundary).value
    return (t + 24 * hour <= limit) & (end + 12 * hour <= limit)


def validation_splits(times, ends, years, train, *, maximum=2):
    """Latest two feasible prior-year folds; all their eligible cases retained."""
    import pandas as pd

    result = []
    for year in sorted(np.unique(years[train]), reverse=True):
        before = chronology(times, ends, pd.Timestamp(f"{year}-01-01", tz="UTC"))
        inner, held = train[before[train]], train[years[train] == year]
        if len(inner) >= 2 and len(held):
            result.append((inner, held))
        if len(result) == maximum:
            break
    return result


def partial_rank_correlation(distance, target, controls):
    """Descriptive pair association only; pairs are not independent samples."""
    valid = np.isfinite(distance) & np.isfinite(target) & np.isfinite(controls).all(axis=1)
    if valid.sum() < controls.shape[1] + 3:
        return np.nan, int(valid.sum())
    x, y = rankdata(distance[valid]), rankdata(target[valid])
    c = np.column_stack([np.ones(valid.sum()), np.apply_along_axis(rankdata, 0, controls[valid])])
    x -= c @ np.linalg.lstsq(c, x, rcond=None)[0]
    y -= c @ np.linalg.lstsq(c, y, rcond=None)[0]
    if x.std() < 1e-10 or y.std() < 1e-10:
        return np.nan, int(valid.sum())
    return float(np.corrcoef(x, y)[0, 1]), int(valid.sum())


def readout_fold(
    ground,
    eo,
    y,
    full_train,
    train,
    test,
    validation_full,
    validation_matched,
    quarter,
    config,
    *,
    seed,
):
    """One lawful outer fold; no outer-test outcomes consulted during fitting."""
    predictions = np.full((3 + config["permutations"], len(test), y.shape[-1]), np.nan)
    records = []
    sources = np.full((config["permutations"], len(test)), -1, int)
    alphas, weights = config["alphas"], config["eo_weights"]
    empty_eo = np.zeros((len(ground), 1))
    if len(full_train) >= 2:
        parameter, nval = choose_parameters(
            ground, empty_eo, y, validation_full, [0.0], alphas, quarter
        )
        parts = kernels(ground, empty_eo, full_train, test)
        predictions[0] = kernel_predictions(parts, y[full_train], [0.0], [parameter[1]])[parameter]
        records.append(
            dict(
                arm="ground_full",
                weight=0.0,
                alpha=parameter[1],
                training_cases=len(full_train),
                validation_cases=nval,
            )
        )
    if len(train) < 2:
        return predictions, records, sources
    # Unsupported query vectors use broader predictions outside this function.
    supported = np.isfinite(eo[test]).all(axis=1)
    held = test[supported]
    if not len(held):
        return predictions, records, sources
    parts = kernels(ground, eo, train, held)
    for arm, grid in [(1, [0.0]), (2, weights)]:
        parameter, nval = choose_parameters(
            ground, eo, y, validation_matched, grid, alphas, quarter
        )
        predictions[arm, supported] = kernel_predictions(
            parts, y[train], [parameter[0]], [parameter[1]]
        )[parameter]
        records.append(
            dict(
                arm="ground_matched" if arm == 1 else "ground_real",
                weight=parameter[0],
                alpha=parameter[1],
                training_cases=len(train),
                validation_cases=nval,
            )
        )
    for replication in range(config["permutations"]):
        key = seed + replication * 100003
        parameter, nval = choose_parameters(
            ground, eo, y, validation_matched, weights, alphas, quarter, seed=key
        )
        part, source, relaxed, perm = shuffled_kernels(
            ground, eo, train, held, quarter, seed=key + 65537
        )
        predictions[3 + replication, supported] = kernel_predictions(
            part, y[train], [parameter[0]], [parameter[1]]
        )[parameter]
        sources[replication, supported] = source
        records.append(
            dict(
                arm="ground_shuffle",
                replication=replication,
                weight=parameter[0],
                alpha=parameter[1],
                training_cases=len(train),
                validation_cases=nval,
                unchanged_train_fraction=float(np.all(eo[perm] == eo[train], axis=1).mean()),
                relaxed_test_quarter_fraction=float(relaxed.mean()),
            )
        )
    return predictions, records, sources
