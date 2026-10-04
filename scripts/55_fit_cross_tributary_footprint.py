"""Event-level working-mean analysis of Dutch six-site high-water footprint.

This is descriptive conditional analysis. The six gauges are not independent
binomial trials; uncertainty resamples whole calendar years of rain episodes.
"""

from __future__ import annotations

import hashlib
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_script("53_cross_tributary_rain_episodes")
OUT = core.OUT
N_SITES = len(core.SITES)
TERMS = ("intercept", "rain_sites_10mm", "log2_peak_rain_10mm", "preflow_per_0p1", "warm")
DURATION_TERMS = (*TERMS, "log2_duration_24h")


def design(frame, include_duration=False):
    columns = [
        np.ones(len(frame)),
        frame.n_sites_rain_10mm.to_numpy(dtype=float),
        np.log2(frame.peak_site_24h_mm.to_numpy(dtype=float) / 10),
        frame.median_pre_rain_q_over_p99.to_numpy(dtype=float) / 0.1,
        frame.rain_month.isin(range(5, 11)).to_numpy(dtype=float),
    ]
    if include_duration:
        columns.append(np.log2(frame.duration_hours.to_numpy(dtype=float) / 24))
    return np.column_stack(columns)


def fit_working_binomial(x, y, max_iterations=50):
    """Fit a bounded count mean; do not use its naive binomial standard errors."""
    if len(y) < 20 or np.linalg.matrix_rank(x) != x.shape[1]:
        raise ValueError("Insufficient or rank-deficient event design")
    coefficients = np.zeros(x.shape[1])
    for iteration in range(max_iterations):
        probability = expit(x @ coefficients)
        weight = N_SITES * probability * (1 - probability)
        score = x.T @ (y - N_SITES * probability)
        change = np.linalg.solve(x.T @ (weight[:, None] * x), score)
        coefficients += change
        if np.max(np.abs(change)) < 1e-8:
            return coefficients, iteration + 1
    raise RuntimeError("Working-binomial mean fit did not converge")


def eligible_frame(per, sites, require_full_coverage=False):
    ready = (
        per.n_sites_low_coverage.eq(0)
        & per.n_sites_incomplete_rain.eq(0)
        & per.n_sites_missing_pre_rain.eq(0)
        & per.n_sites_preexisting.eq(0)
    )
    if require_full_coverage:
        complete = sites.groupby("episode_id").valid_hour_fraction.min().eq(1)
        ready &= per.episode_id.map(complete).fillna(False)
    return per.loc[ready].copy()


def summarize_fit(name, frame, bootstrap_draws=999, seed=20261003, include_duration=False):
    if frame.empty:
        raise ValueError(f"{name}: no eligible episodes")
    x = design(frame, include_duration)
    terms = DURATION_TERMS if include_duration else TERMS
    y = frame.model_n_high.to_numpy(dtype=float)
    beta, iterations = fit_working_binomial(x, y)
    fitted = N_SITES * expit(x @ beta)
    years = np.sort(frame.rain_year.unique())
    year_indices = {year: np.flatnonzero(frame.rain_year.eq(year).to_numpy()) for year in years}
    rng = np.random.default_rng(seed)
    records = []
    for draw in range(bootstrap_draws + 1):
        if draw == 0:
            coefficients, n_iter, failure = beta, iterations, ""
        else:
            chosen = rng.choice(years, size=len(years), replace=True)
            positions = np.concatenate([year_indices[year] for year in chosen])
            try:
                coefficients, n_iter = fit_working_binomial(x[positions], y[positions])
                failure = ""
            except (ValueError, RuntimeError, np.linalg.LinAlgError) as error:
                coefficients = np.full(x.shape[1], np.nan)
                n_iter = 0
                failure = f"{type(error).__name__}: {error}"
        records.append(
            {
                "specification": name,
                "draw": draw,
                **dict(zip(terms, coefficients, strict=True)),
                "iterations": n_iter,
                "failure": failure,
            }
        )
    draws = pd.DataFrame(records)
    clean = draws.loc[draws.draw.gt(0) & draws.failure.eq("")]
    summary = {
        "specification": name,
        "n_episodes": len(frame),
        "n_years": len(years),
        "n_zero_high": int((y == 0).sum()),
        "n_all_six_high": int((y == N_SITES).sum()),
        "mean_high_sites": float(y.mean()),
        "mean_absolute_error_sites": float(np.abs(y - fitted).mean()),
        "bootstrap_attempted": bootstrap_draws,
        "bootstrap_failed": int(draws.loc[draws.draw.gt(0)].failure.ne("").sum()),
    }
    for term in terms:
        summary[f"{term}_estimate"] = float(draws.loc[0, term])
        summary[f"{term}_low"] = float(clean[term].quantile(0.025))
        summary[f"{term}_high"] = float(clean[term].quantile(0.975))
    predictions = frame[["episode_id", "rain_year", "model_n_high"]].copy()
    predictions["fitted_high_sites"] = fitted
    return summary, draws, predictions


def standardized_contrasts(frame, draws):
    """Model-standardized differences over observed event covariates."""
    x = design(frame)
    settings = [
        (
            "rain_sites_iqr",
            1,
            float(frame.n_sites_rain_10mm.quantile(0.25)),
            float(frame.n_sites_rain_10mm.quantile(0.75)),
        ),
        (
            "peak_rain_iqr",
            2,
            float(np.log2(frame.peak_site_24h_mm.quantile(0.25) / 10)),
            float(np.log2(frame.peak_site_24h_mm.quantile(0.75) / 10)),
        ),
        (
            "pre_rain_flow_iqr",
            3,
            float(frame.median_pre_rain_q_over_p99.quantile(0.25) / 0.1),
            float(frame.median_pre_rain_q_over_p99.quantile(0.75) / 0.1),
        ),
        ("warm_vs_cold", 4, 0.0, 1.0),
    ]
    records = []
    for row in draws.itertuples(index=False):
        if row.failure:
            continue
        beta = np.array([getattr(row, term) for term in TERMS])
        for label, column, lower, upper in settings:
            low, high = x.copy(), x.copy()
            low[:, column], high[:, column] = lower, upper
            records.append(
                {
                    "draw": row.draw,
                    "contrast": label,
                    "lower_value": lower,
                    "upper_value": upper,
                    "difference_expected_high_sites": float(
                        np.mean(N_SITES * expit(high @ beta) - N_SITES * expit(low @ beta))
                    ),
                }
            )
    return pd.DataFrame(records)


def leave_one_year_out(frame):
    x = design(frame)
    y = frame.model_n_high.to_numpy(dtype=float)
    records = []
    for year in sorted(frame.rain_year.unique()):
        use = ~frame.rain_year.eq(year).to_numpy()
        beta, iterations = fit_working_binomial(x[use], y[use])
        records.append(
            {
                "omitted_year": int(year),
                "n_episodes": int(use.sum()),
                **dict(zip(TERMS, beta, strict=True)),
                "iterations": iterations,
            }
        )
    return pd.DataFrame(records)


def calibration_bins(predictions):
    table = predictions.copy()
    table["fitted_bin"] = pd.qcut(table.fitted_high_sites, 8, duplicates="drop")
    grouped = table.groupby("fitted_bin", observed=True).agg(
        n_episodes=("episode_id", "size"),
        mean_fitted_high_sites=("fitted_high_sites", "mean"),
        mean_observed_high_sites=("model_n_high", "mean"),
    )
    return grouped.reset_index().astype({"fitted_bin": str})


def attach_diagnostic_flags(per, sites):
    domain = sites.groupby("episode_id").any_high_outside_rating_domain.any()
    gulp = sites.groupby("episode_id").any_high_above_gulp_calibration.any()
    sustained = sites.groupby("episode_id").longest_high_run_hours.agg(
        lambda x: int((x >= 3).sum())
    )
    result = per.copy()
    result["any_high_outside_rating_domain"] = result.episode_id.map(domain)
    result["any_high_above_gulp_calibration"] = result.episode_id.map(gulp)
    result["n_sites_sustained_3h"] = result.episode_id.map(sustained)
    return result


def load_inputs():
    rain = core.read_hourly(core.DATA / "radolan_catchment_hourly.csv")[list(core.SITES)]
    discharge = core.read_hourly(core.DATA / "event_study_discharge_hourly.csv")
    rain = rain.loc[rain.index.intersection(discharge.index)]
    ratings = pd.read_csv(core.DATA / "event_study_rating_eras.csv")
    review = pd.read_csv(core.REVIEW)
    return rain, core.site_states(discharge, ratings), review


def build_variant(rain, states, review, gap, cutoff, response_hours=24):
    episodes = core.rain_episodes(rain, gap, cutoff, response_hours)
    sites = core.footprint(episodes, review, states, rain)
    per = attach_diagnostic_flags(core.summarize(episodes, sites), sites)
    return per, sites


def main():
    rain, states, review = load_inputs()
    results = []
    primary, primary_sites = build_variant(rain, states, review, 12, 10.0)
    saved = pd.read_csv(OUT / "episode_footprints.csv")
    if not primary.episode_id.equals(saved.episode_id) or not primary.n_sites_high.equals(
        saved.n_sites_high
    ):
        raise AssertionError("Model input does not reproduce the descriptive run")
    variants = {
        "main_12h_10mm": (primary, primary_sites),
        "gap12_5mm": build_variant(rain, states, review, 12, 5.0),
        "gap12_20mm": build_variant(rain, states, review, 12, 20.0),
        "gap24_10mm": build_variant(rain, states, review, 24, 10.0),
        "response12_12h_10mm": build_variant(rain, states, review, 12, 10.0, 12),
        "response48_12h_10mm": build_variant(rain, states, review, 12, 10.0, 48),
    }
    for name, (per, sites) in variants.items():
        base = eligible_frame(per, sites)
        specific = [(name, base.assign(model_n_high=base.n_sites_high))]
        if name == "main_12h_10mm":
            full = eligible_frame(per, sites, require_full_coverage=True)
            strict = base.loc[
                ~base.any_measurement_concern
                & ~base.any_high_outside_rating_domain
                & ~base.any_high_above_gulp_calibration
            ]
            specific.extend(
                [
                    ("main_duration_adjusted", base.assign(model_n_high=base.n_sites_high)),
                    ("main_full_coverage", full.assign(model_n_high=full.n_sites_high)),
                    (
                        "main_under_72h",
                        base.loc[base.duration_hours.lt(72)].assign(
                            model_n_high=lambda x: x.n_sites_high
                        ),
                    ),
                    (
                        "main_under_48h",
                        base.loc[base.duration_hours.lt(48)].assign(
                            model_n_high=lambda x: x.n_sites_high
                        ),
                    ),
                    ("main_no_measurement_flags", strict.assign(model_n_high=strict.n_sites_high)),
                    ("main_sustained_3h", base.assign(model_n_high=base.n_sites_sustained_3h)),
                    (
                        "main_without_july_2021",
                        base.loc[~(base.rain_year.eq(2021) & base.rain_month.eq(7))].assign(
                            model_n_high=lambda x: x.n_sites_high
                        ),
                    ),
                ]
            )
        for label, frame in specific:
            summary, draws, predictions = summarize_fit(
                label, frame, include_duration=label == "main_duration_adjusted"
            )
            results.append(summary)
            draws.to_csv(OUT / f"model_draws_{label}.csv", index=False)
            if label == "main_12h_10mm":
                predictions.to_csv(OUT / "model_primary_predictions.csv", index=False)
                frame.to_csv(OUT / "model_primary_events.csv", index=False)
                standardized_contrasts(frame, draws).to_csv(
                    OUT / "model_primary_standardized_contrasts.csv", index=False
                )
                leave_one_year_out(frame).to_csv(
                    OUT / "model_primary_year_omission.csv", index=False
                )
                calibration_bins(predictions).to_csv(
                    OUT / "model_primary_calibration.csv", index=False
                )
    pd.DataFrame(results).to_csv(OUT / "model_sensitivity.csv", index=False)
    manifest = {
        "status": "exploratory conditional mean, no causal or forecast interpretation",
        "outcome": "0–6 sites with observed discharge > era-specific p99",
        "working_likelihood": "binomial mean; sites are dependent; naive binomial SE not used",
        "uncertainty": "999 bootstrap resamples of whole calendar years, fixed seed 20261003",
        "covariates": list(TERMS),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "parent_manifest": str(OUT / "manifest.json"),
    }
    (OUT / "model_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
