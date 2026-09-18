"""Distributed-lag conditional Poisson estimation for the case-crossover design.

Implements protocol draft 0.9 §7-§8 in Python:

- a natural cubic spline lag basis over lags 1-72 with 4 degrees of freedom and
  knots equally spaced on the log scale, built by the same algorithm as R's
  `splines::ns` with the knots of `dlnm::logknots`;
- linear-exposure cross-bases in which lag 1 is the hour before the outcome hour;
- a conditional Poisson fit (the likelihood conditional on each stratum's onset
  count), with optional stratum weights for the block bootstrap;
- the primary summaries: cumulative association at a fixed contrast and the
  median association lag.

Protocol §7 permits this implementation only after it reproduces the R
reference (`dlnm` cross-basis and predictions, with coefficients from a
stratum fixed-effects Poisson GLM) on synthetic data; see
`scripts/38_validate_estimator.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.interpolate import BSpline

MAX_LAG = 72
LAG_DF = 4


def log_knots(max_lag=MAX_LAG, df=LAG_DF):
    """Interior knots of `dlnm::logknots(c(1, max_lag), fun="ns", df=df)`."""
    lower, upper = 1.0, float(max_lag)
    n_knots = df - 2
    if n_knots < 1:
        raise ValueError("A natural spline lag basis needs df >= 3")
    step = (1 + np.log(upper - lower)) / (n_knots + 1)
    return lower + np.exp(step * np.arange(1, n_knots + 1) - 1)


def natural_spline_basis(x, knots, boundary):
    """Natural cubic spline basis with intercept, following R's `splines::ns`."""
    x = np.asarray(x, dtype=float)
    augmented = np.r_[[boundary[0]] * 4, np.asarray(knots, dtype=float), [boundary[1]] * 4]
    n = len(augmented) - 4
    spline = BSpline(augmented, np.eye(n), 3, extrapolate=True)
    basis = spline(x)
    constraint = np.vstack([spline(boundary[0], nu=2), spline(boundary[1], nu=2)])
    q, _ = np.linalg.qr(constraint.T, mode="complete")
    return basis @ q[:, 2:]


def lag_basis(max_lag=MAX_LAG, df=LAG_DF):
    """Lag basis evaluated at lags 1..max_lag; row k is lag k + 1."""
    lags = np.arange(1, max_lag + 1)
    return natural_spline_basis(lags, log_knots(max_lag, df), (1.0, float(max_lag)))


def cross_basis(values, basis):
    """Linear-exposure cross-basis: row t sums x[t - l] * basis[l - 1] over lags l.

    The input must be one watercourse's complete hourly series. A row is
    missing when any lagged value is missing or precedes the series.
    """
    values = np.asarray(values, dtype=float)
    n_lags, n_columns = basis.shape
    missing = np.isnan(values).astype(float)
    filled = np.nan_to_num(values)
    shifted_missing = np.convolve(missing, np.r_[0.0, np.ones(n_lags)])[: len(values)]
    out = np.empty((len(values), n_columns))
    for column in range(n_columns):
        out[:, column] = np.convolve(filled, np.r_[0.0, basis[:, column]])[: len(values)]
    invalid = (shifted_missing > 0) | (np.arange(len(values)) < n_lags)
    out[invalid] = np.nan
    return out


def _group_max(values, codes, n_groups):
    top = np.full(n_groups, -np.inf)
    np.maximum.at(top, codes, values)
    return top


def _probabilities(eta, codes, n_groups, operator):
    """Within-stratum multinomial probabilities, computed stably."""
    exp_eta = np.exp(eta - _group_max(eta, codes, n_groups)[codes])
    return exp_eta / (operator @ exp_eta)[codes]


def prepare_problem(design, onset, strata, blocks=None):
    """Drop incomplete rows and uninformative strata once; index the rest by integer.

    Strata without an onset carry no information in the conditional
    likelihood. Blocks are indexed over every complete row, so a bootstrap
    still resamples calendar blocks that contain no onset.
    """
    design = np.asarray(design, dtype=float)
    onset = np.asarray(onset, dtype=float)
    complete = np.isfinite(design).all(axis=1)
    stratum_codes, _ = pd.factorize(np.asarray(strata)[complete])
    events_all = np.bincount(stratum_codes, weights=onset[complete])
    informative = events_all[stratum_codes] > 0
    codes, _ = pd.factorize(stratum_codes[informative])
    n_strata = int(codes.max()) + 1 if len(codes) else 0
    operator = sparse.csr_matrix(
        (np.ones(len(codes)), (codes, np.arange(len(codes)))), shape=(n_strata, len(codes))
    )
    problem = {
        "design": design[complete][informative],
        "onset": onset[complete][informative],
        "codes": codes,
        "n_strata": n_strata,
        "operator": operator,
    }
    problem["events"] = operator @ problem["onset"]
    if blocks is not None:
        block_codes, block_labels = pd.factorize(np.asarray(blocks)[complete])
        stratum_block = np.zeros(n_strata, dtype=int)
        stratum_block[codes] = block_codes[informative]
        problem["stratum_block"] = stratum_block
        problem["n_blocks"] = len(block_labels)
    return problem


def fit_problem(problem, weight=None, tol=1e-10, max_iter=100):
    """Newton-Raphson maximisation of the (weighted) conditional Poisson likelihood."""
    design, onset, codes = problem["design"], problem["onset"], problem["codes"]
    n_strata, operator, events = problem["n_strata"], problem["operator"], problem["events"]
    weight = np.ones(n_strata) if weight is None else np.asarray(weight, dtype=float)
    weighted_events = weight * events
    row_weight = weight[codes]
    beta = np.zeros(design.shape[1])

    def loglik(coefficients):
        eta = design @ coefficients
        top = _group_max(eta, codes, n_strata)
        log_sum = np.log(operator @ np.exp(eta - top[codes])) + top
        return float(np.sum(row_weight * onset * eta) - np.sum(weighted_events * log_sum))

    def information(probability):
        mean_x = operator @ (probability[:, None] * design)
        scaled = design * np.sqrt(probability * weighted_events[codes])[:, None]
        return mean_x, scaled.T @ scaled - (mean_x * weighted_events[:, None]).T @ mean_x

    current = loglik(beta)
    for _ in range(max_iter):
        probability = _probabilities(design @ beta, codes, n_strata, operator)
        mean_x, hessian = information(probability)
        gradient = design.T @ (row_weight * onset) - weighted_events @ mean_x
        step = np.linalg.solve(hessian, gradient)
        size = 1.0
        while True:
            candidate = beta + size * step
            value = loglik(candidate)
            if value >= current - 1e-12 or size < 1e-8:
                break
            size /= 2
        beta, previous, current = candidate, current, value
        if np.max(np.abs(size * step)) < tol or abs(current - previous) < tol * 1e-3:
            break
    else:
        raise RuntimeError("Conditional Poisson fit did not converge")

    probability = _probabilities(design @ beta, codes, n_strata, operator)
    _, info = information(probability)
    fitted = events[codes] * probability
    residual_df = len(onset) - n_strata - design.shape[1]
    with np.errstate(divide="ignore", invalid="ignore"):
        pearson = np.where(fitted > 0, (onset - fitted) ** 2 / fitted, 0.0)
    return {
        "coef": beta,
        "vcov": np.linalg.inv(info),
        "dispersion": float(pearson.sum() / residual_df) if residual_df > 0 else np.nan,
        "loglik": current,
        "n_strata": n_strata,
        "n_rows": len(onset),
        "n_onsets": int(onset.sum()),
    }


def fit_conditional_poisson(design, onset, strata, **kwargs):
    """Fit the conditional Poisson model: coefficients, covariance and dispersion.

    Returns the model-based covariance and the quasi-Poisson dispersion for
    reference; protocol intervals come from the block bootstrap.
    """
    return fit_problem(prepare_problem(design, onset, strata), **kwargs)


def lag_curve(coefficients, basis):
    """Log rate ratio per unit exposure at each lag."""
    return basis @ np.asarray(coefficients)


def cumulative_log_rr(coefficients, basis, contrast):
    """Log rate ratio accumulated over all lags for `contrast` exposure units."""
    return float(contrast * lag_curve(coefficients, basis).sum())


def median_association_lag(curve):
    """Smallest lag whose cumulative log RR reaches half of the total (protocol §1).

    Returns NaN when the total is not positive.
    """
    cumulative = np.cumsum(curve)
    total = cumulative[-1]
    if not np.isfinite(total) or total <= 0:
        return np.nan
    return float(np.argmax(cumulative >= total / 2) + 1)


def seasonal_design(cross, warm):
    """Rainfall cross-basis split by the outcome hour's season: [warm, cold] blocks."""
    warm = np.asarray(warm, dtype=float)[:, None]
    return np.hstack([cross * warm, cross * (1 - warm)])


def primary_estimand(fit, basis, contrast):
    """Warm, cold and warm-minus-cold summaries from a seasonal fit."""
    n = basis.shape[1]
    warm, cold = fit["coef"][:n], fit["coef"][n:]
    curve_warm, curve_cold = lag_curve(warm, basis), lag_curve(cold, basis)
    result = {
        "cumulative_log_rr_warm": contrast * curve_warm.sum(),
        "cumulative_log_rr_cold": contrast * curve_cold.sum(),
        "median_lag_warm": median_association_lag(curve_warm),
        "median_lag_cold": median_association_lag(curve_cold),
    }
    result["cumulative_log_rr_difference"] = (
        result["cumulative_log_rr_warm"] - result["cumulative_log_rr_cold"]
    )
    result["median_lag_difference"] = result["median_lag_warm"] - result["median_lag_cold"]
    return result


def block_bootstrap(design, onset, strata, blocks, statistic, replicates=999, seed=0):
    """Resample calendar year-month blocks jointly across watercourses (protocol §8).

    `blocks` gives each row's block label; every stratum must sit inside one
    block. Each replicate reweights strata by how often their block was drawn,
    which is equivalent to stacking the resampled blocks as distinct strata.
    Pass every at-risk row, so blocks without onsets are resampled too.
    """
    frame = pd.DataFrame({"stratum": np.asarray(strata), "block": np.asarray(blocks)})
    if frame.groupby("stratum").block.nunique().gt(1).any():
        raise ValueError("A stratum spans more than one bootstrap block")
    problem = prepare_problem(design, onset, strata, blocks)
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(replicates):
        draw = rng.integers(0, problem["n_blocks"], problem["n_blocks"])
        counts = np.bincount(draw, minlength=problem["n_blocks"])
        weight = counts[problem["stratum_block"]].astype(float)
        draws.append(statistic(fit_problem(problem, weight)))
    return pd.DataFrame(draws)


MEDIAN_LAG_RANGE = {
    "median_lag_warm": (1.0, 72.0),
    "median_lag_cold": (1.0, 72.0),
    "median_lag_difference": (-71.0, 71.0),
}


def percentile_interval(draws, level=0.95, ranges=None):
    """Percentile intervals and the share of estimable draws for each statistic.

    For a statistic with an admissible range (`ranges`, e.g. the median lags),
    an undefined draw counts as possibly any value in that range: it enters the
    lower quantile at the range minimum and the upper quantile at the range
    maximum (decision D7). An endpoint therefore reaches the range bound once
    more than the tail share of draws is undefined, meaning the data do not
    bound that side. Without a range, undefined draws are dropped.
    """
    tail = (1 - level) / 2
    ranges = ranges or {}
    rows = {}
    for column in draws:
        values = draws[column]
        defined = values.dropna()
        if column in ranges and len(values):
            low, high = ranges[column]
            lower = values.fillna(low).quantile(tail)
            upper = values.fillna(high).quantile(1 - tail)
        else:
            lower = defined.quantile(tail) if len(defined) else np.nan
            upper = defined.quantile(1 - tail) if len(defined) else np.nan
        rows[column] = {
            "lower": lower,
            "upper": upper,
            "estimable_share": len(defined) / len(values) if len(values) else np.nan,
        }
    return pd.DataFrame(rows).T
