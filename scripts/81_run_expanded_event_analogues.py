#!/usr/bin/env python3
"""Expanded retrospective analogue census and event-level evidence packet.

No training, new representation choices, human verdicts or forecast claims.
Short archives contribute available distinct onset groups; absent archives stay visible.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prep", ROOT / "scripts/80_prepare_event_interpretation.py"
)
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)
C, B, S = P.CROSS, P.BASE, P.S
READY = ROOT / "results/basin_ai_event_interpretation_ready"
OUT = ROOT / "results/basin_ai_expanded_event_pass"


def phase_evidence(query, donors, onset):
    """Continuous duration/recession measures and descriptive donor shares.

    Threshold is existing era-p99. Shares are empirical, not calibrated probabilities.
    A response exceeding cutoff is a later increase, not necessarily a secondary storm.
    """
    q = np.asarray(query, float)
    d = np.asarray(donors, float)
    if (
        q.shape != (72,)
        or d.ndim != 2
        or d.shape[1] != 72
        or not np.isfinite(d).all()
        or not np.isfinite(q).all()
        or not np.isfinite(onset)
    ):
        raise ValueError("Complete 72-hour responses required")
    durations = (d >= 1).sum(axis=1)
    observed_duration = int((q >= 1).sum())
    return {
        "actual_donor_count": len(d),
        "estimated_high_water_hours": float(durations.mean()),
        "observed_high_water_hours": observed_duration,
        "duration_estimate_absolute_error_h": float(abs(durations.mean() - observed_duration)),
        "donor_share_ending_above_p99": float((d[:, -1] >= 1).mean()),
        "observed_ends_above_p99": bool(q[-1] >= 1),
        "estimated_final_24h_mean_over_p99": float(d[:, -24:].mean()),
        "observed_final_24h_mean_over_p99": float(q[-24:].mean()),
        "final_24h_level_absolute_error": float(abs(d[:, -24:].mean() - q[-24:].mean())),
        "donor_share_peak_exceeding_query_cutoff": float((d.max(axis=1) > onset).mean()),
        "observed_peak_exceeds_cutoff": bool(q.max() > onset),
        "donor_share_peak_after_first_hour": float((d.argmax(axis=1) > 0).mean()),
        "observed_peak_after_first_hour": bool(q.argmax() > 0),
    }


def paired_intervals(rows):
    results = []
    metrics = [
        "mean_donor_peak_absolute_error",
        "ensemble_curve_level_rmse",
        "mean_peak_scaled_shape_rmse",
        "duration_estimate_absolute_error_h",
        "final_24h_level_absolute_error",
    ]
    for keys, g in rows.groupby(["cohort", "scenario", "analysis", "target_k"]):
        raw = g[g.arm.eq("raw_state")].set_index("query_event_id")
        ttm = g[g.arm.eq("ttm_ordered_state")].set_index("query_event_id").loc[raw.index]
        if len(raw) != len(ttm) or raw.query_storm_id.nunique() < 2:
            raise ValueError("Matched queries and multiple groups required")
        contrasts = [(m, ttm[m] - raw[m], "raw_state", "ttm_ordered_state") for m in metrics]
        for arm in ["raw_state", "ttm_ordered_state"]:
            a = g[g.arm.eq(arm)].set_index("query_event_id").loc[raw.index]
            for metric, reference in [
                ("mean_donor_peak_absolute_error", "persistence_peak_absolute_error"),
                ("ensemble_curve_level_rmse", "persistence_curve_level_rmse"),
                (
                    "duration_estimate_absolute_error_h",
                    "persistence_high_water_duration_absolute_error",
                ),
                ("mean_donor_peak_absolute_error", "group_balanced_median_absolute_error"),
            ]:
                contrasts.append((metric, a[metric] - a[reference], reference, arm))
        for metric, difference, reference, challenger in contrasts:
            frame = raw[["query_storm_id", "query_onset_utc"]].copy()
            frame["difference"] = difference
            frame["storm_year"] = pd.to_datetime(
                frame.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
            ).dt.year
            for unit in ["query_storm_id", "storm_year"]:
                results.append(
                    {
                        **dict(
                            zip(["cohort", "scenario", "analysis", "target_k"], keys, strict=True)
                        ),
                        "metric": metric,
                        "reference": reference,
                        "challenger": challenger,
                        "resampling_unit": unit,
                        **C.REVIEW.cluster_interval(frame, unit),
                    }
                )
    return pd.DataFrame(results)


def write_browser(out, inventory, response, donors, history):
    """All scorable events, observed curves visibly separate from retrieved donors."""
    payload = []
    main = donors[donors.cohort.eq("q_only_pooled") & donors.analysis.eq("main")]
    for event in inventory[inventory.q_only_scoring_sample].itertuples(index=False):
        eid = event.event_id
        variants = {}
        for (scenario, arm), d in main[main.query_event_id.eq(eid)].groupby(["scenario", "arm"]):
            ids = d.sort_values("rank").head(5).analogue_event_id.tolist()
            variants[f"{scenario} / {arm}"] = ids
        payload.append(
            {
                "id": eid,
                "river": event.physical_river_group,
                "flag": bool(event.measurement_concern),
                "cutoff": float(event.cutoff_q_over_p99_h0),
                "trend6": float(event.cutoff_q_change_6h_over_p99),
                "observed": response.loc[eid].round(6).tolist(),
                "history": history.loc[eid].round(6).tolist(),
                "variants": variants,
            }
        )
    data = json.dumps(payload, allow_nan=False).replace("<", "\\u003c")
    page = """<!doctype html><meta charset="utf-8"><title>Limburg event census</title>
<style>body{font:16px system-ui;max-width:1100px;margin:24px auto}canvas{width:100%;border:1px solid #ccc}select{max-width:100%;padding:8px}pre{white-space:pre-wrap}</style>
<h1>Retrospective event evidence</h1><p>All 851 scorable episodes. Solid black: observed verification response. Blue: prior donor responses. Dashed orange: cutoff persistence. No forecast or human validation claim. Five donors where available; distinct onset groups, not verified meteorological storms.</p>
<select id="event"></select><select id="variant"></select><p id="facts"></p><canvas id="history" width="1050" height="400"></canvas><canvas id="plot" width="1050" height="400"></canvas><pre id="ids"></pre>
<script>const data=PAYLOAD;const lookup=Object.fromEntries(data.map(x=>[x.id,x]));const e=document.getElementById('event'),v=document.getElementById('variant');
data.forEach((x,i)=>{let o=new Option(x.id+' — '+x.river,i);e.add(o)});
function choose(){v.innerHTML='';Object.keys(data[e.value].variants).forEach(k=>v.add(new Option(k,k)));draw()}
function draw(){let x=data[e.value],ds=(x.variants[v.value]||[]).map(id=>({id,curve:lookup[id].observed,history:lookup[id].history}));document.getElementById('facts').textContent='Cutoff Q/p99: '+x.cutoff.toFixed(3)+'; preceding 6h change: '+x.trend6.toFixed(3)+'; measurement concern: '+x.flag+'; available selected donors: '+ds.length;
let h=document.getElementById('history').getContext('2d');h.clearRect(0,0,1050,400);let hm=Math.max(...x.history,...ds.flatMap(d=>d.history))*1.1;function hl(a,col){h.strokeStyle=col;h.lineWidth=col==='black'?3:1;h.beginPath();a.forEach((z,i)=>{let xx=50+i/511*970,yy=350-z/hm*320;i?h.lineTo(xx,yy):h.moveTo(xx,yy)});h.stroke()}ds.forEach(d=>hl(d.history,'#668bbb'));hl(x.history,'black');h.fillText('Input histories, hours −511…0; each event Q / own era-p99; top '+hm.toFixed(2),50,18);let c=document.getElementById('plot').getContext('2d');c.clearRect(0,0,1050,400);let max=Math.max(x.cutoff,...x.observed,...ds.flatMap(d=>d.curve))*1.1;
function line(a,col,dash=[]){c.strokeStyle=col;c.setLineDash(dash);c.lineWidth=col==='black'?3:1.5;c.beginPath();a.forEach((z,i)=>{let xx=50+i/71*970,yy=350-z/max*320;i?c.lineTo(xx,yy):c.moveTo(xx,yy)});c.stroke()}
line(Array(72).fill(1),'#bbb',[3,3]);ds.forEach(d=>line(d.curve,'#668bbb'));line(Array(72).fill(x.cutoff),'#d77900',[6,4]);line(x.observed,'black');c.setLineDash([]);c.fillStyle='black';c.fillText('Q / era-p99; top '+max.toFixed(2),50,18);c.fillText('Response hours 1–72 (verification only)',380,385);document.getElementById('ids').textContent=ds.length?ds.map(d=>d.id).join('\\n'):'No eligible earlier completed donor group.'}
e.onchange=choose;v.onchange=draw;choose();</script>"""
    (out / "event_browser.html").write_text(page.replace("PAYLOAD", data))


def evidence_tables_and_figures(out, rows, donors, inventory, response, history):
    """Census contrasts plus explicitly outcome-selected benefit/failure illustrations."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    keys = ["cohort", "scenario", "analysis", "target_k", "query_event_id"]
    raw = rows[rows.arm.eq("raw_state")].set_index(keys)
    ttm = rows[rows.arm.eq("ttm_ordered_state")].set_index(keys).loc[raw.index]
    contrasted = ttm[["query_river", "actual_donor_count", "archive_status"]].copy()
    for metric in [
        *C.METRICS,
        "duration_estimate_absolute_error_h",
        "final_24h_level_absolute_error",
    ]:
        contrasted[f"ttm_minus_raw_{metric}"] = ttm[metric] - raw[metric]
    contrasted = contrasted.reset_index()
    meta = inventory.set_index("event_id")
    for column in [
        "response_peak_at_first_hour",
        "response_ends_above_p99",
        "additional_q_only_input",
    ]:
        contrasted[column] = contrasted.query_event_id.map(meta[column])
    contrasted.to_csv(out / "event_method_contrasts.csv", index=False)
    for phase in ["response_peak_at_first_hour", "response_ends_above_p99"]:
        contrasted.groupby(["cohort", "scenario", "analysis", "target_k", phase]).filter(
            lambda g: len(g) > 0
        ).groupby(["cohort", "scenario", "analysis", "target_k", phase])[
            [c for c in contrasted if c.startswith("ttm_minus_raw_")]
        ].agg(["mean", "count"]).to_csv(out / f"by_{phase}.csv")
    main = contrasted[
        contrasted.cohort.eq("q_only_pooled")
        & contrasted.scenario.eq("other_rivers")
        & contrasted.analysis.eq("main")
        & contrasted.target_k.eq(5)
    ]
    examples = []
    directory = out / "illustrations"
    directory.mkdir(exist_ok=True)
    metric = "ttm_minus_raw_ensemble_curve_level_rmse"
    for river, group in main.groupby("query_river"):
        for direction, row in [
            ("closer", group.loc[group[metric].idxmin()]),
            ("less_close", group.loc[group[metric].idxmax()]),
        ]:
            eid = row.query_event_id
            d = donors[
                donors.cohort.eq("q_only_pooled")
                & donors.scenario.eq("other_rivers")
                & donors.analysis.eq("main")
                & donors.query_event_id.eq(eid)
                & donors["rank"].le(5)
            ]
            fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
            axes[0].plot(
                np.arange(-511, 1), history.loc[eid], color="black", lw=2, label="Query history"
            )
            for ax, arm in zip(axes[1:], ["raw_state", "ttm_ordered_state"], strict=True):
                ids = d[d.arm.eq(arm)].sort_values("rank").analogue_event_id.tolist()
                a = response.loc[ids].to_numpy()
                for donor in a:
                    ax.plot(np.arange(1, 73), donor, color="#668bbb", alpha=0.45, lw=0.8)
                ax.plot(np.arange(1, 73), a.mean(axis=0), color="#275a85", lw=2, label="Donor mean")
                ax.plot(
                    np.arange(1, 73),
                    response.loc[eid],
                    color="black",
                    lw=2,
                    label="Observed response",
                )
                ax.axhline(
                    meta.loc[eid, "cutoff_q_over_p99_h0"],
                    color="#d77900",
                    ls="--",
                    label="Cutoff persistence",
                )
                ax.set_title(arm + "; " + str(len(ids)) + " prior groups")
                ax.set_xlabel("Response hour (verification only)")
                ax.legend(fontsize=7)
            # Shared response scale makes the two method panels directly comparable.
            ymax = (
                max(
                    response.loc[eid].max(),
                    response.loc[d.analogue_event_id].to_numpy().max(),
                    meta.loc[eid, "cutoff_q_over_p99_h0"],
                )
                * 1.05
            )
            for ax in axes[1:]:
                ax.set_ylim(0, ymax)
            for ax in axes:
                ax.axhline(1, color="grey", lw=0.6)
                ax.set_ylabel("Q / own era-p99")
            axes[0].set_title("Available cutoff history")
            axes[0].set_xlabel("Relative hour; cutoff = 0")
            fig.suptitle(
                f"{river}: {eid}\nOutcome-selected illustration; TTM minus raw curve RMSE {row[metric]:+.4f}; measurement concern {meta.loc[eid, 'measurement_concern']}",
                fontsize=9,
            )
            fig.tight_layout()
            name = river.replace("/", "_") + "_" + direction + ".png"
            fig.savefig(directory / name, dpi=120)
            plt.close(fig)
            examples.append(
                {
                    "query_event_id": eid,
                    "river": river,
                    "selection": direction,
                    "curve_rmse_difference": row[metric],
                    "actual_peak_over_p99": response.loc[eid].max(),
                    "actual_high_water_hours": int((response.loc[eid] >= 1).sum()),
                    "actual_first_peak_hour": int(response.loc[eid].to_numpy().argmax() + 1),
                    "measurement_concern": meta.loc[eid, "measurement_concern"],
                    "figure": "illustrations/" + name,
                }
            )
    pd.DataFrame(examples).to_csv(out / "outcome_selected_illustrations.csv", index=False)


def audit_existing(out, inventory, response, history, hashes):
    """Verify saved retrieval; independently recompute every selected-pair/set score."""
    receipt = json.loads((out / "manifest.json").read_text())
    if hashes != receipt["input_sha256"]:
        raise ValueError("Prepared inputs changed")
    for name, digest in receipt["outputs_sha256"].items():
        if S.TTM.sha256(out / name) != digest:
            raise ValueError(f"Changed saved output: {name}")
    rows = pd.read_csv(out / "event_assessments.csv", float_precision="round_trip")
    donors = pd.read_csv(out / "selected_donors.csv", float_precision="round_trip")
    keys = ["cohort", "scenario", "analysis", "arm"]
    checked_pairs, checked_sets = 0, 0
    for config, d in donors.groupby(keys):
        q = response.loc[d.query_event_id].to_numpy()
        a = response.loc[d.analogue_event_id].to_numpy()
        qp, ap = q.max(axis=1), a.max(axis=1)
        direct = {
            "level_rmse_p99": np.sqrt(((q - a) ** 2).mean(axis=1)),
            "peak_scaled_shape_rmse": np.sqrt(
                ((q / qp[:, None] - a / ap[:, None]) ** 2).mean(axis=1)
            ),
            "peak_time_difference_h": abs(q.argmax(axis=1) - a.argmax(axis=1)),
            "high_water_duration_difference_h": abs((q >= 1).sum(axis=1) - (a >= 1).sum(axis=1)),
            "excess_area_difference_p99_h": abs(
                np.maximum(q - 1, 0).sum(axis=1) - np.maximum(a - 1, 0).sum(axis=1)
            ),
            "terminal_peak_ratio_difference": abs(
                q[:, -24:].mean(axis=1) / qp - a[:, -24:].mean(axis=1) / ap
            ),
        }
        for column, values in direct.items():
            np.testing.assert_allclose(d[column], values, rtol=0, atol=1e-12)
        if (
            d.duplicated(["query_event_id", "rank"]).any()
            or d.duplicated(["query_event_id", "analogue_storm_id"]).any()
        ):
            raise ValueError("Duplicated donor rank/group")
        if d.analogue_storm_id.eq(d.query_storm_id).any():
            raise ValueError("Own group leaked")
        if (
            pd.to_datetime(d.analogue_onset_utc, utc=True) + pd.Timedelta(hours=72)
            > pd.to_datetime(d.query_onset_utc, utc=True)
        ).any():
            raise ValueError("Future donor response leaked")
        if config[1] == "other_rivers" and d.query_river.eq(d.analogue_river).any():
            raise ValueError("Physical-river exclusion failed")
        subset = rows.copy()
        for key, value in zip(keys, config, strict=True):
            subset = subset[subset[key].eq(value)]
        for k in [5, 10]:
            scores = subset[subset.target_k.eq(k)].set_index("query_event_id")
            for eid, g in d[d["rank"].le(k)].groupby("query_event_id"):
                a = response.loc[g.analogue_event_id].to_numpy()
                q = response.loc[eid].to_numpy()
                scored = scores.loc[eid]
                np.testing.assert_allclose(
                    scored.mean_donor_peak_absolute_error,
                    abs(a.max(axis=1).mean() - q.max()),
                    rtol=0,
                    atol=1e-12,
                )
                np.testing.assert_allclose(
                    scored.ensemble_curve_level_rmse,
                    np.sqrt(((a.mean(axis=0) - q) ** 2).mean()),
                    rtol=0,
                    atol=1e-12,
                )
                np.testing.assert_allclose(
                    scored.duration_estimate_absolute_error_h,
                    abs((a >= 1).sum(axis=1).mean() - (q >= 1).sum()),
                    rtol=0,
                    atol=1e-12,
                )
                np.testing.assert_allclose(
                    scored.final_24h_level_absolute_error,
                    abs(a[:, -24:].mean() - q[-24:].mean()),
                    rtol=0,
                    atol=1e-12,
                )
                assert scored.actual_donor_count == min(k, scored.candidate_groups)
                checked_sets += 1
        checked_pairs += len(d)
    assert checked_sets == len(rows)
    intervals = pd.read_csv(out / "paired_intervals.csv", float_precision="round_trip")
    pd.testing.assert_frame_equal(
        intervals, paired_intervals(rows), check_exact=False, rtol=0, atol=1e-12
    )
    metrics = [*C.METRICS, "duration_estimate_absolute_error_h", "final_24h_level_absolute_error"]
    rows.groupby([*keys, "target_k", "archive_status"])[metrics].agg(["mean", "count"]).to_csv(
        out / "by_archive_status.csv"
    )
    own = inventory.set_index("event_id")
    rows["additional_q_only_input"] = rows.query_event_id.map(own.additional_q_only_input)
    rows.groupby([*keys, "target_k", "additional_q_only_input"])[metrics].agg(
        ["mean", "count"]
    ).to_csv(out / "by_additional_input.csv")
    write_browser(out, inventory, response, donors, history)
    evidence_tables_and_figures(out, rows, donors, inventory, response, history)
    receipt["verified_upstream_inputs_sha256"] = json.loads((READY / "manifest.json").read_text())[
        "input_sha256"
    ]
    receipt["figure_sha256"] = {
        str(p.relative_to(out)): S.TTM.sha256(p)
        for p in sorted((out / "illustrations").glob("*.png"))
    }
    receipt["postprocessing_source_sha256"] = S.TTM.sha256(Path(__file__))
    receipt["outputs_sha256"] = {
        p.name: S.TTM.sha256(p) for p in out.iterdir() if p.suffix in {".csv", ".html"}
    }
    (out / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    validation = {
        "independently_checked_selected_slots": checked_pairs,
        "independently_checked_score_sets": checked_sets,
        "paired_interval_rows_recomputed": len(intervals),
        "maximum_allowed_numeric_difference": 1e-12,
        "chronology_unique_groups_cross_river": "pass",
        "prepared_and_saved_hashes": "pass",
        "no_retrieval_changed": True,
        "human_verdicts_assigned": 0,
    }
    (out / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps(validation))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--audit-existing", action="store_true")
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((READY / "manifest.json").read_text())
    # Verify prepared artifacts before any retrieval; editable review is not an input.
    hashes = {}
    for key, digest in manifest["outputs_sha256"].items():
        path = READY / key
        if P.S.TTM.sha256(path) != digest:
            raise ValueError(f"Changed prepared artifact: {path}")
        hashes[str(path.relative_to(ROOT))] = digest
    # Bind provider windows/metadata to the preparation, not merely today's upstream run.
    for name, digest in manifest["input_sha256"].items():
        if S.TTM.sha256(ROOT / name) != digest:
            raise ValueError(f"Changed upstream preparation input: {name}")
    C.verified_run_inputs()
    inventory = pd.read_csv(READY / "event_inventory.csv")
    meta = inventory.set_index("event_id")
    signatures = pd.read_csv(READY / "q_only_signatures.csv", parse_dates=["onset_utc"])
    signatures["physical_river_group"] = signatures.event_id.map(meta.physical_river_group)
    _, _, index, windows = C.REVIEW.load_inputs()
    response, _, _ = C.CENSUS.load_curves(index, windows)
    history = (
        windows.pivot(index="event_id", columns="relative_hour", values="target_discharge_m3s")
        .loc[:, -511:0]
        .div(meta.p99_m3s, axis=0)
    )
    if args.audit_existing:
        audit_existing(out, inventory, response, history, hashes)
        return
    raw = pd.read_parquet(READY / "q_only_standardized_histories.parquet")
    ordered = pd.read_parquet(READY / "q_only_ttm_ordered.parquet")
    state = pd.read_parquet(READY / "q_only_discharge_state.parquet")
    arms = {"r1": {"representation_vectors": raw}}
    for name, vector in [("raw_state", raw), ("ttm_ordered_state", ordered)]:
        arms[name] = {
            "distance_blocks": {"temporal": vector, "state": state},
            "robust_distance_blocks": ("state",),
        }
    references = pd.read_csv(READY / "archive_and_reference_inventory.csv")
    results, selected = [], []
    for cohort in ["q_only_dutch", "q_only_pooled"]:
        sample = signatures.copy()
        if cohort == "q_only_dutch":
            sample = sample[sample.event_id.map(meta.country).eq("NL")].copy()
        for scenario in ["all_rivers", "other_rivers"]:
            for quality in [False, True]:
                analysis = "quality_sensitivity" if quality else "main"
                expected = None
                for arm, settings in arms.items():
                    scores, donors = B.retrieve_prior_analogues(
                        sample,
                        top_k=10,
                        min_candidates=1,
                        min_candidate_storms=1,
                        allow_short_archive=True,
                        exclude_same_river=scenario == "other_rivers",
                        exclude_measurement_concerns=quality,
                        **settings,
                    )
                    ids = set(scores.query_event_id)
                    if expected is not None and ids != expected:
                        raise ValueError("Arm coverage differs")
                    expected = ids
                    if donors.analogue_storm_id.eq(donors.query_storm_id).any():
                        raise ValueError("Query onset group leaked")
                    if (
                        pd.to_datetime(donors.analogue_onset_utc, utc=True) + pd.Timedelta(hours=72)
                        > pd.to_datetime(donors.query_onset_utc, utc=True)
                    ).any():
                        raise ValueError("Donor outcome not completed")
                    for target_k in [5, 10]:
                        d = donors[donors["rank"].le(target_k)]
                        rows, pairs = C.assess(scores, d, response, meta)
                        phases = []
                        for qid, g in d.groupby("query_event_id"):
                            phases.append(
                                {
                                    "query_event_id": qid,
                                    **phase_evidence(
                                        response.loc[qid],
                                        response.loc[g.analogue_event_id],
                                        meta.loc[qid, "cutoff_q_over_p99_h0"],
                                    ),
                                }
                            )
                        rows = rows.merge(
                            pd.DataFrame(phases), on="query_event_id", validate="one_to_one"
                        )
                        ref = references[
                            references.cohort.eq(cohort)
                            & references.scenario.eq(scenario)
                            & references.analysis.eq(analysis)
                        ]
                        rows = rows.merge(
                            ref[
                                [
                                    "query_event_id",
                                    "candidate_events",
                                    "candidate_groups",
                                    "archive_status",
                                    "matches_fixed_k_comparison",
                                    "group_balanced_median_absolute_error",
                                    "persistence_peak_absolute_error",
                                ]
                            ],
                            on="query_event_id",
                            validate="one_to_one",
                        )
                        np.testing.assert_array_equal(rows.candidate_count, rows.candidate_events)
                        np.testing.assert_array_equal(
                            rows.candidate_storm_count, rows.candidate_groups
                        )
                        np.testing.assert_array_equal(
                            rows.actual_donor_count, np.minimum(target_k, rows.candidate_groups)
                        )
                        for column in [
                            "persistence_curve_level_rmse",
                            "persistence_high_water_duration_absolute_error",
                        ]:
                            rows[column] = rows.query_event_id.map(meta[column])
                        for frame in [rows, pairs]:
                            (
                                frame["cohort"],
                                frame["scenario"],
                                frame["analysis"],
                                frame["arm"],
                                frame["target_k"],
                            ) = cohort, scenario, analysis, arm, target_k
                        if (
                            scenario == "other_rivers"
                            and pairs.query_river.eq(pairs.analogue_river).any()
                        ):
                            raise ValueError("Own river leaked")
                        results.append(rows)
                        if target_k == 10:
                            selected.append(pairs)
                    print(f"{cohort}/{scenario}/{analysis}/{arm}: {len(scores)}", flush=True)
    rows, donors = pd.concat(results, ignore_index=True), pd.concat(selected, ignore_index=True)
    rows.to_csv(out / "event_assessments.csv", index=False)
    donors.to_csv(out / "selected_donors.csv", index=False)
    references[references.cohort.isin(["q_only_dutch", "q_only_pooled"])].to_csv(
        out / "coverage_including_unavailable.csv", index=False
    )
    metrics = [
        *C.METRICS,
        "duration_estimate_absolute_error_h",
        "final_24h_level_absolute_error",
        "persistence_peak_absolute_error",
        "persistence_curve_level_rmse",
        "group_balanced_median_absolute_error",
    ]
    rows.groupby(["cohort", "scenario", "analysis", "arm", "target_k"])[metrics].mean().to_csv(
        out / "summary.csv"
    )
    rows.groupby(["cohort", "scenario", "analysis", "arm", "target_k", "query_river"])[metrics].agg(
        ["mean", "count"]
    ).to_csv(out / "by_river.csv")
    paired_intervals(rows).to_csv(out / "paired_intervals.csv", index=False)
    # Keep existing conventional and AlphaEarth evidence accessible, unchanged.
    existing = pd.read_csv(READY / "existing_results_with_explicit_references.csv")
    existing[existing.arm.isin(["r0", "r3_alphaearth", "fusion_raw", "fusion_ttm"])].to_csv(
        out / "existing_context_comparisons.csv", index=False
    )
    write_browser(out, inventory, response, donors, history)
    receipt = {
        "input_sha256": hashes,
        "verified_upstream_inputs_sha256": manifest["input_sha256"],
        "source_sha256": {
            str(p.relative_to(ROOT)): S.TTM.sha256(p)
            for p in [
                Path(__file__),
                ROOT / "scripts/65_hydrological_analogue_baseline.py",
                ROOT / "scripts/78_cross_river_analogue_checks.py",
            ]
        },
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scorable_events": int(inventory.q_only_scoring_sample.sum()),
        "scored_sets": len(rows),
        "selected_slots": len(donors),
        "bootstrap_draws": 9999,
        "seed": 20261013,
        "short_archive_rule": "Available distinct groups, at most target k; no archive retained as unavailable",
        "interpretation": "Retrospective fixed archive; no human verdicts or calibrated forecast probabilities",
        "outputs_sha256": {
            p.name: S.TTM.sha256(p) for p in out.iterdir() if p.suffix in {".csv", ".html"}
        },
    }
    (out / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    audit_existing(out, inventory, response, history, hashes)
    print(json.dumps({k: receipt[k] for k in ["scorable_events", "scored_sets", "selected_slots"]}))


if __name__ == "__main__":
    main()
