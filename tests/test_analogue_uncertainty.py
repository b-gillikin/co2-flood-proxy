"""Protect pairing, dependence and review-selection claims in Step 6."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "step6", ROOT / "scripts/73_analogue_uncertainty_review.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_resample_intact_unequal_storms_preserves_event_weighted_estimand():
    frame = pd.DataFrame(
        {"storm": ["one", "three", "three", "three"], "difference": [4.0, -2.0, -2.0, -2.0]}
    )
    result = MODULE.cluster_interval(frame, "storm", draws=2000, seed=12)
    assert result["difference"] == -0.5  # Equal-storm weighting would incorrectly give +1.
    assert result["lower"] == -2.0
    assert result["upper"] == 4.0
    assert result["cluster_count"] == 2
    assert result["query_count"] == 4
    assert result["finite_draws"] == 2000
    assert result == MODULE.cluster_interval(frame, "storm", draws=2000, seed=12)


def test_constant_paired_difference_has_zero_sampling_width():
    frame = pd.DataFrame({"storm": list("aaabbc"), "difference": [-0.125] * 6})
    result = MODULE.cluster_interval(frame, "storm", draws=100)
    assert result["lower"] == result["upper"] == -0.125


def test_missing_values_or_one_cluster_cannot_silently_get_intervals():
    with pytest.raises(ValueError, match="two query clusters"):
        MODULE.cluster_interval(
            pd.DataFrame({"storm": ["a", "a"], "difference": [1.0, 2.0]}), "storm"
        )
    with pytest.raises(ValueError, match="Complete paired"):
        MODULE.cluster_interval(
            pd.DataFrame({"storm": ["a", "b"], "difference": [1.0, np.nan]}), "storm"
        )


def prediction_fixture():
    return pd.DataFrame(
        {
            "query_event_id": ["a", "b"],
            "query_storm_id": ["s1", "s2"],
            "query_onset_utc": pd.to_datetime(["2020-01-01", "2020-02-01"], utc=True),
            "query_watercourse": ["Geul", "Worm"],
            "candidate_count": [21, 25],
            "candidate_storm_count": [12, 15],
            "observed_peak_over_p99_72h": [1.2, 1.7],
            "analogue_absolute_error": [0.2, 0.4],
        }
    )


def test_pairing_is_by_id_and_checks_target_and_candidate_pool():
    reference = prediction_fixture()
    test = reference.iloc[::-1].copy()
    test["analogue_absolute_error"] -= 0.1
    result = MODULE.paired_errors(reference, test)
    np.testing.assert_allclose(result.difference, -0.1)
    test.loc[test.query_event_id.eq("a"), "candidate_count"] = 22
    with pytest.raises(ValueError, match="candidate_count"):
        MODULE.paired_errors(reference, test)
    with pytest.raises(ValueError, match="identical query IDs"):
        MODULE.paired_errors(reference, test.iloc[:1])


def test_case_selection_includes_gain_loss_typical_and_flagged_without_duplicates():
    cases = pd.DataFrame(
        {
            "query_event_id": list("abcdef"),
            "query_onset_utc": pd.date_range("2020-01-01", periods=6, tz="UTC"),
            "difference": [-2.0, 3.0, -0.1, 0.0, 0.1, 0.2],
        }
    )
    meta = pd.DataFrame(
        {"measurement_concern": [False, False, False, False, False, True]}, index=list("abcdef")
    )
    chosen = MODULE.choose_cases(cases, meta)
    assert chosen.query_event_id.is_unique
    assert chosen.iloc[0].query_event_id == "a"
    assert chosen.iloc[1].query_event_id == "b"
    assert chosen.iloc[3].query_event_id == "f"
    assert chosen.iloc[3].selection_reason == "measurement_concern"
