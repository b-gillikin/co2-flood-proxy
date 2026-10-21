import numpy as np
import pandas as pd

from src.eo_coverage_review import coverage_issues, donor_support, membership_table


def test_missing_model_cannot_shrink_common_requirement():
    x = membership_table(["early", "later"], {"a": ["later"]}, ["a", "pending"])
    assert not x.common.any()
    assert x.a.sum() == 1


def test_common_population_and_separate_model_populations():
    x = membership_table(["a", "b", "c"], {"one": ["a", "b"], "two": ["b", "c"]}, ["one", "two"])
    assert x.loc[x.common, "event_id"].tolist() == ["b"]
    assert x.one.sum() == x.two.sum() == 2


def test_donor_rules_keep_storm_dependence_and_country_river_controls():
    x = pd.DataFrame(
        {
            "event_id": ["a", "b", "c", "d", "q"],
            "start_utc": pd.to_datetime(
                ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-05", "2020-01-06"], utc=True
            ),
            "storm_id": ["old", "old", "separate", "new", "query"],
            "country": ["DE", "DE", "NL", "DE", "NL"],
            "physical_river_group": ["A", "B", "A", "B", "A"],
            "measurement_concern": [True, False, False, False, False],
        }
    )
    q = donor_support(x).set_index("event_id").loc["q"]
    assert q.candidate_events == 3 and q.candidate_storms == 2
    q = donor_support(x, "other_rivers", "foreign", True).set_index("event_id").loc["q"]
    assert q.candidate_events == q.candidate_storms == 1
    assert donor_support(x).set_index("event_id").loc["a", "candidate_events"] == 0


def test_coverage_retains_partial_support_but_rejects_impossible_areas():
    x = pd.DataFrame(
        {
            "context_id": ["x"],
            "catchment_gauge": ["g"],
            "observed_mean_fraction": [0.02],
            "observed_min_fraction": [0.01],
            "observed_common_fraction": [0.0],
        }
    )
    assert coverage_issues(x) == []
    x["observed_common_fraction"] = 0.1
    assert "common_exceeds_minimum" in coverage_issues(x)
    x["observed_mean_fraction"] = np.nan
    assert "nonfinite_coverage" in coverage_issues(x)
