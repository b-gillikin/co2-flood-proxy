"""Small evaluation helpers for discharge-derived labels.

The chapter uses discharge as a soft hydrological-state proxy rather than as a
hard flood label. These helpers keep that logic in one place so analysis
scripts can stay focused on data joins, plots, and model results.
"""

from __future__ import annotations

import pandas as pd

from src.textutils import source_token


def discharge_columns(discharge):
    """Return the discharge value columns in a wide hourly frame."""
    return [column for column in discharge.columns if column.startswith("discharge_")]


def discharge_thresholds(discharge, quantiles=(0.90, 0.95, 0.99)):
    """Compute per-gauge percentile thresholds from available observations."""
    rows = []

    for column in discharge_columns(discharge):
        series = discharge[column].dropna()
        for quantile in quantiles:
            rows.append(
                {
                    "source": column,
                    "quantile": quantile,
                    "threshold_m3s": series.quantile(quantile),
                    "n_observations": len(series),
                    "source_min_timestamp_utc": series.index.min(),
                    "source_max_timestamp_utc": series.index.max(),
                }
            )
    return pd.DataFrame(rows)


def sustained_exceedance_events(
    discharge,
    quantiles=(0.90, 0.95, 0.99),
    min_duration_hours=6,
    antecedent_windows=(24, 72, 168),
):
    """Build a catalogue of sustained discharge-threshold exceedance events.

    Each row represents one contiguous window where a gauge remains above a
    percentile threshold for at least ``min_duration_hours``. The event
    catalogue is intentionally descriptive: later modelling can choose whether
    to use event windows, antecedent summaries, or the hourly soft labels.
    """
    thresholds = discharge_thresholds(discharge, quantiles)
    events = []

    for row in thresholds.itertuples(index=False):
        # Keep the full hourly grid: dropping missing hours first would let a
        # "contiguous" exceedance silently bridge a coverage gap. A missing
        # hour inside a real event now splits it, which is the conservative
        # and time-honest reading.
        series = discharge[row.source]
        above = series >= row.threshold_m3s
        group_id = above.ne(above.shift(fill_value=False)).cumsum()

        for _, group in above.groupby(group_id):
            if not bool(group.iloc[0]):
                continue
            if len(group) < min_duration_hours:
                continue

            events.append(
                _summarize_exceedance_event(
                    series=series,
                    exceedance_index=group.index,
                    source=row.source,
                    quantile=row.quantile,
                    threshold=row.threshold_m3s,
                    antecedent_windows=antecedent_windows,
                )
            )

    event_frame = pd.DataFrame(events)
    if event_frame.empty:
        return event_frame

    event_frame = event_frame.sort_values(
        ["start_timestamp_utc", "source", "threshold_quantile"]
    ).reset_index(drop=True)
    event_frame.insert(
        0,
        "event_id",
        [
            f"evt_{idx + 1:04d}_{_discharge_token(row.source)}_p{int(row.threshold_quantile * 100)}"
            for idx, row in event_frame.iterrows()
        ],
    )
    return event_frame


def hourly_discharge_soft_labels(
    discharge,
    quantiles=(0.90, 0.95, 0.99),
    antecedent_windows=(24, 72, 168),
):
    """Build hourly current and antecedent discharge soft labels.

    Levels are ordinal: 0 below p90, 1 at/above p90, 2 at/above p95, and 3
    at/above p99 by default. Soft-label columns divide those levels by the
    maximum level so downstream models can use a 0..1 proxy if helpful.

    Hours with no discharge observation carry NaN labels: a gauge outage must
    not read as calm conditions. Antecedent columns summarize the observed
    hours in each window and are NaN only when the whole window is unobserved.
    """
    _assert_gapless_hourly(discharge.index)

    thresholds = discharge_thresholds(discharge, quantiles)
    labels = pd.DataFrame(index=discharge.index)

    quantile_scores = {quantile: idx + 1 for idx, quantile in enumerate(quantiles)}
    max_score = len(quantiles)

    for column in discharge_columns(discharge):
        source_thresholds = thresholds.loc[thresholds["source"] == column]
        scores = pd.Series(0.0, index=discharge.index)
        for row in source_thresholds.sort_values("quantile").itertuples(index=False):
            scores = scores.mask(
                discharge[column] >= row.threshold_m3s,
                quantile_scores[row.quantile],
            )
        scores = scores.mask(discharge[column].isna())

        token = _discharge_token(column)
        labels[f"{token}_current_level"] = scores
        labels[f"{token}_current_soft_label"] = scores / max_score

        for window in antecedent_windows:
            # The index is a gapless hourly grid (asserted above), so a
            # ``window``-row positional window is exactly the ``window``-hour
            # antecedent maximum used in the June plan.
            antecedent = scores.rolling(window=window, min_periods=1).max()
            labels[f"{token}_antecedent_{window}h_level"] = antecedent
            labels[f"{token}_antecedent_{window}h_soft_label"] = antecedent / max_score

    level_columns = [column for column in labels.columns if column.endswith("_level")]
    labels["any_current_level"] = labels[
        [column for column in level_columns if "_current_" in column]
    ].max(axis=1)
    labels["any_current_soft_label"] = labels["any_current_level"] / max_score

    for window in antecedent_windows:
        columns = [
            column for column in level_columns if column.endswith(f"_antecedent_{window}h_level")
        ]
        labels[f"any_antecedent_{window}h_level"] = labels[columns].max(axis=1)
        labels[f"any_antecedent_{window}h_soft_label"] = (
            labels[f"any_antecedent_{window}h_level"] / max_score
        )

    return labels


def annotate_event_overlap(events, iot_index=None, weather_index=None):
    """Add simple overlap counts with available IoT/weather hourly indexes."""
    out = events.copy()
    if out.empty:
        return out

    for name, index in (("iot", iot_index), ("weather", weather_index)):
        if index is None:
            continue
        counts = []
        for row in out.itertuples(index=False):
            mask = (index >= row.start_timestamp_utc) & (index <= row.end_timestamp_utc)
            counts.append(int(mask.sum()))
        out[f"{name}_overlap_hours"] = counts

    return out


def deduplicate_event_episodes(events):
    """Collapse overlapping gauge/quantile events into physical episodes.

    The event catalogue deliberately keeps one row per gauge and threshold
    quantile, so a single high-water episode can appear up to nine times.
    Paired statistical tests must not treat those rows as independent; this
    merges events whose [start, end] windows overlap or touch (across gauges
    and quantiles) into one episode row.
    """
    required = ["start_timestamp_utc", "end_timestamp_utc"]
    if events.empty:
        return pd.DataFrame(
            columns=[
                "episode_id",
                *required,
                "duration_hours",
                "n_source_events",
                "n_sources",
                "max_threshold_quantile",
            ]
        )

    ordered = events.sort_values("start_timestamp_utc")
    episodes = []
    current = None

    for row in ordered.itertuples(index=False):
        if current is not None and row.start_timestamp_utc <= current["end_timestamp_utc"]:
            current["end_timestamp_utc"] = max(current["end_timestamp_utc"], row.end_timestamp_utc)
            current["sources"].add(row.source)
            current["n_source_events"] += 1
            current["max_threshold_quantile"] = max(
                current["max_threshold_quantile"], row.threshold_quantile
            )
        else:
            if current is not None:
                episodes.append(current)
            current = {
                "start_timestamp_utc": row.start_timestamp_utc,
                "end_timestamp_utc": row.end_timestamp_utc,
                "sources": {row.source},
                "n_source_events": 1,
                "max_threshold_quantile": row.threshold_quantile,
            }
    episodes.append(current)

    out = pd.DataFrame(
        {
            "episode_id": [f"episode_{idx + 1:03d}" for idx in range(len(episodes))],
            "start_timestamp_utc": [episode["start_timestamp_utc"] for episode in episodes],
            "end_timestamp_utc": [episode["end_timestamp_utc"] for episode in episodes],
            "n_source_events": [episode["n_source_events"] for episode in episodes],
            "n_sources": [len(episode["sources"]) for episode in episodes],
            "max_threshold_quantile": [episode["max_threshold_quantile"] for episode in episodes],
        }
    )
    out["duration_hours"] = (
        (out["end_timestamp_utc"] - out["start_timestamp_utc"]) / pd.Timedelta(hours=1)
    ).astype(int) + 1
    return out


def combine_detector_flags(frames, detector_names):
    """Union per-detector flag frames onto one hourly grid.

    An hour a detector never scored (its complete-case rows differ) reads as
    "did not fire" rather than dropping the hour, so the ensemble record is the
    union of detector coverage instead of the intersection. ``detector_count``
    and ``all_three_anomaly`` are computed on that union.
    """
    detector_names = list(detector_names)
    flags = frames[0]
    for frame in frames[1:]:
        flags = flags.merge(frame, on="timestamp_utc", how="outer")
    flags = flags.sort_values("timestamp_utc").reset_index(drop=True)

    detector_cols = [f"{name}_anomaly" for name in detector_names]
    for column in detector_cols:
        # After the outer merge, an unscored hour is NaN; treat only an explicit
        # True as firing (eq avoids the object-dtype fillna downcast warning).
        flags[column] = flags[column].eq(True)
    flags["detector_count"] = flags[detector_cols].sum(axis=1)
    flags["all_three_anomaly"] = flags["detector_count"] == len(detector_names)
    return flags


def time_based_windows(
    timestamps, train_hours, eval_hours, label, min_coverage, observed_index=None
):
    """Build calendar-time rolling-origin windows with coverage checks.

    ``timestamps`` defines the calendar grid the window starts step across, so a
    window can fall entirely inside an outage and still be enumerated. Coverage
    is measured against ``observed_index`` — the hours the target is actually
    present — so an outage can never masquerade as training data. Windows below
    ``min_coverage`` in either span are recorded but marked unusable.
    ``observed_index`` defaults to ``timestamps`` for callers that pass only
    observed hours.
    """
    timestamps = pd.DatetimeIndex(timestamps).sort_values()
    if observed_index is None:
        observed_hours = timestamps
    else:
        observed_hours = pd.DatetimeIndex(observed_index).sort_values().unique()
    observed = pd.Series(True, index=observed_hours)
    rows = []
    if timestamps.empty:
        return pd.DataFrame(rows)

    step = pd.Timedelta(hours=eval_hours)
    train_span = pd.Timedelta(hours=train_hours)
    eval_span = pd.Timedelta(hours=eval_hours)
    start = timestamps.min()
    last_start = timestamps.max() - train_span - eval_span + pd.Timedelta(hours=1)

    window_id = 0
    while start <= last_start:
        train_end = start + train_span
        eval_end = train_end + eval_span
        train_observed = int(observed.loc[start : train_end - pd.Timedelta(hours=1)].sum())
        eval_observed = int(observed.loc[train_end : eval_end - pd.Timedelta(hours=1)].sum())
        train_coverage = train_observed / train_hours
        eval_coverage = eval_observed / eval_hours
        usable = train_coverage >= min_coverage and eval_coverage >= min_coverage
        rows.append(
            {
                "scheme": label,
                "window_id": f"{label}_{window_id:03d}",
                "train_hours": train_hours,
                "eval_hours": eval_hours,
                "train_start_utc": start,
                "train_end_utc": train_end - pd.Timedelta(hours=1),
                "eval_start_utc": train_end,
                "eval_end_utc": eval_end - pd.Timedelta(hours=1),
                "train_observed_hours": train_observed,
                "eval_observed_hours": eval_observed,
                "train_coverage": train_coverage,
                "eval_coverage": eval_coverage,
                "status": "ok" if usable else "insufficient_coverage",
            }
        )
        window_id += 1
        start = start + step
    return pd.DataFrame(rows)


def _summarize_exceedance_event(
    series,
    exceedance_index,
    source,
    quantile,
    threshold,
    antecedent_windows,
):
    """Summarize one contiguous exceedance window as a catalogue row."""
    event_values = series.loc[exceedance_index]
    start = event_values.index.min()
    peak_timestamp = event_values.idxmax()

    event = {
        "source": source,
        "threshold_quantile": quantile,
        "threshold_m3s": threshold,
        "start_timestamp_utc": start,
        "end_timestamp_utc": event_values.index.max(),
        "duration_hours": len(event_values),
        "peak_timestamp_utc": peak_timestamp,
        "peak_discharge_m3s": event_values.loc[peak_timestamp],
        "mean_discharge_m3s": event_values.mean(),
        "area_above_threshold_m3s_hours": (event_values - threshold).clip(lower=0).sum(),
    }

    for window in antecedent_windows:
        prior = series.loc[
            (series.index >= start - pd.Timedelta(hours=window)) & (series.index < start)
        ]
        event[f"antecedent_{window}h_max_m3s"] = prior.max()
        event[f"antecedent_{window}h_mean_m3s"] = prior.mean()

    return event


def _discharge_token(value):
    """Turn a discharge column name into a compact output-column prefix."""
    return source_token(value, strip_prefix="discharge_", strip_suffix="_m3s")


def _assert_gapless_hourly(index):
    """Guard that positional rolling windows equal their intended hour spans.

    The antecedent soft labels use positional rolling windows, which only equal
    an N-hour lookback when the index is a strictly increasing, gapless hourly
    grid (as produced by the resampled discharge loader). Fail loudly rather
    than silently mislabel if a caller passes an irregular index.
    """
    index = pd.DatetimeIndex(index)
    if len(index) <= 1:
        return
    steps = index.to_series().diff().dropna().unique()
    if list(steps) != [pd.Timedelta(hours=1)]:
        raise ValueError(
            "hourly_discharge_soft_labels expects a gapless hourly index; "
            "resample the discharge frame to hourly frequency first."
        )
