"""Review seasonality in the completed local discharge-reconstruction census."""

import argparse
import calendar as cal
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dise_corrected import population, score, weights
from src.dise_repeatability import balanced_resamples, gauge_resamples, joint_multiplicities
from src.geoglows_experiment import sha, write_json

BASE = ROOT / "results/limburg_representation_extension_v1/c2_alphaearth_2017_v1"
PREDICTIONS = BASE / "paired_predictions.parquet"
REVIEW = BASE / "completion_review.json"
C2_REVIEW = BASE.parent / "c2_multiyear_v1/completion_review.json"
HISTORY = BASE / "preparation/features.parquet"
PREPARATION = HISTORY.with_name("audit.json")
MEMBERSHIP = ROOT / "results/limburg_dise_repeatability_v1/episode_membership.csv"
SETTINGS = ROOT / "config/limburg_dise_repeatability_v1.json"
OUTPUT = ROOT / "results/limburg_dise_seasonality_v1"
POLICIES = ("native_rmse", "article_faithful")
ARMS = ("C2", "C2+AlphaEarth", "C2+TESSERA", "C2+AlphaEarth2017")
MODEL_COLUMNS = [f"{policy}__{arm}" for policy in POLICIES for arm in ARMS]
DEFINITION = "November–April and May–October (Tsiokanos et al. 2024, section 2.3.1)"


def half_year(days):
    return np.where(days.dt.month.isin([11, 12, 1, 2, 3, 4]), "cool", "warm")


def read_inputs():
    review = json.loads(REVIEW.read_text())
    if review["status"] != "completed" or sha(PREDICTIONS) != review["paired_predictions_sha256"]:
        raise ValueError("Saved predictions differ from their completion receipt")
    if sha(HISTORY) != json.loads(PREPARATION.read_text())["features"]:
        raise ValueError("Saved reference observations differ from their receipt")
    fields = ["day", "gauge", "station", "river_group", "q_observed", "clean_verification"]
    local = [("source_role", "==", "local")]
    history = pd.read_parquet(HISTORY, columns=fields, filters=local)
    predictions = pd.read_parquet(
        PREDICTIONS,
        columns=fields
        + ["p99_reference", "high_water", "test_year", "regime", "q_model", *MODEL_COLUMNS],
        filters=local,
    ).sort_values(["regime", "gauge", "day"], ignore_index=True)
    census = predictions.groupby("regime").size().to_dict()
    expected = {
        row["dataset"].removeprefix("local_"): row["rows"]
        for row in review["point_estimates"]
        if row["dataset"].startswith("local_")
        and row["scope"] == "all"
        and row["stratum"] == "all_days"
    }
    if (
        census != expected
        or history.duplicated(["gauge", "day"]).any()
        or predictions.duplicated(["regime", "gauge", "day"]).any()
        or not predictions.day.dt.year.eq(predictions.test_year).all()
        or not np.isfinite(predictions[["q_observed", "q_model", *MODEL_COLUMNS]]).all().all()
        or predictions[["high_water", "clean_verification"]].isna().any().any()
    ):
        raise ValueError("Unexpected local reference or verification census")
    truth = predictions.set_index(["gauge", "day"])
    frozen = history.set_index(["gauge", "day"]).reindex(truth.index)
    np.testing.assert_array_equal(truth.q_observed, frozen.q_observed)
    np.testing.assert_array_equal(truth.clean_verification, frozen.clean_verification)
    return history, predictions, review


def seasonal_context(history, predictions):
    history = history.loc[history.day.ge("2018-01-01") & np.isfinite(history.q_observed)].copy()
    history["half_year"] = half_year(history.day)
    p = predictions.assign(half_year=half_year(predictions.day), month=predictions.day.dt.month)
    context, references = [], []
    for (gauge, year), held in p.groupby(["gauge", "test_year"], sort=True):
        past = history.loc[history.gauge.eq(gauge) & history.day.lt(f"{year}-01-01")]
        q99 = past.q_observed.quantile(0.99)
        np.testing.assert_allclose(held.p99_reference, q99, rtol=0, atol=1e-10)
        for half, tested in held.groupby("half_year"):
            ref = past.loc[past.half_year.eq(half)]
            flows = np.sort(ref.q_observed.to_numpy(float))
            if not len(flows):
                raise ValueError(f"Missing prior flow reference for {gauge} {year} {half}")
            q = tested.q_observed.to_numpy(float)
            ranks = (
                50
                * (np.searchsorted(flows, q, "left") + np.searchsorted(flows, q, "right"))
                / len(flows)
            )
            median, seasonal_q99 = np.quantile(flows, [0.5, 0.99])
            context.append(
                tested.assign(
                    seasonal_percentile=ranks,
                    seasonal_p99=q >= seasonal_q99,
                    seasonal_median_mm_day=median,
                    seasonal_p99_mm_day=seasonal_q99,
                )
            )
            references.append(
                dict(
                    gauge=gauge,
                    test_year=year,
                    half_year=half,
                    reference_days=len(flows),
                    reference_calendar_years=ref.day.dt.year.nunique(),
                    last_reference_day=ref.day.max(),
                    median_mm_day=median,
                    seasonal_p99_mm_day=seasonal_q99,
                    all_season_p99_mm_day=q99,
                )
            )
    p = pd.concat(context).sort_index()
    if len(p) != len(predictions) or not p.high_water.eq(p.q_observed.ge(p.p99_reference)).all():
        raise ValueError("The preserved all-season labels do not match their saved thresholds")
    p["both"] = p.high_water & p.seasonal_p99
    p["all_season_only"] = p.high_water & ~p.seasonal_p99
    p["seasonal_only"] = p.seasonal_p99 & ~p.high_water
    return p, pd.DataFrame(references)


def episode_peaks(spatial):
    events = pd.read_csv(MEMBERSHIP, dtype={"gauge": str})
    events = events.loc[events.dataset.eq("local_spatial")].copy()
    for column in ("start", "end"):
        events[column] = pd.to_datetime(events[column], utc=True)
    high = spatial.loc[spatial.high_water].reset_index(names="row")
    joined = high.merge(events, on=["gauge", "river_group"])
    joined = joined.loc[joined.day.between(joined.start, joined.end)]
    if len(high) != len(joined) or joined.row.duplicated().any():
        raise ValueError("Each high-water day must map to one saved episode")
    peaks = joined.sort_values(["q_observed", "day"], ascending=[False, True]).drop_duplicates(
        ["episode", "gauge"]
    )
    counts = joined.groupby("episode").agg(
        first_observed_p99_day=("day", "min"),
        high_water_days=("day", "size"),
        high_water_half_years=("half_year", "nunique"),
    )
    return (
        peaks[
            [
                "episode",
                "river_group",
                "gauge",
                "station",
                "day",
                "half_year",
                "q_observed",
                "seasonal_percentile",
                "seasonal_p99",
                "clean_verification",
            ]
        ]
        .merge(counts, left_on="episode", right_index=True, validate="many_to_one")
        .sort_values(["episode", "gauge"], ignore_index=True)
    )


def review_errors(p, settings):
    days = pd.date_range(f"{p.test_year.min()}-01-01", f"{p.test_year.max()}-12-31", tz="UTC")
    draws = joint_multiplicities(days, settings["draws"], settings["seed"], block_days=30)
    arms = ["q_model", *MODEL_COLUMNS]
    records = []
    for regime, cohort in p.groupby("regime"):
        eligible = population(cohort)
        for quality, f in (("eligible", cohort), ("clean", cohort.loc[cohort.clean_verification])):
            subsets = {
                "all_days": f,
                "all_season_p99": f.loc[f.high_water],
                "cool_all_season_p99": f.loc[f.high_water & f.half_year.eq("cool")],
                "warm_all_season_p99": f.loc[f.high_water & f.half_year.eq("warm")],
                "seasonal_p99": f.loc[f.seasonal_p99],
                "both": f.loc[f.both],
                "all_season_only": f.loc[f.all_season_only],
                "seasonal_only": f.loc[f.seasonal_only],
            }
            for name, frame in subsets.items():
                expected = population(frame)
                if not expected:
                    raise ValueError(f"No supported observations for {regime} {quality} {name}")
                gs, cs, vs = gauge_resamples(frame, arms, days, draws)
                boot, missing = balanced_resamples(gs, cs, vs, expected)
                point = {arm: score(frame, frame[arm], expected) for arm in arms}
                for policy in POLICIES:
                    for arm in ARMS:
                        candidate = f"{policy}__{arm}"
                        reference = "q_model" if arm == "C2" else f"{policy}__C2"
                        c, r = arms.index(candidate), arms.index(reference)
                        boot_r = boot[:, r, 0]
                        good = np.isfinite(boot[:, c, 0]) & np.isfinite(boot_r) & (boot_r > 0)
                        lo, hi = (
                            np.quantile(100 * (1 - boot[good, c, 0] / boot_r[good]), [0.025, 0.975])
                            if good.any()
                            else (np.nan, np.nan)
                        )
                        mae, reference_mae = point[candidate]["mae"], point[reference]["mae"]
                        records.append(
                            dict(
                                regime=regime,
                                quality=quality,
                                subset=name,
                                policy=policy,
                                candidate=arm,
                                reference="raw GEOGLOWS" if arm == "C2" else "C2",
                                gauge_days=len(frame),
                                dates=frame.day.nunique(),
                                gauges=len(expected),
                                rivers=len(set(expected.values())),
                                gauges_without_days="|".join(sorted(set(eligible) - set(expected))),
                                mae_mm_day=mae,
                                reference_mae_mm_day=reference_mae,
                                bias_mm_day=point[candidate]["bias"],
                                reference_bias_mm_day=point[reference]["bias"],
                                reduction_pct=100 * (1 - mae / reference_mae),
                                low_pct=lo,
                                high_pct=hi,
                                defined_draws=int(good.sum()),
                                missing_gauge_draws=missing,
                            )
                        )
    return pd.DataFrame(records)


def verify_primary(scores, review):
    records = scores.query("subset == 'all_season_p99' and reference == 'C2'")
    indices = ["dataset", "policy", "stratum", "candidate"]
    held = json.loads(C2_REVIEW.read_text())
    if held["status"] != "completed":
        raise ValueError("C2 reference review is incomplete")
    checks = held["point_estimates"] + [
        dict(row, candidate="C2+AlphaEarth2017")
        for row in review["point_estimates"]
        if row["candidate"] == "C2+AlphaEarth 2017"
    ]
    old = (
        pd.DataFrame(checks)
        .query("scope == 'all' and metric == 'mae' and reference == 'C2'")
        .set_index(indices)
    )
    for row in records.itertuples(index=False):
        key = (
            f"local_{row.regime}",
            row.policy,
            "clean_high_water" if row.quality == "clean" else "high_water",
            row.candidate,
        )
        expected = old.loc[key]
        np.testing.assert_allclose(
            [row.gauge_days, row.reduction_pct],
            [expected.rows, expected.reduction_pct],
            atol=1e-9,
            rtol=0,
        )
    return len(records)


def describe(spatial, period):
    return (
        spatial.groupby(["river_group", "gauge", "station", period, "half_year"])
        .agg(
            days=("day", "size"),
            clean_days=("clean_verification", "sum"),
            median_q_mm_day=("q_observed", "median"),
            all_season_p99_days=("high_water", "sum"),
            season_p99_days=("seasonal_p99", "sum"),
            both_days=("both", "sum"),
            seasonal_only_days=("seasonal_only", "sum"),
        )
        .reset_index()
    )


def seasonal_only_year_influence(p):
    records = []
    for regime, cohort in p.loc[p.seasonal_only].groupby("regime"):
        for quality, f in (("eligible", cohort), ("clean", cohort.loc[cohort.clean_verification])):
            # Hold the original row weights so omitting one year cannot change
            # all remaining weights merely by making a gauge disappear.
            errors = f[MODEL_COLUMNS].sub(f.q_observed, axis=0).abs().mul(weights(f), axis=0)
            totals = errors.sum()
            removed = errors.groupby(f.test_year).sum()
            remaining = totals - removed
            for policy in POLICIES:
                baseline = remaining[f"{policy}__C2"]
                for arm in ARMS[1:]:
                    reduction = 100 * (
                        1 - remaining[f"{policy}__{arm}"] / baseline.where(baseline.gt(0))
                    )
                    for year, value in reduction.items():
                        records.append(
                            dict(
                                regime=regime,
                                quality=quality,
                                policy=policy,
                                candidate=arm,
                                year_omitted=year,
                                gauge_days_removed=int(f.test_year.eq(year).sum()),
                                reduction_pct=value,
                            )
                        )
    return pd.DataFrame(records)


def draw(spatial, monthly, output):
    fig, (pulse, peaks) = plt.subplots(2, 1, sharex=True, figsize=(8.4, 6.2), layout="constrained")
    medians = spatial.groupby("gauge").q_observed.median()
    plot = monthly.assign(ratio=monthly.median_q_mm_day / monthly.gauge.map(medians))
    for station, r in plot.groupby("station"):
        pulse.plot(r.month, r.ratio, marker="o", markersize=2.5, label=station)
    pulse.axhline(1, color="#888888", linestyle=":")
    pulse.set(
        ylabel="Monthly median ÷ gauge median",
        title="Seasonal discharge at the seven tributary gauges",
    )
    pulse.legend(ncol=3, frameon=False, fontsize=8)
    by_month = monthly.groupby("month").sum(numeric_only=True)
    peaks.bar(
        by_month.index,
        100 * by_month.all_season_p99_days / by_month.days,
        label="All-season p99",
        color="#1e668c",
    )
    peaks.bar(
        by_month.index,
        100 * by_month.seasonal_only_days / by_month.days,
        bottom=100 * by_month.all_season_p99_days / by_month.days,
        label="Seasonal p99 only",
        color="#cf8151",
    )
    peaks.set(
        ylabel="Days per 100 gauge-days", xticks=np.arange(1, 13), xticklabels=cal.month_abbr[1:]
    )
    peaks.legend(frameon=False)
    for ax in (pulse, peaks):
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["right", "top"]].set_visible(False)
    fig.savefig(output, dpi=175)
    plt.close(fig)


def main(out):
    history, predictions, receipt = read_inputs()
    p, references = seasonal_context(history, predictions)
    settings = json.loads(SETTINGS.read_text())
    s = p.loc[p.regime.eq("spatial")]
    t = p.loc[p.regime.eq("temporal")]
    matched = ["gauge", "day", "q_observed", "high_water", "seasonal_p99", "clean_verification"]
    pd.testing.assert_frame_equal(
        s[matched].reset_index(drop=True), t[matched].reset_index(drop=True)
    )
    scores = review_errors(p, settings)
    verified = verify_primary(scores, receipt)
    monthly, episodes = describe(s, "month"), episode_peaks(s)
    out.mkdir(parents=True, exist_ok=True)
    tables = {
        "seasonal_reference.csv": references,
        "monthly_coverage.csv": monthly,
        "annual_coverage.csv": describe(s, "test_year"),
        "episode_peaks.csv": episodes,
        "model_scores.csv": scores,
        "seasonal_only_year_influence.csv": seasonal_only_year_influence(p),
    }
    for name, table in tables.items():
        table.to_csv(out / name, index=False)
    draw(s, monthly, out / "seasonal_pulse.png")
    write_json(
        out / "manifest.json",
        dict(
            status="completed",
            season_definition=DEFINITION,
            scoring="Fixed predictions; MAE balanced by river and gauge",
            prior="Local prepared reference observations before test year and from 2018; same history for both p99 definitions",
            qa="Clean sensitivity screens verification days; the historical reference stays fixed to isolate this change",
            block_days=30,
            draws=settings["draws"],
            seed=settings["seed"],
            primary_contrasts_verified=verified,
            inputs_sha256={
                str(f.relative_to(ROOT)): sha(f)
                for f in (
                    PREDICTIONS,
                    REVIEW,
                    C2_REVIEW,
                    PREPARATION,
                    HISTORY,
                    MEMBERSHIP,
                    SETTINGS,
                    Path(__file__),
                    ROOT / "src/dise_corrected.py",
                    ROOT / "src/dise_repeatability.py",
                )
            },
            outputs_sha256={name: sha(out / name) for name in (*tables, "seasonal_pulse.png")},
        ),
    )
    print(
        s.groupby("half_year")[["high_water", "seasonal_p99", "both", "seasonal_only"]]
        .sum()
        .to_string()
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    main(parser.parse_args().output)
