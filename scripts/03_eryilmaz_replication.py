"""Week 3 Eryilmaz logistic-regression replication and Kill Check 2."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import pressure_deltas


INTERIM_DIR = Path("data/interim")
PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/eryilmaz")

INPUT_PATH = INTERIM_DIR / "analysis_hourly.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "eryilmaz_replication_predictions.csv"
METRICS_PATH = RESULTS_DIR / "auroc.txt"
PLOT_PATH = RESULTS_DIR / "roc_curves.png"

TARGET_COL = "iot_co2_ppm"
TARGET_THRESHOLD_PPM = 1000
DELTA_LAG_HOURS = 6
N_SPLITS = 5
RANDOM_STATE = 42

MODEL_SPECS = {
    "A_indoor_iot": {
        "label": "Model A: indoor IoT",
        "feature_map": {
            "temperature_c": "iot_temperature_c",
            "relative_humidity_pct": "iot_relative_humidity_pct",
            "pressure_hpa": "iot_air_pressure_hpa",
            "delta_pressure_6h": "iot_delta_pressure_6h",
        },
    },
    "B_outdoor_weather": {
        "label": "Model B: outdoor weather",
        "feature_map": {
            "temperature_c": "kerkrade_weather_temp_c",
            "relative_humidity_pct": "kerkrade_weather_relative_humidity_pct",
            "pressure_hpa": "kerkrade_weather_pressure_hpa",
            "delta_pressure_6h": "weather_delta_pressure_6h",
        },
    },
}


def load_analysis_frame(path=INPUT_PATH):
    """Load the joined Week 1 hourly analysis frame."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return frame.set_index("timestamp_utc").sort_index()


def build_replication_frame(frame):
    """Create the shared complete-case frame used by both replication models."""
    columns = [
        TARGET_COL,
        "iot_temperature_c",
        "iot_relative_humidity_pct",
        "iot_air_pressure_hpa",
        "kerkrade_weather_temp_c",
        "kerkrade_weather_relative_humidity_pct",
        "kerkrade_weather_pressure_hpa",
    ]
    out = frame[columns].copy()
    out = pressure_deltas(
        out,
        lags=(DELTA_LAG_HOURS,),
        pressure_col="iot_air_pressure_hpa",
    ).rename(columns={"delta_pressure_6h": "iot_delta_pressure_6h"})
    out = pressure_deltas(
        out,
        lags=(DELTA_LAG_HOURS,),
        pressure_col="kerkrade_weather_pressure_hpa",
    ).rename(columns={"delta_pressure_6h": "weather_delta_pressure_6h"})

    required = [
        TARGET_COL,
        *MODEL_SPECS["A_indoor_iot"]["feature_map"].values(),
        *MODEL_SPECS["B_outdoor_weather"]["feature_map"].values(),
    ]
    out = out.dropna(subset=required)
    out["co2_leak_event"] = (out[TARGET_COL] > TARGET_THRESHOLD_PPM).astype("int64")
    return out


def model_matrix(replication_frame, spec):
    """Return a model-specific X matrix with canonical feature names."""
    return replication_frame[list(spec["feature_map"].values())].rename(
        columns={source: target for target, source in spec["feature_map"].items()}
    )


def fit_cv_predictions(replication_frame, spec):
    """Run faithful random 5-fold logistic-regression replication."""
    x = model_matrix(replication_frame, spec)
    y = replication_frame["co2_leak_event"]
    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    predictions = pd.DataFrame(index=replication_frame.index)
    predictions["co2_leak_event"] = y
    predictions["co2_ppm"] = replication_frame[TARGET_COL]
    predictions["cv_fold"] = -1
    predictions["predicted_probability"] = float("nan")

    for fold, (train_idx, test_idx) in enumerate(cv.split(x, y), start=1):
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, solver="liblinear"),
        )
        model.fit(x.iloc[train_idx], y.iloc[train_idx])
        test_index = x.index[test_idx]
        predictions.loc[test_index, "cv_fold"] = fold
        predictions.loc[test_index, "predicted_probability"] = model.predict_proba(
            x.iloc[test_idx]
        )[:, 1]

    predictions["predicted_class"] = (
        predictions["predicted_probability"] >= 0.5
    ).astype("int64")

    auc = roc_auc_score(
        predictions["co2_leak_event"],
        predictions["predicted_probability"],
    )
    return predictions, auc


def run_model(replication_frame, model_key, spec):
    """Build data, run CV, and return predictions plus summary metrics."""
    predictions, auroc = fit_cv_predictions(replication_frame, spec)
    predictions = predictions.reset_index().rename(columns={"index": "timestamp_utc"})
    predictions.insert(0, "model", model_key)
    predictions.insert(1, "model_label", spec["label"])

    summary = {
        "model": model_key,
        "model_label": spec["label"],
        "n_rows": len(predictions),
        "positive_events": int(predictions["co2_leak_event"].sum()),
        "negative_events": int((1 - predictions["co2_leak_event"]).sum()),
        "auroc": auroc,
        "window_start": predictions["timestamp_utc"].min(),
        "window_end": predictions["timestamp_utc"].max(),
    }
    return predictions, summary


def kill_check_status(auroc_a, auroc_b):
    """Apply the June Week 3 replication criterion."""
    gap = auroc_a - auroc_b
    if gap <= 0.05:
        return "replicates / proceed"
    return "does not replicate yet / diagnose"


def write_predictions(all_predictions):
    """Save cross-validated probabilities for both Eryilmaz models."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    predictions = pd.concat(all_predictions, ignore_index=True)
    predictions.to_csv(PREDICTIONS_PATH, index=False)
    print(f"wrote {PREDICTIONS_PATH} ({len(predictions)} rows)")


def write_metrics(summaries):
    """Write AUROC report and Kill Check 2 status."""
    by_model = {row["model"]: row for row in summaries}
    auroc_a = by_model["A_indoor_iot"]["auroc"]
    auroc_b = by_model["B_outdoor_weather"]["auroc"]
    gap = auroc_a - auroc_b
    status = kill_check_status(auroc_a, auroc_b)

    lines = [
        "Week 3 Eryilmaz Replication",
        "",
        f"Target: {TARGET_COL} > {TARGET_THRESHOLD_PPM} ppm",
        f"CV: Stratified random {N_SPLITS}-fold, random_state={RANDOM_STATE}",
        "Model: StandardScaler + LogisticRegression(max_iter=1000, solver='liblinear')",
        "",
    ]
    for row in summaries:
        lines.extend(
            [
                row["model_label"],
                f"  Rows used after lag/dropna: {row['n_rows']}",
                f"  Positive events: {row['positive_events']}",
                f"  Negative events: {row['negative_events']}",
                f"  Analysis window: {row['window_start']} to {row['window_end']}",
                f"  AUROC: {row['auroc']:.6f}",
                "",
            ]
        )
    lines.extend(
        [
            f"AUROC gap (A - B): {gap:.6f}",
            f"Kill Check 2 status: {status}",
            "Decision rule: Model B replicates if it is within 0.05 AUROC of Model A.",
            "Note: random 5-fold CV is used here only for faithful Eryilmaz replication; later chapter models should use time-aware evaluation.",
        ]
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {METRICS_PATH}")


def write_roc_plot(all_predictions):
    """Plot cross-validated ROC curves for both replication models."""
    fig, axis = plt.subplots(figsize=(7, 6), constrained_layout=True)

    for predictions in all_predictions:
        label = predictions["model_label"].iloc[0]
        y_true = predictions["co2_leak_event"]
        y_score = predictions["predicted_probability"]
        fpr, tpr, _ = roc_curve(y_true, y_score)
        auroc = roc_auc_score(y_true, y_score)
        axis.plot(fpr, tpr, linewidth=2, label=f"{label} (AUROC {auroc:.3f})")

    axis.plot([0, 1], [0, 1], color="black", linewidth=1, linestyle="--", alpha=0.5)
    axis.set_xlabel("False positive rate")
    axis.set_ylabel("True positive rate")
    axis.set_title("Eryilmaz replication ROC curves")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="lower right")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOT_PATH, dpi=160)
    plt.close(fig)
    print(f"wrote {PLOT_PATH}")


def main():
    """Command-line entry point."""
    frame = load_analysis_frame()
    replication_frame = build_replication_frame(frame)
    all_predictions = []
    summaries = []

    for model_key, spec in MODEL_SPECS.items():
        predictions, summary = run_model(replication_frame, model_key, spec)
        all_predictions.append(predictions)
        summaries.append(summary)

    write_predictions(all_predictions)
    write_metrics(summaries)
    write_roc_plot(all_predictions)

    by_model = {row["model"]: row for row in summaries}
    auroc_a = by_model["A_indoor_iot"]["auroc"]
    auroc_b = by_model["B_outdoor_weather"]["auroc"]
    print(
        "Kill Check 2:",
        kill_check_status(auroc_a, auroc_b),
        f"(A AUROC={auroc_a:.6f}; B AUROC={auroc_b:.6f}; gap={auroc_a - auroc_b:.6f})",
    )


if __name__ == "__main__":
    main()
