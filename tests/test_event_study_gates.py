"""Checks for the prospective data-gate contracts."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "event_study_gates", ROOT / "scripts" / "31_event_study_gates.py"
)
GATES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATES)


def test_hourly_contract_keeps_missing_values_on_a_regular_grid(tmp_path):
    path = tmp_path / "hourly.csv"
    pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2020-01-01", periods=3, freq="h", tz="UTC"),
            "gauge": [1.0, np.nan, 2.0],
        }
    ).to_csv(path, index=False)

    frame, valid = GATES.read_hourly(path)

    assert valid
    assert pd.isna(frame.gauge.iloc[1])


def test_hourly_contract_rejects_an_omitted_hour(tmp_path):
    path = tmp_path / "hourly.csv"
    pd.DataFrame(
        {
            "timestamp_utc": ["2020-01-01T00:00Z", "2020-01-01T02:00Z"],
            "gauge": [1.0, 2.0],
        }
    ).to_csv(path, index=False)

    _, valid = GATES.read_hourly(path)

    assert not valid


def test_common_span_counts_the_inclusive_last_hour():
    index = pd.date_range("2005-01-01", "2014-12-31 23:00", freq="h", tz="UTC")
    frame = pd.DataFrame({"A": 1.0, "B": 2.0}, index=index)

    _, _, years = GATES.common_span(frame)

    assert years >= 10


def test_public_weather_requires_a_regular_grid_for_each_watercourse(tmp_path):
    path = tmp_path / "weather.csv"
    pd.DataFrame(
        {
            "timestamp_utc": [
                "2020-01-01T00:00Z",
                "2020-01-01T01:00Z",
                "2020-01-01T00:00Z",
                "2020-01-01T02:00Z",
            ],
            "watercourse": ["A", "A", "B", "B"],
            "temperature_c": [1.0, 1.0, 1.0, 1.0],
            "relative_humidity_pct": [80.0, 80.0, 80.0, 80.0],
            "pressure_hpa": [1000.0, 1000.0, 1000.0, 1000.0],
        }
    ).to_csv(path, index=False)

    _, valid, _ = GATES.read_long_weather(path)

    assert not valid


def test_complete_precursor_event_requires_every_hour_and_signal():
    index = pd.date_range("2025-01-01", periods=200, freq="h", tz="UTC")
    frame = pd.DataFrame({"co2": 400.0, "pressure": 1000.0}, index=index)
    onsets = pd.DatetimeIndex([index[80], index[180]])
    frame.loc[index[150], "co2"] = np.nan

    count = GATES.complete_precursor_events(onsets, frame, ["co2", "pressure"])

    assert count == 1
