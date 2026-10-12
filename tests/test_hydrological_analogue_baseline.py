import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/65_hydrological_analogue_baseline.py"
SPEC = importlib.util.spec_from_file_location("analogue_baseline", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_features_are_assessment_history_and_labels_are_explicit_outcomes():
    assert all(not column.startswith("outcome_") for column in MODULE.FEATURE_COLUMNS)


def test_retrieval_uses_only_prior_events_from_other_storms():
    event_index = pd.read_csv(
        ROOT / "results/basin_ai_event_library/event_index.csv",
        parse_dates=["onset_utc"],
    )
    windows = pd.read_parquet(ROOT / "results/basin_ai_event_library/event_windows.parquet")
    signatures = MODULE.build_signatures(event_index, windows)
    predictions, neighbors = MODULE.retrieve_prior_analogues(signatures, top_k=3, min_candidates=10)
    assert len(predictions) > 0
    assert len(neighbors) == 3 * len(predictions)
    assert neighbors.analogue_onset_utc.lt(neighbors.query_onset_utc).all()
    assert neighbors.analogue_storm_id.ne(neighbors.query_storm_id).all()
