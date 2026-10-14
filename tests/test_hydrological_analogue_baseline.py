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


def test_outcome_label_excludes_assessment_cutoff_hour():
    index = pd.DataFrame(
        [
            {
                "event_id": "event-1",
                "storm_id": "storm-1",
                "gauge": "g1",
                "watercourse": "river",
                "onset_utc": "2021-01-01T00:00:00Z",
                "p99_m3s": 10.0,
                "measurement_concern": False,
                "primary_usable": True,
                "history_discharge_fraction": 1.0,
                "history_rainfall_fraction": 1.0,
                "history_weather_fraction": 1.0,
                "outcome_discharge_fraction": 1.0,
            }
        ]
    )
    windows = pd.DataFrame(
        {
            "event_id": ["event-1"] * 5,
            "relative_hour": [-24, -6, 0, 1, 2],
            "target_discharge_m3s": [5.0, 8.0, 30.0, 12.0, 11.0],
            "catchment_rainfall_mm": [0.0] * 5,
        }
    )
    signature = MODULE.build_signatures(index, windows).iloc[0]
    assert signature.outcome_peak_over_p99_72h == 1.2
    assert signature.outcome_time_to_peak_h == 1


def test_retrieval_uses_only_prior_events_from_other_storms():
    event_index = pd.read_csv(
        ROOT / "results/basin_ai_event_library/event_index.csv",
        parse_dates=["onset_utc"],
    )
    windows = pd.read_parquet(ROOT / "results/basin_ai_event_library/event_windows.parquet")
    signatures = MODULE.build_signatures(event_index, windows)
    assert signatures.common_representation_sample.sum() == 570
    assert signatures.complete_scoring_sample.sum() == 558
    predictions, neighbors = MODULE.retrieve_prior_analogues(signatures, top_k=3, min_candidates=10)
    assert len(predictions) > 0
    assert len(neighbors) == 3 * len(predictions)
    assert neighbors.analogue_onset_utc.lt(neighbors.query_onset_utc).all()
    assert (
        neighbors.analogue_onset_utc.add(pd.Timedelta(hours=72)).le(neighbors.query_onset_utc).all()
    )
    assert neighbors.analogue_storm_id.ne(neighbors.query_storm_id).all()
    assert neighbors.groupby("query_event_id").analogue_storm_id.nunique().eq(3).all()
    assert predictions.candidate_count.ge(10).all()
    assert predictions.candidate_storm_count.ge(3).all()
    common_ids = set(signatures.loc[signatures.common_representation_sample, "event_id"])
    scoring_ids = set(signatures.loc[signatures.complete_scoring_sample, "event_id"])
    assert set(predictions.query_event_id).issubset(common_ids)
    assert set(neighbors.analogue_event_id).issubset(common_ids)
    assert set(predictions.query_event_id).issubset(scoring_ids)
    assert set(neighbors.analogue_event_id).issubset(scoring_ids)


def test_measurement_concern_sensitivity_excludes_flagged_queries_and_donors():
    event_index = pd.read_csv(
        ROOT / "results/basin_ai_event_library/event_index.csv",
        parse_dates=["onset_utc"],
    )
    windows = pd.read_parquet(ROOT / "results/basin_ai_event_library/event_windows.parquet")
    signatures = MODULE.build_signatures(event_index, windows)
    flagged_ids = set(signatures.loc[signatures.measurement_concern, "event_id"])
    predictions, neighbors = MODULE.retrieve_prior_analogues(
        signatures, top_k=3, min_candidates=10, exclude_measurement_concerns=True
    )
    assert predictions.query_event_id.isin(flagged_ids).sum() == 0
    assert neighbors.analogue_event_id.isin(flagged_ids).sum() == 0


def test_prior_storm_selection_waits_for_known_outcomes_and_deduplicates_storms():
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
                "watercourse": "test_river",
                "onset_utc": pd.Timestamp(onset),
                "complete_scoring_sample": True,
                "measurement_concern": False,
                "outcome_peak_over_p99_72h": value,
                **dict.fromkeys(MODULE.FEATURE_COLUMNS, value),
            }
        )
    predictions, neighbors = MODULE.retrieve_prior_analogues(
        pd.DataFrame(rows), top_k=2, min_candidates=2
    )
    selected = neighbors.loc[neighbors.query_event_id.eq("query")]
    assert len(selected) == 2
    assert set(selected.analogue_event_id) == {"b", "c"}
    assert selected.analogue_storm_id.nunique() == 2
    assert "query" in set(predictions.query_event_id)


def test_cross_river_filter_excludes_both_national_sides_of_one_river():
    rows = []
    for i, (eid, river) in enumerate(
        [
            ("de_wurm", "Wurm/Worm"),
            ("nl_worm", "Wurm/Worm"),
            ("geul", "Geul"),
            ("gulp", "Gulp"),
            ("query", "Wurm/Worm"),
        ]
    ):
        rows.append(
            {
                "event_id": eid,
                "physical_river_group": river,
                "watercourse": river,
                "storm_id": f"s{i}",
                "onset_utc": pd.Timestamp("2020-01-01", tz="UTC") + pd.Timedelta(days=4 * i),
                "complete_scoring_sample": True,
                "measurement_concern": False,
                "outcome_peak_over_p99_72h": 1.0,
                **dict.fromkeys(MODULE.FEATURE_COLUMNS, 1.0),
            }
        )
    frame = pd.DataFrame(rows)
    _, neighbors = MODULE.retrieve_prior_analogues(
        frame, top_k=2, min_candidates=2, exclude_same_river=True
    )
    selected = neighbors.loc[neighbors.query_event_id.eq("query")]
    assert set(selected.analogue_event_id) == {"geul", "gulp"}
    scores, _ = MODULE.retrieve_prior_analogues(
        frame, top_k=1, min_candidates=2, exclude_same_river=True, min_candidate_storms=3
    )
    assert "query" not in set(scores.query_event_id)
