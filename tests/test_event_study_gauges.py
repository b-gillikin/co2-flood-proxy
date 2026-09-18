"""Checks for the primary-gauge metadata build (decision D3/D5)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "event_study_gauges", ROOT / "scripts" / "44_build_event_study_gauges.py"
)
GAUGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GAUGES)


def test_built_gauges_match_the_d3_cohort():
    gauges, _ = GAUGES.build_gauges()

    assert len(gauges) == 6
    assert gauges.gauge.is_unique
    assert gauges.include_primary.all()
    assert gauges.natural_tributary.all()
    assert gauges.july_2021_status.str.len().gt(0).all()


def test_brommelen_shares_one_independence_unit_with_the_split_system():
    gauges, _ = GAUGES.build_gauges()

    row = gauges.set_index("gauge").loc["6.Q.18"]
    assert row.watercourse == "Geleenbeek"
    assert row.independence_unit == "Geleenbeek-Vloedgraaf"
    assert gauges.independence_unit.is_unique


def test_zero_and_timezone_semantics_stay_unverified_but_units_and_sampling_do_not():
    gauges, _ = GAUGES.build_gauges()

    assert not gauges.zero_semantics_verified.any()
    assert not gauges.timezone_verified.any()
    assert gauges.units_verified.all()
    assert gauges.sampling_semantics_verified.all()
    assert gauges.rating_eras_documented.all()


def test_waterschaps_own_pins_confirm_the_provisional_coordinates():
    _, crosscheck = GAUGES.build_gauges()

    assert len(crosscheck) == 6
    assert crosscheck.offset_m.max() < 30.0  # one Copernicus GLO-30 DEM cell
