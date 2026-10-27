"""Reporting must preserve signs, comparison populations and uncertainty ambiguity."""

import numpy as np
import pandas as pd
import pytest

from src.eo_findings import KEYS, collapse_intervals, reverse_contrast


def intervals(storm=(-3.0, -1.0), year=(-4.0, -0.5)):
    key = dict.fromkeys(KEYS, "fixed")
    key.update(target_k=5, reference="reference", challenger="challenger")
    return pd.DataFrame(
        [
            {
                **key,
                "resampling_unit": unit,
                "difference": -2.0,
                "lower": lo,
                "upper": hi,
                "query_count": 12,
                "cluster_count": n,
            }
            for unit, (lo, hi), n in [("query_storm_id", storm, 8), ("storm_year", year, 3)]
        ]
    )


@pytest.mark.parametrize(
    "year, expected",
    [
        ((-4.0, -0.5), "both_below_zero"),
        ((-4.0, 1.0), "resampling_sensitive"),
        ((np.nan, np.nan), "undefined"),
    ],
)
def test_nominal_views_keep_resampling_sensitivity_and_undefined_intervals(year, expected):
    f = collapse_intervals(intervals(year=year))
    assert f.nominal_interval_pattern.tolist() == [expected]
    assert f.query_count.iloc[0] == 12  # two uncertainty views do not double n


def test_intervals_containing_zero_are_not_labelled_equivalent():
    assert (
        collapse_intervals(intervals((-3, 1), (-4, 1))).nominal_interval_pattern.iloc[0]
        == "both_include_zero"
    )


def test_reversing_contrast_swaps_and_negates_bounds():
    f = intervals()
    g = reverse_contrast(f)
    assert (g.reference == "challenger").all()
    assert (g.difference == 2).all()
    np.testing.assert_array_equal(g.lower, -f.upper)
    np.testing.assert_array_equal(g.upper, -f.lower)
    assert collapse_intervals(g).nominal_interval_pattern.iloc[0] == "both_above_zero"


def test_different_cohorts_remain_different_and_duplicate_pairings_fail():
    f = intervals()
    g = f.assign(cohort="other_population")
    assert len(collapse_intervals(pd.concat([f, g]))) == 2
    with pytest.raises(ValueError, match="Duplicate"):
        collapse_intervals(pd.concat([f, f]))


def test_inconsistent_point_estimates_between_bootstraps_are_rejected():
    f = intervals()
    f.loc[1, "difference"] = -3
    with pytest.raises(ValueError, match="Point estimates differ"):
        collapse_intervals(f)
