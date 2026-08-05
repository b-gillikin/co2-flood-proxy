"""Offline tests for groundwater normalization.

Direct-state model tests moved to archive/ on 2026-08-05 with that analysis."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_groundwater import normalize_groundwater, select_primary_series


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


if __name__ == "__main__":
    unittest.main()
