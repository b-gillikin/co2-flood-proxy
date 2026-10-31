import numpy as np
import pytest

from src.eo_supporting_controls import antecedent_state, saved_combined_profiles


def test_no_issue_hour_or_future_state_enters_control():
    values, age = antecedent_state(
        ["2020-01-01T00:00Z", "2020-01-01T01:00Z"],
        [[0.1, 0], [99, 99]], ["2020-01-01T01:00Z"],
    )
    np.testing.assert_array_equal(values, [[0.1, 0]])
    np.testing.assert_array_equal(age, [1])


def test_missing_hour_is_not_filled_and_zero_snow_survives():
    values, age = antecedent_state(
        ["2020-01-01T00:00Z"], [[0.1, 0]],
        ["2020-01-01T00:30Z", "2020-01-01T02:00Z"],
    )
    np.testing.assert_array_equal(values[0], [0.1, 0])
    assert np.isnan(values[1]).all() and np.isnan(age[1])


def test_source_clock_must_be_unique():
    with pytest.raises(ValueError):
        antecedent_state(["2020-01-01", "2020-01-01"], [[1], [2]], [])


def test_combined_definitions_preserved_exactly():
    groups = [dict(name=name, subsets=[[0, 2, 4, 6]], phases=[2]) for name in
              ["network4_schedule6_no_maas", "network4_block12_50pct_no_maas"]]
    assert saved_combined_profiles(groups) == groups
    with pytest.raises(ValueError):
        saved_combined_profiles(groups[:1])
