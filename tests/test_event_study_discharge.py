"""Checks for the discharge-ingest building blocks (protocol §3).

Synthetic 15-minute data only. `build_series`/`build_candidate` read the real
Waterschap delivery and are not unit-tested here; the CLI's refusal to
`--commit` without verified semantics is exercised directly.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "event_study_discharge", ROOT / "scripts" / "45_build_event_study_discharge.py"
)
INGEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INGEST)


def quarter_hours(n, start="2020-01-01"):
    return pd.date_range(start, periods=n, freq="15min")


def test_fixed_offset_never_shifts_across_the_dst_transition():
    # 2020-03-29: the EU spring-forward date. A fixed GMT+1 offset does not move.
    naive = pd.Series(quarter_hours(8, "2020-03-29 00:00"))
    utc = INGEST.convert_timestamps(naive, "fixed_utc_plus_1")
    assert (utc.diff().dropna() == pd.Timedelta(minutes=15)).all()
    assert utc.iloc[0] == pd.Timestamp("2020-03-28 23:00", tz="UTC")


def test_civil_amsterdam_marks_the_nonexistent_spring_forward_hour():
    # Dutch civil time jumps from 02:00 to 03:00 CEST on 2020-03-29.
    naive = pd.Series(quarter_hours(12, "2020-03-29 01:30"))
    utc = INGEST.convert_timestamps(naive, "civil_amsterdam")
    assert utc.isna().any()


def test_civil_amsterdam_marks_the_ambiguous_autumn_hour():
    # 2020-10-25: 02:00-03:00 CEST repeats as 02:00-03:00 CET.
    naive = pd.Series(quarter_hours(8, "2020-10-25 02:00"))
    utc = INGEST.convert_timestamps(naive, "civil_amsterdam")
    assert utc.isna().any()


def test_true_zero_keeps_zeros_and_missing_sentinel_blanks_them():
    values = pd.Series([0.0, 1.5, np.nan, 0.0])

    assert INGEST.apply_zero_assumption(values, "true_zero").tolist()[0] == 0.0
    masked = INGEST.apply_zero_assumption(values, "missing_sentinel")
    assert masked.isna().sum() == 3  # the original NaN plus both zeros


def test_an_hour_is_populated_only_when_all_four_quarters_are_present():
    index = quarter_hours(8, "2020-06-01 00:00")
    values = pd.Series([1.0, 1.0, 1.0, 1.0, 2.0, np.nan, 2.0, 2.0], index=index)
    utc = pd.Series(index, index=index).dt.tz_localize("UTC")

    hourly = INGEST.four_quarter_hour_mean(values, utc)

    assert hourly.iloc[0] == pytest.approx(1.0)
    assert pd.isna(hourly.iloc[1])


def test_a_missing_utc_timestamp_drops_its_quarter_from_the_hour():
    index = quarter_hours(4, "2020-06-01 00:00")
    values = pd.Series([1.0, 1.0, 1.0, 1.0], index=index)
    utc = pd.Series(index, index=index).dt.tz_localize("UTC")
    utc.iloc[0] = pd.NaT

    hourly = INGEST.four_quarter_hour_mean(values, utc)

    assert hourly.empty or pd.isna(hourly.iloc[0])


def test_a_documented_failure_interval_is_masked():
    index = quarter_hours(4, "2020-06-01 00:00")
    values = pd.Series([1.0, 1.0, 1.0, 1.0], index=index)
    INGEST.FAILURE_INTERVALS["TEST"] = [("2020-06-01 00:00", "2020-06-01 00:30")]
    try:
        masked = INGEST.mask_failure_intervals(values, "TEST")
    finally:
        del INGEST.FAILURE_INTERVALS["TEST"]

    assert masked.isna().sum() == 3


def test_commit_is_refused_before_the_gauges_table_is_fully_verified(tmp_path, monkeypatch):
    gauges_path = tmp_path / "gauges.csv"
    pd.DataFrame(
        {
            "gauge": ["A", "B"],
            "timezone_verified": [False, False],
            "zero_semantics_verified": [False, False],
        }
    ).to_csv(gauges_path, index=False)
    monkeypatch.setattr(INGEST, "GAUGES", gauges_path)

    ok, reason = INGEST.gauges_fully_verified()

    assert not ok
    assert "not both true" in reason
