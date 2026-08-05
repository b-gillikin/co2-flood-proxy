"""Archived tests for cross-detector agreement and rolling-origin evaluation.

Moved from tests/test_eval.py on 2026-08-05 with the detector programme.
Retained for reference; the scripts under test live in archive/scripts/.
"""

class EnsembleUnionTests(unittest.TestCase):
    """Detectors with disjoint coverage union rather than intersect."""

    def _detector_frame(self, name, hours, values, scored=None):
        index = pd.date_range("2025-01-01", periods=4, freq="h", tz="UTC")
        scored = [True] * len(values) if scored is None else scored
        return pd.DataFrame(
            {
                "timestamp_utc": index[list(hours)],
                f"{name}_anomaly": values,
                f"{name}_scored": scored,
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
        self.assertEqual(second_hour["coverage_status"], "partial")

    def test_present_but_unscored_flag_is_not_a_normal_or_anomaly(self):
        frames = [
            self._detector_frame("sarimax", (0,), [True], scored=[False]),
            self._detector_frame("kalman", (0,), [False]),
            self._detector_frame("iforest", (0,), [False]),
        ]

        flags = combine_detector_flags(frames, ("sarimax", "kalman", "iforest"))
        hour = flags.iloc[0]

        self.assertFalse(bool(hour["sarimax_anomaly"]))
        self.assertFalse(bool(hour["sarimax_scored"]))
        self.assertFalse(bool(hour["all_detectors_normal"]))
        self.assertFalse(bool(hour["any_detector_anomaly"]))
        self.assertEqual(hour["coverage_status"], "partial")

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
