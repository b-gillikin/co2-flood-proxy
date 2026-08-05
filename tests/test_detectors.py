"""Regression tests for the shared detector family contract."""

from __future__ import annotations

import pickle
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from src.detectors import (
    DetectorSpec,
    _statsmodels_status,
    assert_pressure_safe,
    fit_detector,
    load_detector_spec,
    model_payload,
    score_detector,
    state_space_features,
)
from src.models.signal_frame import TARGET_COL


def detector_fixture(periods=264):
    """Deterministic hourly frame with the locked controls and IF inputs."""
    index = pd.date_range("2026-01-01", periods=periods, freq="h", tz="UTC")
    phase = np.arange(periods, dtype=float)
    return pd.DataFrame(
        {
            TARGET_COL: 8 * np.sin(phase / 12) + phase / 200,
            "iot_co2_ppm": 500 + 15 * np.sin(phase / 24),
            "iot_temperature_c": 18 + 2 * np.sin(phase / 24),
            "iot_relative_humidity_pct": 60 + 4 * np.cos(phase / 24),
            "iot_air_pressure_hpa": 1010 + np.cos(phase / 18),
        },
        index=index,
    )


def detector_specs():
    controls = ("iot_temperature_c", "iot_relative_humidity_pct")
    return {
        "sarimax": DetectorSpec(
            detector="sarimax",
            family="arx",
            features=controls,
            order=(2, 0, 0),
            seasonal_order=(0, 0, 0, 0),
        ),
        "kalman": DetectorSpec(
            detector="kalman",
            family="ridge_local_level",
            features=controls,
            warmup_hours=3,
        ),
        "iforest": DetectorSpec(
            detector="iforest",
            family="isolation_forest",
            features=(
                TARGET_COL,
                "iot_co2_ppm",
                "iot_temperature_c",
                "iot_relative_humidity_pct",
            ),
        ),
    }


class DetectorContractTests(unittest.TestCase):
    def test_state_space_controls_are_pressure_safe(self):
        frame = detector_fixture()

        self.assertEqual(
            state_space_features(frame),
            ["iot_temperature_c", "iot_relative_humidity_pct"],
        )
        with self.assertRaisesRegex(ValueError, "cannot reintroduce pressure"):
            assert_pressure_safe(["iot_air_pressure_hpa"])

    def test_arx_fit_and_future_score_keep_the_same_family(self):
        frame = detector_fixture()
        spec = detector_specs()["sarimax"]
        train = frame.iloc[:168]
        future = frame.iloc[168:192]

        fit = fit_detector(spec, train[TARGET_COL], train[list(spec.features)])
        scored = score_detector(
            fit,
            future[TARGET_COL],
            future[list(spec.features)],
        )

        self.assertEqual(fit.status, "ok")
        self.assertEqual(fit.spec.family, "arx")
        self.assertGreater(int(scored.score.notna().sum()), 20)
        scaler = fit.model.named_steps["standardscaler"]
        self.assertEqual(len(scaler.mean_), len(spec.features) + spec.order[0])

    def test_ridge_local_level_scores_future_without_family_substitution(self):
        frame = detector_fixture()
        spec = detector_specs()["kalman"]
        train = frame.iloc[:168]
        future = frame.iloc[168:192]

        fit = fit_detector(spec, train[TARGET_COL], train[list(spec.features)])
        scored = score_detector(
            fit,
            future[TARGET_COL],
            future[list(spec.features)],
        )

        self.assertEqual(fit.status, "ok")
        self.assertEqual(fit.spec.family, "ridge_local_level")
        self.assertTrue(scored.score.notna().all())
        self.assertIsNotNone(fit.final_state)

    def test_versioned_payload_round_trips_exact_spec(self):
        frame = detector_fixture()
        spec = detector_specs()["sarimax"]
        fit = fit_detector(spec, frame[TARGET_COL], frame[list(spec.features)])

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.pkl"
            with path.open("wb") as handle:
                pickle.dump(model_payload(spec, fit), handle)

            loaded = load_detector_spec(path, "sarimax")

        self.assertEqual(loaded, spec)

    def test_convergence_warning_cannot_be_ok(self):
        class ConvergenceWarning(Warning):
            pass

        result = SimpleNamespace(mle_retvals={"converged": True})
        caught = [SimpleNamespace(category=ConvergenceWarning)]

        self.assertEqual(_statsmodels_status(result, caught), "non_converged")


if __name__ == "__main__":
    unittest.main()
