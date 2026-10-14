"""Context controls share temporal information; donor replacements are accounted for."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha_review", ROOT / "scripts/83_review_alphaearth_event_information.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_changed_donors_separate_same_group_event_swap_from_new_group():
    reference = pd.DataFrame(
        {
            "analogue_event_id": ["a", "b"],
            "analogue_storm_id": ["s1", "s2"],
            "peak_scaled_shape_rmse": [0.4, 0.2],
        }
    )
    challenger = pd.DataFrame(
        {
            "analogue_event_id": ["c", "b"],
            "analogue_storm_id": ["s1", "s2"],
            "peak_scaled_shape_rmse": [0.1, 0.2],
        }
    )
    result = M.donor_change(reference, challenger)
    assert result["changed_events"] == 1 and result["shared_onset_groups"] == 2
    np.testing.assert_allclose(result["replacement_shape_difference"], -0.15)
    same = M.donor_change(reference, reference)
    assert same["changed_events"] == 0 and same["replacement_shape_difference"] == 0
    assert np.isnan(same["entered_mean_shape_error"])


def test_identity_context_cannot_change_cross_river_distance_order():
    vectors = pd.DataFrame([[0.0], [3.0], [1.0]], index=["a", "b", "q"])
    identity = pd.get_dummies(pd.Series(["A", "B", "Q"], index=vectors.index), dtype=float)
    candidates = pd.DataFrame({"event_id": ["a", "b"]})
    query = type("Query", (), {"event_id": "q"})()
    base, _ = M.B.block_distances(candidates, query, {"ttm": vectors})
    controlled, detail = M.B.block_distances(
        candidates, query, {"ttm": vectors, "identity": identity}
    )
    assert base.sort_values().index.tolist() == controlled.sort_values().index.tolist()
    assert detail.identity_distance.nunique() == 1


def test_strengthened_context_controls_share_identical_temporal_and_state_blocks():
    ids = ["a", "b"]
    bands = [f"A{i:02d}" for i in range(64)]
    joined = pd.DataFrame(
        {
            "event_id": ids,
            "alphaearth_input_sample": True,
            "gauge": ["x", "y"],
            "catchment_area_km2": [1.0, 2.0],
        }
    )
    for i, band in enumerate(bands):
        joined[band] = [1.0 if i == 0 else 0.0, 1.0 if i == 1 else 0.0]
    years = joined.rename(columns={"event_id": "unused"}).assign(embedding_year=2017)
    mean = pd.DataFrame([[1.0, 0.0], [0.0, 1.0]], index=ids)
    ordered = pd.DataFrame([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]], index=ids)
    state = pd.DataFrame({"level": [1.0, 2.0]}, index=ids)
    arms, _ = M.context_arms(joined, mean, ordered, state, years)
    for control in M.CONTROLS:
        a = arms[("ordered_state", control)]
        pd.testing.assert_frame_equal(a["distance_blocks"]["temporal"], ordered)
        pd.testing.assert_frame_equal(a["distance_blocks"]["state"], state)
        assert a["robust_distance_blocks"] == ("state",)
    expected = years.set_index("gauge")[bands].loc[joined.gauge].to_numpy()
    np.testing.assert_allclose(
        arms[("mean", "static_2017")]["distance_blocks"]["static_2017"], expected
    )
