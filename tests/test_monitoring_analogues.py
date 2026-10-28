"""Availability, scale, donor and score checks for native-unit monitoring loss."""

import numpy as np
import pandas as pd
import pytest

from src.analogue_distributions import score_distribution
from src.monitoring_analogues import (
    eligible_donors,
    ensemble_metrics,
    information_states,
    last_observed_positions,
    native_members,
    prior_distances,
    q_signature,
    select_distinct,
)


def test_delay_and_stopped_feed_share_identical_instantaneous_information():
    assert sum(len(information_states(u)) for u in [0, 6, 12, 24]) == 26
    assert set(information_states(6)[0]) == {"delay_6", "outage"}
    assert information_states(24)[0] == ["delay_24", "outage"]


def test_hidden_readings_cannot_change_stale_features_and_zero_is_observed():
    x = np.arange(100, dtype=float)
    x[70] = 0
    first, _ = q_signature(x, 80, -10, last_observed_positions(x))
    changed = x.copy()
    changed[71:] = 999999
    second, _ = q_signature(changed, 80, -10, last_observed_positions(changed))
    np.testing.assert_array_equal(first, second)
    assert first[0] == 0 and first[-1] == 10


def test_natural_gap_ages_last_actual_reading_without_interpolation():
    x = np.arange(100, dtype=float)
    x[69:75] = np.nan
    f, s = q_signature(x, 80, -6, last_observed_positions(x))
    assert s == 68 and f[-1] == 12 and f[0] == 68
    x[62] = np.nan
    assert np.isnan(q_signature(x, 80, -6, last_observed_positions(x))[0]).any()


def test_prior_scaling_and_selection_ignore_verification_labels():
    p = np.array([[0, 1], [1, 3], [2, 5]], float)
    q = np.array([1, 4.0])
    d, s = prior_distances(p, q)
    np.testing.assert_allclose(prior_distances(p.copy(), q)[0], d)
    assert s > 0
    chosen = select_distinct(
        np.array([0, 1, 2]), np.array([1.0, 1.0, 2.0]), np.array(["a", "a", "b"])
    )
    assert chosen == [0, 2]


def test_cross_river_excludes_all_wurm_gauges_and_late_donors():
    t = pd.to_datetime(
        ["2020-01-01", "2020-01-05", "2020-01-05", "2020-01-05", "2020-01-05"], utc=True
    )
    m = pd.DataFrame(
        {
            "cutoff_utc": t,
            "end_utc": t,
            "storm_id": ["a", "q", "b", "c", "d"],
            "gauge": ["other", "q", "upstream", "late", "independent"],
            "physical_river": ["Geul", "Wurm", "Wurm", "Gulp", "Voer"],
        }
    )
    q = m.iloc[1]
    assert eligible_donors(m, q, 0, other_rivers=True).tolist() == [
        True,
        False,
        False,
        False,
        False,
    ]
    assert eligible_donors(m, q, 24, other_rivers=True).tolist() == [
        True,
        False,
        False,
        False,
        False,
    ]


def test_area_transfer_preserves_specific_discharge():
    y = np.ones((2, 24)) * 10
    np.testing.assert_allclose(
        native_members(y, np.array([0, 1]), np.array([100.0, 200.0]), 50.0),
        np.array([[5.0] * 24, [2.5] * 24]),
    )


@pytest.mark.parametrize("unit", ["us", "ns"])
def test_vector_chronology_matches_timestamp_arithmetic_for_parquet_units(unit):
    from src.eo_comparison import load_script

    runner = load_script("154_run_monitoring_analogues.py", "monitoring_chronology_" + unit)
    times = pd.to_datetime(["2020-01-01", "2020-01-03", "2020-01-05"], utc=True)
    meta = pd.DataFrame(
        {
            "cutoff_utc": times.as_unit(unit),
            "end_utc": times.as_unit(unit),
            "storm_id": ["a", "b", "c"],
            "gauge": ["x", "x", "x"],
            "physical_river": ["Geul", "Gulp", "Voer"],
        }
    )
    for u in [0, 6, 12, 24]:
        for pool in ["same_gauge", "other_rivers"]:
            found = runner.chronology(meta, u, pool)
            expected = np.stack(
                [
                    eligible_donors(meta, query, u, other_rivers=pool == "other_rivers")
                    for query in meta.itertuples()
                ]
            )
            np.testing.assert_array_equal(found, expected)
            assert found[2, 1]


def test_scores_match_existing_empirical_crps_and_keep_dry_nonresponses():
    y = np.arange(24, dtype=float)
    a = np.stack([y / 2, y * 2])
    w = np.array([0.3, 0.7])
    out = ensemble_metrics(y, a, w)
    assert out["crps"] == pytest.approx(score_distribution(y, a, w).crps.mean())
    dry = ensemble_metrics(np.zeros(24), np.zeros((5, 24)))
    assert dry["crps"] == 0 and dry["coverage80"] == 1 and np.isnan(dry["peak_time_error_h"])


def test_eo_join_normalizes_a_writable_copy_without_mutating_selected_sources(monkeypatch):
    from src.eo_comparison import load_script

    runner = load_script("154_run_monitoring_analogues.py", "monitoring_eo_join_test")
    source = pd.DataFrame(
        {
            "context_id": ["c"],
            "catchment_gauge": ["g"],
            "kind": ["recent"],
            "e0000": [3.0],
            "e0001": [4.0],
        }
    )
    original = source.copy(deep=True)
    monkeypatch.setattr(pd, "read_parquet", lambda *a, **kw: source)
    meta = pd.DataFrame({"recent_context_id": ["c", "absent"], "catchment_gauge": ["g", "g"]})
    x, valid, _ = runner.eo_features(meta, "example", "recent")
    np.testing.assert_allclose(x[0], [0.6, 0.8])
    assert valid.tolist() == [True, False] and np.isnan(x[1]).all()
    pd.testing.assert_frame_equal(source, original)
