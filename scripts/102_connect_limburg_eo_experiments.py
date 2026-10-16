"""Connect census EO vectors to the existing retrospective analogue experiments.

Default builds coverage/experiment plans only. --run reuses the established
retrieval, quality/country/river policies, k=5/10 and 72h withheld-response scores.
No event sampling, tuning or forecast claim. Engineering fixture vectors are excluded.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import assess_selected, event_vectors, load_script, matched_pools, retrieve
from src.eo_inputs import ROUTES, sha256


def paired_intervals(frame, evaluator):
    """Reuse existing equal-count pairing and intact storm/year bootstrap."""
    keys = ["kind", "cohort", "scenario", "analysis", "policy", "target_k", "query_country"]
    output = []
    for config, group in frame.groupby(keys):
        reference = group[group.arm.eq("ttm_state")]
        for arm, challenger in group.groupby("arm"):
            if arm == "ttm_state":
                continue
            for metric in evaluator.METRICS:
                pair = evaluator.paired_differences(reference, challenger, metric, True)
                if pair.empty:
                    continue
                for unit in ["query_storm_id", "storm_year"]:
                    if pair[unit].nunique() < 2:
                        result = {
                            "difference": pair.difference.mean(),
                            "query_count": len(pair),
                            "cluster_count": pair[unit].nunique(),
                            "draws": 0,
                            "lower": np.nan,
                            "upper": np.nan,
                        }
                    else:
                        result = evaluator.C.REVIEW.cluster_interval(pair, unit)
                    output.append(
                        {
                            **dict(zip(keys, config, strict=True)),
                            "reference": "ttm_state",
                            "challenger": arm,
                            "metric": metric,
                            "resampling_unit": unit,
                            **result,
                        }
                    )
    return pd.DataFrame(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preparation", type=Path, default=ROOT / "results/eo_comparison_preparation"
    )
    parser.add_argument(
        "--representations", type=Path, default=ROOT / "results/eo_catchment_representations/census"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results/eo_analogue_comparison")
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--plumbing-fixture",
        action="store_true",
        help="Explicit engineering-only synthetic-vector test; never a scientific comparison",
    )
    args = parser.parse_args()
    args.preparation = args.preparation.resolve()
    args.representations = args.representations.resolve()
    args.out = args.out.resolve()
    if args.plumbing_fixture and args.out == ROOT / "results/eo_analogue_comparison":
        args.out = ROOT / "logs/eo_evaluation_plumbing"
    args.out.mkdir(parents=True, exist_ok=True)
    obs = pd.read_parquet(args.preparation / "observations.parquet")
    links = pd.read_parquet(args.preparation / "observation_windows.parquet")
    ready = ROOT / "results/basin_ai_event_interpretation_ready"
    meta = pd.read_csv(ready / "event_inventory.csv", parse_dates=["onset_utc"]).set_index(
        "event_id"
    )
    sample = pd.read_csv(ready / "q_only_signatures.csv", parse_dates=["onset_utc"])
    for field in ["country", "physical_river_group"]:
        sample[field] = sample.event_id.map(meta[field])
    rain = pd.read_csv(
        ROOT / "results/basin_ai_cross_border_completion/rainfall_event_coverage.csv"
    ).set_index("event_id")
    for col in rain.columns:
        if col not in ("country", "complete_scoring_sample"):
            sample[col] = sample.event_id.map(rain[col])
    base = load_script("65_hydrological_analogue_baseline.py", "eo_existing_baseline")
    raw = pd.read_parquet(ready / "q_only_standardized_histories.parquet")
    ttm = pd.read_parquet(ready / "q_only_ttm_ordered.parquet")
    state = pd.read_parquet(ready / "q_only_discharge_state.parquet")
    base_ids = sorted(
        set(sample.loc[sample.complete_scoring_sample, "event_id"])
        & set(raw.index)
        & set(ttm.index)
        & set(state.index)
    )
    rain_ids = set(
        sample.loc[
            sample.event_id.map(rain.complete_scoring_sample).fillna(False)
            & sample[base.FEATURE_COLUMNS].notna().all(axis=1),
            "event_id",
        ]
    )
    years = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
    context_gauge = meta.gauge.replace(
        {"2828300000200": "herzogenrath_1", "2828900000200": "randerath"}
    )
    key = pd.DataFrame(
        {
            "event_id": meta.index,
            "gauge": context_gauge,
            "embedding_year": meta.onset_utc.dt.year - 1,
        }
    )
    alpha = key.merge(
        years, on=["gauge", "embedding_year"], how="inner", validate="many_to_one"
    ).set_index("event_id")[[f"A{i:02d}" for i in range(64)]]
    alpha = alpha.div(np.linalg.norm(alpha, axis=1), axis=0).dropna()
    baseline_common = base_ids
    areas = (
        pd.read_parquet(args.preparation / "window_coverage.parquet")[
            ["catchment_gauge", "catchment_area_m2"]
        ]
        .drop_duplicates()
        .set_index("catchment_gauge")
        .catchment_area_m2
    )
    context_gauges = sample.gauge.replace(
        {"2828300000200": "herzogenrath_1", "2828900000200": "randerath"}
    )
    area_vectors = pd.DataFrame(
        {"log_area": np.log(context_gauges.map(areas).to_numpy())}, index=sample.event_id
    )
    identity_vectors = pd.get_dummies(sample.set_index("event_id").gauge, dtype=float)
    if args.run and args.representations.exists() and list(args.representations.glob("*.parquet")):
        provenance = json.loads((args.representations / "manifest.json").read_text())
        if provenance.get("engineering") and not args.plumbing_fixture:
            raise ValueError("Engineering vectors cannot enter a scientific comparison")
        for name, digest in provenance["outputs_sha256"].items():
            if sha256(args.representations / name) != digest:
                raise ValueError("Changed catchment representation: " + name)
    report = []
    scores = []
    donors = []
    coverage = []
    model_inputs = {}
    for kind in ["monthly_snapshot", "monthly", "recent"]:
        vectors = {}
        for model in ROUTES:
            path = args.representations / (model + ".parquet")
            if path.exists():
                model_inputs[str(path.relative_to(ROOT))] = sha256(path)
                vectors[model] = event_vectors(obs, links, pd.read_parquet(path), kind)
        available, common = matched_pools(baseline_common, vectors, list(ROUTES))
        for model in ROUTES:
            report.append(
                {
                    "kind": kind,
                    "model": model,
                    "baseline_eligible": len(baseline_common),
                    "model_available_events": len(available.get(model, [])),
                    "all_ten_matched_events": len(common),
                }
            )
        if not args.run:
            continue
        # Separate each model's matched-baseline population and the all-ten intersection.
        population_specs = []
        for m in ROUTES:
            ids = available.get(m, [])
            population_specs.extend(
                [
                    (f"q_only_available_{m}", ids, [m], False, False),
                    (f"rain_matched_available_{m}", sorted(set(ids) & rain_ids), [m], True, False),
                    (
                        f"alphaearth_matched_available_{m}",
                        sorted(set(ids) & set(alpha.index)),
                        [m],
                        False,
                        True,
                    ),
                ]
            )
        population_specs.extend(
            [
                ("q_only_all_ten_matched", common, list(ROUTES), False, False),
                ("rain_all_ten_matched", sorted(set(common) & rain_ids), list(ROUTES), True, False),
            ]
        )
        evaluator = load_script("84_complete_cross_border_analogues.py", "eo_existing_evaluation")
        response = pd.read_parquet(
            ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet"
        )
        for cohort, ids, models, use_rain, use_alpha in population_specs:
            if not ids:
                continue
            population = sample[sample.event_id.isin(ids)].copy()
            arms = {
                "raw_state": {"temporal": raw, "state": state},
                "ttm_state": {"temporal": ttm, "state": state},
            }
            arms["area_ttm_state"] = {"temporal": ttm, "state": state, "area": area_vectors}
            arms["identity_ttm_state"] = {
                "temporal": ttm,
                "state": state,
                "identity": identity_vectors,
            }
            if use_rain:
                arms["conventional"] = None
            if use_alpha:
                arms["alphaearth_ttm_state"] = {
                    "temporal": ttm,
                    "state": state,
                    "alphaearth": alpha,
                }
            for model in models:
                arms[f"{model}_only"] = {"eo": vectors[model]}
                arms[f"{model}_ttm_state"] = {"temporal": ttm, "state": state, "eo": vectors[model]}
            for scenario in ["all_rivers", "other_rivers"]:
                for quality in [False, True]:
                    for policy in ["pooled", "domestic", "foreign"]:
                        expected = None
                        for arm, blocks in arms.items():
                            predictions, selected = retrieve(
                                population,
                                blocks,
                                exclude_same_river=scenario == "other_rivers",
                                quality=quality,
                                policy=policy,
                            )
                            ids_found = (
                                set(predictions.query_event_id) if not predictions.empty else set()
                            )
                            if expected is not None and ids_found != expected:
                                raise ValueError("Comparison query population changed between arms")
                            expected = ids_found
                            tags = {
                                "kind": kind,
                                "cohort": cohort,
                                "scenario": scenario,
                                "analysis": "quality_sensitivity" if quality else "main",
                                "policy": policy,
                                "arm": arm,
                            }
                            coverage.append(
                                {
                                    **tags,
                                    "eligible_events": len(population),
                                    "queries_with_donors": len(ids_found),
                                }
                            )
                            if predictions.empty:
                                continue
                            evaluator.validate_donors(selected, meta, policy, scenario, quality)
                            for k in [5, 10]:
                                chosen = selected[selected["rank"].le(k)]
                                evaluated, details = assess_selected(
                                    predictions, chosen, response, meta, evaluator
                                )
                                scores.append(evaluated.assign(**tags, target_k=k))
                                donors.append(details.assign(**tags, target_k=k))
    pd.DataFrame(report).to_csv(args.out / "eo_event_coverage.csv", index=False)
    if scores:
        assessed = pd.concat(scores, ignore_index=True)
        assessed.to_parquet(args.out / "event_assessments.parquet", index=False)
        paired_intervals(assessed, evaluator).to_csv(args.out / "paired_intervals.csv", index=False)
    if donors:
        pd.concat(donors, ignore_index=True).to_parquet(
            args.out / "selected_donors.parquet", index=False
        )
    if coverage:
        pd.DataFrame(coverage).to_csv(args.out / "retrieval_coverage.csv", index=False)
    for path in [
        args.preparation / "observations.parquet",
        args.preparation / "observation_windows.parquet",
        args.preparation / "window_coverage.parquet",
        ready / "event_inventory.csv",
        ready / "q_only_signatures.csv",
        ready / "q_only_standardized_histories.parquet",
        ready / "q_only_ttm_ordered.parquet",
        ready / "q_only_discharge_state.parquet",
        ROOT / "results/basin_ai_cross_border_completion/rainfall_event_coverage.csv",
        ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet",
        ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet",
        ROOT / "scripts/65_hydrological_analogue_baseline.py",
        ROOT / "scripts/84_complete_cross_border_analogues.py",
        ROOT / "scripts/102_connect_limburg_eo_experiments.py",
        ROOT / "src/eo_comparison.py",
    ]:
        model_inputs[str(path.relative_to(ROOT))] = sha256(path)
    plan = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "executed": args.run,
        "purpose": "engineering_only_synthetic_vectors"
        if args.plumbing_fixture
        else "retrospective_comparison_preparation_or_execution",
        "scored_sets": len(scores),
        "event_population": "All 1062 inventoried high-water events retained; inherited quality/scoring eligibility before fitting; no sample.",
        "rainfall_episode_population": "3744 existing gauge-episode rows linked separately; these can feed script 93 without equating them to onset events.",
        "required_models_for_common_population": list(ROUTES),
        "baseline_q_only_eligible": len(baseline_common),
        "rain_matched_eligible": len(set(baseline_common) & rain_ids),
        "alphaearth_matched_eligible": len(set(baseline_common) & set(alpha.index)),
        "temporal_contexts": [
            "one completed month snapshot control",
            "12 completed months",
            "4 completed weeks",
        ],
        "k": [5, 10],
        "policies": ["pooled", "domestic", "foreign"],
        "scenarios": ["all_rivers", "other_rivers"],
        "quality": ["main", "quality_sensitivity"],
        "estimator": "Existing script 65 retrieval and script 84/C.assess withheld-response scoring, no new estimator or tuning.",
        "uncertainty": "Existing equal-donor-count paired comparisons and intact query-storm/year bootstrap; too few groups retain estimates without an interval.",
        "normalization": "Per-event EO L2 normalization; distance block scales from eligible prior donors only; existing full-era p99 remains retrospective.",
        "interpretation": "EO-only assesses representation retrieval; EO+TTM/state assesses incremental information. No as-issued forecast or warning skill claim.",
        "specificity_controls": ["area_ttm_state", "identity_ttm_state"],
        "coverage_caveat": "No arbitrary area cutoff. Report observed coverage and matched cohorts; do not rank incomplete-download populations as final findings.",
        "input_sha256": model_inputs,
    }
    (args.out / "experiment_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps({k: v for k, v in plan.items() if k != "input_sha256"}, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
