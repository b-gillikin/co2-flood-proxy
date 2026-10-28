"""Research estimands checked against explicit resampled calendars and labels."""

import numpy as np
import pytest

from src.analogue_bootstrap import draw_counts
from src.scarcity_review import joint_summary, severity_labels


def test_mask_mean_year_bootstrap_matches_manual_joint_calendar_resampling():
    years = np.array([2020, 2021, 2022])
    x = np.arange(12, dtype=float).reshape(2, 2, 3)
    result = joint_summary(x, years, random_masks=True, draws=199, seed=9)
    yc, mc = draw_counts(3, 199, 9), draw_counts(2, 199, 100)
    manual = []
    for year_counts, mask_counts in zip(yc, mc, strict=True):
        values = []
        for gi in range(2):
            values.append(
                sum(
                    x[r, gi, t] * mask_counts[r] * year_counts[t]
                    for r in range(2)
                    for t in range(3)
                )
                / (2 * 3)
            )
        manual.append(np.mean(values))
    assert result["estimate"] == pytest.approx(x.mean())
    np.testing.assert_allclose(
        [result["lower"], result["upper"]], np.quantile(manual, [0.025, 0.975])
    )
    assert result["case_storms"] == 3 and result["gauges"] == 2


def test_exact_network_replication_does_not_artificially_shrink_uncertainty():
    x = np.array([[[1.0, 2, 6], [2, 3, 7]]])
    original = joint_summary(x, [2020, 2021, 2022], random_masks=False, draws=199)
    repeated = joint_summary(
        np.repeat(x, 70, axis=0), [2020, 2021, 2022], random_masks=False, draws=199
    )
    for key in ["estimate", "lower", "upper", "case_storms", "gauge_storms"]:
        assert original[key] == repeated[key]


def test_sites_have_equal_mass_despite_different_observation_counts():
    x = np.array([[[0.0, 0, 0], [9, np.nan, np.nan]]])
    assert joint_summary(x, [2020, 2021, 2022], random_masks=False, draws=0)["estimate"] == 4.5


def test_undefined_bootstrap_draws_are_reported_without_finite_only_interval():
    x = np.array([[[1.0, 2, np.nan, np.nan, np.nan]]])
    result = joint_summary(x, np.arange(2020, 2025), random_masks=False, draws=999)
    assert 0 < result["finite_draws"] < 999
    assert np.isnan(result["lower"]) and np.isnan(result["upper"])


def test_hindsight_high_water_unknowns_and_net_direction_stay_distinct():
    y = np.array([[1.0, 5, 2], [1, 2, 1], [1, 9, 3], [1, 9, 3]])
    thresholds = np.full_like(y, 4.0)
    thresholds[-1] = np.nan
    high, phase = severity_labels(y, thresholds, np.array([0.0, 0, 4, 0]))
    assert high.tolist() == [1, 0, 1, -1]
    assert phase.tolist() == [
        "rising_high_water",
        "not_high_water",
        "falling_high_water",
        "undefined",
    ]
