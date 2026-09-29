"""Scientific boundary checks for the first real-data event study runner."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


review = load_script("46_review_events")
analysis = load_script("47_run_real_event_study")


def one_era(gauge="G1"):
    return pd.DataFrame(
        [
            {
                "gauge": gauge,
                "era_id": "A",
                "valid_from_utc": "2010-01-01T00:00:00Z",
                "valid_to_utc": "",
                "domain_min_m3s": 0.0,
                "domain_max_m3s": 5.0,
            }
        ]
    )


def test_peak_outside_domain_does_not_erase_exact_onset():
    index = pd.date_range("2020-01-01", periods=110, freq="h", tz="UTC")
    discharge = pd.Series(1.0, index=index)
    discharge.iloc[90:92] = [2.0, 8.0]
    eras = pd.Series("A", index=index)
    admissible = pd.Series(True, index=index)
    threshold = pd.Series(1.5, index=index)
    row = SimpleNamespace(onset_utc=index[90], last_crossing_utc=index[90], onset_censored=False)
    result = review.inspect_episode(
        discharge, eras, admissible, threshold, one_era(), row, "pending_range_check"
    )
    assert result["onset_within_domain"]
    assert result["peak_outside_rating_domain"]
    assert result["review_decision"] == "include_exact"


def test_lag_one_excludes_outcome_hour_rainfall():
    index = pd.date_range("2020-01-01", periods=130, freq="h", tz="UTC")
    discharge = pd.DataFrame({"G1": np.ones(len(index))}, index=index)
    discharge.iloc[90, 0] = 10.0
    rain = pd.DataFrame({"River": np.zeros(len(index))}, index=index)
    rain.iloc[89, 0] = 2.0
    rain.iloc[90, 0] = 10.0
    gauges = pd.DataFrame([{"gauge": "G1", "watercourse": "River"}])
    rows, cross, _, basis = analysis.make_rows(discharge, rain, gauges, one_era(), None)
    onset = rows.onset.to_numpy().astype(bool)
    assert onset.sum() == 1
    np.testing.assert_allclose(cross[onset][0], 2.0 * basis[0])


def test_undefined_secondary_median_uses_full_admissible_range():
    draws = pd.DataFrame({"pressure_median_lag": [np.nan] * 95 + [10.0] * 5})
    row = analysis.scalar_intervals("weather", {"pressure_median_lag": np.nan}, draws, max_lag=168)[
        0
    ]
    assert row["lower"] == 1.0
    assert row["upper"] == 168.0
    assert row["estimable_share"] == 0.05
