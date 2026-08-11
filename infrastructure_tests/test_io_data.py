"""Small offline checks for source loaders."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_iot import _device_id_from_export_path, load_iot, load_iot_observations

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class LoaderTests(unittest.TestCase):
    """Verify source loaders against tiny cached payloads."""

    def test_load_blynk_iot_export_sample(self):
        observations = load_iot_observations(
            raw_dir=FIXTURES / "missing_iot_raw",
            blynk_export_dir=FIXTURES / "iot_exports",
        )

        self.assertEqual(len(observations), 2)
        self.assertEqual(observations["iot_source"].iloc[0], "blynk_export")
        self.assertEqual(observations["iot_device_name"].iloc[0], "Sample Basement")
        self.assertEqual(observations["iot_device_id"].iloc[0], "12345")
        self.assertEqual(
            observations["timestamp"].iloc[0],
            pd.Timestamp("2025-01-31 00:00:00Z"),
        )

        hourly = load_iot(
            raw_dir=FIXTURES / "missing_iot_raw",
            blynk_export_dir=FIXTURES / "iot_exports",
            frequency="h",
        )

        self.assertEqual(len(hourly), 1)
        self.assertAlmostEqual(hourly["iot_temperature_c"].iloc[0], 21.0)
        self.assertAlmostEqual(hourly["iot_co2_ppm"].iloc[0], 460.0)
        self.assertEqual(hourly["iot_co2_observation_count"].iloc[0], 2)
        self.assertEqual(hourly["iot_device_count"].iloc[0], 1)


class DeviceIdTests(unittest.TestCase):
    """Blynk device id comes from the folder name, not the whole path."""

    def test_numeric_ancestor_is_ignored(self):
        path = Path("/data/2025010112/export/device_67890_basement")
        self.assertEqual(_device_id_from_export_path(path), "67890")


if __name__ == "__main__":
    unittest.main()
