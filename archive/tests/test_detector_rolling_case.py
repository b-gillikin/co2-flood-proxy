"""Archived rolling-origin case, moved from tests/test_detectors.py on 2026-08-05.

Exercised archive/scripts/10_evaluation.py. Kept for reference; not runnable
without restoring that script.
"""

    def test_synthetic_and_rolling_paths_report_persisted_families(self):
        frame = detector_fixture()
        specs = detector_specs()
        injected = frame[TARGET_COL].copy()
        injected.iloc[100:112] += 20

        _, details = injection.run_detectors(frame, injected, specs)

        self.assertEqual(
            {name: detail["model_family"] for name, detail in details.items()},
            {name: spec.family for name, spec in specs.items()},
        )
        self.assertTrue(all(detail["status"] == "ok" for detail in details.values()))

        windows = pd.DataFrame(
            [
                {
                    "window_id": "fixture",
                    "scheme": "fixture",
                    "status": "ok",
                    "train_start_utc": frame.index[0],
                    "train_end_utc": frame.index[167],
                    "eval_start_utc": frame.index[168],
                    "eval_end_utc": frame.index[191],
                }
            ]
        )
        flags, summary = evaluation.rolling_origin_evaluation(
            frame,
            specs,
            windows,
            run_id="fixture",
            data_cutoff_utc=frame.index.max(),
        )

        families = summary.set_index("detector")["model_family"].to_dict()
        self.assertEqual(families, {name: spec.family for name, spec in specs.items()})
        self.assertTrue((summary["fit_status"] == "ok").all())
        self.assertTrue((summary["eval_scored_hours"] > 0).all())
        self.assertIn("sarimax_model_family", flags.columns)
