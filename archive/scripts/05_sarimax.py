"""Fit the residual autoregression detector with an explicit model family."""

from __future__ import annotations

import argparse
import os
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.detectors import (
    fit_detector,
    model_payload,
    score_detector,
    select_sarimax_spec,
    state_space_features,
)
from src.models.signal_frame import (
    CO2_COL,
    TARGET_COL,
    anomaly_table,
    autocorrelation,
    complete_model_frame,
    contiguous_blocks,
    load_signal_frame,
    select_features_by_joint_coverage,
)

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/sarimax")
MODELS_DIR = Path("results/models")

MODEL_PATH = MODELS_DIR / "sarimax.pkl"
ORDER_SEARCH_PATH = MODELS_DIR / "sarimax_order_search.csv"
RESIDUAL_PATH = PROCESSED_DIR / "sarimax-residuals.csv"
ANOMALY_PATH = PROCESSED_DIR / "sarimax-anomalies.csv"

MIN_BLOCK_HOURS = 168


def stationarity_tests(series, name):
    """Run ADF/KPSS and record the level-versus-difference decision."""
    series = pd.Series(series).dropna().astype(float)
    row = {"series": name, "n_rows": len(series), "skew": series.skew()}
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
    except ImportError:
        row.update(
            {
                "adf_pvalue": np.nan,
                "kpss_pvalue": np.nan,
                "decision": "not_tested_statsmodels_unavailable",
                "difference_order": 0,
            }
        )
        return row

    adf = adfuller(series, autolag="AIC")
    kpss_result = kpss(series, regression="c", nlags="auto")
    nonstationary = adf[1] > 0.05 and kpss_result[1] < 0.05
    row.update(
        {
            "adf_pvalue": adf[1],
            "kpss_pvalue": kpss_result[1],
            "decision": "difference" if nonstationary else "keep_level",
            "difference_order": int(nonstationary),
        }
    )
    return row


def co2_transform_decision(series):
    """Record, but do not apply, the CO2 transformation diagnostic."""
    series = pd.Series(series).dropna().astype(float)
    skew = series.skew()
    if bool((series > 0).all()) and abs(skew) > 2:
        transformed, lambda_value = stats.boxcox(series)
        return {
            "series": CO2_COL,
            "transform": "boxcox",
            "lambda": lambda_value,
            "original_skew": skew,
            "transformed_skew": pd.Series(transformed).skew(),
        }
    return {
        "series": CO2_COL,
        "transform": "none",
        "lambda": np.nan,
        "original_skew": skew,
        "transformed_skew": skew,
    }


def fit_selected_blocks(model_frame, target_col, spec, model_key):
    """Refit the selected family per gapless block and collect honest scores."""
    outputs = []
    statuses = []
    representative = None
    representative_hours = 0
    blocks = contiguous_blocks(model_frame.index, min_hours=MIN_BLOCK_HOURS)
    for block_id, index in blocks:
        y = model_frame.loc[index, target_col]
        x = model_frame.loc[index, list(spec.features)]
        fit = fit_detector(spec, y, x)
        statuses.append(
            {
                "block_id": block_id,
                "block_start_utc": index.min(),
                "block_end_utc": index.max(),
                "block_hours": len(index),
                "model_family": spec.family,
                "fit_status": fit.status,
                "fit_detail": fit.detail,
                **fit.diagnostics,
            }
        )
        if fit.status != "ok":
            continue
        scored = score_detector(fit, in_sample=True)
        score_index = scored.score.index
        observed = y.diff(spec.order[1]) if spec.family == "arx" and spec.order[1] else y
        outputs.append(
            pd.DataFrame(
                {
                    "timestamp_utc": score_index,
                    "target": target_col,
                    "observed": observed.reindex(score_index).to_numpy(),
                    "fitted": scored.prediction.reindex(score_index).to_numpy(),
                    "sarimax_residual": scored.score.to_numpy(),
                    "model_type": spec.family,
                    "model_key": model_key,
                    "block_id": block_id,
                    "fit_status": fit.status,
                }
            )
        )
        if len(index) > representative_hours:
            representative = fit
            representative_hours = len(index)

    if not outputs or representative is None:
        raise RuntimeError("Selected residual model did not fit any qualifying block")
    residuals = pd.concat(outputs, ignore_index=True).sort_values("timestamp_utc")
    return residuals, pd.DataFrame(statuses), representative


def write_residual_plots(residuals):
    """Write residual time-series, ACF, and Q-Q diagnostics."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    residual = residuals["sarimax_residual"]

    fig, axis = plt.subplots(figsize=(12, 4), constrained_layout=True)
    axis.plot(residuals["timestamp_utc"], residual, linewidth=1)
    axis.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    axis.set_title("Residual autoregression errors")
    axis.set_ylabel("Residual")
    axis.grid(True, alpha=0.25)
    fig.savefig(RESULTS_DIR / "residual_timeseries.png", dpi=160)
    plt.close(fig)

    acf = autocorrelation(residual, max_lag=48)
    fig, axis = plt.subplots(figsize=(9, 4), constrained_layout=True)
    axis.bar(acf["lag"], acf["acf"], width=0.8)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_title("Residual autocorrelation")
    axis.set_xlabel("Lag hours")
    axis.set_ylabel("ACF")
    fig.savefig(RESULTS_DIR / "residual_acf.png", dpi=160)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(5, 5), constrained_layout=True)
    stats.probplot(residual.dropna(), dist="norm", plot=axis)
    axis.set_title("Residual Q-Q plot")
    fig.savefig(RESULTS_DIR / "residual_qq.png", dpi=160)
    plt.close(fig)


def write_summary(stationarity, transform, search, spec):
    """Write the selected family, features, and convergence audit trail."""
    selected = search.loc[search["selected"]].iloc[0]
    lines = [
        "Residual Autoregression Detector",
        "",
        "Status: provisional pipeline run.",
        f"Selected model family: {spec.family}",
        f"Selected model key: {selected['model_key']}",
        f"Fit status: {selected['fit_status']}",
        f"Order: {selected['order']}",
        f"Seasonal order: {selected['seasonal_order']}",
        f"Controls: {', '.join(spec.features)}",
        "Pressure controls: excluded because the target is already pressure-separated.",
        "",
        "Stationarity decisions:",
    ]
    for row in stationarity:
        lines.append(
            f"  {row['series']}: {row['decision']} "
            f"(ADF p={row['adf_pvalue']}, KPSS p={row['kpss_pvalue']})"
        )
    lines.extend(
        [
            "",
            f"CO2 transform diagnostic: {transform['transform']} "
            f"(skew={transform['original_skew']:.3f}); not applied to the residual target.",
        ]
    )
    if spec.family == "arx":
        lines.append(
            "Interpretation: no tested SARIMAX candidate converged; the reported detector is AR-X."
        )
    else:
        lines.append("Interpretation: the reported detector is a converged SARIMAX fit.")
    (RESULTS_DIR / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-weekly-sensitivity",
        action="store_true",
        help="Also test a weekly seasonal sensitivity after a nonseasonal fit converges.",
    )
    parser.add_argument(
        "--full-grid",
        action="store_true",
        help="Use the full p,q grid instead of the compact default.",
    )
    parser.add_argument("--maxiter", type=int, default=80)
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_signal_frame()
    feature_cols = state_space_features(frame)
    feature_cols, feature_audit = select_features_by_joint_coverage(
        frame,
        target_col=TARGET_COL,
        required=feature_cols,
    )
    model_frame, feature_cols = complete_model_frame(frame, TARGET_COL, feature_cols)
    feature_audit.to_csv(RESULTS_DIR / "feature_coverage.csv", index=False)
    blocks = contiguous_blocks(model_frame.index, min_hours=MIN_BLOCK_HOURS)
    if not blocks:
        raise RuntimeError("No contiguous block is long enough for residual model selection")
    selection_index = max(blocks, key=lambda item: len(item[1]))[1]

    stationarity = [
        stationarity_tests(frame[CO2_COL], CO2_COL),
        stationarity_tests(frame[TARGET_COL], TARGET_COL),
    ]
    difference_order = int(
        next(row["difference_order"] for row in stationarity if row["series"] == TARGET_COL)
    )
    transform = co2_transform_decision(frame[CO2_COL])
    spec, _, search = select_sarimax_spec(
        model_frame.loc[selection_index, TARGET_COL],
        model_frame.loc[selection_index, feature_cols],
        feature_cols,
        difference_order=difference_order,
        full_grid=args.full_grid,
        include_daily=True,
        include_weekly=args.include_weekly_sensitivity,
        maxiter=args.maxiter,
    )
    best_key = search.loc[search["selected"], "model_key"].iloc[0]
    residuals, block_status, representative = fit_selected_blocks(
        model_frame,
        TARGET_COL,
        spec,
        best_key,
    )
    anomalies = anomaly_table(
        pd.DatetimeIndex(residuals["timestamp_utc"]),
        residuals["sarimax_residual"],
        prefix="sarimax",
    )

    search.to_csv(ORDER_SEARCH_PATH, index=False)
    block_status.to_csv(RESULTS_DIR / "block_fit_status.csv", index=False)
    residuals.to_csv(RESIDUAL_PATH, index=False)
    anomalies.to_csv(ANOMALY_PATH, index=False)
    with MODEL_PATH.open("wb") as handle:
        pickle.dump(
            model_payload(
                spec,
                representative,
                model_key=best_key,
                fitted_detector=representative,
                feature_cols=feature_cols,
                target_col=TARGET_COL,
                difference_order=difference_order,
                stationarity=stationarity,
                co2_transform=transform,
                order=spec.order,
                seasonal_order=spec.seasonal_order,
                min_block_hours=MIN_BLOCK_HOURS,
            ),
            handle,
        )

    write_residual_plots(residuals)
    write_summary(stationarity, transform, search, spec)
    print(f"wrote {MODEL_PATH}")
    print(f"wrote {RESIDUAL_PATH} ({len(residuals)} rows)")
    print(f"wrote {ANOMALY_PATH} ({len(anomalies)} rows)")
    print(f"selected {best_key} ({spec.family})")


if __name__ == "__main__":
    main()
