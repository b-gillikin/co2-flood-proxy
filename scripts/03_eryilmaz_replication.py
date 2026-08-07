"""Reproduce the Eryilmaz comparison, and re-run it under the chapter's own inference.

This is the first rung of the chapter's substitution ladder: can public weather
stand in for indoor instrumentation? Eryilmaz answered yes, within 0.05 AUROC,
and that threshold is the decision rule the whole chapter inherits — see
`src/substitution.py`.

**Two results are reported, and they answer different questions.**

*Inherited procedure*: stratified random 5-fold cross-validation, exactly as
published. Random folds mix neighbouring hours in an autocorrelated series, so
this is a faithfulness check on the replication, not evidence of out-of-sample
skill.

*Chapter inference*: the same two score sets passed through `substitution_test`,
scored **within fold** and averaged, with a paired cluster bootstrap over folds.

Both are reported because they answer different questions: the first is whether
the replication is faithful, the second whether the finding survives an
evaluation where no future hour trains the model. They agree at +0.012 and
-0.012.

**Why within-fold.** Each fold is a separately fitted model, so its predicted
probabilities are not on a common scale. Pooling them into one AUROC ranks one
fit's scores against another's, which measures calibration drift as if it were
skill. Doing that here produced a -0.088 gap and an apparent sign flip that was
reported as the session's headline result on 2026-08-06 and withdrawn on
2026-08-07. `tests/test_substitution.py::GroupedScoringTests` guards it.
"""

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
from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import pressure_deltas
from src.substitution import format_result, substitution_test

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
    """Load the joined hourly analysis frame."""
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


def fit_blocked_predictions(replication_frame, spec):
    """Refit under forward-chaining folds, so no future hour trains the model.

    Random k-fold puts hour t-1 in the training set and hour t in the test set.
    In a series this autocorrelated that is close to reading the answer, and it
    inflates *both* models. A bootstrap widens the interval around such a number
    but cannot move the number, so passing random-fold scores into
    `substitution_test` and placing the result beside the precursor and donor
    rungs would launder them: those rungs have no fitting or use held-out
    storms.

    Forward chaining trains only on the past. The gap is expected to survive —
    leakage should flatter both models similarly — but that is a claim to
    demonstrate rather than assume, which is why both are reported.
    """
    x = model_matrix(replication_frame, spec)
    y = replication_frame["co2_leak_event"]
    ordered = replication_frame.sort_index()
    x, y = x.loc[ordered.index], y.loc[ordered.index]

    predictions = pd.DataFrame(index=ordered.index)
    predictions["co2_leak_event"] = y
    predictions["model_label"] = spec["label"]
    predictions["predicted_probability"] = float("nan")
    # Which fold produced each probability. Every fold is a different fitted
    # model, so its scores are only comparable within the fold; see
    # `src.substitution.substitution_test`.
    predictions["cv_fold"] = -1

    for fold, (train_idx, test_idx) in enumerate(
        TimeSeriesSplit(n_splits=N_SPLITS).split(x), start=1
    ):
        if y.iloc[train_idx].nunique() < 2:
            continue
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, solver="liblinear"),
        )
        model.fit(x.iloc[train_idx], y.iloc[train_idx])
        predictions.loc[x.index[test_idx], "cv_fold"] = fold
        predictions.loc[x.index[test_idx], "predicted_probability"] = model.predict_proba(
            x.iloc[test_idx]
        )[:, 1]
    return predictions.dropna(subset=["predicted_probability"])


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

    predictions["predicted_class"] = (predictions["predicted_probability"] >= 0.5).astype("int64")

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
    """Apply the inherited replication criterion."""
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


def write_metrics(summaries, all_predictions, blocked_predictions):
    """Write the replication AUROC report."""
    by_model = {row["model"]: row for row in summaries}
    auroc_a = by_model["A_indoor_iot"]["auroc"]
    auroc_b = by_model["B_outdoor_weather"]["auroc"]
    gap = auroc_a - auroc_b
    status = kill_check_status(auroc_a, auroc_b)

    lines = [
        "Eryilmaz Replication",
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
            f"Replication check: {status}",
            "Decision rule: Model B replicates if it is within 0.05 AUROC of Model A.",
            "Note: random 5-fold CV is used here only for faithful Eryilmaz replication.",
            "",
            "-" * 70,
            "Both blocks below score WITHIN fold and average. Each fold is a separate",
            "fit, so pooling its probabilities into one ranking measures calibration",
            "drift between fits as if it were skill. The pooled figure is printed for",
            "contrast only; where it diverges from the within-fold figure, that",
            "divergence is the artifact, not a result.",
            "",
            "-" * 70,
            "(a) Random folds — the inherited Eryilmaz procedure.",
            "",
            substitution_block(all_predictions),
            "",
            "-" * 70,
            "(b) Forward-chaining folds — no future hour trains the model, so this is",
            "    the evaluation comparable to the CO2 and donor rungs.",
            "",
            substitution_block(blocked_predictions),
            "",
            # Computed, never asserted. An earlier version stated the comparison
            # as literal prose ("the two agree at +0.012 and -0.012"), which was
            # true on the run that wrote it and would silently go false on the
            # next data refresh — a number compared against a number that is not
            # produced at all.
            scheme_comparison(all_predictions, blocked_predictions),
        ]
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {METRICS_PATH}")


def paired_result(all_predictions):
    """Run the two model frames through the shared harness, grouped by CV fold.

    Each fold is a separate fit, so its probabilities are only comparable within
    the fold; pooling them ranks one model's scores against another's and is
    sensitive to calibration drift. That pooling produced the withdrawn -0.088.
    """
    import numpy as np

    frames = {p["model_label"].iloc[0]: p.sort_index() for p in all_predictions}
    labels = list(frames)
    if len(labels) < 2:
        return None
    a, b = frames[labels[0]], frames[labels[1]]
    joined = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
    return substitution_test(
        joined["predicted_probability_a"],
        joined["predicted_probability_b"],
        joined["co2_leak_event_a"],
        name_a=labels[0],
        name_b=labels[1],
        groups=joined["cv_fold_a"] if "cv_fold_a" in joined else None,
        rng=np.random.default_rng(RANDOM_STATE),
    )


def substitution_block(all_predictions, label="scores"):
    """Render one substitution test as the block that goes into the report."""
    result = paired_result(all_predictions)
    if result is None:
        return "  (substitution test unavailable: fewer than two models)"
    return format_result(result)


def scheme_comparison(random_predictions, blocked_predictions):
    """Compare the two evaluation schemes from their values, never as prose.

    Every figure here is interpolated from the results computed in this run, so
    the paragraph cannot drift away from the blocks above it on a data refresh.
    """
    random_result = paired_result(random_predictions)
    blocked = paired_result(blocked_predictions)
    if random_result is None or blocked is None:
        return ""
    agree = max(abs(random_result.gap), abs(blocked.gap)) <= blocked.threshold
    lines = [
        "Comparing the two schemes, all figures computed above:",
        f"  within-fold gap: random folds {random_result.gap:+.3f}, "
        f"forward chaining {blocked.gap:+.3f}",
        f"  both {'are' if agree else 'are NOT'} inside Eryilmaz's "
        f"{blocked.threshold:.2f} threshold, so the substitution conclusion "
        f"{'does not depend' if agree else 'DEPENDS'} on the evaluation scheme",
        f"  forward chaining pooled {blocked.pooled_gap:+.3f} against within-fold "
        f"{blocked.gap:+.3f}: a {abs(blocked.pooled_gap - blocked.gap):.3f} pooling artifact",
        f"  Model A within fold: {random_result.auroc_a:.3f} random against "
        f"{blocked.auroc_a:.3f} forward-chaining — "
        f"{'no measurable' if blocked.auroc_a >= random_result.auroc_a else 'a'} "
        f"random-fold leakage penalty",
    ]
    return "\n".join(lines)


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
    blocked_predictions = []
    summaries = []

    for model_key, spec in MODEL_SPECS.items():
        predictions, summary = run_model(replication_frame, model_key, spec)
        all_predictions.append(predictions)
        blocked_predictions.append(fit_blocked_predictions(replication_frame, spec))
        summaries.append(summary)

    write_predictions(all_predictions)
    write_metrics(summaries, all_predictions, blocked_predictions)
    write_roc_plot(all_predictions)

    by_model = {row["model"]: row for row in summaries}
    auroc_a = by_model["A_indoor_iot"]["auroc"]
    auroc_b = by_model["B_outdoor_weather"]["auroc"]
    print(
        "Replication check:",
        kill_check_status(auroc_a, auroc_b),
        f"(A AUROC={auroc_a:.6f}; B AUROC={auroc_b:.6f}; gap={auroc_a - auroc_b:.6f})",
    )


if __name__ == "__main__":
    main()
