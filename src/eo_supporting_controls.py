"""Preparation helpers for the separately scheduled supporting EO analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd


def antecedent_state(times, values, issues):
    """Latest *strictly earlier* hourly state, with age and missingness retained.

    Input values must already be catchment-area aggregated physical fields.
    This retrospective timestamp rule does not assert historical release time.
    No carry across missing source hours: absence at the requested hour stays NaN.
    """
    times = pd.DatetimeIndex(pd.to_datetime(times, utc=True))
    issues = pd.DatetimeIndex(pd.to_datetime(issues, utc=True))
    if times.has_duplicates or not times.is_monotonic_increasing:
        raise ValueError("Unique increasing source timestamps required")
    x = np.asarray(values, float)
    if x.ndim != 2 or len(x) != len(times):
        raise ValueError("Expected source-hour by physical-field values")
    target = issues.ceil("h") - pd.Timedelta(hours=1)
    position = times.get_indexer(target)
    result = np.full((len(issues), x.shape[1]), np.nan)
    age = np.full(len(issues), np.nan)
    valid = position >= 0
    result[valid] = x[position[valid]]
    age[valid] = (issues[valid] - target[valid]).total_seconds() / 3600
    return result, age


def saved_combined_profiles(groups):
    """Select saved definitions, never redraw network subsets or missing masks."""
    names = ("network4_schedule6_no_maas", "network4_block12_50pct_no_maas")
    result = []
    for name in names:
        matches = [g for g in groups if g["name"] == name]
        if len(matches) != 1:
            raise ValueError(f"Expected one saved definition: {name}")
        result.append(matches[0])
    return result
