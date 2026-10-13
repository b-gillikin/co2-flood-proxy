"""Scientific checks for a complete, multidimensional analogue review."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "census", ROOT / "scripts/74_review_analogue_census.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_equal_peaks_do_not_hide_a_shifted_response():
    query = np.ones(72) * 0.4
    query[9:12] = [1.3, 2, 1.3]
    donor = np.roll(query, 20)
    difference = MODULE.response_distances(query, donor[None, :]).iloc[0]
    assert difference.peak_time_difference_h == 20
    assert difference.peak_scaled_shape_rmse > 0
    assert difference.high_water_duration_difference_h == 0
    assert difference.excess_area_difference_p99_h == 0


def test_level_and_peak_scaled_shape_answer_different_questions():
    query = np.linspace(2, 0.2, 72)
    difference = MODULE.response_distances(query, (query * 3)[None, :]).iloc[0]
    assert difference.level_rmse_p99 > 1
    assert difference.peak_scaled_shape_rmse == pytest.approx(0, abs=1e-15)
    assert difference.high_water_duration_difference_h > 0


def test_already_receding_response_below_threshold_is_valid():
    response = np.linspace(0.9, 0.1, 72)[None, :]
    result = MODULE.response_signatures(response)
    assert result["peak_ratio"][0] == 0.9
    assert result["peak_time_h"][0] == 1
    assert result["high_water_duration_h"][0] == 0
    assert result["excess_area_p99_h"][0] == 0


def test_incomplete_response_cannot_acquire_exact_shape_score():
    response = np.ones((1, 72))
    response[0, 13] = np.nan
    with pytest.raises(ValueError, match="complete finite"):
        MODULE.response_signatures(response)


def test_repeated_gauges_do_not_overweight_a_reference_storm():
    weights = MODULE.storm_weights(["one", "many", "many", "many"])
    np.testing.assert_allclose(weights, [0.5, 1 / 6, 1 / 6, 1 / 6])
    assert np.average([4, -2, -2, -2], weights=weights) == pytest.approx(1)


def test_full_pool_percentiles_give_half_weight_to_ties():
    result = MODULE.weighted_percentiles([1, 1, 2, 4], [0.1, 0.2, 0.3, 0.4], [0, 1, 2, 3, 4, 5])
    np.testing.assert_allclose(result, [0, 0.15, 0.45, 0.6, 0.8, 1])
