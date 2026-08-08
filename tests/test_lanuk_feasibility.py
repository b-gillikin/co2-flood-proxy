"""Checks for the held-data LANUK feasibility audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lanuk_feasibility", ROOT / "scripts" / "32_lanuk_feasibility.py"
)
LANUK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LANUK)


def test_later_iot_overlap_requires_every_precursor_hour(tmp_path, monkeypatch):
    index = pd.date_range("2025-01-01", periods=500, freq="h", tz="UTC")
    discharge = pd.DataFrame({"gauge": 0.0}, index=index)
    discharge.loc[[index[100], index[300]], "gauge"] = 2.0
    iot = pd.DataFrame(
        {
            "timestamp_utc": index,
            "iot_co2_ppm": 400.0,
            "iot_air_pressure_hpa": 1000.0,
        }
    )
    iot.loc[50, "iot_co2_ppm"] = np.nan
    path = tmp_path / "iot.csv"
    iot.to_csv(path, index=False)
    monkeypatch.setattr(LANUK, "LATER_IOT_PATH", path)
    metadata = pd.DataFrame(
        {"gauge": ["gauge"], "watercourse": ["river"], "watercourse_verified": [True]}
    )

    overlap = LANUK.later_iot_overlap(discharge, metadata).iloc[0]

    assert overlap.p99_onsets_in_later_iot_span == 2
    assert overlap.complete_72h_iot_windows == 1
