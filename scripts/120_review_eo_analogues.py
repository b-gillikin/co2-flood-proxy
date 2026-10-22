"""Review the complete held-archive EO comparison and expose actual donor choices.

No reranking, tuning, event subsampling, new model or operational forecast claim.
The browser covers every scored main/pooled/five-donor available-model case;
tables retain all other policies, quality analyses and donor counts.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output

KEYS = ["kind", "cohort", "scenario", "analysis", "policy", "target_k"]
METRICS = [
    "mean_peak_scaled_shape_rmse",
    "mean_donor_peak_absolute_error",
    "ensemble_curve_level_rmse",
    "mean_peak_time_difference_h",
    "duration_estimate_absolute_error_h",
    "final_24h_level_absolute_error",
]


def audit_donors(frame, meta):
    """Audit every stored donor row, including NL/DE direction and quality policy."""
    q = meta.reindex(frame.query_event_id).reset_index(drop=True)
    d = meta.reindex(frame.analogue_event_id).reset_index(drop=True)
    if q.onset_utc.isna().any() or d.onset_utc.isna().any():
        raise ValueError("Unknown query or donor event")
    tests = {
        "unfinished_prior_response": (d.onset_utc + pd.Timedelta(hours=72) > q.onset_utc),
        "same_storm": d.storm_id.eq(q.storm_id),
        "same_event": frame.query_event_id.reset_index(drop=True).eq(
            frame.analogue_event_id.reset_index(drop=True)
        ),
        "wrong_country_policy": (
            frame.policy.reset_index(drop=True).eq("domestic") & d.country.ne(q.country)
        )
        | (frame.policy.reset_index(drop=True).eq("foreign") & d.country.eq(q.country)),
        "same_river_in_other_river_search": frame.scenario.reset_index(drop=True).eq("other_rivers")
        & d.physical_river_group.eq(q.physical_river_group),
        "measurement_concern_in_quality_analysis": frame.analysis.reset_index(drop=True).eq(
            "quality_sensitivity"
        )
        & (q.measurement_concern | d.measurement_concern),
        "inadmissible_response": ~q.q_only_scoring_sample | ~d.q_only_scoring_sample,
        "rank_outside_requested_k": frame["rank"].gt(frame.target_k),
    }
    result = {name: int(values.sum()) for name, values in tests.items()}
    if any(result.values()):
        raise ValueError("Donor audit violations: " + json.dumps(result))
    return result


def paired_event_rows(rows):
    """All event differences, using identical cohort/policy and actual donor counts."""
    output = []
    for reference in ["ttm_state", "raw_state", "conventional"]:
        ref = rows[rows.arm.eq(reference)][
            KEYS + ["query_event_id", "actual_donor_count", *METRICS]
        ]
        pair = rows.merge(
            ref,
            on=KEYS + ["query_event_id"],
            how="inner",
            suffixes=("", "_reference"),
            validate="many_to_one",
        )
        pair = pair[
            pair.arm.ne(reference) & pair.actual_donor_count.eq(pair.actual_donor_count_reference)
        ].copy()
        for metric in METRICS:
            pair[metric + "_difference"] = pair[metric] - pair[metric + "_reference"]
        pair["reference"] = reference
        output.append(
            pair[
                KEYS
                + [
                    "query_event_id",
                    "query_country",
                    "query_river",
                    "arm",
                    "reference",
                    "actual_donor_count",
                    "query_measurement_concern",
                ]
                + [m + "_difference" for m in METRICS]
            ]
        )
    return pd.concat(output, ignore_index=True)


def browser_page(records, meta, response, title, *, coherent=False):
    """One complete-census page per context kind, no external web dependencies."""
    needed = set(records.query_event_id)
    for ids in records.donor_ids:
        needed.update(ids)
    curves = {
        eid: np.round(response.loc[eid].to_numpy(float), 5).tolist() for eid in sorted(needed)
    }
    facts = {
        eid: {
            "country": str(meta.loc[eid, "country"]),
            "river": str(meta.loc[eid, "physical_river_group"]),
            "onset": str(meta.loc[eid, "onset_utc"]),
            "measurement_concern": bool(meta.loc[eid, "measurement_concern"]),
            "provider_status": str(meta.loc[eid, "provider_status"]),
        }
        for eid in sorted(needed)
    }
    columns = [
        "query_event_id",
        "cohort",
        "scenario",
        "policy",
        "arm",
        "actual_donor_count",
        "donor_ids",
        *METRICS,
    ]
    data = json.loads(records[columns].to_json(orient="records"))
    payload = json.dumps({"rows": data, "curves": curves, "facts": facts}, allow_nan=False)
    payload = payload.replace("<", "\\u003c")
    input_note = (
        "These are held-archive inputs with same-UTC-day S2 masking; the three native-product models are reused. Additional Azure imagery is not included."
        if coherent
        else "These are held-archive inputs. Some Sentinel-2 bands have mixed acquisition days; no full same-day corrected embedding run is implied."
    )
    return (
        """<!doctype html><meta charset="utf-8"><title>Actual EO analogues</title>
<style>body{font:16px system-ui;max-width:1200px;margin:25px auto;padding:0 15px}
select{max-width:100%;margin:5px;padding:5px}svg{width:100%;height:330px;border:1px solid #ddd}
table{border-collapse:collapse}td,th{padding:6px;border:1px solid #ddd;text-align:left}
.note{background:#fff4d9;padding:12px}</style>
<h1>"""
        + html.escape(title)
        + """</h1>
<p>Every scored main, pooled, five-donor case in the available-model cohorts is selectable.
The verification curves below show subsequent observed behaviour. These outcomes did not
rank the donors. This is retrospective Q/own-era-p99, not calibrated warning probabilities.</p>
<p class="note">"""
        + html.escape(input_note)
        + """ Countries also differ in rivers,
measurement histories and archive length. p99 does not establish inundation.</p>
<div id="filters"></div><div id="facts"></div><svg id="plot" viewBox="0 0 1100 330"></svg>
<div id="metrics"></div><h2>Selected donors</h2><div id="donors"></div>
<script id="payload" type="application/json">"""
        + payload
        + """</script><script>
const D=JSON.parse(document.querySelector('#payload').textContent), F=document.querySelector('#filters');
const names=['cohort','scenario','query_event_id','arm'], controls={};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
for(const n of names){const label=document.createElement('label');label.textContent=n+' ';
const s=document.createElement('select');controls[n]=s;label.append(s);F.append(label);
s.onchange=()=>refresh(names.indexOf(n)+1);}
function refresh(start=0){let rows=D.rows;
for(let i=0;i<names.length;i++){const n=names[i],s=controls[n];
if(i>=start){const old=s.value,values=[...new Set(rows.map(r=>r[n]))].sort();
s.replaceChildren(...values.map(v=>new Option(v,v)));if(values.includes(old))s.value=old;}
rows=rows.filter(r=>r[n]===s.value);}if(!rows.length)return;const r=rows[0],q=D.curves[r.query_event_id];
const ds=r.donor_ids.map(id=>D.curves[id]),mean=q.map((_,i)=>ds.reduce((a,d)=>a+d[i],0)/ds.length);
const f=D.facts[r.query_event_id];document.querySelector('#facts').textContent=
f.country+' / '+f.river+' / '+f.onset+' | measurement concern: '+f.measurement_concern;
const max=Math.max(1,...q,...ds.flat()),x=i=>45+i/71*1030,y=v=>290-v/max*260;
const path=(a,color,width)=>'<polyline fill="none" stroke="'+color+'" stroke-width="'+width+
'" points="'+a.map((v,i)=>x(i)+','+y(v)).join(' ')+'"/>';
document.querySelector('#plot').innerHTML=ds.map(a=>path(a,'#a7b9ce',1)).join('')+
path(mean,'#2166ac',3)+path(q,'#111',3)+'<line x1="45" x2="1075" y1="'+y(1)+
'" y2="'+y(1)+'" stroke="#999" stroke-dasharray="4"/><text x="45" y="318">Hour 1</text>'+
'<text x="990" y="318">Hour 72</text><text x="45" y="18">Black: query; blue: donor mean; pale: individual donors; dashed: p99</text>';
document.querySelector('#metrics').innerHTML='<table><tr><th>Metric (lower is better)</th><th>Value</th></tr>'+
Object.entries(r).filter(([k])=>k.endsWith('rmse')||k.endsWith('_error')||k.endsWith('_error_h')||k.endsWith('_difference_h'))
.map(([k,v])=>'<tr><td>'+esc(k)+'</td><td>'+Number(v).toFixed(4)+'</td></tr>').join('')+'</table>';
document.querySelector('#donors').innerHTML='<table><tr><th>Rank / event</th><th>Country / river</th><th>Measurement concern / provider status</th></tr>'+
r.donor_ids.map((id,i)=>{const d=D.facts[id];return '<tr><td>'+esc((i+1)+' / '+id)+'</td><td>'+
esc(d.country+' / '+d.river)+'</td><td>'+esc(d.measurement_concern+' / '+d.provider_status)+'</td></tr>';}).join('')+'</table>';}
refresh();</script>"""
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "results/eo_analogue_comparison")
    parser.add_argument("--out", type=Path, default=ROOT / "results/eo_analogue_review")
    args = parser.parse_args()
    receipt = json.loads((args.input / "manifest.json").read_text())
    if receipt["status"] != "completed":
        raise ValueError("A completed scientific comparison is required")
    for name, digest in receipt["outputs_sha256"].items():
        if sha256(args.input / name) != digest:
            raise ValueError("Changed comparison output: " + name)
    for name, digest in receipt["input_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("Changed comparison input: " + name)
    meta = pd.read_csv(
        ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv",
        parse_dates=["onset_utc"],
    ).set_index("event_id")
    response = pd.read_parquet(
        ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet"
    )
    rows = pd.read_parquet(
        args.input / "event_assessments.parquet",
        columns=KEYS
        + [
            "arm",
            "query_event_id",
            "query_country",
            "query_river",
            "query_storm_id",
            "actual_donor_count",
            "query_measurement_concern",
            *METRICS,
        ],
    )
    groups = KEYS + ["arm", "query_country", "query_river"]
    with fresh_output(args.out) as out:
        summary = (
            rows.groupby(groups, dropna=False)
            .agg(
                queries=("query_event_id", "size"),
                storms=("query_storm_id", "nunique"),
                min_actual_donors=("actual_donor_count", "min"),
                mean_actual_donors=("actual_donor_count", "mean"),
                measurement_concern_share=("query_measurement_concern", "mean"),
                **{m: (m, "mean") for m in METRICS},
            )
            .reset_index()
        )
        summary.to_csv(out / "summary_by_configuration_country_river.csv", index=False)
        differences = paired_event_rows(rows)
        differences.to_parquet(out / "paired_event_differences.parquet", index=False)
        differences.groupby(KEYS + ["arm", "reference", "query_country"]).agg(
            queries=("query_event_id", "size"),
            **{m + "_difference": (m + "_difference", "mean") for m in METRICS},
            shape_improvement_share=(METRICS[0] + "_difference", lambda x: (x < 0).mean()),
            duration_improvement_share=(METRICS[4] + "_difference", lambda x: (x < 0).mean()),
        ).reset_index().to_csv(out / "paired_summary.csv", index=False)
        del differences
        primary = rows[
            rows.analysis.eq("main")
            & rows.policy.eq("pooled")
            & rows.target_k.eq(5)
            & rows.cohort.str.startswith(("q_only_available_", "rain_matched_available_"))
        ].copy()
        wanted = set(primary.cohort)
        selected = []
        total = 0
        checks = {}
        parquet = pq.ParquetFile(args.input / "selected_donors.parquet")
        for batch in parquet.iter_batches(batch_size=100_000):
            frame = batch.to_pandas()
            for name, count in audit_donors(frame, meta).items():
                checks[name] = checks.get(name, 0) + count
            total += len(frame)
            take = frame[
                frame.analysis.eq("main")
                & frame.policy.eq("pooled")
                & frame.target_k.eq(5)
                & frame.cohort.isin(wanted)
            ]
            if len(take):
                selected.append(take[KEYS + ["arm", "query_event_id", "rank", "analogue_event_id"]])
        donor_rows = pd.concat(selected, ignore_index=True)
        ids = (
            donor_rows.sort_values("rank")
            .groupby(KEYS + ["arm", "query_event_id"])
            .analogue_event_id.agg(list)
            .rename("donor_ids")
            .reset_index()
        )
        primary = primary.merge(ids, on=KEYS + ["arm", "query_event_id"], validate="one_to_one")
        if not primary.donor_ids.map(len).eq(primary.actual_donor_count).all():
            raise ValueError("Browser donor count differs from scored count")
        if primary.donor_ids.map(lambda ids: len(ids) != len(set(ids))).any():
            raise ValueError("Duplicate donor in browser selection")
        ref_ids = primary[primary.arm.eq("ttm_state")][
            KEYS + ["query_event_id", "donor_ids", "actual_donor_count"]
        ].rename(
            columns={"donor_ids": "ttm_donor_ids", "actual_donor_count": "ttm_actual_donor_count"}
        )
        primary = primary.merge(ref_ids, on=KEYS + ["query_event_id"], validate="many_to_one")
        primary["same_actual_count_as_ttm"] = primary.actual_donor_count.eq(
            primary.ttm_actual_donor_count
        )
        primary["donor_jaccard_with_ttm"] = [
            len(set(a) & set(b)) / len(set(a) | set(b))
            for a, b in zip(primary.donor_ids, primary.ttm_donor_ids, strict=True)
        ]
        primary.to_parquet(out / "browser_case_index.parquet", index=False)
        plan_path = args.input / "experiment_plan.json"
        contract = (
            json.loads(plan_path.read_text()).get("selected_input_contract", {})
            if plan_path.exists()
            else {}
        )
        coherent = any(
            v.get("input_policy") == "s2_same_utc_day_mask_v2" for v in contract.values()
        )
        for kind, group in primary.groupby("kind"):
            (out / f"{kind}.html").write_text(
                browser_page(group, meta, response, kind, coherent=coherent)
            )
        # Explicit post-outcome illustrations; they do not determine the census.
        examples = []
        for (_kind, _country), group in primary[
            primary.scenario.eq("other_rivers")
            & primary.arm.str.endswith("_ttm_state")
            & ~primary.arm.isin(["area_ttm_state", "identity_ttm_state", "alphaearth_ttm_state"])
        ].groupby(["kind", "query_country"]):
            for reason, metric, ascending in [
                ("lowest_shape_error", METRICS[0], True),
                ("highest_shape_error", METRICS[0], False),
                ("largest_duration_error", METRICS[4], False),
            ]:
                item = (
                    group.sort_values(
                        [metric, "query_event_id", "arm"], ascending=[ascending, True, True]
                    )
                    .iloc[0]
                    .to_dict()
                )
                item["selection_reason"] = reason
                examples.append(item)
        pd.DataFrame(examples).to_parquet(out / "posthoc_illustrations.parquet", index=False)
        manifest = {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "assessment_rows": len(rows),
            "unique_scored_queries": rows.query_event_id.nunique(),
            "audited_donor_rows": total,
            "donor_violations": checks,
            "browser_assessment_rows": len(primary),
            "browser_unique_queries": primary.query_event_id.nunique(),
            "population": "Full executed comparison; no event sample. Browser is an explicit main/pooled/k=5 view, not a separate evaluation sample.",
            "illustrations": "Post-outcome error extrema by readout/country; illustrative only, not prevalence estimates or human verdicts.",
            "uncertainty": "Use comparison paired_intervals.csv for storm/year intervals; paired_summary is descriptive and does not add significance claims.",
            "input_sha256": {
                str(args.input / "manifest.json"): sha256(args.input / "manifest.json"),
                "script": sha256(Path(__file__)),
                "event_inventory": sha256(
                    ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv"
                ),
                "response": sha256(
                    ROOT
                    / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet"
                ),
            },
            "outputs_sha256": {p.name: sha256(p) for p in out.iterdir() if p.is_file()},
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k.endswith("rows") or k == "status"}))


if __name__ == "__main__":
    main()
