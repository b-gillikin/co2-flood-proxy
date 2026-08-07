"""Fit the local-level detector with an explicit, reusable model family."""

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
import pandas as pd

from src.detectors import (
    fit_detector,
    model_payload,
    score_detector,
    select_kalman_spec,
    state_space_features,
)
from src.models.signal_frame import (
    TARGET_COL,
    anomaly_table,
    complete_model_frame,
    contiguous_blocks,
    load_signal_frame,
    select_features_by_joint_coverage,
)

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/kalman")
MODELS_DIR = Path("results/models")

MODEL_PATH = MODELS_DIR / "kalman.pkl"
INNOVATION_PATH = PROCESSED_DIR / "kalman-innovations.csv"
ANOMALY_PATH = PROCESSED_DIR / "kalman-anomalies.csv"

MIN_BLOCK_HOURS = 72


def fit_selected_blocks(model_frame, target_col, spec):
    """Refit the selected family per gapless block and collect innovations."""
    outputs = []
    statuses = []
    representative = None
    representative_hours = 0
    for block_id, index in contiguous_blocks(model_frame.index, min_hours=MIN_BLOCK_HOURS):
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
        outputs.append(
            pd.DataFrame(
                {
                    "timestamp_utc": score_index,
                    "block_id": block_id,
                    "observed": y.reindex(score_index).to_numpy(),
                    "predicted": scored.prediction.reindex(score_index).to_numpy(),
                    "standardized_innovation": scored.score.to_numpy(),
                    "model_type": spec.family,
                    "fit_status": fit.status,
                }
            )
        )
        if len(index) > representative_hours:
            representative = fit
            representative_hours = len(index)
    if not outputs or representative is None:
        raise RuntimeError("Selected local-level family did not fit any qualifying block")
    output = pd.concat(outputs, ignore_index=True).sort_values("timestamp_utc")
    return output, pd.DataFrame(statuses), representative


def write_plots(output):
    """Plot fitted values and standardized innovations."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, constrained_layout=True)
    axes[0].plot(output["timestamp_utc"], output["observed"], label="Observed", linewidth=1)
    axes[0].plot(
        output["timestamp_utc"],
        output["predicted"],
        label="Predicted",
        linewidth=1,
    )
    axes[0].set_title("Local-level detector fit")
    axes[0].set_ylabel("Residual ppm")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="upper right")

    axes[1].plot(output["timestamp_utc"], output["standardized_innovation"], linewidth=1)
    axes[1].axhline(3, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    axes[1].axhline(-3, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    axes[1].set_ylabel("Standardized innovation")
    axes[1].set_xlabel("timestamp_utc")
    axes[1].grid(True, alpha=0.25)
    fig.savefig(RESULTS_DIR / "innovations.png", dpi=160)
    plt.close(fig)


def write_summary(search, spec, output):
    """Write the actual family, controls, and convergence status."""
    selected = search.loc[search["selected"]].iloc[0]
    lines = [
        "Local-Level Innovations Detector",
        "",
        "Status: provisional pipeline run.",
        f"Selected model family: {spec.family}",
        f"Fit status: {selected['fit_status']}",
        f"Rows used: {len(output)}",
        f"Controls: {', '.join(spec.features)}",
        "Pressure controls: excluded because the target is already pressure-separated.",
    ]
    if spec.family == "ridge_local_level":
        lines.append(
            "Interpretation: the joint state-space optimizer did not converge; "
            "the reported detector is Ridge + scalar local-level filtering."
        )
    else:
        lines.append(
            "Interpretation: the reported detector is a converged jointly estimated "
            "local-level state-space model."
        )
    (RESULTS_DIR / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maxiter", type=int, default=300)
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
        raise RuntimeError("No contiguous block is long enough for local-level selection")
    selection_index = max(blocks, key=lambda item: len(item[1]))[1]
    spec, _, search = select_kalman_spec(
        model_frame.loc[selection_index, TARGET_COL],
        model_frame.loc[selection_index, feature_cols],
        feature_cols,
        maxiter=args.maxiter,
    )
    output, block_status, representative = fit_selected_blocks(
        model_frame,
        TARGET_COL,
        spec,
    )

    anomalies = anomaly_table(
        pd.DatetimeIndex(output["timestamp_utc"]),
        output["standardized_innovation"],
        prefix="kalman",
    )
    output.to_csv(INNOVATION_PATH, index=False)
    anomalies.to_csv(ANOMALY_PATH, index=False)
    search.to_csv(RESULTS_DIR / "model_family_search.csv", index=False)
    block_status.to_csv(RESULTS_DIR / "block_fit_status.csv", index=False)
    if representative.tuning.empty:
        pd.DataFrame(
            [
                {
                    "status": "not_applicable",
                    "reason": "state-space covariance estimated jointly",
                }
            ]
        ).to_csv(RESULTS_DIR / "covariance_grid.csv", index=False)
    else:
        representative.tuning.to_csv(RESULTS_DIR / "covariance_grid.csv", index=False)

    with MODEL_PATH.open("wb") as handle:
        pickle.dump(
            model_payload(
                spec,
                representative,
                fitted_detector=representative,
                feature_cols=feature_cols,
                target_col=TARGET_COL,
                min_block_hours=MIN_BLOCK_HOURS,
                q=representative.q,
                r=representative.r,
            ),
            handle,
        )

    write_plots(output)
    write_summary(search, spec, output)
    print(f"wrote {MODEL_PATH}")
    print(f"wrote {INNOVATION_PATH} ({len(output)} rows)")
    print(f"wrote {ANOMALY_PATH} ({len(anomalies)} rows)")
    print(f"selected {spec.family}")


if __name__ == "__main__":
    main()
