"""Archive weighting and case selection preserve their stated information boundaries."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "information", ROOT / "scripts/82_review_analogue_information.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_generic_archive_balances_groups_not_gauge_counts():
    q = np.ones(72) * 2
    a = np.array([np.ones(72), np.ones(72) * 3])
    evidence, curve = M.archive_evidence(q, a, ["a", "b"])
    repeated = np.vstack([a[:1]] * 7 + [a[1:]])
    extra, extra_curve = M.archive_evidence(q, repeated, ["a"] * 7 + ["b"])
    np.testing.assert_allclose(curve, extra_curve)
    assert evidence["archive_curve_level_rmse"] == 0
    for key in evidence:
        np.testing.assert_allclose(evidence[key], extra[key], atol=1e-12)


def test_query_outcome_only_scores_archive_curve():
    a = np.array([np.linspace(2, 0.2, 72), np.linspace(4, 0.4, 72)])
    _, curve = M.archive_evidence(np.ones(72), a, ["a", "b"])
    _, other = M.archive_evidence(np.ones(72) * 9, a, ["a", "b"])
    np.testing.assert_array_equal(curve, other)


def test_sentinel_selection_ignores_responses_and_errors():
    rows = pd.DataFrame(
        {
            "query_event_id": list("abcdef"),
            "query_river": "Wurm/Worm",
            "query_onset_utc": pd.date_range("2020-01-01", periods=6, tz="UTC"),
            "actual_donor_count": 5,
            "curve_spread": [1.0, 2.0, 3.0, 6.0, 5.0, 4.0],
            "observed_peak_over_p99_72h": np.arange(6.0),
            "ensemble_curve_level_rmse": np.arange(6.0),
        }
    )
    expected = M.select_sentinels(rows)
    altered = rows.copy()
    altered["observed_peak_over_p99_72h"] = np.arange(6.0)[::-1] * 100
    altered["ensemble_curve_level_rmse"] = 99
    pd.testing.assert_frame_equal(expected, M.select_sentinels(altered))
    assert len(expected) == 4 and expected.query_event_id.nunique() == 4
    assert "d" in expected.query_event_id.tolist()


def test_sparse_illustration_availability_does_not_stop_census_work():
    rows = pd.DataFrame(
        {
            "query_event_id": ["a", "b"],
            "query_river": "Wurm/Worm",
            "query_onset_utc": pd.date_range("2020-01-01", periods=2, tz="UTC"),
            "actual_donor_count": 5,
            "curve_spread": [1.0, 2.0],
        }
    )
    selected = M.select_sentinels(rows)
    assert set(selected.query_event_id) == {"a", "b"}
