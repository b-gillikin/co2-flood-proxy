"""Tests for the case-crossover event definitions (protocol draft 0.9 §3-§5)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import (
    assign_eras,
    at_risk_hours,
    cluster_regional_storms,
    episode_onsets,
    episode_table,
    era_thresholds,
    hourly_presence,
    stage_onsets,
    storm_table,
    stratum_labels,
    warm_season,
)


def hours(n, start="2025-01-01"):
    return pd.date_range(start, periods=n, freq="h", tz="UTC")


def test_episode_onsets_merge_consecutive_recrossings_through_72_hours():
    index = hours(150)
    series = pd.Series(0.0, index=index)
    series.loc[[index[1], index[73], index[145]]] = 2.0

    onsets = episode_onsets(series, threshold=1.0, merge_hours=72)

    assert list(onsets) == [index[1]]


def test_episode_table_reports_unbounded_single_linkage_chain():
    index = hours(150)
    series = pd.Series(0.0, index=index)
    series.loc[[index[1], index[73], index[145]]] = 2.0

    episodes = episode_table(series, threshold=1.0, merge_hours=72)

    assert len(episodes) == 1
    assert episodes.loc[0, "n_crossings"] == 3
    assert episodes.loc[0, "chain_span_hours"] == 144
    assert not episodes.loc[0, "onset_censored"]


def test_record_resuming_above_threshold_starts_a_censored_episode():
    index = hours(7)
    series = pd.Series([0.0, 2.0, 0.0, np.nan, 2.0, 0.0, 2.0], index=index)

    episodes = episode_table(series, threshold=1.0, merge_hours=1)

    assert episodes.onset_utc.tolist() == [index[1], index[4], index[6]]
    assert episodes.onset_censored.tolist() == [False, True, False]
    assert list(episode_onsets(series, threshold=1.0, merge_hours=1)) == [index[1], index[6]]


def test_censored_entry_absorbs_recrossings_within_72_hours():
    index = hours(100)
    series = pd.Series(0.0, index=index)
    series.iloc[10] = np.nan
    series.iloc[11] = 2.0  # true onset hidden by the gap
    series.iloc[40] = 2.0  # re-crossing 29 h later is not a new onset

    episodes = episode_table(series, threshold=1.0)

    assert len(episodes) == 1
    assert episodes.loc[0, "onset_censored"]
    assert episode_onsets(series, threshold=1.0).empty


def test_omitted_timestamp_is_not_bridged():
    index = pd.DatetimeIndex(["2025-01-01 00:00Z", "2025-01-01 02:00Z"])
    series = pd.Series([0.0, 2.0], index=index)

    assert episode_onsets(series, threshold=1.0).empty


def test_inadmissible_later_peak_does_not_censor_an_observed_onset():
    index = hours(6)
    series = pd.Series([0.0, 2.0, 9.0, 9.0, 2.0, 0.0], index=index)
    admissible = pd.Series([True, True, False, False, True, True], index=index)

    episodes = episode_table(series, threshold=1.0, admissible=admissible)

    assert episodes.onset_utc.tolist() == [index[1]]
    assert not episodes.loc[0, "onset_censored"]


def test_inadmissible_onset_hour_is_censored():
    index = hours(4)
    series = pd.Series([0.0, 9.0, 2.0, 0.0], index=index)
    admissible = pd.Series([True, False, True, True], index=index)

    episodes = episode_table(series, threshold=1.0, admissible=admissible)

    assert episodes.onset_censored.tolist() == [True]


def test_thresholds_are_computed_within_each_rating_era():
    index = hours(200)
    series = pd.Series(np.r_[np.arange(100.0), 1000 + np.arange(100.0)], index=index)
    eras = pd.Series(["A"] * 100 + ["B"] * 100, index=index)

    per_era, hourly = era_thresholds(series, eras)

    assert per_era["A"] == pytest.approx(np.quantile(np.arange(100.0), 0.99))
    assert per_era["B"] == pytest.approx(1000 + np.quantile(np.arange(100.0), 0.99))
    assert hourly.iloc[0] == per_era["A"] and hourly.iloc[-1] == per_era["B"]


def test_crossing_at_an_era_boundary_is_censored():
    index = hours(4)
    series = pd.Series([0.0, 0.0, 5.0, 0.0], index=index)
    eras = pd.Series(["A", "A", "B", "B"], index=index)

    episodes = episode_table(series, threshold=1.0, eras=eras)

    assert episodes.onset_censored.tolist() == [True]


def test_eras_are_half_open_and_may_not_overlap():
    table = pd.DataFrame(
        {
            "era_id": ["A", "B"],
            "valid_from_utc": ["2020-01-01T00:00Z", "2020-01-01T02:00Z"],
            "valid_to_utc": ["2020-01-01T02:00Z", None],
        }
    )
    labels = assign_eras(hours(4, "2020-01-01"), table)
    assert labels.tolist() == ["A", "A", "B", "B"]

    table.loc[0, "valid_to_utc"] = "2020-01-01T03:00Z"
    with pytest.raises(ValueError, match="overlap"):
        assign_eras(hours(4, "2020-01-01"), table)


def test_at_risk_excludes_72_hours_after_any_crossing_and_high_previous_flow():
    index = hours(120)
    series = pd.Series(0.0, index=index)
    series.iloc[10] = 2.0
    series.iloc[11] = 2.0

    risk = at_risk_hours(series, threshold=1.0)

    assert risk.onset.iloc[10] and risk.at_risk.iloc[10]
    assert not risk.at_risk.iloc[11]  # previous hour above threshold
    assert not risk.at_risk.iloc[10 + 72]  # crossing exactly 72 h earlier
    assert risk.at_risk.iloc[10 + 73]
    assert not risk.at_risk.iloc[0]  # no previous hour


def test_at_risk_onsets_are_exactly_the_uncensored_episode_onsets():
    rng = np.random.default_rng(20260918)
    index = hours(6000, "2020-01-01")
    for _ in range(20):
        series = pd.Series(rng.gamma(0.4, 1.0, len(index)), index=index)
        series[rng.random(len(index)) < 0.03] = np.nan
        admissible = pd.Series(rng.random(len(index)) > 0.02, index=index)
        eras = pd.Series(np.where(np.arange(len(index)) < 3000, "A", "B"), index=index)
        _, threshold = era_thresholds(series, eras)

        risk = at_risk_hours(series, threshold, admissible, eras)
        onsets = episode_onsets(series, threshold, 72, admissible, eras)

        assert risk.index[risk.onset].equals(onsets)
        assert risk.at_risk.loc[onsets].all()


def test_at_risk_requires_a_complete_hourly_grid():
    series = pd.Series(
        [0.0, 0.0], index=pd.DatetimeIndex(["2025-01-01 00:00Z", "2025-01-01 02:00Z"])
    )
    with pytest.raises(ValueError, match="complete hourly grid"):
        at_risk_hours(series, threshold=1.0)


def test_strata_and_season_follow_the_utc_calendar():
    index = pd.DatetimeIndex(["2021-04-30 23:00Z", "2021-05-01 00:00Z", "2021-10-31 23:00Z"])

    assert stratum_labels(index, "Geul").tolist() == [
        "Geul|2021-04|23",
        "Geul|2021-05|00",
        "Geul|2021-10|23",
    ]
    assert warm_season(index).tolist() == [False, True, True]


def test_regional_storms_join_events_at_72_hours_but_not_after():
    start = pd.Timestamp("2020-01-01", tz="UTC")
    events = pd.DataFrame(
        {
            "watercourse": ["A", "B", "C"],
            "onset_utc": [start, start + pd.Timedelta(hours=72), start + pd.Timedelta(hours=145)],
        }
    )

    storms = cluster_regional_storms(events)

    assert storms.storm_id.tolist() == ["storm_0001", "storm_0001", "storm_0002"]


def test_storm_season_and_estimable_onsets():
    events = pd.DataFrame(
        {
            "watercourse": ["A", "B", "A"],
            "onset_utc": pd.to_datetime(
                ["2021-04-30 20:00", "2021-05-01 10:00", "2021-07-14 12:00"], utc=True
            ),
            "onset_censored": [False, True, True],
        }
    )

    table = storm_table(cluster_regional_storms(events))

    assert table.warm_season.tolist() == [False, True]
    assert table.n_onsets.tolist() == [2, 1]
    assert table.n_uncensored.tolist() == [1, 0]


def test_hourly_mask_uses_trailing_endpoints_and_does_not_fill_gaps():
    index = pd.date_range("2020-01-01", periods=9, freq="15min")
    mask = pd.DataFrame({"a": True}, index=index)
    mask.iloc[2] = False
    assert hourly_presence(mask).a.tolist() == [False, False, True]


def test_stage_crossing_cannot_span_gap_or_datum_change():
    index = hours(8, "2020-01-01")
    stage = pd.Series([0, 2, np.nan, 2, 0, 2, 0, 2], index=index, dtype=float)
    eras = pd.Series(["A"] * 5 + ["B"] * 3, index=index)
    result = stage_onsets(stage, eras, {"A": 1, "B": 1}, merge_hours=0)
    assert result.onset_utc.tolist() == [index[1], index[7]]
