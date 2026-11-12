import numpy as np
import pytest

from limburg_chapter_validity import compare_geometry, label_transition_counts


def scene(**changes):
    return dict(
        platform="sentinel-1a",
        relative_orbit=139,
        pass_direction="descending",
        mode="IW",
        polarizations=("VH", "VV"),
        look="right",
        **changes,
    )


def test_same_track_across_constellation_is_not_a_geometry_failure():
    other = scene()
    other["platform"] = "sentinel-1b"
    result = compare_geometry(scene(), other)
    assert result["status"] == "compatible"
    assert not result["same_platform"]


def test_matching_references_do_not_prove_event_geometry_matches():
    reference = scene()
    event = {**scene(), "pass_direction": "ascending", "relative_orbit": 15}
    assert compare_geometry(reference, reference)["status"] == "compatible"
    result = compare_geometry(reference, event)
    assert result["status"] == "mismatch"
    assert set(result["mismatched"].split(",")) == {"relative_orbit", "pass_direction"}


def test_missing_metadata_is_not_a_match_and_does_not_hide_known_mismatch():
    assert compare_geometry({}, {})["status"] == "unknown"
    assert compare_geometry({"relative_orbit": 1}, {"relative_orbit": 2})["status"] == "mismatch"


def test_mask_reconstruction_does_not_silently_turn_unknown_into_dry():
    primary = np.array([0, 1, 2, 2, 255], dtype=np.uint8)
    alternative = np.array([0, 2, 1, 255, 0], dtype=np.uint8)
    counts = label_transition_counts(primary, alternative, np.ones(5, dtype=bool))
    assert counts.sum() == 5
    assert counts[1, 2] == counts[2, 1] == counts[2, 3] == counts[3, 0] == 1
    with pytest.raises(ValueError, match="encoding"):
        label_transition_counts(np.array([4]), np.array([0]), np.array([True]))


def test_water_collapse_preserves_support_and_distinguishes_attribution():
    import importlib.util
    from pathlib import Path

    import pandas as pd

    path = Path(__file__).resolve().parents[1] / "scripts/255_consolidate_chapter_validity.py"
    spec = importlib.util.spec_from_file_location("validity_summary", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = pd.DataFrame([{f"c{i}{j}": int(i == 2 and j == 1) for i in range(3) for j in range(3)}])
    collapsed = module.water_counts(rows)
    assert rows.c22.iloc[0] == 0
    assert collapsed.c22.iloc[0] == 1
    assert collapsed[module.COUNTS].sum(axis=1).iloc[0] == 1
