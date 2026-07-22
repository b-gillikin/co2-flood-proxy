"""Offline tests for groundwater normalization and the locked direct-state model."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.direct_state import CONTROL_COLS, run_direct_state
from src.io_groundwater import normalize_groundwater, select_primary_series
from src.models.july import TARGET_COL


def metadata_fixture():
    return pd.DataFrame(
        [
            {
                "series_id": "mine_direct",
                "provider": "fixture province",
                "measurement_name": "mine water depth",
                "unit": "m",
                "datum": "below surface",
                "source_tier": 1,
                "site_relationship": "connected shaft",
                "higher_value_means_higher_water": False,
                "operational_notes": "none",
            },
            {
                "series_id": "nearby_well",
                "provider": "fixture water board",
                "measurement_name": "groundwater elevation",
                "unit": "m",
                "datum": "NAP",
                "source_tier": 2,
                "site_relationship": "nearby relevant aquifer",
                "higher_value_means_higher_water": True,
                "operational_notes": "none",
            },
        ]
    )


def direct_state_fixture(days=100):
    rng = np.random.default_rng(3)
    dates = pd.date_range("2026-01-01", periods=days, freq="D", tz="UTC")
    water = rng.normal(0, 1, days)
    daily = pd.DataFrame(
        {
            "date_utc": np.tile(dates, 2),
            "series_id": np.repeat(["mine_direct", "nearby_well"], days),
            "water_level_value": np.concatenate([-water, rng.normal(size=days)]),
            "hydrologic_level": np.concatenate([water, rng.normal(size=days)]),
            "source_observations": 1,
            "usable_observations": 1,
        }
    )
    index = pd.date_range(dates.min(), periods=days * 24, freq="h", tz="UTC")
    day_number = ((index - index.min()) / pd.Timedelta(days=1)).astype(int)
    temperature = 12 + 4 * np.sin(np.arange(len(index)) / 200)
    humidity = 65 + 5 * np.cos(np.arange(len(index)) / 170)
    pressure = 1012 + 2 * np.sin(np.arange(len(index)) / 90)
    residual = 6 * water[day_number] + rng.normal(0, 0.5, len(index))
    frame = pd.DataFrame(
        {
            TARGET_COL: residual,
            CONTROL_COLS[0]: temperature,
            CONTROL_COLS[1]: humidity,
            CONTROL_COLS[2]: pressure,
        },
        index=index,
    )
    gap_start = days // 2 - 1
    frame.loc[
        (frame.index >= dates[gap_start]) & (frame.index < dates[gap_start + 2]),
        TARGET_COL,
    ] = np.nan
    return frame, daily, metadata_fixture()


class GroundwaterNormalizationTests(unittest.TestCase):
    def test_depth_is_reoriented_and_missing_day_is_not_interpolated(self):
        readings = pd.DataFrame(
            {
                "timestamp": ["2026-01-01", "2026-01-03"],
                "series_id": ["mine_direct", "mine_direct"],
                "water_level_value": [4.0, 2.0],
            }
        )
        daily = normalize_groundwater(readings, metadata_fixture(), source_timezone="UTC")
        self.assertEqual(len(daily), 2)
        self.assertEqual(daily["date_utc"].dt.day.tolist(), [1, 3])
        self.assertEqual(daily["hydrologic_level"].tolist(), [-4.0, -2.0])

    def test_direct_tier_wins_before_larger_nearby_overlap(self):
        dates = pd.date_range("2026-01-01", periods=10, freq="D", tz="UTC")
        daily = pd.DataFrame(
            {
                "date_utc": [dates[0], *dates],
                "series_id": ["mine_direct", *(["nearby_well"] * len(dates))],
                "hydrologic_level": np.arange(len(dates) + 1),
            }
        )
        primary, audit = select_primary_series(daily, metadata_fixture(), dates)
        self.assertEqual(primary, "mine_direct")
        self.assertEqual(
            int(audit.loc[audit["series_id"].eq("nearby_well"), "iot_overlap_days"].iloc[0]), 10
        )


class DirectStateTests(unittest.TestCase):
    def test_locked_model_supports_strong_two_block_fixture(self):
        frame, daily, metadata = direct_state_fixture()
        results = run_direct_state(frame, daily, metadata, bootstrap_replicates=100)
        summary = results["summary"]
        self.assertEqual(summary["primary_series_id"], "mine_direct")
        self.assertEqual(summary["outcome"], "direct_state_primary_supported")
        self.assertGreaterEqual(summary["paired_days"], 60)
        self.assertGreaterEqual(summary["qualifying_blocks"], 2)
        self.assertTrue(results["decision"]["passed"].all())
        self.assertTrue(results["sensitivities"]["p_fdr_bh"].notna().all())

    def test_short_record_is_inconclusive_even_with_strong_coefficient(self):
        frame, daily, metadata = direct_state_fixture(days=45)
        results = run_direct_state(frame, daily, metadata, bootstrap_replicates=20)
        self.assertEqual(results["summary"]["outcome"], "inconclusive_because_of_coverage")
        coverage = results["decision"].set_index("criterion").loc["coverage_gate", "passed"]
        self.assertFalse(bool(coverage))


if __name__ == "__main__":
    unittest.main()
