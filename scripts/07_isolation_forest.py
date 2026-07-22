"""July Week 3 Isolation Forest anomaly scoring."""

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

from src.detectors import (
    DetectorSpec,
    fit_detector,
    iforest_features,
    model_payload,
    score_detector,
)
from src.models.july import (
    CO2_COL,
    anomaly_table,
    load_signal_frame,
)

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/iforest")
MODELS_DIR = Path("results/models")

MODEL_PATH = MODELS_DIR / "iforest.pkl"
SCORES_PATH = PROCESSED_DIR / "iforest-scores.csv"
ANOMALIES_PATH = PROCESSED_DIR / "iforest-anomalies.csv"

# The anomaly score does not depend on the contamination setting, so one
# forest is fit and contamination levels become score-quantile sensitivity
# flags. The official flag is the shared robust-MAD rule used by all three
# detectors; a fixed contamination would hard-code the reported anomaly rate.
CONTAMINATIONS = (0.03, 0.05, 0.10)


def feature_columns(frame):
    """Return the shared Isolation Forest feature contract."""
    return iforest_features(frame)


def fit_iforest(x):
    """Fit the shared Isolation Forest and return its sklearn model."""
    spec = DetectorSpec(
        detector="iforest",
        family="isolation_forest",
        features=tuple(x.columns),
    )
    fit = fit_detector(spec, x=x)
    if fit.status != "ok":
        raise RuntimeError(f"Isolation Forest fit status: {fit.status}: {fit.detail}")
    return fit.model


def write_plot(scores):
    """Plot official Isolation Forest score and anomaly flags."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, constrained_layout=True)
    axes[0].plot(scores["timestamp_utc"], scores[CO2_COL], linewidth=1, label="CO2")
    axes[0].scatter(
        scores.loc[scores["iforest_anomaly"], "timestamp_utc"],
        scores.loc[scores["iforest_anomaly"], CO2_COL],
        color="tab:red",
        s=20,
        label="IF anomaly",
    )
    axes[0].set_ylabel("CO2 ppm")
    axes[0].set_title("Isolation Forest provisional anomaly flags")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="upper right")

    axes[1].plot(scores["timestamp_utc"], scores["iforest_score"], linewidth=1)
    axes[1].set_ylabel("Anomaly score")
    axes[1].set_xlabel("timestamp_utc")
    axes[1].grid(True, alpha=0.25)
    fig.savefig(RESULTS_DIR / "iforest_scores.png", dpi=160)
    plt.close(fig)


def write_summary(scores, feature_cols):
    """Write a compact Isolation Forest summary."""
    lines = [
        "July Week 3 Isolation Forest",
        "",
        "Status: provisional pipeline-first run.",
        f"Rows used: {len(scores)}",
        "Official flag: robust-MAD rule on the anomaly score (|robust z| > 3.5),",
        "matching the SARIMAX and Kalman official flags.",
        f"Official anomaly count: {int(scores['iforest_anomaly'].sum())}",
        f"Features used ({len(feature_cols)}): {', '.join(feature_cols)}",
        "",
        "Contamination score-quantile sensitivity counts:",
    ]
    for contamination in CONTAMINATIONS:
        column = f"iforest_anomaly_{str(contamination).replace('.', 'p')}"
        lines.append(f"  {contamination}: {int(scores[column].sum())}")
    (RESULTS_DIR / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_signal_frame()
    features, feature_audit = iforest_features(frame, return_audit=True)
    model_frame = frame[features].replace([np.inf, -np.inf], np.nan).dropna()
    x = model_frame[features]

    scores = pd.DataFrame(
        {
            "timestamp_utc": model_frame.index,
            CO2_COL: model_frame[CO2_COL].to_numpy(dtype=float),
        }
    )
    spec = DetectorSpec(
        detector="iforest",
        family="isolation_forest",
        features=tuple(features),
    )
    fit = fit_detector(spec, x=x)
    if fit.status != "ok":
        raise RuntimeError(f"Isolation Forest fit status: {fit.status}: {fit.detail}")
    raw_score = score_detector(fit, in_sample=True).score.to_numpy()
    scores["iforest_score"] = raw_score

    contamination_thresholds = {}
    for contamination in CONTAMINATIONS:
        token = str(contamination).replace(".", "p")
        threshold = float(np.quantile(raw_score, 1 - contamination))
        contamination_thresholds[contamination] = threshold
        scores[f"iforest_anomaly_{token}"] = raw_score >= threshold

    official = anomaly_table(
        pd.DatetimeIndex(scores["timestamp_utc"]),
        raw_score,
        prefix="iforest",
    )
    scores["iforest_robust_z"] = official["iforest_robust_z"].to_numpy()
    scores["iforest_scored"] = official["iforest_scored"].to_numpy()
    scores["iforest_anomaly"] = official["iforest_anomaly"].to_numpy()

    sensitivity_cols = [
        column for column in scores.columns if column.startswith("iforest_anomaly_")
    ]
    anomalies = scores[["timestamp_utc", "iforest_scored", "iforest_anomaly", *sensitivity_cols]]

    feature_audit.to_csv(RESULTS_DIR / "feature_coverage.csv", index=False)
    scores.to_csv(SCORES_PATH, index=False)
    anomalies.to_csv(ANOMALIES_PATH, index=False)
    with MODEL_PATH.open("wb") as handle:
        pickle.dump(
            model_payload(
                spec,
                fit,
                fitted_detector=fit,
                features=features,
                official_flag="robust_mad_3p5_on_score",
                contamination_thresholds=contamination_thresholds,
            ),
            handle,
        )

    write_plot(scores)
    write_summary(scores, features)

    print(f"wrote {MODEL_PATH}")
    print(f"wrote {SCORES_PATH} ({len(scores)} rows)")
    print(f"wrote {ANOMALIES_PATH} ({len(anomalies)} rows)")


if __name__ == "__main__":
    main()
