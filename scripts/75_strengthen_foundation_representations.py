#!/usr/bin/env python3
"""Exploratory pooling/state and catchment-identity/annual-context controls.

Uses fixed, observed histories and the existing prior-storm retrieval engine.
No training, weight search, outcome-based donor reranking or input imputation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "census", ROOT / "scripts/74_review_analogue_census.py"
)
CENSUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CENSUS)
REVIEW = CENSUS.REVIEW
CONTEXT = REVIEW.CONTEXT
TTM = CONTEXT.TTM
BASE = REVIEW.BASE
OUT = ROOT / "results/basin_ai_representation_checks"
CONTRASTS = {
    "dutch": [
        ("r2", "ttm_ordered"),
        ("r1", "raw_state"),
        ("r2", "ttm_mean_state"),
        ("ttm_ordered", "ttm_ordered_state"),
        ("raw_state", "ttm_mean_state"),
        ("raw_state", "ttm_ordered_state"),
        ("ttm_mean_state", "ttm_ordered_state"),
        ("r0", "ttm_ordered_state"),
    ],
    "pooled": [
        ("r2", "ttm_ordered"),
        ("r1", "raw_state"),
        ("r2", "ttm_mean_state"),
        ("ttm_ordered", "ttm_ordered_state"),
        ("raw_state", "ttm_mean_state"),
        ("raw_state", "ttm_ordered_state"),
        ("ttm_mean_state", "ttm_ordered_state"),
    ],
    "context": [
        ("r0", "r3_alphaearth"),
        ("r2_identity", "r3_alphaearth"),
        ("r3_static_2017", "r3_alphaearth"),
        ("r2_area", "r3_alphaearth"),
        ("r2", "r3_alphaearth"),
    ],
}


def discharge_state(index, windows, event_ids):
    history = (
        windows.loc[windows.relative_hour.between(-511, 0)]
        .pivot(index="event_id", columns="relative_hour", values="target_discharge_m3s")
        .reindex(index=event_ids, columns=np.arange(-511, 1))
    )
    if not np.isfinite(history.to_numpy()).all():
        raise ValueError("Discharge-state block needs the identical complete histories")
    p99 = index.set_index("event_id").loc[event_ids, "p99_m3s"]
    if not np.isfinite(p99).all() or p99.le(0).any():
        raise ValueError("Invalid state normalizer")
    return pd.DataFrame(
        {
            "onset_over_p99": history[0] / p99,
            "mean_over_p99": history.mean(axis=1) / p99,
            "std_over_p99": history.std(axis=1, ddof=0) / p99,
        }
    )


def ordered_embeddings(raw, out):
    path = out / "ordered_patch_embeddings.parquet"
    receipt_path = out / "ordered_patch_receipt.json"
    hashes = {
        str(p.relative_to(ROOT)): TTM.sha256(p)
        for p in [
            ROOT / "results/basin_ai_raw_hydrograph/standardized_histories.parquet",
            ROOT / "results/basin_ai_german_extension/german_standardized_histories.parquet",
            ROOT / "scripts/70_ttm_analogue_comparison.py",
            TTM.MODEL_DIR / "model.safetensors",
            TTM.MODEL_DIR / "config.json",
        ]
    }
    if path.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["input_sha256"] == hashes and receipt["output_sha256"] == TTM.sha256(path):
            vectors = pd.read_parquet(path)
            if not vectors.index.equals(raw.index) or vectors.shape[1] != 1536:
                raise ValueError("Cached ordered embedding identities/dimensions differ")
            return vectors
    vectors, info = TTM.extract_embeddings(raw, pooling="ordered")
    vectors.to_parquet(path)
    receipt = {"input_sha256": hashes, "output_sha256": TTM.sha256(path), "model_info": info}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return vectors


def build_arms(samples, representations, index, windows, out):
    raw = representations["pooled"]["r1"]["representation_vectors"]
    mean = representations["pooled"]["r2"]["representation_vectors"]
    ordered = ordered_embeddings(raw, out)
    state = discharge_state(index, windows, raw.index)
    state.to_parquet(out / "discharge_state_blocks.parquet")
    arms = {}
    for cohort in ["dutch", "pooled"]:
        existing = representations[cohort]
        arms[cohort] = {**existing, "ttm_ordered": {"representation_vectors": ordered}}
        for name, vectors in [
            ("raw_state", raw),
            ("ttm_mean_state", mean),
            ("ttm_ordered_state", ordered),
        ]:
            arms[cohort][name] = {
                "distance_blocks": {"temporal": vectors, "state": state},
                "robust_distance_blocks": ("state",),
            }
    joined = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/event_embeddings.parquet")
    common = joined.loc[joined.alphaearth_input_sample].copy()
    blocks = CONTEXT.context_blocks(common, mean)
    identity = pd.get_dummies(common.set_index("event_id").gauge, dtype=float)
    years = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
    bands = [f"A{i:02d}" for i in range(64)]
    fixed = years.loc[years.embedding_year.eq(2017)].set_index("gauge")[bands]
    static = fixed.loc[common.gauge].copy()
    static.index = common.event_id
    static = static.div(np.linalg.norm(static.to_numpy(), axis=1), axis=0)
    arms["context"] = {
        "r0": {},
        "r1": {"representation_vectors": raw},
        "r2": {"distance_blocks": {"ttm": blocks["ttm"]}},
        "r2_area": {"distance_blocks": {"ttm": blocks["ttm"], "area": blocks["area"]}},
        "r3_alphaearth": {
            "distance_blocks": {"ttm": blocks["ttm"], "alphaearth": blocks["alphaearth"]}
        },
        "r2_identity": {"distance_blocks": {"ttm": blocks["ttm"], "identity": identity}},
        "r3_static_2017": {"distance_blocks": {"ttm": blocks["ttm"], "alphaearth": static}},
    }
    metric_path = (
        ROOT / "results/basin_ai_alphaearth_projection/metric_catchment_year_embeddings.parquet"
    )
    if metric_path.exists():
        metric = pd.read_parquet(metric_path)
        updated = common.drop(columns=bands).merge(
            metric[["gauge", "embedding_year", *bands]],
            on=["gauge", "embedding_year"],
            validate="many_to_one",
        )
        if len(updated) != len(common) or updated[bands].isna().any().any():
            raise ValueError("Metric-grid context changes the common event sample")
        updated_blocks = CONTEXT.context_blocks(updated, mean)
        arms["context"]["r3_metric_grid"] = {
            "distance_blocks": {
                "ttm": updated_blocks["ttm"],
                "alphaearth": updated_blocks["alphaearth"],
            }
        }
    return arms


def evaluate(arms, samples, index, out):
    all_pairs, predictions, checks = [], [], []
    metadata = index.set_index("event_id")
    for cohort, configurations in arms.items():
        for quality in [False, True]:
            label = "quality_sensitivity" if quality else "main"
            query_ids = None
            for arm, settings in configurations.items():
                scores, donors = BASE.retrieve_prior_analogues(
                    samples[cohort],
                    top_k=5,
                    min_candidates=20,
                    exclude_measurement_concerns=quality,
                    **settings,
                )
                if query_ids is None:
                    query_ids = set(scores.query_event_id)
                elif set(scores.query_event_id) != query_ids:
                    raise ValueError("Every paired arm requires identical query events")
                # Replaying controls detects scientific changes from engine edits.
                if arm in ["r0", "r1", "r2", "r2_area", "r3_alphaearth"] and not (
                    cohort == "context" and arm in ["r0", "r1"]
                ):
                    directory = REVIEW.COHORTS[cohort][0]
                    original = REVIEW.read_predictions(directory, label, arm).set_index(
                        "query_event_id"
                    )
                    replay = scores.set_index("query_event_id").loc[original.index]
                    for column in [
                        "candidate_count",
                        "candidate_storm_count",
                        "analogue_absolute_error",
                        "median_absolute_error",
                    ]:
                        np.testing.assert_allclose(
                            replay[column], original[column], rtol=0, atol=1e-12
                        )
                    checks.append(
                        {
                            "cohort": cohort,
                            "analysis": label,
                            "arm": arm,
                            "status": "original predictions reproduced",
                        }
                    )
                scores = scores.assign(cohort=cohort, analysis=label, arm=arm)
                scores.to_csv(out / f"{cohort}_{label}_{arm}_predictions.csv", index=False)
                donors = donors.assign(cohort=cohort, analysis=label, arm=arm)
                for role, key in [("query", "query_event_id"), ("analogue", "analogue_event_id")]:
                    for field in [
                        "gauge",
                        "country",
                        "physical_river_group",
                        "measurement_concern",
                        "p99_m3s",
                    ]:
                        donors[f"{role}_{field}"] = donors[key].map(metadata[field])
                donors["same_gauge"] = donors.query_gauge.eq(donors.analogue_gauge)
                donors["same_river"] = donors.query_physical_river_group.eq(
                    donors.analogue_physical_river_group
                )
                donors["cross_country"] = donors.query_country.ne(donors.analogue_country)
                donors["measurement_concern_pair"] = (
                    donors.query_measurement_concern | donors.analogue_measurement_concern
                )
                predictions.append(scores)
                all_pairs.append(donors)
                print(f"{cohort}/{label}/{arm}: {len(scores)} paired queries", flush=True)
    pd.DataFrame(checks).to_csv(out / "original_control_replay.csv", index=False)
    return pd.concat(predictions, ignore_index=True), pd.concat(all_pairs, ignore_index=True)


def paired_intervals(sets):
    rows, differences = [], []
    contrasts = {key: list(value) for key, value in CONTRASTS.items()}
    if sets.arm.eq("r3_metric_grid").any():
        contrasts["context"].append(("r3_alphaearth", "r3_metric_grid"))
    metrics = CENSUS.METRICS + ["peak_absolute_error"]
    for cohort, comparisons in contrasts.items():
        for label in ["main", "quality_sensitivity"]:
            subset = sets.loc[sets.cohort.eq(cohort) & sets.analysis.eq(label)]
            for reference, challenger in comparisons:
                ref = subset.loc[subset.arm.eq(reference)].set_index("query_event_id")
                test = (
                    subset.loc[subset.arm.eq(challenger)].set_index("query_event_id").loc[ref.index]
                )
                if not ref.query_storm_id.eq(test.query_storm_id).all():
                    raise ValueError("Paired storm identities differ")
                delta = ref[
                    ["query_storm_id", "query_onset_utc", "query_watercourse", "query_country"]
                ].copy()
                delta = delta.assign(
                    cohort=cohort, analysis=label, reference=reference, challenger=challenger
                )
                first = delta.groupby("query_storm_id").query_onset_utc.transform("min")
                delta["storm_year"] = pd.to_datetime(first, utc=True).dt.year
                for metric in metrics:
                    column = (
                        "mean_donor_peak_absolute_error"
                        if metric == "peak_absolute_error"
                        else f"mean_{metric}"
                    )
                    delta["difference"] = test[column] - ref[column]
                    delta[f"difference_{metric}"] = delta.difference
                    for unit in ["query_storm_id", "storm_year"]:
                        rows.append(
                            {
                                "cohort": cohort,
                                "analysis": label,
                                "reference": reference,
                                "challenger": challenger,
                                "metric": metric,
                                "resampling_unit": unit,
                                **REVIEW.cluster_interval(delta, unit),
                            }
                        )
                differences.append(delta.drop(columns="difference").reset_index())
    return pd.DataFrame(rows), pd.concat(differences, ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    samples, representations, index, windows = REVIEW.load_inputs()
    arms = build_arms(samples, representations, index, windows, out)
    predictions, pairs = evaluate(arms, samples, index, out)
    response, history, coverage = CENSUS.load_curves(index, windows)
    assessed, pools, sets = CENSUS.review_all_sets(pairs, samples, response, history, coverage)
    predictions.to_csv(out / "all_predictions.csv", index=False)
    assessed.to_csv(out / "all_selected_pair_diagnostics.csv", index=False)
    pools.to_csv(out / "complete_prior_pool_reference.csv", index=False)
    sets.to_csv(out / "all_query_set_diagnostics.csv", index=False)
    CENSUS.summarize_sets(sets).to_csv(out / "cohort_summary.csv", index=False)
    intervals, differences = paired_intervals(sets)
    intervals.to_csv(out / "paired_metric_intervals.csv", index=False)
    differences.to_csv(out / "paired_query_diagnostics.csv", index=False)
    quantities = [f"mean_{metric}" for metric in CENSUS.METRICS] + [
        "mean_donor_peak_absolute_error",
        "same_gauge_share",
    ]
    grouped = sets.groupby(["cohort", "analysis", "arm", "query_watercourse"])
    grouped[quantities].mean().join(grouped.size().rename("query_sets")).reset_index().to_csv(
        out / "river_summary.csv", index=False
    )
    paths = [
        ROOT / "scripts" / name
        for name in [
            "65_hydrological_analogue_baseline.py",
            "70_ttm_analogue_comparison.py",
            "71_alphaearth_analogue_increment.py",
            "73_analogue_uncertainty_review.py",
            "74_review_analogue_census.py",
            Path(__file__).name,
        ]
    ]
    for directory in [
        "basin_ai_event_library",
        "basin_ai_german_extension",
        "basin_ai_raw_hydrograph",
        "basin_ai_ttm",
        "basin_ai_alphaearth",
        "basin_ai_alphaearth_projection",
    ]:
        for pattern in ["*.csv", "*.parquet"]:
            paths.extend(sorted((ROOT / "results" / directory).glob(pattern)))
    manifest = {
        "status": "exploratory extraction and context controls executed; no winner selected",
        "arm_names": {cohort: list(configs) for cohort, configs in arms.items()},
        "selected_slots": len(assessed),
        "query_sets": len(sets),
        "pooling": "mean versus ordered patch concatenation; identical frozen checkpoint; no training",
        "state": "onset/mean/std Q divided by own-era p99; prior-candidate median/IQR then equal-block scaling",
        "context": "same event frame/pools; identity and static-2017 controls; original mean-TTM backbone retained",
        "projection_status": "metric comparison included"
        if "r3_metric_grid" in arms["context"]
        else "metric download pending; original annual comparison preserved",
        "intervals": "all seven outcomes; unadjusted exploratory fixed-archive query-storm and year resampling",
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
    }
    (out / "summary.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "input_sha256"}, indent=2))


if __name__ == "__main__":
    main()
