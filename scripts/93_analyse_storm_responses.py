#!/usr/bin/env python3
"""Three direct analyses of the shared storm-response census; retrospective, exploratory."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "storm_build", ROOT / "scripts/92_build_storm_response_catalogue.py"
)
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)
OUT = B.OUT
SEED, DRAWS = 20261015, 1999
OUTCOME = "peak_gain_72h"
EPISODE_FORCING = [
    "log_rain_total",
    "log_rain_max",
    "log_duration",
    "wet_area",
    "season_sin",
    "season_cos",
]
# Exploratory refinement after inspecting phase-mismatched pairs: retain the
# episode-only arm, but condition the main comparison on rain over its outcome.
FORCING = [*EPISODE_FORCING, "log_response_rain", "log_response_max", "log_early_rain"]
STATE = ["baseline_ratio", "landmark_ratio", "rise_6h", "log_antecedent_rain"]
LOCAL = [
    *FORCING,
    "log_antecedent_rain",
    "baseline_ratio",
    "rise_6h",
]


def add_features(rows):
    rows = rows.copy()
    for target, source in [
        ("log_rain_total", "rain_total_mm"),
        ("log_rain_max", "rain_max_mm"),
        ("log_duration", "forcing_duration_h"),
        ("log_antecedent_rain", "rain_72h_mm"),
        ("log_response_rain", "rain_response_72h_mm"),
        ("log_response_max", "rain_response_max_mm"),
        ("log_early_rain", "rain_6h_mm"),
    ]:
        rows[target] = np.log1p(rows[source])
    return rows


def year_interval(frame, value, unit="storm_id"):
    """Equal storm mass, with whole-year resampling preserving overlap and peer rows."""
    clean = frame.dropna(subset=[value])
    if clean.empty:
        return {
            "estimate": np.nan,
            "lower": np.nan,
            "upper": np.nan,
            "years": 0,
            "storms": 0,
            "draws": 0,
        }
    grouped = clean.groupby(["year", unit])[value].mean().reset_index()
    years = grouped.groupby("year")[value].agg(["sum", "count"])
    rng = np.random.default_rng(SEED)
    picks = rng.integers(0, len(years), (DRAWS, len(years)))
    estimates = years["sum"].to_numpy()[picks].sum(axis=1) / years["count"].to_numpy()[picks].sum(
        axis=1
    )
    return {
        "estimate": grouped[value].mean(),
        "lower": np.quantile(estimates, 0.025),
        "upper": np.quantile(estimates, 0.975),
        "years": len(years),
        "storms": len(grouped),
        "draws": DRAWS,
    }


def coefficient_table(frame, features, outcome, analysis):
    """OLS associations, gauge effects and whole-year bootstrap via sufficient statistics."""
    selected = frame.dropna(subset=[*features, outcome, "year", "gauge"]).copy()
    if selected.empty:
        return pd.DataFrame()
    scale = selected[features].std(ddof=0).replace(0, 1)
    x = (selected[features] - selected[features].mean()) / scale
    fixed = pd.get_dummies(selected.gauge, drop_first=True, dtype=float)
    x = np.column_stack([np.ones(len(x)), x.to_numpy(), fixed.to_numpy()])
    y = selected[outcome].to_numpy()
    # Regional storms receive equal mass irrespective of how many gauges survived.
    weights = 1 / selected.groupby("storm_id").storm_id.transform("size").to_numpy()
    years = sorted(selected.year.unique())
    cross, rhs = [], []
    for year in years:
        s = selected.year.eq(year).to_numpy()
        cross.append(x[s].T @ (x[s] * weights[s, None]))
        rhs.append(x[s].T @ (y[s] * weights[s]))
    cross, rhs = np.stack(cross), np.stack(rhs)
    beta = np.linalg.lstsq(cross.sum(axis=0), rhs.sum(axis=0), rcond=None)[0]
    rng = np.random.default_rng(SEED)
    coefficients, ranks = [], []
    for _ in range(DRAWS):
        pick = rng.integers(0, len(years), len(years))
        matrix = cross[pick].sum(axis=0)
        coefficients.append(np.linalg.lstsq(matrix, rhs[pick].sum(axis=0), rcond=None)[0])
        ranks.append(np.linalg.matrix_rank(matrix))
    coefficients = np.stack(coefficients)
    rows = []
    for i, feature in enumerate(features, 1):
        rows.append(
            {
                "analysis": analysis,
                "outcome": outcome,
                "feature": feature,
                "estimate_per_unit": beta[i] / scale.iloc[i - 1],
                "lower_per_unit": np.quantile(coefficients[:, i], 0.025) / scale.iloc[i - 1],
                "upper_per_unit": np.quantile(coefficients[:, i], 0.975) / scale.iloc[i - 1],
                "rows": len(selected),
                "storms": selected.storm_id.nunique(),
                "years": len(years),
                "matrix_columns": x.shape[1],
                "matrix_rank": np.linalg.matrix_rank(cross.sum(axis=0)),
                "rank_deficient_draws": int((np.asarray(ranks) < x.shape[1]).sum()),
                "draws": DRAWS,
            }
        )
    return pd.DataFrame(rows)


def donor_distances(query, candidates, columns):
    """Earlier-donor-only robust scales; constant features do not become huge weights."""
    a = candidates[columns].to_numpy(float)
    scale = np.quantile(a, 0.75, axis=0) - np.quantile(a, 0.25, axis=0)
    fallback = a.std(axis=0)
    scale = np.where(scale > 1e-8, scale, np.where(fallback > 1e-8, fallback, 1))
    return np.mean(((a - query[columns].to_numpy(float)) / scale) ** 2, axis=1)


def prepare_vectors(out, rows):
    history = pd.read_parquet(out / "histories_512h.parquet")
    ids = rows.loc[rows.numeric_usable & rows.history_complete, "row_id"]
    history = history.loc[ids]
    values = history.to_numpy(float)
    std = values.std(axis=1, keepdims=True)
    raw = pd.DataFrame(
        (values - values.mean(axis=1, keepdims=True)) / np.where(std > 0, std, 1),
        index=history.index,
    )
    ttm = B.load_script("70_ttm_analogue_comparison.py", "storm_ttm")
    model_files = [
        ttm.MODEL_DIR / "config.json",
        ttm.MODEL_DIR / "model.safetensors",
        ttm.CODE_ARCHIVE,
        ROOT / "scripts/70_ttm_analogue_comparison.py",
        out / "histories_512h.parquet",
        out / "storm_gauge_responses.parquet",
    ]
    fingerprints = {str(p.relative_to(ROOT)): B.sha256(p) for p in model_files}
    fingerprints["ordered_readout"] = "ordered; standardize each 512h input; fixed checkpoint"
    path, receipt = out / "storm_ttm_ordered.parquet", out / "ttm_receipt.json"
    if path.exists() and receipt.exists():
        saved = json.loads(receipt.read_text())
        if saved["inputs"] == fingerprints and saved["output"] == B.sha256(path):
            return raw, pd.read_parquet(path)
    embeddings, info = ttm.extract_embeddings(raw, pooling="ordered")
    embeddings.to_parquet(path)
    receipt.write_text(
        json.dumps(
            {
                "inputs": fingerprints,
                "output": B.sha256(path),
                "model_info": info,
                "rows": len(raw),
            },
            indent=2,
        )
        + "\n"
    )
    return raw, embeddings


def match_events(rows, raw, embeddings):
    """Same-gauge completed earlier storms; future discharge never enters distance."""
    output, donors = [], []
    for quality in [False, True]:
        eligible = rows[
            rows.numeric_usable & (~rows.measurement_concern if quality else True)
        ].dropna(subset=[*FORCING, *STATE, OUTCOME])
        for cohort in ["broad", "complete_512h"]:
            sample = eligible if cohort == "broad" else eligible[eligible.row_id.isin(raw.index)]
            for _, group in sample.groupby("gauge"):
                group = group.sort_values(["start_utc", "row_id"])
                for _, query in group.iterrows():
                    candidates = group[
                        (group.followup_end_utc < query.start_utc)
                        & (group.end_utc < query.start_utc)
                    ]
                    if candidates.empty:
                        continue
                    rain_distance = donor_distances(query, candidates, FORCING)
                    state_distance = donor_distances(query, candidates, STATE)
                    distances = {
                        "rain_episode": donor_distances(query, candidates, EPISODE_FORCING),
                        "rain": rain_distance,
                        "rain_state": (rain_distance + state_distance) / 2,
                    }
                    if cohort == "complete_512h":
                        raw_distance = (
                            (
                                raw.loc[candidates.row_id].to_numpy()
                                - raw.loc[query.row_id].to_numpy()
                            )
                            ** 2
                        ).mean(axis=1)
                        ttm_distance = (
                            (
                                embeddings.loc[candidates.row_id].to_numpy()
                                - embeddings.loc[query.row_id].to_numpy()
                            )
                            ** 2
                        ).sum(axis=1)
                        distances["rain_state_raw"] = (
                            rain_distance + state_distance + raw_distance
                        ) / 3
                        distances["rain_state_ttm"] = (
                            rain_distance + state_distance + ttm_distance
                        ) / 3
                    for arm, distance in distances.items():
                        order = np.lexsort((candidates.row_id.to_numpy(), distance))[:5]
                        selected = candidates.iloc[order]
                        prediction = selected[OUTCOME].mean()
                        keys = {
                            "query_row_id": query.row_id,
                            "storm_id": query.storm_id,
                            "year": query.year,
                            "gauge": query.gauge,
                            "cohort": cohort,
                            "quality": quality,
                            "arm": arm,
                            "footprint": query.footprint,
                            "warm": query.warm,
                        }
                        output.append(
                            {
                                **keys,
                                "donor_count": len(selected),
                                "observed": query[OUTCOME],
                                "estimate": prediction,
                                "absolute_error": abs(prediction - query[OUTCOME]),
                            }
                        )
                        for rank, (_, donor) in enumerate(selected.iterrows(), 1):
                            donors.append(
                                {
                                    **keys,
                                    "rank": rank,
                                    "donor_row_id": donor.row_id,
                                    "donor_start_utc": donor.start_utc,
                                    "donor_followup_end_utc": donor.followup_end_utc,
                                    "query_start_utc": query.start_utc,
                                    "distance": distance[order[rank - 1]],
                                    "outcome_difference": query[OUTCOME] - donor[OUTCOME],
                                    "baseline_difference": query.baseline_ratio
                                    - donor.baseline_ratio,
                                    "rise_difference": query.rise_6h - donor.rise_6h,
                                    "rain_difference_mm": query.rain_total_mm - donor.rain_total_mm,
                                }
                            )
    return pd.DataFrame(output), pd.DataFrame(donors)


def ridge_predict(train, test, features, outcome=OUTCOME):
    """Fixed penalty; training-only centering/scaling; unpenalized intercept."""
    center, scale = train[features].mean(), train[features].std(ddof=0).replace(0, 1)
    x = (train[features] - center).to_numpy() / scale.to_numpy()
    xt = (test[features] - center).to_numpy() / scale.to_numpy()
    x, xt = np.column_stack([np.ones(len(x)), x]), np.column_stack([np.ones(len(xt)), xt])
    penalty = np.eye(x.shape[1])
    penalty[0, 0] = 0
    beta = np.linalg.solve(x.T @ x + penalty, x.T @ train[outcome].to_numpy())
    return xt @ beta


def peer_relationships(rows):
    scores, ledger = [], []
    eligible = rows[rows.numeric_usable].dropna(subset=[*LOCAL, OUTCOME])
    peer_features = ["log_rain_total", "log_response_rain", "wet_area", "baseline_ratio", "rise_6h"]
    for target, target_rows in eligible.groupby("gauge"):
        for peer, peer_rows in rows[rows.peer_state_usable].groupby("gauge"):
            if peer == target:
                continue
            extra = peer_rows[["storm_id", "input_measurement_concern", *peer_features]].rename(
                columns={
                    **{c: "peer_" + c for c in peer_features},
                    "input_measurement_concern": "peer_measurement_concern",
                }
            )
            joined = target_rows.merge(extra, on="storm_id", validate="one_to_one").dropna(
                subset=["peer_" + c for c in peer_features]
            )
            for quality in [False, True]:
                sample = (
                    joined[~(joined.measurement_concern | joined.peer_measurement_concern)]
                    if quality
                    else joined
                )
                for year in sorted(sample.year.unique()):
                    if year < 2015:
                        continue
                    boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
                    train = sample[
                        (sample.year < year)
                        & (sample.followup_end_utc < boundary)
                        & (sample.end_utc < boundary)
                    ]
                    test = sample[sample.year.eq(year)]
                    ledger.append(
                        {
                            "target": target,
                            "peer": peer,
                            "quality": quality,
                            "test_year": year,
                            "train_rows": len(train),
                            "test_rows": len(test),
                            "train_last_followup": train.followup_end_utc.max(),
                            "test_first_start": test.start_utc.min(),
                        }
                    )
                    if test.empty or len(train) <= len(LOCAL) + 6:
                        continue
                    arms = {
                        "local": LOCAL,
                        "peer_rain": [*LOCAL, *["peer_" + c for c in peer_features[:3]]],
                        "peer_state": [*LOCAL, *["peer_" + c for c in peer_features]],
                    }
                    for arm, features in arms.items():
                        predicted = ridge_predict(train, test, features)
                        frame = test[
                            ["row_id", "storm_id", "year", "footprint", "warm", OUTCOME]
                        ].copy()
                        frame["target"], frame["peer"], frame["quality"], frame["arm"] = (
                            target,
                            peer,
                            quality,
                            arm,
                        )
                        frame["estimate"] = predicted
                        frame["absolute_error"] = abs(predicted - test[OUTCOME].to_numpy())
                        scores.append(frame)
    return pd.concat(scores, ignore_index=True), pd.DataFrame(ledger)


def pulse_starts(rain, separation=6):
    """A missing interval cannot establish dry separation or recovery."""
    wet = np.flatnonzero(rain.ge(0.2).to_numpy())
    starts = []
    for k, i in enumerate(wet):
        if k == 0 or i - wet[k - 1] - 1 >= separation:
            known = bool(k == 0 or rain.iloc[wet[k - 1] + 1 : i].notna().all())
            starts.append((int(i), known))
    return starts


def pulse_ledger(rows, q, rain, domain):
    pulses, flags = [], []
    for _, row in rows.iterrows():
        dates = pd.date_range(row.start_utc, row.followup_end_utc, freq="h")
        r = rain[row.gauge].reindex(dates)
        found = pulse_starts(r)
        before_flags = []
        any_repeat = False
        for rank, (i, separation_known) in enumerate(found):
            when = dates[i]
            if rank == 0 or when <= row.landmark_utc or when + 23 * B.HOUR > row.followup_end_utc:
                continue
            any_repeat = True
            previous = when - B.HOUR
            flow_before = q[row.gauge].reindex([previous]).iloc[0]
            history = q[row.gauge].loc[row.start_utc - B.HOUR : previous]
            recovery_known = bool(
                separation_known
                and r.iloc[:i].notna().all()
                and history.notna().all()
                and row.rise_6h > 0.02
                and np.isfinite(row.baseline_ratio)
            )
            before_half = (
                bool((flow_before - row.baseline_q) / row.normalizer_p99 > row.rise_6h / 2)
                if recovery_known
                else np.nan
            )
            before_flags.append(before_half)
            response_dates = pd.date_range(when, periods=24, freq="h")
            response = q[row.gauge].reindex(response_dates)
            pulse_rain = rain[row.gauge].reindex(response_dates)
            valid = bool(
                domain[row.gauge]
                .reindex(pd.date_range(previous, response_dates[-1], freq="h"))
                .fillna(False)
                .all()
            )
            pulses.append(
                {
                    "row_id": row.row_id,
                    "storm_id": row.storm_id,
                    "year": row.year,
                    "gauge": row.gauge,
                    "pulse_start_utc": when,
                    "pulse_hour": i,
                    "recovery_known": recovery_known,
                    "before_half_recovery": before_half,
                    "pulse_q_before_ratio": flow_before / row.normalizer_p99,
                    "initial_rise": row.rise_6h,
                    "log_pulse_rain": np.log1p(B.sum_complete(pulse_rain)),
                    "log_pulse_max": np.log1p(pulse_rain.max())
                    if pulse_rain.notna().all()
                    else np.nan,
                    "rise_next24h": (response.max() - flow_before) / row.normalizer_p99
                    if response.notna().all() and valid
                    else np.nan,
                    "season_sin": row.season_sin,
                    "season_cos": row.season_cos,
                    "measurement_concern": row.measurement_concern,
                    "numeric_usable": row.numeric_usable and valid,
                }
            )
        known = bool(
            row.rise_6h > 0.02
            and r.notna().all()
            and (not any_repeat or all(pd.notna(x) for x in before_flags))
        )
        flags.append(
            {
                "row_id": row.row_id,
                "repeat_recovery_known": known,
                "repeat_before_recovery": float(any(x is True for x in before_flags))
                if known
                else np.nan,
                "any_repeat_pulse": any_repeat,
            }
        )
    return pd.DataFrame(pulses), rows.merge(pd.DataFrame(flags), on="row_id", validate="one_to_one")


def summaries(matches, peers, out):
    comparisons = []
    for keys, frame in matches.groupby(["cohort", "quality"]):
        base = frame[frame.arm.eq("rain")].set_index("query_row_id")
        for arm, part in frame.groupby("arm"):
            if arm == "rain":
                continue
            part = part.set_index("query_row_id").loc[base.index]
            contrast = part[["storm_id", "year"]].copy()
            contrast["difference"] = part.absolute_error - base.absolute_error
            comparisons.append(
                {
                    "kind": "event_matching",
                    "cohort": keys[0],
                    "quality": keys[1],
                    "reference": "rain",
                    "challenger": arm,
                    **year_interval(contrast, "difference"),
                }
            )
        if keys[0] == "complete_512h":
            base = frame[frame.arm.eq("rain_state_raw")].set_index("query_row_id")
            part = frame[frame.arm.eq("rain_state_ttm")].set_index("query_row_id").loc[base.index]
            contrast = part[["storm_id", "year"]].copy()
            contrast["difference"] = part.absolute_error - base.absolute_error
            comparisons.append(
                {
                    "kind": "event_matching",
                    "cohort": keys[0],
                    "quality": keys[1],
                    "reference": "rain_state_raw",
                    "challenger": "rain_state_ttm",
                    **year_interval(contrast, "difference"),
                }
            )
    pair_contrasts = []
    for keys, frame in peers.groupby(["target", "peer", "quality"]):
        base = frame[frame.arm.eq("peer_rain")].set_index("row_id")
        part = frame[frame.arm.eq("peer_state")].set_index("row_id").loc[base.index]
        contrast = part[["storm_id", "year", "footprint", "warm"]].copy()
        contrast["difference"] = part.absolute_error - base.absolute_error
        contrast["base_error"] = base.absolute_error
        contrast["peer_error"] = part.absolute_error
        contrast["target"], contrast["peer"], contrast["quality"] = keys
        pair_contrasts.append(contrast.reset_index())
        groups = (
            [("all", contrast)]
            + [(f"footprint:{k}", x) for k, x in contrast.groupby("footprint")]
            + [(f"warm:{k}", x) for k, x in contrast.groupby("warm")]
        )
        for regime, subset in groups:
            comparisons.append(
                {
                    "kind": "peer_increment",
                    "target": keys[0],
                    "peer": keys[1],
                    "quality": keys[2],
                    "regime": regime,
                    "reference": "peer_rain",
                    "challenger": "peer_state",
                    **year_interval(subset, "difference"),
                }
            )
    intervals = pd.DataFrame(comparisons)
    intervals.to_csv(out / "paired_intervals.csv", index=False)
    contrasts = pd.concat(pair_contrasts, ignore_index=True)
    contrasts.to_csv(out / "peer_event_contrasts.csv", index=False)
    matches.groupby(["cohort", "quality", "arm"]).agg(
        rows=("query_row_id", "size"),
        storms=("storm_id", "nunique"),
        mae=("absolute_error", "mean"),
        mean_donors=("donor_count", "mean"),
    ).to_csv(out / "matching_summary.csv")
    # Average within storm before aggregating pairs; 56 pairs are not 56 independent rivers.
    pooled = (
        contrasts.groupby(["quality", "storm_id", "year", "footprint", "warm"])
        .difference.mean()
        .reset_index()
    )
    combined = []
    for quality, g in pooled.groupby("quality"):
        for regime, subset in [
            ("all", g),
            *[(f"footprint:{k}", x) for k, x in g.groupby("footprint")],
        ]:
            combined.append(
                {"quality": quality, "regime": regime, **year_interval(subset, "difference")}
            )
    pd.DataFrame(combined).to_csv(out / "peer_pooled_intervals.csv", index=False)
    return intervals


def case_outputs(rows, matches, donors, out):
    """All matched cases in a browser; predeclared calendar examples in static plots."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    main = matches[(matches.cohort == "complete_512h") & ~matches.quality]
    frame = main.pivot(index="query_row_id", columns="arm", values="absolute_error")
    frame = rows.set_index("row_id").join(frame, how="inner")
    frame["state_minus_rain_error"] = frame.rain_state - frame.rain
    frame["ttm_minus_raw_error"] = frame.rain_state_ttm - frame.rain_state_raw
    frame.to_csv(out / "event_divergence_cases.csv")
    q = pd.read_parquet(out / "hourly_discharge.parquet")
    rain = pd.read_parquet(out / "hourly_rainfall.parquet")
    curves = {}
    for row in rows.itertuples():
        dates = pd.date_range(row.start_utc - B.HOUR, row.followup_end_utc, freq="h")
        curves[row.row_id] = {
            "q": (q[row.gauge].reindex(dates) / row.normalizer_p99).round(5).tolist(),
            "rain": rain[row.gauge].reindex(dates).round(3).tolist(),
        }
    variants = {}
    main_donors = donors[donors.cohort.eq("complete_512h") & ~donors.quality]
    for (query, arm), d in main_donors.groupby(["query_row_id", "arm"]):
        variants.setdefault(query, {})[arm] = d.sort_values("rank").donor_row_id.tolist()
    # pandas converts nonfinite values to JSON null; missing points are not drawn as zero.
    payload = json.dumps(
        {
            "cases": json.loads(frame.reset_index().to_json(orient="records", date_format="iso")),
            "curves": json.loads(pd.Series(curves).to_json()),
            "variants": variants,
        },
        allow_nan=False,
    )
    html = """<!doctype html><meta charset="utf-8"><title>Limburg storm comparisons</title><style>body{font:16px system-ui;max-width:1050px;margin:30px auto}select{padding:8px;max-width:100%}pre{white-space:pre-wrap}canvas{width:100%;border:1px solid #ddd}</style><h1>Storm-response comparisons</h1><p>All complete-history matched cases. Black: observed query; blue: completed earlier storms on the same gauge. Each curve uses its own era-p99. Dashed line: six-hour landmark. Realized rain informs retrieval; these are retrospective comparisons, not forecasts. Human review has not been performed.</p><select id="e"></select><select id="a"></select><canvas id="q" width="1050" height="330"></canvas><canvas id="r" width="1050" height="250"></canvas><pre id="facts"></pre><script>const data=PAYLOAD;const e=document.getElementById('e'),a=document.getElementById('a');data.cases.forEach((x,i)=>e.add(new Option(x.row_id+' — '+x.station,i)));function choose(){a.innerHTML='';Object.keys(data.variants[data.cases[e.value].row_id]).forEach(k=>a.add(new Option(k,k)));show()}function show(){const x=data.cases[e.value],ids=data.variants[x.row_id][a.value];function draw(id,key,label){const c=document.getElementById(id),ctx=c.getContext('2d'),all=[...ids,x.row_id];ctx.clearRect(0,0,c.width,c.height);const max=Math.max(0.01,...all.flatMap(k=>data.curves[k][key]).filter(z=>z!==null))*1.1;ctx.fillText(label+'; upper axis '+max.toFixed(2),45,17);all.forEach(k=>{ctx.strokeStyle=k===x.row_id?'black':'#7497bd';ctx.lineWidth=k===x.row_id?3:1;ctx.beginPath();let connected=false;data.curves[k][key].forEach((v,i)=>{if(v===null){connected=false;return}const xx=45+i/78*975,yy=c.height-30-v/max*(c.height-65);connected?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy);connected=true});ctx.stroke()});ctx.setLineDash([4,4]);ctx.strokeStyle='#b66b00';ctx.beginPath();ctx.moveTo(45+6/78*975,25);ctx.lineTo(45+6/78*975,c.height-30);ctx.stroke();ctx.setLineDash([]);ctx.fillText('Hours from first rainfall: −1 to +77',380,c.height-8)}draw('q','q','Discharge / era-p99');draw('r','rain','Catchment rainfall (mm/h)');document.getElementById('facts').textContent='Selected donor IDs:\\n'+ids.join('\\n')+'\\n\\n'+JSON.stringify(x,null,2)}e.onchange=choose;a.onchange=show;choose();</script>"""
    (out / "case_browser.html").write_text(html.replace("PAYLOAD", payload.replace("<", "\\u003c")))
    # Calendar-selected July anchors, plus one storm per year independent of Q severity.
    selected = (
        rows[
            (rows.start_utc.dt.month == 7)
            & rows.start_utc.dt.day.between(12, 16)
            & rows.year.eq(2021)
        ]
        .storm_id.unique()
        .tolist()
    )
    selected += rows.sort_values("start_utc").drop_duplicates("year").storm_id.tolist()
    figures = out / "figures"
    figures.mkdir(exist_ok=True)
    for index, storm_id in enumerate(dict.fromkeys(selected)):
        block = rows[rows.storm_id.eq(storm_id)]
        start, end = block.start_utc.iloc[0] - 24 * B.HOUR, block.followup_end_utc.iloc[0]
        fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        for site in block.itertuples():
            axes[0].plot(
                q.loc[start:end].index,
                q.loc[start:end, site.gauge] / site.normalizer_p99,
                label=site.station,
            )
            axes[1].plot(rain.loc[start:end].index, rain.loc[start:end, site.gauge], alpha=0.7)
        axes[0].axvline(block.landmark_utc.iloc[0], color="black", linestyle="--")
        axes[0].set_ylabel("Q / full-era p99")
        axes[1].set_ylabel("Catchment rain (mm/h)")
        axes[0].legend(fontsize=7, ncol=4)
        axes[0].set_title(f"{storm_id} — observed; flagged values shown, not certified exact")
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(figures / f"storm_{index:02d}.png", dpi=130)
        plt.close(fig)
    # Outcome-selected illustrations from the first case inspection, explicitly
    # retained as diagnostics rather than independent validation examples.
    illustrations = [
        ("11.Q.32", "2023-06-22", "2020-06-26"),
        ("15.Q.41", "2024-05-15", "2022-06-08"),
        ("11.Q.32", "2020-03-10", "2019-02-09"),
    ]
    case_rows = []
    for number, (gauge, query_day, donor_day) in enumerate(illustrations):
        query = rows[rows.gauge.eq(gauge) & rows.start_utc.dt.strftime("%Y-%m-%d").eq(query_day)]
        donor = rows[rows.gauge.eq(gauge) & rows.start_utc.dt.strftime("%Y-%m-%d").eq(donor_day)]
        if len(query) != 1 or len(donor) != 1:
            case_rows.append(
                {
                    "case": number,
                    "status": "regional episode date changed under segmentation",
                    "gauge": gauge,
                }
            )
            continue
        fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        for role, part, color in [
            ("query", query.iloc[0], "black"),
            ("earlier comparison", donor.iloc[0], "#5284b8"),
        ]:
            curve = curves[part.row_id]
            hours = np.arange(-1, 78)
            axes[0].plot(hours, curve["q"], label=f"{role}: {part.start_utc.date()}", color=color)
            axes[1].plot(hours, curve["rain"], color=color)
            case_rows.append(
                {
                    "case": number,
                    "status": "outcome-selected diagnostic",
                    "role": role,
                    "row_id": part.row_id,
                    "gauge": gauge,
                    "rain_episode_mm": part.rain_total_mm,
                    "rain_first6h_mm": part.rain_6h_mm,
                    "rain_next72h_mm": part.rain_response_72h_mm,
                    "baseline_ratio": part.baseline_ratio,
                    "rise_6h": part.rise_6h,
                    "later_peak_gain": part.peak_gain_72h,
                    "measurement_concern": part.measurement_concern,
                }
            )
        for ax in axes:
            ax.axvline(5, color="#b66b00", linestyle="--")
        axes[0].set(
            ylabel="Q / own era-p99",
            title=f"{query.iloc[0].station}: episode similarity can hide rainfall timing",
        )
        axes[0].legend()
        axes[1].set(
            xlabel="Hours since first regional wet hour (line: 6h landmark)",
            ylabel="Catchment rain (mm/h)",
        )
        fig.tight_layout()
        fig.savefig(figures / f"diagnostic_pair_{number}.png", dpi=140)
        plt.close(fig)
    pd.DataFrame(case_rows).to_csv(out / "illustrative_pair_evidence.csv", index=False)
    # Population display accompanies the event examples.
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, part in rows[rows.numeric_usable].groupby("watercourse"):
        ax.scatter(part.baseline_ratio, part[OUTCOME], s=5, alpha=0.25, label=name)
    ax.set(xlabel="Pre-rain Q / era-p99", ylabel="Subsequent 72h peak minus 6h landmark, / era-p99")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(figures / "census_state_response.png", dpi=130)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    rows = add_features(pd.read_parquet(out / "storm_gauge_responses.parquet"))
    raw, embeddings = prepare_vectors(out, rows)
    print(f"Frozen TTM vectors ready: {len(embeddings)} histories", flush=True)
    matches, donors = match_events(rows, raw, embeddings)
    matches.to_csv(out / "matched_event_results.csv", index=False)
    donors.to_parquet(out / "matched_event_donors.parquet", index=False)
    print(f"Event contrasts complete: {len(matches)} assessments", flush=True)
    peers, folds = peer_relationships(rows)
    peers.to_parquet(out / "peer_predictions.parquet", index=False)
    folds.to_csv(out / "peer_folds.csv", index=False)
    summaries(matches, peers, out)
    print(f"Peer relationships complete: {len(peers)} matched conditional hindcasts", flush=True)
    pulses, enriched = pulse_ledger(
        rows,
        pd.read_parquet(out / "hourly_discharge.parquet"),
        pd.read_parquet(out / "hourly_rainfall.parquet"),
        pd.read_parquet(out / "hourly_domain.parquet"),
    )
    pulses.to_csv(out / "repeat_pulses.csv", index=False)
    enriched.to_parquet(out / "storm_response_analysis.parquet", index=False)
    coefficients = []
    for quality in [False, True]:
        usable = enriched[
            enriched.numeric_usable & (~enriched.measurement_concern if quality else True)
        ]
        coefficients.append(
            coefficient_table(usable, LOCAL, OUTCOME, f"state_association_quality:{quality}")
        )
        coefficients.append(
            coefficient_table(
                usable[usable.repeat_recovery_known],
                [*LOCAL, "repeat_before_recovery"],
                OUTCOME,
                f"repeat_storm_quality:{quality}",
            )
        )
        p = pulses[
            pulses.numeric_usable
            & pulses.recovery_known
            & (~pulses.measurement_concern if quality else True)
        ].copy()
        p["before_half_recovery"] = p.before_half_recovery.astype(float)
        coefficients.append(
            coefficient_table(
                p,
                [
                    "before_half_recovery",
                    "pulse_q_before_ratio",
                    "initial_rise",
                    "log_pulse_rain",
                    "log_pulse_max",
                    "season_sin",
                    "season_cos",
                ],
                "rise_next24h",
                f"repeat_pulse_quality:{quality}",
            )
        )
    pd.concat(coefficients, ignore_index=True).to_csv(
        out / "conditional_coefficients.csv", index=False
    )
    case_outputs(rows, matches, donors, out)
    paths = [
        Path(__file__),
        ROOT / "scripts/92_build_storm_response_catalogue.py",
        out / "catalogue_manifest.json",
        out / "ttm_receipt.json",
    ]
    manifest = {
        "status": "three storm-response analyses executed; exploratory retrospective",
        "seed": SEED,
        "year_draws": DRAWS,
        "counts": {
            "storms": rows.storm_id.nunique(),
            "gauge_rows": len(rows),
            "numeric_rows": int(rows.numeric_usable.sum()),
            "matches": len(matches),
            "peer_scores": len(peers),
            "repeat_pulses": len(pulses),
        },
        "input_sha256": {str(p.relative_to(ROOT)): B.sha256(p) for p in paths},
        "output_sha256": {
            p.name: B.sha256(p)
            for p in out.iterdir()
            if p.suffix in {".csv", ".parquet"}
            and not p.name.startswith(("hourly_", "spatial_", "histories_", "storm_ttm"))
        },
    }
    (out / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
