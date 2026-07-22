"""Fixture-driven execution of actual core and direct-state entry points."""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import chapter_steps, execute_pipeline
from src.provenance import build_snapshot_id, write_run_manifest

pipeline_cli = importlib.import_module("scripts.15_run_analysis_pipeline")


def write_pipeline_fixture(workspace, periods=1500):
    """Write a deterministic, service-free hourly snapshot for every script."""
    workspace = Path(workspace)
    for directory in ("data/raw/fixture", "data/interim", "data/processed", "results"):
        (workspace / directory).mkdir(parents=True, exist_ok=True)

    index = pd.date_range("2026-01-01", periods=periods, freq="h", tz="UTC")
    phase = np.arange(periods, dtype=float)
    pressure = 1012 + 4 * np.sin(phase / 37) + 0.5 * np.cos(phase / 9)
    temperature = 13 + 6 * np.sin(phase * 2 * np.pi / (24 * 30))
    humidity = 68 + 12 * np.cos(phase * 2 * np.pi / (24 * 14))
    precip = np.where((phase.astype(int) % 113) < 8, 0.8, 0.0)
    residual = (
        7 * np.sin(phase / 11) + 3 * np.cos(phase / 31) + 0.04 * temperature - 0.03 * humidity
    )
    co2 = 520 + residual + 1.7 * (pressure - pressure.mean())

    signal = pd.DataFrame(
        {
            "timestamp_utc": index,
            "co2_residual_barometric_ppm": residual,
            "iot_co2_ppm": co2,
            "iot_air_pressure_hpa": pressure,
            "iot_temperature_c": temperature,
            "iot_relative_humidity_pct": humidity,
            "iot_pm2_5_ugm3": 8 + 0.4 * np.sin(phase / 17),
            "iot_pm10_ugm3": 13 + 0.8 * np.cos(phase / 19),
            "kerkrade_weather_temp_c": temperature + 0.2,
            "kerkrade_weather_relative_humidity_pct": humidity - 1,
            "kerkrade_weather_pressure_hpa": pressure + 0.3,
            "kerkrade_weather_precip_mm": precip,
            "kerkrade_weather_wind_speed_kph": 9 + 2 * np.sin(phase / 23),
            "kerkrade_weather_cloud_cover_pct": 45 + 20 * np.cos(phase / 29),
            "kerkrade_weather_pm2_5_ugm3": 7 + 0.3 * np.sin(phase / 21),
            "kerkrade_weather_pm10_ugm3": 12 + 0.5 * np.cos(phase / 25),
            "kerkrade_weather_no2_ugm3": 18 + np.sin(phase / 15),
            "kerkrade_weather_o3_ugm3": 35 + np.cos(phase / 16),
            "discharge_geul_hommerich_m3s": 2 + 0.02 * phase / 24 + precip,
        }
    )
    signal.to_csv(workspace / "data/processed/signal_characterization_frame.csv", index=False)

    analysis = signal[
        [
            "timestamp_utc",
            "iot_co2_ppm",
            "kerkrade_weather_precip_mm",
            "discharge_geul_hommerich_m3s",
        ]
    ]
    analysis.to_csv(workspace / "data/interim/analysis_hourly.csv", index=False)

    knmi = pd.DataFrame(
        {
            "knmi_station": "06380",
            "timestamp_utc": index,
            "knmi_pressure_hpa": pressure + 0.1,
            "knmi_temperature_c": temperature,
            "knmi_relative_humidity_pct": humidity,
            "knmi_precip_mm": precip,
        }
    )
    knmi.to_csv(workspace / "data/interim/knmi_hourly.csv", index=False)

    rivm = pd.DataFrame(
        {
            "timestamp_utc": index,
            "rivm_nl10136_no2_ugm3": 20 + np.sin(phase / 13),
            "rivm_nl10136_pm10_ugm3": 14 + np.cos(phase / 17),
            "rivm_nl10138_no2_ugm3": 19 + np.cos(phase / 14),
            "rivm_nl10138_o3_ugm3": 37 + np.sin(phase / 18),
            "rivm_nl10138_pm10_ugm3": 15 + np.sin(phase / 16),
        }
    )
    rivm.to_csv(workspace / "data/interim/rivm_hourly.csv", index=False)

    events = pd.DataFrame(
        {
            "event_id": ["fixture_1", "fixture_2"],
            "source": ["fixture_gauge", "fixture_gauge"],
            "threshold_quantile": [0.9, 0.95],
            "start_timestamp_utc": [index[600], index[1100]],
            "end_timestamp_utc": [index[612], index[1115]],
            "peak_timestamp_utc": [index[606], index[1107]],
        }
    )
    events.to_csv(workspace / "data/processed/event_catalogue.csv", index=False)
    soft = pd.DataFrame(
        {
            "timestamp_utc": index,
            "any_current_level": ((phase % 400) < 12).astype(float),
            "any_current_soft_label": ((phase % 400) < 12).astype(float) / 3,
        }
    )
    soft.to_csv(workspace / "data/processed/hourly_soft_labels.csv", index=False)
    water = pd.DataFrame(
        {
            "date_utc": index.floor("D").unique(),
            "series_id": "fixture_mine_level",
            "water_level_value": np.sin(np.arange(index.floor("D").nunique()) / 5),
            "hydrologic_level": np.sin(np.arange(index.floor("D").nunique()) / 5),
            "source_observations": 1,
            "usable_observations": 1,
        }
    )
    water.to_csv(workspace / "data/interim/groundwater_daily.csv", index=False)
    metadata = pd.DataFrame(
        [
            {
                "series_id": "fixture_mine_level",
                "provider": "fixture",
                "measurement_name": "mine water level",
                "unit": "m",
                "datum": "fixture datum",
                "source_tier": 1,
                "site_relationship": "direct fixture connection",
                "higher_value_means_higher_water": True,
                "operational_notes": "deterministic offline fixture",
            }
        ]
    )
    metadata.to_csv(workspace / "data/interim/groundwater_series.csv", index=False)
    raw = workspace / "data/raw/fixture/source.csv"
    signal.iloc[:48].to_csv(raw, index=False)
    return raw


def run_fixture(workspace):
    """Execute the actual scripts and write their development manifest."""
    raw = write_pipeline_fixture(workspace)
    normalized = [
        Path(workspace) / "data/interim/analysis_hourly.csv",
        Path(workspace) / "data/interim/knmi_hourly.csv",
        Path(workspace) / "data/interim/rivm_hourly.csv",
        Path(workspace) / "data/processed/signal_characterization_frame.csv",
        Path(workspace) / "data/processed/event_catalogue.csv",
        Path(workspace) / "data/processed/hourly_soft_labels.csv",
        Path(workspace) / "data/interim/groundwater_daily.csv",
        Path(workspace) / "data/interim/groundwater_series.csv",
    ]
    cutoff = pd.Timestamp("2026-03-04T11:00:00Z")
    execution = execute_pipeline(
        workspace,
        ROOT,
        [raw],
        normalized,
        cutoff,
        fixture=True,
        include_direct_state=True,
    )
    output_paths = [
        Path(workspace) / record["path"]
        for command in execution["ledger"]
        for record in command["outputs"]
    ]
    return write_run_manifest(
        Path(workspace) / "results/run_manifest.json",
        normalized,
        output_paths,
        [],
        cutoff,
        root=Path(workspace),
        raw_input_paths=[raw],
        normalized_input_paths=normalized,
        execution_ledger=execution["ledger"],
        snapshot_id=execution["snapshot_id"],
        model_paths=[
            Path(workspace) / f"results/models/{detector}.pkl"
            for detector in ("sarimax", "kalman", "iforest")
        ],
        git_root=ROOT,
    )


class OfflinePipelineIntegrationTests(unittest.TestCase):
    """Prove actual entry-point execution and deterministic scientific outputs."""

    def test_pipeline_refuses_missing_required_input_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            raw = workspace / "raw.csv"
            raw.write_text("value\n1\n", encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "Missing required normalized inputs"):
                execute_pipeline(
                    workspace,
                    ROOT,
                    [raw],
                    [workspace / "missing.csv"],
                    pd.Timestamp("2026-01-01T00:00:00Z"),
                    fixture=True,
                )

    def test_fixture_profile_cannot_be_frozen(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            raw = workspace / "raw.csv"
            normalized = workspace / "normalized.csv"
            raw.write_text("value\n1\n", encoding="utf-8")
            normalized.write_text("timestamp_utc,value\n2026-01-01T00:00:00Z,1\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "fixture/skip mode"):
                execute_pipeline(
                    workspace,
                    ROOT,
                    [raw],
                    [normalized],
                    pd.Timestamp("2026-01-01T00:00:00Z"),
                    fixture=True,
                    frozen=True,
                )

    def test_transfer_can_be_omitted_without_changing_core_order(self):
        steps = chapter_steps(skip_transfer=True)
        names = [step.name for step in steps]
        self.assertNotIn("11_transfer_stress_test", names)
        self.assertEqual(names[-1], "12_distributed_lag")

    def test_frozen_run_cannot_silently_omit_direct_state(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "explicit --direct-state omit"):
                pipeline_cli.direct_state_scope(Path(directory), "auto", frozen=True)

            include, paths = pipeline_cli.direct_state_scope(
                Path(directory),
                "omit",
                frozen=True,
            )
            self.assertFalse(include)
            self.assertEqual(paths, [])

    def test_actual_analysis_entrypoints_repeat_with_matching_hashes(self):
        with (
            tempfile.TemporaryDirectory() as first_dir,
            tempfile.TemporaryDirectory() as second_dir,
        ):
            first = run_fixture(Path(first_dir))
            second = run_fixture(Path(second_dir))

            expected_steps = [
                "05_sarimax",
                "06_kalman",
                "07_isolation_forest",
                "08_ensemble_agreement",
                "09_synthetic_injection",
                "10_evaluation",
                "16_direct_state",
                "12_distributed_lag",
                "11_transfer_stress_test",
            ]
            self.assertEqual([item["step"] for item in first["commands"]], expected_steps)
            self.assertTrue(all(item["returncode"] == 0 for item in first["commands"]))
            self.assertTrue(all(item["outputs"] for item in first["commands"]))
            self.assertEqual(first["snapshot_id"], build_snapshot_id(first["inputs"]))
            self.assertEqual(first["snapshot_id"], second["snapshot_id"])
            self.assertEqual(first["scientific_output_sha256"], second["scientific_output_sha256"])
            self.assertEqual(
                [(item["detector"], item["fit_status"]) for item in first["models"]],
                [("sarimax", "ok"), ("kalman", "ok"), ("iforest", "ok")],
            )


if __name__ == "__main__":
    unittest.main()
