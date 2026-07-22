"""Locked direct groundwater/mine-water analysis for the Kerkrade chapter."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.io_groundwater import select_primary_series
from src.models.july import TARGET_COL, contiguous_blocks

CONTROL_COLS = ("knmi_temperature_c", "knmi_relative_humidity_pct", "knmi_pressure_hpa")
MIN_HOURS_PER_DAY = 18
MIN_PAIRED_DAYS = 60
MIN_DAYS_PER_BLOCK = 15
HAC_MAXLAGS = 14
BOOTSTRAP_BLOCK_DAYS = 28
BOOTSTRAP_REPLICATES = 2000
PLACEBO_LEAD_DAYS = 7
SENSITIVITY_LAGS = (1, 3, 7, 14)
RANDOM_STATE = 42


def daily_iot_frame(frame):
    """Aggregate eligible residual days within honest contiguous IoT blocks."""
    missing = [column for column in (TARGET_COL, *CONTROL_COLS) if column not in frame]
    if missing:
        raise ValueError("Signal frame lacks direct-state columns: " + ", ".join(missing))
    observed = frame.index[frame[TARGET_COL].notna()]
    rows = []
    for block_id, index in contiguous_blocks(observed):
        block = frame.loc[index, [TARGET_COL, *CONTROL_COLS]].copy()
        block["date_utc"] = block.index.floor("D")
        for date_utc, day in block.groupby("date_utc"):
            residual_hours = int(day[TARGET_COL].notna().sum())
            if residual_hours < MIN_HOURS_PER_DAY:
                continue
            row = {
                "date_utc": date_utc,
                "block_id": block_id,
                "residual_ppm": day[TARGET_COL].mean(),
                "residual_hours": residual_hours,
            }
            row.update({column: day[column].mean() for column in CONTROL_COLS})
            rows.append(row)
    columns = [
        "date_utc",
        "block_id",
        "residual_ppm",
        "residual_hours",
        *CONTROL_COLS,
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return (
        pd.DataFrame(rows, columns=columns)
        .sort_values(["date_utc", "block_id"])
        .reset_index(drop=True)
    )


def _standardize(values):
    values = pd.Series(values).astype(float)
    scale = values.std(ddof=0)
    if not np.isfinite(scale) or scale == 0:
        return pd.Series(np.nan, index=values.index)
    return (values - values.mean()) / scale


def _design(model_frame, exposure_col):
    required = ["residual_ppm", exposure_col, *CONTROL_COLS, "block_id"]
    data = model_frame.replace([np.inf, -np.inf], np.nan).dropna(subset=required).copy()
    if len(data) < 15:
        return data, pd.DataFrame()
    dummies = pd.get_dummies(data["block_id"], prefix="block", drop_first=True, dtype=float)
    x = sm.add_constant(pd.concat([data[[exposure_col, *CONTROL_COLS]], dummies], axis=1))
    return data, x


def fit_exposure(model_frame, exposure_col="water_level_z", hac=True):
    """Fit the locked controlled model and return an explicit status row."""
    data, x = _design(model_frame, exposure_col)
    if x.empty or data[exposure_col].nunique() < 2:
        return (
            {
                "status": "insufficient_data",
                "n_days": len(data),
                "n_blocks": data["block_id"].nunique() if len(data) else 0,
                "coefficient": np.nan,
                "standard_error": np.nan,
                "t": np.nan,
                "p": np.nan,
            },
            None,
            data,
        )
    fit = sm.OLS(data["residual_ppm"], x).fit()
    if hac:
        fit = fit.get_robustcov_results(
            cov_type="HAC",
            maxlags=min(HAC_MAXLAGS, max(len(data) - 1, 0)),
        )
        names = list(x.columns)
        params = pd.Series(fit.params, index=names)
        bse = pd.Series(fit.bse, index=names)
        tvalues = pd.Series(fit.tvalues, index=names)
        pvalues = pd.Series(fit.pvalues, index=names)
    else:
        params, bse, tvalues, pvalues = fit.params, fit.bse, fit.tvalues, fit.pvalues
    return (
        {
            "status": "ok",
            "n_days": int(fit.nobs),
            "n_blocks": data["block_id"].nunique(),
            "coefficient": float(params[exposure_col]),
            "standard_error": float(bse[exposure_col]),
            "t": float(tvalues[exposure_col]),
            "p": float(pvalues[exposure_col]),
        },
        fit,
        data,
    )


def moving_block_bootstrap(model_frame, exposure_col, replicates=BOOTSTRAP_REPLICATES):
    """Bootstrap the water coefficient with independent moving blocks per IoT block."""
    _, _, base = fit_exposure(model_frame, exposure_col=exposure_col, hac=False)
    groups = [group.reset_index(drop=True) for _, group in base.groupby("block_id")]
    if not groups:
        return {
            "replicates_requested": replicates,
            "replicates_valid": 0,
            "ci_low": np.nan,
            "ci_high": np.nan,
        }
    rng = np.random.default_rng(RANDOM_STATE)
    coefficients = []
    for _ in range(replicates):
        parts = []
        for group in groups:
            n = len(group)
            length = min(BOOTSTRAP_BLOCK_DAYS, n)
            draws = []
            while sum(len(draw) for draw in draws) < n:
                start = int(rng.integers(0, n - length + 1))
                draws.append(group.iloc[start : start + length])
            parts.append(pd.concat(draws, ignore_index=True).iloc[:n])
        row, _, _ = fit_exposure(pd.concat(parts, ignore_index=True), exposure_col, hac=False)
        if row["status"] == "ok" and np.isfinite(row["coefficient"]):
            coefficients.append(row["coefficient"])
    return {
        "replicates_requested": replicates,
        "replicates_valid": len(coefficients),
        "ci_low": float(np.percentile(coefficients, 2.5)) if coefficients else np.nan,
        "ci_high": float(np.percentile(coefficients, 97.5)) if coefficients else np.nan,
    }


def _per_block(primary):
    rows = []
    for block_id, block in primary.groupby("block_id"):
        if (
            len(block.dropna(subset=["water_level_z", "residual_ppm", *CONTROL_COLS]))
            < MIN_DAYS_PER_BLOCK
        ):
            rows.append({"block_id": block_id, "status": "insufficient_data", "n_days": len(block)})
            continue
        fit_row, _, _ = fit_exposure(block, "water_level_z")
        fit_row["block_id"] = block_id
        rows.append(fit_row)
    if not rows:
        return pd.DataFrame(columns=["block_id", "status", "n_days", "coefficient"])
    return pd.DataFrame(rows)


def _shifted_exposure(water, days, output_col):
    shifted = water[["date_utc", "hydrologic_level"]].copy()
    shifted["date_utc"] = shifted["date_utc"] + pd.Timedelta(days=days)
    return shifted.rename(columns={"hydrologic_level": output_col})


def _fdr_bh(pvalues):
    pvalues = pd.Series(pvalues, dtype=float)
    valid = pvalues.dropna().sort_values()
    adjusted = pd.Series(np.nan, index=pvalues.index, dtype=float)
    if valid.empty:
        return adjusted
    ranked = valid.to_numpy() * len(valid) / np.arange(1, len(valid) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted.loc[valid.index] = np.minimum(ranked, 1.0)
    return adjusted


def _sensitivities(iot_daily, water_daily, primary_id):
    rows = []
    primary_water = water_daily.loc[water_daily["series_id"].eq(primary_id)].sort_values("date_utc")
    specifications = []
    for lag in SENSITIVITY_LAGS:
        specifications.append(
            (f"primary_lag_{lag}d", _shifted_exposure(primary_water, lag, "exposure"))
        )
    changed = primary_water[["date_utc", "hydrologic_level"]].copy()
    exact_prior = _shifted_exposure(primary_water, 1, "prior_level")
    changed = changed.merge(exact_prior, on="date_utc", how="left")
    changed["exposure"] = changed["hydrologic_level"] - changed["prior_level"]
    specifications.append(("primary_daily_change", changed[["date_utc", "exposure"]]))
    for series_id, series in water_daily.groupby("series_id"):
        if series_id != primary_id:
            specifications.append(
                (
                    f"alternative_{series_id}_same_day",
                    series.rename(columns={"hydrologic_level": "exposure"})[
                        ["date_utc", "exposure"]
                    ],
                )
            )

    for name, exposure in specifications:
        model = iot_daily.merge(exposure, on="date_utc", how="inner")
        model["exposure_z"] = _standardize(model["exposure"])
        fit_row, _, _ = fit_exposure(model, "exposure_z")
        rows.append({"specification": name, **fit_row})
    output = pd.DataFrame(rows)
    output["p_fdr_bh"] = _fdr_bh(output["p"])
    output["analysis_role"] = "secondary_sensitivity"
    return output


def run_direct_state(frame, water_daily, metadata, bootstrap_replicates=BOOTSTRAP_REPLICATES):
    """Run the locked primary analysis and return all reviewable result tables."""
    iot_daily = daily_iot_frame(frame)
    water_daily = pd.DataFrame(water_daily).copy()
    water_daily["date_utc"] = pd.to_datetime(water_daily["date_utc"], utc=True).dt.floor("D")
    primary_id, selection = select_primary_series(water_daily, metadata, iot_daily["date_utc"])
    primary_water = water_daily.loc[water_daily["series_id"].eq(primary_id)]
    primary = iot_daily.merge(primary_water, on="date_utc", how="inner")
    complete = primary.dropna(subset=["residual_ppm", "hydrologic_level", *CONTROL_COLS])
    block_counts = complete.groupby("block_id").size()
    qualifying_ids = block_counts.loc[block_counts >= MIN_DAYS_PER_BLOCK].index
    primary = primary.loc[primary["block_id"].isin(qualifying_ids)].copy()
    primary["water_level_z"] = _standardize(primary["hydrologic_level"])
    primary_fit, _, model_days = fit_exposure(primary)
    qualifying_blocks = len(qualifying_ids)
    coverage_pass = len(model_days) >= MIN_PAIRED_DAYS and qualifying_blocks >= 2

    bootstrap = moving_block_bootstrap(
        primary,
        "water_level_z",
        replicates=bootstrap_replicates,
    )
    per_block = _per_block(primary)
    future = _shifted_exposure(primary_water, -PLACEBO_LEAD_DAYS, "future_level")
    iot_usable = iot_daily.loc[iot_daily["block_id"].isin(qualifying_ids)]
    placebo_frame = iot_usable.merge(future, on="date_utc", how="inner")
    placebo_frame["future_water_z"] = _standardize(placebo_frame["future_level"])
    placebo, _, _ = fit_exposure(placebo_frame, "future_water_z")

    ok_blocks = per_block.loc[per_block.get("status", pd.Series(dtype=str)).eq("ok")]
    same_sign_blocks = (
        int((np.sign(ok_blocks["coefficient"]) == np.sign(primary_fit["coefficient"])).sum())
        if primary_fit["status"] == "ok" and not ok_blocks.empty
        else 0
    )
    criteria = {
        "coverage_gate": coverage_pass,
        "primary_hac_p_lt_0p05": primary_fit["status"] == "ok" and primary_fit["p"] < 0.05,
        "bootstrap_ci_excludes_zero": bootstrap["ci_low"] > 0 or bootstrap["ci_high"] < 0,
        "same_sign_in_two_blocks": same_sign_blocks >= 2,
        "future_water_placebo_abs_t_lt_2": placebo["status"] == "ok" and abs(placebo["t"]) < 2,
    }
    supported = all(criteria.values())
    if supported:
        outcome = "direct_state_primary_supported"
    elif not coverage_pass:
        outcome = "inconclusive_because_of_coverage"
    else:
        outcome = "null_boundary_result"
    decision = pd.DataFrame(
        [{"criterion": name, "passed": bool(passed)} for name, passed in criteria.items()]
    )
    summary = {
        "primary_series_id": primary_id,
        "outcome": outcome,
        "paired_days": len(model_days),
        "qualifying_blocks": qualifying_blocks,
        "same_sign_blocks": same_sign_blocks,
        **{f"primary_{key}": value for key, value in primary_fit.items()},
        **{f"bootstrap_{key}": value for key, value in bootstrap.items()},
        **{f"placebo_{key}": value for key, value in placebo.items()},
    }
    return {
        "summary": summary,
        "decision": decision,
        "selection": selection,
        "daily_analysis": primary,
        "per_block": per_block,
        "sensitivities": _sensitivities(iot_usable, water_daily, primary_id),
    }
