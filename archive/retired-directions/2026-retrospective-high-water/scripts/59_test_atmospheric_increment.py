"""Test whether held ERA5-Land pressure change or humidity adds prediction skill.

All predictors are timestamped at the six-hour issue time. ERA5-Land is
retrospective reanalysis, so positive results are not as-issued warning skill.
"""

from __future__ import annotations

import hashlib
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("prediction", ROOT / "scripts/58_test_tributary_prediction.py")
prediction = module_from_spec(spec)
spec.loader.exec_module(prediction)
core = prediction.core
OUT = prediction.OUT / "atmospheric_increment"
WEATHER = core.DATA / "event_study_weather_hourly.csv"
SPECS = {
    "rain_plus_flow": prediction.FLOW_FEATURES,
    "plus_pressure_change": (*prediction.FLOW_FEATURES, "pressure_change_6h_hpa"),
    "plus_humidity": (*prediction.FLOW_FEATURES, "relative_humidity_pct"),
    "plus_both": (
        *prediction.FLOW_FEATURES,
        "pressure_change_6h_hpa",
        "relative_humidity_pct",
    ),
}


def attach_issue_weather(frame, weather):
    """Exact timestamp/site match; preserve the same six-site decision sample."""
    required = [
        "timestamp_utc",
        "watercourse",
        "pressure_change_6h_hpa",
        "relative_humidity_pct",
    ]
    if weather.duplicated(["timestamp_utc", "watercourse"]).any():
        raise ValueError("Duplicate site/weather timestamp")
    table = weather[required].rename(columns={"timestamp_utc": "issue_utc", "watercourse": "site"})
    joined = frame.merge(table, on=["issue_utc", "site"], how="left", validate="one_to_one")
    missing = joined[["pressure_change_6h_hpa", "relative_humidity_pct"]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"Incomplete issue-time weather on {int(missing.sum())} site rows")
    return joined


def forward_predictions(frame):
    outputs = []
    for year in sorted(frame.year.unique()):
        if year < prediction.FIRST_TEST_YEAR:
            continue
        test_start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        training = frame.loc[frame.year.lt(year) & frame.target_end_utc.lt(test_start)]
        testing = frame.loc[frame.year.eq(year)].copy()
        if testing.empty:
            continue
        if training.high_next_24h.nunique() != 2:
            raise ValueError(f"No positive and negative training outcomes before {year}")
        for name, features in SPECS.items():
            fit = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=1000))
            fit.fit(training[list(features)], training.high_next_24h)
            testing[f"p_{name}"] = fit.predict_proba(testing[list(features)])[:, 1]
        outputs.append(testing)
    if not outputs:
        raise ValueError("No forward-test years")
    return pd.concat(outputs, ignore_index=True)


def comparison_table(predictions):
    rows = []
    for name in SPECS:
        paired = predictions.assign(
            climatology_probability=predictions.p_rain_plus_flow,
            p_rain_only=predictions.p_rain_plus_flow,
            p_rain_plus_flow=predictions[f"p_{name}"],
        )
        score = prediction.metrics(paired)
        fitted = score.loc[score.model.eq("rain_plus_flow")].iloc[0].to_dict()
        fitted["model"] = name
        rows.append(fitted)
    return pd.DataFrame(rows)


def paired_gain(predictions, candidate, baseline="rain_plus_flow"):
    paired = predictions.assign(
        climatology_probability=predictions[f"p_{baseline}"],
        p_rain_only=predictions[f"p_{baseline}"],
        p_rain_plus_flow=predictions[f"p_{candidate}"],
    )
    draws = prediction.paired_year_bootstrap(paired)
    return prediction.summarize_bootstrap(draws), draws


def within_decision_ranks(forecasts):
    """High-versus-low site ranking within the same mixed-outcome decision."""
    rows = []
    for decision_id, group in forecasts.groupby("decision_id"):
        if group.high_next_24h.nunique() != 2:
            continue
        row = {"decision_id": decision_id, "year": int(group.year.iloc[0])}
        high = group.high_next_24h.eq(1).to_numpy()
        for name in SPECS:
            probabilities = group[f"p_{name}"].to_numpy()
            pair = probabilities[high, None] - probabilities[None, ~high]
            row[f"rank_{name}"] = float(np.mean((pair > 0) + 0.5 * (pair == 0)))
        rows.append(row)
    return pd.DataFrame(rows)


def within_decision_bootstrap(ranks, draws=999, seed=20261003):
    years = np.sort(ranks.year.unique())
    groups = {year: ranks.loc[ranks.year.eq(year)] for year in years}
    rng = np.random.default_rng(seed)
    records = []
    for draw in range(draws + 1):
        chosen = years if draw == 0 else rng.choice(years, size=len(years), replace=True)
        sample = pd.concat([groups[year] for year in chosen], ignore_index=True)
        row = {"draw": draw, "n_mixed_decisions": len(sample)}
        for name in tuple(SPECS)[1:]:
            row[f"gain_{name}"] = float(
                (sample[f"rank_{name}"] - sample.rank_rain_plus_flow).mean()
            )
        records.append(row)
    return pd.DataFrame(records)


def future_rain_diagnostic(forecasts, rain):
    """Post-outcome interpretation only; future rain never enters prediction."""
    rows = []
    for decision_id, group in forecasts.groupby("decision_id"):
        event = group.iloc[0]
        future = rain.loc[
            (rain.index > event.issue_utc) & (rain.index <= event.target_end_utc),
            list(core.SITES),
        ]
        rows.append(
            {
                "decision_id": decision_id,
                "year": int(event.year),
                "mean_site_pressure_change_6h_hpa": float(group.pressure_change_6h_hpa.mean()),
                "past6_maxsite_rain_mm": float(event.regional_max_rain_6h_mm),
                "future24_maxsite_rain_mm": float(future.sum().max()),
                "n_high_sites": int(group.high_next_24h.sum()),
            }
        )
    return pd.DataFrame(rows)


def main():
    rain = core.read_hourly(core.DATA / "radolan_catchment_hourly.csv")[list(core.SITES)]
    discharge = core.read_hourly(core.DATA / "event_study_discharge_hourly.csv")
    rain = rain.loc[rain.index.intersection(discharge.index)]
    ratings = pd.read_csv(core.DATA / "event_study_rating_eras.csv")
    states = core.site_states(discharge, ratings)
    decisions = prediction.build_decisions(rain, states)
    weather = pd.read_csv(WEATHER, parse_dates=["timestamp_utc"])
    joined = attach_issue_weather(decisions, weather)
    forecasts = forward_predictions(joined)
    OUT.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(OUT / "forward_predictions.csv", index=False)
    comparison_table(forecasts).to_csv(OUT / "scores.csv", index=False)
    comparisons = []
    for name in tuple(SPECS)[1:]:
        summary, draws = paired_gain(forecasts, name)
        comparisons.append({"baseline": "rain_plus_flow", "candidate": name, **summary})
        draws.to_csv(OUT / f"paired_bootstrap_{name}.csv", index=False)
    summary, draws = paired_gain(forecasts, "plus_both", baseline="plus_pressure_change")
    comparisons.append({"baseline": "plus_pressure_change", "candidate": "plus_both", **summary})
    draws.to_csv(OUT / "paired_bootstrap_humidity_after_pressure.csv", index=False)
    pd.DataFrame(comparisons).to_csv(OUT / "incremental_gain.csv", index=False)
    ranks = within_decision_ranks(forecasts)
    ranks.to_csv(OUT / "within_decision_ranks.csv", index=False)
    within_decision_bootstrap(ranks).to_csv(OUT / "within_decision_bootstrap.csv", index=False)
    future_rain_diagnostic(forecasts, rain).to_csv(OUT / "future_rain_diagnostic.csv", index=False)

    review = pd.read_csv(core.REVIEW)
    clean_decisions, removed = prediction.exclude_reviewed_measurement_concerns(decisions, review)
    clean_forecasts = forward_predictions(attach_issue_weather(clean_decisions, weather))
    clean_scores = comparison_table(clean_forecasts)
    clean_scores.insert(0, "n_decision_windows_excluded", removed)
    clean_scores.to_csv(OUT / "measurement_clean_scores.csv", index=False)
    clean_summary, clean_draws = paired_gain(clean_forecasts, "plus_pressure_change")
    (OUT / "measurement_clean_pressure_gain.json").write_text(
        json.dumps(clean_summary, indent=2) + "\n"
    )
    clean_draws.to_csv(OUT / "measurement_clean_pressure_bootstrap.csv", index=False)
    manifest = {
        "status": "exploratory incremental weather test; not as-issued forecasting",
        "comparison": "fixed rainfall-plus-flow baseline versus pressure change, humidity, and joint block",
        "issue_clock": "weather timestamp exactly equals sixth-hour decision timestamp UTC",
        "weather_source": "held ERA5-Land reanalysis nearest catchment-centroid cell",
        "cohort": "same six-site 2-mm trigger and future coverage as script 58",
        "test_years": "2014-2025; training target windows end before the test year",
        "uncertainty": "999 paired resamples of held-out years; fixed predictions, no refitting",
        "input_sha256": {
            "rain": core.hash_file(core.DATA / "radolan_catchment_hourly.csv"),
            "discharge": core.hash_file(core.DATA / "event_study_discharge_hourly.csv"),
            "ratings": core.hash_file(core.DATA / "event_study_rating_eras.csv"),
            "weather": core.hash_file(WEATHER),
            "onset_review": core.hash_file(core.REVIEW),
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
