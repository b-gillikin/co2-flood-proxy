"""Short-archive retrieval stays chronological; phase evidence is verification-only."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "expanded", ROOT / "scripts/81_run_expanded_event_analogues.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_short_archive_uses_available_distinct_groups_without_future_leakage():
    sample = pd.DataFrame(
        {
            "event_id": ["a", "b", "q", "future"],
            "storm_id": ["a", "a", "q", "future"],
            "onset_utc": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-10", "2020-02-01"], utc=True
            ),
            "complete_scoring_sample": True,
            "measurement_concern": False,
            "watercourse": "Wurm",
            "outcome_peak_over_p99_72h": [1.0, 3.0, 2.0, 9.0],
        }
    )
    vectors = pd.DataFrame([0.0, 1.0, 0.1, 0.2], index=sample.event_id)
    args = dict(top_k=10, min_candidates=1, min_candidate_storms=1, representation_vectors=vectors)
    strict, _ = M.B.retrieve_prior_analogues(sample, **args)
    assert strict.empty
    scores, donors = M.B.retrieve_prior_analogues(sample, **args, allow_short_archive=True)
    selected = donors[donors.query_event_id.eq("q")]
    assert selected.analogue_event_id.tolist() == ["a"]
    assert scores.set_index("query_event_id").loc["q", "candidate_storm_count"] == 1
    assert "a" not in scores.query_event_id.tolist()
    changed = sample.copy()
    changed.loc[changed.event_id.eq("q"), "outcome_peak_over_p99_72h"] = 200.0
    _, reranked = M.B.retrieve_prior_analogues(changed, **args, allow_short_archive=True)
    pd.testing.assert_frame_equal(selected, reranked[reranked.query_event_id.eq("q")])


def test_phase_estimates_use_donor_responses_not_query_outcomes():
    donor = np.array([np.ones(72) * 2.0, np.ones(72) * 0.5])
    a = M.phase_evidence(np.ones(72) * 3.0, donor, 1.1)
    b = M.phase_evidence(np.ones(72) * 0.1, donor, 1.1)
    assert a["estimated_high_water_hours"] == b["estimated_high_water_hours"] == 36
    assert a["donor_share_ending_above_p99"] == b["donor_share_ending_above_p99"] == 0.5
    assert a["observed_high_water_hours"] == 72 and b["observed_high_water_hours"] == 0
    assert a["donor_share_peak_after_first_hour"] == 0
