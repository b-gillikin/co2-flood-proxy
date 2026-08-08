"""Checks for the retained same-site Eryilmaz context analysis."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "eryilmaz_replication", ROOT / "scripts" / "03_eryilmaz_replication.py"
)
ERYILMAZ = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ERYILMAZ)


def test_pressure_change_does_not_bridge_a_coverage_gap():
    index = pd.DatetimeIndex(
        [
            "2025-01-01 00:00Z",
            "2025-01-01 01:00Z",
            "2025-01-01 02:00Z",
            "2025-01-01 07:00Z",
        ]
    )
    pressure = pd.Series([1000.0, 1001.0, 1002.0, 1007.0], index=index)

    change = ERYILMAZ.observed_change(pressure, hours=3)

    assert change.isna().all()


def test_calendar_splits_are_defined_before_complete_case_gaps():
    full = pd.date_range("2025-01-01", periods=600, freq="h", tz="UTC")
    observed = full.delete(slice(100, 500))
    frame = pd.DataFrame({"high_co2": [0, 1] * 100}, index=observed)
    frame.attrs.update(full_start=full.min(), full_end=full.max())

    splits = list(ERYILMAZ.calendar_splits(frame))

    assert len(splits) == 5
    for _, train, test, test_start, test_end in splits:
        assert (frame.index[train] < test_start).all()
        assert ((frame.index[test] >= test_start) & (frame.index[test] < test_end)).all()


def test_complete_case_outage_is_measured_in_calendar_hours():
    index = pd.DatetimeIndex(["2025-01-01 00:00Z", "2025-01-01 05:00Z"])

    gap = ERYILMAZ.longest_missing_run(
        index,
        pd.Timestamp("2025-01-01 00:00Z"),
        pd.Timestamp("2025-01-01 06:00Z"),
    )

    assert gap == 4
