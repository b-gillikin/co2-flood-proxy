"""Small helpers for the pre-high-water event study.

These functions define event grouping, quiet controls and pressure adjustment.
They contain no chapter-specific model search or reporting machinery.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def episode_table(series, threshold, merge_hours=72):
    """Describe observed upward crossings joined by the fixed single-linkage rule."""
    previous = series.shift(1)
    crossing = series.gt(threshold) & previous.le(threshold)
    onsets = series.index[crossing & series.notna() & previous.notna()]
    columns = ["onset_utc", "last_crossing_utc", "n_crossings", "chain_span_hours"]
    if not len(onsets):
        return pd.DataFrame(columns=columns)

    rows = []
    first = previous_onset = onsets[0]
    n_crossings = 1
    gap = pd.Timedelta(hours=merge_hours)
    for onset in onsets[1:]:
        if onset - previous_onset > gap:
            rows.append(
                {
                    "onset_utc": first,
                    "last_crossing_utc": previous_onset,
                    "n_crossings": n_crossings,
                    "chain_span_hours": (previous_onset - first) / pd.Timedelta(hours=1),
                }
            )
            first = onset
            n_crossings = 0
        n_crossings += 1
        previous_onset = onset
    rows.append(
        {
            "onset_utc": first,
            "last_crossing_utc": previous_onset,
            "n_crossings": n_crossings,
            "chain_span_hours": (previous_onset - first) / pd.Timedelta(hours=1),
        }
    )
    return pd.DataFrame(rows, columns=columns)


def episode_onsets(series, threshold, merge_hours=72):
    """Return episode starts while preserving gap-honest crossing detection."""
    episodes = episode_table(series, threshold, merge_hours)
    return pd.DatetimeIndex(episodes.onset_utc)


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
    heldout_block=None,
    n_controls=5,
    minimum_controls=3,
    exclusion_days=7,
):
    """Choose deterministic season/hour-matched times away from high water.

    Candidate controls share the event's calendar month and UTC hour. Nearest
    eligible times are selected deterministically, with timestamp as a tie-break.
    """
    index = pd.DatetimeIndex(index).sort_values().unique()
    candidates = index[(index.month == event_time.month) & (index.hour == event_time.hour)]
    if heldout_block is not None:
        block_start, block_end = map(pd.Timestamp, heldout_block)
        if block_start >= block_end:
            raise ValueError("Held-out block start must precede its end")
        inside = (candidates >= block_start) & (candidates < block_end)
        event_is_heldout = block_start <= event_time < block_end
        candidates = candidates[inside if event_is_heldout else ~inside]
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
    selected = pd.DatetimeIndex(order[:n_controls])
    return selected if len(selected) >= minimum_controls else pd.DatetimeIndex([])


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
    fold_watercourse_col="fold_heldout_watercourse",
    fold_block_col="fold_heldout_time_block",
    watercourse_col="watercourse",
    block_col="time_block",
    signal_col="signal",
    value_col="contrast",
    watercourses=None,
    time_blocks=None,
    signals=None,
    minimum_heldout_events=3,
):
    """Summarise contrasts that were estimated separately inside each fold.

    The input carries the fold that produced each contrast. This prevents a
    globally thresholded or scaled contrast table from entering a protocol that
    requires fold-specific events, controls and standardisation.
    """
    required = {
        fold_watercourse_col,
        fold_block_col,
        watercourse_col,
        block_col,
        signal_col,
        value_col,
    }
    missing = required - set(contrasts)
    if missing:
        raise ValueError(f"Missing contrast columns: {sorted(missing)}")

    frame = contrasts.copy()
    watercourses = sorted(
        frame[fold_watercourse_col].dropna().unique() if watercourses is None else watercourses
    )
    time_blocks = sorted(
        frame[fold_block_col].dropna().unique() if time_blocks is None else time_blocks
    )
    signals = sorted(frame[signal_col].dropna().unique() if signals is None else signals)
    observed = frame.dropna(subset=[value_col])
    rows = []
    for receiver in watercourses:
        for block in time_blocks:
            fold = observed[
                observed[fold_watercourse_col].eq(receiver) & observed[fold_block_col].eq(block)
            ]
            held = fold[fold[watercourse_col].eq(receiver) & fold[block_col].eq(block)]
            reference = fold[fold[watercourse_col].ne(receiver) & fold[block_col].ne(block)]
            for signal in signals:
                held_signal = held[held[signal_col].eq(signal)]
                reference_signal = reference[reference[signal_col].eq(signal)]
                reference_watercourses = reference_signal.groupby(watercourse_col)[
                    value_col
                ].median()
                n_heldout = len(held_signal)
                fold_eligible = n_heldout >= minimum_heldout_events
                if held_signal.empty:
                    status = "no_heldout_events"
                elif not fold_eligible:
                    status = "sparse_heldout_events"
                elif reference_watercourses.empty:
                    status = "no_reference_events"
                else:
                    status = "eligible"

                expected = (
                    reference_watercourses.median() if len(reference_watercourses) else np.nan
                )
                heldout = held_signal[value_col].median() if n_heldout else np.nan
                expected_sign = int(np.sign(expected)) if np.isfinite(expected) else pd.NA
                heldout_sign = int(np.sign(heldout)) if np.isfinite(heldout) else pd.NA
                concordant = pd.NA
                if not pd.isna(expected_sign) and not pd.isna(heldout_sign):
                    concordant = pd.NA if expected_sign == 0 else heldout_sign == expected_sign
                rows.append(
                    {
                        "heldout_watercourse": receiver,
                        "heldout_time_block": block,
                        "signal": signal,
                        "reference_network_median": expected,
                        "heldout_median": heldout,
                        "expected_sign": expected_sign,
                        "heldout_sign": heldout_sign,
                        "sign_concordant": concordant,
                        "magnitude_difference": heldout - expected,
                        "n_reference_watercourses": len(reference_watercourses),
                        "n_reference_events": len(reference_signal),
                        "n_heldout_events": n_heldout,
                        "minimum_heldout_events": minimum_heldout_events,
                        "fold_eligible": fold_eligible and len(reference_watercourses) > 0,
                        "fold_status": status,
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
