"""Signal-frame assembly and shared modelling helpers.

Loads the hourly analysis frame with its KNMI reference meteorology, defines
the contiguous-block rules that keep coverage gaps from being modelled as
one-hour steps, and provides the small fitting and scoring helpers shared by
the analysis scripts.
"""

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
    """Load the signal frame and join KNMI reference meteorology."""
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
            station = knmi["knmi_station"].astype(str).str.split(".").str[0].str.zfill(5)
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


def _coverage_blocks(index, min_block_hours):
    """Return material contiguous blocks, or one generic-index block."""
    index = pd.Index(index)
    if not isinstance(index, pd.DatetimeIndex):
        return [index] if len(index) >= min_block_hours else []
    return [block for _, block in contiguous_blocks(index, min_hours=min_block_hours)]


def select_features_by_joint_coverage(
    frame,
    target_col=TARGET_COL,
    required=(),
    optional=(),
    min_non_missing=50,
    min_joint_share=0.90,
    min_block_share=0.90,
    min_block_hours=24,
):
    """Select optional features without erasing required-data coverage blocks.

    Optional features are considered in priority order. A feature is retained
    only if the complete-case frame accumulated so far preserves both the
    overall required-data share and every material contiguous block.
    """
    if target_col not in frame.columns:
        raise KeyError(f"Missing target column: {target_col}")
    data = frame.replace([np.inf, -np.inf], np.nan)
    required = list(dict.fromkeys(required))
    optional = [column for column in dict.fromkeys(optional) if column not in required]
    missing_required = [column for column in required if column not in data.columns]
    if missing_required:
        raise KeyError("Missing required features: " + ", ".join(missing_required))

    required_mask = data[target_col].notna()
    for column in required:
        required_mask &= data[column].notna()
    required_index = data.index[required_mask]
    required_rows = int(required_mask.sum())
    if required_rows < min_non_missing:
        raise ValueError(
            f"Required target/features have {required_rows} rows; need {min_non_missing}"
        )
    blocks = _coverage_blocks(required_index, min_block_hours)
    if not blocks:
        blocks = [required_index]

    selected = required.copy()
    current_mask = required_mask.copy()
    audit_rows = []
    for column in required:
        audit_rows.append(
            {
                "feature": column,
                "role": "required",
                "status": "selected",
                "reason": "required_feature",
                "target_overlap_rows": int((data[target_col].notna() & data[column].notna()).sum()),
                "joint_rows_after": required_rows,
                "joint_share_of_required": 1.0,
                "minimum_material_block_share": 1.0,
                "latest_joint_timestamp_utc": (
                    required_index.max() if len(required_index) else pd.NaT
                ),
            }
        )

    for column in optional:
        if column not in data.columns:
            audit_rows.append(
                {
                    "feature": column,
                    "role": "optional",
                    "status": "rejected",
                    "reason": "missing_column",
                    "target_overlap_rows": 0,
                    "joint_rows_after": int(current_mask.sum()),
                    "joint_share_of_required": float(current_mask.sum() / required_rows),
                    "minimum_material_block_share": 0.0,
                    "latest_joint_timestamp_utc": pd.NaT,
                }
            )
            continue

        target_overlap = data[target_col].notna() & data[column].notna()
        proposed_mask = current_mask & data[column].notna()
        joint_rows = int(proposed_mask.sum())
        joint_share = joint_rows / required_rows
        block_shares = [
            float(proposed_mask.reindex(block, fill_value=False).mean()) for block in blocks
        ]
        minimum_block_share = min(block_shares) if block_shares else 0.0
        if int(target_overlap.sum()) < min_non_missing:
            status = "rejected"
            reason = "insufficient_target_overlap"
        elif joint_share < min_joint_share:
            status = "rejected"
            reason = "joint_coverage_below_threshold"
        elif minimum_block_share < min_block_share:
            status = "rejected"
            reason = "material_block_coverage_below_threshold"
        else:
            status = "selected"
            reason = "coverage_gate_passed"
            selected.append(column)
            current_mask = proposed_mask
        joint_index = data.index[proposed_mask]
        audit_rows.append(
            {
                "feature": column,
                "role": "optional",
                "status": status,
                "reason": reason,
                "target_overlap_rows": int(target_overlap.sum()),
                "joint_rows_after": joint_rows,
                "joint_share_of_required": joint_share,
                "minimum_material_block_share": minimum_block_share,
                "latest_joint_timestamp_utc": (joint_index.max() if len(joint_index) else pd.NaT),
            }
        )
    return selected, pd.DataFrame(audit_rows)


def available_exog(
    frame,
    target_col=TARGET_COL,
    min_non_missing=50,
    return_audit=False,
):
    """Return optional exogenous features that preserve joint block coverage."""
    target_rows = int(frame[target_col].notna().sum()) if target_col in frame else 0
    if target_rows < min_non_missing:
        audit = pd.DataFrame(
            [
                {
                    "feature": column,
                    "role": "optional",
                    "status": "rejected",
                    "reason": "insufficient_target_coverage",
                    "target_overlap_rows": (
                        int((frame[target_col].notna() & frame[column].notna()).sum())
                        if target_col in frame and column in frame
                        else 0
                    ),
                    "joint_rows_after": target_rows,
                    "joint_share_of_required": np.nan,
                    "minimum_material_block_share": np.nan,
                    "latest_joint_timestamp_utc": pd.NaT,
                }
                for column in EXOG_FEATURES
            ]
        )
        return ([], audit) if return_audit else []
    features, audit = select_features_by_joint_coverage(
        frame,
        target_col=target_col,
        optional=EXOG_FEATURES,
        min_non_missing=min_non_missing,
    )
    return (features, audit) if return_audit else features


def complete_model_frame(frame, target_col=TARGET_COL, feature_cols=None):
    """Return a complete-case target/exogenous modelling frame."""
    if feature_cols is None:
        feature_cols = available_exog(frame, target_col=target_col)
    feature_cols = list(feature_cols)
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


def fitted_model_status(result):
    """Return a stable status for a fitted statsmodels result.

    Statsmodels commonly reports optimizer non-convergence as a warning rather
    than an exception. Chapter outputs must preserve that distinction instead
    of labelling every returned result ``ok``.
    """
    mle_retvals = getattr(result, "mle_retvals", None)
    if isinstance(mle_retvals, dict) and mle_retvals.get("converged") is False:
        return "non_converged"
    return "ok"


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
    scored = score.notna() & robust_z.notna()
    out = pd.DataFrame(
        {
            "timestamp_utc": index,
            f"{prefix}_score": score.to_numpy(),
            f"{prefix}_robust_z": robust_z.to_numpy(),
            f"{prefix}_z": z.to_numpy(),
            f"{prefix}_scored": scored.to_numpy(),
            f"{prefix}_anomaly_mad": (robust_z.abs() > mad_threshold).to_numpy()
            & scored.to_numpy(),
            f"{prefix}_anomaly_3sigma": (z.abs() > z_threshold).to_numpy() & scored.to_numpy(),
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
