"""Country filtering, prior-year context and radar completeness must be explicit."""

import importlib.util
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cross_border_completion", ROOT / "scripts/84_complete_cross_border_analogues.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def sample():
    return pd.DataFrame(
        {
            "event_id": ["nl", "de", "q", "future"],
            "storm_id": ["n", "d", "q", "f"],
            "onset_utc": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-10", "2020-02-01"], utc=True
            ),
            "complete_scoring_sample": True,
            "measurement_concern": False,
            "watercourse": "Wurm",
            "physical_river_group": "Wurm/Worm",
            "country": ["NL", "DE", "DE", "NL"],
            "outcome_peak_over_p99_72h": [1.0, 2.0, 3.0, 4.0],
        }
    )


def test_country_filters_do_not_change_default_or_leak_future():
    s = sample()
    v = pd.DataFrame([0.0, 1.0, 0.1, 0.05], index=s.event_id)
    kwargs = dict(
        top_k=5,
        min_candidates=1,
        min_candidate_storms=1,
        allow_short_archive=True,
        representation_vectors=v,
    )
    _, default = M.B.retrieve_prior_analogues(s, **kwargs)
    _, pooled = M.B.retrieve_prior_analogues(s, **kwargs, donor_country="pooled")
    pd.testing.assert_frame_equal(default, pooled)
    for policy, expected in [("domestic", ["de"]), ("foreign", ["nl"])]:
        _, d = M.B.retrieve_prior_analogues(s, **kwargs, donor_country=policy)
        assert d[d.query_event_id.eq("q")].analogue_event_id.tolist() == expected
    scores, _ = M.B.retrieve_prior_analogues(
        s, **kwargs, donor_country="domestic", exclude_same_river=True
    )
    assert scores.empty  # Two German stations are one physical river, not two.
    with pytest.raises(ValueError, match="mapped countries"):
        M.B.retrieve_prior_analogues(s.drop(columns="country"), **kwargs, donor_country="foreign")


def test_context_maps_provider_id_and_uses_only_prior_year():
    s = pd.DataFrame(
        {
            "event_id": ["a", "b"],
            "gauge": ["2828300000200", "2828900000200"],
            "onset_utc": pd.to_datetime(["2018-01-01", "2017-01-01"], utc=True),
        }
    )
    years = pd.DataFrame(
        {
            "gauge": ["herzogenrath_1", "randerath"],
            "embedding_year": [2017, 2017],
            "catchment_area_km2": [95.0, 299.0],
            **{f"A{i:02d}": [1.0, 2.0] for i in range(64)},
        }
    )
    joined = M.join_context(s, years)
    assert joined.context_gauge.tolist() == ["herzogenrath_1", "randerath"]
    assert joined.embedding_year.tolist() == [2017, 2016]
    assert joined.context_available.tolist() == [True, False]


def test_radar_intersection_rejects_partial_coverage_and_missing_weighted_cells():
    m = {"crop_bounds_m": [0, 0, 2, 1], "cell_m": 1, "crs": "EPSG:3035"}
    g = gpd.GeoDataFrame({"gauge": ["g"]}, geometry=[box(0, 0, 1, 1)], crs=m["crs"])
    w = M.radar_weights(g, m)
    assert M.weighted_rain(np.array([[[10, -1]]]), w)[0, 0] == 1.0
    assert np.isnan(M.weighted_rain(np.array([[[-1, 10]]]), w)[0, 0])
    g.geometry = [box(0, 0, 3, 1)]
    with pytest.raises(ValueError, match="outside held crop"):
        M.radar_weights(g, m)


def test_rain_history_requires_all_512_hours_and_never_uses_future():
    dates = pd.date_range("2019-12-20", periods=600, freq="h", tz="UTC")
    onset = dates[511]
    s = pd.DataFrame(
        {
            "event_id": ["a"],
            "gauge": ["2828300000200"],
            "country": ["DE"],
            "onset_utc": [onset],
            "complete_scoring_sample": [True],
        }
    )
    rain = pd.DataFrame({"herzogenrath_1": 1.0}, index=dates)
    a = M.add_rain_signatures(s, rain)
    assert a.rain_sum_24h_mm.iloc[0] == 24 and a.complete_scoring_sample.iloc[0]
    rain.loc[dates[512] :] = 900.0
    pd.testing.assert_frame_equal(a, M.add_rain_signatures(s, rain))
    rain.loc[dates[0]] = np.nan
    b = M.add_rain_signatures(s, rain)
    assert not b.complete_scoring_sample.iloc[0] and b.rain_sum_24h_mm.iloc[0] == 24


def test_paired_archive_effect_uses_same_queries_and_optional_equal_counts():
    a = pd.DataFrame(
        {
            "query_event_id": ["x", "y"],
            "query_storm_id": ["g", "h"],
            "query_onset_utc": ["2020-01-01", "2020-02-01"],
            "actual_donor_count": [5, 2],
            "error": [2.0, 3.0],
        }
    )
    b = pd.DataFrame(
        {
            "query_event_id": ["x", "y", "z"],
            "actual_donor_count": [5, 5, 5],
            "error": [1.0, 1.0, 0.0],
        }
    )
    p = M.paired_differences(a, b, "error", True)
    assert p.query_event_id.tolist() == ["x"] and p.difference.tolist() == [-1.0]
    assert M.paired_differences(a, b, "error", False).query_event_id.tolist() == ["x", "y"]
