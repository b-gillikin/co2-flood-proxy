"""Small, exploratory Wurm/CO2 diagnostic using held source-native data.

This is an event-level description, not a flood predictor or CO2 source model.
The weather-only route is summarized from the existing forward-year predictions;
those models were trained on six tributaries, not fitted to Wurm alone.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
IOT = ROOT / "data/interim/viefhues_iot.csv"
EVENTS = ROOT / "results/event_study/real_data_v1/events.csv"
FORECASTS = (
    ROOT
    / "results/event_study/cross_tributary_rain_v1/prediction_6h"
    / "atmospheric_increment/forward_predictions.csv"
)
OUT = ROOT / "results/event_study/wurm_co2_diagnostic_2026-10-03"
SEED = 20261003


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def features(frame: pd.DataFrame) -> pd.DataFrame:
    """Pressure level/tendency and minimal daily/weekly building pattern."""
    local = frame.index.tz_convert("Europe/Amsterdam")
    hour = local.hour.to_numpy()
    pressure = frame.iot_air_pressure_hpa
    return pd.DataFrame(
        {
            "pressure_hpa": pressure,
            "pressure_change_6h_hpa": pressure - pressure.shift(6),
            "pressure_squared": (pressure - 998.0) ** 2,
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "hour_sin2": np.sin(4 * np.pi * hour / 24),
            "hour_cos2": np.cos(4 * np.pi * hour / 24),
            "weekend": (local.dayofweek >= 5).astype(int),
        },
        index=frame.index,
    )


def auc(y: np.ndarray, score: np.ndarray) -> float:
    positive = int(y.sum())
    negative = len(y) - positive
    if not positive or not negative:
        return float("nan")
    return float((rankdata(score)[y == 1].sum() - positive * (positive + 1) / 2) / (positive * negative))


def average_precision(y: np.ndarray, score: np.ndarray) -> float:
    ordered = y[np.argsort(-score)]
    positive_positions = np.flatnonzero(ordered)
    if not len(positive_positions):
        return float("nan")
    precision = np.cumsum(ordered)[positive_positions] / (positive_positions + 1)
    return float(precision.mean())


def observed_median(values: pd.Series) -> float:
    return float(values.median()) if values.notna().any() else float("nan")


def weather_route() -> dict:
    predictions = pd.read_csv(FORECASTS)
    worm = predictions.loc[predictions.site.eq("Worm")].copy()
    by_year = {year: part for year, part in worm.groupby("year")}
    years = np.array(sorted(by_year))
    rng = np.random.default_rng(SEED)

    def gain(sample: pd.DataFrame) -> tuple[float, float, float]:
        y = sample.high_next_24h.to_numpy(dtype=int)
        base = sample.p_rain_plus_flow.to_numpy(dtype=float)
        pressure = sample.p_plus_pressure_change.to_numpy(dtype=float)
        return (
            auc(y, pressure) - auc(y, base),
            average_precision(y, pressure) - average_precision(y, base),
            float(np.mean((y - base) ** 2) - np.mean((y - pressure) ** 2)),
        )

    draws = np.array(
        [gain(pd.concat([by_year[year] for year in rng.choice(years, len(years), replace=True)])) for _ in range(999)]
    )
    point = gain(worm)
    without_2024 = gain(worm.loc[worm.year.ne(2024)])
    return {
        "note": "Wurm subset of models fitted to all six tributaries; retrospective ERA5-Land pressure; year-resampled evaluation intervals do not refit models",
        "n_decisions": len(worm),
        "n_positive": int(worm.high_next_24h.sum()),
        "base_auc": auc(worm.high_next_24h.to_numpy(dtype=int), worm.p_rain_plus_flow.to_numpy()),
        "pressure_auc": auc(worm.high_next_24h.to_numpy(dtype=int), worm.p_plus_pressure_change.to_numpy()),
        "auc_gain": point[0],
        "auc_gain_year_interval": np.quantile(draws[:, 0], [0.025, 0.975]).tolist(),
        "ap_gain": point[1],
        "ap_gain_year_interval": np.quantile(draws[:, 1], [0.025, 0.975]).tolist(),
        "brier_improvement": point[2],
        "brier_improvement_year_interval": np.quantile(draws[:, 2], [0.025, 0.975]).tolist(),
        "without_2024_auc_gain": without_2024[0],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    iot = pd.read_csv(IOT, parse_dates=["timestamp_utc"]).set_index("timestamp_utc").sort_index().asfreq("h")
    events = pd.read_csv(EVENTS, parse_dates=["onset_utc"])
    events = events.loc[
        events.watercourse.eq("Worm")
        & events.onset_utc.between(iot.index.min(), iot.index.max())
    ].sort_values("onset_utc")
    x = features(iot)
    complete = iot.iot_co2_ppm.notna() & x.notna().all(axis=1)
    uncapped = complete & iot.iot_co2_ppm.lt(4990)
    quiet = uncapped.copy()
    for onset in events.onset_utc:
        quiet &= ~((iot.index >= onset - pd.Timedelta(hours=72)) & (iot.index <= onset + pd.Timedelta(hours=72)))
    if quiet.sum() < 100:
        raise ValueError("Insufficient non-event training hours")

    mean, std = x.loc[quiet].mean(), x.loc[quiet].std()
    std = std.where(std.ne(0), 1)

    def design(rows: pd.DataFrame) -> np.ndarray:
        return np.column_stack([np.ones(len(rows)), ((rows - mean) / std).to_numpy()])

    target = np.log(iot.loc[quiet, "iot_co2_ppm"].to_numpy())
    coefficients = np.linalg.lstsq(design(x.loc[quiet]), target, rcond=None)[0]
    predicted = pd.Series(np.nan, index=iot.index)
    predicted.loc[uncapped] = np.exp(design(x.loc[uncapped]) @ coefficients)
    residual = iot.iot_co2_ppm - predicted
    ratio = iot.iot_co2_ppm / predicted
    training_r2 = float(1 - np.sum((target - design(x.loc[quiet]) @ coefficients) ** 2) / np.sum((target - target.mean()) ** 2))

    rows = []
    for event in events.itertuples(index=False):
        for label, start, end in (
            ("prior_48_to_25h", -48, -25),
            ("prior_24_to_1h", -24, -1),
            ("onset_to_23h", 0, 23),
            ("after_24_to_47h", 24, 47),
        ):
            window = slice(event.onset_utc + pd.Timedelta(hours=start), event.onset_utc + pd.Timedelta(hours=end))
            observed = iot.loc[window, "iot_co2_ppm"]
            rows.append(
                {
                    "onset_utc": event.onset_utc,
                    "window": label,
                    "n_observed_co2_hours": int(observed.notna().sum()),
                    "n_adjusted_uncapped_hours": int(residual.loc[window].notna().sum()),
                    "n_capped_hours": int(observed.ge(4990).sum()),
                    "median_co2_ppm": observed_median(observed),
                    "median_pressure_adjusted_excess_ppm": observed_median(residual.loc[window]),
                    "median_observed_to_expected_ratio": observed_median(ratio.loc[window]),
                    "measurement_concern": bool(event.measurement_concern),
                }
            )
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "event_windows.csv", index=False)
    report = {
        "description": "Exploratory event-level diagnostic; association is not source attribution or forecast skill",
        "sensor": "Viefhues source-native K4 basement, May–September 2021",
        "event_definition": "reviewed Worm/Rimburg p99 discharge onsets; no peak magnitude inference",
        "baseline": "quiet-hour least-squares log CO2 on indoor pressure level, squared level, 6h change, two daily harmonics and weekend; event ±72h excluded; 4990+ ppm censored hours excluded",
        "n_events": len(events),
        "n_complete_uncapped_hours": int(uncapped.sum()),
        "n_quiet_fit_hours": int(quiet.sum()),
        "quiet_fit_r2_log_co2": training_r2,
        "weather_route": weather_route(),
        "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in [IOT, EVENTS, FORECASTS]},
        "seed": SEED,
    }
    (OUT / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(table.to_string(index=False))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
