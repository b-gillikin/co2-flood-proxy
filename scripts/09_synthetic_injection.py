"""July Week 3 synthetic anomaly injection smoke tests."""

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
from sklearn.ensemble import IsolationForest

from src.models.july import TARGET_COL, load_signal_frame, robust_zscore


RESULTS_DIR = Path("results/synthetic_injection")
RANDOM_STATE = 42


def injection_templates(series):
    """Create deterministic Gaussian-burst and CutAddPaste injections."""
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

    # Tiny jitter breaks detector ties without changing the visible pattern.
    for name, (injected, mask) in templates.items():
        templates[name] = (injected + rng.normal(0, std * 1e-6, size=n), mask)
    return templates


def kalman_like_flags(series):
    """Simple local-level innovations for injected-series detection."""
    series = pd.Series(series).astype(float)
    state = float(series.iloc[0])
    innovations = []
    for value in series:
        innovation = value - state
        innovations.append(innovation)
        state = state + 0.2 * innovation
    innovations = pd.Series(innovations, index=series.index)
    return robust_zscore(innovations).abs() > 3.5


def iforest_flags(frame, injected):
    """Fit a provisional Isolation Forest on the injected multivariate frame."""
    out = frame.copy()
    out[TARGET_COL] = injected
    features = [
        column
        for column in out.columns
        if column
        in {
            TARGET_COL,
            "iot_co2_ppm",
            "iot_temperature_c",
            "iot_relative_humidity_pct",
            "iot_air_pressure_hpa",
        }
        or "_delta_" in column
    ]
    features = list(dict.fromkeys(features))
    model_frame = out[features].replace([np.inf, -np.inf], np.nan).dropna()
    model = IsolationForest(
        n_estimators=200,
        max_features=0.8,
        contamination=0.05,
        random_state=RANDOM_STATE,
        n_jobs=1,
    ).fit(model_frame)
    flags = pd.Series(False, index=out.index)
    flags.loc[model_frame.index] = model.predict(model_frame) == -1
    return flags


def run_detectors(frame, injected):
    """Run the three provisional detector families on an injected series."""
    return {
        "sarimax": robust_zscore(injected).abs() > 3.5,
        "kalman": kalman_like_flags(injected),
        "iforest": iforest_flags(frame, injected),
    }


def write_plot(series, injected, mask, flags, template):
    """Plot injected series and detector hits."""
    fig, axis = plt.subplots(figsize=(12, 4), constrained_layout=True)
    axis.plot(series.index, injected, linewidth=1, label="Injected residual")
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


def main():
    """Command-line entry point."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_signal_frame()
    base = frame[TARGET_COL].dropna()
    frame = frame.loc[base.index]
    templates = injection_templates(base)
    rows = []
    flag_frames = []

    for template, (injected, mask) in templates.items():
        flags = run_detectors(frame, injected)
        for detector, detector_flags in flags.items():
            injected_count = int(mask.sum())
            rows.append(
                {
                    "template": template,
                    "detector": detector,
                    "injected_hours": injected_count,
                    "detected_injected_hours": int((detector_flags & mask).sum()),
                    "detection_rate": float((detector_flags & mask).sum() / injected_count),
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
        write_plot(base, injected, mask, flags, template)

    detection = pd.DataFrame(rows)
    flags = pd.concat(flag_frames, ignore_index=True)
    detection.to_csv(RESULTS_DIR / "detection_rates.csv", index=False)
    flags.to_csv(RESULTS_DIR / "injection_flags.csv", index=False)
    print(f"wrote {RESULTS_DIR / 'detection_rates.csv'}")
    print(f"wrote {RESULTS_DIR / 'injection_flags.csv'}")


if __name__ == "__main__":
    main()
