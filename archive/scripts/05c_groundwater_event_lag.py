"""Test whether groundwater leads or lags tributary high-flow events.

An early-warning precursor carried by indoor CO2 requires a subsurface signal
that moves *before* the river does. If the water table responds only after the
discharge peak, there is no hydrological precursor to detect and any apparent
pre-event CO2 signal is more likely barometric.

Two views, both on barometrically corrected water level:

1. Cross-correlation of 6-hourly first differences against gauge discharge,
   over the full groundwater/discharge overlap.
2. Event composites around episode onset, raw and locally detrended, since the
   available episodes fall inside a summer recession that would otherwise
   dominate the composite.

Interpretation limits are printed with the results and should travel with any
quotation of them.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval import deduplicate_event_episodes

READINGS_PATH = Path("data/raw/groundwater/bro_gld_readings.csv")
DISCHARGE_PATH = Path("data/interim/discharge_hourly.csv")
KNMI_PATH = Path("data/interim/knmi_hourly.csv")
EVENTS_PATH = Path("data/processed/event_catalogue.csv")
OUTPUT_PATH = Path("results/groundwater/event_lead_lag.txt")

# Barometric efficiency per well, from scripts/05b_barometric_efficiency.py.
BAROMETRIC_EFFICIENCY = {
    "bro_gmw13161": 0.2405,
    "bro_gmw13172": 0.1990,
    "bro_gmw13210": 0.3376,
}
HPA_TO_M_HEAD = 0.0102
MAX_LAG_STEPS = 28
COMPOSITE_OFFSETS = (-72, -48, -24, -12, 0, 12, 24, 48, 72)
DETREND_WINDOW_DAYS = 14


def corrected_levels():
    """Return barometrically corrected level series keyed by series_id."""
    readings = pd.read_csv(READINGS_PATH, parse_dates=["timestamp"])
    knmi = pd.read_csv(KNMI_PATH, parse_dates=["timestamp_utc"])
    knmi = knmi.loc[knmi["knmi_station"].astype(str).str.contains("380")]
    pressure = knmi.set_index("timestamp_utc")["knmi_pressure_hpa"].dropna().sort_index()

    series = {}
    for series_id, efficiency in BAROMETRIC_EFFICIENCY.items():
        level = readings.loc[readings["series_id"].eq(series_id)]
        level = level.set_index("timestamp")["water_level_value"].sort_index()
        level = level[~level.index.duplicated()]
        aligned = pressure.reindex(level.index, method="nearest", tolerance=pd.Timedelta("3h"))
        series[series_id] = (level + efficiency * aligned * HPA_TO_M_HEAD).dropna()
    return series


def usable_episodes(groundwater_end):
    """Episodes with CO2 coverage before and during, and groundwater available."""
    events = pd.read_csv(EVENTS_PATH, parse_dates=["start_timestamp_utc", "end_timestamp_utc"])
    covered = events.loc[events["iot_overlap_hours"].gt(0) & events["iot_pre_event_hours"].ge(60)]
    episodes = deduplicate_event_episodes(covered)
    cutoff = groundwater_end - pd.Timedelta(days=2)
    return episodes.loc[episodes["start_timestamp_utc"].le(cutoff)].sort_values(
        "start_timestamp_utc"
    )


def cross_correlation(level, discharge):
    """Peak |correlation| of 6-hourly differences; positive lag = level leads."""
    level6 = level.resample("6h").mean()
    rows = []
    for gauge in discharge.columns:
        merged = pd.DataFrame({"gw": level6, "q": discharge[gauge]}).dropna()
        deltas = merged.diff().dropna()
        best_lag, best_r, count = np.nan, 0.0, 0
        for lag in range(-MAX_LAG_STEPS, MAX_LAG_STEPS + 1):
            joined = pd.DataFrame({"a": deltas["gw"], "b": deltas["q"].shift(-lag)}).dropna()
            if len(joined) < 200:
                continue
            r = np.corrcoef(joined["a"], joined["b"])[0, 1]
            if abs(r) > abs(best_r):
                best_lag, best_r, count = lag, r, len(joined)
        rows.append((gauge, best_lag, best_r, count))
    return rows


def composite(level, episodes, detrend):
    """Mean level change relative to onset across episodes."""
    columns = {offset: [] for offset in COMPOSITE_OFFSETS}
    for row in episodes.itertuples(index=False):
        onset = row.start_timestamp_utc
        window = level.loc[
            onset - pd.Timedelta(days=DETREND_WINDOW_DAYS) : onset
            + pd.Timedelta(days=DETREND_WINDOW_DAYS)
        ]
        if len(window) < 40:
            continue
        if detrend:
            hours = (window.index - onset).total_seconds() / 3600.0
            slope, intercept = np.polyfit(hours, window.to_numpy(), 1)
            window = pd.Series(window.to_numpy() - (slope * hours + intercept), index=window.index)
        base = window.reindex([onset], method="nearest", tolerance=pd.Timedelta("6h"))
        if base.isna().all():
            continue
        for offset in COMPOSITE_OFFSETS:
            value = window.reindex(
                [onset + pd.Timedelta(hours=offset)],
                method="nearest",
                tolerance=pd.Timedelta("6h"),
            )
            columns[offset].append(np.nan if value.isna().all() else value.iloc[0] - base.iloc[0])
    return [float(np.nanmean(columns[o])) if columns[o] else np.nan for o in COMPOSITE_OFFSETS]


def main():
    levels = corrected_levels()
    discharge = (
        pd.read_csv(DISCHARGE_PATH, parse_dates=["timestamp_utc"])
        .set_index("timestamp_utc")
        .sort_index()
        .resample("6h")
        .mean()
    )
    groundwater_end = max(series.index.max() for series in levels.values())
    episodes = usable_episodes(groundwater_end)

    lines = ["Groundwater Lead/Lag Against Tributary High-Flow Events", ""]
    lines.append(f"Episodes with groundwater coverage: {len(episodes)}")
    for row in episodes.itertuples(index=False):
        lines.append(
            f"  {row.start_timestamp_utc:%Y-%m-%d %H:%M} "
            f"({row.duration_hours:.0f} h, {row.n_sources} gauges)"
        )
    lines.append("")

    lines.append("Cross-correlation of 6-hourly differences.")
    lines.append("Positive lag means groundwater leads discharge.")
    for series_id, level in levels.items():
        for gauge, lag, r, count in cross_correlation(level, discharge):
            name = gauge.replace("discharge_", "").replace("_m3s", "")
            lines.append(
                f"  {series_id} vs {name:16} peak r = {r:+.3f} at {lag * 6:+d} h (n = {count})"
            )
    lines.append("")

    header = " ".join(f"{o:>+7d}h" for o in COMPOSITE_OFFSETS)
    for detrend, label in ((False, "raw"), (True, "locally detrended")):
        lines.append(f"Event composite, {label}; level change relative to onset (m):")
        lines.append(f"  {'well':14} {header}")
        for series_id, level in levels.items():
            values = composite(level, episodes, detrend)
            lines.append(f"  {series_id:14} " + " ".join(f"{v:+8.4f}" for v in values))
        lines.append("")

    lines.extend(
        [
            "Interpretation limits:",
            "  - All usable episodes fall in July-August 2025, inside one summer",
            "    recession. Antecedent conditions were dry and recharge minimal.",
            "  - Episodes cluster within about five weeks, so the detrending",
            "    windows overlap and each contains other episodes.",
            "  - Wells are shallow phreatic, 2.85-3.60 km from the site. They are",
            "    not mine water and not at the site.",
            "  - Seven episodes is a weak basis for a composite.",
            "  - Nothing here tests winter conditions, wet antecedent states, or a",
            "    connected mine-water compartment.",
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
