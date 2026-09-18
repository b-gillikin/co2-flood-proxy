"""Tests for the distributed-lag conditional Poisson estimator (protocol §7-§8).

These protect what could silently change a reported number: the lag basis,
lag alignment, the conditional likelihood, bootstrap weighting and the
summary definitions. Agreement with R on full simulated datasets is checked
by `scripts/38_validate_estimator.py`.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.case_crossover import (
    MEDIAN_LAG_RANGE,
    block_bootstrap,
    cross_basis,
    fit_conditional_poisson,
    lag_basis,
    log_knots,
    median_association_lag,
    percentile_interval,
    primary_estimand,
    seasonal_design,
)


def test_knots_match_dlnm_logknots():
    assert log_knots() == pytest.approx([3.125967, 13.285912], abs=1e-6)


def test_lag_basis_spans_the_dlnm_basis():
    reference = pd.read_csv(ROOT / "tests/fixtures/dlnm_ns_lag_basis.csv")
    r_basis = reference[["b1", "b2", "b3", "b4"]].to_numpy()
    basis = lag_basis()
    coefficients, *_ = np.linalg.lstsq(basis, r_basis, rcond=None)
    assert np.abs(basis @ coefficients - r_basis).max() < 1e-10
    assert np.linalg.matrix_rank(basis) == 4


def test_lag_one_is_the_hour_before_the_outcome_hour():
    basis = lag_basis()
    values = np.zeros(200)
    values[100] = 1.0

    cross = cross_basis(values, basis)

    assert np.allclose(cross[100], 0.0)  # the outcome hour itself is never a lag
    assert np.allclose(cross[101], basis[0])
    assert np.allclose(cross[172], basis[71])
    assert np.allclose(cross[173], 0.0)


def test_cross_basis_is_missing_when_any_lag_is_missing():
    basis = lag_basis()
    values = np.ones(200)
    values[120] = np.nan

    cross = cross_basis(values, basis)

    assert np.isnan(cross[:72]).all()  # lags precede the series
    assert np.isfinite(cross[72:121]).all()
    assert np.isnan(cross[121:193]).all()
    assert np.isfinite(cross[193:]).all()


def conditional_loglik(beta, design, onset, strata):
    total = 0.0
    for stratum in np.unique(strata):
        mask = strata == stratum
        events = onset[mask].sum()
        if events:
            eta = design[mask] @ beta
            total += onset[mask] @ eta - events * np.log(np.exp(eta).sum())
    return total


def small_problem(seed=1):
    rng = np.random.default_rng(seed)
    n = 4000
    strata = rng.integers(0, 200, n)
    design = rng.normal(size=(n, 3))
    onset = rng.poisson(0.05 * np.exp(design @ np.array([0.5, -0.3, 0.2]))).astype(float)
    return design, onset, strata


def test_fit_maximises_the_conditional_likelihood():
    design, onset, strata = small_problem()

    fit = fit_conditional_poisson(design, onset, strata)

    best = conditional_loglik(fit["coef"], design, onset, strata)
    for step in np.eye(3) * 1e-4:
        assert best >= conditional_loglik(fit["coef"] + step, design, onset, strata)
        assert best >= conditional_loglik(fit["coef"] - step, design, onset, strata)
    assert fit["loglik"] == pytest.approx(best)


def test_strata_without_onsets_do_not_change_the_fit():
    design, onset, strata = small_problem()
    extra = np.random.default_rng(2).normal(size=(300, 3))

    base = fit_conditional_poisson(design, onset, strata)
    padded = fit_conditional_poisson(
        np.vstack([design, extra]), np.r_[onset, np.zeros(300)], np.r_[strata, np.full(300, 999)]
    )

    assert np.allclose(base["coef"], padded["coef"])


def test_bootstrap_weights_equal_duplicated_strata():
    from src.case_crossover import fit_problem, prepare_problem

    design, onset, strata = small_problem()
    problem = prepare_problem(design, onset, strata)
    weight = np.where(np.arange(problem["n_strata"]) % 3 == 0, 2.0, 1.0)

    weighted = fit_problem(problem, weight)
    codes = problem["codes"]
    repeat = weight[codes] == 2.0
    duplicated = fit_conditional_poisson(
        np.vstack([problem["design"], problem["design"][repeat]]),
        np.r_[problem["onset"], problem["onset"][repeat]],
        np.r_[codes, codes[repeat] + 10_000],
    )

    assert np.allclose(weighted["coef"], duplicated["coef"])


def test_bootstrap_rejects_a_stratum_spanning_two_blocks():
    design, onset, strata = small_problem()
    blocks = np.arange(len(strata)) % 2

    with pytest.raises(ValueError, match="more than one bootstrap block"):
        block_bootstrap(design, onset, strata, blocks, lambda fit: {}, replicates=1)


def test_median_association_lag_definition():
    curve = np.zeros(72)
    curve[[2, 9]] = 1.0  # half of the total is reached at lag 3
    assert median_association_lag(curve) == 3.0
    assert np.isnan(median_association_lag(-np.ones(72)))
    assert np.isnan(median_association_lag(np.zeros(72)))


def test_seasonal_design_uses_the_outcome_hour_season():
    cross = np.arange(8.0).reshape(2, 4)
    design = seasonal_design(cross, np.array([1, 0]))
    assert np.array_equal(design[0], np.r_[cross[0], np.zeros(4)])
    assert np.array_equal(design[1], np.r_[np.zeros(4), cross[1]])


def test_primary_estimand_is_warm_minus_cold():
    basis = lag_basis()
    warm, cold = np.array([0.1, 0.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0, 0.05])
    result = primary_estimand({"coef": np.r_[warm, cold]}, basis, contrast=2.0)
    assert result["cumulative_log_rr_warm"] == pytest.approx(2.0 * (basis @ warm).sum())
    assert result["cumulative_log_rr_difference"] == pytest.approx(
        2.0 * (basis @ (warm - cold)).sum()
    )


def test_undefined_median_lag_draws_widen_the_interval_to_the_range():
    few = pd.DataFrame({"median_lag_warm": np.r_[np.full(99, 10.0), np.nan]})
    many = pd.DataFrame({"median_lag_warm": np.r_[np.full(90, 10.0), [np.nan] * 10]})

    narrow = percentile_interval(few, ranges=MEDIAN_LAG_RANGE)
    wide = percentile_interval(many, ranges=MEDIAN_LAG_RANGE)

    assert narrow.loc["median_lag_warm", ["lower", "upper"]].tolist() == [10.0, 10.0]
    assert wide.loc["median_lag_warm", ["lower", "upper"]].tolist() == [1.0, 72.0]
    assert wide.loc["median_lag_warm", "estimable_share"] == 0.9


def test_percentile_interval_reports_estimable_share():
    draws = pd.DataFrame({"a": np.r_[np.arange(95.0), [np.nan] * 5]})
    interval = percentile_interval(draws)
    assert interval.loc["a", "estimable_share"] == 0.95
    assert interval.loc["a", "lower"] == pytest.approx(np.quantile(np.arange(95.0), 0.025))
