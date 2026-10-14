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
