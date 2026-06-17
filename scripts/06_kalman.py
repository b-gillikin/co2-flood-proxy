"""July Week 2 provisional Kalman innovations model."""

from __future__ import annotations

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
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.models.july import (
    TARGET_COL,
    anomaly_table,
    available_exog,
    complete_model_frame,
    load_signal_frame,
)


PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/kalman")
MODELS_DIR = Path("results/models")

MODEL_PATH = MODELS_DIR / "kalman.pkl"
INNOVATION_PATH = PROCESSED_DIR / "kalman-innovations.csv"
ANOMALY_PATH = PROCESSED_DIR / "kalman-anomalies.csv"

RIDGE_ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)
Q_SCALES = (0.001, 0.01, 0.05, 0.1, 0.5)
R_SCALES = (0.25, 0.5, 1.0, 2.0)


def fit_exogenous_mean(model_frame, target_col, feature_cols):
    """Fit an observation-equation mean from exogenous regressors."""
    x = model_frame[feature_cols]
    y = model_frame[target_col]
    model = make_pipeline(StandardScaler(), RidgeCV(alphas=RIDGE_ALPHAS))
    model.fit(x, y)
    fitted = pd.Series(model.predict(x), index=model_frame.index)
    return model, fitted


def local_level_filter(observed, q, r):
    """Run a scalar local-level Kalman filter on a residualized series."""
    y = pd.Series(observed).astype(float)
    state = float(y.iloc[0])
    variance = float(max(y.var(ddof=0), 1e-6))
    rows = []

    for timestamp, value in y.items():
        predicted_state = state
        predicted_variance = variance + q
        innovation = float(value - predicted_state)
        innovation_variance = float(predicted_variance + r)
        gain = predicted_variance / innovation_variance
        state = predicted_state + gain * innovation
        variance = (1 - gain) * predicted_variance
        rows.append(
            {
                "timestamp_utc": timestamp,
                "predicted_state": predicted_state,
                "filtered_state": state,
                "innovation": innovation,
                "innovation_variance": innovation_variance,
                "standardized_innovation": innovation / np.sqrt(innovation_variance),
            }
        )
    return pd.DataFrame(rows)


def tune_q_r(residualized):
    """Choose Q/R by a compact likelihood grid."""
    residualized = pd.Series(residualized).astype(float)
    base_var = max(float(residualized.var(ddof=0)), 1e-6)
    rows = []
    for q_scale in Q_SCALES:
        for r_scale in R_SCALES:
            q = base_var * q_scale
            r = base_var * r_scale
            filtered = local_level_filter(residualized, q, r)
            innovation = filtered["innovation"]
            variance = filtered["innovation_variance"].clip(lower=1e-9)
            nll = float(0.5 * (np.log(2 * np.pi * variance) + (innovation**2) / variance).sum())
            rows.append(
                {
                    "q_scale": q_scale,
                    "r_scale": r_scale,
                    "q": q,
                    "r": r,
                    "negative_log_likelihood": nll,
                }
            )
    search = pd.DataFrame(rows).sort_values("negative_log_likelihood").reset_index(drop=True)
    best = search.iloc[0]
    return search, float(best["q"]), float(best["r"])


def fit_statsmodels_local_level(model_frame, target_col, feature_cols):
    """Fit the planned statsmodels local-level model when available."""
    try:
        from statsmodels.tsa.statespace.structural import UnobservedComponents
    except ImportError:
        return None

    y = model_frame[target_col].astype(float)
    x = model_frame[feature_cols].astype(float)
    try:
        model = UnobservedComponents(y, level="local level", exog=x)
        result = model.fit(disp=False, maxiter=300)
    except Exception:
        return None

    fitted = pd.Series(result.fittedvalues, index=model_frame.index)
    innovation = y - fitted
    scale = innovation.std(ddof=0)
    if pd.isna(scale) or scale == 0:
        standardized = pd.Series(0.0, index=model_frame.index)
    else:
        standardized = innovation / scale

    output = pd.DataFrame(
        {
            "timestamp_utc": model_frame.index,
            "observed": y.to_numpy(),
            "predicted": fitted.to_numpy(),
            "exog_fitted": np.nan,
            "predicted_state": np.nan,
            "filtered_state": np.nan,
            "innovation": innovation.to_numpy(),
            "innovation_variance": scale**2,
            "standardized_innovation": standardized.to_numpy(),
        }
    )
    return result, output


def write_plots(output):
    """Plot innovations and standardized innovations."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, constrained_layout=True)
    axes[0].plot(output["timestamp_utc"], output["observed"], label="Observed", linewidth=1)
    axes[0].plot(
        output["timestamp_utc"],
        output["predicted"],
        label="Exog + local level",
        linewidth=1,
    )
    axes[0].set_title("Kalman local-level fit")
    axes[0].set_ylabel("Residual ppm")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="upper right")

    axes[1].plot(output["timestamp_utc"], output["standardized_innovation"], linewidth=1)
    axes[1].axhline(3, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    axes[1].axhline(-3, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    axes[1].set_ylabel("Std innovation")
    axes[1].set_xlabel("timestamp_utc")
    axes[1].grid(True, alpha=0.25)
    fig.savefig(RESULTS_DIR / "innovations.png", dpi=160)
    plt.close(fig)


def write_summary(search, q, r, feature_cols, n_rows, model_type):
    """Write the Kalman specification and tuning result."""
    lines = [
        "July Week 2 Kalman Innovations",
        "",
        "Status: provisional pipeline-first run.",
        f"Specification: {model_type}.",
        f"Rows used: {n_rows}",
        f"Exogenous features used: {', '.join(feature_cols)}",
    ]
    if search is not None:
        lines.extend(
            [
                f"Selected Q: {q:.6f}",
                f"Selected R: {r:.6f}",
                "",
                "Top covariance grid rows:",
                search.head(8).to_string(index=False),
            ]
        )
    (RESULTS_DIR / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_signal_frame()
    feature_cols = available_exog(frame)
    model_frame, feature_cols = complete_model_frame(frame, TARGET_COL, feature_cols)
    statsmodels_fit = fit_statsmodels_local_level(model_frame, TARGET_COL, feature_cols)
    if statsmodels_fit is None:
        mean_model, exog_fitted = fit_exogenous_mean(model_frame, TARGET_COL, feature_cols)
        residualized = model_frame[TARGET_COL] - exog_fitted
        search, q, r = tune_q_r(residualized)
        filtered = local_level_filter(residualized, q, r)

        output = filtered.copy()
        output["timestamp_utc"] = pd.to_datetime(output["timestamp_utc"], utc=True)
        output = output.set_index("timestamp_utc")
        output["observed"] = model_frame.loc[output.index, TARGET_COL]
        output["exog_fitted"] = exog_fitted.loc[output.index]
        output["predicted"] = output["exog_fitted"] + output["predicted_state"]
        output = output.reset_index()
        model_type = "exogenous Ridge mean + scalar local-level Kalman fallback"
        model_payload = {
            "model_type": "ridge_exog_local_level",
            "target_col": TARGET_COL,
            "feature_cols": feature_cols,
            "mean_model": mean_model,
            "q": q,
            "r": r,
        }
    else:
        result, output = statsmodels_fit
        search = None
        q = np.nan
        r = np.nan
        model_type = "statsmodels local-level state-space model with exogenous regressors"
        model_payload = {
            "model_type": "statsmodels_unobserved_components",
            "target_col": TARGET_COL,
            "feature_cols": feature_cols,
            "model": result,
        }

    anomalies = anomaly_table(
        pd.DatetimeIndex(output["timestamp_utc"]),
        output["standardized_innovation"],
        prefix="kalman",
        mad_threshold=3.5,
        z_threshold=3.0,
    )
    anomalies["kalman_anomaly"] = output["standardized_innovation"].abs().to_numpy() > 3

    output.to_csv(INNOVATION_PATH, index=False)
    anomalies.to_csv(ANOMALY_PATH, index=False)
    if search is not None:
        search.to_csv(RESULTS_DIR / "covariance_grid.csv", index=False)
    else:
        pd.DataFrame(
            [
                {
                    "status": "not_applicable",
                    "reason": "statsmodels fit estimated state-space covariance directly",
                }
            ]
        ).to_csv(RESULTS_DIR / "covariance_grid.csv", index=False)

    with MODEL_PATH.open("wb") as handle:
        pickle.dump(model_payload, handle)

    write_plots(output)
    write_summary(search, q, r, feature_cols, len(output), model_type)

    print(f"wrote {MODEL_PATH}")
    print(f"wrote {INNOVATION_PATH} ({len(output)} rows)")
    print(f"wrote {ANOMALY_PATH} ({len(anomalies)} rows)")


if __name__ == "__main__":
    main()
