"""July Week 4 evaluation: time-aware windows, rolling-origin scoring, API baseline.

Evaluation windows are defined in calendar time with explicit coverage
requirements, so a "30-day" training window can never silently span a
multi-month outage. Detectors are then genuinely refit per rolling-origin
window and scored out-of-sample with thresholds taken from their own training
window, which is the time-aware protocol the chapter commits to. Event-window
anomaly-rate tests run on deduplicated physical episodes, because the event
catalogue intentionally repeats one episode across gauges and quantiles.
"""

from __future__ import annotations

import argparse
import os
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.eval import deduplicate_event_episodes
from src.models.july import (
    IFOREST_BASE_FEATURES,
    TARGET_COL,
    antecedent_precipitation_index,
    available_exog,
    complete_model_frame,
    fit_local_level,
    fit_sarimax_fixed,
    load_signal_frame,
    robust_zscore,
    standardized_innovations,
)


PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/evaluation")

ANALYSIS_PATH = Path("data/interim/analysis_hourly.csv")
FLAGS_PATH = PROCESSED_DIR / "ensemble_anomaly_flags.csv"
EVENTS_PATH = PROCESSED_DIR / "event_catalogue.csv"
API_PATH = PROCESSED_DIR / "api.csv"
SARIMAX_MODEL_PATH = Path("results/models/sarimax.pkl")

WINDOWS_PATH = RESULTS_DIR / "evaluation_windows.csv"
DETECTOR_SUMMARY_PATH = RESULTS_DIR / "provisional_detector_summary.csv"
EVENT_TESTS_PATH = RESULTS_DIR / "anomaly_rate_tests.csv"
EPISODES_PATH = RESULTS_DIR / "event_episodes.csv"
ROLLING_FLAGS_PATH = RESULTS_DIR / "rolling_origin_flags.csv"
ROLLING_SUMMARY_PATH = RESULTS_DIR / "rolling_origin_summary.csv"
SUMMARY_PATH = RESULTS_DIR / "evaluation_summary.txt"

OFFICIAL_TRAIN_HOURS = 30 * 24
OFFICIAL_EVAL_HOURS = 7 * 24
SMOKE_TRAIN_HOURS = 14 * 24
SMOKE_EVAL_HOURS = 3 * 24
MIN_WINDOW_COVERAGE = 0.7
MAD_THRESHOLD = 3.5
EXOG_INTERPOLATION_LIMIT_HOURS = 6

DETECTORS = ("sarimax", "kalman", "iforest")
DEFAULT_ORDER = (1, 0, 2)
DEFAULT_SEASONAL_ORDER = (1, 0, 1, 24)


def read_timestamped(path):
    """Read a CSV with normalized UTC timestamps."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    return frame.sort_values("timestamp_utc")


def selected_sarimax_spec():
    """Read the order selected by 05_sarimax.py, with a safe default."""
    if SARIMAX_MODEL_PATH.exists():
        import pickle

        with SARIMAX_MODEL_PATH.open("rb") as handle:
            payload = pickle.load(handle)
        order = payload.get("order")
        seasonal_order = payload.get("seasonal_order")
        if order and seasonal_order:
            return tuple(order), tuple(seasonal_order)
    return DEFAULT_ORDER, DEFAULT_SEASONAL_ORDER


def time_based_windows(timestamps, train_hours, eval_hours, label, min_coverage):
    """Build calendar-time rolling-origin windows with coverage checks.

    Coverage is the share of expected hourly stamps actually observed inside
    each span; windows below ``min_coverage`` in either span are recorded but
    marked unusable, so an outage can never masquerade as training data.
    """
    timestamps = pd.DatetimeIndex(timestamps).sort_values()
    observed = pd.Series(True, index=timestamps)
    rows = []
    if timestamps.empty:
        return pd.DataFrame(rows)

    step = pd.Timedelta(hours=eval_hours)
    train_span = pd.Timedelta(hours=train_hours)
    eval_span = pd.Timedelta(hours=eval_hours)
    start = timestamps.min()
    last_start = timestamps.max() - train_span - eval_span + pd.Timedelta(hours=1)

    window_id = 0
    while start <= last_start:
        train_end = start + train_span
        eval_end = train_end + eval_span
        train_observed = int(observed.loc[start : train_end - pd.Timedelta(hours=1)].sum())
        eval_observed = int(
            observed.loc[train_end : eval_end - pd.Timedelta(hours=1)].sum()
        )
        train_coverage = train_observed / train_hours
        eval_coverage = eval_observed / eval_hours
        usable = train_coverage >= min_coverage and eval_coverage >= min_coverage
        rows.append(
            {
                "scheme": label,
                "window_id": f"{label}_{window_id:03d}",
                "train_hours": train_hours,
                "eval_hours": eval_hours,
                "train_start_utc": start,
                "train_end_utc": train_end - pd.Timedelta(hours=1),
                "eval_start_utc": train_end,
                "eval_end_utc": eval_end - pd.Timedelta(hours=1),
                "train_observed_hours": train_observed,
                "eval_observed_hours": eval_observed,
                "train_coverage": train_coverage,
                "eval_coverage": eval_coverage,
                "status": "ok" if usable else "insufficient_coverage",
            }
        )
        window_id += 1
        start = start + step
    return pd.DataFrame(rows)


def hourly_window_frame(frame, feature_cols, start, end):
    """Reindex one window span to a full hourly grid with finite exog.

    The endogenous target keeps NaN for unobserved hours (the Kalman filter
    treats them as missing). Exogenous gaps are interpolated up to
    ``EXOG_INTERPOLATION_LIMIT_HOURS``; hours needing more imputation keep a
    finite exog placeholder but have the target masked, so they never
    contribute information to the fit or the score.
    """
    grid = pd.date_range(start, end, freq="h")
    y = frame[TARGET_COL].reindex(grid)
    x = frame[feature_cols].reindex(grid)
    x = x.interpolate(limit=EXOG_INTERPOLATION_LIMIT_HOURS, limit_direction="both")
    still_missing = x.isna().any(axis=1)
    y = y.mask(still_missing)
    x = x.ffill().bfill().fillna(0.0)
    return y, x


def rolling_origin_evaluation(frame, feature_cols, windows, order, seasonal_order):
    """Refit each detector per usable window and score its eval span OOS."""
    usable = windows.loc[windows["status"] == "ok"]
    flag_parts = []
    summary_rows = []

    iforest_features = [
        column
        for column in [
            *IFOREST_BASE_FEATURES,
            *[c for c in frame.columns if "_delta_" in c],
        ]
        if column in frame.columns
    ]
    iforest_features = list(dict.fromkeys(iforest_features))

    for window in usable.itertuples(index=False):
        y_train, x_train = hourly_window_frame(
            frame, feature_cols, window.train_start_utc, window.train_end_utc
        )
        y_eval, x_eval = hourly_window_frame(
            frame, feature_cols, window.eval_start_utc, window.eval_end_utc
        )
        eval_flags = pd.DataFrame({"timestamp_utc": y_eval.index})
        eval_flags["window_id"] = window.window_id
        eval_flags["scheme"] = window.scheme
        eval_flags["target_observed"] = y_eval.notna().to_numpy()

        for detector in DETECTORS:
            status = "ok"
            flags = pd.Series(False, index=y_eval.index)
            try:
                if detector == "sarimax":
                    result = fit_sarimax_fixed(y_train, x_train, order, seasonal_order)
                    residual_train = y_train - pd.Series(
                        result.fittedvalues, index=y_train.index
                    )
                    extended = result.extend(y_eval, exog=x_eval)
                    residual_eval = y_eval - pd.Series(
                        extended.fittedvalues, index=y_eval.index
                    )
                    z = robust_zscore(residual_eval, reference=residual_train.dropna())
                    flags = z.abs() > MAD_THRESHOLD
                elif detector == "kalman":
                    result = fit_local_level(y_train, x_train)
                    innovations_train = standardized_innovations(
                        result, y_train.index, warmup=3
                    )
                    extended = result.extend(y_eval, exog=x_eval)
                    innovations_eval = pd.Series(
                        np.asarray(
                            extended.filter_results.standardized_forecasts_error[0]
                        ),
                        index=y_eval.index,
                    )
                    z = robust_zscore(
                        innovations_eval, reference=innovations_train.dropna()
                    )
                    flags = z.abs() > MAD_THRESHOLD
                else:
                    train_rows = (
                        frame.loc[window.train_start_utc : window.train_end_utc,
                                  iforest_features]
                        .replace([np.inf, -np.inf], np.nan)
                        .dropna()
                    )
                    eval_rows = (
                        frame.loc[window.eval_start_utc : window.eval_end_utc,
                                  iforest_features]
                        .replace([np.inf, -np.inf], np.nan)
                        .dropna()
                    )
                    if len(train_rows) < 48 or eval_rows.empty:
                        raise ValueError("insufficient complete-case rows")
                    model = IsolationForest(
                        n_estimators=200,
                        max_features=0.8,
                        random_state=42,
                        n_jobs=1,
                    ).fit(train_rows)
                    score_train = pd.Series(
                        -model.score_samples(train_rows), index=train_rows.index
                    )
                    score_eval = pd.Series(
                        -model.score_samples(eval_rows), index=eval_rows.index
                    )
                    z = robust_zscore(score_eval, reference=score_train)
                    flags = pd.Series(False, index=y_eval.index)
                    flags.loc[score_eval.index] = (z.abs() > MAD_THRESHOLD).to_numpy()
            except Exception as exc:
                status = f"failed: {type(exc).__name__}"

            flags = flags & y_eval.notna() if detector != "iforest" else flags
            eval_flags[f"{detector}_anomaly"] = flags.fillna(False).to_numpy()
            summary_rows.append(
                {
                    "window_id": window.window_id,
                    "scheme": window.scheme,
                    "detector": detector,
                    "eval_start_utc": window.eval_start_utc,
                    "eval_end_utc": window.eval_end_utc,
                    "eval_observed_hours": int(y_eval.notna().sum()),
                    "anomaly_hours": int(eval_flags[f"{detector}_anomaly"].sum()),
                    "status": status,
                }
            )
        flag_parts.append(eval_flags)

    if not flag_parts:
        return pd.DataFrame(), pd.DataFrame(summary_rows)
    return pd.concat(flag_parts, ignore_index=True), pd.DataFrame(summary_rows)


def detector_summary(flags, basis):
    """Summarize detector anomaly rates over one flag record."""
    rows = []
    detector_cols = [f"{name}_anomaly" for name in DETECTORS]
    for detector in DETECTORS:
        column = f"{detector}_anomaly"
        rows.append(
            {
                "flag_basis": basis,
                "detector": detector,
                "n_hours": len(flags),
                "anomaly_hours": int(flags[column].sum()),
                "anomaly_rate": float(flags[column].mean()) if len(flags) else np.nan,
            }
        )
    if len(flags):
        any_detector = flags[detector_cols].sum(axis=1) > 0
        rows.append(
            {
                "flag_basis": basis,
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


def event_window_tests(flags, episodes, basis):
    """Compare anomaly rates in 72h antecedent windows against prior controls.

    Tests run per physical episode, not per catalogue row: the raw catalogue
    lists one row per gauge and quantile, and treating those as independent
    pairs would overstate significance through pseudo-replication.
    """
    rows = []
    for detector in DETECTORS:
        column = f"{detector}_anomaly"
        diffs = []
        used_events = 0
        for episode in episodes.itertuples(index=False):
            event_start = episode.start_timestamp_utc
            event_window_start = event_start - pd.Timedelta(hours=72)
            control_start = event_start - pd.Timedelta(hours=144)
            event_rate, event_n = window_rate(flags, column, event_window_start, event_start)
            control_rate, control_n = window_rate(
                flags, column, control_start, event_window_start
            )
            if event_n >= 6 and control_n >= 6:
                used_events += 1
                diffs.append(event_rate - control_rate)

        status = "ok" if used_events >= 2 else "insufficient_overlap"
        rows.append(
            {
                "flag_basis": basis,
                "detector": detector,
                "event_window_hours": 72,
                "control_window_hours": 72,
                "episodes_total": len(episodes),
                "episodes_with_overlap": used_events,
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


def write_summary(
    windows,
    rolling_summary,
    detector_rates,
    event_tests,
    episodes,
    api,
):
    """Write a compact evaluation readout."""
    official = windows.loc[windows["scheme"].str.startswith("official")]
    smoke = windows.loc[windows["scheme"].str.startswith("provisional")]
    official_ok = int((official["status"] == "ok").sum()) if not official.empty else 0
    smoke_ok = int((smoke["status"] == "ok").sum()) if not smoke.empty else 0
    lines = [
        "July Week 4 Evaluation and API Baseline",
        "",
        "Status: provisional; the IoT record is blocky and the capture outage",
        "since 2026-04-13 truncates the record.",
        "",
        "Windows are defined in calendar time with a minimum coverage of "
        f"{MIN_WINDOW_COVERAGE:.0%} in both train and eval spans.",
        f"Official 30d/7d windows: {len(official)} defined, {official_ok} usable",
        f"Smoke 14d/3d windows: {len(smoke)} defined, {smoke_ok} usable",
        "",
        "Rolling-origin out-of-sample evaluation (official windows):",
        (
            rolling_summary.groupby("detector")["anomaly_hours"].sum().to_string()
            if not rolling_summary.empty
            else "  not run (no usable windows or --skip-rolling)"
        ),
        "",
        "Detector anomaly rates:",
        detector_rates.to_string(index=False),
        "",
        f"Event episodes after deduplication: {len(episodes)} "
        "(raw catalogue rows collapse across gauges/quantiles)",
        "",
        "Event-window anomaly-rate tests (per episode):",
        event_tests.to_string(index=False),
        "",
        f"API baseline rows: {len(api)} ({api['timestamp_utc'].min()} to {api['timestamp_utc'].max()})",
        "API definition: hourly Visual Crossing precipitation, d=0.85, N=14 days.",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-rolling",
        action="store_true",
        help="Skip the rolling-origin refit evaluation (fast pipeline check).",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=MIN_WINDOW_COVERAGE,
        help="Minimum observed-hour share required in train and eval spans.",
    )
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    flags = read_timestamped(FLAGS_PATH)
    for detector in DETECTORS:
        flags[f"{detector}_anomaly"] = flags[f"{detector}_anomaly"].astype(bool)

    timestamps = pd.DatetimeIndex(flags["timestamp_utc"])
    windows = pd.concat(
        [
            time_based_windows(
                timestamps,
                OFFICIAL_TRAIN_HOURS,
                OFFICIAL_EVAL_HOURS,
                "official_30d_train_7d_eval",
                args.min_coverage,
            ),
            time_based_windows(
                timestamps,
                SMOKE_TRAIN_HOURS,
                SMOKE_EVAL_HOURS,
                "provisional_14d_train_3d_eval",
                args.min_coverage,
            ),
        ],
        ignore_index=True,
    )

    events = pd.read_csv(
        EVENTS_PATH,
        parse_dates=["start_timestamp_utc", "end_timestamp_utc", "peak_timestamp_utc"],
    )
    for column in ("start_timestamp_utc", "end_timestamp_utc"):
        events[column] = pd.to_datetime(events[column], utc=True)
    episodes = deduplicate_event_episodes(events)

    detector_rates = detector_summary(flags, basis="in_sample_full_record")
    event_tests = [event_window_tests(flags, episodes, basis="in_sample_full_record")]

    rolling_flags = pd.DataFrame()
    rolling_summary = pd.DataFrame()
    if not args.skip_rolling:
        frame = load_signal_frame()
        feature_cols = available_exog(frame)
        model_frame, feature_cols = complete_model_frame(frame, TARGET_COL, feature_cols)
        order, seasonal_order = selected_sarimax_spec()
        official_windows = windows.loc[
            windows["scheme"] == "official_30d_train_7d_eval"
        ]
        rolling_flags, rolling_summary = rolling_origin_evaluation(
            frame.loc[model_frame.index.min() : model_frame.index.max()],
            feature_cols,
            official_windows,
            order,
            seasonal_order,
        )
        if not rolling_flags.empty:
            rolling_flags.to_csv(ROLLING_FLAGS_PATH, index=False)
            observed = rolling_flags.loc[rolling_flags["target_observed"]]
            detector_rates = pd.concat(
                [detector_rates, detector_summary(observed, basis="rolling_origin_oos")],
                ignore_index=True,
            )
            event_tests.append(
                event_window_tests(observed, episodes, basis="rolling_origin_oos")
            )
        if not rolling_summary.empty:
            rolling_summary.to_csv(ROLLING_SUMMARY_PATH, index=False)

    event_tests = pd.concat(event_tests, ignore_index=True)
    api = write_api_baseline()

    windows.to_csv(WINDOWS_PATH, index=False)
    detector_rates.to_csv(DETECTOR_SUMMARY_PATH, index=False)
    event_tests.to_csv(EVENT_TESTS_PATH, index=False)
    episodes.to_csv(EPISODES_PATH, index=False)
    write_summary(windows, rolling_summary, detector_rates, event_tests, episodes, api)

    usable_official = int(
        (
            (windows["scheme"] == "official_30d_train_7d_eval")
            & (windows["status"] == "ok")
        ).sum()
    )
    print(f"wrote {API_PATH} ({len(api)} rows)")
    print(f"wrote {WINDOWS_PATH} ({len(windows)} rows)")
    print(f"wrote {EPISODES_PATH} ({len(episodes)} episodes)")
    print(f"wrote {DETECTOR_SUMMARY_PATH}")
    print(f"wrote {EVENT_TESTS_PATH}")
    if not rolling_flags.empty:
        print(f"wrote {ROLLING_FLAGS_PATH} ({len(rolling_flags)} rows)")
        print(f"wrote {ROLLING_SUMMARY_PATH} ({len(rolling_summary)} rows)")
    print(f"usable official 30d/7d windows: {usable_official}")


if __name__ == "__main__":
    main()
