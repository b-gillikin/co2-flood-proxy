"""Validate the case-crossover estimator on synthetic data (protocol §7, §12).

Synthetic data only: no discharge, rainfall or weather record is read.

1. Agreement: the Python estimator (`src/case_crossover.py`) must reproduce the
   R reference (`dlnm` + `gnm`, `scripts/R/case_crossover_reference.R`) on the
   same simulated datasets to numerical tolerance.
2. Recovery: across simulated datasets with a known seasonal lag structure,
   report bias and RMSE of the primary summaries.
3. Coverage: with the calendar year-month block bootstrap, report how often
   95% percentile intervals cover the truth, including two nulls: no
   association, and identical association in both seasons.
4. Stress: the same checks when onset hazards saturate (see SCENARIOS).

Example: python scripts/38_validate_estimator.py --datasets 200 --bootstrap 199
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.case_crossover import (
    MAX_LAG,
    block_bootstrap,
    cross_basis,
    fit_conditional_poisson,
    lag_basis,
    median_association_lag,
    percentile_interval,
    primary_estimand,
    seasonal_design,
)
from src.event_study import stratum_labels, warm_season

OUTPUT = ROOT / "results/estimator_validation"
LAGS = np.arange(1, MAX_LAG + 1)
YEARS = (2010, 2025)
N_WATERCOURSES = 6
STATISTICS = [
    "cumulative_log_rr_warm",
    "cumulative_log_rr_cold",
    "cumulative_log_rr_difference",
    "median_lag_warm",
    "median_lag_cold",
    "median_lag_difference",
]


def gamma_shape(shape, scale):
    curve = LAGS ** (shape - 1) * np.exp(-LAGS / scale)
    return curve / curve.sum()


# True log rate ratio per mm at each lag. Warm: concentrated within hours
# (convective, mode 3 h); cold: building over one to three days (frontal, mode
# 20 h). The first three scenarios keep hourly onset hazards rare (below 0.1 at
# about 99% of onsets), where the log-linear conditional Poisson model is the
# data-generating model; they test the implementation and the bootstrap. The
# stress scenario makes onsets strongly rain-driven, so hazards saturate
# (about half of onsets occur at hazards above 0.1). It measures how far the
# summaries drift when the rare-event approximation fails, a property of real
# high water that the protocol must acknowledge. Sizes and baselines were
# calibrated on simulated data only, to 40-70 onsets per watercourse in 16 years.
SCENARIOS = {
    "seasonal": {"warm": 1.2 * gamma_shape(2, 3), "cold": 3.0 * gamma_shape(3, 10)},
    "same_in_both_seasons": {"warm": 2.5 * gamma_shape(3, 10), "cold": 2.5 * gamma_shape(3, 10)},
    "no_association": {"warm": np.zeros(MAX_LAG), "cold": np.zeros(MAX_LAG)},
    "saturating_stress": {"warm": 4.0 * gamma_shape(2, 3), "cold": 14.0 * gamma_shape(3, 10)},
}
BASELINE = {
    "seasonal": -8.5,
    "same_in_both_seasons": -8.6,
    "no_association": -7.6,
    "saturating_stress": -12.0,
}


def simulate_rain(index, rng):
    """Hourly rainfall for all watercourses: shared frontal systems, patchy convection."""
    n = len(index)
    warm = warm_season(index).to_numpy()
    rain = np.zeros((n, N_WATERCOURSES))
    hour = 0
    while hour < n:
        rate = 1 / 96 if not warm[hour] else 1 / 240
        hour += int(rng.exponential(1 / rate))
        if hour >= n:
            break
        length = int(rng.integers(12, 49))
        span = slice(hour, min(n, hour + length))
        size = span.stop - span.start
        wet = rng.random(size) < 0.6
        amount = rng.gamma(1.5, 0.5 / 1.5, size) * wet
        rain[span] += amount[:, None] * rng.lognormal(0, 0.3, (size, N_WATERCOURSES))
    hour = 0
    while hour < n:
        hour += int(rng.exponential(72))
        if hour >= n:
            break
        if not warm[hour]:
            continue
        length = int(rng.integers(1, 5))
        span = slice(hour, min(n, hour + length))
        size = span.stop - span.start
        hit = rng.random(N_WATERCOURSES) < 0.5
        amount = rng.gamma(0.8, 4.0 / 0.8, (size, N_WATERCOURSES)) * hit
        rain[span] += amount
    return np.round(rain, 1)


def simulate(scenario, seed):
    """One synthetic cohort: hourly rain, observation gaps, at-risk hours and onsets."""
    rng = np.random.default_rng(seed)
    index = pd.date_range(f"{YEARS[0]}-01-01", f"{YEARS[1]}-12-31 23:00", freq="h", tz="UTC")
    n = len(index)
    warm = warm_season(index).to_numpy()
    rain = simulate_rain(index, rng)
    truth = SCENARIOS[scenario]
    frames = []
    for w in range(N_WATERCOURSES):
        lagged = np.zeros(n)
        for season, mask in (("warm", warm), ("cold", ~warm)):
            effect = np.convolve(rain[:, w], np.r_[0.0, truth[season]])[:n]
            lagged += np.where(mask, effect, 0.0)
        monthly = 0.3 * np.cos(2 * np.pi * (index.month.to_numpy() - 1) / 12)
        hazard = np.exp(BASELINE[scenario] + 0.2 * rng.normal() + monthly + lagged)
        candidate = rng.random(n) < -np.expm1(-hazard)
        observed = np.ones(n, dtype=bool)
        starts = np.flatnonzero(rng.random(n) < 0.0005)
        for start in starts:
            observed[start : start + int(rng.integers(1, 49))] = False
        eligible = observed & np.r_[False, observed[:-1]]
        # A crossing, observed or not, blocks the next 72 hours (the merge rule).
        accepted, blocked_until = [], -1
        for t in np.flatnonzero(candidate):
            if t > blocked_until:
                accepted.append(t)
                blocked_until = t + MAX_LAG
        blocked = np.zeros(n + MAX_LAG + 1, dtype=int)
        np.add.at(blocked, np.asarray(accepted, dtype=int) + 1, 1)
        np.add.at(blocked, np.asarray(accepted, dtype=int) + MAX_LAG + 1, -1)
        at_risk = eligible & (np.cumsum(blocked)[:n] == 0)
        onset = np.zeros(n, dtype=bool)
        onset[accepted] = at_risk[accepted]
        rain_w = rain[:, w].copy()
        gaps = rng.random(n) < 0.002
        rain_w[gaps] = np.nan
        frames.append(
            pd.DataFrame(
                {
                    "watercourse": f"W{w}",
                    "hour": np.arange(n),
                    "timestamp_utc": index,
                    "rain": rain_w,
                    "warm": warm.astype(int),
                    "onset": onset.astype(int),
                    "at_risk": at_risk.astype(int),
                    "stratum": stratum_labels(index, f"W{w}").to_numpy(),
                    "block": (index.year * 100 + index.month).to_numpy(),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def contrast_of(data):
    """Pooled 95th percentile of positive hourly rainfall (protocol §7)."""
    rain = data.rain.dropna()
    return float(rain[rain > 0].quantile(0.95))


def true_estimand(scenario, contrast):
    truth = SCENARIOS[scenario]
    result = {
        "cumulative_log_rr_warm": contrast * truth["warm"].sum(),
        "cumulative_log_rr_cold": contrast * truth["cold"].sum(),
        "median_lag_warm": median_association_lag(truth["warm"]),
        "median_lag_cold": median_association_lag(truth["cold"]),
    }
    result["cumulative_log_rr_difference"] = (
        result["cumulative_log_rr_warm"] - result["cumulative_log_rr_cold"]
    )
    result["median_lag_difference"] = result["median_lag_warm"] - result["median_lag_cold"]
    return result


def analysis_rows(data, basis):
    """Cross-basis per watercourse on the full series, then the at-risk rows."""
    parts = []
    for _, group in data.groupby("watercourse", sort=True):
        cross = cross_basis(group.rain.to_numpy(), basis)
        design = seasonal_design(cross, group.warm.to_numpy())
        risk = group.at_risk.to_numpy() == 1
        parts.append((design[risk], group.loc[risk, ["onset", "stratum", "block"]]))
    design = np.vstack([part[0] for part in parts])
    rows = pd.concat([part[1] for part in parts], ignore_index=True)
    return design, rows


def python_fit(data, basis, contrast):
    design, rows = analysis_rows(data, basis)
    fit = fit_conditional_poisson(design, rows.onset, rows.stratum)
    return fit, design, rows, primary_estimand(fit, basis, contrast)


def r_reference(data, contrast):
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "input.csv"
        target = Path(folder) / "output.csv"
        data[["watercourse", "hour", "rain", "warm", "onset", "at_risk", "stratum"]].to_csv(
            source, index=False, na_rep="NA"
        )
        subprocess.run(
            [
                "Rscript",
                str(ROOT / "scripts/R/case_crossover_reference.R"),
                str(source),
                str(target),
                repr(contrast),
            ],
            check=True,
            capture_output=True,
        )
        return pd.read_csv(target)


def agreement(scenario, seed, basis):
    data = simulate(scenario, seed)
    contrast = contrast_of(data)
    fit, _, _, estimate = python_fit(data, basis, contrast)
    reference = r_reference(data, contrast)
    n = basis.shape[1]
    rows = []
    for season, coefficients in (("warm", fit["coef"][:n]), ("cold", fit["coef"][n:])):
        r = reference[reference.season.eq(season)].sort_values("lag")
        python_curve = basis @ coefficients
        rows.append(
            {
                "scenario": scenario,
                "seed": seed,
                "season": season,
                "n_rows_python": fit["n_rows"],
                "n_rows_r": int(r.n_rows.iloc[0]),
                "n_onsets": fit["n_onsets"],
                "max_abs_curve_difference": float(
                    np.abs(python_curve - r.log_rr_per_unit.to_numpy()).max()
                ),
                "cumulative_python": estimate[f"cumulative_log_rr_{season}"],
                "cumulative_r": float(r.cumulative_log_rr.iloc[0]),
                "median_lag_python": estimate[f"median_lag_{season}"],
                "median_lag_r": float(r.median_lag.iloc[0]),
                "dispersion_python": fit["dispersion"],
                "dispersion_r": float(r.dispersion.iloc[0]),
            }
        )
    return rows


def one_dataset(task):
    scenario, seed, replicates = task
    basis = lag_basis()
    data = simulate(scenario, seed)
    contrast = contrast_of(data)
    fit, design, rows, estimate = python_fit(data, basis, contrast)
    truth = true_estimand(scenario, contrast)
    draws = block_bootstrap(
        design,
        rows.onset,
        rows.stratum,
        rows.block,
        lambda f: primary_estimand(f, basis, contrast),
        replicates=replicates,
        seed=seed + 1,
    )
    interval = percentile_interval(draws[STATISTICS])
    out = []
    for statistic in STATISTICS:
        lower, upper = interval.loc[statistic, ["lower", "upper"]]
        out.append(
            {
                "scenario": scenario,
                "seed": seed,
                "statistic": statistic,
                "truth": truth[statistic],
                "estimate": estimate[statistic],
                "lower": lower,
                "upper": upper,
                "estimable_share": interval.loc[statistic, "estimable_share"],
                "covered": bool(lower <= truth[statistic] <= upper)
                if np.isfinite([lower, upper, truth[statistic]]).all()
                else np.nan,
                "n_onsets": fit["n_onsets"],
                "n_strata": fit["n_strata"],
                "contrast_mm": contrast,
            }
        )
    return out


def summarise(replicates):
    rows = []
    for (scenario, statistic), group in replicates.groupby(["scenario", "statistic"], sort=False):
        estimable = group.dropna(subset=["estimate"])
        covered = group.covered.dropna().astype(float)
        error = estimable.estimate - estimable.truth
        rows.append(
            {
                "scenario": scenario,
                "statistic": statistic,
                "truth": group.truth.iloc[0],
                "datasets": len(group),
                "estimable_share": len(estimable) / len(group),
                "mean_estimate": estimable.estimate.mean(),
                "bias": error.mean(),
                "rmse": float(np.sqrt((error**2).mean())),
                "coverage": covered.mean() if len(covered) else np.nan,
                "coverage_mcse": float(
                    np.sqrt(covered.mean() * (1 - covered.mean()) / len(covered))
                )
                if len(covered)
                else np.nan,
                "median_interval_width": (group.upper - group.lower).median(),
                "mean_onsets": group.n_onsets.mean(),
            }
        )
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--datasets", type=int, default=200)
    parser.add_argument("--bootstrap", type=int, default=199)
    parser.add_argument("--agreement-datasets", type=int, default=2)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260918)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    basis = lag_basis()

    agreement_rows = []
    for scenario in SCENARIOS:
        for k in range(args.agreement_datasets):
            agreement_rows.extend(agreement(scenario, args.seed + 1000 * k, basis))
    agreement_table = pd.DataFrame(agreement_rows)
    agreement_table.to_csv(OUTPUT / "r_agreement.csv", index=False)
    print(agreement_table.to_string(index=False), flush=True)

    tasks = [
        (scenario, args.seed + 10_000 + 7 * k, args.bootstrap)
        for scenario in SCENARIOS
        for k in range(args.datasets)
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = [row for chunk in pool.map(one_dataset, tasks, chunksize=4) for row in chunk]
    replicates = pd.DataFrame(results)
    replicates.to_csv(OUTPUT / "replicates.csv", index=False)
    summary = summarise(replicates)
    summary.to_csv(OUTPUT / "summary.csv", index=False)
    print(summary.round(4).to_string(index=False))

    manifest = {
        "status": "synthetic_validation_not_empirical_evidence",
        "seed": args.seed,
        "datasets_per_scenario": args.datasets,
        "bootstrap_replicates": args.bootstrap,
        "watercourses": N_WATERCOURSES,
        "years": list(YEARS),
        "max_abs_curve_difference_vs_r": float(agreement_table.max_abs_curve_difference.max()),
        "max_abs_cumulative_difference_vs_r": float(
            (agreement_table.cumulative_python - agreement_table.cumulative_r).abs().max()
        ),
        "median_lags_identical": bool(
            (
                agreement_table.median_lag_python.fillna(-1)
                == agreement_table.median_lag_r.fillna(-1)
            ).all()
        ),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
