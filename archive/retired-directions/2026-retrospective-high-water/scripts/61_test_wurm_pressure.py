"""Wurm-only forward-year test of six-hour pressure change.

The regional rain-start clock and six-hour issue time match script 58, but
eligibility, predictors, and the verified 24-hour outcome depend only on Wurm
after the regional rain trigger. ERA5-Land pressure is retrospective and the
discharge/rating series is retrospectively verified: not as-issued FEWS skill.
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
spec = spec_from_file_location("prediction", ROOT / "scripts/58_test_tributary_prediction.py")
prediction = module_from_spec(spec)
spec.loader.exec_module(prediction)
core = prediction.core
OUT = prediction.OUT / "wurm_pressure_only_site"
WEATHER = core.DATA / "event_study_weather_hourly.csv"
RAIN = core.DATA / "radolan_catchment_hourly.csv"
DISCHARGE = core.DATA / "event_study_discharge_hourly.csv"
RATINGS = core.DATA / "event_study_rating_eras.csv"
REVIEW = core.REVIEW
SEED = 20261003
BASE = (
    "log1p_local_rain_6h",
    "log1p_regional_max_rain_6h",
    "n_sites_rain_2mm_6h",
    "warm",
    "issue_q_over_p99",
)
PRESSURE = (*BASE, "pressure_change_6h_hpa")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_wurm_decisions(rain: pd.DataFrame, worm: pd.DataFrame) -> pd.DataFrame:
    """One Wurm decision per eligible regional wet spell, with no other gauge QA."""
    rows = []
    last_issue = None
    for start in prediction.rain_starts(rain):
        issue = start + prediction.DECISION_HOUR - 1
        end = issue + prediction.HORIZON_HOURS
        if end >= len(rain):
            continue
        issue_time = rain.index[issue]
        if last_issue is not None and issue_time <= last_issue + pd.Timedelta(hours=24):
            continue
        past = rain.iloc[start : issue + 1]
        if past.isna().any().any():
            continue
        totals = past.sum()
        if totals.max() < prediction.RAIN_TRIGGER_MM:
            continue
        current = worm.loc[issue_time]
        if not bool(current.valid) or pd.isna(current.q) or pd.isna(current.p99) or current.p99 <= 0 or current.q > current.p99:
            continue
        future = worm.loc[rain.index[issue + 1 : end + 1]]
        observed = future.valid & future.q.notna() & future.p99.notna()
        coverage = float(observed.mean())
        if coverage < prediction.MIN_FUTURE_COVERAGE:
            continue
        rows.append(
            {
                "decision_id": f"decision_{issue_time:%Y%m%d%H}",
                "rain_start_utc": rain.index[start],
                "issue_utc": issue_time,
                "target_end_utc": rain.index[end],
                "year": issue_time.year,
                "high_next_24h": int((observed & future.q.gt(future.p99)).any()),
                "future_coverage": coverage,
                "local_rain_6h_mm": float(totals.Worm),
                "regional_max_rain_6h_mm": float(totals.max()),
                "n_sites_rain_2mm_6h": int(totals.ge(2).sum()),
                "issue_q_over_p99": float(current.q / current.p99),
                "warm": int(issue_time.month in range(5, 11)),
            }
        )
        last_issue = issue_time
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("No eligible Wurm decisions")
    frame["log1p_local_rain_6h"] = np.log1p(frame.local_rain_6h_mm)
    frame["log1p_regional_max_rain_6h"] = np.log1p(frame.regional_max_rain_6h_mm)
    return frame


def attach_pressure(decisions: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    worm = weather.loc[weather.watercourse.eq("Worm"), ["timestamp_utc", "pressure_change_6h_hpa"]]
    if worm.timestamp_utc.duplicated().any():
        raise ValueError("Duplicate Wurm weather hours")
    joined = decisions.merge(worm.rename(columns={"timestamp_utc": "issue_utc"}), on="issue_utc", how="left", validate="one_to_one")
    if joined.pressure_change_6h_hpa.isna().any():
        raise ValueError("Missing pressure at an issue time")
    return joined


def forward_fit(frame: pd.DataFrame) -> pd.DataFrame:
    forecasts = []
    for year in sorted(frame.year.unique()):
        if year < prediction.FIRST_TEST_YEAR:
            continue
        start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        train = frame.loc[frame.year.lt(year) & frame.target_end_utc.lt(start)]
        test = frame.loc[frame.year.eq(year)].copy()
        if test.empty:
            continue
        if train.high_next_24h.nunique() != 2:
            raise ValueError(f"Training has a single outcome class for {year}")
        test["training_n"] = len(train)
        test["training_positive"] = int(train.high_next_24h.sum())
        test["p_training_prevalence"] = float(train.high_next_24h.mean())
        for name, features in (("base", BASE), ("pressure", PRESSURE)):
            model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=1000))
            model.fit(train[list(features)], train.high_next_24h)
            test[f"p_{name}"] = model.predict_proba(test[list(features)])[:, 1]
        forecasts.append(test)
    if not forecasts:
        raise ValueError("No forward-test years")
    return pd.concat(forecasts, ignore_index=True)


def scores(frame: pd.DataFrame) -> pd.DataFrame:
    y = frame.high_next_24h.to_numpy()
    if len(np.unique(y)) != 2:
        raise ValueError("Evaluation has a single outcome class")
    records = []
    for name, column in (("training_prevalence", "p_training_prevalence"), ("base", "p_base"), ("pressure", "p_pressure")):
        p = frame[column].to_numpy()
        records.append(
            {
                "model": name,
                "n_decisions": len(frame),
                "n_positive": int(y.sum()),
                "brier": float(brier_score_loss(y, p)),
                "log_loss": float(log_loss(y, p)),
                "roc_auc": float(roc_auc_score(y, p)),
                "average_precision": float(average_precision_score(y, p)),
            }
        )
    return pd.DataFrame(records)


def gains(frame: pd.DataFrame) -> dict:
    table = scores(frame).set_index("model")
    return {
        "brier_improvement": float(table.loc["base", "brier"] - table.loc["pressure", "brier"]),
        "log_loss_improvement": float(table.loc["base", "log_loss"] - table.loc["pressure", "log_loss"]),
        "roc_auc_gain": float(table.loc["pressure", "roc_auc"] - table.loc["base", "roc_auc"]),
        "average_precision_gain": float(table.loc["pressure", "average_precision"] - table.loc["base", "average_precision"]),
    }


def paired_year_bootstrap(frame: pd.DataFrame, draws: int = 999) -> pd.DataFrame:
    years = np.sort(frame.year.unique())
    groups = {year: frame.loc[frame.year.eq(year)] for year in years}
    rng = np.random.default_rng(SEED)
    rows = [{"draw": 0, "failure": "", **gains(frame)}]
    for draw in range(1, draws + 1):
        sample = pd.concat([groups[year] for year in rng.choice(years, size=len(years), replace=True)])
        if sample.high_next_24h.nunique() != 2:
            rows.append({"draw": draw, "failure": "single outcome class"})
        else:
            rows.append({"draw": draw, "failure": "", **gains(sample)})
    return pd.DataFrame(rows)


def independent_episode_sensitivity(frame: pd.DataFrame, review: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Drop decisions in an ongoing episode and unsupported repeat-crossing positives."""
    onsets = review.loc[review.watercourse.eq("Worm") & review.review_decision.eq("include_exact"), "onset_utc"]
    kept = []
    removed = {"recent_onset": 0, "high_without_new_reviewed_onset": 0}
    for row in frame.itertuples(index=False):
        recent = onsets.between(row.issue_utc - pd.Timedelta(hours=72), row.issue_utc, inclusive="both").any()
        new = onsets.between(row.issue_utc, row.target_end_utc, inclusive="right").any()
        if recent:
            removed["recent_onset"] += 1
        elif row.high_next_24h and not new:
            removed["high_without_new_reviewed_onset"] += 1
        else:
            kept.append(row.decision_id)
    return frame.loc[frame.decision_id.isin(kept)].copy(), removed


def main() -> None:
    rain = core.read_hourly(RAIN)[list(core.SITES)]
    discharge = core.read_hourly(DISCHARGE)
    rain = rain.loc[rain.index.intersection(discharge.index)]
    ratings = pd.read_csv(RATINGS)
    worm = core.site_states(discharge, ratings)["Worm"]
    weather = pd.read_csv(WEATHER, parse_dates=["timestamp_utc"])
    decisions = attach_pressure(build_wurm_decisions(rain, worm), weather)
    forecasts = forward_fit(decisions)
    OUT.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(OUT / "all_decisions.csv", index=False)
    forecasts.to_csv(OUT / "forward_predictions.csv", index=False)
    result = scores(forecasts)
    result.to_csv(OUT / "scores.csv", index=False)
    draws = paired_year_bootstrap(forecasts)
    draws.to_csv(OUT / "paired_year_bootstrap.csv", index=False)
    point = draws.iloc[0]
    valid = draws.loc[draws.draw.gt(0) & draws.failure.eq("")]
    summary = {"n_bootstrap_failed": len(draws) - 1 - len(valid)}
    for term in ("brier_improvement", "log_loss_improvement", "roc_auc_gain", "average_precision_gain"):
        summary[term] = float(point[term])
        summary[f"{term}_year_interval"] = valid[term].quantile([0.025, 0.975]).tolist()

    review = pd.read_csv(REVIEW, parse_dates=["onset_utc"])
    episode_decisions, episode_removed = independent_episode_sensitivity(decisions, review)
    episode_forecasts = forward_fit(episode_decisions)
    episode_forecasts.to_csv(OUT / "independent_episode_predictions.csv", index=False)
    episode_scores = scores(episode_forecasts)
    episode_scores.to_csv(OUT / "independent_episode_scores.csv", index=False)
    episode_draws = paired_year_bootstrap(episode_forecasts)
    episode_draws.to_csv(OUT / "independent_episode_bootstrap.csv", index=False)
    episode_valid = episode_draws.loc[episode_draws.draw.gt(0) & episode_draws.failure.eq("")]
    episode_summary = {
        "n_decisions": len(episode_decisions),
        "n_positive": int(episode_decisions.high_next_24h.sum()),
        "n_test_decisions": len(episode_forecasts),
        "n_test_positive": int(episode_forecasts.high_next_24h.sum()),
        "removed": episode_removed,
        "bootstrap_failed": len(episode_draws) - 1 - len(episode_valid),
        "gains": gains(episode_forecasts),
        "year_intervals": {
            term: episode_valid[term].quantile([0.025, 0.975]).tolist()
            for term in ("brier_improvement", "log_loss_improvement", "roc_auc_gain", "average_precision_gain")
        },
    }
    concerns = review.loc[review.watercourse.eq("Worm") & review.measurement_concern, "onset_utc"]
    concern_ids = forecasts.loc[
        forecasts.apply(lambda row: concerns.between(row.issue_utc, row.target_end_utc, inclusive="right").any(), axis=1),
        "decision_id",
    ]
    clean = forecasts.loc[~forecasts.decision_id.isin(concern_ids)]
    july = forecasts.loc[forecasts.issue_utc.dt.date.eq(pd.Timestamp("2021-07-13").date())]
    manifest = {
        "status": "exploratory Wurm-only retrospective test; not as-issued forecasting",
        "decision": "sixth hour of regional rain-defined wet spell; regional max first-six-hour rain >=2mm",
        "outcome": "Wurm era-p99 exceedance in next 24h with >=90% valid future hours",
        "fit": "expanding prior-year L2 logistic, StandardScaler, C=1; same rows and labels for both models",
        "first_test_year": prediction.FIRST_TEST_YEAR,
        "n_all_decisions": len(decisions),
        "n_all_positive": int(decisions.high_next_24h.sum()),
        "n_test_decisions": len(forecasts),
        "n_test_positive": int(forecasts.high_next_24h.sum()),
        "july_13_decisions": july[["issue_utc", "high_next_24h", "future_coverage", "p_base", "p_pressure"]].astype({"issue_utc": "str"}).to_dict("records"),
        "n_measurement_concern_decisions": int(len(concern_ids)),
        "measurement_clean_evaluation_only": gains(clean) if len(clean) != len(forecasts) else None,
        "omit_2024_evaluation_only": gains(forecasts.loc[forecasts.year.ne(2024)]),
        "paired_year_bootstrap": summary,
        "independent_episode_sensitivity": episode_summary,
        "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in (RAIN, DISCHARGE, RATINGS, WEATHER, REVIEW)},
        "seed": SEED,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(result.to_string(index=False))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
