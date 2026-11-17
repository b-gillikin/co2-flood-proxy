"""Geometry review cannot improve apparent skill by silently dropping hard cases."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dise_spatial import analysis_memberships, location_stratum, overlap_stratum, review_status

BANDS = {
    "minimal_overlap_dice_below": 0.1,
    "existing_high_overlap_dice_at_least": 0.8,
    "directional_coverage_at_least": 0.9,
    "near_reference_within_m": 100,
    "large_reference_offset_above_m": 1000,
}


def test_directional_overlap_is_distinct_from_minimal_overlap():
    assert (
        overlap_stratum(True, 0.72, 0.98, 0.6, BANDS)
        == "reference_mostly_inside_larger_model_footprint"
    )
    assert (
        overlap_stratum(True, 0.72, 0.6, 0.98, BANDS)
        == "model_mostly_inside_larger_reference_footprint"
    )
    assert overlap_stratum(True, 0.02, 0.02, 0.02, BANDS) == "minimal_or_disjoint_footprints"
    assert overlap_stratum(True, 0.65, 0.7, 0.6, BANDS) == "mixed_partial_overlap"


def test_missing_and_unmapped_are_explicit():
    assert overlap_stratum(False, np.nan, np.nan, np.nan, BANDS) == "no_model_network_coverage"
    assert overlap_stratum(True, np.nan, 0.9, 0.8, BANDS) == "unknown_footprint"
    assert location_stratum(np.nan, BANDS) == "unknown_station_reference_location"


def test_station_reference_conflict_does_not_assign_the_wrong_source():
    location = location_stratum(5000, BANDS)
    assert (
        review_status("high_overlap_proxy", location)
        == "unresolved_station_or_reference_metadata_conflict"
    )
    assert location_stratum(100, BANDS) == "on_or_near_reference_footprint"
    assert location_stratum(500, BANDS) == "moderate_station_reference_offset"


def test_uncertainty_preserves_acquired_census_and_role_boundaries():
    for role in ["regional_donor", "reserved_external"]:
        v = analysis_memberships(
            True, role, "minimal_or_disjoint_footprints", "large_station_reference_disagreement"
        )
        assert v["include_all_mapped_census"] and v["evaluate_mapping_stress_stratum"]
        assert not v["include_high_overlap_sensitivity"]
    assert not analysis_memberships(
        True,
        "local_connected_section_excluded",
        "high_overlap_proxy",
        "on_or_near_reference_footprint",
    )["include_all_mapped_census"]
    assert not analysis_memberships(
        False,
        "unmapped_source_coverage",
        "no_model_network_coverage",
        "on_or_near_reference_footprint",
    )["include_all_mapped_census"]


def test_high_overlap_location_sensitivity_does_not_silently_change_census():
    a = analysis_memberships(
        True, "regional_donor", "high_overlap_proxy", "large_station_reference_disagreement"
    )
    b = analysis_memberships(
        True, "regional_donor", "high_overlap_proxy", "on_or_near_reference_footprint"
    )
    assert a["include_all_mapped_census"] and b["include_all_mapped_census"]
    assert (
        a["include_high_overlap_sensitivity"]
        and not a["include_high_overlap_location_consistent_sensitivity"]
    )
    assert b["include_high_overlap_location_consistent_sensitivity"]
