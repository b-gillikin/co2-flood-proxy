"""Meuse observational context: source quality and cutoff-safe hourly support."""

from __future__ import annotations

import numpy as np
import pandas as pd

DISPLAY_CODES = {"00", "10", "20", "25", "30", "40"}


def source_rows(payload):
    """Keep F103 unprocessed Q, not daily summaries or other method series."""
    rows, audit = [], []
    for block in payload["WaarnemingenLijst"]:
        m = block["AquoMetadata"]
        method = m["WaardeBepalingsMethode"]["Code"]
        processing = m["WaardeBewerkingsMethode"]["Code"]
        times = pd.to_datetime([o["Tijdstip"] for o in block["MetingenLijst"]], utc=True)
        steps = np.diff(np.sort(times.unique().as_unit("ns").asi8)) / 60e9
        cadence = float(np.median(steps)) if len(steps) else np.nan
        eligible = (
            cadence <= 10
            and method == "other:F103"
            and processing == "NVT"
            and m["Grootheid"]["Code"] == "Q"
            and m["Eenheid"]["Code"] == "m3/s"
        )
        counts = {}
        for obs in block["MetingenLijst"]:
            meta = obs["WaarnemingMetadata"]
            code, status = str(meta["Kwaliteitswaardecode"]).zfill(2), meta["Statuswaarde"]
            key = f"{code}|{status}"
            counts[key] = counts.get(key, 0) + 1
            value = obs["Meetwaarde"].get("Waarde_Numeriek")
            if eligible and value is not None and np.isfinite(value) and 0 <= value < 1e8:
                rows.append((obs["Tijdstip"], float(value), code, status))
        audit.append(
            dict(
                method=method,
                processing=processing,
                selected_method=eligible,
                median_step_minutes=cadence if np.isfinite(cadence) else None,
                code_status_counts=counts,
            )
        )
    return pd.DataFrame(rows, columns=["timestamp", "q", "code", "status"]), audit


def hourly_context(rows, start, end):
    """A bin's right edge is later than every contributing F103 support endpoint.

    F103 is centred +/-5 minutes. Binning timestamp+5min avoids post-cutoff
    observations. No filling; minimum four distinct readings per hourly mean.
    """
    rows = rows.copy()
    rows["timestamp"] = pd.to_datetime(rows.timestamp, utc=True)
    rows = rows[rows.status.eq("Gecontroleerd") & rows.code.isin(DISPLAY_CODES)]
    if rows.groupby("timestamp").q.nunique().gt(1).any():
        raise ValueError("Conflicting source values at a shared timestamp")
    rows = rows.drop_duplicates(["timestamp", "code"])
    rows["hour_end_utc"] = (rows.timestamp + pd.Timedelta(minutes=5)).dt.ceil("h")
    index = pd.date_range(pd.to_datetime(start, utc=True), pd.to_datetime(end, utc=True), freq="h")
    out = pd.DataFrame(index=index)
    for label, select in [
        ("strict", rows.code.eq("00")),
        ("display", rows.code.isin(DISPLAY_CODES)),
    ]:
        x = rows.loc[select].drop_duplicates("timestamp")
        groups = x.groupby("hour_end_utc").q.agg(["mean", "count"])
        out[f"n_{label}"] = groups["count"].reindex(index, fill_value=0).astype(int)
        out[f"q_{label}"] = groups["mean"].where(groups["count"].ge(4)).reindex(index)
    out["n_interpolated"] = (
        rows[rows.code.eq("25")]
        .drop_duplicates("timestamp")
        .groupby("hour_end_utc")
        .size()
        .reindex(index, fill_value=0)
    )
    out.index.name = "hour_end_utc"
    return out


def state_at_cutoff(frame, cutoff):
    """Past-only descriptors. Empirical rank uses strict data in previous years.

    These are retrospective available-observation ranks, not flood thresholds
    or real-time/as-issued information. No stale value substitution.
    """
    t = pd.Timestamp(cutoff)
    past = frame.loc[frame.index < pd.Timestamp(f"{t.year}-01-01", tz="UTC"), "q_strict"].dropna()
    values = np.sort(past.to_numpy())
    row = dict(history_hours=len(values), history_years=int(past.index.year.nunique()))

    def at(time, column):
        return frame[column].get(time, np.nan)

    for view in ["strict", "display"]:
        value = at(t, f"q_{view}")
        row[f"q_{view}_m3s"] = value
        row[f"rise6_{view}_m3s"] = value - at(t - pd.Timedelta(hours=6), f"q_{view}")
        row[f"rise24_{view}_m3s"] = value - at(t - pd.Timedelta(hours=24), f"q_{view}")
    value = row["q_strict_m3s"]
    row["prior_year_rank"] = (
        float(np.searchsorted(values, value, side="right") / len(values))
        if len(values) and np.isfinite(value)
        else np.nan
    )
    row["interpolated_readings_at_cutoff"] = at(t, "n_interpolated")
    for hours in [24, 72]:
        window = frame.reindex(pd.date_range(t - pd.Timedelta(hours=hours - 1), t, freq="h"))
        row[f"strict_coverage_past{hours}h"] = window.q_strict.notna().mean()
        row[f"interpolated_readings_past{hours}h"] = window.n_interpolated.sum(min_count=1)
    return row
