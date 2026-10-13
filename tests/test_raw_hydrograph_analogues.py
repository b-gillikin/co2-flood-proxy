import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "raw_hydrograph", ROOT / "scripts/69_raw_hydrograph_analogue_baseline.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_vectors_use_only_history_and_standardize_each_event_independently():
    hours = np.arange(-511, 73)
    q = np.arange(len(hours), dtype=float)
    windows = pd.DataFrame({"event_id": "a", "relative_hour": hours, "target_discharge_m3s": q})
    scaled = windows.assign(event_id="b", target_discharge_m3s=q * 20 + 300)
    data = pd.concat([windows, scaled], ignore_index=True)
    vectors, _ = MODULE.standardized_histories(pd.Series(["a", "b"]), data)
    np.testing.assert_allclose(vectors.loc["a"], vectors.loc["b"], atol=1e-12)
    np.testing.assert_allclose(vectors.mean(axis=1), 0, atol=1e-12)
    np.testing.assert_allclose(vectors.std(axis=1, ddof=0), 1)
    altered = data.copy()
    altered.loc[altered.relative_hour.gt(0), "target_discharge_m3s"] = 1e12
    after, _ = MODULE.standardized_histories(pd.Series(["a", "b"]), altered)
    pd.testing.assert_frame_equal(vectors, after)


def test_incomplete_history_is_not_padded_or_imputed():
    windows = pd.DataFrame(
        {
            "event_id": "a",
            "relative_hour": np.arange(-511, 1),
            "target_discharge_m3s": np.arange(512, dtype=float),
        }
    )
    with pytest.raises(ValueError):
        MODULE.standardized_histories(pd.Series(["a"]), windows.iloc[1:])
    windows.loc[1, "target_discharge_m3s"] = np.nan
    with pytest.raises(ValueError):
        MODULE.standardized_histories(pd.Series(["a"]), windows)


def test_vector_retrieval_keeps_shared_eligibility_and_distinct_prior_storms():
    rows = []
    for event_id, storm, onset, value in (
        ("a", "s1", "2020-01-01T00:00:00Z", 1.0),
        ("b", "s1", "2020-01-01T01:00:00Z", 1.01),
        ("c", "s2", "2020-01-02T00:00:00Z", 2.0),
        ("d", "s3", "2020-01-04T00:00:00Z", 1.01),
        ("query", "s4", "2020-01-06T00:00:00Z", 1.01),
    ):
        rows.append(
            {
                "event_id": event_id,
                "storm_id": storm,
                "onset_utc": pd.Timestamp(onset),
                "watercourse": "river",
                "complete_scoring_sample": True,
                "measurement_concern": False,
                "outcome_peak_over_p99_72h": value,
                **dict.fromkeys(MODULE.BASELINE.FEATURE_COLUMNS, value),
            }
        )
    signatures = pd.DataFrame(rows)
    vectors = pd.DataFrame({"q": [1.0, 1.01, 2.0, 1.01, 1.01]}, index=signatures.event_id)
    conventional, _ = MODULE.BASELINE.retrieve_prior_analogues(
        signatures, top_k=2, min_candidates=2
    )
    raw, neighbors = MODULE.BASELINE.retrieve_prior_analogues(
        signatures, top_k=2, min_candidates=2, representation_vectors=vectors
    )
    MODULE.paired_comparison(conventional, raw)
    selected = neighbors.loc[neighbors.query_event_id.eq("query")]
    assert set(selected.analogue_event_id) == {"b", "c"}
    assert selected.analogue_storm_id.nunique() == 2
