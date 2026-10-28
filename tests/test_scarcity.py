"""Counterexamples for scarcity masks, source timing, matching and CRPS."""

import json
from pathlib import Path

import numpy as np
import pytest

from src.monitoring_analogues import ensemble_metrics
from src.scarcity import (
    batch_scores,
    combine_ground,
    coordinate_moments,
    forward_hold,
    mask_series,
    measured_donor_support,
    partial_history_distances,
    rain_histories,
    scenario_groups,
    scenario_keep,
    stable_members,
)


def test_masks_are_nested_coherent_reproducible_and_not_independent_events():
    for length in [None, 6, 12, 24]:
        x = mask_series(5000, 8, 2, [0.25, 0.5, 0.75], seed=72, mean_run=length)
        assert np.all(x[:-1] <= x[1:])
        np.testing.assert_array_equal(
            x, mask_series(5000, 8, 2, [0.25, 0.5, 0.75], seed=72, mean_run=length)
        )
        np.testing.assert_allclose(x.mean(axis=(1, 2, 3)), [0.25, 0.5, 0.75], atol=0.025)
    with pytest.raises(ValueError):
        mask_series(100, 2, 1, [0.75], seed=1, mean_run=1)


def test_clustered_mask_has_the_declared_run_duration():
    x = mask_series(30000, 2, 1, [0.5], seed=17, mean_run=12)[0].ravel()
    padded = np.r_[False, x, False].astype(int)
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    assert np.mean(ends - starts) == pytest.approx(12, rel=0.1)


def test_holding_is_causal_and_retains_zero_without_backfilling():
    x = np.array([np.nan, 3, np.nan, 0, np.nan, 9.0])
    np.testing.assert_allclose(forward_hold(x), [np.nan, 3, 3, 0, 0, 9], equal_nan=True)


def test_hidden_query_values_cannot_change_either_missing_data_treatment():
    rng = np.random.default_rng(1)
    q = rng.random((10, 72))
    donor = rng.random((5, 10, 72))
    keep = rng.random((4, 10, 72)) > 0.5
    for held in [False, True]:
        expected, _ = partial_history_distances(
            q, donor, np.zeros((10, 72)), np.ones((10, 72)), keep, held=held
        )
        # Poison each replication's own hidden entries independently.
        for r in range(4):
            changed = q.copy()
            changed[~keep[r]] = 1e9
            actual, _ = partial_history_distances(
                changed, donor, np.zeros((10, 72)), np.ones((10, 72)), keep[r : r + 1], held=held
            )
            np.testing.assert_allclose(actual[0], expected[r], atol=1e-12)


def test_density_really_changes_matching_despite_identical_three_point_signature():
    q = np.zeros((10, 72))
    q[0, -2] = 10
    donor = np.zeros((2, 10, 72))
    donor[1] = q
    keep = np.ones((1, 10, 72), bool)
    dense, support = partial_history_distances(
        q, donor, np.zeros((10, 72)), np.ones((10, 72)), keep
    )
    sparse = keep.copy()
    sparse[:, 0] = np.arange(71, -1, -1) % 3 == 0
    thin, _ = partial_history_distances(q, donor, np.zeros((10, 72)), np.ones((10, 72)), sparse)
    assert (
        stable_members(combine_ground(dense, support, np.zeros((1, 2)), 0), np.ones(2, bool))[0, 0]
        == 1
    )
    assert thin[0, :, 0].tolist() == [0.0, 0.0]
    assert stable_members(thin[:, :, 0], np.ones(2, bool))[0, 0] == 0


def test_rain_coarsening_cannot_read_an_endpoint_after_issue():
    x = np.arange(500, dtype=float)[:, None]
    before, age = rain_histories(x, np.arange(500), np.array([250]), 24, 0)
    changed = x.copy()
    changed[251:] = 1e9
    after, _ = rain_histories(changed, np.arange(500), np.array([250]), 24, 0)
    np.testing.assert_array_equal(before, after)
    assert age[0] == 10
    base, _ = rain_histories(x, np.arange(500), np.array([250]), 1, 0)
    assert before[0, 0, 0] != base[0, 0, 0]


def test_prior_calibration_does_not_read_query_or_future_rows():
    x = np.arange(16, dtype=float).reshape(4, 2, 2)
    prior = np.tri(4, 4, k=-1, dtype=bool)
    m, v = coordinate_moments(prior, x)
    poisoned = x.copy()
    poisoned[2:] = 1e9
    mm, vv = coordinate_moments(prior, poisoned)
    np.testing.assert_array_equal(m[2], mm[2])
    np.testing.assert_array_equal(v[2], vv[2])
    assert m[0].sum() == 0 and v[0].sum() == 0


def test_top_members_exactly_match_full_stable_sort_including_boundary_ties():
    d = np.random.default_rng(8).integers(0, 4, (30, 100)).astype(float)
    allowed = np.arange(100) % 3 != 0
    actual = stable_members(d, allowed)
    expected = np.argsort(np.where(allowed, d, np.inf), axis=1, kind="stable")[:, :10]
    np.testing.assert_array_equal(actual, expected)
    assert (stable_members(d, np.zeros(100, bool)) == -1).all()


def test_batched_scores_match_validated_scalar_helper_for_variable_member_counts():
    rng = np.random.default_rng(12)
    outcome = rng.random((15, 24))
    y = rng.random(24)
    ids = np.full((4, 10), -1)
    for r, n in enumerate([0, 1, 5, 10]):
        ids[r, :n] = np.arange(n)
    scores, counts = batch_scores(y, outcome, ids)
    assert counts.tolist() == [0, 1, 5, 10] and np.isnan(scores[0]).all()
    for r, n in enumerate([1, 5, 10], 1):
        expected = ensemble_metrics(y, outcome[:n])
        np.testing.assert_allclose(scores[r], list(expected.values()), atol=1e-12, equal_nan=True)


def test_network_inventory_is_the_complete_census_at_declared_sizes():
    cfg = json.loads((Path(__file__).parents[1] / "config/limburg_scarcity_v1.json").read_text())
    groups = scenario_groups(cfg)
    subsets = [tuple(range(8))] + [
        tuple(s) for g in groups if g["family"] == "network" for s in g["subsets"]
    ]
    assert len(subsets) == 128 and len(set(subsets)) == 128
    assert {len(s) for s in subsets} == {0, 2, 4, 6, 8}
    spec = next(g for g in groups if g["name"] == "network_4")
    keep = scenario_keep(spec, np.arange(72), np.arange(72), None, 0)
    assert (keep[:, :8].sum(axis=(1, 2)) == 4 * 72).all()
    assert keep[:, 8:].all()


def test_all_discharge_absent_is_not_removal_of_verification_or_rain():
    spec = dict(family="all_absent", replicas=1)
    keep = scenario_keep(spec, np.arange(72), np.arange(72), None, 0)
    qdist, support = partial_history_distances(
        np.ones((10, 72)), np.ones((3, 10, 72)), np.zeros((10, 72)), np.ones((10, 72)), keep
    )
    rain = np.array([[0.1, 0.3, 0.2]])
    np.testing.assert_array_equal(combine_ground(qdist, support, rain, 0), rain)


def test_combined_profiles_degrade_all_retained_feeds_and_share_the_network_view():
    cfg = json.loads((Path(__file__).parents[1] / "config/limburg_scarcity_v1.json").read_text())
    groups = scenario_groups(cfg)
    schedule = next(g for g in groups if g["name"] == "network4_schedule6_no_maas")
    epochs = np.arange(72)
    keep = scenario_keep(schedule, epochs, epochs, None, 0)
    assert keep.shape == (420, 10, 72)
    assert not keep[:, 8:].any()
    assert (keep[:, :8].any(axis=-1).sum(axis=1) == 4).all()
    assert (keep.sum(axis=(1, 2)) == 48).all()
    np.testing.assert_array_equal(keep, scenario_keep(schedule, epochs, epochs, None, 7))
    missing = next(g for g in groups if g["name"] == "network4_block12_50pct_no_maas")
    hidden = mask_series(72, 100, 8, [0.5], seed=4, mean_run=12)[0]
    packed = np.packbits(hidden, axis=-1)
    keep = scenario_keep(missing, epochs, epochs, packed, 0)
    for r, subset in enumerate(missing["subsets"]):
        for channel in subset:
            np.testing.assert_array_equal(keep[r, channel], ~hidden[r, channel])
    np.testing.assert_array_equal(keep, scenario_keep(missing, epochs, epochs, packed, 7))


def test_measured_support_rejects_mean_filled_donors_and_ignores_hidden_query_values():
    query = np.ones((10, 72))
    donors = np.ones((3, 10, 72))
    donors[1, 0, :30] = np.nan
    donors[2, 9] = np.nan
    keep = np.ones((2, 10, 72), bool)
    keep[1, 9] = False
    rain = np.ones((2, 7))
    result = measured_donor_support(query, donors, keep, rain, np.ones((3, 7)))
    assert result.tolist() == [[True, False, False], [True, False, True]]
    poisoned = query.copy()
    poisoned[9] = 1e12
    np.testing.assert_array_equal(
        result[1], measured_donor_support(poisoned, donors, keep[1:], rain[1:], np.ones((3, 7)))[0]
    )
    ranked = stable_members(np.zeros((2, 3)), result)
    assert ranked[0].tolist() == [0, -1, -1]
    assert ranked[1].tolist() == [0, 2, -1]
