"""Small offline checks for source loaders."""

from __future__ import annotations

import sys
import unittest
import importlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "kerkrade_data"))

from src.io_data import load_iot, load_iot_observations, load_knmi, load_rivm
from src.models.july import antecedent_precipitation_index, available_exog

knmi_backfill = importlib.import_module("knmi_backfill")
rivm_ingest = importlib.import_module("scripts.04_ingest_rivm")


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class LoaderTests(unittest.TestCase):
    """Verify Week 4 loaders against tiny cached payloads."""

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
        self.assertEqual(hourly["iot_observation_count"].iloc[0], 2)
        self.assertEqual(hourly["iot_device_count"].iloc[0], 1)

    def test_load_knmi_csv_sample(self):
        frame = load_knmi(FIXTURES, frequency="h", station="380")

        self.assertEqual(len(frame), 3)
        self.assertEqual(frame["knmi_station"].iloc[0], "06380")
        self.assertIn("knmi_temperature_c", frame.columns)
        self.assertIn("knmi_pressure_hpa", frame.columns)
        self.assertAlmostEqual(frame["knmi_temperature_c"].iloc[0], 12.3)
        self.assertAlmostEqual(frame["knmi_pressure_hpa"].iloc[0], 1012.3)

    def test_load_knmi_named_station_set(self):
        frame = load_knmi(FIXTURES, frequency="h", station_set="meuse")

        self.assertEqual(len(frame), 4)
        self.assertEqual(set(frame["knmi_station"]), {"06377", "06380"})

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


class KnmiBackfillHelperTests(unittest.TestCase):
    """Verify the Azure KNMI backfill cursor helpers."""

    def test_knmi_filename_uses_utc_10_minute_boundary(self):
        timestamp = knmi_backfill.floor_10_minutes(
            knmi_backfill.parse_utc("2020-01-01T00:09:59Z")
        )

        self.assertEqual(timestamp.isoformat(), "2020-01-01T00:00:00+00:00")
        self.assertEqual(
            knmi_backfill.filename_for(timestamp),
            "KMDS__OPER_P___10M_OBS_L2_202001010000.nc",
        )

    def test_knmi_blob_name_uses_raw_prefix(self):
        self.assertEqual(
            knmi_backfill.blob_name_for("file.nc", "raw/10-minute-in-situ"),
            "raw/10-minute-in-situ/file.nc",
        )

    def test_knmi_station_list_is_zero_padded(self):
        self.assertEqual(
            knmi_backfill.parse_station_list("380,06377, 6392"),
            ["06380", "06377", "06392"],
        )

    def test_knmi_slim_blob_name_is_monthly(self):
        timestamp = knmi_backfill.parse_utc("2020-02-03T04:10:00Z")

        self.assertEqual(
            knmi_backfill.slim_blob_name_for(timestamp, "slim/10-minute-in-situ"),
            "slim/10-minute-in-situ/year=2020/month=02/knmi_meuse_10min_2020_02.csv.gz",
        )

    def test_knmi_backward_cursor_helpers(self):
        start = knmi_backfill.parse_utc("2020-01-01T00:00:00Z")
        end = knmi_backfill.parse_utc("2020-01-01T01:09:00Z")
        direction = knmi_backfill.normalize_direction("reverse")
        cursor = knmi_backfill.initial_cursor(start, end, direction)

        self.assertEqual(direction, "backward")
        self.assertEqual(cursor.isoformat(), "2020-01-01T01:00:00+00:00")
        self.assertTrue(knmi_backfill.cursor_in_bounds(cursor, start, end, direction))
        self.assertEqual(
            knmi_backfill.advance_cursor(cursor, direction).isoformat(),
            "2020-01-01T00:50:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
