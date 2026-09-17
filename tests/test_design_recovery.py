import numpy as np
import pandas as pd
import pytest

from src.design_recovery import (
    distances_km,
    hourly_presence,
    median_estimates,
    simulate_once,
    spatial_subset,
    stage_onsets,
)


def test_hourly_mask_uses_trailing_endpoints_and_does_not_fill_gaps():
    index = pd.date_range("2020-01-01", periods=9, freq="15min")
    mask = pd.DataFrame({"a": True}, index=index)
    mask.iloc[2] = False
    assert hourly_presence(mask).a.tolist() == [False, False, True]


def test_known_pair_median_slope_and_local_contrast():
    d = distances_km(np.array([50.0, 50.1, 50.4]), np.array([6.0, 6.2, 6.0]))
    x = np.log1p(d)
    panel = np.tile(0.5 - 0.25 * x, (8, 1, 1))
    assert np.allclose(median_estimates(panel, x), [0.5, -0.25])
    panel[:, 0, 1] = np.nan
    assert np.isclose(median_estimates(panel, x)[0], 0.5)
    assert np.isnan(median_estimates(panel, x)[1])


def test_geometry_selection_never_invents_additional_rivers():
    d = np.array([[0, 3, 1], [3, 0, 2], [1, 2, 0]])
    assert spatial_subset(d, 2).tolist() == [0, 1]
    with pytest.raises(ValueError):
        spatial_subset(d, 4)


def test_stage_crossing_cannot_span_gap_or_datum_change():
    index = pd.date_range("2020-01-01", periods=8, freq="h", tz="UTC")
    stage = pd.Series([0, 2, np.nan, 2, 0, 2, 0, 2], index=index)
    eras = pd.Series(["A"] * 5 + ["B"] * 3, index=index)
    result = stage_onsets(stage, eras, {"A": 1, "B": 1}, merge_hours=0)
    assert result.onset_utc.tolist() == [index[1], index[7]]


def test_storm_simulation_reproducible_and_unavailable_design_is_visible():
    d = np.array([[0, 1, 3], [1, 0, 2], [3, 2, 0]], dtype=float)
    availability = np.ones((25, 3, 3), dtype=bool)
    a = simulate_once(d, availability, -0.25, 0.7, np.random.default_rng(3), bootstrap=29)
    b = simulate_once(d, availability, -0.25, 0.7, np.random.default_rng(3), bootstrap=29)
    assert np.allclose(a[0], b[0]) and np.allclose(a[1], b[1])
    availability[:, 0, 1] = False
    estimate, ci, _ = simulate_once(d, availability, 0, 0.2, np.random.default_rng(3), bootstrap=29)
    assert np.isfinite(estimate[0]) and np.isnan(estimate[1])
    assert np.isnan(ci[:, 1]).all()
