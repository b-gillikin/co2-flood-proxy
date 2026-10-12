"""Check the two descriptive rainfall windows against explicit lag sums."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/50_audit_observed_rainfall_histories.py"
spec = importlib.util.spec_from_file_location("rainfall_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
FOLLOWUP = SCRIPT.with_name("51_fit_observed_window_followup.py")
followup_spec = importlib.util.spec_from_file_location("rainfall_followup", FOLLOWUP)
followup = importlib.util.module_from_spec(followup_spec)
followup_spec.loader.exec_module(followup)


def test_windows_exclude_onset_hour_and_require_all_lags():
    rain = pd.Series(np.arange(80, dtype=float))
    recent, earlier = audit.rainfall_windows(rain)
    assert np.isnan(recent.iloc[23])
    assert np.isnan(earlier.iloc[71])
    assert recent.iloc[72] == rain.iloc[48:72].sum()
    assert earlier.iloc[72] == rain.iloc[0:48].sum()
    rain.iloc[20] = np.nan
    recent, earlier = audit.rainfall_windows(rain)
    assert np.isnan(earlier.iloc[72])
    assert np.isfinite(recent.iloc[72])


def test_followup_design_uses_separate_seasonal_windows():
    frame = pd.DataFrame(
        {"warm": [True, False], "rain_1_24_mm": [20.0, 30.0], "rain_25_72_mm": [5.0, 10.0]}
    )
    np.testing.assert_allclose(
        followup.design_matrix(frame),
        [[2.0, 0.5, 0.0, 0.0], [0.0, 0.0, 3.0, 1.0]],
    )
