"""Regression tests for source quirks that materially changed discharge."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "waterschap_ingest", ROOT / "scripts" / "22_ingest_waterschap_gauges.py"
)
INGEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INGEST)


def write_payload(path, values):
    rows = [
        {"DateTime": f"2025-01-01T{hour:02}:00:00Z", "Value": value}
        for hour, value in enumerate(values)
    ]
    path.write_text(json.dumps({"value": rows}))


def test_sparse_zero_sentinels_become_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(INGEST, "RAW_DIR", tmp_path)
    write_payload(tmp_path / "test_1.json", [1.0, 0.0, 1.2, 1.1])

    series = INGEST.fetch_series(1, "test")

    assert np.isnan(series.iloc[1, 0])
    assert series.iloc[[0, 2, 3], 0].notna().all()


def test_mostly_zero_dry_gauge_is_flagged_but_not_erased(tmp_path, monkeypatch):
    monkeypatch.setattr(INGEST, "RAW_DIR", tmp_path)
    write_payload(tmp_path / "dry_2.json", [0.0, 0.0, 0.0, 1.0])

    series = INGEST.fetch_series(2, "dry")

    assert series.iloc[:3, 0].eq(0).all()
