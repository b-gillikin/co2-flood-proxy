"""Checks for the prospective data-gate contracts."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

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


def test_observation_density_rejects_sparse_series_with_long_endpoints():
    index = pd.date_range("2012-01-01", "2021-12-31 23:00", freq="h", tz="UTC")
    frame = pd.DataFrame({"gauge": np.nan}, index=index)
    frame.loc[index[0], "gauge"] = 1.0
    frame.loc[index[-1], "gauge"] = 2.0

    summary = GATES.coverage_summary(frame, index[0], index[-1])

    assert not GATES.coverage_passes(summary)


def test_joint_period_must_contain_july_2021():
    assert GATES.contains_july_2021(
        pd.Timestamp("2012-01-01", tz="UTC"), pd.Timestamp("2021-12-31", tz="UTC")
    )
    assert not GATES.contains_july_2021(
        pd.Timestamp("2005-01-01", tz="UTC"), pd.Timestamp("2015-12-31", tz="UTC")
    )


def test_episode_feasibility_excludes_crossings_outside_joint_period():
    index = pd.date_range("2020-01-01", periods=500, freq="h", tz="UTC")
    frame = pd.DataFrame({"gauge": 0.0}, index=index)
    frame.loc[[index[20], index[250]], "gauge"] = 2.0

    counts, _, events = GATES.episode_feasibility(frame, index[200], index[400])

    assert counts == {"gauge": 1}
    assert events.onset_utc.tolist() == [index[250]]


def test_nearest_donor_availability_requires_complete_12_hour_change():
    index = pd.date_range("2025-01-01", periods=100, freq="h", tz="UTC")
    discharge = pd.DataFrame({"A": 1.0, "B": 2.0}, index=index)
    discharge.loc[index[75], "B"] = np.nan
    events = pd.DataFrame({"gauge": ["A", "A"], "onset_utc": [index[50], index[80]]})
    gauges = pd.DataFrame(
        {
            "gauge": ["A", "B"],
            "latitude": [50.0, 50.1],
            "longitude": [6.0, 6.1],
        }
    )

    availability = GATES.donor_event_availability(discharge, events, gauges)
    receiver = availability[availability.receiver_gauge.eq("A")].iloc[0]

    assert receiver.donor_gauge == "B"
    assert receiver.n_receiver_events == 2
    assert receiver.n_donor_complete == 1
    assert receiver.availability == 0.5


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


def test_catchment_contract_opens_and_checks_geometries(tmp_path):
    geopandas = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely.geometry")
    path = tmp_path / "catchments.gpkg"
    frame = geopandas.GeoDataFrame(
        {"watercourse": ["A", "B"]},
        geometry=[
            shapely.box(0, 0, 1, 1),
            shapely.box(2, 0, 3, 1),
        ],
        crs="EPSG:28992",
    )
    frame.to_file(path, driver="GPKG")

    valid, observed = GATES.validate_catchments(path, ["A", "B"])

    assert valid, observed
