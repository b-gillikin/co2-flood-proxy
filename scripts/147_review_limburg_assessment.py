"""Synthesize completed evidence and report the new archive/Meuse comparisons."""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import load_script
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import fresh_output

OUT = ROOT / "results/limburg_assessment_2026_10_27"


def evidence_map():
    base = "docs/"
    return [
        dict(
            claim_id=cid,
            question=q,
            finding=f,
            population=p,
            source=base + s,
            development_status="exploratory; chronology preserved",
            limitation=limit,
        )
        for cid, q, f, p, s, limit in [
            (
                "E01",
                "Does matching help?",
                "Conventional/raw matching improves individual shape over generic archive.",
                "Final matched NL/DE EO populations",
                "limburg-findings-consolidated-2026-10-27.md",
                "Trajectory estimation is a distinct endpoint.",
            ),
            (
                "E02",
                "Does TTM add information?",
                "Modest TTM individual-shape increment over raw/state.",
                "610 NL / 235 DE broad Q-history queries",
                "limburg-findings-consolidated-2026-10-27.md",
                "Peak/curve gains less consistent.",
            ),
            (
                "E03",
                "Does EO add information?",
                "AnySat has a conditional DE snapshot curve/severity benefit.",
                "111 DE shared snapshot queries plus own-available sensitivity",
                "limburg-findings-consolidated-2026-10-27.md",
                "Two gauges on one river; exploratory multi-comparison result.",
            ),
            (
                "E04",
                "Are all model gains stable?",
                "Several attractive EO gains weaken on larger application populations.",
                "All-ten intersections versus each model-available cohort",
                "limburg-findings-consolidated-2026-10-27.md",
                "Population differences alone do not identify an archive effect.",
            ),
            (
                "E05",
                "Do analogues improve distributions?",
                "Five-donor TTM has no clear increment; ten-donor gains over archive are also achievable conventionally.",
                "845 Q / 764 earlier rainfall / 365 annual-context queries",
                "limburg-analogue-distribution-results-2026-10-15.md",
                "Not final all-ten EO distributional verification; earlier rainfall support.",
            ),
            (
                "E06",
                "Does AlphaEarth help?",
                "Selective timing evidence; no consistent general shape/curve increment.",
                "294 NL / 71 DE annual-context cohort",
                "limburg-findings-consolidated-2026-10-27.md",
                "Landscape descriptors do not observe hourly wetness.",
            ),
            (
                "E07",
                "Do storms explain divergence?",
                "Local phase and subsequent forcing can defeat a similar storm-total match.",
                "468 rainfall episodes, 8 NL/DE gauges",
                "limburg-storm-response-results-2026-10-15.md",
                "Realized future rainfall used for explanation; not forecast skill.",
            ),
            (
                "E08",
                "Do peer gauges help?",
                "No robust general peer-state increment after rainfall/local-state controls.",
                "56 directed gauge pairs",
                "limburg-storm-response-results-2026-10-15.md",
                "No causal routing or national-treatment inference.",
            ),
            (
                "E09",
                "Do repeat pulses explain escalation?",
                "Recovery association is segmentation-sensitive and does not establish a stable mechanism.",
                "2254 known-state pulses / 338 storms",
                "limburg-storm-response-results-2026-10-15.md",
                "Pulse order and algebraic coupling limit interpretation.",
            ),
            (
                "E10",
                "Why do severe cases fail?",
                "Archive support, retrieval, extreme members, averaging and window anchoring fail in distinct ways.",
                "15 register rows / 7 core H3 cases / 2 scored pre-flood queries",
                "limburg-flood-case-review-2026-10-27.md",
                "Case diagnosis is not independent population verification.",
            ),
            (
                "E11",
                "What is basin context?",
                "Sint Pieter/Venlo show wider-basin states and contrasting trends.",
                "1062 held tributary events",
                "limburg-meuse-context-2026-10-27.md",
                "Observed context alone does not demonstrate incremental retrieval value.",
            ),
            (
                "E12",
                "What is the FEWS/DRR contribution?",
                "Quality and limits of historical evidence for interpreting developing high water.",
                "Retrospective study, source-specific thresholds and measurement provenance",
                "reviews/limburg-analogue-question-literature-reassessment-2026-10-27.md",
                "Operator benefit, impacts and as-issued warning skill not established.",
            ),
        ]
    ]


def quantified_evidence():
    effects = {
        "E02": {
            "NL_shape_difference": -0.00407,
            "NL_storm_interval": [-0.00706, -0.00120],
            "DE_shape_difference": -0.00543,
            "DE_storm_interval": [-0.01078, -0.00049],
        },
        "E03": {
            "DE_snapshot_curve_reference": 0.3009,
            "challenger": 0.2674,
            "difference": -0.03350,
            "storm_interval": [-0.05038, -0.01728],
            "year_interval": [-0.05602, -0.01026],
        },
        "E04": {
            "Copernicus_shared_difference": -0.02023,
            "Copernicus_own_population_difference": 0.00264,
            "CROMA_shared_difference": -0.02835,
            "CROMA_own_population_difference": -0.00408,
        },
        "E05": {
            "five_donor_TTM_CRPS": 0.27503,
            "Q_archive_CRPS": 0.26892,
            "ten_donor_TTM_CRPS": 0.25399,
            "ten_donor_raw_state_CRPS": 0.25771,
            "ten_donor_conventional_CRPS_other_cohort": 0.24765,
        },
        "E06": {"NL_peak_time_mismatch_difference_h": -0.92, "storm_interval": [-1.79, -0.06]},
        "E07": {
            "episode_minus_response_window_rain_error": 0.03762,
            "year_interval": [0.02779, 0.04718],
        },
        "E08": {"added_peer_state_error": 0.00536, "year_interval": [0.00258, 0.00849]},
        "E09": {"postpulse_rise_association": -0.02771, "year_interval": [-0.08696, 0.02697]},
        "E10": {"register_rows": 15, "core_H3_cases": 7, "scored_preflood_queries": 2},
        "E11": {
            "inventory_events": 1062,
            "Sint_Pieter_strict_cutoff": 931,
            "Venlo_strict_cutoff": 613,
        },
    }
    rows = evidence_map()
    for row in rows:
        row["quantitative_anchor"] = json.dumps(effects.get(row["claim_id"], {}))
        row["full_estimates_and_sensitivities"] = (
            "results/limburg_findings_consolidation_2026_10_27/contrasts.parquet"
            if row["claim_id"] in {"E01", "E02", "E03", "E04", "E06"}
            else row["source"]
        )
    return rows


def folder_tags(name):
    for setting in ["other_rivers", "quality", "main"]:
        if name.endswith("_" + setting):
            return name[: -(len(setting) + 1)], setting
    raise ValueError(name)


def fallback_and_ledger(run):
    pairs = []
    ledger = []
    intervals = []
    meta = run.meta
    broad = set(run.sample.event_id)
    for eid, r in meta.iterrows():
        ledger.append(
            dict(
                module="baseline",
                context="q",
                event_id=eid,
                country=r.country,
                watercourse=r.watercourse,
                year=r.onset_utc.year,
                base_eligible=eid in broad,
                population_eligible=eid in broad,
                reason="eligible" if eid in broad else "outside_declared_history_outcome_cohort",
            )
        )
    for path in (OUT / "archive").glob("*/population.parquet"):
        family, kind = path.parent.name.split("_", 1)
        ids = pd.read_parquet(path)
        base = set(run.full[family].event_id)
        for model, g in ids.groupby("model"):
            support = set(g.event_id)
            for eid, r in meta.iterrows():
                ledger.append(
                    dict(
                        module="eo",
                        context=f"{family}:{kind}:{model}",
                        event_id=eid,
                        country=r.country,
                        watercourse=r.watercourse,
                        year=r.onset_utc.year,
                        base_eligible=eid in base,
                        population_eligible=eid in support,
                        reason="outside_declared_history_outcome_cohort"
                        if eid not in base
                        else ("eligible" if eid in support else "missing_representation"),
                    )
                )
    for folder in sorted((OUT / "meuse").iterdir()):
        context, setting = folder_tags(folder.name)
        f = pd.read_parquet(folder / "scores.parquet")
        full = pd.read_parquet(OUT / "baselines" / f"rain_{setting}" / "scores.parquet")
        features = run.config["context_features"][context]
        complete = set(run.context[features].dropna().index)
        if setting == "main":
            base = set(run.full["rain"].event_id)
            for eid, r in meta.iterrows():
                ledger.append(
                    dict(
                        module="meuse",
                        context=context,
                        event_id=eid,
                        country=r.country,
                        watercourse=r.watercourse,
                        year=r.onset_utc.year,
                        base_eligible=eid in base,
                        population_eligible=eid in base and eid in complete,
                        reason="outside_declared_history_outcome_cohort"
                        if eid not in base
                        else (
                            "eligible" if eid in complete else "missing_ordinary_controlled_context"
                        ),
                    )
                )
        for baseline in run.config["baselines"]:
            a = f[f.method.eq(baseline + "_meuse")].set_index(["query_event_id", "target_k"])
            b = full[full.method.eq(baseline)]
            for r in b.itertuples():
                key = (r.query_event_id, r.target_k)
                used = key in a.index
                selected = a.loc[key] if used else None
                row = dict(
                    context=context,
                    setting=setting,
                    baseline=baseline,
                    target_k=r.target_k,
                    query_event_id=r.query_event_id,
                    query_storm_id=r.query_storm_id,
                    query_onset_utc=r.query_onset_utc,
                    query_country=r.query_country,
                    used_meuse=used,
                    fallback_reason=""
                    if used
                    else (
                        "missing_query_context"
                        if r.query_event_id not in complete
                        else "no_context_supported_prior_storm"
                    ),
                    actual_donors=selected.actual_donors if used else r.actual_donors,
                )
                for metric in ["crps_mean_24h"] + runmodule.SCORE_FIELDS[:6]:
                    row[metric + "_baseline"] = getattr(r, metric)
                    row[metric + "_policy"] = selected[metric] if used else getattr(r, metric)
                    row[metric + "_difference"] = (
                        row[metric + "_policy"] - row[metric + "_baseline"]
                    )
                pairs.append(row)
    ledger_frame = pd.DataFrame(ledger)
    # Exclusion evidence stays multi-label: one missing input does not erase
    # simultaneous outcome or measurement limitations.
    for field in [
        "q_only_input_sample",
        "q_only_scoring_sample",
        "outcome_discharge_fraction",
        "outcome_score_admissible",
        "history_discharge_fraction",
        "measurement_concern",
    ]:
        ledger_frame[field] = ledger_frame.event_id.map(meta[field])
    features = run.sample.set_index("event_id")[run.base.FEATURE_COLUMNS].notna().all(axis=1)
    ledger_frame["conventional_features_complete_in_Q_population"] = ledger_frame.event_id.map(
        features
    )
    supports = []
    for path in (OUT / "archive").glob("*/support.parquet"):
        f = pd.read_parquet(path)
        f = f[f.setting.eq("main")].copy()
        f["module"] = "eo"
        f["context"] = f.family + ":" + f.kind + ":" + f.model
        f = f.rename(columns={"query_event_id": "event_id"})
        supports.append(
            f[
                [
                    "module",
                    "context",
                    "event_id",
                    "candidate_events",
                    "candidate_storms",
                    "observed_H3_positive",
                    "H3_label_unknown",
                ]
            ]
        )
    for folder in (OUT / "meuse").glob("*_main"):
        f = pd.read_parquet(folder / "support.parquet").rename(
            columns={"query_event_id": "event_id"}
        )
        f["module"] = "meuse"
        f["context"] = folder.name.removesuffix("_main")
        supports.append(
            f[
                [
                    "module",
                    "context",
                    "event_id",
                    "candidate_events",
                    "candidate_storms",
                    "observed_H3_positive",
                    "H3_label_unknown",
                ]
            ]
        )
    f = pd.read_parquet(OUT / "baselines/q_main/support.parquet")
    f = f.rename(columns={"event_id": "event_id"}).assign(module="baseline", context="q")
    supports.append(
        f[
            [
                "module",
                "context",
                "event_id",
                "candidate_events",
                "candidate_storms",
                "observed_H3_positive",
                "H3_label_unknown",
            ]
        ]
    )
    ledger_frame = ledger_frame.merge(
        pd.concat(supports), on=["module", "context", "event_id"], how="left", validate="one_to_one"
    )
    ledger_frame.loc[
        ledger_frame.population_eligible & ledger_frame.candidate_storms.eq(0), "reason"
    ] = "no_completed_prior_storm"
    policies = pd.DataFrame(pairs)
    for key, g in policies.groupby(["context", "setting", "baseline", "target_k"]):
        tags = dict(zip(["context", "setting", "baseline", "target_k"], key, strict=True))
        for country in ["all", "NL", "DE"]:
            h = g if country == "all" else g[g.query_country.eq(country)]
            columns = [c for c in h if c.endswith("_difference")]
            for r in run.ci(h, tags | {"module": "fallback", "query_country": country}, columns):
                r["metric"] = r.pop("component").removesuffix("_difference")
                r["component"] = "total_difference"
                intervals.append(r)
    return ledger_frame, policies, pd.DataFrame(intervals)


def figures(intervals, ledger, work):
    for kind in ["monthly_snapshot", "monthly", "recent"]:
        f = intervals[
            (intervals.module == "archive")
            & (intervals.family == "rain")
            & (intervals.kind == kind)
            & (intervals.setting == "main")
            & (intervals.baseline == "conventional")
            & (intervals.target_k == 5)
            & (intervals.query_country == "all")
            & (intervals.metric == "ensemble_curve_level_rmse")
            & (intervals.resampling_unit == "storm_id")
        ]
        fig, axes = plt.subplots(1, 2, figsize=(13, 7), sharey=True)
        for ax, pop in zip(axes, ["all_ten", "own"], strict=True):
            g = f[f.population.eq("all_ten")] if pop == "all_ten" else f[f.population.eq(f.model)]
            for j, component in enumerate(
                ["archive_difference", "representation_difference", "total_difference"]
            ):
                h = g[g.component.eq(component)].set_index("model").reindex(sorted(ROUTES))
                y = np.arange(len(h)) + (j - 1) * 0.19
                ax.errorbar(
                    h.difference,
                    y,
                    xerr=np.vstack([h.difference - h.lower, h.upper - h.difference]),
                    fmt="o",
                    markersize=3,
                    label=component.removesuffix("_difference"),
                )
            ax.axvline(0, color="grey", lw=0.7)
            ax.set_yticks(range(len(ROUTES)), sorted(ROUTES))
            ax.set_title(
                "All-ten shared archive" if pop == "all_ten" else "Own model-available archive"
            )
            ax.set_xlabel("Mean-trajectory RMSE difference, Q/p99; lower is better")
            ax.grid(alpha=0.15)
        axes[0].legend(fontsize=8)
        fig.suptitle(f"{kind}: paired decomposition; k=5, pooled NL/DE; nominal storm intervals")
        fig.tight_layout()
        fig.savefig(work / f"archive_{kind}.png", dpi=150)
        plt.close(fig)
    # Coverage relative to the actual broad rainfall-complete population in each year.
    base = (
        ledger[(ledger.module == "meuse") & (ledger.context == "both_sites")]
        .groupby("year")
        .base_eligible.sum()
    )
    g = ledger[
        ((ledger.module == "eo") & ledger.context.str.startswith("rain:monthly_snapshot:"))
        | (ledger.module == "meuse")
    ]
    table = g.groupby(["context", "year"]).population_eligible.sum().unstack().div(base, axis=1)
    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(table.to_numpy(), vmin=0, vmax=1, cmap="YlGnBu", aspect="auto")
    ax.set_yticks(range(len(table)), [x.replace("rain:monthly_snapshot:", "") for x in table.index])
    ax.set_xticks(range(len(table.columns)), table.columns, rotation=45)
    ax.set_title(
        "Input eligibility / broad rainfall-complete population in each year; before prior-donor availability"
    )
    fig.colorbar(im, ax=ax, label="Eligible fraction")
    fig.tight_layout()
    fig.savefig(work / "coverage_by_year.png", dpi=150)
    plt.close(fig)
    f = intervals[
        (intervals.module == "meuse")
        & (intervals.setting == "main")
        & (intervals.target_k == 5)
        & (intervals.metric == "crps_mean_24h")
        & (intervals.component == "representation_difference")
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), sharey=True)
    labels = [
        (c, b) for c in ["both_sites", "sint_pieter_only"] for b in ["conventional", "ttm_state"]
    ]
    for ax, country in zip(axes, ["all", "NL", "DE"], strict=True):
        for unit, offset, color in [
            ("storm_id", -0.08, "tab:blue"),
            ("storm_year", 0.08, "tab:orange"),
        ]:
            h = (
                f[(f.query_country == country) & (f.resampling_unit == unit)]
                .set_index(["context", "baseline"])
                .reindex(labels)
            )
            ax.hlines(np.arange(4) + offset, h.lower, h.upper, color=color, label=unit)
            ax.plot(h.difference, np.arange(4) + offset, "o", color=color, markersize=4)
        ax.axvline(0, color="grey", lw=0.7)
        ax.set_title(country)
        ax.set_yticks(range(4), [f"{c}: {b}" for c, b in labels])
        ax.grid(alpha=0.15)
        ax.set_xlabel("CRPS change from adding Meuse; Q/p99")
    axes[0].legend(fontsize=8)
    fig.suptitle("Matched event/donor pools; next-24h distribution; k=5")
    fig.tight_layout()
    fig.savefig(work / "meuse_increment.png", dpi=150)
    plt.close(fig)


def browser(run, work):
    basefolder = OUT / "baselines/rain_main"
    baseline = pd.read_parquet(basefolder / "donors.parquet")
    meta = run.meta
    methods = {}
    allids = set()
    for context in run.config["context_features"]:
        d = pd.read_parquet(OUT / "meuse" / f"{context}_main/donors.parquet")
        for method in run.config["baselines"]:
            for label, frame in [
                ("broad", baseline[baseline.method.eq(method)]),
                ("restricted", d[d.method.eq(method)]),
                ("meuse", d[d.method.eq(method + "_meuse")]),
            ]:
                for eid, g in frame.groupby("query_event_id"):
                    ids = g.sort_values("rank").analogue_event_id.tolist()
                    methods.setdefault(eid, {})[f"{context}:{method}:{label}"] = ids
                    allids.add(eid)
                    allids.update(ids)
    facts = {
        eid: dict(
            gauge=meta.loc[eid, "gauge"],
            country=meta.loc[eid, "country"],
            watercourse=meta.loc[eid, "watercourse"],
            onset=str(meta.loc[eid, "onset_utc"]),
        )
        for eid in allids
    }
    curves = {eid: run.response.loc[eid].to_numpy().tolist() for eid in allids}
    payload = json.dumps(dict(sets=methods, facts=facts, curves=curves), allow_nan=False).replace(
        "<", "\\u003c"
    )
    # One browser spans every scored main-view rainfall query; examples are not the denominator.
    template = """<!doctype html><meta charset="utf-8"><title>Historical analogues and Meuse context</title>
<style>body{font:15px system-ui;margin:24px;max-width:1200px}select{max-width:650px;margin:6px}svg{width:100%;height:430px;border:1px solid #bbb}table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:4px}</style>
<h1>Historical analogue assessment: Meuse context</h1><p>Retrospective observed Q/p99. Select any scored query. Black=query; grey=individual Meuse-selected donors; blue=broad baseline mean; orange=restricted baseline mean; green=Meuse mean. Missing context remains explicit. Member envelope is not a calibrated probability band. Hover a donor row to identify its event.</p>
<select id="event"></select><br><select id="context"><option>both_sites</option><option>sint_pieter_only</option></select><select id="method"><option>conventional</option><option>ttm_state</option></select><select id="k"><option>5</option><option>10</option></select><p id="note"></p><svg id="plot" viewBox="0 0 1100 420"></svg><div id="donors"></div>
<script>const D=PAYLOAD;const el=id=>document.getElementById(id);let opts=Object.keys(D.sets).sort((a,b)=>D.facts[a].onset.localeCompare(D.facts[b].onset));for(let id of opts){let o=document.createElement('option');o.value=id;o.textContent=id;el('event').appendChild(o)}
function draw(){let id=el('event').value,c=el('context').value,m=el('method').value,k=+el('k').value,ss=D.sets[id],sets={};for(let role of ['broad','restricted','meuse'])sets[role]=(ss[c+':'+m+':'+role]||[]).slice(0,k);let ymax=Math.max(...D.curves[id],...Object.values(sets).flat().flatMap(i=>D.curves[i]))*1.06;let ns='http://www.w3.org/2000/svg',svg=el('plot');svg.replaceChildren();function line(v,color,width){let p=document.createElementNS(ns,'polyline');p.setAttribute('points',v.map((y,i)=>(45+i*1040/71)+','+(380-y/ymax*350)).join(' '));p.setAttribute('stroke',color);p.setAttribute('stroke-width',width);p.setAttribute('fill','none');svg.appendChild(p)}for(let d of sets.meuse)line(D.curves[d],'#bbb',1);for(let [role,color] of [['broad','#2675b7'],['restricted','#e68a00'],['meuse','#238b45']]){let ids=sets[role];if(ids.length)line(Array.from({length:72},(_,h)=>ids.reduce((s,i)=>s+D.curves[i][h],0)/ids.length),color,2.5)}line(D.curves[id],'#111',3);for(let h of [1,24,48,72]){let t=document.createElementNS(ns,'text');t.setAttribute('x',45+(h-1)*1040/71);t.setAttribute('y',407);t.textContent='+'+h+'h';svg.appendChild(t)}let t=document.createElementNS(ns,'text');t.setAttribute('x',5);t.setAttribute('y',22);t.textContent='Q/p99, max '+ymax.toFixed(2);svg.appendChild(t);el('note').textContent=JSON.stringify(D.facts[id])+(sets.meuse.length?' | Meuse members: '+sets.meuse.length:' | Meuse retrieval unavailable; baseline retained');let div=el('donors');div.replaceChildren();for(let role of ['broad','restricted','meuse']){let h=document.createElement('h3');h.textContent=role;div.appendChild(h);let ol=document.createElement('ol');for(let d of sets[role]){let li=document.createElement('li');li.textContent=d+' | '+D.facts[d].watercourse+' '+D.facts[d].country;ol.appendChild(li)}div.appendChild(ol)}}for(let id of ['event','context','method','k'])el(id).onchange=draw;draw();</script>"""
    (work / "analogues.html").write_text(template.replace("PAYLOAD", payload))


def case_panels(run, pairs, work):
    f = pairs[
        (pairs.context == "both_sites")
        & (pairs.setting == "main")
        & (pairs.baseline == "conventional")
        & (pairs.target_k == 5)
        & (pairs.metric == "crps_mean_24h")
    ].sort_values(["representation_difference", "query_event_id"])
    chosen = {
        eid: "existing severe/recovery case"
        for eid in [
            "18.Q.45|2014-07-08T12:00:00+00:00",
            "15.Q.41|2024-05-17T07:00:00+00:00",
            "15.Q.41|2024-05-20T18:00:00+00:00",
            "11.Q.32|2021-07-10T19:00:00+00:00",
        ]
    }
    for _, r in f.head(2).iterrows():
        chosen.setdefault(r.query_event_id, "largest paired CRPS improvement")
    for _, r in f.tail(2).iterrows():
        chosen.setdefault(r.query_event_id, "largest paired CRPS degradation")
    for _, r in (
        f.assign(absdiff=f.representation_difference.abs())
        .sort_values(["absdiff", "query_event_id"])
        .head(2)
        .iterrows()
    ):
        chosen.setdefault(r.query_event_id, "smallest paired CRPS change")
    ds = pd.read_parquet(OUT / "meuse/both_sites_main/donors.parquet")
    broad = pd.read_parquet(OUT / "baselines/rain_main/donors.parquet")
    selection = []
    for eid, reason in chosen.items():
        fig, axes = plt.subplots(1, 2, figsize=(13, 4), sharey=True)
        for ax, method in zip(axes, run.config["baselines"], strict=True):
            for role, frame, color in [
                ("broad", broad, "tab:blue"),
                ("restricted", ds, "tab:orange"),
                ("meuse", ds, "tab:green"),
            ]:
                arm = method + "_meuse" if role == "meuse" else method
                g = (
                    frame[frame.query_event_id.eq(eid) & frame.method.eq(arm)]
                    .sort_values("rank")
                    .head(5)
                )
                if g.empty:
                    continue
                a = run.response.loc[g.analogue_event_id].to_numpy()
                if role == "meuse":
                    for v in a:
                        ax.plot(range(1, 73), v, color="grey", alpha=0.3, lw=0.7)
                ax.plot(range(1, 73), a.mean(0), label=role, color=color)
            q = run.response.loc[eid].to_numpy()
            ax.plot(range(1, 73), q, color="black", label="query")
            ax.set_title(method)
            ax.grid(alpha=0.2)
            ax.set_xlabel("Hours after p99 onset")
            ax.legend(fontsize=8)
        axes[0].set_ylabel("Observed Q / own-era p99")
        fig.suptitle(eid + " — " + reason)
        fig.tight_layout()
        name = "case_" + str(len(selection) + 1) + ".png"
        fig.savefig(work / name, dpi=140)
        plt.close(fig)
        selection.append(dict(event_id=eid, selection_reason=reason, figure=name))
    pd.DataFrame(selection).to_json(work / "case_selection.json", orient="records", indent=2)
    return selection


def main():
    global runmodule
    runmodule = load_script("146_run_limburg_assessment.py", "assessment_reporting_run")
    run = runmodule.Run()
    for folder in (
        list((OUT / "baselines").iterdir())
        + list((OUT / "archive").iterdir())
        + list((OUT / "meuse").iterdir())
        + [OUT / "intervals"]
    ):
        if not run.valid(folder):
            raise ValueError("Missing completed stage " + str(folder))
    intervals = pd.read_parquet(OUT / "intervals/paired_intervals.parquet")
    pairs = pd.read_parquet(OUT / "intervals/meuse_pairs.parquet")
    ledger, policies, fallback = fallback_and_ledger(run)
    intervals = pd.concat([intervals, fallback], ignore_index=True)
    dest = OUT / "review"
    with fresh_output(dest) as work:
        pd.DataFrame(quantified_evidence()).to_json(
            work / "evidence_map.json", orient="records", indent=2
        )
        ledger.to_parquet(work / "eligibility_ledger.parquet", index=False)
        policies.to_parquet(work / "fallback_policy.parquet", index=False)
        intervals.to_parquet(work / "all_intervals.parquet", index=False)
        (work / "reading_order.md").write_text(
            "# Evidence reading order\n\n1. Main synthesis memo and claim map.\n2. Coverage by year, source quality and paired archive decomposition.\n3. Meuse distributional contrasts and fallback applicability.\n4. Deterministically chosen case panels and full query browser.\n5. Original ten-encoder comparisons, October 15 distribution/storm-response evidence, and all sensitivity tables.\n\nBrian writes all dissertation prose. Cases are diagnostic illustrations; the complete declared census supplies performance denominators.\n"
        )
        figures(intervals, ledger, work)
        browser(run, work)
        selected = case_panels(run, pairs, work)
        support = []
        for folder in (OUT / "meuse").iterdir():
            context, setting = folder_tags(folder.name)
            f = pd.read_parquet(folder / "scores.parquet")
            for country, g in f[f.method.eq("conventional") & f.target_k.eq(5)].groupby(
                "query_country"
            ):
                support.append(
                    dict(
                        context=context,
                        setting=setting,
                        country=country,
                        queries=len(g),
                        storms=g.query_storm_id.nunique(),
                        years=pd.to_datetime(g.query_onset_utc, utc=True).dt.year.nunique(),
                    )
                )
        pd.DataFrame(support).to_json(work / "meuse_support.json", orient="records", indent=2)
        # All loss contrasts and effect sizes are kept, not just nominally favorable ones.
        primary = intervals[
            (intervals.module == "meuse")
            & (intervals.setting == "main")
            & (intervals.target_k == 5)
            & (intervals.metric == "crps_mean_24h")
            & (intervals.component == "representation_difference")
        ]
        primary.to_json(work / "primary_meuse_results.json", orient="records", indent=2)
        body = "<h1>Limburg historical analogue assessment</h1><p>Retrospective evidence. "
        body += 'No calibrated warning or operator-benefit claim. <a href="analogues.html">Inspect all main-view query/donor selections</a>.</p>'
        body += "<h2>Evidence map</h2>" + pd.DataFrame(evidence_map()).to_html(
            index=False, escape=True
        )
        body += "<h2>Meuse primary comparison</h2>" + primary.to_html(index=False)
        for p in sorted(work.glob("*.png")):
            body += f'<h2>{html.escape(p.name)}</h2><img style="max-width:100%" src="{p.name}">'
        body += "<p>Case selection: " + html.escape(json.dumps(selected)) + "</p>"
        (work / "index.html").write_text(
            '<!doctype html><meta charset="utf-8"><title>Limburg synthesis</title>' + body
        )
        # Bind every completed-stage manifest and immutable evidence note behind the claim map.
        for p in OUT.glob("*/*/manifest.json"):
            run.bind(p)
        run.bind(OUT / "intervals/manifest.json")
        for e in evidence_map():
            run.bind(ROOT / e["source"])
        m = dict(
            status="completed",
            created_utc=datetime.now(timezone.utc).isoformat(),
            inputs_sha256=run.inputs,
            source_sha256=run.sources
            | {str(Path(__file__).relative_to(ROOT)): sha256(Path(__file__))},
            outputs_sha256={
                str(p.relative_to(work)): sha256(p) for p in work.rglob("*") if p.is_file()
            },
        )
        (work / "manifest.json").write_text(json.dumps(m, indent=2))
    print(
        "review complete",
        len(ledger),
        "eligibility rows;",
        len(policies),
        "fallback rows",
        flush=True,
    )


if __name__ == "__main__":
    main()
