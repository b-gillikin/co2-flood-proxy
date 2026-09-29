"""First real-data Limburg case-crossover analysis; no manuscript prose.

Run after `46_review_events.py`. The runner uses the existing event definitions
and validated conditional-Poisson estimator, writes each specification as it
finishes, and keeps every attempted bootstrap draw (including failures).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy import optimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.case_crossover import (  # noqa: E402
    cross_basis,
    cumulative_log_rr,
    fit_problem,
    lag_basis,
    lag_curve,
    median_association_lag,
    natural_spline_basis,
    percentile_interval,
    prepare_problem,
    primary_estimand,
    seasonal_design,
)
from src.event_study import (  # noqa: E402
    assign_eras,
    at_risk_hours,
    episode_table,
    era_thresholds,
    rating_domain_admissible,
    stratum_labels,
)

spec = spec_from_file_location("review_events", ROOT / "scripts/46_review_events.py")
review_module = module_from_spec(spec)
spec.loader.exec_module(review_module)

OUT = ROOT / "results/event_study/real_data_v1"
FILES = {
    "discharge": ROOT / "data/interim/event_study_discharge_hourly.csv",
    "rainfall": ROOT / "data/interim/radolan_catchment_hourly.csv",
    "weather": ROOT / "data/interim/event_study_weather_hourly.csv",
    "gauges": ROOT / "data/interim/event_study_gauges.csv",
    "rating_eras": ROOT / "data/interim/event_study_rating_eras.csv",
    "literal_rating_eras": ROOT / "data/interim/event_study_rating_eras_literal.csv",
    "review": OUT / "events.csv",
}
SEED = 20260929


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_weather(path, watercourses, index):
    data = pd.read_csv(path)
    data.timestamp_utc = pd.to_datetime(data.timestamp_utc, utc=True)
    data = data.loc[data.watercourse.isin(watercourses) & data.timestamp_utc.isin(index)]
    by_site = {}
    for site, group in data.groupby("watercourse"):
        by_site[site] = group.set_index("timestamp_utc").reindex(index)[
            ["relative_humidity_pct", "pressure_change_6h_hpa"]
        ]
    return by_site


def make_rows(discharge, rain, gauges, rating_table, review, max_lag=72, df=4, weather=None):
    """Define outcomes independently, then attach complete exposure histories."""
    index = discharge.index.intersection(rain.index)
    if not index.to_series().diff().iloc[1:].eq(pd.Timedelta(hours=1)).all():
        raise ValueError("discharge/rainfall joint index is not hourly")
    basis = lag_basis(max_lag, df)
    all_rows, cross_rain, cross_weather = [], [], []
    for gauge in gauges.itertuples(index=False):
        series = discharge.loc[index, gauge.gauge]
        era_table = rating_table.loc[rating_table.gauge.eq(gauge.gauge)]
        eras = assign_eras(index, era_table)
        _, threshold = era_thresholds(series, eras)
        admissible = rating_domain_admissible(series, eras, era_table, threshold)
        risk = at_risk_hours(series, threshold, admissible, eras)
        observed_onsets = pd.DatetimeIndex(
            episode_table(series, threshold, 72, admissible, eras)
            .query("not onset_censored")
            .onset_utc
        )
        if not pd.DatetimeIndex(index[risk.onset]).equals(observed_onsets):
            raise AssertionError(f"episode/onset mismatch for {gauge.gauge}")
        rain_values = rain.loc[index, gauge.watercourse].to_numpy()
        rain_cross = cross_basis(rain_values, basis)
        if weather is not None:
            met = weather[gauge.watercourse]
            rh = cross_basis(met.relative_humidity_pct.to_numpy() / 10.0, basis)
            pressure = cross_basis(met.pressure_change_6h_hpa.to_numpy(), basis)
            met_cross = np.hstack([rh, pressure])
        else:
            met_cross = np.empty((len(index), 0))
        selected = risk.at_risk.to_numpy()
        times = index[selected]
        rows = pd.DataFrame(
            {
                "timestamp_utc": times,
                "gauge": gauge.gauge,
                "watercourse": gauge.watercourse,
                "onset": risk.onset.to_numpy()[selected].astype(int),
                "warm": times.month.isin(range(5, 11)),
                "period_late": times.year >= 2018,
                "stratum": stratum_labels(times, gauge.watercourse).to_numpy(),
                "block": times.year * 100 + times.month,
                "complete_rain": np.isfinite(rain_cross[selected]).all(axis=1),
                "complete_weather": np.isfinite(met_cross[selected]).all(axis=1),
            }
        )
        rows["measurement_concern"] = False
        if review is not None:
            concerned = pd.DatetimeIndex(
                pd.to_datetime(
                    review.loc[
                        review.gauge.eq(gauge.gauge) & review.measurement_concern, "onset_utc"
                    ],
                    utc=True,
                )
            )
            rows.loc[rows.timestamp_utc.isin(concerned), "measurement_concern"] = True
        all_rows.append(rows)
        cross_rain.append(rain_cross[selected])
        cross_weather.append(met_cross[selected])
    frame = pd.concat(all_rows, ignore_index=True)
    x_rain = np.vstack(cross_rain)
    x_weather = np.vstack(cross_weather)
    if frame.onset.sum() != (
        review.review_decision.eq("include_exact").sum()
        if review is not None
        else frame.onset.sum()
    ):
        raise AssertionError("reviewed and reconstructed onsets differ")
    return frame, x_rain, x_weather, basis


def fit_draws(name, design, rows, summary, replicates, global_blocks, seed=SEED):
    """Fit once and resample year-month blocks; preserve failed draw records."""
    eligible = np.isfinite(design).all(axis=1)
    subset = rows.loc[eligible].reset_index(drop=True)
    if not subset.onset.any():
        raise ValueError(f"{name}: no complete onsets")
    problem = prepare_problem(
        design[eligible],
        subset.onset.to_numpy(),
        subset.stratum.to_numpy(),
        subset.block.to_numpy(),
    )
    # Every watercourse must receive the *same* year-month resampling draw.
    # Its locally observed blocks may be a proper subset of the regional grid.
    local_labels = pd.factorize(subset.block.to_numpy())[1]
    global_index = {int(block): position for position, block in enumerate(global_blocks)}
    local_to_global = np.array([global_index[int(block)] for block in local_labels])
    fit = fit_problem(problem)
    pd.DataFrame([fit["coef"]], columns=[f"coef_{i}" for i in range(len(fit["coef"]))]).to_csv(
        OUT / f"point_coefficients_{name}.csv", index=False
    )
    eta = problem["design"] @ fit["coef"]
    grouped_max = np.full(problem["n_strata"], -np.inf)
    np.maximum.at(grouped_max, problem["codes"], eta)
    exponent = np.exp(eta - grouped_max[problem["codes"]])
    probability = exponent / (problem["operator"] @ exponent)[problem["codes"]]
    case_probability = probability[problem["onset"] > 0]
    estimates = summary(fit["coef"])
    rng = np.random.default_rng(seed)
    draws, coefficients, failures = [], [], []
    for _ in range(replicates):
        sample = rng.integers(0, len(global_blocks), len(global_blocks))
        counts = np.bincount(sample, minlength=len(global_blocks))
        weights = counts[local_to_global[problem["stratum_block"]]].astype(float)
        try:
            draw_fit = fit_problem(problem, weights)
            item = summary(draw_fit["coef"])
            coefficients.append(draw_fit["coef"])
            failures.append("")
        except (np.linalg.LinAlgError, RuntimeError, ValueError, FloatingPointError) as error:
            item = {key: np.nan for key in estimates}
            coefficients.append(np.full_like(fit["coef"], np.nan))
            failures.append(f"{type(error).__name__}: {error}")
        draws.append(item)
    table = pd.DataFrame(draws)
    table.insert(0, "draw", np.arange(1, replicates + 1))
    table.insert(0, "model", name)
    table["failure"] = failures
    table.to_csv(OUT / f"bootstrap_{name}.csv", index=False)
    coeff = pd.DataFrame(coefficients, columns=[f"coef_{i}" for i in range(len(fit["coef"]))])
    coeff.insert(0, "draw", np.arange(1, replicates + 1))
    coeff.to_csv(OUT / f"bootstrap_coefficients_{name}.csv", index=False)
    status = {
        "model": name,
        "n_rows": fit["n_rows"],
        "n_onsets": fit["n_onsets"],
        "n_strata": fit["n_strata"],
        "n_blocks": problem["n_blocks"],
        "dispersion": fit["dispersion"],
        "bootstrap_attempted": replicates,
        "bootstrap_failed": sum(bool(value) for value in failures),
        "onset_probability_median": float(np.median(case_probability)),
        "onset_probability_minimum": float(np.min(case_probability)),
        "onsets_with_probability_below_0_0001": int((case_probability < 0.0001).sum()),
    }
    (OUT / f"fit_status_{name}.json").write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps(status), flush=True)
    return fit, table, coeff, status


def scalar_intervals(model, point, draws, max_lag=72):
    metrics = [key for key in point if not key.startswith("_")]
    ranges = {
        key: (-(max_lag - 1), max_lag - 1)
        if key.endswith("median_lag_difference")
        else (1.0, float(max_lag))
        for key in metrics
        if "median_lag" in key
    }
    intervals = percentile_interval(draws[metrics], ranges=ranges)
    return [
        {
            "model": model,
            "metric": key,
            "estimate": float(value) if pd.notna(value) else np.nan,
            "lower": intervals.loc[key, "lower"],
            "upper": intervals.loc[key, "upper"],
            "estimable_share": intervals.loc[key, "estimable_share"],
        }
        for key, value in point.items()
        if key in metrics
    ]


def curve_intervals(model, fit, coefficients, basis, slices):
    rows = []
    for label, columns in slices.items():
        point = lag_curve(fit["coef"][columns], basis)
        draws = coefficients.iloc[:, 1:].to_numpy()[:, columns] @ basis.T
        for lag, value in enumerate(point, start=1):
            sampled = draws[:, lag - 1]
            rows.append(
                {
                    "model": model,
                    "signal": label,
                    "lag_hour": lag,
                    "log_rr_per_unit": value,
                    "lower": np.nanquantile(sampled, 0.025)
                    if np.isfinite(sampled).any()
                    else np.nan,
                    "upper": np.nanquantile(sampled, 0.975)
                    if np.isfinite(sampled).any()
                    else np.nan,
                }
            )
    return rows


def log_summary(beta, basis, contrast, prefix="rain"):
    curve = lag_curve(beta, basis)
    return {
        f"{prefix}_cumulative_log_rr": cumulative_log_rr(beta, basis, contrast),
        f"{prefix}_median_lag": median_association_lag(curve),
    }


def save_tables(primary, secondary, watercourses, curves, diagnostics):
    pd.DataFrame(primary).to_csv(OUT / "primary_estimand.csv", index=False)
    pd.DataFrame(secondary).to_csv(OUT / "secondary_estimates.csv", index=False)
    pd.DataFrame(watercourses).to_csv(OUT / "watercourse_estimates.csv", index=False)
    pd.DataFrame(curves).to_csv(OUT / "crossbasis_estimates.csv", index=False)
    pd.DataFrame(diagnostics).to_csv(OUT / "analysis_counts.csv", index=False)


def meta_pool(site_rows, site_draws):
    """GLS pool with joint-block covariance; nonnegative scalar heterogeneity."""
    names = list(site_rows)
    values = np.array([site_rows[name] for name in names], dtype=float)
    paired = pd.DataFrame({name: site_draws[name] for name in names}).dropna()
    covariance = paired.cov().to_numpy()
    if len(paired) < 30 or not np.isfinite(covariance).all():
        raise ValueError("too few paired site draws for covariance-aware pooling")
    one = np.ones(len(names))

    def estimate(tau2):
        matrix = covariance + tau2 * np.eye(len(names))
        inverse_one = np.linalg.solve(matrix, one)
        weights = inverse_one / (one @ inverse_one)
        mean = weights @ values
        return mean, float(np.sqrt(1 / (one @ inverse_one))), weights, matrix

    fixed, fixed_se, _, _ = estimate(0.0)

    def restricted(tau2):
        mean, _, _, matrix = estimate(tau2)
        sign, determinant = np.linalg.slogdet(matrix)
        if sign <= 0:
            return np.inf
        quadratic = (values - mean) @ np.linalg.solve(matrix, values - mean)
        return float(determinant + np.log(one @ np.linalg.solve(matrix, one)) + quadratic)

    bound = max(float(np.max(np.diag(covariance)) * 100), 1e-8)
    solution = optimize.minimize_scalar(restricted, bounds=(0, bound), method="bounded")
    tau2 = float(solution.x) if solution.success else np.nan
    random_mean, random_se = estimate(tau2)[:2] if solution.success else (np.nan, np.nan)
    return {
        "n_sites": len(names),
        "n_paired_draws": len(paired),
        "fixed_log_rr": fixed,
        "fixed_se": fixed_se,
        "random_log_rr": random_mean,
        "random_se": random_se,
        "tau2": tau2,
        "random_fit_converged": bool(solution.success),
    }


def main(replicates):
    OUT.mkdir(parents=True, exist_ok=True)
    review = pd.read_csv(FILES["review"])
    review.onset_utc = pd.to_datetime(review.onset_utc, utc=True)
    discharge = review_module.read_hourly(FILES["discharge"])
    rain = review_module.read_hourly(FILES["rainfall"])
    gauges = pd.read_csv(FILES["gauges"])
    gauges = gauges.loc[gauges.include_primary & gauges.natural_tributary]
    eras = pd.read_csv(FILES["rating_eras"])
    common = discharge.index.intersection(rain.index)
    weather = load_weather(FILES["weather"], gauges.watercourse, common)
    frame, x, met, basis = make_rows(discharge, rain, gauges, eras, review, weather=weather)
    all_months = np.sort(frame.block.unique())
    frame.to_parquet(OUT / "at_risk_hours.parquet", index=False)
    flow = (
        frame.groupby(["watercourse", "warm"], observed=True)
        .agg(
            at_risk_hours=("onset", "size"),
            candidate_onsets=("onset", "sum"),
            complete_rain_hours=("complete_rain", "sum"),
            complete_weather_hours=("complete_weather", "sum"),
        )
        .reset_index()
    )
    complete_cases = frame.loc[
        frame.onset.eq(1),
        ["gauge", "timestamp_utc", "complete_rain", "complete_weather", "measurement_concern"],
    ].rename(columns={"timestamp_utc": "onset_utc"})
    event_status = review.merge(
        complete_cases, on=["gauge", "onset_utc"], how="left", validate="one_to_one"
    )
    event_status["primary_usable"] = event_status.review_decision.eq(
        "include_exact"
    ) & event_status.complete_rain.fillna(False)
    event_status.to_csv(OUT / "event_analysis_status.csv", index=False)
    storm_status = (
        event_status.groupby("storm_id")
        .agg(
            warm=("onset_utc", lambda x: x.min().month in range(5, 11)),
            candidate_events=("event_id", "size"),
            usable_events=("primary_usable", "sum"),
        )
        .reset_index()
    )
    storm_status.to_csv(OUT / "storm_analysis_status.csv", index=False)
    flow["usable_onsets"] = [
        int(
            frame.loc[
                frame.watercourse.eq(row.watercourse)
                & frame.warm.eq(row.warm)
                & frame.onset.eq(1)
                & frame.complete_rain
            ].shape[0]
        )
        for row in flow.itertuples(index=False)
    ]
    flow.to_csv(OUT / "sample_flow.csv", index=False)
    rainfall_positive = rain.loc[common, gauges.watercourse].stack().dropna()
    contrast = float(rainfall_positive[rainfall_positive > 0].quantile(0.95))
    n = basis.shape[1]
    primary, secondary, watercourses, curves, diagnostics = [], [], [], [], []

    def record(model, design, subset, summary, destination, slices):
        fit, draws, coef, status = fit_draws(model, design, subset, summary, replicates, all_months)
        point = summary(fit["coef"])
        destination.extend(scalar_intervals(model, point, draws))
        curves.extend(curve_intervals(model, fit, coef, basis, slices))
        diagnostics.append(status)
        save_tables(primary, secondary, watercourses, curves, diagnostics)
        return fit, draws, coef

    seasonal = seasonal_design(x, frame.warm.to_numpy())
    record(
        "primary",
        seasonal,
        frame,
        lambda beta: primary_estimand({"coef": beta}, basis, contrast),
        primary,
        {"warm_rain": slice(0, n), "cold_rain": slice(n, 2 * n)},
    )
    record(
        "S1_pooled_rain",
        x,
        frame,
        lambda beta: log_summary(beta, basis, contrast),
        secondary,
        {"rain": slice(0, n)},
    )
    record(
        "S2_atmospheric",
        np.hstack([x, met]),
        frame,
        lambda beta: {
            **log_summary(beta[:n], basis, contrast),
            **log_summary(beta[n : 2 * n], basis, 10.0, "rh_10pct_points"),
            **log_summary(beta[2 * n : 3 * n], basis, 1.0, "pressure_change_1hpa"),
        },
        secondary,
        {
            "rain": slice(0, n),
            "rh_per_10pct_points": slice(n, 2 * n),
            "pressure_change_per_1hpa": slice(2 * n, 3 * n),
        },
    )
    site_points, site_draws = {}, {}
    for site in gauges.watercourse:
        mask = frame.watercourse.eq(site).to_numpy()
        fit, draws, _ = record(
            f"S3_{site}",
            x[mask],
            frame.loc[mask].reset_index(drop=True),
            lambda beta: log_summary(beta, basis, contrast),
            watercourses,
            {"rain": slice(0, n)},
        )
        site_points[site] = log_summary(fit["coef"], basis, contrast)["rain_cumulative_log_rr"]
        site_draws[site] = draws.rain_cumulative_log_rr.to_numpy()
    period_design = seasonal_design(x, frame.period_late.to_numpy())
    record(
        "S4_period",
        period_design,
        frame,
        lambda beta: {
            "late_cumulative_log_rr": cumulative_log_rr(beta[:n], basis, contrast),
            "early_cumulative_log_rr": cumulative_log_rr(beta[n : 2 * n], basis, contrast),
            "late_minus_early_log_rr": cumulative_log_rr(
                beta[:n] - beta[n : 2 * n], basis, contrast
            ),
        },
        secondary,
        {"late_rain": slice(0, n), "early_rain": slice(n, 2 * n)},
    )

    # The review-based stress test deletes flagged event hours, never turning
    # them into controls. Other risk hours retain the original episode spacing.
    keep = ~((frame.onset.eq(1) & frame.measurement_concern).to_numpy())
    record(
        "measurement_concern_omitted",
        seasonal[keep],
        frame.loc[keep].reset_index(drop=True),
        lambda beta: primary_estimand({"coef": beta}, basis, contrast),
        secondary,
        {"warm_rain": slice(0, n), "cold_rain": slice(n, 2 * n)},
    )

    literal = pd.read_csv(FILES["literal_rating_eras"])
    literal_frame, literal_x, _, literal_basis = make_rows(discharge, rain, gauges, literal, None)
    if not np.allclose(literal_basis, basis):
        raise AssertionError("literal-era lag basis changed")
    record(
        "literal_rating_eras",
        seasonal_design(literal_x, literal_frame.warm),
        literal_frame,
        lambda beta: primary_estimand({"coef": beta}, basis, contrast),
        secondary,
        {"warm_rain": slice(0, n), "cold_rain": slice(n, 2 * n)},
    )

    long_frame, long_x, _, long_basis = make_rows(
        discharge, rain, gauges, eras, review, max_lag=168
    )
    long_design = seasonal_design(long_x, long_frame.warm)
    fit, draws, coeff = fit_draws(
        "lag168",
        long_design,
        long_frame,
        lambda beta: primary_estimand({"coef": beta}, long_basis, contrast),
        replicates,
        all_months,
    )[:3]
    secondary.extend(
        scalar_intervals("lag168", primary_estimand(fit, long_basis, contrast), draws, 168)
    )
    diagnostics.append(json.loads((OUT / "fit_status_lag168.json").read_text()))
    save_tables(primary, secondary, watercourses, curves, diagnostics)

    flexible_frame, flexible_x, _, flexible_basis = make_rows(
        discharge, rain, gauges, eras, review, df=6
    )
    flexible_design = seasonal_design(flexible_x, flexible_frame.warm)
    fit, draws, coeff = fit_draws(
        "lag_df6",
        flexible_design,
        flexible_frame,
        lambda beta: primary_estimand({"coef": beta}, flexible_basis, contrast),
        replicates,
        all_months,
    )[:3]
    secondary.extend(
        scalar_intervals("lag_df6", primary_estimand(fit, flexible_basis, contrast), draws)
    )
    diagnostics.append(json.loads((OUT / "fit_status_lag_df6.json").read_text()))
    save_tables(primary, secondary, watercourses, curves, diagnostics)

    if replicates >= 30:
        pool = meta_pool(site_points, site_draws)
        pd.DataFrame([pool]).to_csv(OUT / "two_stage_pooling.csv", index=False)
    # A centred natural spline with two exposure knots (3 independent columns).
    values = rainfall_positive[rainfall_positive > 0]
    knots = values.quantile([0.5, 0.9]).to_numpy()
    boundary = (0.0, float(rainfall_positive.max()))

    def exposure_basis(v):
        val = natural_spline_basis(np.asarray(v, dtype=float), knots, boundary)
        zero = natural_spline_basis(np.array([0.0]), knots, boundary)[0]
        return (val - zero)[:, 1:]

    shape_rows = []
    for gauge in gauges.itertuples(index=False):
        raw = rain.loc[common, gauge.watercourse].to_numpy()
        transformed = np.column_stack(
            [
                np.where(np.isfinite(raw), exposure_basis(np.nan_to_num(raw))[:, col], np.nan)
                for col in range(3)
            ]
        )
        cross = np.hstack([cross_basis(transformed[:, col], basis) for col in range(3)])
        shape_rows.append(cross)
    # Select at-risk rows by their timestamps, preserving the same row order.
    shape_design = np.vstack(
        [
            part[
                np.asarray(
                    common.isin(
                        pd.DatetimeIndex(frame.loc[frame.gauge.eq(g.gauge), "timestamp_utc"])
                    )
                )
            ]
            for part, g in zip(shape_rows, gauges.itertuples(index=False), strict=True)
        ]
    )
    if len(shape_design) != len(frame):
        raise AssertionError("nonlinear design misaligned")

    def shape_summary(beta):
        out = {}
        for amount in [float(values.quantile(0.5)), contrast]:
            exposure = exposure_basis([amount])[0]
            coefficients = beta.reshape(3, n)
            logrr = float(exposure @ coefficients @ basis.sum(axis=0))
            out[f"rain_{amount:.3f}mm_cumulative_log_rr"] = logrr
        return out

    fit, draws, coeff = fit_draws(
        "S1_rain_shape", shape_design, frame, shape_summary, replicates, all_months
    )[:3]
    secondary.extend(scalar_intervals("S1_rain_shape", shape_summary(fit["coef"]), draws))
    diagnostics.append(json.loads((OUT / "fit_status_S1_rain_shape.json").read_text()))
    save_tables(primary, secondary, watercourses, curves, diagnostics)

    bootstrap_files = sorted(OUT.glob("bootstrap_*.csv"))
    pd.concat([pd.read_csv(path) for path in bootstrap_files], ignore_index=True).to_csv(
        OUT / "bootstrap_draws.csv", index=False
    )
    manifest = {
        "analysis_version": "real_data_v1",
        "python_version": platform.python_version(),
        "package_versions": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "seed": SEED,
        "bootstrap_replicates": replicates,
        "rainfall_positive_p95_mm_per_hour": contrast,
        "input_sha256": {key: hash_file(path) for key, path in FILES.items()},
        "code_sha256": {
            path.name: hash_file(path)
            for path in [
                ROOT / "src/event_study.py",
                ROOT / "src/case_crossover.py",
                ROOT / "scripts/46_review_events.py",
                Path(__file__),
            ]
        },
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "fit_status": diagnostics,
    }
    (OUT / "analysis_run.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Analysis complete", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=999)
    args = parser.parse_args()
    main(args.replicates)
