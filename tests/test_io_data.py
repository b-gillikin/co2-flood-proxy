"""Small offline checks for source loaders."""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "kerkrade_data"))

from src.features import antecedent_precipitation_index
from src.io_data import load_iot, load_iot_observations, load_knmi
from src.io_iot import _device_id_from_export_path
from src.io_knmi import _normalize_knmi_frame
from src.models.signal_frame import (
    available_exog,
    select_features_by_joint_coverage,
)

knmi_backfill = importlib.import_module("knmi_backfill")


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


class KnmiUnitTests(unittest.TestCase):
    """KNMI tenths-unit codes scale deterministically and warn when off."""

    def _tenths_frame(self, temp_tenths):
        # Real KNMI hourly rows carry both U (humidity, whole %) and RH
        # (precipitation, 0.1 mm); include U so RH is sourced as precip.
        return pd.DataFrame(
            {
                "STN": [380, 380],
                "timestamp": ["2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z"],
                "T": temp_tenths,
                "P": [10123, 10125],
                "U": [80, 82],
                "RH": [-1, 5],
            }
        )

    def test_tenths_codes_are_scaled(self):
        out = _normalize_knmi_frame(self._tenths_frame([123, 50]))

        self.assertAlmostEqual(out["knmi_temperature_c"].iloc[0], 12.3)
        self.assertAlmostEqual(out["knmi_pressure_hpa"].iloc[0], 1012.3)
        # Humidity code U is whole percent (factor 1.0), not tenths.
        self.assertAlmostEqual(out["knmi_relative_humidity_pct"].iloc[0], 80.0)
        # KNMI trace sentinel -1 (0.1 mm units) maps to 0; 5 -> 0.5 mm.
        self.assertAlmostEqual(out["knmi_precip_mm"].iloc[0], 0.0)
        self.assertAlmostEqual(out["knmi_precip_mm"].iloc[1], 0.5)

    def test_out_of_range_values_warn(self):
        # 600 tenths -> 60 C, outside the plausible [-40, 50] range.
        with self.assertLogs("src.io_knmi", level="WARNING") as captured:
            _normalize_knmi_frame(self._tenths_frame([600, 50]))
        self.assertTrue(any("knmi_temperature_c" in message for message in captured.output))


class DeviceIdTests(unittest.TestCase):
    """Blynk device id comes from the folder name, not the whole path."""

    def test_numeric_ancestor_is_ignored(self):
        path = Path("/data/2025010112/export/device_67890_basement")
        self.assertEqual(_device_id_from_export_path(path), "67890")


class JulyModelHelperTests(unittest.TestCase):
    """Verify the small shared modelling helpers."""

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

    def test_optional_feature_cannot_erase_a_material_recent_block(self):
        early = pd.date_range("2026-01-01", periods=216, freq="h", tz="UTC")
        recent = pd.date_range("2026-07-09", periods=24, freq="h", tz="UTC")
        index = early.append(recent)
        frame = pd.DataFrame(
            {
                "target": 1.0,
                "required": 2.0,
                "optional_historical_only": [3.0] * len(early) + [None] * len(recent),
            },
            index=index,
        )

        selected, audit = select_features_by_joint_coverage(
            frame,
            target_col="target",
            required=["required"],
            optional=["optional_historical_only"],
            min_non_missing=20,
        )

        self.assertEqual(selected, ["required"])
        row = audit.set_index("feature").loc["optional_historical_only"]
        self.assertEqual(row["reason"], "material_block_coverage_below_threshold")
        self.assertEqual(float(row["minimum_material_block_share"]), 0.0)

    def test_optional_features_are_gated_on_accumulated_joint_coverage(self):
        index = pd.date_range("2026-01-01", periods=100, freq="h", tz="UTC")
        frame = pd.DataFrame(
            {
                "target": 1.0,
                "required": 2.0,
                "optional_a": [None] * 5 + [1.0] * 95,
                "optional_b": [1.0] * 95 + [None] * 5,
                "optional_c": [1.0] * 5 + [None] * 5 + [1.0] * 90,
            },
            index=index,
        )

        selected, audit = select_features_by_joint_coverage(
            frame,
            target_col="target",
            required=["required"],
            optional=["optional_a", "optional_b", "optional_c"],
            min_non_missing=20,
            min_block_share=0.0,
        )

        self.assertEqual(selected, ["required", "optional_a", "optional_b"])
        rejected = audit.set_index("feature").loc["optional_c"]
        self.assertEqual(rejected["reason"], "joint_coverage_below_threshold")


class KnmiBackfillHelperTests(unittest.TestCase):
    """Verify the Azure KNMI backfill cursor helpers."""

    def test_knmi_filename_uses_utc_10_minute_boundary(self):
        timestamp = knmi_backfill.floor_10_minutes(knmi_backfill.parse_utc("2020-01-01T00:09:59Z"))

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

    def test_knmi_forward_uses_an_independent_state_blob(self):
        self.assertEqual(
            knmi_backfill.default_state_blob("forward"),
            "state/knmi_forward_state.json",
        )
        self.assertEqual(
            knmi_backfill.default_state_blob("backward"),
            "state/knmi_backfill_state.json",
        )

    def test_knmi_forward_end_respects_publication_lag(self):
        now = knmi_backfill.parse_utc("2026-07-21T20:09:00Z")

        end = knmi_backfill.availability_end(now, "forward", 180)

        self.assertEqual(end.isoformat(), "2026-07-21T17:09:00+00:00")
        self.assertEqual(
            knmi_backfill.availability_end(now, "backward", 180),
            now,
        )

    def test_knmi_publication_lag_cannot_be_negative(self):
        now = knmi_backfill.parse_utc("2026-07-21T20:00:00Z")

        with self.assertRaisesRegex(ValueError, "must be non-negative"):
            knmi_backfill.availability_end(now, "forward", -1)


if __name__ == "__main__":
    unittest.main()
