"""Matched archive reference and common-donor supplemental contrasts; no new inference."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import assess_selected, event_vectors, load_script, retrieve
from src.eo_followup import (
    METRICS,
    archive_metrics,
    cluster_intervals_multi,
    eligible_archive,
    feature_complete,
)
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import fresh_output
from src.eo_retrieval_cache import RetrievalCache

OUT = ROOT / "results/eo_followup_2026_10_27"
INDEPENDENT = ROOT / "results/eo_followup_independent_2026_10_27"
VARIANTS = {
    "satmae_toa_qa60": "satmae",
    "copernicus_fm_toa_qa60": "copernicus_fm",
    "croma_ascending_15": "croma",
    "croma_ascending_161": "croma",
}
KEYS = ["kind", "cohort", "scenario", "analysis", "policy", "target_k"]


def inputs():
    ready = ROOT / "results/basin_ai_event_interpretation_ready"
    meta = pd.read_csv(ready / "event_inventory.csv", parse_dates=["onset_utc"]).set_index(
        "event_id"
    )
    sample = pd.read_csv(ready / "q_only_signatures.csv", parse_dates=["onset_utc"])
    for c in ["country", "physical_river_group"]:
        sample[c] = sample.event_id.map(meta[c])
    rain = pd.read_csv(
        ROOT / "results/basin_ai_cross_border_completion/rainfall_event_coverage.csv"
    ).set_index("event_id")
    for c in rain:
        if c not in ("country", "complete_scoring_sample"):
            sample[c] = sample.event_id.map(rain[c])
    base = load_script("65_hydrological_analogue_baseline.py", "followup_base")
    raw = pd.read_parquet(ready / "q_only_standardized_histories.parquet")
    ttm = pd.read_parquet(ready / "q_only_ttm_ordered.parquet")
    state = pd.read_parquet(ready / "q_only_discharge_state.parquet")
    ids = (
        set(sample.loc[sample.complete_scoring_sample, "event_id"])
        & set(raw.index)
        & set(ttm.index)
        & set(state.index)
    )
    sample = sample[sample.event_id.isin(ids)].copy()
    years = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
    key = pd.DataFrame(
        {
            "event_id": meta.index,
            "gauge": meta.gauge.replace(
                {"2828300000200": "herzogenrath_1", "2828900000200": "randerath"}
            ),
            "embedding_year": meta.onset_utc.dt.year - 1,
        }
    )
    alpha_frame = key.merge(
        years, on=["gauge", "embedding_year"], how="inner", validate="many_to_one"
    ).set_index("event_id")[[f"A{i:02d}" for i in range(64)]]
    alpha_frame = alpha_frame.div(np.linalg.norm(alpha_frame, axis=1), axis=0).dropna()
    alpha = set(alpha_frame.index)
    return (
        sample,
        meta,
        raw,
        ttm,
        state,
        base,
        set(
            sample.loc[sample.event_id.map(rain.complete_scoring_sample).fillna(False), "event_id"]
        ),
        set(sample.loc[feature_complete(sample, base.FEATURE_COLUMNS), "event_id"]),
        alpha,
    )


def vectors_for(comparison, kind, obs, links):
    manifest = json.loads((comparison / "manifest.json").read_text())
    out = {}
    for model in ROUTES:
        paths = [p for p in manifest["input_sha256"] if p.endswith("/" + model + ".parquet")]
        if len(paths) != 1:
            raise ValueError("Ambiguous model source " + model)
        path = ROOT / paths[0]
        if sha256(path) != manifest["input_sha256"][paths[0]]:
            raise ValueError("Changed representation")
        out[model] = event_vectors(obs, links, pd.read_parquet(path), kind)
    return out


def cohort_population(name, sample, vectors, rain_ids, alpha_ids):
    ids = set(sample.event_id)
    if "all_ten_matched" in name:
        for v in vectors.values():
            ids &= set(v.index)
    else:
        model = name.split("_available_", 1)[1]
        ids &= set(vectors[model].index)
    if name.startswith("rain"):
        ids &= rain_ids
    if name.startswith("alphaearth"):
        ids &= alpha_ids
    return sample[sample.event_id.isin(ids)].copy()


def interval_rows(frame, group_columns, value_columns, review):
    rows = []
    for config, g in frame.groupby(group_columns, observed=True, dropna=False):
        config = config if isinstance(config, tuple) else (config,)
        ids = g[["query_event_id", "query_storm_id", "query_onset_utc"]].copy()
        ids["storm_year"] = pd.to_datetime(
            ids.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
        ).dt.year
        for column in value_columns.values():
            ids[column] = g[column].to_numpy()
        for unit in ["query_storm_id", "storm_year"]:
            estimates = cluster_intervals_multi(ids, unit, list(value_columns.values()))
            for metric, column in value_columns.items():
                rows.append(
                    {
                        **dict(zip(group_columns, config, strict=True)),
                        "metric": metric,
                        "resampling_unit": unit,
                        **estimates[column],
                    }
                )
    return pd.DataFrame(rows)


def archive_specs(include_rain=True):
    specs = [("main", ROOT / "results/eo_analogue_comparison_coherent_v1", False)]
    specs += [(n, ROOT / "results/eo_expansion_comparisons" / n, False) for n in VARIANTS]
    if include_rain:
        specs += [("rain168", ROOT / "results/eo_analogue_comparison_rain168_v1", True)]
    return specs


def reuse_independent(folder, destination):
    """Validate frozen partial results and link immutable large files without copying."""
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest.get("status") != "completed" or manifest.get("stage") != "independent":
        raise ValueError("Independent stage is not complete")
    for section in ["input_sha256", "source_sha256"]:
        for name, digest in manifest[section].items():
            if sha256(ROOT / name) != digest:
                raise ValueError("Independent stage dependency changed: " + name)
    for name, digest in manifest["outputs_sha256"].items():
        if sha256(folder / name) != digest:
            raise ValueError("Independent stage output changed: " + name)
    # These tables will be combined, not modified through a hard link.
    combined = {"archive_summary.parquet", "archive_intervals.parquet", "archive_progress.json"}
    for name in manifest["outputs_sha256"]:
        if name in combined:
            continue
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(folder / name, target)


def archive_pass(
    sample, meta, old_rain, new_rain, alpha, obs, links, evaluator, *, specs=None, prior=None
):
    cache = {}
    summary = [] if prior is None else [pd.read_parquet(prior / "archive_summary.parquet")]
    intervals = [] if prior is None else [pd.read_parquet(prior / "archive_intervals.parquet")]
    support = [] if prior is None else json.loads((prior / "archive_progress.json").read_text())
    specs = archive_specs() if specs is None else specs
    for label, comparison, is_new in specs:
        dest = OUT / "archive_reference" / label
        dest.mkdir(parents=True, exist_ok=True)
        for kind in ["monthly_snapshot", "monthly", "recent"]:
            vectors = vectors_for(comparison, kind, obs, links)
            cols = KEYS + [
                "arm",
                "query_event_id",
                "query_storm_id",
                "query_onset_utc",
                "query_country",
                "query_river",
                "actual_donor_count",
                "candidate_count",
                "candidate_storm_count",
                *METRICS,
            ]
            table = pq.read_table(
                comparison / "event_assessments.parquet",
                columns=cols,
                filters=[("kind", "==", kind)],
            )
            f = table.to_pandas(
                categories=[
                    "kind",
                    "cohort",
                    "scenario",
                    "analysis",
                    "policy",
                    "arm",
                    "query_country",
                    "query_river",
                ]
            )
            pieces = []
            for (cohort, scenario, analysis, policy), g in f.groupby(
                ["cohort", "scenario", "analysis", "policy"], observed=True
            ):
                population = cohort_population(
                    str(cohort), sample, vectors, new_rain if is_new else old_rain, alpha
                )
                population_key = tuple(sorted(population.event_id))
                indexed = population.set_index("event_id", drop=False)
                refs = []
                for qid in g.query_event_id.unique():
                    key = (population_key, str(scenario), str(analysis), str(policy), qid)
                    if key not in cache:
                        query = indexed.loc[qid]
                        c = eligible_archive(
                            population,
                            query,
                            str(scenario),
                            str(policy),
                            analysis == "quality_sensitivity",
                        )
                        if not len(c):
                            raise ValueError("Scored query has no generic archive")
                        metrics = archive_metrics(
                            RESPONSE.loc[qid], RESPONSE.loc[c.event_id], c.storm_id
                        )
                        cache[key] = {
                            "query_event_id": qid,
                            "archive_candidate_events": len(c),
                            "archive_candidate_storms": int(c.storm_id.nunique()),
                            **{"archive_" + k: v for k, v in metrics.items()},
                        }
                    refs.append(cache[key])
                joined = g.merge(pd.DataFrame(refs), on="query_event_id", validate="many_to_one")
                if (
                    not joined.candidate_count.eq(joined.archive_candidate_events).all()
                    or not joined.candidate_storm_count.eq(joined.archive_candidate_storms).all()
                ):
                    raise ValueError("Generic reference differs from scored eligible archive")
                for metric in METRICS:
                    joined[metric + "_minus_archive"] = joined[metric] - joined["archive_" + metric]
                pieces.append(joined)
            result = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
            if result.empty:
                continue
            result.to_parquet(dest / (kind + ".parquet"), index=False)
            keys = KEYS + ["arm", "query_country"]
            summary.append(
                result.groupby(keys, observed=True)
                .agg(
                    queries=("query_event_id", "nunique"),
                    **{m + "_minus_archive": (m + "_minus_archive", "mean") for m in METRICS},
                )
                .reset_index()
                .assign(run=label)
            )
            intervals.append(
                interval_rows(
                    result, keys, {m: m + "_minus_archive" for m in METRICS}, evaluator.C.REVIEW
                ).assign(run=label)
            )
            support.append(
                {
                    "run": label,
                    "kind": kind,
                    "rows": len(result),
                    "unique_queries": result.query_event_id.nunique(),
                }
            )
            print("archive", label, kind, "queries", result.query_event_id.nunique(), flush=True)
            pd.DataFrame(support).to_json(OUT / "archive_progress.json", orient="records", indent=2)
    pd.concat(summary, ignore_index=True).to_parquet(OUT / "archive_summary.parquet", index=False)
    pd.concat(intervals, ignore_index=True).to_parquet(
        OUT / "archive_intervals.parquet", index=False
    )


def route_pass(sample, meta, raw, ttm, state, new_rain, obs, links, evaluator):
    results = []
    support = []
    # Isolated from the active rainfall replay: no concurrent cache writers.
    retrieval = RetrievalCache(ROOT / "data/processed/eo_followup_route_retrieval_cache", retrieve)
    main = ROOT / "results/eo_analogue_comparison_coherent_v1"
    for name, model in VARIANTS.items():
        for kind in ["monthly_snapshot", "monthly", "recent"]:
            a = vectors_for(main, kind, obs, links)[model]
            b = vectors_for(ROOT / "results/eo_expansion_comparisons" / name, kind, obs, links)[
                model
            ]
            common = set(sample.event_id) & set(a.index) & set(b.index)
            for cohort, ids, use_rain in [
                ("q_common", common, False),
                ("rain168_common", common & new_rain, True),
            ]:
                pop = sample[sample.event_id.isin(ids)].copy()
                if pop.empty:
                    support.append(
                        {
                            "variant": name,
                            "kind": kind,
                            "cohort": cohort,
                            "common_eligible_events": 0,
                            "scored_queries": 0,
                            "status": "no_common_support",
                        }
                    )
                    continue
                arms = {
                    "raw_state": {"temporal": raw, "state": state},
                    "ttm_state": {"temporal": ttm, "state": state},
                    "main_only": {"eo": a},
                    "supplement_only": {"eo": b},
                    "main_ttm_state": {"temporal": ttm, "state": state, "eo": a},
                    "supplement_ttm_state": {"temporal": ttm, "state": state, "eo": b},
                }
                if use_rain:
                    arms["conventional"] = None
                for scenario in ["all_rivers", "other_rivers"]:
                    for quality in [False, True]:
                        for policy in ["pooled", "domestic", "foreign"]:
                            local = []
                            query_set = None
                            for arm, blocks in arms.items():
                                pred, donors = retrieval(
                                    pop,
                                    blocks,
                                    exclude_same_river=scenario == "other_rivers",
                                    quality=quality,
                                    policy=policy,
                                )
                                found = set(pred.query_event_id) if not pred.empty else set()
                                if query_set is not None and found != query_set:
                                    raise ValueError("Common-route query mismatch")
                                query_set = found
                                if pred.empty:
                                    continue
                                evaluator.validate_donors(donors, meta, policy, scenario, quality)
                                for k in [5, 10]:
                                    scores, _ = assess_selected(
                                        pred, donors[donors["rank"] <= k], RESPONSE, meta, evaluator
                                    )
                                    tags = {
                                        "variant": name,
                                        "kind": kind,
                                        "cohort": cohort,
                                        "scenario": scenario,
                                        "analysis": "quality_sensitivity" if quality else "main",
                                        "policy": policy,
                                        "target_k": k,
                                        "arm": arm,
                                    }
                                    local.append(scores.assign(**tags))
                            if not local:
                                continue
                            frame = pd.concat(local, ignore_index=True)
                            results.append(frame)
                            support.append(
                                {
                                    "variant": name,
                                    "kind": kind,
                                    "cohort": cohort,
                                    "scenario": scenario,
                                    "quality": quality,
                                    "policy": policy,
                                    "common_eligible_events": len(pop),
                                    "scored_queries": len(query_set),
                                }
                            )
                print("route", name, kind, cohort, "common eligible", len(pop), flush=True)
    if results:
        frame = pd.concat(results, ignore_index=True)
        frame.to_parquet(OUT / "common_route_assessments.parquet", index=False)
        pairs = []
        keys = [
            "variant",
            "kind",
            "cohort",
            "scenario",
            "analysis",
            "policy",
            "target_k",
            "query_event_id",
        ]
        for ref, test in [
            ("main_only", "supplement_only"),
            ("main_ttm_state", "supplement_ttm_state"),
        ]:
            x = frame[frame.arm == test].merge(
                frame[frame.arm == ref][keys + ["actual_donor_count", *METRICS]],
                on=keys,
                suffixes=("", "_reference"),
                validate="one_to_one",
            )
            if not x.actual_donor_count.eq(x.actual_donor_count_reference).all():
                raise ValueError("Common-route donor counts differ")
            for m in METRICS:
                x[m + "_difference"] = x[m] - x[m + "_reference"]
            x["contrast"] = test + "_minus_" + ref
            pairs.append(x)
        pairs = pd.concat(pairs, ignore_index=True)
        pairs.to_parquet(OUT / "common_route_pairs.parquet", index=False)
        groups = [
            "variant",
            "kind",
            "cohort",
            "scenario",
            "analysis",
            "policy",
            "target_k",
            "query_country",
            "contrast",
        ]
        interval_rows(
            pairs, groups, {m: m + "_difference" for m in METRICS}, evaluator.C.REVIEW
        ).to_parquet(OUT / "common_route_intervals.parquet", index=False)
    pd.DataFrame(support).to_json(OUT / "common_route_support.json", orient="records", indent=2)


def execute(stage="all"):
    global RESPONSE
    OUT.mkdir(parents=True, exist_ok=True)
    sample, meta, raw, ttm, state, base, old_rain, new_rain, alpha = inputs()
    prep = ROOT / "results/eo_comparison_preparation"
    obs = pd.read_parquet(prep / "observations.parquet")
    links = pd.read_parquet(prep / "observation_windows.parquet")
    evaluator = load_script("84_complete_cross_border_analogues.py", "followup_evaluator")
    RESPONSE = pd.read_parquet(
        ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet"
    )
    prior = None
    if stage == "all" and (INDEPENDENT / "manifest.json").exists():
        reuse_independent(INDEPENDENT, OUT)
        prior = INDEPENDENT
    else:
        route_pass(sample, meta, raw, ttm, state, new_rain, obs, links, evaluator)
    specs = archive_specs(include_rain=stage == "all")
    if prior is not None:
        specs = [spec for spec in specs if spec[0] == "rain168"]
    archive_pass(
        sample,
        meta,
        old_rain,
        new_rain,
        alpha,
        obs,
        links,
        evaluator,
        specs=specs,
        prior=prior,
    )
    manifest = {
        "status": "completed",
        "stage": stage,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "all eligible events; unchanged targets; all donor policies, quality/scenario settings and k=5/10; group-balanced generic reference and common-route donor universes",
        "input_sha256": {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [
                ROOT / "results/eo_analogue_comparison_coherent_v1/manifest.json",
                *(
                    [ROOT / "results/eo_analogue_comparison_rain168_v1/manifest.json"]
                    if stage == "all"
                    else []
                ),
                *([INDEPENDENT / "manifest.json"] if prior is not None else []),
                *[
                    ROOT / "results/eo_expansion_comparisons" / n / "manifest.json"
                    for n in VARIANTS
                ],
                ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv",
                ROOT / "results/basin_ai_event_interpretation_ready/q_only_signatures.csv",
                ROOT
                / "results/basin_ai_event_interpretation_ready/q_only_standardized_histories.parquet",
                ROOT / "results/basin_ai_event_interpretation_ready/q_only_ttm_ordered.parquet",
                ROOT / "results/basin_ai_event_interpretation_ready/q_only_discharge_state.parquet",
                ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet",
                ROOT / "results/eo_comparison_preparation/observations.parquet",
                ROOT / "results/eo_comparison_preparation/observation_windows.parquet",
                ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet",
                ROOT / "results/basin_ai_cross_border_completion/rainfall_event_coverage.csv",
            ]
        },
        "source_sha256": {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [
                Path(__file__),
                ROOT / "src/eo_followup.py",
                ROOT / "src/eo_comparison.py",
                ROOT / "src/eo_retrieval_cache.py",
                ROOT / "src/eo_inputs.py",
                ROOT / "src/eo_integrity.py",
                *ROOT.glob("scripts/[678][0-9]_*.py"),
            ]
        },
        "outputs_sha256": {
            str(p.relative_to(OUT)): sha256(p)
            for p in sorted(OUT.rglob("*"))
            if p.is_file() and p.suffix in {".parquet", ".json"}
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["all", "independent"], default="all")
    args = parser.parse_args()
    destination = INDEPENDENT if args.stage == "independent" else OUT

    def status(state, **extra):
        if args.stage != "independent":
            return
        path = ROOT / "logs/eo-followup-2026-10-27/independent-stage.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".partial")
        temp.write_text(
            json.dumps(
                {
                    "status": state,
                    "pid": os.getpid(),
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                    "free_gib": round(shutil.disk_usage(ROOT).free / 2**30, 1),
                    "destination": str(destination),
                    **extra,
                },
                indent=2,
            )
            + "\n"
        )
        temp.replace(path)

    try:
        status("waiting_for_lock")
        with (ROOT / "results/.eo-followup-analysis.lock").open("a") as lock:
            # The already-running controller may reach this step before the parallel
            # worker finishes. Wait, then reuse its validated output instead of racing.
            print("Waiting for independent-stage lock, if occupied", flush=True)
            fcntl.flock(lock, fcntl.LOCK_EX)
            status("running")
            with fresh_output(destination) as stage:
                OUT = stage
                execute(args.stage)
        status("completed")
    except BaseException as exc:
        status("failed", error=str(exc))
        raise


if __name__ == "__main__":
    main()
