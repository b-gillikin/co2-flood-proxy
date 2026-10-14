"""Cross-river response review must preserve prefix size and matched inputs."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cross", ROOT / "scripts/78_cross_river_analogue_checks.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_prefix_peak_score_and_spread_use_selected_donors_only():
    metadata = pd.DataFrame(
        {
            "event_id": ["q", "a", "b"],
            "physical_river_group": ["Wurm/Worm", "Geul", "Gulp"],
            "country": ["DE", "NL", "NL"],
            "measurement_concern": [False] * 3,
        }
    ).set_index("event_id")
    response = pd.DataFrame(
        np.array([np.ones(72) * 2, np.ones(72), np.ones(72) * 3]), index=metadata.index
    )
    scores = pd.DataFrame(
        {
            "query_event_id": ["q"],
            "analogue_prediction": [99.0],
            "analogue_absolute_error": [99.0],
            "query_storm_id": ["sq"],
        }
    )
    donors = pd.DataFrame(
        {"query_event_id": ["q", "q"], "analogue_event_id": ["a", "b"], "rank": [1, 2]}
    )
    one, _ = M.assess(scores, donors.head(1), response, metadata)
    two, pairs = M.assess(scores, donors, response, metadata)
    assert one.iloc[0].analogue_prediction == 1
    assert one.iloc[0].analogue_absolute_error == 1
    assert two.iloc[0].analogue_prediction == 2
    assert two.iloc[0].analogue_absolute_error == 0
    assert two.iloc[0].peak_spread == 1
    assert two.iloc[0].same_river_share == 0
    assert pairs.cross_country.all()


def test_fusion_controls_receive_identical_conventional_features():
    feature = pd.DataFrame({key: [1.0, 2.0] for key in M.BASE.FEATURE_COLUMNS}, index=["a", "q"])
    sample = feature.reset_index(names="event_id")
    raw = pd.DataFrame([[1.0, 0.0], [0.0, 1.0]], index=feature.index)
    ordered = pd.DataFrame([[1.0, 2.0, 0.0], [2.0, 0.0, 1.0]], index=feature.index)
    settings = {
        "r0": {},
        "r1": {"representation_vectors": raw},
        "raw_state": {},
        "ttm_ordered_state": {},
        "ttm_ordered": {"representation_vectors": ordered},
    }
    context = {key: {} for key in ["r0", "r1", "r2", "r2_area", "r2_identity", "r3_alphaearth"]}
    configs = M.configurations(
        {"dutch": settings, "pooled": settings, "context": context},
        {"dutch": sample, "context": sample, "pooled": sample},
    )
    for cohort in ["dutch", "context"]:
        a, b = configs[cohort]["fusion_raw"], configs[cohort]["fusion_ttm"]
        pd.testing.assert_frame_equal(
            a["distance_blocks"]["conventional"], b["distance_blocks"]["conventional"]
        )
        assert a["robust_distance_blocks"] == b["robust_distance_blocks"] == ("conventional",)


def test_replay_rejects_changed_inputs_but_does_not_freeze_code(tmp_path):
    import hashlib

    import pytest

    upstream = tmp_path / "results/basin_ai_representation_checks/summary.json"
    upstream.parent.mkdir(parents=True)
    upstream.write_text("{}")
    data = tmp_path / "observations.csv"
    data.write_text("value\n1\n")
    manifest = {
        "upstream_manifest_sha256": hashlib.sha256(upstream.read_bytes()).hexdigest(),
        "input_sha256": {"observations.csv": hashlib.sha256(data.read_bytes()).hexdigest()},
    }
    assert M.verified_run_inputs(manifest, tmp_path) == manifest["input_sha256"]
    (tmp_path / "code.py").write_text("changed code is allowed in a separately recorded audit")
    upstream.write_text('{"code_revision":"updated"}')
    assert M.verified_run_inputs(manifest, tmp_path) == manifest["input_sha256"]
    data.write_text("value\n2\n")
    with pytest.raises(ValueError, match="Changed input"):
        M.verified_run_inputs(manifest, tmp_path)


def test_replay_rejects_changed_upstream_manifest(tmp_path):
    import hashlib

    import pytest

    upstream = tmp_path / "results/basin_ai_representation_checks/summary.json"
    upstream.parent.mkdir(parents=True)
    upstream.write_text("{}")
    manifest = {
        "upstream_manifest_sha256": hashlib.sha256(upstream.read_bytes()).hexdigest(),
    }
    upstream.write_text('{"new":"run"}')
    with pytest.raises(ValueError, match="Upstream manifest changed"):
        M.verified_run_inputs(manifest, tmp_path)


def test_mean_donor_peak_is_not_peak_of_mean_curve_and_timing_is_individual():
    metadata = pd.DataFrame(
        {
            "event_id": ["q", "a", "b"],
            "physical_river_group": ["Wurm/Worm", "Geul", "Gulp"],
            "country": ["DE", "NL", "NL"],
            "measurement_concern": [False] * 3,
        }
    ).set_index("event_id")
    values = np.ones((3, 72))
    values[0, 0] = 2
    values[1, 0] = 3
    values[2, -1] = 3
    response = pd.DataFrame(values, index=metadata.index)
    scores = pd.DataFrame({"query_event_id": ["q"], "query_storm_id": ["sq"]})
    donors = pd.DataFrame(
        {"query_event_id": ["q", "q"], "analogue_event_id": ["a", "b"], "rank": [1, 2]}
    )
    result, _ = M.assess(scores, donors, response, metadata)
    row = result.iloc[0]
    assert row.analogue_prediction == 3
    assert response.loc[["a", "b"]].mean(axis=0).max() == 2
    assert row.mean_donor_peak_absolute_error == 1
    assert row.mean_peak_time_difference_h == 35.5
    np.testing.assert_allclose(row.ensemble_curve_level_rmse, 1 / np.sqrt(72))
