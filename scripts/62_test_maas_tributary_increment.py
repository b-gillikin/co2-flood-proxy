"""Exploratory information-value pilot: tributaries and later Venlo high water.

Retrospectively verified data make this a research diagnostic, not an as-issued
operational forecast evaluation. No feature/model search is performed. Outputs
are internal research aids, not manuscript text.
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
DATA = ROOT / "data/interim"
RAW = ROOT / "data/raw/discharge/rws"
OUT = ROOT / "results/event_study/maas_tributary_increment_v1"
YEARS = range(2017, 2025)
FIRST_TEST_YEAR = 2020
VALID_CODES = {"00"}  # strict measured/ordinary-value primary; exclude interpolated 25
BASE = ("sint_pieter_over_p90", "sint_pieter_rise_6h", "sint_pieter_rise_24h",
        "log1p_regional_rain_6h", "n_rain_sites_2mm_6h", "warm")
ADDED = (*BASE, "n_tributaries_above_p90", "max_tributary_percentile")

spec = spec_from_file_location("cross_tributary", ROOT / "scripts/53_cross_tributary_rain_episodes.py")
core = module_from_spec(spec)
spec.loader.exec_module(core)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_rws_hourly(site, min_high_frequency_block_readings=10000):
    """Use controlled code-00 F103 readings; retain full source-code QA."""
    rows, counts, paths = [], [], []
    for year in YEARS:
        path = RAW / f"{site}_{year}.json"
        paths.append(path)
        source = json.loads(path.read_text())
        quality = {}
        accepted = 0
        for block in source["WaarnemingenLijst"]:
            method = block["AquoMetadata"]["WaardeBepalingsMethode"]["Code"]
            processing = block["AquoMetadata"]["WaardeBewerkingsMethode"]["Code"]
            for observation in block["MetingenLijst"]:
                meta = observation["WaarnemingMetadata"]
                code, status = meta["Kwaliteitswaardecode"], meta["Statuswaarde"]
                key = f"{method}|{processing}|{code}|{status}"
                quality[key] = quality.get(key, 0) + 1
                if (method != "other:F103" or processing != "NVT"
                        or len(block["MetingenLijst"]) < min_high_frequency_block_readings
                        or status != "Gecontroleerd" or code not in VALID_CODES):
                    continue
                value = observation["Meetwaarde"].get("Waarde_Numeriek")
                if value is None or not np.isfinite(value) or value < 0 or value > 10000:
                    continue
                rows.append((observation["Tijdstip"], float(value)))
                accepted += 1
        counts.append({"site": site, "year": year, "accepted_readings": accepted,
                       "all_code_counts": json.dumps(quality, sort_keys=True)})
    raw = pd.DataFrame(rows, columns=["timestamp", "q"])
    raw["timestamp"] = pd.to_datetime(raw.timestamp, utc=True)
    repeated = raw.loc[raw.timestamp.duplicated(keep=False)]
    if repeated.groupby("timestamp").q.nunique().gt(1).any():
        raise ValueError(f"Conflicting accepted timestamps for {site}")
    raw = raw.drop_duplicates("timestamp")  # adjacent annual API files share one endpoint
    raw["hour_end"] = raw.timestamp.dt.ceil("h")
    grouped = raw.groupby("hour_end").q.agg(["mean", "count"])
    # At least four of six nominal 10-minute readings in the preceding hour.
    hourly = grouped["mean"].where(grouped["count"].ge(4))
    index = pd.date_range(f"{YEARS.start}-01-01", f"{YEARS.stop}-01-01", freq="h", tz="UTC")
    hourly = hourly.reindex(index)
    return hourly, pd.DataFrame(counts), paths


def make_decisions(rain, tributaries, upstream, downstream, target_quantile=0.90):
    """Start at rain-spell hour six, update daily during rain; one Venlo target."""
    both = upstream.index.intersection(downstream.index).intersection(rain.index)
    rain, upstream, downstream = rain.loc[both], upstream.loc[both], downstream.loc[both]
    # Freeze scaling on 2017-2019; forward test years cannot set thresholds.
    calibration = both.year < FIRST_TEST_YEAR
    up_p90 = upstream.loc[calibration].quantile(.90)
    target = downstream.loc[calibration].quantile(target_quantile)
    rank = {}
    for site in core.SITES:
        series = tributaries[site].loc[both]
        valid = np.sort(series.loc[series.valid & series.q.notna() & calibration, "q"].to_numpy())
        percentile = pd.Series(np.searchsorted(valid, series.q.to_numpy(), side="right") / len(valid),
                               index=series.index).where(series.q.notna())
        rank[site] = percentile.where(series.valid)
    rank = pd.DataFrame(rank)
    rows = []
    wet = np.flatnonzero(rain.max(axis=1).ge(.2).to_numpy())
    if len(wet):
        breaks = np.r_[0, np.flatnonzero(np.diff(wet) > 12) + 1, len(wet)]
        storm_windows = [(int(wet[a]), int(wet[b - 1])) for a, b in zip(breaks[:-1], breaks[1:])]
    else:
        storm_windows = []
    issue_positions = [(start, issue) for start, stop in storm_windows
                       for issue in range(start + 5, stop + 1, 24)]
    for start, issue in issue_positions:
        end = issue + 72
        if end >= len(rain):
            continue
        time = rain.index[issue]
        r = rain.iloc[issue - 5:issue + 1]
        if r.isna().any().any():
            continue
        totals = r.sum()
        if totals.max() < 2:
            continue
        # Lag upstream and tributary information one full hour so centered
        # 10-minute averages cannot carry post-issue flow into predictors.
        past = issue - 1
        if past < 24 or upstream.iloc[[past, past - 6, past - 24]].isna().any():
            continue
        state = rank.iloc[past]
        if state.isna().any():
            continue
        if pd.isna(downstream.iloc[issue]) or downstream.iloc[issue] >= target:
            continue
        future = downstream.iloc[issue + 1:end + 1]
        if future.isna().any():
            continue  # prevent unobserved high water from becoming a negative
        rows.append({
            "rain_start_utc": rain.index[start], "issue_utc": time,
            "target_end_utc": rain.index[end], "year": time.year,
            "high_venlo_next_72h": int(future.ge(target).any()),
            "sint_pieter_over_p90": upstream.iloc[past] / up_p90,
            "sint_pieter_rise_6h": (upstream.iloc[past] - upstream.iloc[past - 6]) / up_p90,
            "sint_pieter_rise_24h": (upstream.iloc[past] - upstream.iloc[past - 24]) / up_p90,
            "log1p_regional_rain_6h": np.log1p(totals.max()),
            "n_rain_sites_2mm_6h": int(totals.ge(2).sum()),
            "warm": int(5 <= time.month <= 10),
            "n_tributaries_above_p90": int(state.ge(.90).sum()),
            "max_tributary_percentile": float(state.max()),
        })
    return pd.DataFrame(rows), {"calibration_years": [2017, 2018, 2019],
                                "sint_pieter_p90_m3s": float(up_p90),
                                "venlo_target_quantile": target_quantile,
                                "venlo_target_m3s": float(target)}


def forward_predictions(frame):
    outputs = []
    for year in range(FIRST_TEST_YEAR, YEARS.stop):
        train = frame.loc[frame.year.lt(year) & frame.target_end_utc.lt(pd.Timestamp(f"{year}-01-01", tz="UTC"))]
        test = frame.loc[frame.year.eq(year)].copy()
        if len(test) == 0 or train.high_venlo_next_72h.nunique() < 2:
            continue
        test["p_climatology"] = train.high_venlo_next_72h.mean()
        for label, features in [("base", BASE), ("plus_tributaries", ADDED)]:
            model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=1000))
            model.fit(train[list(features)], train.high_venlo_next_72h)
            test[f"p_{label}"] = model.predict_proba(test[list(features)])[:, 1]
        outputs.append(test)
    return pd.concat(outputs, ignore_index=True) if outputs else pd.DataFrame()


def score(frame):
    y = frame.high_venlo_next_72h.to_numpy()
    result = []
    for label in ("climatology", "base", "plus_tributaries"):
        p = frame[f"p_{label}"].to_numpy()
        result.append({"model": label, "n_decisions": len(frame), "n_positive": int(y.sum()),
                       "brier": brier_score_loss(y, p), "log_loss": log_loss(y, p),
                       "average_precision": average_precision_score(y, p),
                       "roc_auc": roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan})
    return pd.DataFrame(result)


def bootstrap(predictions, draws=999, seed=20261004):
    years = predictions.year.unique()
    groups = {year: predictions.loc[predictions.year.eq(year)] for year in years}
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(draws + 1):
        selected = years if i == 0 else rng.choice(years, len(years), replace=True)
        sample = pd.concat([groups[year] for year in selected], ignore_index=True)
        scores = score(sample).set_index("model")
        base, added = scores.loc["base"], scores.loc["plus_tributaries"]
        rows.append({"draw": i, "n_positive": int(sample.high_venlo_next_72h.sum()),
                     "brier_improvement": base.brier - added.brier,
                     "log_loss_improvement": base.log_loss - added.log_loss,
                     "average_precision_gain": added.average_precision - base.average_precision,
                     "roc_auc_gain": added.roc_auc - base.roc_auc})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    upstream, upstream_qa, up_paths = clean_rws_hourly("maastricht.sintpieter")
    downstream, downstream_qa, down_paths = clean_rws_hourly("venlo")
    pd.concat([upstream_qa, downstream_qa]).to_csv(OUT / "rws_quality_codes_by_year.csv", index=False)
    pd.DataFrame({"sint_pieter": upstream, "venlo": downstream}).to_csv(OUT / "clean_rws_hourly.csv", index_label="hour_end_utc")
    rain_path = DATA / "radolan_catchment_hourly.csv"
    flow_path = DATA / "event_study_discharge_hourly.csv"
    ratings_path = DATA / "event_study_rating_eras.csv"
    rain = core.read_hourly(rain_path)[list(core.SITES)]
    flow = core.read_hourly(flow_path)
    tributaries = core.site_states(flow, pd.read_csv(ratings_path))
    frame, thresholds = make_decisions(rain, tributaries, upstream, downstream)
    if frame.empty:
        raise ValueError("No eligible decisions")
    frame.to_csv(OUT / "decisions.csv", index=False)
    predictions = forward_predictions(frame)
    if predictions.empty:
        raise ValueError("No forward-year model evaluation possible")
    predictions.to_csv(OUT / "forward_predictions.csv", index=False)
    score(predictions).to_csv(OUT / "scores.csv", index=False)
    bootstrap(predictions).to_csv(OUT / "year_bootstrap.csv", index=False)
    manifest = {"purpose": "exploratory retrospective information-value test",
                "years": list(YEARS), "first_test_year": FIRST_TEST_YEAR,
                "accepted_rws_quality_codes": sorted(VALID_CODES),
                "analysis_script_sha256": sha256(Path(__file__)),
                "first_issue_hours_after_rain_start": 6,
                "repeat_issue_interval_hours_during_storm": 24,
                "horizon_hours": 72,
                "minimum_future_target_coverage": 1.0, "bootstrap_seed": 20261004,
                "thresholds": thresholds, "inputs_sha256": {str(p.relative_to(ROOT)): sha256(p)
                    for p in [*up_paths, *down_paths, rain_path, flow_path, ratings_path]},
                "limitations": ["retrospectively verified flow",
                    "regional rainfall trigger from held RADOLAN", "not an operational forecast replay"]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(score(predictions).to_string(index=False))
    print("decisions_by_year", frame.groupby("year").high_venlo_next_72h.agg(["count", "sum"]).to_dict("index"))


if __name__ == "__main__":
    main()
