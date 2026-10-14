"""Hand-computed phase entries, censoring, averaging and escalation integrity."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "thresholds", ROOT / "scripts/86_analyse_warning_threshold_progression.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_positive_survives_later_gap_but_missing_negative_is_unknown():
    assert M.reach_label([1, 3, np.nan], 3) == (1.0, 0.5)
    assert np.isnan(M.reach_label([1, 2, np.nan], 3)[0])
    assert M.reach_label([1, 2, 2.9], 3)[0] == 0
    assert np.isnan(M.reach_label([1, 3, 2], 3, [True, False, True])[0])


def test_entry_includes_equality_and_marks_unobserved_start():
    t = pd.date_range("2020-01-01", periods=6, freq="15min", tz="UTC")
    entries = M.crossing_entries(pd.Series([1, 2, 2, 1, np.nan, 3], index=t), 2)
    assert entries.timestamp_utc.tolist() == [t[1], t[5]]
    assert entries.adjacent_below.tolist() == [True, False]


def test_skip_levels_and_missing_recovery_are_not_precise_physical_progression():
    t = pd.date_range("2020-01-01", periods=400, freq="15min", tz="UTC")
    q = pd.Series(0.0, index=t)
    q.iloc[1] = 5
    thresholds = pd.Series({"H1": 2.0, "H2": 3.0, "H3": 5.0})
    episodes, phases = M.episode_catalogue(q, thresholds, "g", "g", True, {"range26": q.notna()})
    assert len(episodes) == 1
    assert episodes.H3_elapsed_from_first_H1_h.iloc[0] == 0
    assert phases.observed_reach.tolist() == [1, 1, 1]
    q.iloc[3] = np.nan
    episodes, _ = M.episode_catalogue(q, thresholds, "g", "g", True, {"range26": q.notna()})
    assert not episodes.recovery_observed.iloc[0]
    assert episodes.H3_observed.iloc[0] == 1


def test_long_recorded_recovery_separates_episodes_and_boundary_is_censored():
    t = pd.date_range("2020-01-01", periods=600, freq="15min", tz="UTC")
    q = pd.Series(0.0, index=t)
    q.iloc[[1, 400]] = 2
    thresholds = pd.Series({"H1": 2.0, "H2": 3.0, "H3": 4.0})
    e, _ = M.episode_catalogue(q, thresholds, "g", "g", True, {})
    assert len(e) == 2 and e.recovery_observed.tolist() == [True, False]
    assert e.H3_observed.iloc[0] == 0 and np.isnan(e.H3_observed.iloc[1])


def test_native_mean_can_cross_when_hourly_mean_does_not():
    t = pd.date_range("2020-01-01 00:15", periods=4, freq="15min", tz="UTC")
    q = pd.Series([0, 0, 0, 8.0], index=t)
    ingest = M.load_module("45", "test_threshold_ingest")
    hourly = ingest.four_quarter_hour_mean(q, pd.Series(t))
    assert M.reach_label(q, 5)[0] == 1 and M.reach_label(hourly, 5)[0] == 0


def test_group_balancing_and_unknown_loss_bounds_are_explicit():
    assert M.group_mean([1, 1, 0], ["a", "a", "b"]) == 0.5
    assert M.squared_error_bounds(0.2, 0.8, 1) == (0.03999999999999998, 0.6400000000000001)
    lower, upper = M.squared_error_bounds(0, 1, np.nan)
    assert lower == 0 and upper == 1


def test_threshold_parser_and_capacity_conflict_are_explicit(tmp_path):
    source = tmp_path / "thresholds.csv"
    source.write_text(
        "Discharge in m3/s,,,,,\n,,,H1,H2,H3\nGeul Cottessen,10.Q.29,,10,20,27.5\nGulp Azijnfabriek,13.Q.34,,5,8,16\nH3,Flooding,,,,\n"
    )
    thresholds = M.read_thresholds(source)
    assert len(thresholds) == 2
    assert thresholds.loc["10.Q.29", "H3"] == 27.5
    assert thresholds.loc["13.Q.34", "H3"] == 16


def test_phase_eligibility_depends_on_cutoff_not_future_escalation():
    sample = pd.DataFrame({"event_id": ["below", "already"], "complete_scoring_sample": True})
    labels = pd.DataFrame(
        {"H3_below_cutoff": [True, False], "H3_native": [0, 1]}, index=sample.event_id
    )
    a = M.phase_sample(sample, labels, "H3")
    assert a.complete_scoring_sample.tolist() == [True, False]
    labels["H3_native"] = [1, 0]
    pd.testing.assert_frame_equal(a, M.phase_sample(sample, labels, "H3"))


def test_history_repair_is_old_isolated_low_flow_and_never_mutates_source():
    t = pd.date_range("2020-01-01", periods=50, freq="h", tz="UTC")
    history = pd.Series(1.0, index=t)
    history.iloc[[2, 5, 6, 10, 30]] = np.nan
    history.iloc[9] = 5.0
    native = pd.Series(1.0, index=pd.date_range(t[0], t[-1], freq="15min"))
    original = history.copy()
    fixed, log = M.repair_isolated_history(history, native, t[-1], 3)
    assert fixed.iloc[2] == 1
    assert fixed.iloc[[5, 6, 10, 30]].isna().all()
    assert [r["timestamp_utc"] for r in log] == [t[2]]
    pd.testing.assert_series_equal(history, original)


def test_native_high_water_prevents_low_hourly_neighbor_repair():
    t = pd.date_range("2020-01-01", periods=50, freq="h", tz="UTC")
    history = pd.Series(1.0, index=t)
    history.iloc[2] = np.nan
    native = pd.Series(1.0, index=pd.date_range(t[0], t[-1], freq="15min"))
    native.loc[t[2]] = 3.0
    fixed, log = M.repair_isolated_history(history, native, t[-1], 3)
    assert pd.isna(fixed.iloc[2]) and log == []


def test_independent_native_outcome_does_not_impute_a_missing_negative():
    spec = importlib.util.spec_from_file_location(
        "threshold_audit", ROOT / "scripts/87_audit_warning_threshold_results.py"
    )
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    t = pd.date_range("2020-01-01", periods=289, freq="15min", tz="UTC")
    q = pd.Series(1.0, index=t)
    q.iloc[1] = np.nan
    assert np.isnan(audit.native_outcome(q, t[0], 3)[0])
    q.iloc[2] = 3
    assert audit.native_outcome(q, t[0], 3) == (1.0, 0.5, False)


def test_maximal_conventional_cohort_has_no_nonexistent_model_contrast():
    rows = pd.DataFrame(
        [
            {
                "cohort": "h1_r0_maximal",
                "level": "H3",
                "scenario": "all_rivers",
                "analysis": "main",
                "target_k": 5,
                "arm": "r0",
                "query_event_id": "q",
                "query_storm_id": "storm",
                "query_onset_utc": "2020-01-01T00:00:00Z",
                "actual_donors": 1,
                "share_squared_error": 1.0,
                "archive_squared_error": 1.0,
                "observed_reach": 1.0,
                "first_escalation_24h": True,
            }
        ]
    )
    result = M.paired_intervals(rows)
    assert result.reference.eq("archive").all()
    assert result.challenger.eq("r0").all()
    assert result["difference"].dropna().eq(0).all()
