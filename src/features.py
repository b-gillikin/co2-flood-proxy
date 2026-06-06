"""Feature engineering helpers for the Chapter 1 CO2 analysis."""

from __future__ import annotations


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

