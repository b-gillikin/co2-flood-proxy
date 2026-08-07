"""Estimate the barometric response function of indoor CO2.

> **The response SHAPE from this script is withdrawn. The response SUM is not.**
>
> The deconvolution fits 49 correlated lags under plain ordinary least squares
> and rings: individual coefficients oscillate in a way the physics does not
> support, and the "instantaneous response" claim derived from the shape was an
> artifact of a bad summary statistic. Do not quote the impulse shape, the peak
> lag, or any single coefficient without first regularising — ridge, or a
> constrained lag form.
>
> The **cumulative sum** of the coefficients, the static gain, is a different
> matter. A sum over a correlated lag distribution is far better conditioned
> than its individual terms, which is precisely why the shape claim failed while
> the total did not. `scripts/21_forward_gain_model.py` uses only
> `cumsum(impulse)[-1]` and its detectability bound is unaffected by the
> ringing.
>
> This script was briefly archived on 2026-08-06 and restored, because
> `21_forward_gain_model.py` loads it by path and archiving it silently broke a
> live result. Keep them together.

The barometric response function (BRF) is the impulse response of indoor CO2 to
atmospheric pressure forcing, estimated by regression deconvolution: regress the
hourly change in CO2 on a series of lagged hourly pressure changes, and the
fitted coefficient sequence is the response.

    dCO2(t) = sum_i beta_i * dP(t - i) + e(t)

Its *shape* is diagnostic, which is why this beats reporting a single R2. A
response concentrated at short lag indicates a well-connected, shallow air-filled
void. A response spread over many hours indicates diffusion through thicker
unsaturated material. That shape is a direct read on the space the chapter's
mechanism depends on, and it is the method the soil-gas literature this chapter
already cites uses (Forde et al. 2019).

Three things are estimated:

1. the full-record BRF, fitted per contiguous block so no lag structure spans a
   coverage gap;
2. windowed BRFs, to ask whether the response changes over time;
3. whether window amplitude or timing tracks barometrically corrected water
   level, which is what the gain-modulation mechanism predicts. Physics predicts
   amplitude falls as water rises, because rising water shrinks the void.

Raw CO2 is the target, not the barometric residual. The residual has already had
a pressure model subtracted, which would remove the very response being measured.

KNMI 06380 is the forcing by default. It is external to the building, so it
cannot share a sensor artifact with the CO2 record; indoor pressure is available
via --pressure-source as a sensitivity check.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.signal_frame import CO2_COL, contiguous_blocks, load_signal_frame

READINGS_PATH = Path("data/raw/groundwater/bro_gld_readings.csv")
OUTPUT_DIR = Path("results/barometric_response")

MAX_LAG_HOURS = 48
MIN_BLOCK_HOURS = 336  # two weeks; shorter blocks cannot support 48 lags
WINDOW_HOURS = 336
WINDOW_STEP_HOURS = 72
HPA_TO_M_HEAD = 0.0102

# Per-well barometric efficiency from scripts/05b_barometric_efficiency.py.
BAROMETRIC_EFFICIENCY = {
    "bro_gmw13161": 0.2405,
    "bro_gmw13172": 0.1990,
    "bro_gmw13210": 0.3376,
}
PRIMARY_WELL = "bro_gmw13210"


def deconvolve(co2, pressure, max_lag=MAX_LAG_HOURS):
    """Return the impulse response of CO2 to pressure change, in ppm/hPa.

    Both series are first-differenced before fitting. Differencing removes the
    slow drift that would otherwise dominate a level-on-level regression, and it
    is what makes the coefficients interpretable as a response to a *change* in
    pressure rather than to its absolute value.
    """
    d_co2 = co2.diff()
    d_pressure = pressure.diff()
    design = pd.DataFrame({f"lag_{lag}": d_pressure.shift(lag) for lag in range(max_lag + 1)})
    frame = design.join(d_co2.rename("y")).dropna()
    if len(frame) < max_lag * 4:
        return None, 0
    x = np.column_stack([np.ones(len(frame)), frame.drop(columns="y").to_numpy()])
    coefficients, *_ = np.linalg.lstsq(x, frame["y"].to_numpy(), rcond=None)
    return coefficients[1:], len(frame)


def response_shape(impulse):
    """Summarize a BRF: total response, peak lag, and spread."""
    cumulative = np.cumsum(impulse)
    total = float(cumulative[-1])
    peak_lag = int(np.argmax(np.abs(impulse)))
    # Lag at which the cumulative response first reaches 63% of its final value,
    # the discrete analogue of a time constant. Undefined if the response never
    # settles, which is itself informative.
    if total == 0 or not np.isfinite(total):
        settle_lag = np.nan
    else:
        reached = np.where(np.abs(cumulative) >= 0.63 * abs(total))[0]
        settle_lag = int(reached[0]) if len(reached) else np.nan
    return {
        "total_ppm_per_hpa": total,
        "peak_lag_h": peak_lag,
        "settle_lag_h": settle_lag,
        "peak_impulse": float(impulse[peak_lag]),
    }


def corrected_water_level():
    """Daily barometrically corrected level for the primary well."""
    readings = pd.read_csv(READINGS_PATH, parse_dates=["timestamp"])
    level = readings.loc[readings["series_id"].eq(PRIMARY_WELL)]
    level = level.set_index("timestamp")["water_level_value"].sort_index()
    return level[~level.index.duplicated()]


def windowed_responses(frame, pressure_col):
    """Fit a BRF in overlapping windows within each contiguous block."""
    observed = frame.index[frame[CO2_COL].notna()]
    rows = []
    for block_id, index in contiguous_blocks(observed, min_hours=MIN_BLOCK_HOURS):
        block = frame.loc[index]
        for start in range(0, len(block) - WINDOW_HOURS + 1, WINDOW_STEP_HOURS):
            window = block.iloc[start : start + WINDOW_HOURS]
            impulse, count = deconvolve(window[CO2_COL], window[pressure_col])
            if impulse is None:
                continue
            rows.append(
                {
                    "block_id": block_id,
                    "window_start_utc": window.index[0],
                    "window_end_utc": window.index[-1],
                    "n_hours": count,
                    **response_shape(impulse),
                }
            )
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pressure-source",
        default="knmi_pressure_hpa",
        choices=["knmi_pressure_hpa", "iot_air_pressure_hpa"],
        help="Barometric forcing series; KNMI is external to the building.",
    )
    args = parser.parse_args()

    frame = load_signal_frame()
    pressure_col = args.pressure_source

    lines = ["Barometric Response Function of Indoor CO2", ""]
    lines.append(f"Forcing: {pressure_col}")
    lines.append(f"Lags: 0 to {MAX_LAG_HOURS} h; fitted per contiguous block")
    lines.append("")

    observed = frame.index[frame[CO2_COL].notna()]
    blocks = contiguous_blocks(observed, min_hours=MIN_BLOCK_HOURS)
    lines.append(f"Blocks of at least {MIN_BLOCK_HOURS} h: {len(blocks)}")

    impulses = {}
    lines.append("")
    lines.append("Full-block responses:")
    for block_id, index in blocks:
        block = frame.loc[index]
        impulse, count = deconvolve(block[CO2_COL], block[pressure_col])
        if impulse is None:
            lines.append(f"  block {block_id}: insufficient data")
            continue
        impulses[block_id] = impulse
        shape = response_shape(impulse)
        lines.append(
            f"  block {block_id} ({index[0]:%Y-%m-%d} to {index[-1]:%Y-%m-%d}, n={count}): "
            f"total {shape['total_ppm_per_hpa']:+.2f} ppm/hPa, "
            f"peak at lag {shape['peak_lag_h']} h ({shape['peak_impulse']:+.2f}), "
            f"63% of response by {shape['settle_lag_h']} h"
        )

    windows = windowed_responses(frame, pressure_col)
    lines.append("")
    lines.append(f"Windowed responses: {len(windows)} windows of {WINDOW_HOURS} h")

    if not windows.empty:
        lines.append(
            f"  total response: median {windows['total_ppm_per_hpa'].median():+.2f}, "
            f"range {windows['total_ppm_per_hpa'].min():+.2f} to "
            f"{windows['total_ppm_per_hpa'].max():+.2f} ppm/hPa"
        )
        lines.append(
            f"  peak lag: median {windows['peak_lag_h'].median():.0f} h, "
            f"range {windows['peak_lag_h'].min():.0f} to {windows['peak_lag_h'].max():.0f} h"
        )

        # Does the response track water state, as gain modulation predicts?
        level = corrected_water_level()
        pressure = frame[pressure_col].reindex(level.index, method="nearest")
        corrected = level + BAROMETRIC_EFFICIENCY[PRIMARY_WELL] * pressure * HPA_TO_M_HEAD
        windows["window_mid_utc"] = (
            windows["window_start_utc"]
            + (windows["window_end_utc"] - windows["window_start_utc"]) / 2
        )
        windows["water_level_m"] = [
            corrected.reindex([t], method="nearest", tolerance=pd.Timedelta("3D")).iloc[0]
            for t in windows["window_mid_utc"]
        ]
        paired = windows.dropna(subset=["water_level_m"])
        lines.append("")
        lines.append(
            f"Response versus corrected water level ({PRIMARY_WELL}), {len(paired)} paired windows:"
        )
        if len(paired) >= 5:
            for column in ("total_ppm_per_hpa", "peak_lag_h"):
                r = np.corrcoef(paired["water_level_m"], paired[column])[0, 1]
                lines.append(f"  corr(water level, {column}) = {r:+.3f}")
            lines.append("")
            lines.append(
                "  Gain modulation predicts a positive correlation for total "
                "response:\n  higher water shrinks the void, weakening a negative "
                "response toward zero."
            )
        else:
            lines.append("  too few paired windows to correlate")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if impulses:
        pd.DataFrame(impulses).rename_axis("lag_hours").to_csv(OUTPUT_DIR / "impulse_response.csv")
    if not windows.empty:
        windows.to_csv(OUTPUT_DIR / "windowed_response.csv", index=False)
    (OUTPUT_DIR / "barometric_response.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_DIR}/barometric_response.txt")


if __name__ == "__main__":
    main()
