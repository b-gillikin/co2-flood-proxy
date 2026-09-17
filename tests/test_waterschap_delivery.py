"""Checks for the Waterschap delivery and source-metadata audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "waterschap_delivery", ROOT / "scripts" / "35_audit_waterschap_delivery.py"
)
WATERSCHAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WATERSCHAP)


def test_source_qa_registry_classifies_every_delivered_series_once():
    metadata = WATERSCHAP.station_metadata_table()
    expected = {row[0] for row in WATERSCHAP.SERIES}

    assert set(metadata.series_key) == expected
    assert metadata.series_key.is_unique


def test_reply_resolves_sampling_but_not_timezone_zero_or_validation_flags():
    metadata = WATERSCHAP.station_metadata_table()

    assert metadata.sampling_semantics_verified.all()
    assert metadata.units_verified.all()
    assert not metadata.timezone_verified.any()
    assert not metadata.zero_sentinel_verified.any()
    assert not metadata.validation_flags_available.any()
    assert not metadata.rating_curve_verified.any()


def test_populated_july_cells_are_not_equated_with_usable_discharge():
    metadata = WATERSCHAP.station_metadata_table().set_index("series_key")

    assert metadata.loc["18.Q.45", "july_2021_instrument_status"] == "operational"
    assert (
        metadata.loc["18.Q.45", "july_2021_discharge_status"]
        == "exclude_peak_outside_rating_domain"
    )
    assert "exclude" in metadata.loc["10.Q.36", "july_2021_discharge_status"]
    assert "exclude" in metadata.loc["12.Q.46", "july_2021_discharge_status"]
