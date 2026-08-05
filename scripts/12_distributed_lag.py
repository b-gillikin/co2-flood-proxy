"""Distributed-lag test of the multi-week antecedent-wetness signal.

An exploratory lag scan suggested the barometric CO2 residual co-moves with
antecedent hydrology at roughly a ten-day lead. This script tests that
suggestion with regression machinery honest to the record's block structure:

- Daily aggregation per contiguous block (days need >= 18 observed hours).
- Primary: a timescale scan regressing the daily residual on an
  exponentially weighted antecedent-precipitation index across a grid of
  half-lives, with same-day meteorology and block fixed effects as controls.
- Confirmatory inference at the pre-stated half-life of 10 days (from the
  exploratory scan), with HAC standard errors and a moving-block bootstrap.
- Placebo: the same scan on *future* precipitation (leads), which must show
  nothing if the lagged structure is real.
- Secondary: binned distributed lags for precipitation and discharge.

The decision rule is stated in DECISION_RULE below and evaluated verbatim in
the summary, so the outcome cannot be reinterpreted after the fact.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.models.signal_frame import TARGET_COL, contiguous_blocks, load_signal_frame

RESULTS_DIR = Path("results/distributed_lag")

MIN_BLOCK_HOURS = 168
MIN_HOURS_PER_DAY = 18
MIN_DAYS_PER_BLOCK = 15
MAX_LAG_DAYS = 30

HALF_LIFE_GRID_DAYS = (0.5, 1, 2, 3, 5, 7, 10, 14, 20)
CONFIRMATORY_HALF_LIFE_DAYS = 10
LAG_BINS = ((0, 1), (2, 4), (5, 9), (10, 14))

HAC_MAXLAGS = 14
BOOTSTRAP_REPLICATES = 2000
BOOTSTRAP_BLOCK_DAYS = 28
RANDOM_STATE = 42

PRECIP_SOURCES = {
    "knmi_precip": "knmi_precip_mm",
    "visualcrossing_precip": "kerkrade_weather_precip_mm",
}
PRIMARY_PRECIP = "knmi_precip"
DISCHARGE_COL = "discharge_geul_hommerich_m3s"
CONTROL_COLS = ["knmi_temperature_c", "knmi_relative_humidity_pct", "knmi_pressure_hpa"]

DECISION_RULE = (
    "SUPPORTED requires all of: (1) the timescale scan peaks at a half-life "
    ">= 3 days; (2) pooled HAC p < 0.05 for the API coefficient at the "
    "pre-stated confirmatory half-life of 10 days; (3) the moving-block "
    "bootstrap 95% CI at 10 days excludes zero; (4) the coefficient has the "
    "same sign in at least two usable blocks at 10 days; (5) the future-"
    "precipitation placebo at 10 days is null (|t| < 2)."
)


def daily_block_frame():
    """Aggregate the hourly signal frame to a per-block daily frame."""
    frame = load_signal_frame()
    observed = frame.index[frame[TARGET_COL].notna()]
    blocks = contiguous_blocks(observed, min_hours=MIN_BLOCK_HOURS)

    rows = []
    for block_id, block_index in blocks:
        block = frame.loc[block_index.min() : block_index.max()]
        by_day = block.groupby(block.index.floor("D"))

        daily = pd.DataFrame(
            {
                "residual_ppm": by_day[TARGET_COL].mean(),
                "residual_hours": by_day[TARGET_COL].count(),
            }
        )
        for name, column in PRECIP_SOURCES.items():
            if column in block.columns:
                daily[f"{name}_mm"] = by_day[column].sum(min_count=MIN_HOURS_PER_DAY)
        if DISCHARGE_COL in block.columns:
            daily["discharge_m3s"] = by_day[DISCHARGE_COL].mean()
        for column in CONTROL_COLS:
            if column in block.columns:
                daily[column] = by_day[column].mean()

        daily.loc[daily["residual_hours"] < MIN_HOURS_PER_DAY, "residual_ppm"] = np.nan
        daily["block_id"] = block_id
        rows.append(daily)

    out = pd.concat(rows)
    out.index.name = "date_utc"
    return out


def weighted_api(precip, half_life_days, direction="lag"):
    """Exponentially weighted antecedent (or future, for placebo) precip.

    Weights are normalized to sum to one, so the regression coefficient is in
    ppm per mm/day of decay-weighted rainfall regardless of half-life. NaNs
    propagate, so early block days without full history drop out naturally.
    """
    max_k = min(MAX_LAG_DAYS, max(2, int(np.ceil(4 * half_life_days))))
    weights = np.exp(-np.log(2) * np.arange(1, max_k + 1) / half_life_days)
    weights = weights / weights.sum()
    shifted = pd.concat(
        {k: precip.shift(k if direction == "lag" else -k) for k in range(1, max_k + 1)},
        axis=1,
    )
    return shifted.mul(weights, axis=1).sum(axis=1, min_count=max_k)


def fit_pooled(daily, api_col):
    """OLS with same-day met controls and block fixed effects, HAC errors."""
    model_frame = daily.dropna(subset=["residual_ppm", api_col, *CONTROL_COLS])
    if model_frame["block_id"].nunique() > 1:
        dummies = pd.get_dummies(
            model_frame["block_id"], prefix="block", drop_first=True, dtype=float
        )
    else:
        dummies = pd.DataFrame(index=model_frame.index)
    x = pd.concat([model_frame[[api_col, *CONTROL_COLS]], dummies], axis=1)
    x = sm.add_constant(x)
    result = sm.OLS(model_frame["residual_ppm"], x).fit(
        cov_type="HAC", cov_kwds={"maxlags": HAC_MAXLAGS}
    )
    return result, model_frame


def scan_row(daily, half_life, direction, source):
    """One timescale-scan fit summarized as a table row."""
    api_col = f"api_{source}"
    scan_frame = daily.copy()
    scan_frame[api_col] = scan_frame.groupby("block_id")[f"{source}_mm"].transform(
        lambda s: weighted_api(s, half_life, direction)
    )
    result, model_frame = fit_pooled(scan_frame, api_col)
    return (
        {
            "source": source,
            "direction": direction,
            "half_life_days": half_life,
            "n_days": int(result.nobs),
            "coef_ppm_per_mm_day": float(result.params[api_col]),
            "hac_se": float(result.bse[api_col]),
            "t": float(result.tvalues[api_col]),
            "p": float(result.pvalues[api_col]),
            "r2": float(result.rsquared),
        },
        scan_frame,
        api_col,
    )


def per_block_fits(scan_frame, api_col):
    """Fit the confirmatory model separately inside each usable block."""
    rows = []
    for block_id, block in scan_frame.groupby("block_id"):
        model_frame = block.dropna(subset=["residual_ppm", api_col, *CONTROL_COLS])
        if len(model_frame) < MIN_DAYS_PER_BLOCK:
            rows.append(
                {
                    "block_id": block_id,
                    "n_days": len(model_frame),
                    "status": "too_short",
                    "coef_ppm_per_mm_day": np.nan,
                    "hac_se": np.nan,
                    "t": np.nan,
                }
            )
            continue
        x = sm.add_constant(model_frame[[api_col, *CONTROL_COLS]])
        result = sm.OLS(model_frame["residual_ppm"], x).fit(
            cov_type="HAC", cov_kwds={"maxlags": HAC_MAXLAGS}
        )
        rows.append(
            {
                "block_id": block_id,
                "n_days": int(result.nobs),
                "status": "ok",
                "coef_ppm_per_mm_day": float(result.params[api_col]),
                "hac_se": float(result.bse[api_col]),
                "t": float(result.tvalues[api_col]),
            }
        )
    return pd.DataFrame(rows)


def moving_block_bootstrap(scan_frame, api_col, replicates=BOOTSTRAP_REPLICATES):
    """Percentile CI for the confirmatory API coefficient."""
    rng = np.random.default_rng(RANDOM_STATE)
    base = scan_frame.dropna(subset=["residual_ppm", api_col, *CONTROL_COLS])
    block_arrays = [group for _, group in base.groupby("block_id")]
    coefs = []
    for _ in range(replicates):
        parts = []
        for group in block_arrays:
            n = len(group)
            if n < 5:
                parts.append(group)
                continue
            length = min(BOOTSTRAP_BLOCK_DAYS, n)
            picks = []
            while sum(len(p) for p in picks) < n:
                start = int(rng.integers(0, n - length + 1))
                picks.append(group.iloc[start : start + length])
            parts.append(pd.concat(picks).iloc[:n])
        sample = pd.concat(parts)
        if sample["block_id"].nunique() > 1:
            dummies = pd.get_dummies(
                sample["block_id"], prefix="block", drop_first=True, dtype=float
            )
        else:
            dummies = pd.DataFrame(index=sample.index)
        x = sm.add_constant(pd.concat([sample[[api_col, *CONTROL_COLS]], dummies], axis=1))
        try:
            coefs.append(float(sm.OLS(sample["residual_ppm"], x).fit().params[api_col]))
        except Exception:
            continue
    coefs = np.asarray(coefs)
    return {
        "n_replicates": len(coefs),
        "ci_low": float(np.percentile(coefs, 2.5)),
        "ci_high": float(np.percentile(coefs, 97.5)),
    }


def lag_bin_fits(daily, value_col, label, statistic):
    """Binned distributed-lag model for one predictor series."""
    frame = daily.copy()
    bin_cols = []
    for low, high in LAG_BINS:
        column = f"{label}_lag_{low}_{high}d"
        lags = pd.concat(
            {k: frame.groupby("block_id")[value_col].shift(k) for k in range(low, high + 1)},
            axis=1,
        )
        frame[column] = (
            lags.sum(axis=1, min_count=high - low + 1) if statistic == "sum" else lags.mean(axis=1)
        )
        frame.loc[lags.isna().any(axis=1), column] = np.nan
        bin_cols.append(column)

    model_frame = frame.dropna(subset=["residual_ppm", *bin_cols, *CONTROL_COLS])
    if len(model_frame) < 30:
        return pd.DataFrame(
            [{"predictor": label, "status": "insufficient_days", "n_days": len(model_frame)}]
        )
    dummies = pd.get_dummies(model_frame["block_id"], prefix="block", drop_first=True, dtype=float)
    x = sm.add_constant(pd.concat([model_frame[[*bin_cols, *CONTROL_COLS]], dummies], axis=1))
    result = sm.OLS(model_frame["residual_ppm"], x).fit(
        cov_type="HAC", cov_kwds={"maxlags": HAC_MAXLAGS}
    )
    rows = []
    for column in bin_cols:
        rows.append(
            {
                "predictor": label,
                "lag_bin": column.split("_lag_")[1],
                "status": "ok",
                "n_days": int(result.nobs),
                "coef": float(result.params[column]),
                "hac_se": float(result.bse[column]),
                "t": float(result.tvalues[column]),
                "p": float(result.pvalues[column]),
            }
        )
    return pd.DataFrame(rows)


def write_scan_plot(scan):
    """Plot the lag and placebo timescale-scan curves."""
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, constrained_layout=True)
    for direction, axis, title in (
        ("lag", axes[0], "Antecedent precipitation (lags)"),
        ("lead", axes[1], "Placebo: future precipitation (leads)"),
    ):
        subset = scan.loc[(scan["direction"] == direction) & (scan["source"] == PRIMARY_PRECIP)]
        axis.errorbar(
            subset["half_life_days"],
            subset["coef_ppm_per_mm_day"],
            yerr=1.96 * subset["hac_se"],
            marker="o",
            linewidth=1,
        )
        axis.axhline(0, color="black", linewidth=0.8, alpha=0.6)
        axis.axvline(CONFIRMATORY_HALF_LIFE_DAYS, color="tab:red", linestyle="--", alpha=0.5)
        axis.set_ylabel("ppm per weighted mm/day")
        axis.set_title(title)
        axis.grid(True, alpha=0.25)
    axes[1].set_xlabel("API half-life (days)")
    axes[1].set_xscale("log")
    fig.savefig(RESULTS_DIR / "timescale_scan.png", dpi=160)
    plt.close(fig)


def evaluate_decision(scan, confirmatory, bootstrap, blocks, placebo):
    """Apply the pre-stated decision rule and return per-criterion results."""
    lag_scan = scan.loc[(scan["direction"] == "lag") & (scan["source"] == PRIMARY_PRECIP)]
    peak = lag_scan.loc[lag_scan["t"].abs().idxmax()]
    usable = blocks.loc[blocks["status"] == "ok"]
    sign_agreement = (
        int(
            (
                np.sign(usable["coef_ppm_per_mm_day"])
                == np.sign(confirmatory["coef_ppm_per_mm_day"])
            ).sum()
        )
        if not usable.empty
        else 0
    )
    criteria = {
        "1_peak_half_life_ge_3d": bool(peak["half_life_days"] >= 3),
        "2_pooled_hac_p_lt_0p05_at_10d": bool(confirmatory["p"] < 0.05),
        "3_bootstrap_ci_excludes_zero": bool(bootstrap["ci_low"] > 0 or bootstrap["ci_high"] < 0),
        "4_same_sign_in_ge_2_blocks": bool(sign_agreement >= 2),
        "5_placebo_null_at_10d": bool(abs(placebo["t"]) < 2),
    }
    return criteria, peak


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bootstrap-replicates",
        type=int,
        default=BOOTSTRAP_REPLICATES,
        help="Moving-block bootstrap replicates (locked default: 2000).",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    daily = daily_block_frame()
    daily.to_csv(RESULTS_DIR / "daily_frame.csv")

    scan_rows = []
    confirmatory_frame = None
    confirmatory_col = None
    for source in PRECIP_SOURCES:
        if f"{source}_mm" not in daily.columns:
            continue
        for direction in ("lag", "lead"):
            for half_life in HALF_LIFE_GRID_DAYS:
                row, scan_frame, api_col = scan_row(daily, half_life, direction, source)
                scan_rows.append(row)
                if (
                    source == PRIMARY_PRECIP
                    and direction == "lag"
                    and half_life == CONFIRMATORY_HALF_LIFE_DAYS
                ):
                    confirmatory_frame = scan_frame
                    confirmatory_col = api_col
    scan = pd.DataFrame(scan_rows)
    scan.to_csv(RESULTS_DIR / "timescale_scan.csv", index=False)

    confirmatory = scan.loc[
        (scan["source"] == PRIMARY_PRECIP)
        & (scan["direction"] == "lag")
        & (scan["half_life_days"] == CONFIRMATORY_HALF_LIFE_DAYS)
    ].iloc[0]
    placebo = scan.loc[
        (scan["source"] == PRIMARY_PRECIP)
        & (scan["direction"] == "lead")
        & (scan["half_life_days"] == CONFIRMATORY_HALF_LIFE_DAYS)
    ].iloc[0]

    blocks = per_block_fits(confirmatory_frame, confirmatory_col)
    blocks.to_csv(RESULTS_DIR / "per_block.csv", index=False)
    bootstrap = moving_block_bootstrap(
        confirmatory_frame,
        confirmatory_col,
        replicates=args.bootstrap_replicates,
    )

    bins = pd.concat(
        [
            lag_bin_fits(daily, f"{PRIMARY_PRECIP}_mm", "precip", "sum"),
            lag_bin_fits(daily, "discharge_m3s", "discharge", "mean")
            if "discharge_m3s" in daily.columns
            else pd.DataFrame(),
        ],
        ignore_index=True,
    )
    bins.to_csv(RESULTS_DIR / "lag_bins.csv", index=False)

    criteria, peak = evaluate_decision(scan, confirmatory, bootstrap, blocks, placebo)
    supported = all(criteria.values())

    write_scan_plot(scan)

    lines = [
        "Distributed-Lag Antecedent-Wetness Test",
        "",
        f"Daily frame: {int(daily['residual_ppm'].notna().sum())} usable days "
        f"across {daily['block_id'].nunique()} blocks",
        f"Primary precip source: {PRIMARY_PRECIP}; controls: {', '.join(CONTROL_COLS)}; "
        "block fixed effects included",
        "",
        f"Scan peak: half-life {peak['half_life_days']} d, "
        f"coef {peak['coef_ppm_per_mm_day']:.3f} ppm/(mm/day), t={peak['t']:.2f}",
        f"Confirmatory (half-life {CONFIRMATORY_HALF_LIFE_DAYS} d, pre-stated): "
        f"coef {confirmatory['coef_ppm_per_mm_day']:.3f}, HAC p={confirmatory['p']:.4f}, "
        f"n={int(confirmatory['n_days'])} days",
        f"Moving-block bootstrap 95% CI: [{bootstrap['ci_low']:.3f}, {bootstrap['ci_high']:.3f}] "
        f"({bootstrap['n_replicates']} replicates)",
        f"Placebo (future precip, 10 d): coef {placebo['coef_ppm_per_mm_day']:.3f}, "
        f"t={placebo['t']:.2f}",
        "",
        "Per-block confirmatory fits:",
        blocks.to_string(index=False),
        "",
        "Decision rule: " + DECISION_RULE,
        "",
        "Criteria:",
        *[f"  {name}: {'PASS' if passed else 'FAIL'}" for name, passed in criteria.items()],
        "",
        f"OUTCOME: {'SUPPORTED' if supported else 'NOT SUPPORTED'} — "
        + (
            "the residual carries a multi-week antecedent-wetness component."
            if supported
            else "the multi-week antecedent-wetness claim is not established on the current record."
        ),
    ]
    (RESULTS_DIR / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {RESULTS_DIR / 'timescale_scan.csv'} ({len(scan)} rows)")
    print(f"wrote {RESULTS_DIR / 'per_block.csv'}")
    print(f"wrote {RESULTS_DIR / 'lag_bins.csv'}")
    print(f"wrote {RESULTS_DIR / 'summary.txt'}")
    print(f"OUTCOME: {'SUPPORTED' if supported else 'NOT SUPPORTED'}")
    for name, passed in criteria.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()
