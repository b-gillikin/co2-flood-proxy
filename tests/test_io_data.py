"""Small offline checks for source loaders."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io_data import load_knmi, load_rivm


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class LoaderTests(unittest.TestCase):
    """Verify Week 4 loaders against tiny cached payloads."""

    def test_load_knmi_csv_sample(self):
        frame = load_knmi(raw_dir=FIXTURES, frequency="h", station="380")

        self.assertEqual(len(frame), 3)
        self.assertIn("knmi_temperature_c", frame.columns)
        self.assertIn("knmi_pressure_hpa", frame.columns)
        self.assertAlmostEqual(frame["knmi_temperature_c"].iloc[0], 12.3)
        self.assertAlmostEqual(frame["knmi_pressure_hpa"].iloc[0], 1012.3)

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


if __name__ == "__main__":
    unittest.main()
