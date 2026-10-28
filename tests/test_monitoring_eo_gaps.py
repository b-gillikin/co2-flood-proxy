"""Causal source-clock checks for the targeted EO addition inventory."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

SPEC = importlib.util.spec_from_file_location(
    "eo_gaps", Path(__file__).resolve().parents[1] / "scripts/151_prepare_monitoring_eo_gaps.py"
)
GAPS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GAPS)


def test_slow_episode_uses_first_known_qualification_not_fixed_six_hours():
    dates = pd.date_range("2020-05-01", periods=18, freq="h", tz="UTC")
    rain = pd.DataFrame({"a": np.ones(18)}, index=dates)
    assert GAPS.observed_qualification(rain, dates[0], dates[-1]) == dates[9]
    changed = rain.copy()
    changed.loc[dates[10] :] = 999
    assert GAPS.observed_qualification(changed, dates[0], dates[-1]) == dates[9]


def test_missing_prefix_does_not_become_a_known_cumulative_total():
    dates = pd.date_range("2020-05-01", periods=18, freq="h", tz="UTC")
    rain = pd.DataFrame({"a": np.ones(18) * 2, "b": np.ones(18)}, index=dates)
    rain.loc[dates[1], "a"] = np.nan
    # The known second catchment can qualify; do not silently fill the first one.
    assert GAPS.observed_qualification(rain, dates[0], dates[-1]) == dates[9]
