"""Small modelling helpers for the July provisional anomaly scripts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.features import pressure_deltas


SIGNAL_FRAME_PATH = Path("data/processed/signal_characterization_frame.csv")
KNMI_PATH = Path("data/interim/knmi_hourly.csv")

TARGET_COL = "co2_residual_barometric_ppm"
CO2_COL = "iot_co2_ppm"
PRESSURE_COL = "iot_air_pressure_hpa"
PRESSURE_LAGS = (1, 3, 6, 12, 24)
REFERENCE_KNMI_STATION = "06380"

IFOREST_BASE_FEATURES = [
    CO2_COL,
    TARGET_COL,
    "iot_temperature_c",
    "iot_relative_humidity_pct",
    "iot_air_pressure_hpa",
    "iot_pm2_5_ugm3",
    "iot_pm10_ugm3",
    "kerkrade_weather_temp_c",
    "kerkrade_weather_relative_humidity_pct",
    "kerkrade_weather_pressure_hpa",
    "kerkrade_weather_precip_mm",
    "kerkrade_weather_wind_speed_kph",
    "kerkrade_weather_pm2_5_ugm3",
    "kerkrade_weather_pm10_ugm3",
]

EXOG_FEATURES = [
    PRESSURE_COL,
    *[f"delta_pressure_{lag}h" for lag in PRESSURE_LAGS],
    "kerkrade_weather_temp_c",
    "kerkrade_weather_relative_humidity_pct",
    "kerkrade_weather_pressure_hpa",
    "kerkrade_weather_precip_mm",
    "kerkrade_weather_wind_speed_kph",
    "kerkrade_weather_cloud_cover_pct",
    "kerkrade_weather_pm2_5_ugm3",
    "kerkrade_weather_pm10_ugm3",
    "knmi_pressure_hpa",
    "knmi_temperature_c",
    "knmi_relative_humidity_pct",
    "knmi_precip_mm",
]


def load_signal_frame(
    path=SIGNAL_FRAME_PATH,
    knmi_path=KNMI_PATH,
    knmi_station=REFERENCE_KNMI_STATION,
):
    """Load the Week 4 signal frame and add optional KNMI reference met data."""
    frame = pd.read_csv(path, parse_dates=["timestamp_utc"])
    frame = frame.set_index("timestamp_utc").sort_index()

    # A full hourly grid keeps every lagged difference an honest hourly lag;
    # rows added here are NaN-only and drop out of complete-case model frames.
    full_index = pd.date_range(frame.index.min(), frame.index.max(), freq="h")
    frame = frame.reindex(full_index)
    frame.index.name = "timestamp_utc"

    if knmi_path is not None and Path(knmi_path).exists():
        knmi = pd.read_csv(knmi_path, parse_dates=["timestamp_utc"])
        if knmi_station is not None and "knmi_station" in knmi.columns:
            station = (
                knmi["knmi_station"].astype(str).str.split(".").str[0].str.zfill(5)
            )
            selected = knmi.loc[station == str(knmi_station).zfill(5)]
            # Fall back to the full cache only when the reference station has
            # not been backfilled yet, so pressure stays single-elevation.
            if not selected.empty:
                knmi = selected
        numeric = knmi.select_dtypes(include=[np.number]).columns.tolist()
        knmi = knmi.groupby("timestamp_utc", as_index=True)[numeric].mean()
        frame = frame.join(knmi, how="left")

    if PRESSURE_COL in frame.columns:
        frame = pressure_deltas(frame, lags=PRESSURE_LAGS, pressure_col=PRESSURE_COL)

    return frame


def contiguous_blocks(index, min_hours=1):
    """Return (block_id, DatetimeIndex) runs of consecutive hourly timestamps.

    Detector fits must not treat a coverage gap as a one-hour step, so callers
    fit per block and skip fragments shorter than ``min_hours``.
    """
    index = pd.DatetimeIndex(index).sort_values()
    if len(index) == 0:
        return []
    timestamps = pd.Series(index)
    block_ids = (timestamps.diff() > pd.Timedelta(hours=1)).cumsum()
    blocks = []
    for block_id, chunk in timestamps.groupby(block_ids):
        if len(chunk) >= min_hours:
            blocks.append((int(block_id), pd.DatetimeIndex(chunk)))
    return blocks


def available_exog(frame, target_col=TARGET_COL, min_non_missing=50):
    """Return July exogenous features with enough usable rows.

    KNMI backfill is incremental, so a sparse reference-met file can exist long
    before it overlaps the Kerkrade residual window. Filtering by usable rows
    keeps optional KNMI columns from collapsing complete-case model frames.
    """
    features = []
    for column in EXOG_FEATURES:
        if column not in frame.columns:
            continue
        usable = frame[column].notna()
        if target_col in frame.columns:
            usable = usable & frame[target_col].notna()
        if int(usable.sum()) >= min_non_missing:
            features.append(column)
    return features


def complete_model_frame(frame, target_col=TARGET_COL, feature_cols=None):
    """Return a complete-case target/exogenous modelling frame."""
    feature_cols = list(feature_cols or available_exog(frame, target_col=target_col))
    columns = [target_col, *feature_cols]
    return frame[columns].replace([np.inf, -np.inf], np.nan).dropna(), feature_cols


def robust_zscore(values, reference=None):
    """Median/MAD z-score with a standard-deviation fallback.

    When ``reference`` is given, the median/MAD come from the reference
    sample (e.g. a training window) and are applied to ``values``, so
    out-of-sample scoring involves no look-ahead.
    """
    series = pd.Series(values).astype(float)
    ref = series if reference is None else pd.Series(reference).astype(float)
    median = ref.median()
    mad = (ref - median).abs().median()
    if pd.isna(mad) or mad == 0:
        std = ref.std(ddof=0)
        if pd.isna(std) or std == 0:
            return pd.Series(0.0, index=series.index)
        return (series - ref.mean()) / std
    return 0.6745 * (series - median) / mad


def standard_zscore(values):
    """Mean/std z-score with zero-variance protection."""
    series = pd.Series(values).astype(float)
    std = series.std(ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def anomaly_table(index, score, prefix, mad_threshold=3.5, z_threshold=3.0):
    """Build a standard anomaly flag table from a score series."""
    score = pd.Series(np.asarray(score, dtype=float), index=index)
    robust_z = robust_zscore(score)
    z = standard_zscore(score)
    out = pd.DataFrame(
        {
            "timestamp_utc": index,
            f"{prefix}_score": score.to_numpy(),
            f"{prefix}_robust_z": robust_z.to_numpy(),
            f"{prefix}_z": z.to_numpy(),
            f"{prefix}_anomaly_mad": robust_z.abs().to_numpy() > mad_threshold,
            f"{prefix}_anomaly_3sigma": z.abs().to_numpy() > z_threshold,
        }
    )
    out[f"{prefix}_anomaly"] = out[f"{prefix}_anomaly_mad"]
    return out


def fit_sarimax_fixed(y, x, order, seasonal_order, maxiter=80):
    """Fit one SARIMAX with a fixed specification on a contiguous block."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    model = SARIMAX(
        pd.Series(y).astype(float),
        exog=pd.DataFrame(x).astype(float),
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    return model.fit(disp=False, maxiter=maxiter)


def fit_local_level(y, x, maxiter=300):
    """Fit a local-level UnobservedComponents model on a contiguous block."""
    from statsmodels.tsa.statespace.structural import UnobservedComponents

    model = UnobservedComponents(
        pd.Series(y).astype(float),
        level="local level",
        exog=pd.DataFrame(x).astype(float),
    )
    return model.fit(disp=False, maxiter=maxiter)


def standardized_innovations(result, index, warmup=0):
    """Per-timestep standardized one-step forecast errors from a fit result."""
    series = pd.Series(
        np.asarray(result.filter_results.standardized_forecasts_error[0]),
        index=index,
    )
    warmup = max(int(warmup), int(result.loglikelihood_burn))
    if warmup > 0:
        series.iloc[:warmup] = np.nan
    return series


def autocorrelation(values, max_lag=48):
    """Simple autocorrelation values for plotting without statsmodels."""
    series = pd.Series(values).dropna().astype(float)
    centered = series - series.mean()
    denom = float((centered**2).sum())
    rows = []
    for lag in range(max_lag + 1):
        if lag == 0:
            corr = 1.0
        elif denom == 0 or lag >= len(centered):
            corr = np.nan
        else:
            left = centered.iloc[:-lag].to_numpy()
            right = centered.iloc[lag:].to_numpy()
            corr = float((left * right).sum() / denom)
        rows.append({"lag": lag, "acf": corr})
    return pd.DataFrame(rows)


def antecedent_precipitation_index(precip, days=14, decay=0.85, hours_per_day=24):
    """Compute hourly antecedent rain with day-scaled exponential decay.

    The July plan specifies d=0.85 and N=14 days. Each lagged hour receives
    the weight for its lagged day: 0.85 for the previous 24 hours, 0.85**2 for
    the next 24 hours back, and so on through day 14.
    """
    precip = pd.Series(precip).fillna(0).astype(float)
    api = pd.Series(0.0, index=precip.index)
    for lag_hour in range(1, days * hours_per_day + 1):
        lag_day = int(np.ceil(lag_hour / hours_per_day))
        api = api + (decay**lag_day) * precip.shift(lag_hour).fillna(0)
    return api
