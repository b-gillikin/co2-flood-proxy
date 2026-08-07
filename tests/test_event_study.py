"""Tests for the prospective event-study definitions."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import (
    cluster_regional_storms,
    contiguous_time_blocks,
    episode_onsets,
    exact_onset_events,
    heldout_signal_transfer,
    pressure_residuals_by_era,
    quiet_control_times,
    robust_standardize,
)


def test_episode_onsets_merge_consecutive_recrossings_through_72_hours():
    index = pd.date_range("2025-01-01", periods=150, freq="h", tz="UTC")
    series = pd.Series(0.0, index=index)
    series.loc[[index[1], index[73], index[145]]] = 2.0

    onsets = episode_onsets(series, threshold=1.0, merge_hours=72)

    assert list(onsets) == [index[1]]


def test_episode_onsets_do_not_bridge_a_missing_hour():
    index = pd.date_range("2025-01-01", periods=7, freq="h", tz="UTC")
    series = pd.Series([0.0, 2.0, 0.0, np.nan, 2.0, 0.0, 2.0], index=index)

    onsets = episode_onsets(series, threshold=1.0, merge_hours=1)

    assert list(onsets) == [index[1], index[6]]


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


def test_censored_event_is_not_eligible_for_exact_onset_analysis():
    events = pd.DataFrame(
        {
            "event": ["2021 flood", "later high water"],
            "onset_utc": pd.to_datetime(["2021-07-13", "2025-01-09"], utc=True),
            "onset_censored": [True, False],
        }
    )

    eligible = exact_onset_events(events)

    assert eligible.event.tolist() == ["later high water"]


def test_controls_match_month_hour_and_avoid_event_neighbourhoods():
    index = pd.date_range("2018-01-01", "2025-12-31 23:00", freq="h", tz="UTC")
    event = pd.Timestamp("2025-03-15 06:00", tz="UTC")
    other_event = pd.Timestamp("2024-03-15 06:00", tz="UTC")

    controls = quiet_control_times(index, event, [event], [other_event], n_controls=5)

    assert len(controls) == 5
    assert set(controls.month) == {3}
    assert set(controls.hour) == {6}
    assert all(abs(time - other_event) > pd.Timedelta(days=7) for time in controls)
    assert list(abs(controls - event)) == sorted(abs(controls - event))


def test_control_availability_is_respected():
    index = pd.date_range("2020-01-01", "2022-12-31 23:00", freq="h", tz="UTC")
    event = pd.Timestamp("2022-05-10 12:00", tz="UTC")
    available = pd.Series(False, index=index)
    allowed = pd.Timestamp("2020-05-10 12:00", tz="UTC")
    available.loc[allowed] = True

    controls = quiet_control_times(index, event, [event], [], available, n_controls=5)

    assert controls.tolist() == [allowed]


def test_missing_control_availability_is_not_treated_as_true():
    index = pd.date_range("2020-01-01", "2022-12-31 23:00", freq="h", tz="UTC")
    event = pd.Timestamp("2022-05-10 12:00", tz="UTC")
    available = pd.Series([True, pd.NA], index=[index[0], index[1]], dtype="boolean")

    controls = quiet_control_times(index, event, [event], [], available, n_controls=5)

    assert controls.empty


def test_robust_standardization_uses_reference_only():
    result = robust_standardize(pd.Series([10.0]), pd.Series([0.0, 1.0, 2.0, 3.0, 4.0]))
    assert result.iloc[0] == 8.0


def synthetic_contrasts(values):
    rows = []
    for (watercourse, block), value in values.items():
        rows.append(
            {
                "watercourse": watercourse,
                "time_block": block,
                "signal": "rain_72h",
                "contrast": value,
            }
        )
    return pd.DataFrame(rows)


def test_positive_signal_transfers_to_every_heldout_fold():
    contrasts = synthetic_contrasts(
        {(watercourse, block): 1.0 for watercourse in "ABC" for block in [1, 2]}
    )

    transfer = heldout_signal_transfer(contrasts)

    assert transfer.sign_concordant.eq(True).all()
    assert transfer.n_reference_watercourses.eq(2).all()
    assert transfer.n_reference_events.eq(2).all()


def test_null_reference_direction_is_reported_as_undefined():
    contrasts = synthetic_contrasts(
        {("A", 1): 2.0, ("A", 2): 4.0, ("B", 1): 3.0, ("B", 2): -1.0, ("C", 1): 5.0, ("C", 2): 1.0}
    )

    transfer = heldout_signal_transfer(contrasts)
    fold = transfer[transfer.heldout_watercourse.eq("A") & transfer.heldout_time_block.eq(1)].iloc[
        0
    ]

    assert fold.reference_network_median == 0
    assert pd.isna(fold.sign_concordant)


def test_heterogeneous_signal_fails_heldout_sign_concordance():
    contrasts = synthetic_contrasts(
        {
            ("A", 1): 2.0,
            ("A", 2): 100.0,
            ("B", 1): 100.0,
            ("B", 2): -1.0,
            ("C", 1): 100.0,
            ("C", 2): -2.0,
        }
    )

    transfer = heldout_signal_transfer(contrasts)
    fold = transfer[transfer.heldout_watercourse.eq("A") & transfer.heldout_time_block.eq(1)].iloc[
        0
    ]

    assert fold.reference_network_median == -1.5
    assert fold.n_reference_watercourses == 2
    assert not fold.sign_concordant


def test_pressure_residuals_are_fit_separately_by_sensor_era():
    index = pd.date_range("2020-01-01", periods=500, freq="h", tz="UTC")
    rng = np.random.default_rng(42)
    pressure = 1000 + np.sin(np.arange(500) / 20)
    era = np.where(np.arange(500) < 250, "old", "new")
    offset = np.where(era == "old", 400.0, 1200.0)
    frame = pd.DataFrame(
        {
            "iot_air_pressure_hpa": pressure,
            "iot_co2_ppm": offset + 3 * pressure + rng.normal(size=500),
            "sensor_era": era,
        },
        index=index,
    )

    residual = pressure_residuals_by_era(frame, pd.Series(True, index=index))

    for label in ["old", "new"]:
        values = residual[frame.sensor_era.eq(label)].dropna()
        assert abs(values.median()) < 1e-8
        assert abs(values.abs().median() - 1) < 1e-8


def test_pressure_baseline_rejects_too_little_calibration_data():
    index = pd.date_range("2020-01-01", periods=50, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "iot_air_pressure_hpa": np.arange(50, dtype=float),
            "iot_co2_ppm": np.arange(50, dtype=float),
            "sensor_era": "one",
        },
        index=index,
    )

    with pytest.raises(ValueError, match="100 complete quiet calibration"):
        pressure_residuals_by_era(frame, pd.Series(True, index=index))


def test_pressure_change_does_not_bridge_an_omitted_timestamp():
    index = pd.date_range("2020-01-01", periods=260, freq="h", tz="UTC").delete(120)
    pressure = pd.Series(np.arange(len(index), dtype=float), index=index)
    frame = pd.DataFrame(
        {
            "iot_air_pressure_hpa": pressure,
            "iot_co2_ppm": 400 + pressure,
            "sensor_era": "one",
        },
        index=index,
    )

    residual = pressure_residuals_by_era(
        frame,
        pd.Series(True, index=index),
        lags=(1,),
    )

    assert pd.isna(residual.loc[index[120]])


def test_five_time_blocks_are_contiguous_and_cover_the_record():
    index = pd.date_range("2005-01-01", "2014-12-31 23:00", freq="h", tz="UTC")
    blocks = contiguous_time_blocks(index)

    assert len(blocks) == 5
    assert blocks[0][0] == index.min()
    assert blocks[-1][1] == index.max() + pd.Timedelta(hours=1)
    assert all(left[1] == right[0] for left, right in zip(blocks[:-1], blocks[1:], strict=True))
