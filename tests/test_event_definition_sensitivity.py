"""One-factor event selection, censoring and fixed verification-clock checks."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "definition_check", ROOT / "scripts/88_event_definition_sensitivity.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def example():
    times = pd.date_range("2020-01-01", periods=200, freq="h", tz="UTC")
    q = pd.Series(1.0, index=times)
    q.iloc[[10, 100, 190]] = [5, 20, 15]
    eras = pd.Series("a", index=times, dtype="string")
    table = pd.DataFrame([dict(era_id="a", domain_min_m3s=0, domain_max_m3s=100)])
    return q, eras, table


def test_percentile_changes_event_selection_without_rescaling_discharge():
    q, era, table = example()
    a, threshold99, scale99, _, _ = M.episode_definition(q, era, table, 0.99, 72)
    b, threshold95, scale95, _, _ = M.episode_definition(q, era, table, 0.95, 72)
    assert len(a) == 2 and len(b) == 3
    assert threshold95.lt(threshold99).all()
    pd.testing.assert_series_equal(scale95, scale99)


def test_longer_separation_changes_linkage_not_threshold_or_first_onset():
    q, era, table = example()
    a, threshold, scale, _, _ = M.episode_definition(q, era, table, 0.99, 72)
    b, other_threshold, other_scale, _, _ = M.episode_definition(q, era, table, 0.99, 120)
    assert len(a) == 2 and len(b) == 1
    assert a.onset_utc.iloc[0] == b.onset_utc.iloc[0]
    assert b.n_crossings.iloc[0] == 2
    pd.testing.assert_series_equal(threshold, other_threshold)
    pd.testing.assert_series_equal(scale, other_scale)


def test_censored_first_crossing_does_not_become_known_when_linked():
    q, era, table = example()
    q[:] = 1
    q.iloc[[0, 100]] = 20
    episodes, *_ = M.episode_definition(q, era, table, 0.99, 120)
    assert len(episodes) == 1 and episodes.onset_censored.iloc[0]


def test_linkage_boundary_is_inclusive_and_chains_can_exceed_the_interval():
    q, era, table = example()
    q[:] = 1
    q.iloc[[10, 82, 154]] = 20
    episodes = M.R.episode_table(q, 2, 72, eras=era)
    assert len(episodes) == 1 and episodes.chain_span_hours.iloc[0] == 144
    q.iloc[154] = 1
    q.iloc[155] = 20
    assert len(M.R.episode_table(q, 2, 72, eras=era)) == 2


def test_candidate_response_remains_72_hours_with_120_hour_linkage():
    times = pd.date_range("2020-01-01", periods=1000, freq="h", tz="UTC")
    q = pd.Series(1.0, index=times)
    q.iloc[[600, 690, 780]] = 20
    era = pd.Series("a", index=times, dtype="string")
    table = pd.DataFrame([dict(era_id="a", domain_min_m3s=0, domain_max_m3s=100)])
    source = dict(
        gauge="test",
        country="NL",
        watercourse="test",
        q=q,
        rain=pd.Series(0.0, index=times),
        eras=era,
        literal=era,
        table=table,
        source_note="documented",
    )
    index, windows, census, _ = M.build_library([source], 0.99, 120)
    assert len(index) == len(census) == 1
    assert windows.relative_hour.tolist() == list(range(-511, 73))
    assert windows[windows.relative_hour.gt(0)].target_discharge_m3s.eq(1).all()
    assert index.last_crossing_utc.iloc[0] == times[780]
    assert index.onset_utc.iloc[0] == times[600]


def test_archive_reference_hand_calculation_has_equal_group_not_event_weight():
    query = np.ones(72)
    donors = np.array([np.ones(72), np.ones(72), np.full(72, 4)])
    result, curve = M.INFO.archive_evidence(query, donors, ["a", "a", "b"])
    np.testing.assert_allclose(curve, 2.5)
    assert result["archive_curve_level_rmse"] == 1.5
    assert result["archive_mean_peak_absolute_error"] == 1.5


def test_independent_pair_metric_arithmetic():
    spec = importlib.util.spec_from_file_location(
        "definition_audit_test", ROOT / "scripts/89_audit_event_definition_sensitivity.py"
    )
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    q = np.array([np.ones(72)])
    a = np.array([np.full(72, 2.0)])
    result = audit.direct_pairs(q, a)
    assert result["level_rmse_p99"][0] == 1
    assert result["peak_scaled_shape_rmse"][0] == 0
    assert result["high_water_duration_difference_h"][0] == 0
    assert result["excess_area_difference_p99_h"][0] == 72


def test_exact_row_cache_matches_original_with_duplicates_and_robust_state():
    ids = pd.Index(["a", "b", "c", "query", "future"], name="event_id")
    temporal = pd.DataFrame(
        [
            [1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0],
            [5.0, 6.0, 8.0],
            [3.0, 4.0, 9.0],
            [999.0, 777.0, -800.0],
        ],
        index=ids,
    )
    state = pd.DataFrame(
        [[1.0, 1.0], [2.0, 1.0], [3.0, 1.0], [4.0, 2.0], [999.0, -888.0]], index=ids
    )
    blocks = dict(temporal=temporal, state=state)
    candidates = pd.DataFrame({"event_id": ["a", "b", "c"]}, index=[8, 2, 15])
    query = type("Query", (), {"event_id": "query"})()
    original = M.B.block_distances(candidates, query, blocks, ("state",))
    cache = M.ExactRowCache()
    actual = cache(candidates, query, blocks, ("state",))
    pd.testing.assert_series_equal(actual[0], original[0], check_exact=True)
    pd.testing.assert_frame_equal(actual[1], original[1], check_exact=True)
    # Future outliers and additional duplicate rows never affect a prior scale.
    smaller = {k: v.loc[["a", "b", "c", "query"]].copy() for k, v in blocks.items()}
    other = cache(candidates, query, smaller, ("state",))
    pd.testing.assert_frame_equal(actual[1], other[1], check_exact=True)


def test_independent_set_reconstruction_preserves_key_names():
    spec = importlib.util.spec_from_file_location(
        "definition_set_audit_test", ROOT / "scripts/89_audit_event_definition_sensitivity.py"
    )
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    key = dict(
        cohort="q_only",
        scenario="all_rivers",
        analysis="main",
        policy="pooled",
        arm="raw_state",
        query_event_id="q",
    )
    response = pd.DataFrame([np.ones(72), np.full(72, 2.0)], index=["q", "a"])
    metrics = {
        k: float(v[0])
        for k, v in audit.direct_pairs(
            np.array([np.ones(72)]), np.array([np.full(72, 2.0)])
        ).items()
    }
    donors = pd.DataFrame([{**key, "analogue_event_id": "a", "rank": 1, **metrics}])
    rows = pd.DataFrame(
        [
            {
                **key,
                "target_k": k,
                "actual_donor_count": 1,
                "ensemble_curve_level_rmse": 1.0,
                "mean_donor_peak_absolute_error": 1.0,
                "estimated_high_water_hours": 72.0,
                "duration_estimate_absolute_error_h": 0.0,
                "final_24h_level_absolute_error": 1.0,
                **{"mean_" + field: value for field, value in metrics.items()},
            }
            for k in [5, 10]
        ]
    )
    assert audit.selected_set_check(donors, rows, response) == 0


def test_episode_mapping_reports_earlier_start_without_inventing_lead_time():
    spec = importlib.util.spec_from_file_location(
        "definition_mapping_test", ROOT / "scripts/89_audit_event_definition_sensitivity.py"
    )
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    baseline = pd.DataFrame(
        [
            dict(event_id="b1", gauge="g", country="NL", onset_utc="2020-01-02T00:00:00Z"),
            dict(event_id="b2", gauge="g", country="NL", onset_utc="2020-01-05T00:00:00Z"),
        ]
    )
    alternative = pd.DataFrame(
        [dict(event_id="a", gauge="g", onset_utc="2020-01-01T00:00:00Z", onset_censored=False)]
    )
    alternative.loc[1] = dict(
        event_id="future", gauge="g", onset_utc="2020-02-01T00:00:00Z", onset_censored=False
    )
    result = audit.map_catalogues(baseline, alternative)
    assert result.alternative_event_id.tolist() == ["a", "a"]
    assert result.assessment_start_shift_h.tolist() == [24, 96]
    assert result.response_window_overlap_h.tolist() == [48, 0]
