"""Offline checks for the weekly readiness record."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import pandas as pd

weekly = importlib.import_module("scripts.14_weekly_readiness")


class WeeklyReadinessTests(unittest.TestCase):
    def test_build_status_handles_pre_restoration_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis.csv"
            index = pd.date_range("2026-04-01", periods=24, freq="h", tz="UTC")
            pd.DataFrame({"timestamp_utc": index, "iot_co2_ppm": [450.0] * len(index)}).to_csv(
                analysis, index=False
            )

            status = weekly.build_status(
                analysis_path=analysis,
                knmi_path=root / "missing_knmi.csv",
                groundwater_path=root / "missing_groundwater.csv",
                windows_path=root / "missing_windows.csv",
                refresh_date="2026-07-12",
            )

            self.assertEqual(status["post_restoration_block_days"], 0.0)
            self.assertIsNone(status["knmi_06380_overlap"])

    def test_markdown_row_handles_pending_knmi_overlap(self):
        row = weekly.markdown_row(
            {
                "refresh_date": "2026-07-12",
                "iot_latest_utc": None,
                "co2_observed_share": None,
                "longest_block_hours": 0,
                "post_restoration_block_days": 0.0,
                "knmi_06380_overlap": None,
                "groundwater_paired_days": 0,
                "usable_official_windows": 0,
            }
        )
        self.assertIn("pending", row)

    def test_append_plan_row_replaces_same_date(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.md"
            path.write_text(
                "| Refresh date | Notes |\n"
                "| --- | --- |\n"
                "| 2026-07-12 | old |\n"
                f"{weekly.LOG_MARKER}\n",
                encoding="utf-8",
            )

            weekly.append_plan_row(path, "| 2026-07-12 | new |", "2026-07-12")
            text = path.read_text(encoding="utf-8")

            self.assertNotIn("| 2026-07-12 | old |", text)
            self.assertEqual(text.count("| 2026-07-12 |"), 1)
            self.assertLess(text.index("| 2026-07-12 | new |"), text.index(weekly.LOG_MARKER))


if __name__ == "__main__":
    unittest.main()
