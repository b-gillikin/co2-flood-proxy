"""Offline fixture integration across provisional analysis scripts 05-12."""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.detectors import local_level_filter, make_lagged_frame
from src.eval import combine_detector_flags, time_based_windows
from src.models.july import TARGET_COL

iforest = importlib.import_module("scripts.07_isolation_forest")
ensemble = importlib.import_module("scripts.08_ensemble_agreement")
injection = importlib.import_module("scripts.09_synthetic_injection")
evaluation = importlib.import_module("scripts.10_evaluation")
transfer = importlib.import_module("scripts.11_transfer_stress_test")
distributed_lag = importlib.import_module("scripts.12_distributed_lag")


def signal_fixture(periods=240):
    """Deterministic hourly signal fixture with the shared model columns."""
    index = pd.date_range("2026-01-01", periods=periods, freq="h", tz="UTC")
    phase = np.arange(periods, dtype=float)
    return pd.DataFrame(
        {
            TARGET_COL: 10 * np.sin(phase / 12) + phase / 100,
            "iot_co2_ppm": 500 + 20 * np.sin(phase / 24),
            "iot_air_pressure_hpa": 1010 + np.cos(phase / 18),
            "iot_temperature_c": 18 + np.sin(phase / 24),
            "iot_relative_humidity_pct": 60 + np.cos(phase / 24),
        },
        index=index,
    )


class OfflinePipelineIntegrationTests(unittest.TestCase):
    """Exercise one substantive offline contract from every script 05-12."""

    def test_scripts_05_through_12_share_one_offline_fixture(self):
        frame = signal_fixture()

        # 05: lag construction keeps honest hourly predictors.
        lagged, predictors = make_lagged_frame(
            frame,
            TARGET_COL,
            ["iot_air_pressure_hpa"],
            p=1,
            d=0,
        )
        self.assertFalse(lagged.empty)
        self.assertIn("target_lag_1", predictors)

        # 06: fallback local-level filter returns one innovation per hour.
        filtered = local_level_filter(frame[TARGET_COL].iloc[:72], q=1.0, r=4.0)
        self.assertEqual(len(filtered), 72)
        self.assertTrue(np.isfinite(filtered["standardized_innovation"]).all())

        # 07: the multivariate detector fits without external services.
        model = iforest.fit_iforest(frame[[TARGET_COL, "iot_co2_ppm"]])
        self.assertEqual(len(model.score_samples(frame[[TARGET_COL, "iot_co2_ppm"]])), len(frame))

        # 08: common-coverage agreement is distinct from the union.
        detector_frames = []
        for name, start in (("sarimax", 0), ("kalman", 1), ("iforest", 2)):
            detector_frames.append(
                pd.DataFrame(
                    {
                        "timestamp_utc": frame.index[start : start + 20],
                        f"{name}_scored": [True] * 20,
                        f"{name}_anomaly": [False] * 19 + [True],
                    }
                )
            )
        flags = combine_detector_flags(detector_frames, ("sarimax", "kalman", "iforest"))
        agreement, pairwise = ensemble.agreement_tables(flags)
        self.assertEqual(int(agreement["n_hours"].sum()), 18)
        self.assertTrue((pairwise["common_scored_hours"] > 0).all())

        # 09: all locked injection templates produce explicit windows.
        templates = injection.injection_templates(frame[TARGET_COL])
        self.assertEqual(set(templates), {"gaussian_burst", "cut_add_paste", "level_shift"})
        self.assertTrue(all(mask.any() for _, mask in templates.values()))
        detection = pd.DataFrame(
            {
                "template": ["a", "b", "a", "b"],
                "detector": ["valid", "valid", "invalid", "invalid"],
                "detector_status": ["ok", "ok", "ok", "non_converged"],
                "event_detected": [True, False, True, False],
                "detection_rate": [1.0, 0.0, 1.0, 0.0],
                "false_flag_rate": [0.1, 0.1, 0.0, 0.0],
            }
        )
        selection = injection.model_selection_table(detection).set_index("detector")
        self.assertEqual(int(selection.loc["valid", "selection_rank"]), 1)
        self.assertTrue(pd.isna(selection.loc["invalid", "selection_rank"]))
        self.assertEqual(selection.loc["invalid", "selection_status"], "excluded_non_ok_fit")

        # 10: official-style calendar windows carry explicit coverage status.
        windows = time_based_windows(
            frame.index,
            train_hours=120,
            eval_hours=24,
            label="offline",
            min_coverage=0.7,
        )
        self.assertTrue((windows["status"] == "ok").all())
        rate_summary = evaluation.detector_summary(flags, basis="offline_fixture")
        self.assertIn("n_hours", rate_summary.columns)

        # 11: feature availability/deployability is evaluated locally.
        transfer_frame = pd.DataFrame({column: np.ones(60) for column in transfer.TRANSFER_SCHEMA})
        availability = transfer.feature_availability(
            transfer_frame,
            {site: transfer_frame.copy() for site in transfer.TRANSFER_SITES},
        )
        selected = transfer.deployable_features(availability, min_transfer_hours=24)
        self.assertEqual(selected, transfer.TRANSFER_SCHEMA)

        # 12: antecedent and placebo transforms remain distinct and gap-honest.
        precip = pd.Series(
            np.arange(60, dtype=float), index=pd.date_range("2026-01-01", periods=60, freq="D")
        )
        antecedent = distributed_lag.weighted_api(precip, half_life_days=3, direction="lag")
        placebo = distributed_lag.weighted_api(precip, half_life_days=3, direction="lead")
        self.assertFalse(antecedent.equals(placebo))


if __name__ == "__main__":
    unittest.main()
