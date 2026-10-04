"""Protect exact issue-time weather alignment in the bounded weather check."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location(
    "weather_increment", ROOT / "scripts/59_test_atmospheric_increment.py"
)
increment = module_from_spec(spec)
spec.loader.exec_module(increment)


def test_weather_join_requires_exact_issue_hour_and_site():
    issue = pd.Timestamp("2020-01-01 06:00", tz="UTC")
    decisions = pd.DataFrame({"decision_id": ["d1"], "issue_utc": [issue], "site": ["Gulp"]})
    weather = pd.DataFrame(
        {
            "timestamp_utc": [issue],
            "watercourse": ["Gulp"],
            "pressure_change_6h_hpa": [-2.0],
            "relative_humidity_pct": [89.0],
        }
    )
    joined = increment.attach_issue_weather(decisions, weather)
    assert joined.pressure_change_6h_hpa.iloc[0] == -2.0
    future_only = weather.assign(timestamp_utc=issue + pd.Timedelta(hours=1))
    with pytest.raises(ValueError, match="Incomplete issue-time weather"):
        increment.attach_issue_weather(decisions, future_only)


def test_within_decision_ranking_excludes_uniform_outcomes():
    frame = pd.DataFrame(
        {
            "decision_id": ["mixed", "mixed", "uniform", "uniform"],
            "year": [2020] * 4,
            "high_next_24h": [1, 0, 0, 0],
            "p_rain_plus_flow": [0.8, 0.2, 0.1, 0.2],
            "p_plus_pressure_change": [0.2, 0.8, 0.1, 0.2],
            "p_plus_humidity": [0.8, 0.2, 0.1, 0.2],
            "p_plus_both": [0.8, 0.2, 0.1, 0.2],
        }
    )
    ranks = increment.within_decision_ranks(frame)
    assert ranks.decision_id.tolist() == ["mixed"]
    assert ranks.rank_rain_plus_flow.iloc[0] == 1.0
    assert ranks.rank_plus_pressure_change.iloc[0] == 0.0
