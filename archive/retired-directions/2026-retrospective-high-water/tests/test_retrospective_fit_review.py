"""Checks for matched-support and joint-block descriptive diagnostics."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/52_review_retrospective_fit.py"
spec = importlib.util.spec_from_file_location("retrospective_review", SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def test_support_is_calculated_within_each_matched_stratum():
    controls = pd.DataFrame(
        {
            "stratum": ["a", "a", "b", "b"],
            "rain_1_24_mm": [0.0, 2.0, 10.0, 12.0],
            "rain_25_72_mm": [1.0, 3.0, 0.0, 1.0],
        }
    )
    cases = pd.DataFrame(
        {
            "stratum": ["a", "b"],
            "rain_1_24_mm": [3.0, 11.0],
            "rain_25_72_mm": [2.0, 2.0],
        }
    )
    supported = review.overlap(cases, controls)
    assert supported.above_control_max_rain_1_24_mm.tolist() == [True, False]
    assert supported.above_control_max_rain_25_72_mm.tolist() == [False, True]
