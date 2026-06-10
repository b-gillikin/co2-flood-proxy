"""Week 2 barometric baseline and Kill Check 1."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.metrics import r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import pressure_deltas


INTERIM_DIR = Path("data/interim")
PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/baseline")

INPUT_PATH = INTERIM_DIR / "analysis_hourly.csv"
RESIDUAL_PATH = PROCESSED_DIR / "co2-residual-barometric.csv"
METRICS_PATH = RESULTS_DIR / "r2.txt"
PLOT_PATH = RESULTS_DIR / "co2_fit_residual.png"

CO2_COL = "iot_co2_ppm"
PRIMARY_PRESSURE_COL = "iot_air_pressure_hpa"
WEATHER_PRESSURE_COL = "kerkrade_weather_pressure_hpa"
LAGS = (1, 3, 6, 12, 24)
RIDGE_ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)


def load_analysis_frame(path=INPUT_PATH):
    """Load the joined Week 1 hourly frame."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return frame.set_index("timestamp_utc").sort_index()


def build_model_frame(frame, pressure_col):
    """Add pressure-delta features and keep complete modelling rows."""
    model_frame = pressure_deltas(
        frame[[CO2_COL, pressure_col]].copy(),
        lags=LAGS,
        pressure_col=pressure_col,
    )
    feature_cols = [
        pressure_col,
        *[f"delta_pressure_{lag}h" for lag in LAGS],
    ]
    return model_frame.dropna(subset=[CO2_COL, *feature_cols]), feature_cols


def kill_check_status(r2):
    """Translate the official R2 into the June kill-check decision."""
    if r2 <= 0.85:
        return "proceed"
    if r2 <= 0.95:
        return "proceed with caution"
    return "pause/redirect"


def fit_baseline(frame, pressure_col, label):
    """Fit linear and ridge pressure-only CO2 baselines for one pressure source."""
    model_frame, feature_cols = build_model_frame(frame, pressure_col)
    x = model_frame[feature_cols]
    y = model_frame[CO2_COL]

    linear_model = LinearRegression().fit(x, y)
    linear_fit = linear_model.predict(x)
    linear_r2 = r2_score(y, linear_fit)

    ridge_model = make_pipeline(
        StandardScaler(),
        RidgeCV(alphas=RIDGE_ALPHAS),
    ).fit(x, y)
    ridge_fit = ridge_model.predict(x)
    ridge_r2 = r2_score(y, ridge_fit)
    ridge_alpha = ridge_model.named_steps["ridgecv"].alpha_

    return {
        "label": label,
        "pressure_col": pressure_col,
        "feature_cols": feature_cols,
        "n_rows": len(model_frame),
        "window_start": model_frame.index.min(),
        "window_end": model_frame.index.max(),
        "linear_model": linear_model,
        "linear_fit": linear_fit,
        "linear_r2": linear_r2,
        "ridge_model": ridge_model,
        "ridge_fit": ridge_fit,
        "ridge_r2": ridge_r2,
        "ridge_alpha": ridge_alpha,
        "model_frame": model_frame,
    }


def write_residuals(primary_result):
    """Save observed CO2, pressure features, fitted CO2, and residuals."""
    frame = primary_result["model_frame"].copy()
    frame["co2_fitted_barometric_ppm"] = primary_result["linear_fit"]
    frame["co2_residual_barometric_ppm"] = (
        frame[CO2_COL] - frame["co2_fitted_barometric_ppm"]
    )
    frame["barometric_pressure_source"] = primary_result["pressure_col"]

    keep_cols = [
        CO2_COL,
        primary_result["pressure_col"],
        *primary_result["feature_cols"][1:],
        "co2_fitted_barometric_ppm",
        "co2_residual_barometric_ppm",
        "barometric_pressure_source",
    ]
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    frame[keep_cols].to_csv(RESIDUAL_PATH, index_label="timestamp_utc")
    print(f"wrote {RESIDUAL_PATH} ({len(frame)} rows)")


def write_metrics(primary_result, weather_result, total_rows):
    """Write the Week 2 metric report used for the kill-check decision."""
    formula = (
        "CO2 ~ pressure + delta_pressure_1h + delta_pressure_3h + "
        "delta_pressure_6h + delta_pressure_12h + delta_pressure_24h"
    )
    status = kill_check_status(primary_result["linear_r2"])

    lines = [
        "Week 2 Barometric Baseline",
        "",
        f"Formula: {formula}",
        f"Official pressure source: {primary_result['pressure_col']}",
        f"Analysis window: {primary_result['window_start']} to {primary_result['window_end']}",
        f"Rows in joined frame: {total_rows}",
        f"Rows used after lag/dropna: {primary_result['n_rows']}",
        "",
        "Primary IoT-pressure model:",
        f"  Linear R2: {primary_result['linear_r2']:.6f}",
        f"  Ridge R2: {primary_result['ridge_r2']:.6f}",
        f"  Ridge alpha: {primary_result['ridge_alpha']}",
        "",
        "Kerkrade weather-pressure sensitivity:",
        f"  Rows used after lag/dropna: {weather_result['n_rows']}",
        f"  Linear R2: {weather_result['linear_r2']:.6f}",
        f"  Ridge R2: {weather_result['ridge_r2']:.6f}",
        f"  Ridge alpha: {weather_result['ridge_alpha']}",
        "",
        f"Kill Check 1 status: {status}",
        "Decision rule: R2 <= 0.85 proceed; 0.85 < R2 <= 0.95 proceed with caution; R2 > 0.95 pause/redirect.",
    ]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {METRICS_PATH}")


def write_plot(primary_result):
    """Plot observed CO2, fitted barometric CO2, and residuals."""
    frame = primary_result["model_frame"].copy()
    fitted = pd.Series(
        primary_result["linear_fit"],
        index=frame.index,
        name="co2_fitted_barometric_ppm",
    )
    residual = frame[CO2_COL] - fitted

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(12, 7),
        sharex=True,
        constrained_layout=True,
    )
    axes[0].plot(frame.index, frame[CO2_COL], label="Observed CO2", linewidth=1)
    axes[0].plot(frame.index, fitted, label="Barometric fit", linewidth=1)
    axes[0].set_ylabel("CO2 ppm")
    axes[0].set_title("Observed CO2 and pressure-only fit")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="upper right")

    axes[1].plot(frame.index, residual, label="Residual", linewidth=1, color="tab:orange")
    axes[1].axhline(0, color="black", linewidth=0.8, alpha=0.6)
    axes[1].set_ylabel("Residual ppm")
    axes[1].set_xlabel("timestamp_utc")
    axes[1].grid(True, alpha=0.25)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOT_PATH, dpi=160)
    plt.close(fig)
    print(f"wrote {PLOT_PATH}")


def main():
    """Command-line entry point."""
    frame = load_analysis_frame()
    primary = fit_baseline(frame, PRIMARY_PRESSURE_COL, "primary_iot_pressure")
    weather = fit_baseline(frame, WEATHER_PRESSURE_COL, "weather_pressure_sensitivity")

    write_residuals(primary)
    write_metrics(primary, weather, total_rows=len(frame))
    write_plot(primary)

    print(
        "Kill Check 1:",
        kill_check_status(primary["linear_r2"]),
        f"(official linear R2={primary['linear_r2']:.6f})",
    )


if __name__ == "__main__":
    main()
