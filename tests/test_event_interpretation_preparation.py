"""References have explicit weights, cutoff-only inputs and honest timing."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare", ROOT / "scripts/80_prepare_event_interpretation.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_balanced_median_matches_ordinary_median_for_singleton_groups():
    for values in [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0, 4.0]]:
        assert M.group_balanced_median(values, np.arange(len(values))) == np.median(values)


def test_one_multigauge_group_does_not_overweight_balanced_reference():
    values = [1.0] * 7 + [9.0]
    groups = ["a"] * 7 + ["b"]
    assert np.median(values) == 1
    assert M.group_balanced_median(values, groups) == 5
    assert M.group_balanced_median([1.0] * 14 + [9.0], ["a"] * 14 + ["b"]) == 5
    assert np.isnan(M.group_balanced_median([], []))


def test_persistence_preserves_cutoff_and_does_not_invent_peak_timing():
    response = np.linspace(2.0, 0.2, 72)
    result = M.persistence_reference(1.5, response)
    assert result["persistence_peak_estimate"] == 1.5
    assert result["persistence_peak_absolute_error"] == 0.5
    assert result["persistence_peak_timing_defined"] is False
    assert result["persistence_high_water_hours_estimate"] == 72
    altered = response.copy()
    altered[50] = 20
    assert M.persistence_reference(1.5, altered)["persistence_peak_estimate"] == 1.5


def test_short_and_empty_archives_are_retained_without_fake_medians():
    times = pd.date_range("2020-01-01", periods=3, freq="4D", tz="UTC")
    sample = pd.DataFrame(
        {
            "event_id": ["a", "b", "c"],
            "storm_id": ["s1", "s2", "s3"],
            "onset_utc": times,
            "complete_scoring_sample": True,
            "measurement_concern": [False, True, False],
            "outcome_peak_over_p99_72h": [1.0, 2.0, 3.0],
        }
    )
    inventory = pd.DataFrame(
        {
            "event_id": ["a", "b", "c"],
            "country": "NL",
            "physical_river_group": ["Geul", "Gulp", "Geul"],
            "persistence_peak_absolute_error": [0.1, 0.2, 0.3],
        }
    )
    rows = M.candidate_references({"q_only": sample}, inventory)
    main = rows[rows.analysis.eq("main") & rows.scenario.eq("all_rivers")].set_index(
        "query_event_id"
    )
    assert len(main) == 3
    assert main.loc["a", "candidate_groups"] == 0
    assert np.isnan(main.loc["a", "group_balanced_median_peak"])
    assert main.loc["b", "archive_status"] == "short"
    assert not main.matches_fixed_k_comparison.any()
    sensitivity = rows[
        rows.analysis.eq("quality_sensitivity") & rows.scenario.eq("all_rivers")
    ].set_index("query_event_id")
    assert sensitivity.loc["b", "query_excluded_by_quality_sensitivity"]
    assert sensitivity.loc["c", "candidate_groups"] == 1
