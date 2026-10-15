"""Checks for the one-email-per-day Azure notification design."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kerkrade_data"))

from daily_summary import build_message


class DailySummaryTests(unittest.TestCase):
    def test_message_combines_weather_and_iot_once(self):
        message = build_message(
            now=datetime(2026, 7, 13, 21, 5, tzinfo=timezone.utc),
            sender="sender@example.test",
            recipients=["reader@example.test"],
            hourly_weather_summary="WEATHER SUMMARY",
            iot_summary="IOT SUMMARY",
        )

        self.assertEqual(
            message["content"]["subject"],
            "Kerkrade daily data summary — 2026-07-13 UTC",
        )
        self.assertEqual(message["content"]["plainText"].count("WEATHER SUMMARY"), 1)
        self.assertEqual(message["content"]["plainText"].count("IOT SUMMARY"), 1)

    def test_timer_runs_once_daily_at_2105_utc(self):
        binding_path = ROOT / "kerkrade_data/daily_summary_email_timer/function.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))["bindings"][0]
        self.assertEqual(binding["type"], "timerTrigger")
        self.assertEqual(binding["schedule"], "0 5 21 * * *")

    def test_blob_email_trigger_has_been_removed(self):
        self.assertFalse((ROOT / "kerkrade_data/blob_created_email_alert/function.json").exists())


if __name__ == "__main__":
    unittest.main()
