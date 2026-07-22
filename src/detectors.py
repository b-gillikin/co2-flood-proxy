"""Shared detector specifications, fitting, and scoring.

The full-record, synthetic-injection, and rolling-origin workflows must use
the same model family and feature contract. This module is the single path for
fitting and scoring those detector families.
"""

from __future__ import annotations

import pickle
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.models.july import IFOREST_BASE_FEATURES, fitted_model_status

DETECTOR_SCHEMA_VERSION = 2
MAD_THRESHOLD = 3.5
RANDOM_STATE = 42
RIDGE_ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)
Q_SCALES = (0.001, 0.01, 0.05, 0.1, 0.5)
R_SCALES = (0.25, 0.5, 1.0, 2.0)

STATE_SPACE_FEATURES = (
    "iot_temperature_c",
    "iot_relative_humidity_pct",
)
PRESSURE_TOKEN = "pressure"


@dataclass(frozen=True)
class DetectorSpec:
    """Serializable identity of one fitted detector family."""

    detector: str
    family: str
    features: tuple[str, ...]
    order: tuple[int, int, int] | None = None
    seasonal_order: tuple[int, int, int, int] | None = None
    warmup_hours: int = 0
    maxiter: int = 300

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> DetectorSpec:
        values = dict(payload)
        values["features"] = tuple(values.get("features", ()))
        if values.get("order") is not None:
            values["order"] = tuple(values["order"])
        if values.get("seasonal_order") is not None:
            values["seasonal_order"] = tuple(values["seasonal_order"])
        return cls(**values)


@dataclass
class FittedDetector:
    """A detector fit plus the state needed for honest future scoring."""

    spec: DetectorSpec
    status: str
    detail: str = ""
    model: object | None = None
    scaler: object | None = None
    train_score: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    train_prediction: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    diagnostics: dict = field(default_factory=dict)
    tuning: pd.DataFrame = field(default_factory=pd.DataFrame)
    history: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    q: float | None = None
    r: float | None = None
    final_state: float | None = None
    final_variance: float | None = None


@dataclass
class DetectorScore:
    """Scores and predictions aligned to the requested timestamps."""

    score: pd.Series
    prediction: pd.Series


def state_space_features(frame: pd.DataFrame) -> list[str]:
    """Return the locked non-pressure controls available in a frame."""
    missing = [column for column in STATE_SPACE_FEATURES if column not in frame.columns]
    if missing:
        raise ValueError("Missing locked state-space controls: " + ", ".join(missing))
    features = list(STATE_SPACE_FEATURES)
    assert_pressure_safe(features)
    return features


def assert_pressure_safe(features) -> None:
    """Reject pressure controls after pressure has been removed from the target."""
    unsafe = [column for column in features if PRESSURE_TOKEN in column.lower()]
    if unsafe:
        raise ValueError(
            "Pressure-separated residual models cannot reintroduce pressure features: "
            + ", ".join(unsafe)
        )


def iforest_features(frame: pd.DataFrame) -> list[str]:
    """Return the shared Isolation Forest feature contract."""
    deltas = [column for column in frame.columns if "_delta_" in column]
    selected = [column for column in [*IFOREST_BASE_FEATURES, *deltas] if column in frame.columns]
    return list(dict.fromkeys(selected))


def model_payload(spec: DetectorSpec, fit: FittedDetector, **extra) -> dict:
    """Build a versioned pickle payload with explicit model identity."""
    return {
        "detector_schema_version": DETECTOR_SCHEMA_VERSION,
        "detector_spec": spec.to_dict(),
        "model_type": spec.family,
        "fit_status": fit.status,
        "fit_detail": fit.detail,
        "fit_diagnostics": fit.diagnostics,
        "model": fit.model,
        **extra,
    }


def load_detector_spec(path: Path | str, detector: str) -> DetectorSpec:
    """Load a current detector spec; reject stale family-ambiguous artifacts."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Run the full-record {detector} script first: {path}")
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    if payload.get("detector_schema_version") != DETECTOR_SCHEMA_VERSION:
        raise RuntimeError(
            f"{path} predates the shared detector contract; rerun its full-record script"
        )
    spec = DetectorSpec.from_dict(payload["detector_spec"])
    if spec.detector != detector:
        raise ValueError(f"{path} contains {spec.detector}, expected {detector}")
    return spec


def _series(y) -> pd.Series:
    return pd.Series(y).astype(float)


def _frame(x, features) -> pd.DataFrame:
    frame = pd.DataFrame(x).loc[:, list(features)].astype(float)
    return frame.replace([np.inf, -np.inf], np.nan)


def _scaled_train(x: pd.DataFrame):
    scaler = StandardScaler()
    scaled = pd.DataFrame(
        scaler.fit_transform(x),
        index=x.index,
        columns=x.columns,
    )
    return scaler, scaled


def _scaled_score(scaler, x: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        scaler.transform(x),
        index=x.index,
        columns=x.columns,
    )


def _optimizer_diagnostics(result, caught_warnings) -> dict:
    mle = getattr(result, "mle_retvals", {}) or {}
    categories = [item.category.__name__ for item in caught_warnings]
    messages = [str(item.message) for item in caught_warnings]
    return {
        "converged": mle.get("converged"),
        "warnflag": mle.get("warnflag"),
        "iterations": mle.get("iterations"),
        "function_calls": mle.get("fcalls"),
        "aic": float(result.aic) if np.isfinite(result.aic) else np.nan,
        "bic": float(result.bic) if np.isfinite(result.bic) else np.nan,
        "log_likelihood": float(result.llf) if np.isfinite(result.llf) else np.nan,
        "warning_categories": "|".join(categories),
        "warning_messages": " | ".join(messages),
    }


def _statsmodels_status(result, caught_warnings) -> str:
    status = fitted_model_status(result)
    if any(item.category.__name__ == "ConvergenceWarning" for item in caught_warnings):
        return "non_converged"
    return status


def _failed(spec: DetectorSpec, exc: Exception) -> FittedDetector:
    return FittedDetector(
        spec=spec,
        status="failed",
        detail=f"{type(exc).__name__}: {exc}",
        diagnostics={"exception_type": type(exc).__name__},
    )


def _insufficient(spec: DetectorSpec, detail: str) -> FittedDetector:
    return FittedDetector(spec=spec, status="insufficient_data", detail=detail)


def _fit_sarimax(spec: DetectorSpec, y, x) -> FittedDetector:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    assert_pressure_safe(spec.features)
    y = _series(y)
    x = _frame(x, spec.features)
    if len(y) < 48 or int(y.notna().sum()) < 48 or x.isna().any(axis=None):
        return _insufficient(spec, "SARIMAX requires 48 observed target hours and finite controls")
    scaler, scaled = _scaled_train(x)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = SARIMAX(
            y,
            exog=scaled,
            order=spec.order,
            seasonal_order=spec.seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False, maxiter=spec.maxiter)
    status = _statsmodels_status(result, caught)
    prediction = pd.Series(np.asarray(result.fittedvalues), index=y.index)
    score = y - prediction
    warmup = max(int(result.loglikelihood_burn), spec.warmup_hours)
    score.iloc[:warmup] = np.nan
    diagnostics = _optimizer_diagnostics(result, caught)
    diagnostics["warmup_hours_masked"] = warmup
    return FittedDetector(
        spec=spec,
        status=status,
        detail=diagnostics["warning_messages"],
        model=result,
        scaler=scaler,
        train_score=score,
        train_prediction=prediction,
        diagnostics=diagnostics,
    )


def _arx_design(y: pd.Series, x: pd.DataFrame, p: int, d: int) -> pd.DataFrame:
    design = x.copy()
    target = y.diff(d) if d else y
    design["model_target"] = target
    for lag in range(1, p + 1):
        design[f"target_lag_{lag}"] = target.shift(lag)
    return design.replace([np.inf, -np.inf], np.nan)


def make_lagged_frame(
    model_frame,
    target_col,
    feature_cols,
    p,
    d,
    min_block_hours=168,
):
    """Build a gap-honest AR-X design frame for compatibility and tests."""
    from src.models.july import contiguous_blocks

    predictors = [*feature_cols, *[f"target_lag_{lag}" for lag in range(1, p + 1)]]
    parts = []
    for block_id, index in contiguous_blocks(model_frame.index, min_hours=min_block_hours):
        block = model_frame.loc[index, [target_col, *feature_cols]]
        design = _arx_design(block[target_col], block[feature_cols], p, d)
        design["block_id"] = block_id
        parts.append(design)
    if not parts:
        return pd.DataFrame(columns=[*feature_cols, "model_target", *predictors]), predictors
    return pd.concat(parts).dropna(subset=["model_target", *predictors]), predictors


def _fit_arx(spec: DetectorSpec, y, x) -> FittedDetector:
    assert_pressure_safe(spec.features)
    y = _series(y)
    x = _frame(x, spec.features)
    p, d, _ = spec.order
    design = _arx_design(y, x, p, d)
    predictors = [*spec.features, *[f"target_lag_{lag}" for lag in range(1, p + 1)]]
    usable = design.dropna(subset=["model_target", *predictors])
    if len(usable) < 48:
        return _insufficient(spec, "AR-X requires 48 complete lagged training rows")
    model = make_pipeline(StandardScaler(), RidgeCV(alphas=RIDGE_ALPHAS))
    model.fit(usable[predictors], usable["model_target"])
    prediction = pd.Series(model.predict(usable[predictors]), index=usable.index)
    score = usable["model_target"] - prediction
    n = len(score)
    k = len(predictors) + 1
    rss = float((score**2).sum())
    diagnostics = {
        "converged": True,
        "n_rows": n,
        "n_features": len(predictors),
        "rss": rss,
        "aic": n * np.log(max(rss / n, 1e-12)) + 2 * k,
        "bic": n * np.log(max(rss / n, 1e-12)) + np.log(n) * k,
        "ridge_alpha": float(model[-1].alpha_),
    }
    return FittedDetector(
        spec=spec,
        status="ok",
        model=model,
        train_score=score,
        train_prediction=prediction,
        diagnostics=diagnostics,
        history=y.tail(p + d),
    )


def local_level_filter(
    observed,
    q,
    r,
    initial_state=None,
    initial_variance=None,
    return_state=False,
):
    """Run a scalar local-level filter, preserving missing hours."""
    y = _series(observed)
    observed_values = y.dropna()
    if observed_values.empty:
        raise ValueError("Local-level filter requires at least one observation")
    state = float(observed_values.iloc[0] if initial_state is None else initial_state)
    variance = float(
        max(observed_values.var(ddof=0), 1e-6) if initial_variance is None else initial_variance
    )
    rows = []
    for timestamp, value in y.items():
        predicted_state = state
        predicted_variance = variance + q
        innovation_variance = float(predicted_variance + r)
        if pd.isna(value):
            innovation = np.nan
            standardized = np.nan
            state = predicted_state
            variance = predicted_variance
        else:
            innovation = float(value - predicted_state)
            gain = predicted_variance / innovation_variance
            state = predicted_state + gain * innovation
            variance = (1 - gain) * predicted_variance
            standardized = innovation / np.sqrt(innovation_variance)
        rows.append(
            {
                "timestamp_utc": timestamp,
                "predicted_state": predicted_state,
                "filtered_state": state,
                "filtered_variance": variance,
                "innovation": innovation,
                "innovation_variance": innovation_variance,
                "standardized_innovation": standardized,
            }
        )
    output = pd.DataFrame(rows)
    if return_state:
        return output, state, variance
    return output


def tune_q_r(residualized_blocks):
    """Choose local-level Q/R with a compact pooled likelihood grid."""
    pooled = pd.concat([_series(block).dropna() for block in residualized_blocks])
    base_var = max(float(pooled.var(ddof=0)), 1e-6)
    rows = []
    for q_scale in Q_SCALES:
        for r_scale in R_SCALES:
            q = base_var * q_scale
            r = base_var * r_scale
            nll = 0.0
            for block in residualized_blocks:
                filtered = local_level_filter(block, q, r)
                innovation = filtered["innovation"]
                variance = filtered["innovation_variance"].clip(lower=1e-9)
                valid = innovation.notna()
                nll += float(
                    0.5
                    * (
                        np.log(2 * np.pi * variance.loc[valid])
                        + (innovation.loc[valid] ** 2) / variance.loc[valid]
                    ).sum()
                )
            rows.append(
                {
                    "q_scale": q_scale,
                    "r_scale": r_scale,
                    "q": q,
                    "r": r,
                    "negative_log_likelihood": nll,
                }
            )
    search = pd.DataFrame(rows).sort_values("negative_log_likelihood").reset_index(drop=True)
    best = search.iloc[0]
    return search, float(best["q"]), float(best["r"])


def _fit_local_level(spec: DetectorSpec, y, x) -> FittedDetector:
    from statsmodels.tsa.statespace.structural import UnobservedComponents

    assert_pressure_safe(spec.features)
    y = _series(y)
    x = _frame(x, spec.features)
    if len(y) < 48 or int(y.notna().sum()) < 48 or x.isna().any(axis=None):
        return _insufficient(
            spec, "Local-level state space requires 48 observed target hours and finite controls"
        )
    scaler, scaled = _scaled_train(x)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = UnobservedComponents(
            y,
            level="local level",
            exog=scaled,
        ).fit(disp=False, maxiter=spec.maxiter)
    status = _statsmodels_status(result, caught)
    prediction = pd.Series(np.asarray(result.fittedvalues), index=y.index)
    score = pd.Series(
        np.asarray(result.filter_results.standardized_forecasts_error[0]),
        index=y.index,
    )
    warmup = max(int(result.loglikelihood_burn), spec.warmup_hours)
    score.iloc[:warmup] = np.nan
    diagnostics = _optimizer_diagnostics(result, caught)
    diagnostics["warmup_hours_masked"] = warmup
    return FittedDetector(
        spec=spec,
        status=status,
        detail=diagnostics["warning_messages"],
        model=result,
        scaler=scaler,
        train_score=score,
        train_prediction=prediction,
        diagnostics=diagnostics,
    )


def _fit_ridge_local_level(spec: DetectorSpec, y, x) -> FittedDetector:
    assert_pressure_safe(spec.features)
    y = _series(y)
    x = _frame(x, spec.features)
    valid = y.notna() & ~x.isna().any(axis=1)
    if int(valid.sum()) < 48:
        return _insufficient(spec, "Ridge + local-level requires 48 complete training rows")
    model = make_pipeline(StandardScaler(), RidgeCV(alphas=RIDGE_ALPHAS))
    model.fit(x.loc[valid], y.loc[valid])
    exogenous_prediction = pd.Series(model.predict(x), index=x.index)
    residualized = y - exogenous_prediction
    search, q, r = tune_q_r([residualized])
    filtered, state, variance = local_level_filter(
        residualized,
        q,
        r,
        return_state=True,
    )
    filtered = filtered.set_index("timestamp_utc")
    prediction = exogenous_prediction + filtered["predicted_state"]
    score = filtered["standardized_innovation"].copy()
    score.iloc[: spec.warmup_hours] = np.nan
    diagnostics = {
        "converged": True,
        "n_rows": int(valid.sum()),
        "q": q,
        "r": r,
        "ridge_alpha": float(model[-1].alpha_),
        "negative_log_likelihood": float(search.iloc[0]["negative_log_likelihood"]),
        "warmup_hours_masked": spec.warmup_hours,
    }
    return FittedDetector(
        spec=spec,
        status="ok",
        model=model,
        train_score=score,
        train_prediction=prediction,
        diagnostics=diagnostics,
        tuning=search,
        q=q,
        r=r,
        final_state=state,
        final_variance=variance,
    )


def _fit_iforest(spec: DetectorSpec, x) -> FittedDetector:
    x = _frame(x, spec.features).dropna()
    if len(x) < 48:
        return _insufficient(spec, "Isolation Forest requires 48 complete training rows")
    model = IsolationForest(
        n_estimators=200,
        max_features=0.8,
        random_state=RANDOM_STATE,
        n_jobs=1,
    ).fit(x)
    score = pd.Series(-model.score_samples(x), index=x.index)
    return FittedDetector(
        spec=spec,
        status="ok",
        model=model,
        train_score=score,
        diagnostics={"converged": True, "n_rows": len(x), "n_features": x.shape[1]},
    )


def fit_detector(spec: DetectorSpec, y=None, x=None) -> FittedDetector:
    """Fit one specified family without silently substituting another."""
    try:
        if spec.family == "sarimax":
            return _fit_sarimax(spec, y, x)
        if spec.family == "arx":
            return _fit_arx(spec, y, x)
        if spec.family == "local_level_state_space":
            return _fit_local_level(spec, y, x)
        if spec.family == "ridge_local_level":
            return _fit_ridge_local_level(spec, y, x)
        if spec.family == "isolation_forest":
            return _fit_iforest(spec, x)
        raise ValueError(f"Unknown detector family: {spec.family}")
    except Exception as exc:
        return _failed(spec, exc)


def _search_row(key: str, spec: DetectorSpec, fit: FittedDetector) -> dict:
    return {
        "model_key": key,
        "model_type": spec.family,
        "order": str(spec.order) if spec.order is not None else "",
        "seasonal_order": (str(spec.seasonal_order) if spec.seasonal_order is not None else ""),
        "n_features": len(spec.features),
        "fit_status": fit.status,
        "fit_detail": fit.detail,
        **fit.diagnostics,
    }


def select_sarimax_spec(
    y,
    x,
    features,
    *,
    difference_order=0,
    full_grid=False,
    include_daily=True,
    include_weekly=False,
    maxiter=80,
):
    """Select a converged SARIMAX progressively, then an explicit AR-X fallback."""
    orders = (
        [(p, q) for p in range(3) for q in range(3)]
        if full_grid
        else [(1, 0), (1, 1), (1, 2), (2, 0)]
    )
    candidates = []
    rows = []
    for p, q in orders:
        spec = DetectorSpec(
            detector="sarimax",
            family="sarimax",
            features=tuple(features),
            order=(p, difference_order, q),
            seasonal_order=(0, 0, 0, 0),
            warmup_hours=24,
            maxiter=maxiter,
        )
        fit = fit_detector(spec, y, x)
        key = f"sarimax_p{p}_d{difference_order}_q{q}_nonseasonal"
        rows.append(_search_row(key, spec, fit))
        if fit.status == "ok":
            candidates.append((key, spec, fit))

    if candidates:
        base_key, base_spec, _ = min(
            candidates,
            key=lambda item: (
                item[2].diagnostics.get("bic", np.inf),
                item[2].diagnostics.get("aic", np.inf),
            ),
        )
        seasonal_periods = []
        if include_daily:
            seasonal_periods.append(("daily", 24))
        if include_weekly:
            seasonal_periods.append(("weekly_sensitivity", 168))
        for label, period in seasonal_periods:
            spec = DetectorSpec(
                detector="sarimax",
                family="sarimax",
                features=tuple(features),
                order=base_spec.order,
                seasonal_order=(1, 0, 1, period),
                warmup_hours=period if period == 24 else 24,
                maxiter=maxiter,
            )
            fit = fit_detector(spec, y, x)
            key = f"{base_key}_{label}"
            rows.append(_search_row(key, spec, fit))
            if fit.status == "ok":
                candidates.append((key, spec, fit))
    else:
        for p in (1, 2, 3):
            spec = DetectorSpec(
                detector="sarimax",
                family="arx",
                features=tuple(features),
                order=(p, difference_order, 0),
                seasonal_order=(0, 0, 0, 0),
            )
            fit = fit_detector(spec, y, x)
            key = f"arx_p{p}_d{difference_order}"
            rows.append(_search_row(key, spec, fit))
            if fit.status == "ok":
                candidates.append((key, spec, fit))

    if not candidates:
        search = pd.DataFrame(rows)
        raise RuntimeError(
            "No SARIMAX or AR-X candidate produced an ok fit\n"
            + search[["model_key", "fit_status", "fit_detail"]].to_string(index=False)
        )
    best_key, best_spec, best_fit = min(
        candidates,
        key=lambda item: (
            item[2].diagnostics.get("bic", np.inf),
            item[2].diagnostics.get("aic", np.inf),
        ),
    )
    search = pd.DataFrame(rows)
    search["selected"] = search["model_key"].eq(best_key)
    search = search.sort_values(
        ["selected", "fit_status", "bic", "aic"],
        ascending=[False, True, True, True],
        na_position="last",
    ).reset_index(drop=True)
    return best_spec, best_fit, search


def select_kalman_spec(y, x, features, *, maxiter=300):
    """Choose the state-space family once, with an explicit named fallback."""
    primary = DetectorSpec(
        detector="kalman",
        family="local_level_state_space",
        features=tuple(features),
        warmup_hours=3,
        maxiter=maxiter,
    )
    primary_fit = fit_detector(primary, y, x)
    rows = [_search_row("local_level_state_space", primary, primary_fit)]
    if primary_fit.status == "ok":
        search = pd.DataFrame(rows)
        search["selected"] = True
        return primary, primary_fit, search

    fallback = DetectorSpec(
        detector="kalman",
        family="ridge_local_level",
        features=tuple(features),
        warmup_hours=3,
    )
    fallback_fit = fit_detector(fallback, y, x)
    rows.append(_search_row("ridge_local_level", fallback, fallback_fit))
    search = pd.DataFrame(rows)
    search["selected"] = search["model_type"].eq(fallback.family)
    if fallback_fit.status != "ok":
        raise RuntimeError(
            "Neither local-level state space nor Ridge + local-level produced an ok fit\n"
            + search[["model_key", "fit_status", "fit_detail"]].to_string(index=False)
        )
    return fallback, fallback_fit, search


def _score_arx(fit: FittedDetector, y, x) -> DetectorScore:
    y = _series(y)
    x = _frame(x, fit.spec.features)
    p, d, _ = fit.spec.order
    history = fit.history
    combined = pd.concat([history, y])
    combined = combined.loc[~combined.index.duplicated(keep="last")]
    target = combined.diff(d) if d else combined
    design = x.copy()
    for lag in range(1, p + 1):
        design[f"target_lag_{lag}"] = target.shift(lag).reindex(x.index)
    predictors = [
        *fit.spec.features,
        *[f"target_lag_{lag}" for lag in range(1, p + 1)],
    ]
    valid = ~design[predictors].isna().any(axis=1) & target.reindex(x.index).notna()
    prediction = pd.Series(np.nan, index=x.index)
    prediction.loc[valid] = fit.model.predict(design.loc[valid, predictors])
    score = target.reindex(x.index) - prediction
    return DetectorScore(score=score, prediction=prediction)


def score_detector(
    fit: FittedDetector,
    y=None,
    x=None,
    *,
    in_sample=False,
) -> DetectorScore:
    """Score one fitted detector on training data or a future contiguous span."""
    if in_sample:
        return DetectorScore(fit.train_score.copy(), fit.train_prediction.copy())
    index = pd.DataFrame(x).index if x is not None else pd.Series(y).index
    empty = DetectorScore(
        pd.Series(np.nan, index=index, dtype=float),
        pd.Series(np.nan, index=index, dtype=float),
    )
    if fit.status != "ok":
        return empty

    if fit.spec.family == "arx":
        return _score_arx(fit, y, x)

    x = _frame(x, fit.spec.features)
    if fit.spec.family == "sarimax":
        y = _series(y)
        extended = fit.model.extend(y, exog=_scaled_score(fit.scaler, x))
        prediction = pd.Series(np.asarray(extended.fittedvalues), index=y.index)
        return DetectorScore(y - prediction, prediction)

    if fit.spec.family == "local_level_state_space":
        y = _series(y)
        extended = fit.model.extend(y, exog=_scaled_score(fit.scaler, x))
        score = pd.Series(
            np.asarray(extended.filter_results.standardized_forecasts_error[0]),
            index=y.index,
        )
        prediction = pd.Series(np.asarray(extended.fittedvalues), index=y.index)
        return DetectorScore(score, prediction)

    if fit.spec.family == "ridge_local_level":
        y = _series(y)
        exogenous_prediction = pd.Series(fit.model.predict(x), index=x.index)
        residualized = y - exogenous_prediction
        filtered = local_level_filter(
            residualized,
            fit.q,
            fit.r,
            initial_state=fit.final_state,
            initial_variance=fit.final_variance,
        ).set_index("timestamp_utc")
        prediction = exogenous_prediction + filtered["predicted_state"]
        return DetectorScore(filtered["standardized_innovation"], prediction)

    if fit.spec.family == "isolation_forest":
        valid = ~x.isna().any(axis=1)
        score = pd.Series(np.nan, index=x.index)
        score.loc[valid] = -fit.model.score_samples(x.loc[valid])
        return DetectorScore(score, pd.Series(np.nan, index=x.index))

    raise ValueError(f"Unknown detector family: {fit.spec.family}")


def robust_zscore(values, reference=None):
    """Median/MAD z-score with a standard-deviation fallback."""
    series = pd.Series(values).astype(float)
    ref = series if reference is None else pd.Series(reference).dropna().astype(float)
    median = ref.median()
    mad = (ref - median).abs().median()
    if pd.isna(mad) or mad == 0:
        std = ref.std(ddof=0)
        if pd.isna(std) or std == 0:
            return pd.Series(0.0, index=series.index)
        return (series - ref.mean()) / std
    return 0.6745 * (series - median) / mad


def flag_scores(score, reference=None, threshold=MAD_THRESHOLD):
    """Return anomaly flags, score coverage, and robust z-scores."""
    score = pd.Series(score).astype(float)
    z = robust_zscore(score, reference=reference)
    scored = score.notna() & z.notna()
    flags = (z.abs() > threshold) & scored
    return flags, scored, z
