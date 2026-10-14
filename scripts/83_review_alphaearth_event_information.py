#!/usr/bin/env python3
"""Matched AlphaEarth donor changes, specificity and existing-context controls.

Original mean-TTM family plus the already-held ordered-TTM/state readout.
No training, downloads, weight search, outcome-based ranks or human verdicts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "information", ROOT / "scripts/82_review_analogue_information.py"
)
INFO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INFO)
E, C, B = INFO.E, INFO.E.C, INFO.E.B
OUT = ROOT / "results/basin_ai_alphaearth_information_review"
METRICS = [*C.METRICS, "duration_estimate_absolute_error_h", "final_24h_level_absolute_error"]
CONTROLS = ["temporal", "area", "identity", "static_2017", "alphaearth"]


def context_arms(joined, mean, ordered, state, years):
    common = joined[joined.alphaearth_input_sample].copy()
    blocks = C.REVIEW.CONTEXT.context_blocks(common, mean)
    identity = pd.get_dummies(common.set_index("event_id").gauge, dtype=float)
    bands = [f"A{i:02d}" for i in range(64)]
    fixed = years[years.embedding_year.eq(2017)].set_index("gauge")[bands]
    static = fixed.loc[common.gauge].copy()
    static.index = common.event_id
    static = static.div(np.linalg.norm(static.to_numpy(), axis=1), axis=0)
    contexts = {
        "area": blocks["area"],
        "identity": identity,
        "static_2017": static,
        "alphaearth": blocks["alphaearth"],
    }
    families = {
        "mean": {"ttm": blocks["ttm"]},
        "ordered_state": {
            "temporal": ordered.loc[common.event_id],
            "state": state.loc[common.event_id],
        },
    }
    arms = {("conventional", "r0"): {}}
    for family, base in families.items():
        for control in CONTROLS:
            settings = {
                "distance_blocks": {
                    **base,
                    **({control: contexts[control]} if control != "temporal" else {}),
                }
            }
            if family == "ordered_state":
                settings["robust_distance_blocks"] = ("state",)
            arms[(family, control)] = settings
    return arms, common


def donor_change(reference, challenger, metric="peak_scaled_shape_rmse"):
    """Exact event/group overlap and additive pair-metric replacement accounting."""
    a = reference.set_index("analogue_event_id")
    b = challenger.set_index("analogue_event_id")
    if len(a) != len(b) or not a.index.is_unique or not b.index.is_unique:
        raise ValueError("Equal-size distinct donor sets required")
    shared = set(a.index) & set(b.index)
    entered = set(b.index) - set(a.index)
    exited = set(a.index) - set(b.index)
    actual = float(b[metric].mean() - a[metric].mean())
    replacement = float(
        (b.loc[sorted(entered), metric].sum() - a.loc[sorted(exited), metric].sum()) / len(a)
    )
    np.testing.assert_allclose(actual, replacement, rtol=0, atol=1e-12)
    return {
        "shared_events": len(shared),
        "changed_events": len(entered),
        "donor_jaccard": len(shared) / (len(a) + len(b) - len(shared)),
        "shared_onset_groups": len(set(a.analogue_storm_id) & set(b.analogue_storm_id)),
        "entered_mean_shape_error": float(b.loc[sorted(entered), metric].mean())
        if entered
        else np.nan,
        "exited_mean_shape_error": float(a.loc[sorted(exited), metric].mean())
        if exited
        else np.nan,
        "replacement_shape_difference": replacement,
    }


def inspect_pairs(donors, common):
    details = common.set_index("event_id")
    for role, key in [("query", "query_event_id"), ("analogue", "analogue_event_id")]:
        for field in ["gauge", "embedding_year", "catchment_area_km2"]:
            donors[role + "_" + field] = donors[key].map(details[field])
    donors["same_gauge"] = donors.query_gauge.eq(donors.analogue_gauge)
    donors["absolute_log_area_difference"] = abs(
        np.log(donors.query_catchment_area_km2 / donors.analogue_catchment_area_km2)
    )
    annual = details[[f"A{i:02d}" for i in range(64)]].to_numpy(float, copy=True)
    annual /= np.linalg.norm(annual, axis=1)[:, None]
    positions = pd.Series(np.arange(len(details)), index=details.index)
    donors["annual_context_vector_distance"] = np.linalg.norm(
        annual[donors.query_event_id.map(positions)]
        - annual[donors.analogue_event_id.map(positions)],
        axis=1,
    )
    # Context distances describe routing; they do not validate response relevance.
    if donors.query_gauge.isna().any() or donors.analogue_gauge.isna().any():
        raise ValueError("Unmapped context donor")
    return donors


def paired_intervals(rows):
    intervals = []
    for (scenario, analysis, k), g in rows.groupby(["scenario", "analysis", "target_k"]):
        conventional = g[g.family.eq("conventional")].set_index("query_event_id")
        for family in ["mean", "ordered_state"]:
            ae = g[g.family.eq(family) & g.control.eq("alphaearth")].set_index("query_event_id")
            for control in ["temporal", "area", "identity", "static_2017", "r0", "archive"]:
                ref = (
                    conventional
                    if control == "r0"
                    else ae
                    if control == "archive"
                    else g[g.family.eq(family) & g.control.eq(control)].set_index("query_event_id")
                )
                if set(ref.index) != set(ae.index):
                    raise ValueError("Mismatched comparison queries")
                ref = ref.loc[ae.index]
                for metric in METRICS:
                    if control == "archive" and metric not in INFO.METRICS:
                        continue
                    reference_metric = INFO.METRICS[metric] if control == "archive" else metric
                    f = ae[["query_storm_id", "query_onset_utc"]].copy()
                    f["difference"] = ae[metric] - ref[reference_metric]
                    f["storm_year"] = pd.to_datetime(
                        f.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
                    ).dt.year
                    for unit in ["query_storm_id", "storm_year"]:
                        intervals.append(
                            {
                                "scenario": scenario,
                                "analysis": analysis,
                                "target_k": k,
                                "family": family,
                                "reference": control,
                                "metric": metric,
                                "resampling_unit": unit,
                                **C.REVIEW.cluster_interval(f, unit),
                            }
                        )
    return pd.DataFrame(intervals)


def select_cases(rows, changes):
    """Outcome-independent river sentinels plus clearly outcome-selected illustrations."""
    ae = rows[
        rows.scenario.eq("other_rivers")
        & rows.analysis.eq("main")
        & rows.target_k.eq(5)
        & rows.family.eq("ordered_state")
        & rows.control.eq("alphaearth")
    ]
    # Three per river rather than expanding the previous case packet unnecessarily.
    selected = INFO.select_sentinels(ae)
    selected = selected[~selected.selection_reason.str.startswith("middle_date")].copy()
    selected["selection_kind"] = "outcome_independent"
    selected["family"] = "ordered_state"
    selected["scenario"] = "other_rivers"
    others = []
    for (family, scenario), g in changes[
        changes.analysis.eq("main") & changes.target_k.eq(5) & changes.reference.eq("temporal")
    ].groupby(["family", "scenario"]):
        for reason, row in [
            ("largest_shape_improvement", g.loc[g.replacement_shape_difference.idxmin()]),
            ("largest_shape_deterioration", g.loc[g.replacement_shape_difference.idxmax()]),
        ]:
            others.append(
                {
                    "query_event_id": row.query_event_id,
                    "query_river": row.query_river,
                    "selection_reason": reason,
                    "selection_kind": "outcome_selected",
                    "family": family,
                    "scenario": scenario,
                }
            )
    return pd.concat([selected, pd.DataFrame(others)], ignore_index=True)


def render_cases(chosen, rows, donors, history, response, meta):
    directory = OUT / "cases"
    directory.mkdir(exist_ok=True)
    for case in chosen.itertuples(index=False):
        eid = case.query_event_id
        base = donors[
            donors.scenario.eq(case.scenario)
            & donors.analysis.eq("main")
            & donors.family.eq(case.family)
            & donors.query_event_id.eq(eid)
            & donors["rank"].le(5)
        ]
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        controls = ["temporal", "alphaearth", "static_2017", "area", "identity"]
        ax = axes.flat[0]
        ax.plot(np.arange(-511, 1), history.loc[eid], color="black")
        ax.axhline(1, color="grey", lw=0.6)
        ax.set_title("Cutoff history; Q / own p99")
        ax.set_xlabel("Relative hour")
        ymax = (
            max(
                response.loc[eid].max(),
                response.loc[base.analogue_event_id].to_numpy().max(),
                meta.loc[eid, "cutoff_q_over_p99_h0"],
            )
            * 1.05
        )
        for ax, control in zip(list(axes.flat)[1:], controls, strict=True):
            ids = base[base.control.eq(control)].sort_values("rank").analogue_event_id.tolist()
            values = response.loc[ids].to_numpy()
            for a in values:
                ax.plot(np.arange(1, 73), a, color="#668bbb", alpha=0.4, lw=0.8)
            ax.plot(
                np.arange(1, 73), values.mean(axis=0), color="#275a85", lw=1.8, label="Donor mean"
            )
            ax.plot(
                np.arange(1, 73), response.loc[eid], color="black", lw=2, label="Query verification"
            )
            ax.axhline(
                meta.loc[eid, "cutoff_q_over_p99_h0"], ls="--", color="#d77900", label="Cutoff Q"
            )
            ax.axhline(1, color="grey", lw=0.6)
            ax.set_ylim(0, ymax)
            ax.set_title(control + "; " + str(len(ids)) + " prior groups")
            ax.set_xlabel("Response hour")
            ax.set_ylabel("Q / own p99")
        axes.flat[2].legend(fontsize=7)
        fig.suptitle(
            eid
            + "\n"
            + case.family
            + " / "
            + case.scenario
            + " / "
            + case.selection_kind
            + " / "
            + case.selection_reason,
            fontsize=10,
        )
        fig.tight_layout()
        fig.savefig(
            directory
            / (
                case.family
                + "_"
                + case.scenario
                + "_"
                + eid.replace("|", "_").replace(":", "").replace("+", "")
                + ".png"
            ),
            dpi=110,
        )
        plt.close(fig)


def audit_saved():
    """Verify existing outputs independently; add case facts without reranking."""
    receipt = json.loads((OUT / "manifest.json").read_text())
    for name, digest in receipt["input_sha256"].items():
        if E.S.TTM.sha256(ROOT / name) != digest:
            raise ValueError("Changed input: " + name)
    for name, digest in receipt["output_sha256"].items():
        if E.S.TTM.sha256(OUT / name) != digest:
            raise ValueError("Changed saved output: " + name)
    rows = pd.read_csv(OUT / "query_evidence.csv", float_precision="round_trip")
    donors = pd.read_csv(OUT / "selected_donor_evidence.csv", float_precision="round_trip")
    _, _, index, windows = C.REVIEW.load_inputs()
    response, _, _ = C.CENSUS.load_curves(index, windows)
    checked = 0
    for config, d in donors.groupby(["scenario", "analysis", "family", "control"]):
        q = response.loc[d.query_event_id].to_numpy()
        a = response.loc[d.analogue_event_id].to_numpy()
        qp = q.max(axis=1)
        ap = a.max(axis=1)
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
        for metric, value in direct.items():
            np.testing.assert_allclose(d[metric], value, rtol=0, atol=1e-12)
        subset = rows.copy()
        for key, value in zip(["scenario", "analysis", "family", "control"], config, strict=True):
            subset = subset[subset[key].eq(value)]
        for k in [5, 10]:
            scores = subset[subset.target_k.eq(k)].set_index("query_event_id")
            for eid, g in d[d["rank"].le(k)].groupby("query_event_id"):
                a = response.loc[g.analogue_event_id].to_numpy()
                q = response.loc[eid].to_numpy()
                score = scores.loc[eid]
                expected = {
                    "mean_donor_peak_absolute_error": abs(a.max(axis=1).mean() - q.max()),
                    "ensemble_curve_level_rmse": np.sqrt(((a.mean(axis=0) - q) ** 2).mean()),
                    "duration_estimate_absolute_error_h": abs(
                        (a >= 1).sum(axis=1).mean() - (q >= 1).sum()
                    ),
                    "final_24h_level_absolute_error": abs(a[:, -24:].mean() - q[-24:].mean()),
                }
                for metric, value in expected.items():
                    np.testing.assert_allclose(score[metric], value, rtol=0, atol=1e-12)
                assert len(g) == min(k, score.candidate_storm_count)
                checked += 1
    recomputed_intervals = paired_intervals(rows)
    pd.testing.assert_frame_equal(
        pd.read_csv(OUT / "paired_intervals.csv", float_precision="round_trip"),
        recomputed_intervals,
        check_exact=False,
        rtol=0,
        atol=1e-12,
    )
    # A fixed same-site indicator is constant when all donors are other sites.
    for (_analysis, _family), d in donors[
        donors.scenario.eq("other_rivers") & donors.family.ne("conventional")
    ].groupby(["analysis", "family"]):
        a = (
            d[d.control.eq("temporal")]
            .sort_values(["query_event_id", "rank"])
            .reset_index(drop=True)
        )
        b = (
            d[d.control.eq("identity")]
            .sort_values(["query_event_id", "rank"])
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(
            a[["query_event_id", "rank", "analogue_event_id"]],
            b[["query_event_id", "rank", "analogue_event_id"]],
        )
    static_old = pd.read_csv(
        ROOT / "results/basin_ai_representation_checks/all_selected_pair_diagnostics.csv",
        float_precision="round_trip",
    )
    replay = []
    for analysis in ["main", "quality_sensitivity"]:
        old = (
            static_old[
                static_old.cohort.eq("context")
                & static_old.analysis.eq(analysis)
                & static_old.arm.eq("r3_static_2017")
            ]
            .sort_values(["query_event_id", "rank"])
            .reset_index(drop=True)
        )
        new = (
            donors[
                donors.family.eq("mean")
                & donors.scenario.eq("all_rivers")
                & donors.analysis.eq(analysis)
                & donors.control.eq("static_2017")
                & donors["rank"].le(5)
                & donors.query_event_id.isin(old.query_event_id)
            ]
            .sort_values(["query_event_id", "rank"])
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(
            old[["query_event_id", "rank", "analogue_event_id"]],
            new[["query_event_id", "rank", "analogue_event_id"]],
        )
        np.testing.assert_allclose(old.distance, new.distance, rtol=0, atol=1e-12)
        replay.append(
            {
                "analysis": analysis,
                "queries": old.query_event_id.nunique(),
                "status": "static-2017 original donors/distances replayed",
            }
        )
    pd.DataFrame(replay).to_csv(OUT / "static_original_replay.csv", index=False)
    geography = []
    for k in [5, 10]:
        d = donors[donors["rank"].le(k)].copy()
        g = (
            d.groupby(["scenario", "analysis", "family", "control"])[
                ["same_gauge", "absolute_log_area_difference", "annual_context_vector_distance"]
            ]
            .mean()
            .reset_index()
        )
        g["target_k"] = k
        geography.append(g)
    pd.concat(geography, ignore_index=True).to_csv(OUT / "donor_context_by_k.csv", index=False)
    chosen = pd.read_csv(OUT / "review_cases.csv")
    meta = pd.read_csv(E.READY / "event_inventory.csv").set_index("event_id")
    facts = []
    for case in chosen.itertuples(index=False):
        selected = rows[
            rows.scenario.eq(case.scenario)
            & rows.analysis.eq("main")
            & rows.family.eq(case.family)
            & rows.target_k.eq(5)
            & rows.query_event_id.eq(case.query_event_id)
        ]
        for score in selected.itertuples(index=False):
            d = donors[
                donors.scenario.eq(case.scenario)
                & donors.analysis.eq("main")
                & donors.family.eq(case.family)
                & donors.control.eq(score.control)
                & donors.query_event_id.eq(case.query_event_id)
                & donors["rank"].le(5)
            ]
            facts.append(
                {
                    "query_event_id": case.query_event_id,
                    "family": case.family,
                    "scenario": case.scenario,
                    "selection_kind": case.selection_kind,
                    "selection_reason": case.selection_reason,
                    "control": score.control,
                    "cutoff_q_over_p99": meta.loc[case.query_event_id, "cutoff_q_over_p99_h0"],
                    "measurement_concern": score.query_measurement_concern,
                    "actual_donor_count": score.actual_donor_count,
                    "same_gauge_share": d.same_gauge.mean(),
                    "donor_ids": " ; ".join(d.sort_values("rank").analogue_event_id),
                    "observed_peak": score.observed_peak_over_p99_72h,
                    "observed_peak_hour": meta.loc[case.query_event_id, "response_first_peak_hour"],
                    "observed_high_water_hours": score.observed_high_water_hours,
                    **{metric: getattr(score, metric) for metric in METRICS},
                }
            )
    pd.DataFrame(facts).to_csv(OUT / "case_facts.csv", index=False)
    # River-by-river directions are descriptive, with only six geographic units.
    contrasts = []
    for config, g in rows.groupby(["scenario", "analysis", "family", "target_k"]):
        if config[2] == "conventional":
            continue
        ae = g[g.control.eq("alphaearth")].set_index("query_event_id")
        for control in ["temporal", "area", "identity", "static_2017"]:
            ref = g[g.control.eq(control)].set_index("query_event_id").loc[ae.index]
            delta = ae[["query_river"]].copy()
            for metric in METRICS:
                delta[metric] = ae[metric] - ref[metric]
            r = delta.groupby("query_river")[METRICS].mean().reset_index()
            for key, value in zip(
                ["scenario", "analysis", "family", "target_k"], config, strict=True
            ):
                r[key] = value
            r["reference"] = control
            contrasts.append(r)
    pd.concat(contrasts, ignore_index=True).to_csv(OUT / "paired_river_directions.csv", index=False)
    validation = json.loads((OUT / "validation.json").read_text())
    validation.update(
        {
            "independent_pair_slots_verified": len(donors),
            "independent_score_sets_verified": checked,
            "interval_rows_recomputed": len(recomputed_intervals),
            "cross_river_identity_matches_temporal": True,
            "static_original_replay_queries": [r["queries"] for r in replay],
        }
    )
    (OUT / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    # Preserve all context responses, including six missing-archive episodes.
    coverage = pd.read_csv(OUT / "context_coverage.csv")
    wide = coverage.copy()
    selected = rows[
        rows.scenario.eq("other_rivers") & rows.analysis.eq("main") & rows.target_k.eq(5)
    ]
    for (family, control), g in selected.groupby(["family", "control"]):
        values = g[["query_event_id", *METRICS]].rename(
            columns={m: family + "__" + control + "__" + m for m in METRICS}
        )
        wide = wide.merge(
            values,
            left_on="event_id",
            right_on="query_event_id",
            how="left",
            validate="one_to_one",
            suffixes=("", "_joined"),
        ).drop(columns=["query_event_id_joined"], errors="ignore")
    wide.to_csv(OUT / "event_comparison_census.csv", index=False)
    years = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
    held = (
        years.groupby(["gauge", "experiment_role"])
        .embedding_year.agg(["min", "max", "count"])
        .reset_index()
    )
    held["included_in_this_matched_review"] = held.gauge.isin(coverage.gauge)
    held.to_csv(OUT / "held_context_assets.csv", index=False)
    note_path = ROOT / "docs/reviews/limburg-alphaearth-case-notes-2026-10-14.json"
    if note_path.exists():
        notes = pd.DataFrame(json.loads(note_path.read_text())["records"])
        notes.to_csv(OUT / "ai_case_review.csv", index=False)
        receipt["ai_note_source_sha256"] = E.S.TTM.sha256(note_path)
    receipt["postprocessing_source_sha256"] = E.S.TTM.sha256(Path(__file__))
    receipt["dependency_source_sha256"] = {
        str(p.relative_to(ROOT)): E.S.TTM.sha256(p)
        for p in [
            ROOT / "scripts/82_review_analogue_information.py",
            ROOT / "scripts/81_run_expanded_event_analogues.py",
            ROOT / "scripts/65_hydrological_analogue_baseline.py",
        ]
    }
    receipt["output_sha256"] = {
        str(p.relative_to(OUT)): E.S.TTM.sha256(p)
        for p in OUT.rglob("*")
        if p.suffix in [".csv", ".png"]
    }
    (OUT / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(validation))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-existing", action="store_true")
    args = parser.parse_args()
    if args.audit_existing:
        audit_saved()
        return
    OUT.mkdir(exist_ok=True)
    hashes = C.verified_run_inputs()
    # Prior saved tables are immutable controls; no upstream writing/build_arms.
    old_manifest = json.loads((C.OUT / "manifest.json").read_text())
    for name, digest in old_manifest["outputs_sha256"].items():
        if E.S.TTM.sha256(C.OUT / name) != digest:
            raise ValueError("Changed old result " + name)
    samples, representations, index, windows = C.REVIEW.load_inputs()
    sample = samples["context"].copy()
    inventory = pd.read_csv(E.READY / "event_inventory.csv")
    meta = inventory.set_index("event_id")
    sample["physical_river_group"] = sample.event_id.map(meta.physical_river_group)
    joined = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/event_embeddings.parquet")
    years = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
    mean = representations["pooled"]["r2"]["representation_vectors"]
    ordered = pd.read_parquet(
        ROOT / "results/basin_ai_representation_checks/ordered_patch_embeddings.parquet"
    )
    state = pd.read_parquet(
        ROOT / "results/basin_ai_representation_checks/discharge_state_blocks.parquet"
    )
    common_years = joined[joined.alphaearth_input_sample]
    if not common_years.embedding_year.eq(common_years.event_year - 1).all():
        raise ValueError("Context must be from the specified prior year")
    for name in [
        "results/basin_ai_event_interpretation_ready/event_inventory.csv",
        "results/basin_ai_alphaearth/event_embeddings.parquet",
        "results/basin_ai_alphaearth/catchment_year_embeddings.parquet",
        "results/basin_ai_representation_checks/discharge_state_blocks.parquet",
    ]:
        hashes[name] = E.S.TTM.sha256(ROOT / name)
    arms, common = context_arms(joined, mean, ordered, state, years)
    response, _, _ = C.CENSUS.load_curves(index, windows)
    history = (
        windows.pivot(index="event_id", columns="relative_hour", values="target_discharge_m3s")
        .loc[:, -511:0]
        .div(meta.p99_m3s, axis=0)
    )
    sets = []
    pairs = []
    references = []
    replays = []
    old = pd.read_csv(C.OUT / "selected_donors.csv", float_precision="round_trip")
    original_names = {
        "temporal": "r2",
        "area": "r2_area",
        "identity": "r2_identity",
        "alphaearth": "r3_alphaearth",
        "r0": "r0",
    }
    for scenario in ["all_rivers", "other_rivers"]:
        for quality in [False, True]:
            analysis = "quality_sensitivity" if quality else "main"
            query_ids = None
            for (family, control), settings in arms.items():
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
                if query_ids is not None and set(scores.query_event_id) != query_ids:
                    raise ValueError("Control eligibility differs")
                query_ids = set(scores.query_event_id)
                if donors.analogue_storm_id.eq(donors.query_storm_id).any():
                    raise ValueError("Same onset group")
                if (
                    pd.to_datetime(donors.analogue_onset_utc, utc=True) + pd.Timedelta(hours=72)
                    > pd.to_datetime(donors.query_onset_utc, utc=True)
                ).any():
                    raise ValueError("Unfinished prior outcome")
                if (
                    scenario == "other_rivers"
                    and donors.query_event_id.map(meta.physical_river_group)
                    .eq(donors.analogue_event_id.map(meta.physical_river_group))
                    .any()
                ):
                    raise ValueError("Same physical river")
                for k in [5, 10]:
                    d = donors[donors["rank"].le(k)]
                    evaluated, scored = C.assess(scores, d, response, meta)
                    phases = [
                        {
                            "query_event_id": eid,
                            **E.phase_evidence(
                                response.loc[eid],
                                response.loc[g.analogue_event_id],
                                meta.loc[eid, "cutoff_q_over_p99_h0"],
                            ),
                        }
                        for eid, g in d.groupby("query_event_id")
                    ]
                    evaluated = evaluated.merge(
                        pd.DataFrame(phases), on="query_event_id", validate="one_to_one"
                    )
                    for frame in [evaluated, scored]:
                        (
                            frame["scenario"],
                            frame["analysis"],
                            frame["family"],
                            frame["control"],
                            frame["target_k"],
                        ) = scenario, analysis, family, control, k
                    sets.append(evaluated)
                    if k == 10:
                        pairs.append(scored)
                if family in ["mean", "conventional"] and control in original_names:
                    prior = old[
                        old.cohort.eq("context")
                        & old.scenario.eq(scenario)
                        & old.analysis.eq(analysis)
                        & old.arm.eq(original_names[control])
                        & old.k.eq(10)
                    ]
                    replay = (
                        donors[donors.query_event_id.isin(prior.query_event_id)]
                        .sort_values(["query_event_id", "rank"])
                        .reset_index(drop=True)
                    )
                    prior = prior.sort_values(["query_event_id", "rank"]).reset_index(drop=True)
                    pd.testing.assert_frame_equal(
                        replay[["query_event_id", "rank", "analogue_event_id"]],
                        prior[["query_event_id", "rank", "analogue_event_id"]],
                    )
                    np.testing.assert_allclose(replay.distance, prior.distance, rtol=0, atol=1e-12)
                    replays.append(
                        {
                            "scenario": scenario,
                            "analysis": analysis,
                            "control": control,
                            "old_queries": prior.query_event_id.nunique(),
                            "status": "exact donor/rank/distance replay",
                        }
                    )
                print(f"{scenario}/{analysis}/{family}/{control}: {len(scores)}", flush=True)
            complete = sample[sample.complete_scoring_sample].copy()
            if quality:
                complete = complete[~complete.measurement_concern]
            for eid in sorted(query_ids):
                q = complete[complete.event_id.eq(eid)].iloc[0]
                candidates = complete[
                    (complete.onset_utc + pd.Timedelta(hours=72)).le(q.onset_utc)
                    & complete.storm_id.ne(q.storm_id)
                ]
                if scenario == "other_rivers":
                    candidates = candidates[
                        candidates.physical_river_group.ne(q.physical_river_group)
                    ]
                evidence, curve = INFO.archive_evidence(
                    response.loc[eid], response.loc[candidates.event_id], candidates.storm_id
                )
                grouped = response.loc[candidates.event_id].copy()
                grouped["group"] = candidates.storm_id.to_numpy()
                np.testing.assert_allclose(
                    curve, grouped.groupby("group").mean().mean().to_numpy(), rtol=0, atol=1e-12
                )
                references.append(
                    {
                        "scenario": scenario,
                        "analysis": analysis,
                        "query_event_id": eid,
                        "archive_candidate_events": len(candidates),
                        "archive_candidate_groups": candidates.storm_id.nunique(),
                        **evidence,
                    }
                )
    rows = pd.concat(sets, ignore_index=True)
    donors = inspect_pairs(pd.concat(pairs, ignore_index=True), common)
    refs = pd.DataFrame(references)
    rows = rows.merge(refs, on=["scenario", "analysis", "query_event_id"], validate="many_to_one")
    np.testing.assert_array_equal(rows.candidate_count, rows.archive_candidate_events)
    np.testing.assert_array_equal(rows.candidate_storm_count, rows.archive_candidate_groups)
    rows.to_csv(OUT / "query_evidence.csv", index=False)
    donors.to_csv(OUT / "selected_donor_evidence.csv", index=False)
    refs.to_csv(OUT / "generic_context_archive.csv", index=False)
    pd.DataFrame(replays).to_csv(OUT / "old_control_replay.csv", index=False)
    rows.groupby(["scenario", "analysis", "family", "control", "target_k"])[METRICS].mean().to_csv(
        OUT / "summary.csv"
    )
    rows.groupby(["scenario", "analysis", "family", "control", "target_k", "query_river"])[
        METRICS
    ].agg(["mean", "count"]).to_csv(OUT / "by_river.csv")
    intervals = paired_intervals(rows)
    intervals.to_csv(OUT / "paired_intervals.csv", index=False)
    changes = []
    for (scenario, analysis, family, k), r in rows[rows.family.ne("conventional")].groupby(
        ["scenario", "analysis", "family", "target_k"]
    ):
        d = donors[
            donors.scenario.eq(scenario)
            & donors.analysis.eq(analysis)
            & donors.family.eq(family)
            & donors["rank"].le(k)
        ]
        by = {(control, eid): g for (control, eid), g in d.groupby(["control", "query_event_id"])}
        for eid in r.query_event_id.unique():
            ae = by[("alphaearth", eid)]
            for control in ["temporal", "area", "identity", "static_2017"]:
                evidence = donor_change(by[(control, eid)], ae)
                changes.append(
                    {
                        "scenario": scenario,
                        "analysis": analysis,
                        "family": family,
                        "target_k": k,
                        "reference": control,
                        "query_event_id": eid,
                        "query_river": meta.loc[eid, "physical_river_group"],
                        **evidence,
                    }
                )
    changes = pd.DataFrame(changes)
    changes.to_csv(OUT / "donor_set_changes.csv", index=False)
    changes.groupby(["scenario", "analysis", "family", "target_k", "reference"])[
        [
            "shared_events",
            "changed_events",
            "donor_jaccard",
            "shared_onset_groups",
            "replacement_shape_difference",
        ]
    ].mean().to_csv(OUT / "donor_change_summary.csv")
    donors.groupby(["scenario", "analysis", "family", "control"])[
        ["same_gauge", "absolute_log_area_difference", "annual_context_vector_distance"]
    ].mean().to_csv(OUT / "donor_context_summary.csv")
    chosen = select_cases(rows, changes)
    chosen.to_csv(OUT / "review_cases.csv", index=False)
    render_cases(chosen, rows, donors, history, response, meta)
    # Match coverage of all 296 context responses, with missing estimates for no archive.
    census = common[common.alphaearth_scoring_sample].copy()
    count = rows[
        rows.scenario.eq("other_rivers")
        & rows.analysis.eq("main")
        & rows.family.eq("mean")
        & rows.control.eq("alphaearth")
        & rows.target_k.eq(5)
    ]
    census = census.merge(
        count[["query_event_id", "candidate_storm_count", "actual_donor_count"]],
        left_on="event_id",
        right_on="query_event_id",
        how="left",
        validate="one_to_one",
    )
    census.to_csv(OUT / "context_coverage.csv", index=False)
    validation = {
        "matched_queries_all_controls": True,
        "finished_prior_groups_and_cross_river": True,
        "old_controls_replayed": len(replays),
        "archive_curves_independently_verified": len(refs),
        "replacement_decompositions_verified": len(changes),
        "human_verdicts": 0,
    }
    (OUT / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    receipt = {
        "status": "Detailed matched context review; AI case notes separate from human validation",
        "input_sha256": hashes,
        "source_sha256": E.S.TTM.sha256(Path(__file__)),
        "families": ["original mean-TTM", "existing ordered-TTM + state"],
        "weights": "equal RMS-scaled distance blocks; robust state block as existing; no weight tuning",
        "bootstrap_draws": 9999,
        "seed": 20261013,
        "sample_inputs": len(common),
        "sample_responses": len(census),
        "scored_sets": len(rows),
        "selected_slots": len(donors),
        "case_rows": len(chosen),
        "output_sha256": {
            str(p.relative_to(OUT)): E.S.TTM.sha256(p)
            for p in OUT.rglob("*")
            if p.suffix in [".csv", ".png"]
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in [
                    "sample_inputs",
                    "sample_responses",
                    "scored_sets",
                    "selected_slots",
                    "case_rows",
                ]
            }
        )
    )

    audit_saved()


if __name__ == "__main__":
    main()
