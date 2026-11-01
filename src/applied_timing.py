"""Retrospective acquisition context, preserving measured versus display data."""

import numpy as np
import pandas as pd


def acquisition_context(frame, when, start, end):
    """Use declared hour-end UTC series. No invented delivery or flood threshold.

    Peak timing is known only within the stated complete review window; it is
    not the time of maximum inundation. Interpolated display data stay separate.
    """
    when, start, end = (pd.Timestamp(t) for t in [when, start, end])
    if any(t.tzinfo is None for t in [when, start, end]) or frame.index.tz is None:
        raise ValueError("Explicit timezone required")
    if not start <= when <= end or not frame.index.is_unique:
        raise ValueError("Acquisition outside window or duplicate hourly source")
    index = pd.date_range(start.ceil("h"), end.floor("h"), freq="h")
    clock = when.ceil("h")
    result = dict(
        acquisition_utc=when.isoformat(),
        containing_hour_end_utc=clock.isoformat(),
        window_start=start.isoformat(),
        window_end=end.isoformat(),
        convention="Retrospective hour-end averages; not a live issue clock or maximum flood extent",
    )
    for column, name in [("q_strict", "measured"), ("q_display", "display_proxy")]:
        values = frame[column].reindex(index)
        current = values.get(clock, np.nan)
        previous = values.get(clock - pd.Timedelta(hours=1), np.nan)
        complete = bool(len(values) and np.isfinite(values).all())
        delta = (
            float(current - previous) if np.isfinite(current) and np.isfinite(previous) else None
        )
        peak = values.idxmax() if complete else None
        result[name] = dict(
            known_hours=int(np.isfinite(values).sum()),
            expected_hours=len(values),
            window_complete=complete,
            value=float(current) if np.isfinite(current) else None,
            preceding_hour_change=delta,
            local_trend="unknown"
            if delta is None
            else "rising"
            if delta > 0
            else "falling"
            if delta < 0
            else "unchanged",
            window_peak_utc=peak.isoformat() if peak is not None else None,
            acquisition_hours_from_window_peak=(when - peak).total_seconds() / 3600
            if peak is not None
            else None,
        )
    result["measured_peak_verified_in_window"] = result["measured"]["window_complete"]
    result["display_caveat"] = (
        "May include interpolated readings; cannot verify measured peak or instantaneous inundation"
    )
    return result
