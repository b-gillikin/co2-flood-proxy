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


def test_unmet_information_benchmark_does_not_fail_input_contract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rows = []
    GATES.add(rows, "Verified time axis", True, "hourly UTC", "valid")
    GATES.add(rows, "Regional storm benchmark", False, 12, ">=40", binding=False)

    table = pd.DataFrame(rows)

    assert table.loc[1, "status"] == "REVIEW"
    assert GATES.write_report(table)
    report = (tmp_path / "results/event_study/gate_audit.md").read_text()
    assert "Input contracts: **PASS**" in report


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
            "relative_humidity_pct": [80.0, 80.0, 80.0, 80.0],
            "surface_pressure_hpa": [1000.0, 1000.0, 1000.0, 1000.0],
        }
    ).to_csv(path, index=False)

    _, valid, _ = GATES.read_long_weather(path)

    assert not valid


def test_catchment_contract_opens_and_checks_geometries(tmp_path):
    geopandas = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely.geometry")
    path = tmp_path / "catchments.gpkg"
    frame = geopandas.GeoDataFrame(
        {"watercourse": ["A", "B"], "dem_source": "Copernicus GLO-30"},
        geometry=[
            shapely.box(0, 0, 1, 1),
            shapely.box(2, 0, 3, 1),
        ],
        crs="EPSG:28992",
    )
    frame.to_file(path, driver="GPKG")

    valid, observed = GATES.validate_catchments(path, ["A", "B"])

    assert valid, observed


def test_catchments_without_a_named_dem_fail(tmp_path):
    geopandas = pytest.importorskip("geopandas")
    shapely = pytest.importorskip("shapely.geometry")
    path = tmp_path / "catchments.gpkg"
    geopandas.GeoDataFrame(
        {"watercourse": ["A"]}, geometry=[shapely.box(0, 0, 1, 1)], crs="EPSG:28992"
    ).to_file(path, driver="GPKG")

    valid, _ = GATES.validate_catchments(path, ["A"])

    assert not valid


def test_episode_feasibility_uses_joint_period_and_counts_censored_onsets():
    index = pd.date_range("2020-01-01", periods=500, freq="h", tz="UTC")
    frame = pd.DataFrame({"gauge": 0.0}, index=index)
    frame.loc[[index[20], index[250]], "gauge"] = 2.0
    frame.loc[index[349], "gauge"] = np.nan
    frame.loc[index[350], "gauge"] = 2.0
    eras = pd.DataFrame(
        {
            "gauge": ["gauge"],
            "era_id": ["one"],
            "valid_from_utc": ["2019-01-01T00:00Z"],
            "valid_to_utc": [None],
            "domain_min_m3s": [None],
            "domain_max_m3s": [None],
            "relation_uniform_above_m3s": [0.0],
        }
    )

    counts, _, events, risk = GATES.episode_feasibility(
        frame, {"gauge": eras}, index[200], index[400]
    )

    assert counts == {"gauge": {"uncensored": 1, "censored": 1}}
    assert events.onset_utc.tolist() == [index[250], index[350]]
    assert risk.loc[0, "strata_with_onset"] == 1


def test_overlapping_rating_eras_fail_the_gate(tmp_path):
    path = tmp_path / "eras.csv"
    pd.DataFrame(
        {
            "gauge": ["A", "A"],
            "era_id": ["1", "2"],
            "valid_from_utc": ["2010-01-01T00:00Z", "2015-01-01T00:00Z"],
            "valid_to_utc": ["2016-01-01T00:00Z", None],
            "domain_min_m3s": [0.0, 0.0],
            "domain_max_m3s": [10.0, 12.0],
            "relation_uniform_above_m3s": [0.0, 0.0],
            "source_document": ["curve.pdf", "curve.pdf"],
        }
    ).to_csv(path, index=False)

    _, valid, observed = GATES.read_rating_eras(path, ["A"])

    assert not valid
    assert "overlap" in str(observed)


def era_rows(gauge, uniform_above, domain_max=(12.0, 12.0)):
    """One era over two intervals with a hole between them."""
    return pd.DataFrame(
        {
            "gauge": gauge,
            "era_id": ["A", "A"],
            "valid_from_utc": ["2010-01-01T00:00Z", "2016-01-01T00:00Z"],
            "valid_to_utc": ["2015-01-01T00:00Z", None],
            "domain_min_m3s": [0.0, 0.0],
            "domain_max_m3s": list(domain_max),
            "relation_uniform_above_m3s": [uniform_above, uniform_above],
            "source_document": ["curve.pdf", "curve.pdf"],
        }
    )


def test_an_era_may_span_intervals_but_must_agree_on_its_domain(tmp_path):
    path = tmp_path / "eras.csv"
    era_rows("A", 0.5).to_csv(path, index=False)
    _, valid, _ = GATES.read_rating_eras(path, ["A"])
    assert valid

    era_rows("A", 0.5, domain_max=(12.0, 10.0)).to_csv(path, index=False)
    _, valid, observed = GATES.read_rating_eras(path, ["A"])
    assert not valid
    assert "disagree" in str(observed)


def test_merged_era_fails_when_p99_lies_where_its_versions_disagree():
    index = pd.date_range("2020-01-01", periods=1000, freq="h", tz="UTC")
    frame = pd.DataFrame({"G": np.linspace(0.0, 2.0, len(index))}, index=index)

    merges = GATES.era_merge_checks(frame, {"G": era_rows("G", 3.0)}, index[0], index[-1])
    assert merges.p99_m3s.iloc[0] < 3.0
    assert not merges.ok.any()

    merges = GATES.era_merge_checks(frame, {"G": era_rows("G", 1.0)}, index[0], index[-1])
    assert merges.ok.all()


def write_fixture(root, n_units=6, storms_every_days=20):
    """A complete synthetic input set that should pass every binding gate."""
    import geopandas
    import shapely.geometry

    rng = np.random.default_rng(7)
    index = pd.date_range("2011-01-01", "2021-12-31 23:00", freq="h", tz="UTC")
    names = [f"W{k}" for k in range(n_units)]
    storm_hours = np.zeros(len(index))
    storm_hours[:: storms_every_days * 24] = 1
    common = np.convolve(storm_hours, np.ones(12), mode="same")
    flow = {
        f"G{k}": 1 + rng.gamma(1.0, 0.2, len(index)) + 20 * common * rng.random(len(index))
        for k in range(n_units)
    }
    interim = root / "data" / "interim"
    interim.mkdir(parents=True)
    pd.DataFrame({"timestamp_utc": index, **flow}).to_csv(
        interim / "event_study_discharge_hourly.csv", index=False
    )
    pd.DataFrame(
        {
            "gauge": list(flow),
            "watercourse": names,
            "independence_unit": names,
            "latitude": 50.8,
            "longitude": 5.9,
            "include_primary": True,
            "natural_tributary": True,
            "july_2021_status": "documented",
            **{column: True for column in GATES.QA_COLUMNS},
        }
    ).to_csv(interim / "event_study_gauges.csv", index=False)
    pd.DataFrame(
        {
            "gauge": list(flow),
            "era_id": "1",
            "valid_from_utc": "2000-01-01T00:00Z",
            "valid_to_utc": None,
            "domain_min_m3s": 0.0,
            "domain_max_m3s": 1000.0,
            "relation_uniform_above_m3s": 0.0,
            "source_document": "synthetic",
        }
    ).to_csv(interim / "event_study_rating_eras.csv", index=False)
    pd.DataFrame(
        {"timestamp_utc": index, **{name: rng.gamma(0.2, 1.0, len(index)) for name in names}}
    ).to_csv(interim / "radolan_catchment_hourly.csv", index=False)
    geopandas.GeoDataFrame(
        {"watercourse": names, "dem_source": "synthetic"},
        geometry=[shapely.geometry.box(k, 0, k + 1, 1) for k in range(n_units)],
        crs="EPSG:28992",
    ).to_file(interim / "event_study_catchments.gpkg", driver="GPKG")
    pd.concat(
        pd.DataFrame(
            {
                "timestamp_utc": index,
                "watercourse": name,
                "relative_humidity_pct": 80.0,
                "surface_pressure_hpa": 1000.0,
            }
        )
        for name in names
    ).to_csv(interim / "event_study_weather_hourly.csv", index=False)
    pd.DataFrame(
        {
            "watercourse": names,
            "source_id": "era5-land",
            "source_type": "reanalysis",
            "spatial_assignment": "nearest cell to catchment centroid",
            "timezone_verified": True,
            "units_verified": True,
        }
    ).to_csv(interim / "event_study_weather_sources.csv", index=False)


def test_complete_synthetic_inputs_pass_every_binding_gate(tmp_path, monkeypatch):
    pytest.importorskip("geopandas")
    write_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    table = GATES.audit()

    binding = table[table.binding]
    assert binding.status.eq("PASS").all(), binding[binding.status.ne("PASS")].to_string()
    assert GATES.write_report(table)


def test_watercourse_breadth_is_a_nonbinding_information_benchmark(tmp_path, monkeypatch):
    pytest.importorskip("geopandas")
    write_fixture(tmp_path, n_units=4)
    monkeypatch.chdir(tmp_path)

    table = GATES.audit().set_index("gate")

    assert table.loc["Independent natural watercourses (breadth benchmark)", "status"] == "REVIEW"
    assert not table.loc["Independent natural watercourses (breadth benchmark)", "binding"]
    assert GATES.write_report(table.reset_index())
