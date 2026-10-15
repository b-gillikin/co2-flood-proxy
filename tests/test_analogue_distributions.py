"""Hand-derived finite-distribution scores and information-boundary checks."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analogue_distributions import (
    cluster_intervals,
    distribution_parameters,
    eligible_archive,
    group_weights,
    score_distribution,
)


def direct_crps(y, x, w):
    w = np.asarray(w) / np.sum(w)
    return w @ np.abs(x - y) - 0.5 * np.einsum(
        "i,j,ijh->h", w, w, np.abs(x[:, None, :] - x[None, :, :])
    )


def test_hand_calculated_score_and_inverse_cdf_quantiles():
    x = np.array([[0.0, 2.0], [2.0, 0.0]])
    scores = score_distribution([1, 1], x, [0.25, 0.75])
    np.testing.assert_allclose(scores.crps, 0.625)
    np.testing.assert_array_equal(scores["median"], [2, 0])
    np.testing.assert_array_equal(scores.lower50, [0, 0])
    np.testing.assert_array_equal(scores.upper50, [2, 0])
    np.testing.assert_array_equal(scores.coverage50, [True, False])


def test_sorted_crps_matches_direct_weighted_pairs_and_is_permutation_invariant():
    rng = np.random.default_rng(31)
    x, y, w = rng.normal(size=(17, 24)), rng.normal(size=24), rng.uniform(size=17)
    actual = score_distribution(y, x, w)
    np.testing.assert_allclose(actual.crps, direct_crps(y, x, w), atol=1e-14)
    order = rng.permutation(len(x))
    pd.testing.assert_frame_equal(actual, score_distribution(y, x[order], w[order]), atol=1e-14)


def test_degenerate_distribution_ties_and_linear_units():
    x = np.array([[2.0, 3.0, 4.0]])
    y = np.array([1.0, 3.0, 5.0])
    scores = score_distribution(y, x, [1])
    np.testing.assert_allclose(scores.crps, [1, 0, 1])
    np.testing.assert_array_equal(scores.coverage80, [False, True, False])
    scaled = score_distribution(y * 7, x * 7, [1])
    for field in ["crps", "width50", "width80", "median_absolute_error"]:
        np.testing.assert_allclose(scaled[field], scores[field] * 7)
    np.testing.assert_allclose(scaled.mean_squared_error, scores.mean_squared_error * 49)
    np.testing.assert_array_equal(scaled.coverage80, scores.coverage80)


def test_group_weighting_invariant_to_repeating_identical_group_distribution():
    x = np.array([[1.0, 2], [3, 4], [5, 6]])
    groups = ["a", "a", "b"]
    w = group_weights(groups)
    np.testing.assert_allclose(w, [0.25, 0.25, 0.5])
    repeated = np.vstack([x[:2], x[:2], x[2:]])
    y = np.array([2.0, 3])
    a = score_distribution(y, x, w)
    b = score_distribution(y, repeated, group_weights(["a"] * 4 + ["b"]))
    pd.testing.assert_frame_equal(a, b, atol=1e-14)


def test_response_perturbation_cannot_change_distribution_or_archive_selection():
    pool = pd.DataFrame(
        {
            "event_id": ["a", "b", "c", "d"],
            "storm_id": ["one", "two", "three", "four"],
            "onset_utc": pd.to_datetime(
                ["2020-01-01", "2020-01-07", "2020-01-08", "2020-01-10"], utc=True
            ),
            "physical_river_group": ["A", "B", "C", "A"],
            "outcome": [1, 2, 3, 4],
        }
    )
    query = pool.iloc[3]
    before = eligible_archive(pool, query, True)
    pool.loc[3, "outcome"] = -100
    after = eligible_archive(pool, pool.iloc[3], True)
    assert before.event_id.tolist() == after.event_id.tolist() == ["b"]
    x, w = np.array([[1.0, 2.0], [4.0, 5.0]]), np.array([0.5, 0.5])
    a, b = distribution_parameters(x, w), distribution_parameters(x, w)
    assert not np.allclose(
        score_distribution([1, 2], x, w).crps, score_distribution([10, 20], x, w).crps
    )
    for field in a:
        np.testing.assert_array_equal(a[field], b[field])


def test_cluster_bootstrap_preserves_joint_endpoints_and_event_weighting():
    a = np.array([[0.0, 0], [0, 0], [3, 6]])
    samples = cluster_intervals(a, ["one", "one", "two"], draws=500, seed=7)
    np.testing.assert_allclose(samples[:, 1], samples[:, 0] * 2)
    assert set(samples[:, 0]) == {0, 1, 3}
    np.testing.assert_array_equal(samples, cluster_intervals(a, ["one", "one", "two"], 500, 7))
    assert cluster_intervals(a, ["one"] * 3, draws=5) is None


@pytest.mark.parametrize("weights", [[0, 0], [-1, 2], [float("nan"), 1], [1]])
def test_invalid_weights_rejected(weights):
    with pytest.raises(ValueError):
        score_distribution([1], np.array([[1.0], [2.0]]), weights)


def test_zero_weight_and_tied_members_have_no_spurious_mass():
    x = np.array([[-99.0], [1.0], [1.0], [3.0]])
    scores = score_distribution([2], x, [0, 0.25, 0.25, 0.5])
    np.testing.assert_allclose(scores.crps, [0.5])
    assert scores["median"].iloc[0] == 1
    assert scores.lower80.iloc[0] == 1


def test_lead_indices_are_one_based_and_quantile_interval_tails_partition_cases():
    x = np.tile(np.arange(1, 25), (5, 1))
    y = x[0].astype(float)
    y[[0, 1]] += [-1, 1]
    scores = score_distribution(y, x, np.ones(5))
    assert scores.loc[scores.lead_hour.isin([6, 12, 24]), "observed"].tolist() == [6, 12, 24]
    np.testing.assert_array_equal(
        scores.coverage80.astype(int) + scores.below80 + scores.above80, 1
    )


def test_independent_cdf_audit_accepts_read_only_weights_without_mutating_them():
    path = Path(__file__).parents[1] / "scripts/91_audit_analogue_distributions.py"
    spec = importlib.util.spec_from_file_location("distribution_audit", path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    x = np.array([[0.0, 2.0], [2.0, 0.0]])
    w = np.array([0.25, 0.75])
    w.flags.writeable = False
    actual = audit.cdf_scores([1, 1], x, w)
    np.testing.assert_allclose(actual["crps"], [0.625, 0.625])
    np.testing.assert_array_equal(w, [0.25, 0.75])
