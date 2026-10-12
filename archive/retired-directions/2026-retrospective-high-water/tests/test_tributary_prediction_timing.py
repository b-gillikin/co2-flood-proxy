"""Protect the issue-time boundary in the retrospective prediction test."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("prediction", ROOT / "scripts/58_test_tributary_prediction.py")
prediction = module_from_spec(spec)
spec.loader.exec_module(prediction)


def test_rain_trigger_and_features_do_not_use_future_rainfall():
    times = pd.date_range("2020-07-01", periods=40, freq="h", tz="UTC")
    rain = pd.DataFrame(0.0, index=times, columns=prediction.core.SITES)
    rain.iloc[0, 0] = 2.0
    states = {}
    for site in prediction.core.SITES:
        state = pd.DataFrame({"q": 1.0, "p99": 10.0, "valid": True}, index=times)
        states[site] = state
    states[prediction.core.SITES[0]].loc[times[6], "q"] = 11.0
    first = prediction.build_decisions(rain, states)
    changed = rain.copy()
    changed.iloc[6:30] = 99.0
    second = prediction.build_decisions(changed, states)
    left = first.loc[first.issue_utc.eq(times[5])].sort_values("site").reset_index(drop=True)
    right = second.loc[second.issue_utc.eq(times[5])].sort_values("site").reset_index(drop=True)
    assert len(left) == len(prediction.core.SITES)
    assert left.issue_utc.eq(times[5]).all()
    assert left.target_end_utc.eq(times[29]).all()
    assert left.high_next_24h.sum() == 1
    for column in prediction.RAIN_FEATURES:
        assert left[column].equals(right[column])


def test_forward_fit_uses_only_prior_years():
    rng = np.random.default_rng(7)
    rows = []
    for year in range(2010, 2015):
        for item in range(30):
            site = prediction.core.SITES[item % len(prediction.core.SITES)]
            rows.append(
                {
                    "decision_id": f"{year}_{item}",
                    "year": year,
                    "target_end_utc": pd.Timestamp(f"{year}-06-01", tz="UTC"),
                    "high_next_24h": item % 5 == 0,
                    "site": site,
                    "log1p_local_rain_6h": rng.uniform(),
                    "log1p_regional_max_rain_6h": rng.uniform(),
                    "n_sites_rain_2mm_6h": item % 6,
                    "warm": item % 2,
                    "issue_q_over_p99": rng.uniform(),
                    **{name: int(name == f"site_{site}") for name in prediction.SITE_DUMMIES},
                }
            )
    table = pd.DataFrame(rows)
    spill = table.iloc[0].copy()
    spill["year"] = 2013
    spill["target_end_utc"] = pd.Timestamp("2014-01-01 05:00", tz="UTC")
    table = pd.concat([table, pd.DataFrame([spill])], ignore_index=True)
    actual = prediction.forward_predictions(table)
    assert set(actual.year) == {2014}
    assert actual.training_last_year.eq(2013).all()
    assert actual.training_site_rows.eq(120).all()
    assert actual.training_positive_site_rows.eq(24).all()


def test_flagged_future_onset_removes_whole_decision_window():
    base = pd.Timestamp("2021-07-01", tz="UTC")
    decisions = pd.DataFrame(
        {
            "decision_id": ["first", "first", "second"],
            "issue_utc": [base, base, base + pd.Timedelta(days=2)],
            "target_end_utc": [
                base + pd.Timedelta(days=1),
                base + pd.Timedelta(days=1),
                base + pd.Timedelta(days=3),
            ],
        }
    )
    review = pd.DataFrame(
        {
            "onset_utc": [base + pd.Timedelta(hours=2)],
            "measurement_concern": [True],
            "review_decision": ["include_exact"],
        }
    )
    clean, removed = prediction.exclude_reviewed_measurement_concerns(decisions, review)
    assert removed == 1
    assert clean.decision_id.tolist() == ["second"]
