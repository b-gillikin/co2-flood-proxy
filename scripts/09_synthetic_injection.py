"""July Week 3 synthetic anomaly injection and detector selection.

Deterministic anomaly templates (Gaussian burst, cut-add-paste, level shift)
are injected into the barometric CO2 residual on the longest contiguous
hourly block, and the three *actual* pipeline detectors are refit on the
injected series. Per-detector recovery metrics then provide the
synthetic-injection surrogate ranking the evaluation protocol uses for
unsupervised model selection (tsadams-style), since no labelled anomalies
exist inside the analysis window.
"""

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
from sklearn.ensemble import IsolationForest

from src.models.july import (
    CO2_COL,
    TARGET_COL,
    available_exog,
    complete_model_frame,
    contiguous_blocks,
    fit_local_level,
    fit_sarimax_fixed,
    fitted_model_status,
    load_signal_frame,
    robust_zscore,
    standardized_innovations,
)

RESULTS_DIR = Path("results/synthetic_injection")
SARIMAX_MODEL_PATH = Path("results/models/sarimax.pkl")

RANDOM_STATE = 42
MIN_BLOCK_HOURS = 168
WARMUP_HOURS = 24
MAD_THRESHOLD = 3.5
DEFAULT_ORDER = (1, 0, 2)
DEFAULT_SEASONAL_ORDER = (1, 0, 1, 24)

IFOREST_FEATURES = [
    TARGET_COL,
    CO2_COL,
    "iot_temperature_c",
    "iot_relative_humidity_pct",
    "iot_air_pressure_hpa",
]


def selected_sarimax_spec():
    """Read the order selected by 05_sarimax.py, with a safe default."""
    if SARIMAX_MODEL_PATH.exists():
        with SARIMAX_MODEL_PATH.open("rb") as handle:
            payload = pickle.load(handle)
        order = payload.get("order")
        seasonal_order = payload.get("seasonal_order")
        if order and seasonal_order:
            return tuple(order), tuple(seasonal_order)
    return DEFAULT_ORDER, DEFAULT_SEASONAL_ORDER


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

    # Tiny jitter breaks detector ties without changing the visible pattern.
    for name, (injected, mask) in templates.items():
        templates[name] = (injected + rng.normal(0, std * 1e-6, size=n), mask)
    return templates


def sarimax_flags(injected, exog, order, seasonal_order):
    """Refit the selected SARIMAX spec on the injected series and flag."""
    result = fit_sarimax_fixed(injected, exog, order, seasonal_order)
    status = fitted_model_status(result)
    if status != "ok":
        return pd.Series(False, index=injected.index), status
    fitted = pd.Series(result.fittedvalues, index=injected.index)
    residual = injected - fitted
    warmup = max(int(result.loglikelihood_burn), WARMUP_HOURS)
    residual.iloc[:warmup] = np.nan
    return robust_zscore(residual).abs() > MAD_THRESHOLD, status


def kalman_flags(injected, exog):
    """Refit the local-level model on the injected series and flag."""
    result = fit_local_level(injected, exog)
    status = fitted_model_status(result)
    if status != "ok":
        return pd.Series(False, index=injected.index), status
    standardized = standardized_innovations(result, injected.index, warmup=3)
    return robust_zscore(standardized).abs() > MAD_THRESHOLD, status


def iforest_flags(frame, injected):
    """Fit the pipeline Isolation Forest on the injected block and flag."""
    out = frame.copy()
    out[TARGET_COL] = injected
    features = [
        column for column in out.columns if column in set(IFOREST_FEATURES) or "_delta_" in column
    ]
    features = list(dict.fromkeys(features))
    model_frame = out[features].replace([np.inf, -np.inf], np.nan).dropna()
    model = IsolationForest(
        n_estimators=200,
        max_features=0.8,
        random_state=RANDOM_STATE,
        n_jobs=1,
    ).fit(model_frame)
    score = pd.Series(-model.score_samples(model_frame), index=model_frame.index)
    flags = pd.Series(False, index=out.index)
    flags.loc[model_frame.index] = (robust_zscore(score).abs() > MAD_THRESHOLD).to_numpy()
    return flags, "ok"


def run_detectors(frame, injected, order, seasonal_order, feature_cols):
    """Run the three pipeline detectors on one injected series."""
    exog = frame[feature_cols]
    flags = {}
    statuses = {}
    for detector, runner in (
        ("sarimax", lambda: sarimax_flags(injected, exog, order, seasonal_order)),
        ("kalman", lambda: kalman_flags(injected, exog)),
        ("iforest", lambda: iforest_flags(frame, injected)),
    ):
        try:
            flags[detector], statuses[detector] = runner()
        except Exception:
            flags[detector] = pd.Series(False, index=injected.index)
            statuses[detector] = "failed"
    return flags, statuses


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
    """Rank detectors by synthetic-injection recovery (tsadams-style)."""
    scored = detection.assign(fit_ok=detection["detector_status"].eq("ok"))
    grouped = scored.groupby("detector").agg(
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
        ["eligible_for_selection", "selection_score"], ascending=[False, False]
    ).reset_index()
    grouped["selection_rank"] = pd.Series(pd.NA, index=grouped.index, dtype="Int64")
    eligible = grouped["eligible_for_selection"]
    grouped.loc[eligible, "selection_rank"] = range(1, int(eligible.sum()) + 1)
    grouped["selection_basis"] = (
        "synthetic-injection surrogate metric; unsupervised model selection "
        "in the absence of labelled anomalies; all template fits must be ok "
        "to receive a rank (provisional)"
    )
    return grouped


def main():
    """Command-line entry point."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_signal_frame()
    feature_cols = available_exog(frame)
    model_frame, feature_cols = complete_model_frame(frame, TARGET_COL, feature_cols)
    blocks = contiguous_blocks(model_frame.index, min_hours=MIN_BLOCK_HOURS)
    if not blocks:
        raise RuntimeError("No contiguous block long enough for injection tests.")
    block_index = max(blocks, key=lambda item: len(item[1]))[1]
    block = frame.loc[block_index]
    base = block[TARGET_COL].astype(float)
    order, seasonal_order = selected_sarimax_spec()

    templates = injection_templates(base)
    rows = []
    flag_frames = []

    for template, (injected, mask) in templates.items():
        flags, statuses = run_detectors(block, injected, order, seasonal_order, feature_cols)
        injected_count = int(mask.sum())
        for detector, detector_flags in flags.items():
            hits = int((detector_flags & mask).sum())
            outside = detector_flags & ~mask
            rows.append(
                {
                    "template": template,
                    "detector": detector,
                    "detector_status": statuses[detector],
                    "injected_hours": injected_count,
                    "detected_injected_hours": hits,
                    "detection_rate": hits / injected_count if injected_count else np.nan,
                    "event_detected": hits > 0,
                    "false_flag_hours": int(outside.sum()),
                    "false_flag_rate": float(outside.sum() / max((~mask).sum(), 1)),
                    "total_flagged_hours": int(detector_flags.sum()),
                }
            )
        flag_frame = pd.DataFrame(
            {
                "timestamp_utc": injected.index,
                "template": template,
                "injected_value": injected.to_numpy(),
                "is_injected_window": mask.to_numpy(),
                **{f"{name}_anomaly": flag.to_numpy() for name, flag in flags.items()},
            }
        )
        flag_frames.append(flag_frame)
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
    print(selection[["detector", "selection_rank", "selection_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
