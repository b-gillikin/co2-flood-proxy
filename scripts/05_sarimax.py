"""July Week 1 provisional SARIMAX-family residual modelling."""

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
from scipy import stats
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.models.july import (
    CO2_COL,
    TARGET_COL,
    anomaly_table,
    autocorrelation,
    available_exog,
    complete_model_frame,
    load_signal_frame,
)


PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results/sarimax")
MODELS_DIR = Path("results/models")

MODEL_PATH = MODELS_DIR / "sarimax.pkl"
ORDER_SEARCH_PATH = MODELS_DIR / "sarimax_order_search.csv"
RESIDUAL_PATH = PROCESSED_DIR / "sarimax-residuals.csv"
ANOMALY_PATH = PROCESSED_DIR / "sarimax-anomalies.csv"

RANDOM_STATE = 42
RIDGE_ALPHAS = (0.01, 0.1, 1.0, 10.0, 100.0)


def stationarity_tests(series, name):
    """Run ADF/KPSS when statsmodels is available; otherwise record fallback."""
    series = pd.Series(series).dropna().astype(float)
    row = {"series": name, "n_rows": len(series), "skew": series.skew()}
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
    except ImportError:
        row.update(
            {
                "adf_pvalue": np.nan,
                "kpss_pvalue": np.nan,
                "decision": "not_tested_statsmodels_unavailable",
                "difference_order": 0,
            }
        )
        return row

    adf = adfuller(series, autolag="AIC")
    kpss_result = kpss(series, regression="c", nlags="auto")
    nonstationary = adf[1] > 0.05 and kpss_result[1] < 0.05
    row.update(
        {
            "adf_pvalue": adf[1],
            "kpss_pvalue": kpss_result[1],
            "decision": "difference" if nonstationary else "keep_level",
            "difference_order": int(nonstationary),
        }
    )
    return row


def co2_transform_decision(series):
    """Record the CO2 variance-stabilization decision."""
    series = pd.Series(series).dropna().astype(float)
    skew = series.skew()
    positive = bool((series > 0).all())
    if positive and abs(skew) > 2:
        transformed, lambda_value = stats.boxcox(series)
        return {
            "series": CO2_COL,
            "transform": "boxcox",
            "lambda": lambda_value,
            "original_skew": skew,
            "transformed_skew": pd.Series(transformed).skew(),
        }
    return {
        "series": CO2_COL,
        "transform": "none",
        "lambda": np.nan,
        "original_skew": skew,
        "transformed_skew": skew,
    }


def make_lagged_frame(model_frame, target_col, feature_cols, p, d):
    """Build an AR-X design matrix for the statsmodels-free fallback."""
    out = model_frame[[target_col, *feature_cols]].copy()
    y = out[target_col].diff(d) if d else out[target_col]
    out["model_target"] = y
    for lag in range(1, p + 1):
        out[f"target_lag_{lag}"] = y.shift(lag)
    predictors = [*feature_cols, *[f"target_lag_{lag}" for lag in range(1, p + 1)]]
    out = out.dropna(subset=["model_target", *predictors])
    return out, predictors


def fit_fallback_arx(model_frame, target_col, feature_cols, d):
    """Fit a small AR-with-exogenous grid when SARIMAX is unavailable."""
    rows = []
    fits = {}
    for p in (1, 2, 3):
        lagged, predictors = make_lagged_frame(model_frame, target_col, feature_cols, p, d)
        x = lagged[predictors]
        y = lagged["model_target"]
        model = make_pipeline(StandardScaler(), RidgeCV(alphas=RIDGE_ALPHAS))
        model.fit(x, y)
        fitted = pd.Series(model.predict(x), index=lagged.index)
        residual = y - fitted
        n = len(residual)
        k = len(predictors) + 1
        rss = float((residual**2).sum())
        aic = n * np.log(max(rss / n, 1e-12)) + 2 * k
        bic = n * np.log(max(rss / n, 1e-12)) + np.log(n) * k
        key = f"arx_p{p}_d{d}"
        rows.append(
            {
                "model_key": key,
                "model_type": "fallback_arx",
                "order": f"({p},{d},0)",
                "seasonal_order": "(0,0,0,0)",
                "n_rows": n,
                "n_features": len(predictors),
                "aic": aic,
                "bic": bic,
                "rss": rss,
            }
        )
        fits[key] = {
            "model": model,
            "predictors": predictors,
            "lagged": lagged,
            "fitted": fitted,
            "residual": residual,
        }

    search = pd.DataFrame(rows).sort_values(["bic", "aic"]).reset_index(drop=True)
    best_key = search.iloc[0]["model_key"]
    return search, fits[best_key], best_key


def fit_statsmodels_sarimax(model_frame, target_col, feature_cols, d):
    """Fit the planned compact SARIMAX grid when statsmodels is installed."""
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except ImportError:
        return None

    y = model_frame[target_col].astype(float)
    x = model_frame[feature_cols].astype(float)
    rows = []
    fits = {}
    seasonal_specs = [
        ("daily", (1, 0, 1, 24)),
        ("weekly_sensitivity", (1, 0, 1, 168)),
    ]

    for p in range(3):
        for q in range(3):
            for seasonal_label, seasonal_order in seasonal_specs:
                key = f"sarimax_p{p}_d{d}_q{q}_{seasonal_label}"
                try:
                    model = SARIMAX(
                        y,
                        exog=x,
                        order=(p, d, q),
                        seasonal_order=seasonal_order,
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    )
                    result = model.fit(disp=False, maxiter=200)
                    fitted = pd.Series(result.fittedvalues, index=model_frame.index)
                    residual = y - fitted
                    rows.append(
                        {
                            "model_key": key,
                            "model_type": "statsmodels_sarimax",
                            "order": f"({p},{d},{q})",
                            "seasonal_order": str(seasonal_order),
                            "n_rows": len(residual.dropna()),
                            "n_features": len(feature_cols),
                            "aic": float(result.aic),
                            "bic": float(result.bic),
                            "rss": float((residual.dropna() ** 2).sum()),
                            "fit_status": "ok",
                        }
                    )
                    fits[key] = {
                        "model": result,
                        "predictors": feature_cols,
                        "lagged": model_frame,
                        "fitted": fitted,
                        "residual": residual,
                    }
                except Exception as exc:
                    rows.append(
                        {
                            "model_key": key,
                            "model_type": "statsmodels_sarimax",
                            "order": f"({p},{d},{q})",
                            "seasonal_order": str(seasonal_order),
                            "n_rows": len(model_frame),
                            "n_features": len(feature_cols),
                            "aic": np.nan,
                            "bic": np.nan,
                            "rss": np.nan,
                            "fit_status": f"failed: {type(exc).__name__}",
                        }
                    )

    search = pd.DataFrame(rows)
    ok = search[search["fit_status"] == "ok"].copy()
    if ok.empty:
        return None
    ok = ok.sort_values(["bic", "aic"]).reset_index(drop=True)
    search = pd.concat([ok, search[search["fit_status"] != "ok"]], ignore_index=True)
    best_key = ok.iloc[0]["model_key"]
    return search, fits[best_key], best_key


def write_residual_plots(residuals):
    """Write residual time-series, ACF, and Q-Q diagnostics."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    residual = residuals["sarimax_residual"]

    fig, axis = plt.subplots(figsize=(12, 4), constrained_layout=True)
    axis.plot(residuals["timestamp_utc"], residual, linewidth=1)
    axis.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    axis.set_title("SARIMAX-family provisional residuals")
    axis.set_ylabel("Residual")
    axis.grid(True, alpha=0.25)
    fig.savefig(RESULTS_DIR / "residual_timeseries.png", dpi=160)
    plt.close(fig)

    acf = autocorrelation(residual, max_lag=48)
    fig, axis = plt.subplots(figsize=(9, 4), constrained_layout=True)
    axis.bar(acf["lag"], acf["acf"], width=0.8)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_title("Residual autocorrelation")
    axis.set_xlabel("Lag hours")
    axis.set_ylabel("ACF")
    fig.savefig(RESULTS_DIR / "residual_acf.png", dpi=160)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(5, 5), constrained_layout=True)
    stats.probplot(residual.dropna(), dist="norm", plot=axis)
    axis.set_title("Residual Q-Q plot")
    fig.savefig(RESULTS_DIR / "residual_qq.png", dpi=160)
    plt.close(fig)


def write_summary(stationarity, transform, search, best_key, feature_cols, model_type):
    """Write the text summary used as the first-pass SARIMAX audit trail."""
    lines = [
        "July Week 1 SARIMAX First Pass",
        "",
        "Status: provisional pipeline-first run.",
        f"Model path: {model_type}.",
        "",
        "Stationarity decisions:",
    ]
    for row in stationarity:
        lines.append(
            f"  {row['series']}: {row['decision']} "
            f"(ADF p={row['adf_pvalue']}, KPSS p={row['kpss_pvalue']})"
        )
    lines.extend(
        [
            "",
            f"CO2 transform decision: {transform['transform']} "
            f"(skew={transform['original_skew']:.3f})",
            "Selected provisional order: "
            f"{search.loc[search['model_key'] == best_key, 'order'].iloc[0]}",
            "Selected seasonal order: "
            f"{search.loc[search['model_key'] == best_key, 'seasonal_order'].iloc[0]}",
            f"Exogenous features used: {', '.join(feature_cols)}",
        ]
    )
    if "fallback" in model_type:
        lines.append("Weekly seasonal SARIMAX sensitivity: skipped in fallback AR-X path.")
    (RESULTS_DIR / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    """Command-line entry point."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_signal_frame()
    feature_cols = available_exog(frame)
    model_frame, feature_cols = complete_model_frame(frame, TARGET_COL, feature_cols)

    stationarity = [
        stationarity_tests(frame[CO2_COL], CO2_COL),
        stationarity_tests(frame[TARGET_COL], TARGET_COL),
    ]
    d = int(next(row["difference_order"] for row in stationarity if row["series"] == TARGET_COL))
    transform = co2_transform_decision(frame[CO2_COL])

    sarimax_fit = fit_statsmodels_sarimax(model_frame, TARGET_COL, feature_cols, d)
    if sarimax_fit is None:
        search, fit, best_key = fit_fallback_arx(model_frame, TARGET_COL, feature_cols, d)
        model_type = (
            "fallback AR-X because statsmodels is not importable or no "
            "SARIMAX grid fit converged"
        )
    else:
        search, fit, best_key = sarimax_fit
        model_type = "statsmodels SARIMAX"
    lagged = fit["lagged"]
    observed = lagged["model_target"] if "model_target" in lagged.columns else lagged[TARGET_COL]
    residuals = pd.DataFrame(
        {
            "timestamp_utc": lagged.index,
            "target": TARGET_COL,
            "observed": observed.to_numpy(),
            "fitted": fit["fitted"].to_numpy(),
            "sarimax_residual": fit["residual"].to_numpy(),
            "model_type": search.loc[search["model_key"] == best_key, "model_type"].iloc[0],
            "model_key": best_key,
        }
    )
    anomalies = anomaly_table(
        pd.DatetimeIndex(residuals["timestamp_utc"]),
        residuals["sarimax_residual"],
        prefix="sarimax",
    )

    search.to_csv(ORDER_SEARCH_PATH, index=False)
    residuals.to_csv(RESIDUAL_PATH, index=False)
    anomalies.to_csv(ANOMALY_PATH, index=False)

    with MODEL_PATH.open("wb") as handle:
        pickle.dump(
            {
                "model_type": search.loc[search["model_key"] == best_key, "model_type"].iloc[0],
                "model_key": best_key,
                "model": fit["model"],
                "predictors": fit["predictors"],
                "feature_cols": feature_cols,
                "target_col": TARGET_COL,
                "difference_order": d,
                "stationarity": stationarity,
                "co2_transform": transform,
            },
            handle,
        )

    write_residual_plots(residuals)
    write_summary(stationarity, transform, search, best_key, feature_cols, model_type)

    print(f"wrote {MODEL_PATH}")
    print(f"wrote {RESIDUAL_PATH} ({len(residuals)} rows)")
    print(f"wrote {ANOMALY_PATH} ({len(anomalies)} rows)")
    print(f"selected {best_key}")


if __name__ == "__main__":
    main()
