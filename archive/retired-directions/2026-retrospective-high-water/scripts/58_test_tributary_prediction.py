"""Retrospective six-hour rain-trigger test of next-day tributary high water.

Only observations timestamped at or before issue time enter predictors. The
discharge and era-p99 series are retrospectively verified, so this is not an
as-issued operational warning evaluation.
"""

from __future__ import annotations

import hashlib
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location(
    "cross_tributary", ROOT / "scripts/53_cross_tributary_rain_episodes.py"
)
core = module_from_spec(spec)
spec.loader.exec_module(core)

OUT = core.OUT / "prediction_6h"
DECISION_HOUR = 6
HORIZON_HOURS = 24
RAIN_TRIGGER_MM = 2.0
MIN_FUTURE_COVERAGE = 0.9
FIRST_TEST_YEAR = 2014
SITE_DUMMIES = tuple(f"site_{site}" for site in core.SITES[1:])
RAIN_FEATURES = (
    "log1p_local_rain_6h",
    "log1p_regional_max_rain_6h",
    "n_sites_rain_2mm_6h",
    "warm",
    *SITE_DUMMIES,
)
FLOW_FEATURES = (*RAIN_FEATURES, "issue_q_over_p99")


def rain_starts(rain, dry_gap_hours=12):
    """Recognize wet-spell starts without using their future total or end."""
    wet = rain.max(axis=1, skipna=True).ge(core.WET_MM_H).to_numpy()
    positions = np.flatnonzero(wet)
    if not len(positions):
        return np.array([], dtype=int)
    return positions[np.r_[True, np.diff(positions) > dry_gap_hours]]


def build_decisions(rain, states, trigger_mm=RAIN_TRIGGER_MM, full_future=False):
    """One non-overlapping decision per selected wet spell, six site rows each."""
    rows = []
    last_issue = None
    for start_position in rain_starts(rain):
        issue_position = start_position + DECISION_HOUR - 1
        end_position = issue_position + HORIZON_HOURS
        if end_position >= len(rain):
            continue
        issue_time = rain.index[issue_position]
        if last_issue is not None and issue_time <= last_issue + pd.Timedelta(hours=24):
            continue
        observed_rain = rain.iloc[start_position : issue_position + 1]
        if observed_rain.isna().any().any():
            continue
        rain_totals = observed_rain.sum()
        if rain_totals.max() < trigger_mm:
            continue
        future_times = rain.index[issue_position + 1 : end_position + 1]
        current = {site: states[site].loc[issue_time] for site in core.SITES}
        if any(
            not state.valid
            or pd.isna(state.q)
            or pd.isna(state.p99)
            or state.p99 <= 0
            or state.q > state.p99
            for state in current.values()
        ):
            continue
        future = {site: states[site].loc[future_times] for site in core.SITES}
        coverage = {
            site: float((window.valid & window.q.notna() & window.p99.notna()).mean())
            for site, window in future.items()
        }
        required = 1.0 if full_future else MIN_FUTURE_COVERAGE
        if min(coverage.values()) < required:
            continue
        decision_id = f"decision_{issue_time:%Y%m%d%H}"
        for site in core.SITES:
            window = future[site]
            high = window.valid & window.q.gt(window.p99)
            rows.append(
                {
                    "decision_id": decision_id,
                    "rain_start_utc": rain.index[start_position],
                    "issue_utc": issue_time,
                    "target_end_utc": rain.index[end_position],
                    "year": issue_time.year,
                    "site": site,
                    "high_next_24h": int(high.any()),
                    "future_coverage": coverage[site],
                    "local_rain_6h_mm": float(rain_totals[site]),
                    "regional_max_rain_6h_mm": float(rain_totals.max()),
                    "n_sites_rain_2mm_6h": int(rain_totals.ge(2).sum()),
                    "issue_q_over_p99": float(current[site].q / current[site].p99),
                    "warm": int(issue_time.month in range(5, 11)),
                }
            )
        last_issue = issue_time
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("No fully observed six-site rain-trigger decisions")
    frame["log1p_local_rain_6h"] = np.log1p(frame.local_rain_6h_mm)
    frame["log1p_regional_max_rain_6h"] = np.log1p(frame.regional_max_rain_6h_mm)
    for site in core.SITES[1:]:
        frame[f"site_{site}"] = frame.site.eq(site).astype(int)
    return frame


def forward_predictions(frame):
    """Fit only on prior calendar years; test on each later year once."""
    outputs = []
    for year in sorted(frame.year.unique()):
        if year < FIRST_TEST_YEAR:
            continue
        test_start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        training = frame.loc[frame.year.lt(year) & frame.target_end_utc.lt(test_start)]
        testing = frame.loc[frame.year.eq(year)].copy()
        if testing.empty:
            continue
        if training.high_next_24h.nunique() != 2:
            raise ValueError(f"No positive and negative training outcomes before {year}")
        testing["training_last_year"] = year - 1
        testing["training_site_rows"] = len(training)
        testing["training_positive_site_rows"] = int(training.high_next_24h.sum())
        testing["climatology_probability"] = float(training.high_next_24h.mean())
        for name, features in (
            ("rain_only", RAIN_FEATURES),
            ("rain_plus_flow", FLOW_FEATURES),
        ):
            fit = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=1000))
            fit.fit(training[list(features)], training.high_next_24h)
            testing[f"p_{name}"] = fit.predict_proba(testing[list(features)])[:, 1]
        outputs.append(testing)
    if not outputs:
        raise ValueError("No forward-test years")
    return pd.concat(outputs, ignore_index=True)


def metrics(frame):
    y = frame.high_next_24h.to_numpy()
    if y.min() == y.max():
        return None
    records = []
    for name, column in (
        ("training_climatology", "climatology_probability"),
        ("rain_only", "p_rain_only"),
        ("rain_plus_flow", "p_rain_plus_flow"),
    ):
        p = frame[column].to_numpy()
        records.append(
            {
                "model": name,
                "n_site_rows": len(frame),
                "n_decisions": frame.decision_id.nunique(),
                "n_positive_site_rows": int(y.sum()),
                "prevalence": float(y.mean()),
                "brier": float(brier_score_loss(y, p)),
                "log_loss": float(log_loss(y, p)),
                "roc_auc": float(roc_auc_score(y, p)),
                "average_precision": float(average_precision_score(y, p)),
            }
        )
    return pd.DataFrame(records)


def paired_year_bootstrap(frame, draws=999, seed=20261003):
    years = np.sort(frame.year.unique())
    groups = {year: frame.loc[frame.year.eq(year)] for year in years}
    rng = np.random.default_rng(seed)
    records = []
    for draw in range(draws + 1):
        chosen = years if draw == 0 else rng.choice(years, size=len(years), replace=True)
        sample = pd.concat([groups[year] for year in chosen], ignore_index=True)
        score = metrics(sample)
        if score is None:
            records.append({"draw": draw, "failure": "single outcome class"})
            continue
        rain = score.set_index("model").loc["rain_only"]
        flow = score.set_index("model").loc["rain_plus_flow"]
        records.append(
            {
                "draw": draw,
                "failure": "",
                "brier_improvement": float(rain.brier - flow.brier),
                "log_loss_improvement": float(rain.log_loss - flow.log_loss),
                "roc_auc_gain": float(flow.roc_auc - rain.roc_auc),
                "average_precision_gain": float(flow.average_precision - rain.average_precision),
            }
        )
    return pd.DataFrame(records)


def exclude_reviewed_measurement_concerns(frame, review):
    """Omit entire decision windows with a flagged reviewed high-water onset."""
    flagged = review.loc[review.measurement_concern & review.review_decision.eq("include_exact")]
    flagged_times = pd.to_datetime(flagged.onset_utc, utc=True)
    decisions = frame.drop_duplicates("decision_id")
    concern_ids = set()
    for decision in decisions.itertuples(index=False):
        if flagged_times.between(
            decision.issue_utc, decision.target_end_utc, inclusive="right"
        ).any():
            concern_ids.add(decision.decision_id)
    return frame.loc[~frame.decision_id.isin(concern_ids)].copy(), len(concern_ids)


def summarize_bootstrap(draws):
    valid = draws.loc[draws.draw.gt(0) & draws.failure.eq("")]
    point = draws.iloc[0]
    result = {
        "bootstrap_attempted": len(draws) - 1,
        "bootstrap_failed": len(draws) - 1 - len(valid),
    }
    for term in (
        "brier_improvement",
        "log_loss_improvement",
        "roc_auc_gain",
        "average_precision_gain",
    ):
        result[f"{term}_estimate"] = float(point[term])
        result[f"{term}_low"] = float(valid[term].quantile(0.025))
        result[f"{term}_high"] = float(valid[term].quantile(0.975))
    return result


def main():
    rain = core.read_hourly(core.DATA / "radolan_catchment_hourly.csv")[list(core.SITES)]
    discharge = core.read_hourly(core.DATA / "event_study_discharge_hourly.csv")
    rain = rain.loc[rain.index.intersection(discharge.index)]
    ratings = pd.read_csv(core.DATA / "event_study_rating_eras.csv")
    states = core.site_states(discharge, ratings)
    review = pd.read_csv(core.REVIEW)
    OUT.mkdir(parents=True, exist_ok=True)
    specifications = {
        "main_2mm_90pct": (RAIN_TRIGGER_MM, False, False),
        "all_wet_90pct": (0.0, False, False),
        "rain5mm_90pct": (5.0, False, False),
        "main_2mm_full_future": (RAIN_TRIGGER_MM, True, False),
        "main_2mm_no_onset_concerns": (RAIN_TRIGGER_MM, False, True),
    }
    results = []
    for name, (trigger_mm, full_future, exclude_concerns) in specifications.items():
        frame = build_decisions(rain, states, trigger_mm, full_future)
        if exclude_concerns:
            frame, removed = exclude_reviewed_measurement_concerns(frame, review)
        else:
            removed = 0
        predictions = forward_predictions(frame)
        scores = metrics(predictions)
        draws = paired_year_bootstrap(predictions)
        scores.insert(0, "specification", name)
        scores.insert(1, "n_measurement_concern_decisions_excluded", removed)
        results.append(scores)
        predictions.to_csv(OUT / f"predictions_{name}.csv", index=False)
        draws.to_csv(OUT / f"bootstrap_{name}.csv", index=False)
        (OUT / f"bootstrap_summary_{name}.json").write_text(
            json.dumps(summarize_bootstrap(draws), indent=2) + "\n"
        )
        if name == "main_2mm_90pct":
            pd.concat(
                [metrics(group).assign(year=year) for year, group in predictions.groupby("year")],
                ignore_index=True,
            ).to_csv(OUT / "year_scores.csv", index=False)
            pd.concat(
                [metrics(group).assign(site=site) for site, group in predictions.groupby("site")],
                ignore_index=True,
            ).to_csv(OUT / "site_scores.csv", index=False)
    pd.concat(results, ignore_index=True).to_csv(OUT / "scores.csv", index=False)
    manifest = {
        "status": "retrospective forward-year test using verified historical discharge",
        "decision": "sixth hour from first regional wet hour after >12 h dry",
        "trigger": "maximum six-hour catchment rain >=2 mm, observed by issue time",
        "target": "site crosses era-p99 in next 24 hours; all six below p99 at issue",
        "selection": "all six sites valid at issue and >=90% valid target hours; no overlapping chosen decisions",
        "test_years": "2014-2025; each fit uses only earlier years",
        "predictor_timing": "rain accumulation through issue hour and discharge at issue hour only",
        "caveat": "p99 and discharge are retrospectively verified, not archived as-issued versions",
        "bootstrap": "999 resamples of whole held-out calendar years, fixed seed 20261003",
        "input_sha256": {
            "rain": core.hash_file(core.DATA / "radolan_catchment_hourly.csv"),
            "discharge": core.hash_file(core.DATA / "event_study_discharge_hourly.csv"),
            "ratings": core.hash_file(core.DATA / "event_study_rating_eras.csv"),
            "onset_review": core.hash_file(core.REVIEW),
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
