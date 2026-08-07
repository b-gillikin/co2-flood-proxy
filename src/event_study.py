"""Small helpers for the pre-high-water event study.

These functions define event grouping, quiet controls and pressure adjustment.
They contain no chapter-specific model search or reporting machinery.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def episode_onsets(series, threshold, merge_hours=72):
    """Find observed upward crossings and merge consecutive re-crossings."""
    previous = series.shift(1)
    crossing = series.gt(threshold) & previous.le(threshold)
    onsets = series.index[crossing & series.notna() & previous.notna()]
    if len(onsets) < 2:
        return pd.DatetimeIndex(onsets)

    keep = [onsets[0]]
    previous_onset = onsets[0]
    gap = pd.Timedelta(hours=merge_hours)
    for onset in onsets[1:]:
        if onset - previous_onset > gap:
            keep.append(onset)
        previous_onset = onset
    return pd.DatetimeIndex(keep)


def cluster_regional_storms(events, onset_col="onset_utc", max_gap_hours=72):
    """Assign chronologically adjacent watercourse events to regional storms."""
    if events.empty:
        return events.assign(storm_id=pd.Series(dtype="string"))
    out = events.sort_values(onset_col).reset_index(drop=True).copy()
    gap = out[onset_col].diff().gt(pd.Timedelta(hours=max_gap_hours))
    gap.iloc[0] = True
    number = gap.cumsum().astype(int)
    out["storm_id"] = number.map(lambda value: f"storm_{value:04d}")
    return out


def exact_onset_events(events, onset_col="onset_utc", censored_col="onset_censored"):
    """Return events eligible for calculations requiring an exact onset."""
    if events.empty:
        return events.copy()
    censored = events[censored_col].fillna(False) if censored_col in events else False
    return events.loc[events[onset_col].notna() & ~censored].copy()


def quiet_control_times(
    index,
    event_time,
    receiver_exceedances,
    regional_storms,
    available=None,
    n_controls=5,
    exclusion_days=7,
):
    """Choose deterministic season/hour-matched times away from high water.

    Candidate controls share the event's calendar month and UTC hour. Nearest
    eligible times are selected deterministically, with timestamp as a tie-break.
    """
    index = pd.DatetimeIndex(index).sort_values().unique()
    candidates = index[(index.month == event_time.month) & (index.hour == event_time.hour)]
    if available is not None:
        valid = pd.Series(available, index=getattr(available, "index", index))
        is_available = valid.reindex(candidates).fillna(False).astype(bool)
        candidates = candidates[is_available.to_numpy()]

    exclusion = pd.Timedelta(days=exclusion_days)
    forbidden = pd.DatetimeIndex(receiver_exceedances).append(pd.DatetimeIndex(regional_storms))
    if len(forbidden):
        candidate_ns = candidates.to_numpy(dtype="datetime64[ns]").astype("int64")
        forbidden_ns = forbidden.to_numpy(dtype="datetime64[ns]").astype("int64")
        distance = np.abs(candidate_ns[:, None] - forbidden_ns[None, :]).min(axis=1)
        candidates = candidates[distance > exclusion.value]

    candidates = candidates[candidates != event_time]
    order = sorted(candidates, key=lambda time: (abs(time - event_time), time))
    return pd.DatetimeIndex(order[:n_controls])


def robust_standardize(values, reference):
    """Standardize with a reference median/MAD and a standard-deviation fallback."""
    values = pd.Series(values, copy=False, dtype=float)
    reference = pd.Series(reference, copy=False, dtype=float).dropna()
    median = reference.median()
    scale = (reference - median).abs().median()
    if not np.isfinite(scale) or scale == 0:
        scale = reference.std(ddof=0)
    if not np.isfinite(scale) or scale == 0:
        return pd.Series(np.nan, index=values.index)
    return (values - median) / scale


def heldout_signal_transfer(
    contrasts,
    watercourse_col="watercourse",
    block_col="time_block",
    signal_col="signal",
    value_col="contrast",
):
    """Compare each held-out contrast with a direction learned elsewhere.

    For each watercourse-by-period test fold, the expected direction is the
    median of reference-watercourse medians. The reference excludes the held-out
    watercourse and every event in the held-out period.
    """
    required = {watercourse_col, block_col, signal_col, value_col}
    missing = required - set(contrasts)
    if missing:
        raise ValueError(f"Missing contrast columns: {sorted(missing)}")

    frame = contrasts.dropna(subset=[value_col]).copy()
    rows = []
    for receiver in sorted(frame[watercourse_col].unique()):
        for block in sorted(frame[block_col].unique()):
            held = frame[frame[watercourse_col].eq(receiver) & frame[block_col].eq(block)]
            reference = frame[frame[watercourse_col].ne(receiver) & frame[block_col].ne(block)]
            for signal in sorted(held[signal_col].unique()):
                held_signal = held[held[signal_col].eq(signal)]
                reference_signal = reference[reference[signal_col].eq(signal)]
                reference_watercourses = reference_signal.groupby(watercourse_col)[
                    value_col
                ].median()
                if held_signal.empty or reference_watercourses.empty:
                    continue

                expected = reference_watercourses.median()
                observed = held_signal[value_col].median()
                expected_sign = int(np.sign(expected))
                observed_sign = int(np.sign(observed))
                concordant = pd.NA if expected_sign == 0 else observed_sign == expected_sign
                rows.append(
                    {
                        "heldout_watercourse": receiver,
                        "heldout_time_block": block,
                        "signal": signal,
                        "reference_network_median": expected,
                        "heldout_median": observed,
                        "expected_sign": expected_sign,
                        "heldout_sign": observed_sign,
                        "sign_concordant": concordant,
                        "magnitude_difference": observed - expected,
                        "n_reference_watercourses": len(reference_watercourses),
                        "n_reference_events": len(reference_signal),
                        "n_heldout_events": len(held_signal),
                    }
                )
    return pd.DataFrame(rows)


def pressure_residuals(
    frame,
    calibration_mask,
    co2_col="iot_co2_ppm",
    pressure_col="iot_air_pressure_hpa",
    lags=(1, 3, 6, 12, 24),
):
    """Fit a pressure-only baseline on quiet calibration hours and return residuals."""
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Pressure baseline requires a sorted, unique hourly index")

    features = pd.DataFrame({"pressure": frame[pressure_col]}, index=frame.index)
    for lag in lags:
        complete = frame[pressure_col].notna().rolling(lag + 1, min_periods=lag + 1).sum()
        elapsed = frame.index.to_series().diff(lag)
        delta = frame[pressure_col] - frame[pressure_col].shift(lag)
        observed_span = complete.eq(lag + 1) & elapsed.eq(pd.Timedelta(hours=lag))
        features[f"pressure_change_{lag}h"] = delta.where(observed_span)

    data = features.join(frame[co2_col].rename("co2")).dropna()
    calibration = data.loc[
        pd.Series(calibration_mask, index=frame.index).reindex(data.index).eq(True)
    ]
    if len(calibration) < 100:
        raise ValueError("Pressure baseline needs at least 100 complete quiet calibration hours")

    model = LinearRegression().fit(calibration[features.columns], calibration.co2)
    residual = pd.Series(np.nan, index=frame.index, name="co2_pressure_residual_ppm")
    residual.loc[data.index] = data.co2 - model.predict(data[features.columns])
    return residual


def pressure_residuals_by_era(frame, quiet_mask, era_col="sensor_era", **kwargs):
    """Pressure-adjust and quiet-period-standardize CO2 within each sensor era."""
    residual = pd.Series(np.nan, index=frame.index, name="co2_pressure_residual_mad")
    for _, era in frame.groupby(era_col, sort=True):
        era = era.sort_index()
        era_quiet = pd.Series(quiet_mask, index=frame.index).reindex(era.index).eq(True)
        raw = pressure_residuals(era, era_quiet, **kwargs)
        residual.loc[era.index] = robust_standardize(raw, raw.loc[era_quiet])
    return residual


def contiguous_time_blocks(index, n_blocks=5):
    """Split a UTC record into equal-duration, non-overlapping time blocks."""
    index = pd.DatetimeIndex(index).sort_values()
    if index.empty:
        return []
    start = index.min()
    end = index.max() + pd.Timedelta(hours=1)
    boundaries = pd.date_range(start, end, periods=n_blocks + 1)
    return list(zip(boundaries[:-1], boundaries[1:], strict=True))
