"""Synthetic anomaly injection using the persisted pipeline detector families."""

from __future__ import annotations

import os
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
    flag_scores,
    load_detector_spec,
    score_detector,
)
from src.models.july import TARGET_COL, complete_model_frame, contiguous_blocks, load_signal_frame

RESULTS_DIR = Path("results/synthetic_injection")
MODEL_PATHS = {
    "sarimax": Path("results/models/sarimax.pkl"),
    "kalman": Path("results/models/kalman.pkl"),
    "iforest": Path("results/models/iforest.pkl"),
}

RANDOM_STATE = 42
MIN_BLOCK_HOURS = 168


def load_pipeline_specs() -> dict[str, DetectorSpec]:
    """Load the exact families selected by the full-record detector scripts."""
    return {detector: load_detector_spec(path, detector) for detector, path in MODEL_PATHS.items()}


def injection_templates(series):
    """Create deterministic injections with known anomaly windows."""
    rng = np.random.default_rng(RANDOM_STATE)
    series = pd.Series(series).astype(float)
    n = len(series)
    std = series.std(ddof=0)
    templates = {}

    burst = series.copy()
    burst_mask = pd.Series(False, index=series.index)
    burst_start = int(n * 0.35)
    burst_length = min(12, n - burst_start)
    burst_idx = series.index[burst_start : burst_start + burst_length]
    shape = np.hanning(burst_length) if burst_length > 2 else np.ones(burst_length)
    burst.loc[burst_idx] = burst.loc[burst_idx] + 3 * std * shape
    burst_mask.loc[burst_idx] = True
    templates["gaussian_burst"] = (burst, burst_mask)

    cutpaste = series.copy()
    cut_mask = pd.Series(False, index=series.index)
    source_start = int(n * 0.15)
    target_start = int(n * 0.70)
    length = min(12, n - source_start, n - target_start)
    source = series.iloc[source_start : source_start + length].to_numpy()
    target_idx = series.index[target_start : target_start + length]
    cutpaste.loc[target_idx] = cutpaste.loc[target_idx] + source - np.median(source)
    cut_mask.loc[target_idx] = True
    templates["cut_add_paste"] = (cutpaste, cut_mask)

    shift = series.copy()
    shift_mask = pd.Series(False, index=series.index)
    shift_start = int(n * 0.55)
    shift_length = min(24, n - shift_start)
    shift_idx = series.index[shift_start : shift_start + shift_length]
    shift.loc[shift_idx] = shift.loc[shift_idx] + 2.5 * std
    shift_mask.loc[shift_idx] = True
    templates["level_shift"] = (shift, shift_mask)

    for name, (injected, mask) in templates.items():
        templates[name] = (injected + rng.normal(0, std * 1e-6, size=n), mask)
    return templates


def run_detectors(frame, injected, specs):
    """Refit and score the exact persisted family for each detector slot."""
    injected_frame = frame.copy()
    injected_frame[TARGET_COL] = injected
    flags = {}
    details = {}
    for detector, spec in specs.items():
        index = injected.index
        detector_flags = pd.Series(False, index=index)
        x = injected_frame.reindex(columns=list(spec.features))
        y = None if spec.family == "isolation_forest" else injected
        fit = fit_detector(spec, y=y, x=x)
        if fit.status == "ok":
            scores = score_detector(fit, in_sample=True).score
            fitted_flags, _, _ = flag_scores(scores)
            detector_flags.loc[fitted_flags.index] = fitted_flags.to_numpy()
        flags[detector] = detector_flags
        details[detector] = {
            "status": fit.status,
            "detail": fit.detail,
            "model_family": spec.family,
            "features": "|".join(spec.features),
            "diagnostics": fit.diagnostics,
        }
    return flags, details


def write_plot(injected, mask, flags, template):
    """Plot injected series and detector hits."""
    fig, axis = plt.subplots(figsize=(12, 4), constrained_layout=True)
    axis.plot(injected.index, injected, linewidth=1, label="Injected residual")
    axis.scatter(
        injected.index[mask],
        injected.loc[mask],
        color="black",
        s=28,
        label="Injected window",
    )
    for detector, detector_flags in flags.items():
        hits = detector_flags & mask
        axis.scatter(injected.index[hits], injected.loc[hits], s=18, label=f"{detector} hit")
    axis.set_title(f"Synthetic injection: {template}")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="upper right")
    fig.savefig(RESULTS_DIR / f"{template}.png", dpi=160)
    plt.close(fig)


def model_selection_table(detection):
    """Rank detectors only when every synthetic fit is valid."""
    if "model_family" not in detection.columns:
        detection = detection.assign(model_family=detection["detector"])
    scored = detection.assign(fit_ok=detection["detector_status"].eq("ok"))
    grouped = scored.groupby(["detector", "model_family"]).agg(
        templates_run=("template", "count"),
        templates_detected=("event_detected", "sum"),
        mean_detection_rate=("detection_rate", "mean"),
        mean_false_flag_rate=("false_flag_rate", "mean"),
        templates_with_ok_fit=("fit_ok", "sum"),
    )
    raw_score = (
        grouped["templates_detected"]
        + grouped["mean_detection_rate"]
        - grouped["mean_false_flag_rate"]
    )
    grouped["eligible_for_selection"] = grouped["templates_with_ok_fit"].eq(
        grouped["templates_run"]
    )
    grouped["selection_score"] = raw_score.where(grouped["eligible_for_selection"])
    grouped["selection_status"] = np.where(
        grouped["eligible_for_selection"], "eligible", "excluded_non_ok_fit"
    )
    grouped = grouped.sort_values(
        ["eligible_for_selection", "selection_score"],
        ascending=[False, False],
    ).reset_index()
    grouped["selection_rank"] = pd.Series(pd.NA, index=grouped.index, dtype="Int64")
    eligible = grouped["eligible_for_selection"]
    grouped.loc[eligible, "selection_rank"] = range(1, int(eligible.sum()) + 1)
    grouped["selection_basis"] = (
        "synthetic-injection surrogate; the persisted full-record family is refit "
        "for each template and all fits must be ok to receive a rank"
    )
    return grouped


def main():
    """Command-line entry point."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    specs = load_pipeline_specs()

    frame = load_signal_frame()
    model_frame, _ = complete_model_frame(
        frame,
        TARGET_COL,
        list(specs["sarimax"].features),
    )
    blocks = contiguous_blocks(model_frame.index, min_hours=MIN_BLOCK_HOURS)
    if not blocks:
        raise RuntimeError("No contiguous block long enough for injection tests")
    block_index = max(blocks, key=lambda item: len(item[1]))[1]
    block = frame.loc[block_index]
    base = block[TARGET_COL].astype(float)

    rows = []
    flag_frames = []
    for template, (injected, mask) in injection_templates(base).items():
        flags, details = run_detectors(block, injected, specs)
        injected_count = int(mask.sum())
        for detector, detector_flags in flags.items():
            hits = int((detector_flags & mask).sum())
            outside = detector_flags & ~mask
            rows.append(
                {
                    "template": template,
                    "detector": detector,
                    "model_family": details[detector]["model_family"],
                    "detector_status": details[detector]["status"],
                    "fit_detail": details[detector]["detail"],
                    "features": details[detector]["features"],
                    "fit_converged": details[detector]["diagnostics"].get("converged"),
                    "fit_iterations": details[detector]["diagnostics"].get("iterations"),
                    "fit_warnings": details[detector]["diagnostics"].get("warning_messages", ""),
                    "injected_hours": injected_count,
                    "detected_injected_hours": hits,
                    "detection_rate": hits / injected_count if injected_count else np.nan,
                    "event_detected": hits > 0,
                    "false_flag_hours": int(outside.sum()),
                    "false_flag_rate": float(outside.sum() / max((~mask).sum(), 1)),
                    "total_flagged_hours": int(detector_flags.sum()),
                }
            )
        flag_frames.append(
            pd.DataFrame(
                {
                    "timestamp_utc": injected.index,
                    "template": template,
                    "injected_value": injected.to_numpy(),
                    "is_injected_window": mask.to_numpy(),
                    **{f"{name}_anomaly": flag.to_numpy() for name, flag in flags.items()},
                }
            )
        )
        write_plot(injected, mask, flags, template)

    detection = pd.DataFrame(rows)
    selection = model_selection_table(detection)
    flags = pd.concat(flag_frames, ignore_index=True)
    detection.to_csv(RESULTS_DIR / "detection_rates.csv", index=False)
    selection.to_csv(RESULTS_DIR / "model_selection.csv", index=False)
    flags.to_csv(RESULTS_DIR / "injection_flags.csv", index=False)
    print(f"wrote {RESULTS_DIR / 'detection_rates.csv'}")
    print(f"wrote {RESULTS_DIR / 'model_selection.csv'}")
    print(f"wrote {RESULTS_DIR / 'injection_flags.csv'}")
    print(f"injection block: {block_index.min()} -> {block_index.max()} ({len(block_index)} h)")
    print(
        selection[["detector", "model_family", "selection_rank", "selection_score"]].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
