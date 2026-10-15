"""Protect storm selection, temporal contrasts, missingness and dependent inference."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "storm_analysis", ROOT / "scripts/93_analyse_storm_responses.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_storm_selection_includes_ordinary_responses_and_requires_observed_separation():
    dates = pd.date_range("2020-01-01", periods=80, freq="h", tz="UTC")
    rain = pd.DataFrame(0.0, index=dates, columns=["a", "b"])
    rain.iloc[15, 0] = 11
    rain.iloc[28, 0] = 12  # twelve dry hours: distinct episodes
    rain.iloc[40, 0] = 2  # eleven dry hours: remains in the second episode
    storms = M.B.storm_catalogue(rain)
    assert len(storms) == 2
    assert storms.start_utc.tolist() == [dates[15], dates[28]]
    assert storms.end_utc.iloc[1] == dates[40]
    assert storms.boundary_known.all()
    # A missing hour cannot act as evidence for a twelve-hour dry interval.
    rain.iloc[20, 1] = np.nan
    broken = M.B.storm_catalogue(rain)
    assert len(broken) == 2 and not broken.boundary_known.any()
    # An unknown core catchment prevents treating an apparently wet hour as complete.
    rain.iloc[15, 1] = np.nan
    assert len(M.B.storm_catalogue(rain)) == 1


def test_response_maximum_is_not_calculated_across_a_gap():
    values = np.arange(1, 73, dtype=float)
    metrics = M.B.response_metrics(values, 0, 1, 10)
    assert metrics["peak_gain_72h"] == 7.1
    assert metrics["peak_hour"] == 72
    values[20] = np.nan
    assert all(pd.isna(x) for x in M.B.response_metrics(values, 0, 1, 10).values())


def test_prior_donors_must_have_completed_their_response_before_query():
    frame = pd.DataFrame(
        {
            "row_id": ["old", "overlap", "query"],
            "storm_id": ["s1", "s2", "s3"],
            "start_utc": pd.to_datetime(["2020-01-01", "2020-01-04", "2020-01-06"], utc=True),
            "end_utc": pd.to_datetime(["2020-01-02", "2020-01-05", "2020-01-07"], utc=True),
            "followup_end_utc": pd.to_datetime(
                ["2020-01-04", "2020-01-08", "2020-01-10"], utc=True
            ),
            "numeric_usable": True,
            "measurement_concern": False,
            "gauge": "g",
            "year": 2020,
            "footprint": "broad",
            "warm": False,
            M.OUTCOME: [1.0, 999.0, 2.0],
            "rain_total_mm": [10.0, 12.0, 15.0],
            **{x: [1.0, 1.5, 2.0] for x in [*M.FORCING, *M.STATE]},
        }
    )
    _, donors = M.match_events(frame, pd.DataFrame(), pd.DataFrame())
    query = donors[donors.query_row_id.eq("query")]
    assert set(query.donor_row_id) == {"old"}
    # Outcomes do not enter matching distances.
    _, changed = M.match_events(frame.assign(**{M.OUTCOME: 9000.0}), pd.DataFrame(), pd.DataFrame())
    assert np.array_equal(donors.distance, changed.distance)


def test_ridge_uses_training_scales_and_not_test_outcomes():
    train = pd.DataFrame({"x": [0.0, 1, 2, 3], M.OUTCOME: [0.0, 2, 4, 6]})
    test = pd.DataFrame({"x": [4.0], M.OUTCOME: [0.0]})
    predicted = M.ridge_predict(train, test, ["x"])
    assert 6 < predicted[0] < 8
    np.testing.assert_array_equal(
        predicted, M.ridge_predict(train, test.assign(**{M.OUTCOME: 999.0}), ["x"])
    )
    # Appending another test row cannot change the first row's scaling.
    expanded = pd.concat([test, pd.DataFrame({"x": [100000.0]})])
    np.testing.assert_allclose(predicted, M.ridge_predict(train, expanded, ["x"])[:1])


def test_unknown_dry_hours_cannot_establish_a_repeat_pulse():
    rain = pd.Series([1.0, 0, 0, 0, 0, 0, 0, 2])
    assert M.pulse_starts(rain) == [(0, True), (7, True)]
    rain.iloc[3] = np.nan
    assert M.pulse_starts(rain) == [(0, True), (7, False)]


def test_year_intervals_do_not_treat_duplicate_peer_rows_as_independent_storms():
    frame = pd.DataFrame(
        {"storm_id": ["a", "b", "c"], "year": [2020, 2020, 2021], "difference": [-1.0, 0, 2]}
    )
    a = M.year_interval(frame, "difference")
    b = M.year_interval(pd.concat([frame] * 8), "difference")
    assert a == b and a["storms"] == 3 and a["years"] == 2


def test_main_forcing_match_distinguishes_rainfall_timing_from_episode_totals():
    candidates = pd.DataFrame({x: [1.0, 1.0] for x in M.FORCING})
    candidates["log_early_rain"] = [0.0, 3.0]
    query = candidates.iloc[0]
    episode = M.donor_distances(query, candidates, M.EPISODE_FORCING)
    full_window = M.donor_distances(query, candidates, M.FORCING)
    assert episode.tolist() == [0.0, 0.0]
    assert full_window[0] == 0 and full_window[1] > 0
