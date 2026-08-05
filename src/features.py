"""Feature engineering helpers for the Chapter 1 CO2 analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


def pressure_deltas(df, lags=(1, 3, 6, 12, 24), pressure_col="pressure"):
    """Add pressure-tendency columns for the requested hourly lags.

    Parameters
    ----------
    df:
        DataFrame-like object with a pressure column.
    lags:
        Hourly lags to difference against.
    pressure_col:
        Column containing atmospheric pressure.
    """
    out = df.copy()
    for lag in lags:
        out[f"delta_pressure_{lag}h"] = out[pressure_col].diff(lag)
    return out


def antecedent_precipitation_index(precip, days=14, decay=0.85, hours_per_day=24):
    """Compute hourly antecedent rain with day-scaled exponential decay.

    Each lagged hour receives the weight for its lagged day: ``decay`` for the
    previous 24 hours, ``decay**2`` for the 24 before that, and so on through
    ``days``. Defaults of d=0.85 over 14 days are the values the distributed-lag
    test was specified with.
    """
    precip = pd.Series(precip).fillna(0).astype(float)
    api = pd.Series(0.0, index=precip.index)
    for lag_hour in range(1, days * hours_per_day + 1):
        lag_day = int(np.ceil(lag_hour / hours_per_day))
        api = api + (decay**lag_day) * precip.shift(lag_hour).fillna(0)
    return api
