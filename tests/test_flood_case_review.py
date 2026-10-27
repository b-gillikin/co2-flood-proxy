"""Protect flood-label scope, whole-episode linkage, unknowns and diagnostic role."""

import numpy as np
import pandas as pd

from src.flood_case_review import archive_stage, build_register, curve_diagnostics, link_inventory


def test_register_retains_ancillary_h3_and_does_not_claim_inundation():
    row = dict(
        first_H3_utc="2021-07-14T12:00:00Z",
        onset_utc="2021-07-13T12:00:00Z",
        review_end_utc="2021-07-18T00:00:00Z",
        H3_observed=1,
        H3_range26=np.nan,
        H3_range27_5=np.nan,
    )
    episodes = pd.DataFrame(
        [
            {**row, "gauge": "core", "series_key": "core", "primary": True, "episode_id": "a"},
            {**row, "gauge": "other", "series_key": "other", "primary": False, "episode_id": "b"},
        ]
    )
    f = build_register(episodes, {"documentary_cases": []}, {"core"})
    assert len(f) == 2
    assert f.primary.sum() == 1
    assert f.impact_confirmation.eq("not_independent_inundation_observation").all()
    assert f.regional_event.nunique() == 1


def inventory():
    return pd.DataFrame(
        [
            {
                "event_id": "q",
                "gauge": "g",
                "onset_utc": pd.Timestamp("2021-07-10T19:00:00Z"),
                "last_crossing_utc": pd.Timestamp("2021-07-14T19:00:00Z"),
                "q_only_input_sample": True,
                "q_only_scoring_sample": False,
                "onset_censored": False,
                "outcome_discharge_fraction": 1.0,
                "outcome_score_admissible": False,
                "measurement_concern": True,
                "history_discharge_fraction": 1.0,
            }
        ]
    )


def test_episode_review_captures_flood_after_original_72h_without_scoring_it_negative():
    register = pd.DataFrame(
        [
            {
                "case_id": "f",
                "gauge": "g",
                "start": pd.Timestamp("2021-07-13T18:00:00Z"),
                "end": pd.Timestamp("2021-07-18T00:00:00Z"),
                "first_H3_utc": pd.Timestamp("2021-07-14T13:00:00Z"),
                "date_precision": "native_recorded_threshold_episode",
            }
        ]
    )
    f = link_inventory(register, inventory())
    assert f.event_id.tolist() == ["q"]
    assert f.timing_role.tolist() == ["H3_after_72h"]
    assert f.q_only_input_sample.iloc[
        0
    ]  # an unavailable label need not imply unavailable past inputs
    assert not f.q_only_scoring_sample.iloc[0]


def test_coarse_documentary_date_does_not_turn_candidates_into_flood_labels():
    register = pd.DataFrame(
        [
            {
                "case_id": "f",
                "gauge": "g",
                "start": pd.Timestamp("2021-01-01T00:00:00Z"),
                "end": pd.Timestamp("2022-01-01T00:00:00Z"),
                "first_H3_utc": pd.NaT,
                "date_precision": "year_only",
            }
        ]
    )
    f = link_inventory(register, inventory())
    assert f.match_status.tolist() == ["coarse_documentary_candidate_not_flood_label"]


def test_recovery_query_is_not_counted_as_a_new_flood_onset_prediction():
    f = inventory()
    f["onset_utc"] = pd.Timestamp("2021-07-15T00:00:00Z")
    f["last_crossing_utc"] = pd.Timestamp("2021-07-15T03:00:00Z")
    register = pd.DataFrame(
        [
            {
                "case_id": "f",
                "gauge": "g",
                "start": pd.Timestamp("2021-07-13T18:00:00Z"),
                "end": pd.Timestamp("2021-07-18T00:00:00Z"),
                "first_H3_utc": pd.Timestamp("2021-07-14T13:00:00Z"),
                "date_precision": "native_recorded_threshold_episode",
            }
        ]
    )
    assert link_inventory(register, f).timing_role.tolist() == ["after_first_H3"]


def test_unlabelled_candidates_are_not_asserted_to_be_non_floods():
    assert archive_stage(0, 4, 0) == "no_confirmed_positive_with_incomplete_labelling"
    assert archive_stage(0, 0, 0) == "no_positive_in_observed_label_archive"
    assert archive_stage(2, 4, 0) == "confirmed_positive_available_not_selected"
    assert archive_stage(2, 4, 1) == "confirmed_positive_selected_examine_estimate"


def test_averaging_can_dilute_an_extreme_member_without_any_small_member_peak():
    q = np.zeros(72)
    q[0] = 10
    d = np.zeros((2, 72))
    d[0, 0] = 10
    d[1, 24] = 10
    f = curve_diagnostics(q, d, d)
    assert f["peak_estimate_pattern"] == "extreme_member_diluted_or_time_smeared"
    assert f["peak_loss_from_time_averaging"] == 5


def test_oracle_is_only_a_diagnostic_and_does_not_replace_selected_donors():
    q = np.full(72, 2.0)
    a = np.stack([q, q + 1])
    selected = a[1:].copy()
    original = selected.copy()
    f = curve_diagnostics(q, a, selected)
    assert f["oracle_best_single_curve_rmse"] == 0
    assert f["selected_mean_curve_rmse_recomputed"] == 1
    np.testing.assert_array_equal(selected, original)
