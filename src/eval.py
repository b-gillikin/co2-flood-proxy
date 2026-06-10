"""Small evaluation helpers for discharge-derived labels.

The chapter uses discharge as a soft hydrological-state proxy rather than as a
hard flood label. These helpers keep that logic in one place so analysis
scripts can stay focused on data joins, plots, and model results.
"""

from __future__ import annotations

import pandas as pd


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
        series = discharge[row.source].dropna()
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
            f"evt_{idx + 1:04d}_{_source_token(row.source)}_p{int(row.threshold_quantile * 100)}"
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
    """
    thresholds = discharge_thresholds(discharge, quantiles)
    labels = pd.DataFrame(index=discharge.index)

    quantile_scores = {quantile: idx + 1 for idx, quantile in enumerate(quantiles)}
    max_score = len(quantiles)

    for column in discharge_columns(discharge):
        source_thresholds = thresholds.loc[thresholds["source"] == column]
        scores = pd.Series(0, index=discharge.index, dtype="int64")
        for row in source_thresholds.sort_values("quantile").itertuples(index=False):
            scores = scores.mask(
                discharge[column] >= row.threshold_m3s,
                quantile_scores[row.quantile],
            )

        token = _source_token(column)
        labels[f"{token}_current_level"] = scores
        labels[f"{token}_current_soft_label"] = scores / max_score

        for window in antecedent_windows:
            # The frame is hourly by construction, so a 72-row rolling window is
            # the 72-hour antecedent maximum used in the June plan.
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
            column
            for column in level_columns
            if column.endswith(f"_antecedent_{window}h_level")
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
        "area_above_threshold_m3s_hours": (event_values - threshold)
        .clip(lower=0)
        .sum(),
    }

    for window in antecedent_windows:
        prior = series.loc[
            (series.index >= start - pd.Timedelta(hours=window))
            & (series.index < start)
        ]
        event[f"antecedent_{window}h_max_m3s"] = prior.max()
        event[f"antecedent_{window}h_mean_m3s"] = prior.mean()

    return event


def _source_token(value):
    """Turn a discharge column name into a compact output-column prefix."""
    token = str(value)
    token = token.removeprefix("discharge_").removesuffix("_m3s")
    return "".join(char.lower() if char.isalnum() else "_" for char in token).strip("_")
