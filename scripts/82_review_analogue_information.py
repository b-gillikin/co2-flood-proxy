#!/usr/bin/env python3
"""Describe information in fixed analogues relative to their eligible prior archive.

No reranking/training, new input, relevance threshold, or human verdict.
Outcome-blind sentinel selection uses dates, rivers and prior donor disagreement.
"""

from __future__ import annotations

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
    "expanded", ROOT / "scripts/81_run_expanded_event_analogues.py"
)
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)
READY = E.READY
INPUT = E.OUT
OUT = ROOT / "results/basin_ai_information_review"
KEYS = ["scenario", "analysis", "query_event_id"]
METRICS = {
    "ensemble_curve_level_rmse": "archive_curve_level_rmse",
    "mean_peak_scaled_shape_rmse": "archive_mean_individual_shape_rmse",
    "duration_estimate_absolute_error_h": "archive_duration_absolute_error_h",
    "final_24h_level_absolute_error": "archive_final_24h_level_absolute_error",
    "mean_donor_peak_absolute_error": "archive_mean_peak_absolute_error",
}


def archive_evidence(query, candidates, groups):
    """Equal mass per onset group, equal members inside it; no similarity search."""
    q = np.asarray(query, float)
    a = np.asarray(candidates, float)
    g = pd.Series(np.asarray(groups))
    if q.shape != (72,) or a.ndim != 2 or a.shape[1] != 72 or len(a) != len(g) or not len(a):
        raise ValueError("Complete query and nonempty matching archive required")
    if (
        not np.isfinite(q).all()
        or not np.isfinite(a).all()
        or g.isna().any()
        or (a.max(axis=1) <= 0).any()
        or q.max() <= 0
    ):
        raise ValueError("Finite positive-peak responses and named groups required")
    weights = 1 / g.map(g.value_counts()).to_numpy(float) / g.nunique()
    curve = weights @ a
    peaks = a.max(axis=1)
    return {
        "archive_curve_level_rmse": float(np.sqrt(((curve - q) ** 2).mean())),
        "archive_mean_individual_shape_rmse": float(
            weights @ np.sqrt(((a / peaks[:, None] - q / q.max()) ** 2).mean(axis=1))
        ),
        "archive_duration_estimate_h": float(weights @ (a >= 1).sum(axis=1)),
        "archive_duration_absolute_error_h": float(
            abs(weights @ (a >= 1).sum(axis=1) - (q >= 1).sum())
        ),
        "archive_final_24h_mean_level": float(curve[-24:].mean()),
        "archive_final_24h_level_absolute_error": float(abs(curve[-24:].mean() - q[-24:].mean())),
        "archive_mean_peak_absolute_error": float(abs(weights @ peaks - q.max())),
    }, curve


def select_sentinels(rows):
    """Four per physical river: first full-five archive, middle, latest, max prior spread.

    The selector reads no response/accuracy/measurement outcome. Duplicate choices
    are filled in chronological order. Short/no archives are reviewed separately.
    """
    needed = [
        "query_event_id",
        "query_river",
        "query_onset_utc",
        "actual_donor_count",
        "curve_spread",
    ]
    sample = rows[needed].copy().sort_values(["query_onset_utc", "query_event_id"])
    picked = []
    for river, g in sample.groupby("query_river", sort=True):
        eligible = g[g.actual_donor_count.ge(5)].copy()
        if eligible.empty:
            continue  # Illustration availability must not stop the census analysis.
        options = [
            ("earliest_full_five", eligible.iloc[0]),
            ("middle_date", eligible.iloc[len(eligible) // 2]),
            ("latest_date", eligible.iloc[-1]),
            (
                "largest_prior_curve_spread",
                eligible.sort_values(
                    ["curve_spread", "query_onset_utc", "query_event_id"],
                    ascending=[False, True, True],
                ).iloc[0],
            ),
        ]
        used = set()
        for reason, row in options:
            if row.query_event_id in used:
                remaining = eligible[~eligible.query_event_id.isin(used)]
                if remaining.empty:
                    continue
                row = remaining.iloc[0]
                reason += "__chronological_duplicate_fill"
            used.add(row.query_event_id)
            picked.append(
                {
                    "query_event_id": row.query_event_id,
                    "query_river": river,
                    "selection_reason": reason,
                }
            )
    return pd.DataFrame(picked)


def make_review_pages(out, chosen, rows, donors, meta, history, response, archive_curves):
    """Separate cutoff-only page from response verification, same fixed selected IDs."""
    main = rows[rows.scenario.eq("other_rivers") & rows.analysis.eq("main") & rows.target_k.eq(5)]
    d = donors[
        donors.scenario.eq("other_rivers") & donors.analysis.eq("main") & donors["rank"].le(5)
    ]
    directory = out / "sentinel_pages"
    directory.mkdir(exist_ok=True)
    facts = []
    for river, g in chosen.groupby("query_river"):
        ids = g.query_event_id.tolist()
        fig, axes = plt.subplots(len(ids), 2, figsize=(13, 3.2 * len(ids)), squeeze=False)
        verify, vaxes = plt.subplots(len(ids), 2, figsize=(13, 3.2 * len(ids)), squeeze=False)
        for r, eid in enumerate(ids):
            own = history.loc[eid].to_numpy()
            evidence = meta.loc[eid]
            for col, arm in enumerate(["raw_state", "ttm_ordered_state"]):
                prior = d[d.query_event_id.eq(eid) & d.arm.eq(arm)].sort_values("rank")
                pids = prior.analogue_event_id.tolist()
                ax = axes[r, col]
                for pid in pids:
                    ax.plot(
                        np.arange(-511, 1), history.loc[pid], color="#668bbb", alpha=0.4, lw=0.8
                    )
                ax.plot(np.arange(-511, 1), own, color="black", lw=1.8)
                ax.axhline(1, color="grey", lw=0.6)
                ax.set_title(eid + "\n" + arm + "; complete histories only", fontsize=8)
                ax.set_xlabel("Relative hour: cutoff = 0")
                ax.set_ylabel("Q / own era-p99")
                ax.set_ylim(0, max(history.loc[pids].to_numpy().max(), own.max()) * 1.05)
                values = response.loc[pids].to_numpy()
                va = vaxes[r, col]
                for a in values:
                    va.plot(np.arange(1, 73), a, color="#668bbb", alpha=0.4, lw=0.8)
                va.plot(
                    np.arange(1, 73),
                    values.mean(axis=0),
                    color="#275a85",
                    lw=1.8,
                    label="Selected donor mean",
                )
                va.plot(
                    np.arange(1, 73),
                    archive_curves[("other_rivers", "main", eid)],
                    color="#a23c91",
                    ls=":",
                    lw=1.8,
                    label="Group-balanced eligible archive",
                )
                va.plot(
                    np.arange(1, 73), response.loc[eid], color="black", lw=2, label="Observed query"
                )
                va.axhline(
                    evidence.cutoff_q_over_p99_h0,
                    color="#d77900",
                    ls="--",
                    label="Cutoff persistence",
                )
                va.axhline(1, color="grey", lw=0.6)
                va.set_title(eid + "\n" + arm, fontsize=8)
                va.set_xlabel("Verification response hour")
                va.set_ylabel("Q / own era-p99")
                if r == 0:
                    va.legend(fontsize=7)
                score = main[main.query_event_id.eq(eid) & main.arm.eq(arm)].iloc[0]
                facts.append(
                    {
                        "query_event_id": eid,
                        "arm": arm,
                        "cutoff_q_over_p99": evidence.cutoff_q_over_p99_h0,
                        "prior_6h_change_over_p99": evidence.cutoff_q_change_6h_over_p99,
                        "prior_24h_change_over_p99": evidence.cutoff_q_change_24h_over_p99,
                        "prior_24h_rain_mm": evidence.cutoff_rain_sum_24h_mm,
                        "source_concern": evidence.measurement_concern,
                        "candidate_groups": score.candidate_groups,
                        "curve_spread": score.curve_spread,
                        "donor_ids": " ; ".join(pids),
                        "observed_peak": response.loc[eid].max(),
                        "observed_peak_hour": int(response.loc[eid].to_numpy().argmax() + 1),
                        "observed_high_water_hours": int((response.loc[eid] >= 1).sum()),
                        "curve_error": score.ensemble_curve_level_rmse,
                        "archive_curve_error": score.archive_curve_level_rmse,
                        "duration_error": score.duration_estimate_absolute_error_h,
                        "final_24h_level_error": score.final_24h_level_absolute_error,
                    }
                )
            lim = max(max(ax.get_ylim()[1] for ax in vaxes[r]), 1.05)
            for ax in vaxes[r]:
                ax.set_ylim(0, lim)
        for f, name in [(fig, "input_only"), (verify, "verification")]:
            f.suptitle(
                river + " — " + name + "; cases selected without query response/error", fontsize=11
            )
            f.tight_layout()
            f.savefig(directory / (river.replace("/", "_") + "_" + name + ".png"), dpi=110)
            plt.close(f)
    pd.DataFrame(facts).to_csv(out / "sentinel_facts.csv", index=False)


def main():
    OUT.mkdir(exist_ok=True)
    source = json.loads((INPUT / "manifest.json").read_text())
    hashes = {}
    for name, digest in source["outputs_sha256"].items():
        p = INPUT / name
        if E.S.TTM.sha256(p) != digest:
            raise ValueError("Changed expanded output: " + name)
        hashes[str(p.relative_to(ROOT))] = digest
    prep = json.loads((READY / "manifest.json").read_text())
    for name, digest in prep["input_sha256"].items():
        if E.S.TTM.sha256(ROOT / name) != digest:
            raise ValueError("Changed preparation source: " + name)
    for name, digest in prep["outputs_sha256"].items():
        if E.S.TTM.sha256(READY / name) != digest:
            raise ValueError("Changed prepared artifact: " + name)
        hashes[str((READY / name).relative_to(ROOT))] = digest
    rows = pd.read_csv(INPUT / "event_assessments.csv", float_precision="round_trip")
    rows = rows[rows.cohort.eq("q_only_pooled")].copy()
    donors = pd.read_csv(INPUT / "selected_donors.csv", float_precision="round_trip")
    donors = donors[donors.cohort.eq("q_only_pooled")].copy()
    sig = pd.read_csv(READY / "q_only_signatures.csv", parse_dates=["onset_utc"])
    inventory = pd.read_csv(READY / "event_inventory.csv")
    meta = inventory.set_index("event_id")
    _, _, index, windows = E.C.REVIEW.load_inputs()
    response, _, _ = E.C.CENSUS.load_curves(index, windows)
    history = (
        windows.pivot(index="event_id", columns="relative_hour", values="target_discharge_m3s")
        .loc[:, -511:0]
        .div(meta.p99_m3s, axis=0)
    )
    complete = sig[sig.complete_scoring_sample].copy()
    refs = []
    previous_numeric = {
        p.name: E.S.TTM.sha256(p)
        for p in OUT.glob("*.csv")
        if p.name
        not in [
            "ai_case_review.csv",
            "ai_cutoff_notes_before_verification.csv",
            "archive_limit_cases.csv",
            "numeric_improvement_counts.csv",
        ]
    }
    archive_curves = {}
    for scenario in ["all_rivers", "other_rivers"]:
        for analysis in ["main", "quality_sensitivity"]:
            available = complete if analysis == "main" else complete[~complete.measurement_concern]
            matched = rows[rows.scenario.eq(scenario) & rows.analysis.eq(analysis)]
            for eid in sorted(matched.query_event_id.unique()):
                event = available[available.event_id.eq(eid)].iloc[0]
                candidates = available[
                    (available.onset_utc + pd.Timedelta(hours=72)).le(event.onset_utc)
                    & available.storm_id.ne(event.storm_id)
                ]
                if scenario == "other_rivers":
                    candidates = candidates[
                        candidates.event_id.map(meta.physical_river_group).ne(
                            meta.loc[eid, "physical_river_group"]
                        )
                    ]
                evidence, curve = archive_evidence(
                    response.loc[eid], response.loc[candidates.event_id], candidates.storm_id
                )
                # Independent groupby aggregation verifies event/group weighting.
                by_group = response.loc[candidates.event_id].copy()
                by_group["onset_group"] = candidates.storm_id.to_numpy()
                independent_curve = by_group.groupby("onset_group").mean().mean().to_numpy()
                np.testing.assert_allclose(curve, independent_curve, rtol=0, atol=1e-12)
                refs.append(
                    {
                        "scenario": scenario,
                        "analysis": analysis,
                        "query_event_id": eid,
                        "archive_candidate_events": len(candidates),
                        "archive_candidate_groups": candidates.storm_id.nunique(),
                        **evidence,
                    }
                )
                archive_curves[(scenario, analysis, eid)] = curve
            print(f"{scenario}/{analysis}: {matched.query_event_id.nunique()} archives", flush=True)
    refs = pd.DataFrame(refs)
    refs.to_csv(OUT / "eligible_archive_response_references.csv", index=False)
    rows = rows.merge(refs, on=KEYS, validate="many_to_one")
    np.testing.assert_array_equal(rows.candidate_events, rows.archive_candidate_events)
    np.testing.assert_array_equal(rows.candidate_groups, rows.archive_candidate_groups)
    for metric, ref in METRICS.items():
        rows[metric + "_minus_archive"] = rows[metric] - rows[ref]
    rows.to_csv(OUT / "event_information_evidence.csv", index=False)
    measures = list(METRICS) + list(METRICS.values()) + [m + "_minus_archive" for m in METRICS]
    rows.groupby(["scenario", "analysis", "arm", "target_k"])[measures].mean().to_csv(
        OUT / "information_summary.csv"
    )
    rows.groupby(["scenario", "analysis", "arm", "target_k", "query_river"])[measures].agg(
        ["mean", "count"]
    ).to_csv(OUT / "information_by_river.csv")
    comparisons = []
    for (scenario, analysis, arm, k), g in rows[rows.arm.ne("r1")].groupby(
        ["scenario", "analysis", "arm", "target_k"]
    ):
        f = g[["query_event_id", "query_storm_id", "query_onset_utc"]].copy()
        f["storm_year"] = pd.to_datetime(
            f.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
        ).dt.year
        for metric in METRICS:
            f["difference"] = g[metric + "_minus_archive"]
            for unit in ["query_storm_id", "storm_year"]:
                comparisons.append(
                    {
                        "scenario": scenario,
                        "analysis": analysis,
                        "arm": arm,
                        "target_k": k,
                        "metric": metric,
                        "resampling_unit": unit,
                        **E.C.REVIEW.cluster_interval(f, unit),
                    }
                )
    pd.DataFrame(comparisons).to_csv(OUT / "archive_specificity_intervals.csv", index=False)
    cutoff = rows[
        rows.scenario.eq("other_rivers")
        & rows.analysis.eq("main")
        & rows.arm.eq("ttm_ordered_state")
        & rows.target_k.eq(5)
    ]
    chosen = select_sentinels(cutoff)
    chosen.to_csv(OUT / "outcome_blind_sentinels.csv", index=False)
    make_review_pages(OUT, chosen, rows, donors, meta, history, response, archive_curves)
    counts = []
    for config, g in rows.groupby(["scenario", "analysis", "arm", "target_k"]):
        for metric in METRICS:
            difference = g[metric + "_minus_archive"]
            counts.append(
                {
                    **dict(zip(["scenario", "analysis", "arm", "target_k"], config, strict=True)),
                    "metric": metric,
                    "lower_error_than_archive": int((difference < -1e-12).sum()),
                    "equal_within_numeric_tolerance": int((difference.abs() <= 1e-12).sum()),
                    "higher_error_than_archive": int((difference > 1e-12).sum()),
                    "median_difference": float(difference.median()),
                    "meaning": "Metric comparison only; no human utility verdict",
                }
            )
    pd.DataFrame(counts).to_csv(OUT / "numeric_improvement_counts.csv", index=False)
    coverage = pd.read_csv(INPUT / "coverage_including_unavailable.csv")
    limited = coverage[
        coverage.cohort.eq("q_only_pooled")
        & coverage.scenario.eq("other_rivers")
        & coverage.analysis.eq("main")
        & coverage.candidate_groups.lt(5)
    ].copy()
    limited = limited.merge(
        inventory[
            [
                "event_id",
                "cutoff_q_over_p99_h0",
                "cutoff_q_change_6h_over_p99",
                "measurement_concern",
                "response_peak_over_p99",
                "response_high_water_hours_72h",
            ]
        ],
        left_on="query_event_id",
        right_on="event_id",
        validate="one_to_one",
    )
    limited["interpretation_constraint"] = (
        "Few/no completed prior groups; inspect individual precedents and source record; zero donor spread is not calibrated confidence"
    )
    limited.to_csv(OUT / "archive_limit_cases.csv", index=False)
    note_path = ROOT / "docs/reviews/limburg-ai-case-notes-2026-10-14.json"
    if note_path.exists():
        notes = pd.DataFrame(json.loads(note_path.read_text())["records"])
        notes = notes[notes.query_event_id.isin(chosen.query_event_id)].copy()
        notes.to_csv(OUT / "ai_case_review.csv", index=False)
        notes.drop(
            columns=[
                "observed_verification_ai",
                "analogue_information_added_ai",
                "review_date",
                "review_design",
            ]
        ).to_csv(OUT / "ai_cutoff_notes_before_verification.csv", index=False)
        hashes[str(note_path.relative_to(ROOT))] = E.S.TTM.sha256(note_path)
    validation = {
        "independent_group_balanced_curves_checked": len(refs),
        "candidate_counts_match_expanded_run": True,
        "numeric_tables_identical_to_previous_execution": all(
            E.S.TTM.sha256(OUT / name) == digest for name, digest in previous_numeric.items()
        ),
        "human_verdicts_assigned": 0,
        "sentinel_selection_query_response_fields_used": 0,
    }
    (OUT / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    # One row for every scorable episode, including all six unavailable archives.
    census = inventory[inventory.q_only_scoring_sample].copy()
    census = census.rename(columns={"event_id": "query_event_id"})
    main = rows[rows.scenario.eq("other_rivers") & rows.analysis.eq("main") & rows.target_k.eq(5)]
    detail = [
        "actual_donor_count",
        "analogue_prediction",
        "estimated_high_water_hours",
        "estimated_final_24h_mean_over_p99",
        "curve_spread",
        *METRICS,
    ]
    for arm in ["r1", "raw_state", "ttm_ordered_state"]:
        a = main[main.arm.eq(arm)][["query_event_id", *detail]].rename(
            columns={c: arm + "__" + c for c in detail}
        )
        census = census.merge(a, on="query_event_id", how="left", validate="one_to_one")
    archive = refs[refs.scenario.eq("other_rivers") & refs.analysis.eq("main")].drop(
        columns=["scenario", "analysis"]
    )
    census = census.merge(archive, on="query_event_id", how="left", validate="one_to_one")
    for metric, reference in METRICS.items():
        census["ttm_minus_archive__" + metric] = (
            census["ttm_ordered_state__" + metric] - census[reference]
        )
        census["ttm_minus_raw__" + metric] = (
            census["ttm_ordered_state__" + metric] - census["raw_state__" + metric]
        )
    census["analogue_evidence_status"] = np.where(
        census["ttm_ordered_state__actual_donor_count"].notna(),
        "available_prior_responses",
        "no_finished_prior_group",
    )
    census.to_csv(OUT / "event_information_census.csv", index=False)
    receipt = {
        "census_events": len(census),
        "status": "numeric specificity and outcome-blind case packet; AI judgments recorded separately; no human verdicts",
        "input_sha256": {**hashes, **prep["input_sha256"]},
        "source_sha256": E.S.TTM.sha256(Path(__file__)),
        "dependency_source_sha256": {
            str(p.relative_to(ROOT)): E.S.TTM.sha256(p)
            for p in [
                ROOT / "scripts/81_run_expanded_event_analogues.py",
                ROOT / "scripts/74_review_analogue_census.py",
                ROOT / "scripts/73_analogue_uncertainty_review.py",
            ]
        },
        "score_sets": len(rows),
        "archive_queries": len(refs),
        "sentinels": len(chosen),
        "archive_weighting": "equal group mass / equal within-group event mass; finished prior responses only",
        "selection": "dates and prior donor spread; no query response or accuracy input",
        "bootstrap_draws": 9999,
        "seed": 20261013,
        "output_sha256": {
            str(p.relative_to(OUT)): E.S.TTM.sha256(p)
            for p in OUT.rglob("*")
            if p.suffix in [".csv", ".png"]
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ["score_sets", "archive_queries", "sentinels"]}))


if __name__ == "__main__":
    main()
