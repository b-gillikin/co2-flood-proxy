"""Track the CO2 response to the semidiurnal atmospheric tide.

The atmosphere carries strong, nearly deterministic thermal tides: S1 at 24 h and
S2 at 12 h. They are a narrowband, high signal-to-noise probe of the same
pressure coupling the broadband response function measures, obtained for free.

**This probe does not work at this site, and the script now measures why.**

The method was chosen on the premise that indoor CO2 carries little semidiurnal
behaviour, so the 12-hour band would be a clean view of the tidal response. That
premise is false for a residence. Morning and evening occupancy make the daily
cycle strongly non-sinusoidal, and a double-humped 24-hour cycle projects heavily
onto the 12-hour harmonic.

Two measurements establish it, both printed below. The observed CO2 amplitude at
S2 is four to eight times larger than the barometric response function can
account for, and the amplitude survives subtracting the fitted pressure model,
which a genuinely barometric signal could not.

The estimated "gain" is therefore an occupancy artifact and must not be read as a
pressure response. The script is retained because the contamination check is the
useful part: it is direct evidence that the sensor reads the building rather than
the subsurface. Use the broadband response in 19_barometric_response.py instead.

For each window this estimates the complex amplitude of CO2 and of pressure at
S2 by least squares, and reports:

    gain  = |A_co2| / |A_pressure|          ppm per hPa at 12 h
    phase = arg(A_co2) - arg(A_pressure)    degrees, negative meaning CO2 lags

then asks whether gain tracks barometrically corrected water level. The
gain-modulation mechanism predicts gain falls as water rises, because rising
water shrinks the connected air-filled void.

Windows overlap, so the count of windows overstates independent information.
The effective sample is reported alongside it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.signal_frame import CO2_COL, TARGET_COL, contiguous_blocks, load_signal_frame

READINGS_PATH = Path("data/raw/groundwater/bro_gld_readings.csv")
OUTPUT_DIR = Path("results/barometric_response")

PRESSURE_COL = "knmi_pressure_hpa"
S2_PERIOD_HOURS = 12.0
S1_PERIOD_HOURS = 24.0
WINDOW_HOURS = 336
WINDOW_STEP_HOURS = 72
MIN_BLOCK_HOURS = 336
HPA_TO_M_HEAD = 0.0102

BAROMETRIC_EFFICIENCY = {"bro_gmw13210": 0.3376}
PRIMARY_WELL = "bro_gmw13210"


def complex_amplitude(series, period_hours):
    """Least-squares complex amplitude of one harmonic, with trend removed.

    A constant and linear trend are included so slow drift cannot leak into the
    harmonic estimate. Both tidal bands are fitted together so they cannot
    absorb one another.
    """
    values = series.to_numpy(dtype=float)
    hours = (series.index - series.index[0]).total_seconds().to_numpy() / 3600.0
    design = [np.ones_like(hours), hours]
    for period in (S1_PERIOD_HOURS, S2_PERIOD_HOURS):
        design.append(np.cos(2 * np.pi * hours / period))
        design.append(np.sin(2 * np.pi * hours / period))
    x = np.column_stack(design)
    coefficients, *_ = np.linalg.lstsq(x, values, rcond=None)
    index = 2 if period_hours == S1_PERIOD_HOURS else 4
    return complex(coefficients[index], -coefficients[index + 1])


def window_rows(frame):
    """Estimate S2 gain and phase in overlapping windows."""
    observed = frame.index[frame[CO2_COL].notna() & frame[PRESSURE_COL].notna()]
    rows = []
    for block_id, index in contiguous_blocks(observed, min_hours=MIN_BLOCK_HOURS):
        block = frame.loc[index]
        for start in range(0, len(block) - WINDOW_HOURS + 1, WINDOW_STEP_HOURS):
            window = block.iloc[start : start + WINDOW_HOURS]
            co2 = window[CO2_COL].dropna()
            pressure = window[PRESSURE_COL].dropna()
            if len(co2) < WINDOW_HOURS * 0.9 or len(pressure) < WINDOW_HOURS * 0.9:
                continue
            a_co2 = complex_amplitude(co2, S2_PERIOD_HOURS)
            a_pressure = complex_amplitude(pressure, S2_PERIOD_HOURS)
            if abs(a_pressure) == 0:
                continue
            phase = np.degrees(np.angle(a_co2) - np.angle(a_pressure))
            rows.append(
                {
                    "block_id": block_id,
                    "window_start_utc": window.index[0],
                    "window_end_utc": window.index[-1],
                    "co2_amplitude_ppm": abs(a_co2),
                    "pressure_amplitude_hpa": abs(a_pressure),
                    "gain_ppm_per_hpa": abs(a_co2) / abs(a_pressure),
                    "phase_deg": (phase + 180) % 360 - 180,
                }
            )
    return pd.DataFrame(rows)


def corrected_level_at(times):
    """Barometrically corrected primary-well level nearest each timestamp."""
    readings = pd.read_csv(READINGS_PATH, parse_dates=["timestamp"])
    level = readings.loc[readings["series_id"].eq(PRIMARY_WELL)]
    level = level.set_index("timestamp")["water_level_value"].sort_index()
    level = level[~level.index.duplicated()]
    values = []
    for moment in times:
        nearest = level.reindex([moment], method="nearest", tolerance=pd.Timedelta("3D"))
        values.append(np.nan if nearest.isna().all() else float(nearest.iloc[0]))
    return pd.Series(values, index=times)


def contamination_check(frame, assumed_gain_ppm_per_hpa=20.0):
    """Test whether the 12-hour CO2 signal is barometric at all.

    Compares the observed S2 amplitude in raw CO2 against what the broadband
    response function predicts, and against the amplitude surviving in the
    pressure-separated residual. A barometric signal should be close to the
    prediction and should largely vanish from the residual.
    """
    lines = [
        "Is the 12-hour signal barometric? Per contiguous block:",
        f"  {'block':>6} {'raw CO2':>9} {'residual':>9} {'pressure':>9} {'predicted':>10}",
    ]
    observed = frame.index[frame[CO2_COL].notna()]
    for block_id, index in contiguous_blocks(observed, min_hours=MIN_BLOCK_HOURS):
        block = frame.loc[index]
        raw = abs(complex_amplitude(block[CO2_COL].dropna(), S2_PERIOD_HOURS))
        residual_series = block[TARGET_COL].dropna()
        residual = (
            abs(complex_amplitude(residual_series, S2_PERIOD_HOURS))
            if len(residual_series) > 300
            else float("nan")
        )
        pressure = abs(complex_amplitude(block[PRESSURE_COL].dropna(), S2_PERIOD_HOURS))
        lines.append(
            f"  {block_id:>6} {raw:9.1f} {residual:9.1f} {pressure:9.3f} "
            f"{pressure * assumed_gain_ppm_per_hpa:10.1f}"
        )
    lines.append(
        f"  Amplitudes in ppm except pressure in hPa; predicted = pressure x "
        f"{assumed_gain_ppm_per_hpa:.0f} ppm/hPa,"
    )
    lines.append("  the midpoint of the broadband response from 19_barometric_response.py.")
    lines.append(
        "  Raw CO2 far exceeding the prediction, and a residual that stays large,\n"
        "  together mean the 12-hour band is occupancy, not tide."
    )
    return lines


def main():
    frame = load_signal_frame()
    windows = window_rows(frame)

    lines = ["Semidiurnal (S2) Tidal Response of Indoor CO2", ""]
    lines.append(f"Forcing: {PRESSURE_COL}; probe period {S2_PERIOD_HOURS:.0f} h")
    lines.append(f"Windows: {WINDOW_HOURS} h, stepped {WINDOW_STEP_HOURS} h")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if windows.empty:
        lines.append("No window met the coverage requirement.")
        (OUTPUT_DIR / "tidal_response.txt").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return

    overlap = WINDOW_HOURS / WINDOW_STEP_HOURS
    effective = len(windows) / overlap
    lines.append(
        f"Windows fitted: {len(windows)} "
        f"(overlapping {overlap:.0f}x, so about {effective:.0f} independent)"
    )
    lines.append("")
    lines.append("S2 amplitudes and gain:")
    lines.append(
        f"  pressure amplitude: median {windows['pressure_amplitude_hpa'].median():.3f} hPa"
    )
    lines.append(f"  CO2 amplitude:      median {windows['co2_amplitude_ppm'].median():.1f} ppm")
    lines.append(
        f"  gain:               median {windows['gain_ppm_per_hpa'].median():.1f} ppm/hPa, "
        f"IQR {windows['gain_ppm_per_hpa'].quantile(0.25):.1f} to "
        f"{windows['gain_ppm_per_hpa'].quantile(0.75):.1f}"
    )
    lines.append(
        f"  phase:              median {windows['phase_deg'].median():+.0f} deg "
        "(negative means CO2 lags pressure)"
    )

    lines.append("")
    lines.extend(contamination_check(frame))

    windows["window_mid_utc"] = (
        windows["window_start_utc"] + (windows["window_end_utc"] - windows["window_start_utc"]) / 2
    )
    windows["water_level_m"] = corrected_level_at(windows["window_mid_utc"]).to_numpy()
    paired = windows.dropna(subset=["water_level_m"])

    lines.append("")
    lines.append(f"Gain versus corrected water level, {len(paired)} paired windows:")
    if len(paired) >= 5:
        r = np.corrcoef(paired["water_level_m"], paired["gain_ppm_per_hpa"])[0, 1]
        lines.append(f"  corr(water level, S2 gain) = {r:+.3f}")
        lines.append(
            f"  about {len(paired) / overlap:.0f} independent windows, so this "
            "correlation carries very little weight"
        )
        lines.append("")
        lines.append(
            "  Gain modulation predicts a negative correlation: rising water\n"
            "  shrinks the void and weakens the response."
        )
    else:
        lines.append("  too few paired windows to correlate")

    windows.to_csv(OUTPUT_DIR / "tidal_windows.csv", index=False)
    (OUTPUT_DIR / "tidal_response.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_DIR}/tidal_response.txt")


if __name__ == "__main__":
    main()
