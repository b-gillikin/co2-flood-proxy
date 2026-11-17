"""Acquisition support is explicit; missing coverage never silently becomes zero."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dise_regional_inputs import selected_mapping, spatial_table, weather_table


def test_selection_keeps_flagged_records_and_external_roles():
    f = pd.DataFrame(
        dict(
            gauge_id=["a", "b", "c"],
            resolved_role=[
                "regional_donor",
                "reserved_external",
                "local_connected_section_excluded",
            ],
            best_river_id=[1, 2, 3],
            reference_area_km2=[100, 200, 300],
            geometry_review_flag=[True, False, False],
        )
    )
    got = selected_mapping(f, ["regional_donor", "reserved_external"])
    assert got.gauge_id.tolist() == ["a", "b"] and bool(got.iloc[0].geometry_review_flag)
    with pytest.raises(ValueError):
        selected_mapping(pd.concat([f, f]), ["regional_donor"])


def test_weather_preserves_leap_calendar_missingness_and_mean_denominator():
    features = [
        dict(
            properties={
                "gauge": "a",
                "sampled_area_m2": 2,
                "20200101_rain": 8,
                "20200102_rain": None,
            }
        )
    ]
    got = weather_table(features, 2020, ["rain"], ["a"])
    assert len(got) == 366 and got.iloc[0].rain == 4 and np.isnan(got.iloc[1].rain)
    with pytest.raises(ValueError):
        weather_table(features, 2020, ["rain"], ["a", "b"])
    with pytest.raises(ValueError):
        weather_table(
            [dict(properties={"gauge": "a", "sampled_area_m2": 0})], 2020, ["rain"], ["a"]
        )


def test_embedding_support_stays_unknown_and_axes_share_support():
    feature = dict(
        properties={
            "gauge": "a",
            "geometry_sha256": "x",
            "A00_mean": None,
            "A01_mean": None,
            "A00_count": 0,
            "A01_count": 0,
        }
    )
    got = spatial_table([feature], ["a"], "alphaearth", ["A00", "A01"])
    assert got.coverage_status.iloc[0] == "no_valid_pixels" and pd.isna(got.A00.iloc[0])
    feature["properties"]["A01_count"] = 1
    with pytest.raises(ValueError):
        spatial_table([feature], ["a"], "alphaearth", ["A00", "A01"])


def test_attribute_common_support_and_duplicate_identity():
    feature = dict(properties={"gauge": "a", "geometry_sha256": "x", "area_m2": 2, "a_slope": 10})
    assert spatial_table([feature], ["a"], "attributes", ["a_slope"]).a_slope.iloc[0] == 5
    with pytest.raises(ValueError):
        spatial_table([feature, feature], ["a"], "attributes", ["a_slope"])
