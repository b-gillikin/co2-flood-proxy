"""Outcome-blind descriptive strata for gauge/global-model correspondence.

Bands label geometry, not statistical validity or mandatory exclusion rules.
"""

from __future__ import annotations

import numpy as np


def overlap_stratum(mapped, dice, reference_covered, model_purity, bands):
    if not mapped:
        return "no_model_network_coverage"
    values = [dice, reference_covered, model_purity]
    if not np.isfinite(values).all():
        return "unknown_footprint"
    if dice < bands["minimal_overlap_dice_below"]:
        return "minimal_or_disjoint_footprints"
    if dice >= bands["existing_high_overlap_dice_at_least"]:
        return "high_overlap_proxy"
    if reference_covered >= bands["directional_coverage_at_least"]:
        return "reference_mostly_inside_larger_model_footprint"
    if model_purity >= bands["directional_coverage_at_least"]:
        return "model_mostly_inside_larger_reference_footprint"
    return "mixed_partial_overlap"


def location_stratum(distance_m, bands):
    if not np.isfinite(distance_m):
        return "unknown_station_reference_location"
    if distance_m <= bands["near_reference_within_m"]:
        return "on_or_near_reference_footprint"
    if distance_m <= bands["large_reference_offset_above_m"]:
        return "moderate_station_reference_offset"
    return "large_station_reference_disagreement"


def review_status(overlap, location):
    if overlap == "no_model_network_coverage":
        return "coverage_case_no_same_site_model_series"
    if location == "large_station_reference_disagreement":
        return "unresolved_station_or_reference_metadata_conflict"
    if overlap in ["minimal_or_disjoint_footprints", "unknown_footprint"]:
        return "unresolved_footprint_correspondence"
    if overlap == "high_overlap_proxy":
        return "high_overlap_proxy_supported_not_exact_site_validation"
    if overlap.startswith(("reference_mostly_", "model_mostly_")):
        return "directional_footprint_difference_explicitly_stratified"
    return "partial_footprint_difference_explicitly_stratified"


def analysis_memberships(mapped, role, overlap, location):
    """No geometry band silently removes an acquired record from the census."""
    allowed = mapped and role in ["regional_donor", "reserved_external"]
    return dict(
        include_all_mapped_census=bool(allowed),
        include_high_overlap_sensitivity=bool(allowed and overlap == "high_overlap_proxy"),
        include_high_overlap_location_consistent_sensitivity=bool(
            allowed
            and overlap == "high_overlap_proxy"
            and location == "on_or_near_reference_footprint"
        ),
        evaluate_mapping_stress_stratum=bool(
            allowed
            and (
                overlap in ["minimal_or_disjoint_footprints", "unknown_footprint"]
                or location == "large_station_reference_disagreement"
            )
        ),
    )
