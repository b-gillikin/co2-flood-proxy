"""Estimate well barometric efficiency and test the shared-pressure confound.

Groundwater level and indoor CO2 both respond to atmospheric pressure. If the
water level used as the direct-state exposure still carries a barometric
component, an association with the pressure-separated CO2 residual can be a
shared-pressure artifact rather than hydrological information.

This script:

1. estimates barometric efficiency per well from 6-hourly first differences
   against KNMI 06380 pressure over the full 2021-2025 record;
2. reports how much of daily water-level change that explains;
3. measures the water-level/pressure correlation inside each IoT overlap
   window, before and after barometric correction.

Barometric efficiency is estimated on differences, not levels, so slow recharge
trends do not enter the estimate. The correction is the standard
``W_corrected = W + BE * P_head`` with pressure converted to equivalent metres
of water head (1 hPa = 0.0102 m).

The long record is what makes this possible: the overlap windows alone are far
too short to separate a barometric response from seasonal recharge.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

READINGS_PATH = Path("data/raw/groundwater/bro_gld_readings.csv")
DAILY_PATH = Path("data/interim/groundwater_daily.csv")
KNMI_PATH = Path("data/interim/knmi_hourly.csv")
OUTPUT_PATH = Path("results/groundwater/barometric_efficiency.txt")

REFERENCE_STATION = "380"
HPA_TO_M_HEAD = 0.0102

# Contiguous IoT blocks with groundwater overlap; see docs/data-requests.md.
IOT_WINDOWS = {
    "Feb 2025 (Blynk Basement 1)": ("2025-01-31", "2025-02-27"),
    "Jun-Aug 2025 (Blynk Basement 2)": ("2025-06-26", "2025-08-26"),
}


def knmi_pressure():
    """Return hourly and daily-mean KNMI 06380 pressure."""
    frame = pd.read_csv(KNMI_PATH, parse_dates=["timestamp_utc"])
    frame = frame.loc[frame["knmi_station"].astype(str).str.contains(REFERENCE_STATION)]
    frame = frame[["timestamp_utc", "knmi_pressure_hpa"]].dropna()
    hourly = frame.set_index("timestamp_utc")["knmi_pressure_hpa"].sort_index()
    daily = hourly.groupby(hourly.index.floor("D")).mean()
    return hourly, daily


def barometric_efficiency(readings, pressure_hourly, series_id):
    """Fit dW/dP on 6-hourly first differences; return (BE, r, n)."""
    water = readings.loc[readings["series_id"].eq(series_id)]
    water = water.set_index("timestamp")["water_level_value"].sort_index()
    water = water[~water.index.duplicated()]
    merged = pd.DataFrame({"W": water}).join(pressure_hourly, how="inner").dropna()
    merged["P_head"] = merged["knmi_pressure_hpa"] * HPA_TO_M_HEAD
    steps = pd.Series(merged.index).diff().dt.total_seconds().to_numpy()[1:] / 3600
    deltas = merged.diff().dropna()
    deltas = deltas[(steps > 5) & (steps < 7)]
    slope = np.polyfit(deltas["P_head"], deltas["W"], 1)[0]
    correlation = np.corrcoef(deltas["P_head"], deltas["W"])[0, 1]
    return -slope, correlation, len(deltas)


def daily_share(daily_levels, pressure_daily, series_id):
    """Return the share of day-to-day water-level change explained by pressure."""
    water = daily_levels.loc[daily_levels["series_id"].eq(series_id)]
    water = water.set_index("date_utc")["hydrologic_level"].sort_index()
    merged = pd.DataFrame({"W": water}).join(pressure_daily.rename("P"), how="inner").dropna()
    gaps = pd.Series(merged.index).diff().dt.days.to_numpy()
    deltas = merged.diff()[gaps == 1].dropna()
    if len(deltas) < 30:
        return np.nan, 0
    correlation = np.corrcoef(deltas["P"] * HPA_TO_M_HEAD, deltas["W"])[0, 1]
    return correlation**2, len(deltas)


def window_correlations(daily_levels, pressure_daily, series_id, efficiency):
    """Water-level/pressure correlation per IoT window, raw and corrected."""
    water = daily_levels.loc[daily_levels["series_id"].eq(series_id)]
    water = water.set_index("date_utc")["hydrologic_level"].sort_index()
    merged = pd.DataFrame({"W": water}).join(pressure_daily.rename("P"), how="inner").dropna()
    merged["W_corrected"] = merged["W"] + efficiency * merged["P"] * HPA_TO_M_HEAD
    rows = []
    for label, (start, end) in IOT_WINDOWS.items():
        window = merged.loc[start:end]
        if len(window) < 10:
            continue
        rows.append(
            {
                "window": label,
                "n_days": len(window),
                "raw_corr": np.corrcoef(window["W"], window["P"])[0, 1],
                "corrected_corr": np.corrcoef(window["W_corrected"], window["P"])[0, 1],
            }
        )
    return rows


def main():
    readings = pd.read_csv(READINGS_PATH, parse_dates=["timestamp"])
    daily_levels = pd.read_csv(DAILY_PATH, parse_dates=["date_utc"])
    pressure_hourly, pressure_daily = knmi_pressure()

    lines = ["Well Barometric Efficiency and Shared-Pressure Confound", ""]
    lines.append(f"Reference pressure: KNMI station 0{REFERENCE_STATION}")
    lines.append(
        f"Record: {readings['timestamp'].min():%Y-%m-%d} to {readings['timestamp'].max():%Y-%m-%d}"
    )
    lines.append("")

    efficiencies = {}
    lines.append("Barometric efficiency (6-hourly first differences, full record):")
    for series_id in sorted(readings["series_id"].unique()):
        efficiency, correlation, count = barometric_efficiency(readings, pressure_hourly, series_id)
        efficiencies[series_id] = efficiency
        share, daily_n = daily_share(daily_levels, pressure_daily, series_id)
        lines.append(
            f"  {series_id}: BE = {efficiency:+.3f}  (r = {correlation:+.3f}, n = {count:,})"
            f" | daily change explained: {share * 100:.1f}% (n = {daily_n:,})"
        )
    lines.append("")

    lines.append("Water level vs pressure inside IoT overlap windows:")
    lines.append(f"  {'window':32} {'series':14} {'n':>4} {'raw':>8} {'corrected':>10}")
    for series_id, efficiency in efficiencies.items():
        for row in window_correlations(daily_levels, pressure_daily, series_id, efficiency):
            lines.append(
                f"  {row['window']:32} {series_id:14} {row['n_days']:>4}"
                f" {row['raw_corr']:>+8.3f} {row['corrected_corr']:>+10.3f}"
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
