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
