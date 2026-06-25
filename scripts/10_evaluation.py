"""July Week 4 evaluation scaffolding and API baseline.

The current Kerkrade residual window is too short for the chapter's planned
30-day train / 7-day rolling-origin evaluation. This script writes that
insufficiency check explicitly, then runs a shorter smoke-window summary so the
evaluation pipeline can be rerun unchanged when more IoT data arrive.
"""

from __future__ import annotations

import os
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import numpy as np
import pandas as pd

from src.models.july import antecedent_precipitation_index


PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/evaluation")

ANALYSIS_PATH = Path("data/interim/analysis_hourly.csv")
FLAGS_PATH = PROCESSED_DIR / "ensemble_anomaly_flags.csv"
EVENTS_PATH = PROCESSED_DIR / "event_catalogue.csv"
API_PATH = PROCESSED_DIR / "api.csv"

WINDOWS_PATH = RESULTS_DIR / "evaluation_windows.csv"
DETECTOR_SUMMARY_PATH = RESULTS_DIR / "provisional_detector_summary.csv"
EVENT_TESTS_PATH = RESULTS_DIR / "anomaly_rate_tests.csv"
SUMMARY_PATH = RESULTS_DIR / "evaluation_summary.txt"

OFFICIAL_TRAIN_HOURS = 30 * 24
OFFICIAL_EVAL_HOURS = 7 * 24
SMOKE_TRAIN_HOURS = 14 * 24
SMOKE_EVAL_HOURS = 3 * 24

DETECTORS = ("sarimax", "kalman", "iforest")


def read_timestamped(path):
    """Read a CSV with normalized UTC timestamps."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    return frame.sort_values("timestamp_utc")


def evaluation_windows(timestamps, train_hours, eval_hours, label):
    """Create rolling-origin window records for one train/evaluation setup."""
    timestamps = pd.DatetimeIndex(timestamps).sort_values()
    rows = []
    total = len(timestamps)
    step = eval_hours
    for start in range(0, total - train_hours - eval_hours + 1, step):
        train = timestamps[start : start + train_hours]
        evaluation = timestamps[start + train_hours : start + train_hours + eval_hours]
        rows.append(
            {
                "scheme": label,
                "train_hours": train_hours,
                "eval_hours": eval_hours,
                "train_start_utc": train[0],
                "train_end_utc": train[-1],
                "eval_start_utc": evaluation[0],
                "eval_end_utc": evaluation[-1],
            }
        )
    return pd.DataFrame(rows)


def official_and_smoke_windows(flags):
    """Write official readiness and provisional smoke-window definitions."""
    timestamps = pd.DatetimeIndex(flags["timestamp_utc"])
    n_hours = len(timestamps)
    official_needed = OFFICIAL_TRAIN_HOURS + OFFICIAL_EVAL_HOURS
    official_ok = n_hours >= official_needed

    window_frames = []
    if official_ok:
        window_frames.append(
            evaluation_windows(
                timestamps,
                OFFICIAL_TRAIN_HOURS,
                OFFICIAL_EVAL_HOURS,
                "official_30d_train_7d_eval",
            )
        )

    smoke = evaluation_windows(
        timestamps,
        SMOKE_TRAIN_HOURS,
        SMOKE_EVAL_HOURS,
        "provisional_14d_train_3d_eval",
    )
    if not smoke.empty:
        window_frames.append(smoke)

    windows = (
        pd.concat(window_frames, ignore_index=True)
        if window_frames
        else pd.DataFrame(
            columns=[
                "scheme",
                "train_hours",
                "eval_hours",
                "train_start_utc",
                "train_end_utc",
                "eval_start_utc",
                "eval_end_utc",
            ]
        )
    )
    status = {
        "n_hours": n_hours,
        "official_needed_hours": official_needed,
        "official_scheme_status": "ready" if official_ok else "insufficient_current_window",
        "smoke_window_count": len(smoke),
    }
    return windows, status


def detector_summary(flags):
    """Summarize detector anomaly rates over the current overlap."""
    rows = []
    detector_cols = [f"{name}_anomaly" for name in DETECTORS]
    for detector in DETECTORS:
        column = f"{detector}_anomaly"
        rows.append(
            {
                "detector": detector,
                "n_hours": len(flags),
                "anomaly_hours": int(flags[column].sum()),
                "anomaly_rate": float(flags[column].mean()),
            }
        )
    any_detector = flags[detector_cols].sum(axis=1) > 0
    rows.append(
        {
            "detector": "any_detector",
            "n_hours": len(flags),
            "anomaly_hours": int(any_detector.sum()),
            "anomaly_rate": float(any_detector.mean()),
        }
    )
    return pd.DataFrame(rows)


def window_rate(flags, column, start, end):
    """Return anomaly rate and overlap count for a half-open time window."""
    mask = (flags["timestamp_utc"] >= start) & (flags["timestamp_utc"] < end)
    values = flags.loc[mask, column].astype(bool)
    if values.empty:
        return np.nan, 0
    return float(values.mean()), int(len(values))


def sign_flip_pvalue(differences):
    """Two-sided paired sign-flip p-value for event/control rate differences."""
    differences = np.asarray(differences, dtype=float)
    differences = differences[np.isfinite(differences)]
    if len(differences) == 0:
        return np.nan
    observed = abs(float(differences.mean()))
    if len(differences) <= 16:
        means = []
        for signs in product((-1, 1), repeat=len(differences)):
            means.append(abs(float((differences * np.asarray(signs)).mean())))
        return float((np.asarray(means) >= observed - 1e-12).mean())

    rng = np.random.default_rng(42)
    draws = rng.choice((-1, 1), size=(5000, len(differences)))
    means = np.abs((draws * differences).mean(axis=1))
    return float((means >= observed - 1e-12).mean())


def event_window_tests(flags):
    """Compare anomaly rates in 72h antecedent windows against prior controls."""
    events = pd.read_csv(
        EVENTS_PATH,
        parse_dates=["start_timestamp_utc", "end_timestamp_utc", "peak_timestamp_utc"],
    )
    for column in ("start_timestamp_utc", "end_timestamp_utc", "peak_timestamp_utc"):
        events[column] = pd.to_datetime(events[column], utc=True)

    rows = []
    for detector in DETECTORS:
        column = f"{detector}_anomaly"
        diffs = []
        used_events = 0
        for _, event in events.iterrows():
            event_start = event["start_timestamp_utc"]
            event_window_start = event_start - pd.Timedelta(hours=72)
            control_start = event_start - pd.Timedelta(hours=144)
            event_rate, event_n = window_rate(flags, column, event_window_start, event_start)
            control_rate, control_n = window_rate(flags, column, control_start, event_window_start)
            if event_n >= 6 and control_n >= 6:
                used_events += 1
                diffs.append(event_rate - control_rate)

        status = "ok" if used_events >= 2 else "insufficient_overlap"
        rows.append(
            {
                "detector": detector,
                "event_window_hours": 72,
                "control_window_hours": 72,
                "events_with_overlap": used_events,
                "mean_event_minus_control_rate": float(np.mean(diffs)) if diffs else np.nan,
                "sign_flip_pvalue": sign_flip_pvalue(diffs),
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def write_api_baseline():
    """Compute Kerkrade Antecedent Precipitation Index from Visual Crossing rain."""
    analysis = read_timestamped(ANALYSIS_PATH)
    if "kerkrade_weather_precip_mm" not in analysis.columns:
        raise KeyError("analysis_hourly.csv is missing kerkrade_weather_precip_mm")
    analysis = analysis.set_index("timestamp_utc")
    api = antecedent_precipitation_index(
        analysis["kerkrade_weather_precip_mm"],
        days=14,
        decay=0.85,
    )
    out = pd.DataFrame(
        {
            "timestamp_utc": analysis.index,
            "kerkrade_weather_precip_mm": analysis["kerkrade_weather_precip_mm"].to_numpy(),
            "api_d0_85_n14d": api.to_numpy(),
        }
    )
    out.to_csv(API_PATH, index=False)
    return out


def write_summary(window_status, windows, detector_rates, event_tests, api):
    """Write a compact evaluation readout."""
    first_time = api["timestamp_utc"].min()
    last_time = api["timestamp_utc"].max()
    lines = [
        "July Week 4 Evaluation and API Baseline",
        "",
        "Status: provisional pipeline validation; current IoT/residual record is gappy.",
        f"Official 30d train / 7d eval status: {window_status['official_scheme_status']}",
        f"Current detector-overlap hours: {window_status['n_hours']}",
        f"Required official hours: {window_status['official_needed_hours']}",
        f"Smoke windows written: {window_status['smoke_window_count']}",
        "",
        "Detector anomaly rates:",
        detector_rates.to_string(index=False),
        "",
        "Event-window anomaly-rate tests:",
        event_tests.to_string(index=False),
        "",
        f"API baseline rows: {len(api)} ({first_time} to {last_time})",
        "API definition: hourly Visual Crossing precipitation, d=0.85, N=14 days.",
        "",
        f"Window table rows: {len(windows)}",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    flags = read_timestamped(FLAGS_PATH)
    for detector in DETECTORS:
        flags[f"{detector}_anomaly"] = flags[f"{detector}_anomaly"].astype(bool)

    windows, window_status = official_and_smoke_windows(flags)
    detector_rates = detector_summary(flags)
    event_tests = event_window_tests(flags)
    api = write_api_baseline()

    windows.to_csv(WINDOWS_PATH, index=False)
    detector_rates.to_csv(DETECTOR_SUMMARY_PATH, index=False)
    event_tests.to_csv(EVENT_TESTS_PATH, index=False)
    write_summary(window_status, windows, detector_rates, event_tests, api)

    print(f"wrote {API_PATH} ({len(api)} rows)")
    print(f"wrote {WINDOWS_PATH} ({len(windows)} rows)")
    print(f"wrote {DETECTOR_SUMMARY_PATH}")
    print(f"wrote {EVENT_TESTS_PATH}")
    print(f"official scheme: {window_status['official_scheme_status']}")


if __name__ == "__main__":
    main()
