"""Small offline checks for source loaders."""

from __future__ import annotations

import sys
import unittest
import importlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_data import load_knmi, load_rivm
from src.models.july import antecedent_precipitation_index, available_exog

rivm_ingest = importlib.import_module("scripts.04_ingest_rivm")


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class LoaderTests(unittest.TestCase):
    """Verify Week 4 loaders against tiny cached payloads."""

    def test_load_knmi_csv_sample(self):
        frame = load_knmi(FIXTURES, frequency="h", station="380")

        self.assertEqual(len(frame), 3)
        self.assertIn("knmi_temperature_c", frame.columns)
        self.assertIn("knmi_pressure_hpa", frame.columns)
        self.assertAlmostEqual(frame["knmi_temperature_c"].iloc[0], 12.3)
        self.assertAlmostEqual(frame["knmi_pressure_hpa"].iloc[0], 1012.3)

    def test_load_rivm_json_sample(self):
        frame = load_rivm(
            FIXTURES / "rivm",
            frequency="h",
            stations=["NL90001"],
            components=["PM10", "PM25"],
        )

        self.assertEqual(len(frame), 1)
        self.assertIn("rivm_nl90001_pm10_ugm3", frame.columns)
        self.assertIn("rivm_nl90001_pm25_ugm3", frame.columns)
        self.assertAlmostEqual(frame["rivm_nl90001_pm10_ugm3"].iloc[0], 17.5)
        self.assertAlmostEqual(frame["rivm_nl90001_pm25_ugm3"].iloc[0], 8.25)

    def test_load_rivm_portal_csv_sample(self):
        frame = load_rivm(
            FIXTURES / "rivm",
            frequency="h",
            stations=["NL90002"],
            components=["PM10"],
        )

        self.assertEqual(len(frame), 2)
        self.assertIn("rivm_nl90002_pm10_ugm3", frame.columns)
        self.assertAlmostEqual(frame["rivm_nl90002_pm10_ugm3"].iloc[0], 12.5)

    def test_rivm_api_station_number_is_normalized(self):
        candidates = rivm_ingest.candidate_stations(
            [{"number": "NL50010", "location": "Maastricht Philipsweg"}],
            ["maastricht"],
        )

        self.assertEqual(candidates["station_number"].iloc[0], "NL50010")


class JulyModelHelperTests(unittest.TestCase):
    """Verify small shared July modelling helpers."""

    def test_api_uses_day_scaled_exponential_decay(self):
        precip = [10.0, 0.0, 0.0, 0.0]
        api = antecedent_precipitation_index(
            precip,
            days=2,
            decay=0.85,
            hours_per_day=2,
        )

        self.assertAlmostEqual(api.iloc[0], 0.0)
        self.assertAlmostEqual(api.iloc[1], 8.5)
        self.assertAlmostEqual(api.iloc[2], 8.5)
        self.assertAlmostEqual(api.iloc[3], 7.225)

    def test_available_exog_filters_against_requested_target(self):
        frame = pd.DataFrame(
            {
                "co2_residual_barometric_ppm": [None, None, None],
                "iot_co2_ppm": [450.0, 460.0, 470.0],
                "iot_air_pressure_hpa": [1001.0, 1002.0, 1003.0],
            }
        )

        self.assertNotIn(
            "iot_air_pressure_hpa",
            available_exog(frame, min_non_missing=2),
        )
        self.assertIn(
            "iot_air_pressure_hpa",
            available_exog(frame, target_col="iot_co2_ppm", min_non_missing=2),
        )


if __name__ == "__main__":
    unittest.main()
