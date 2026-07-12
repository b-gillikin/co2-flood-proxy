"""Offline checks for discharge-label evaluation and July anomaly helpers."""

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

from src.eval import (
    combine_detector_flags,
    deduplicate_event_episodes,
    hourly_discharge_soft_labels,
    sustained_exceedance_events,
    time_based_windows,
)
from src.models.july import anomaly_table, contiguous_blocks, fitted_model_status, robust_zscore

evaluation_script = importlib.import_module("scripts.10_evaluation")


def ascending_discharge(with_gap=False):
    """One gauge with strictly ascending values so p90 exceedance is the tail."""
    index = pd.date_range("2025-01-01", periods=100, freq="h", tz="UTC")
    values = np.arange(100, dtype=float)
    if with_gap:
        values[95] = np.nan
    return pd.DataFrame({"discharge_test_m3s": values}, index=index)


class SoftLabelTests(unittest.TestCase):
    """Missing discharge must not read as calm conditions."""

    def test_unobserved_hours_get_nan_labels(self):
        discharge = ascending_discharge(with_gap=True)
        labels = hourly_discharge_soft_labels(discharge, quantiles=(0.90,))

        gap_hour = discharge.index[95]
        high_hour = discharge.index[99]
        low_hour = discharge.index[0]

        self.assertTrue(pd.isna(labels.loc[gap_hour, "test_current_level"]))
        self.assertEqual(labels.loc[high_hour, "test_current_level"], 1.0)
        self.assertEqual(labels.loc[low_hour, "test_current_level"], 0.0)

    def test_antecedent_max_skips_missing_hours(self):
        discharge = ascending_discharge(with_gap=True)
        labels = hourly_discharge_soft_labels(
            discharge, quantiles=(0.90,), antecedent_windows=(24,)
        )
        # The last hour's 24h antecedent window contains the gap but also
        # observed exceedance hours, so the maximum must still be 1.
        self.assertEqual(labels.iloc[-1]["test_antecedent_24h_level"], 1.0)


class SustainedEventTests(unittest.TestCase):
    """Exceedance runs must not bridge coverage gaps."""

    def test_contiguous_exceedance_is_one_event(self):
        events = sustained_exceedance_events(
            ascending_discharge(),
            quantiles=(0.90,),
            min_duration_hours=7,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events.iloc[0]["duration_hours"], 10)

    def test_missing_hour_splits_the_run(self):
        events = sustained_exceedance_events(
            ascending_discharge(with_gap=True),
            quantiles=(0.90,),
            min_duration_hours=7,
        )
        # The NaN hour splits the exceedance tail into 6h + 4h fragments,
        # both below the 7-hour minimum duration.
        self.assertEqual(len(events), 0)


class EpisodeDeduplicationTests(unittest.TestCase):
    """Overlapping gauge/quantile rows collapse into physical episodes."""

    def test_overlapping_rows_merge(self):
        start = pd.Timestamp("2025-06-01 00:00", tz="UTC")
        events = pd.DataFrame(
            {
                "source": [
                    "discharge_a_m3s",
                    "discharge_a_m3s",
                    "discharge_b_m3s",
                    "discharge_a_m3s",
                ],
                "threshold_quantile": [0.90, 0.95, 0.90, 0.90],
                "start_timestamp_utc": [
                    start,
                    start + pd.Timedelta(hours=2),
                    start + pd.Timedelta(hours=5),
                    start + pd.Timedelta(days=10),
                ],
                "end_timestamp_utc": [
                    start + pd.Timedelta(hours=12),
                    start + pd.Timedelta(hours=8),
                    start + pd.Timedelta(hours=20),
                    start + pd.Timedelta(days=10, hours=6),
                ],
            }
        )
        episodes = deduplicate_event_episodes(events)

        self.assertEqual(len(episodes), 2)
        first = episodes.iloc[0]
        self.assertEqual(first["n_source_events"], 3)
        self.assertEqual(first["n_sources"], 2)
        self.assertEqual(first["max_threshold_quantile"], 0.95)
        self.assertEqual(first["end_timestamp_utc"], start + pd.Timedelta(hours=20))
        self.assertEqual(episodes.iloc[1]["n_source_events"], 1)

    def test_empty_catalogue(self):
        episodes = deduplicate_event_episodes(pd.DataFrame())
        self.assertTrue(episodes.empty)


class AnomalyScoreTests(unittest.TestCase):
    """Shared scoring helpers behave sensibly at the edges."""

    def test_anomaly_table_flags_outlier_and_skips_nan(self):
        index = pd.date_range("2025-01-01", periods=50, freq="h", tz="UTC")
        score = np.zeros(50)
        score[10] = 10.0
        score[20] = np.nan
        table = anomaly_table(index, score, prefix="demo")

        self.assertTrue(bool(table.loc[10, "demo_anomaly"]))
        self.assertFalse(bool(table.loc[20, "demo_anomaly"]))
        self.assertEqual(int(table["demo_anomaly"].sum()), 1)

    def test_robust_zscore_uses_reference_sample(self):
        z = robust_zscore([2.0, 12.0], reference=[0.0, 1.0, 2.0, 3.0, 4.0])
        self.assertAlmostEqual(float(z.iloc[0]), 0.0)
        self.assertAlmostEqual(float(z.iloc[1]), 0.6745 * 10.0, places=6)

    def test_contiguous_blocks_split_and_filter(self):
        early = pd.date_range("2025-01-01 00:00", periods=6, freq="h", tz="UTC")
        late = pd.date_range("2025-01-02 00:00", periods=12, freq="h", tz="UTC")
        blocks = contiguous_blocks(early.append(late))
        self.assertEqual([len(index) for _, index in blocks], [6, 12])

        filtered = contiguous_blocks(early.append(late), min_hours=8)
        self.assertEqual([len(index) for _, index in filtered], [12])


class EnsembleUnionTests(unittest.TestCase):
    """Detectors with disjoint coverage union rather than intersect."""

    def _detector_frame(self, name, hours, values):
        index = pd.date_range("2025-01-01", periods=4, freq="h", tz="UTC")
        return pd.DataFrame(
            {
                "timestamp_utc": index[list(hours)],
                f"{name}_anomaly": values,
            }
        )

    def test_missing_detector_rows_are_unscored_not_normal(self):
        frames = [
            self._detector_frame("sarimax", (0, 1), [True, False]),
            self._detector_frame("kalman", (1, 2), [True, True]),
            self._detector_frame("iforest", (2, 3), [False, True]),
        ]
        flags = combine_detector_flags(frames, ("sarimax", "kalman", "iforest"))

        # Union of the three disjoint coverages is four hours, not the empty
        # intersection an inner join would produce.
        self.assertEqual(len(flags), 4)
        second_hour = flags.iloc[1]
        self.assertFalse(bool(second_hour["sarimax_anomaly"]))
        self.assertTrue(bool(second_hour["kalman_anomaly"]))
        self.assertFalse(bool(second_hour["iforest_anomaly"]))
        self.assertTrue(bool(second_hour["sarimax_scored"]))
        self.assertTrue(bool(second_hour["kalman_scored"]))
        self.assertFalse(bool(second_hour["iforest_scored"]))
        self.assertEqual(int(second_hour["detector_count"]), 1)
        self.assertEqual(int(second_hour["scored_detector_count"]), 2)
        self.assertFalse(bool(second_hour["all_detectors_scored"]))
        self.assertFalse(bool(flags["all_three_anomaly"].any()))

    def test_any_detector_summary_counts_only_common_coverage(self):
        frames = [
            self._detector_frame("sarimax", (0, 1), [True, False]),
            self._detector_frame("kalman", (0, 1, 2), [False, False, True]),
            self._detector_frame("iforest", (0, 1, 2, 3), [False, True, False, True]),
        ]
        flags = combine_detector_flags(frames, ("sarimax", "kalman", "iforest"))
        summary = evaluation_script.detector_summary(flags, basis="test")
        any_detector = summary.loc[summary["detector"].eq("any_detector")].iloc[0]
        self.assertEqual(int(any_detector["n_hours"]), 2)


class ModelFitStatusTests(unittest.TestCase):
    """Warning-only optimizer failures must stay visible in outputs."""

    class Result:
        def __init__(self, converged):
            self.mle_retvals = {"converged": converged}

    def test_non_converged_result_is_not_ok(self):
        self.assertEqual(fitted_model_status(self.Result(False)), "non_converged")

    def test_converged_result_is_ok(self):
        self.assertEqual(fitted_model_status(self.Result(True)), "ok")


class RollingArtifactLifecycleTests(unittest.TestCase):
    """Skipped/replacement runs cannot leave valid-looking older outputs."""

    def test_invalidate_rolling_outputs_removes_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / "flags.csv", Path(directory) / "summary.csv"]
            for path in paths:
                path.write_text("stale\n", encoding="utf-8")

            evaluation_script.invalidate_rolling_outputs(paths)

            self.assertTrue(all(not path.exists() for path in paths))


class WindowCoverageTests(unittest.TestCase):
    """Coverage is scored against observed hours, not the calendar grid."""

    def test_outage_window_is_insufficient(self):
        record_index = pd.date_range("2025-01-01", periods=96, freq="h", tz="UTC")
        observed_index = record_index[24:]  # first 24h are an IoT outage

        windows = time_based_windows(
            record_index,
            train_hours=24,
            eval_hours=24,
            label="t",
            min_coverage=0.7,
            observed_index=observed_index,
        )

        # The window whose training span sits in the outage is enumerated but
        # unusable; a later fully observed window is ok.
        self.assertEqual(windows.iloc[0]["status"], "insufficient_coverage")
        self.assertTrue((windows["status"] == "ok").any())

    def test_full_coverage_defaults_to_observed(self):
        record_index = pd.date_range("2025-01-01", periods=96, freq="h", tz="UTC")
        windows = time_based_windows(
            record_index,
            train_hours=24,
            eval_hours=24,
            label="t",
            min_coverage=0.7,
        )
        self.assertTrue((windows["status"] == "ok").all())


if __name__ == "__main__":
    unittest.main()
