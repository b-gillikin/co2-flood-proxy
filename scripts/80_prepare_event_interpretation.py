#!/usr/bin/env python3
"""Prepare the full Q-only census, frozen vectors and explicit reference measures.

Preserves original comparisons. Does not retrieve/rerank expanded analogues,
train models, write interpretation verdicts or produce dissertation prose.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cross", ROOT / "scripts/78_cross_river_analogue_checks.py"
)
CROSS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CROSS)
S, BASE = CROSS.S, CROSS.BASE
OUT = ROOT / "results/basin_ai_event_interpretation_ready"


def group_balanced_median(values, groups):
    """Equal mass per group and equal mass within group; midpoint at half-mass.

    With singleton groups, matches the ordinary even/odd sample median.
    No query outcomes or similarity ranks choose this reference.
    """
    values = np.asarray(values, dtype=float)
    groups = pd.Series(np.asarray(groups))
    if len(values) == 0:
        return np.nan
    if len(values) != len(groups) or not np.isfinite(values).all() or groups.isna().any():
        raise ValueError("Finite values and explicit group identities required")
    weights = 1 / groups.map(groups.value_counts()).to_numpy(dtype=float)
    order = np.argsort(values, kind="stable")
    values, weights = values[order], weights[order]
    cumulative = np.cumsum(weights)
    half = weights.sum() / 2
    tolerance = 1e-12 * weights.sum()
    i = int(np.flatnonzero(cumulative >= half - tolerance)[0])
    if np.isclose(cumulative[i], half, rtol=0, atol=1e-12 * weights.sum()) and i + 1 < len(values):
        return float((values[i] + values[i + 1]) / 2)
    return float(values[i])


def persistence_reference(onset_ratio, response):
    """Carry observed cutoff Q/p99 forward; flat curves have no unique peak time."""
    q = np.asarray(response, dtype=float)
    if q.shape != (72,) or not np.isfinite(q).all() or not np.isfinite(onset_ratio):
        raise ValueError("Require finite onset level and complete 72h response")
    return {
        "persistence_peak_estimate": float(onset_ratio),
        "persistence_peak_absolute_error": float(abs(onset_ratio - q.max())),
        "persistence_curve_level_rmse": float(np.sqrt(((q - onset_ratio) ** 2).mean())),
        "persistence_high_water_hours_estimate": 72 if onset_ratio >= 1 else 0,
        "persistence_high_water_duration_absolute_error": float(
            abs((72 if onset_ratio >= 1 else 0) - (q >= 1).sum())
        ),
        "persistence_peak_timing_defined": False,
    }


def prepare_vectors(signatures, index, windows, representations, out, input_hashes):
    ids = signatures.loc[signatures.common_representation_sample, "event_id"]
    raw, checks = S.TTM.RAW.standardized_histories(ids, windows)
    original = representations["pooled"]["r1"]["representation_vectors"]
    pd.testing.assert_frame_equal(raw.loc[original.index], original)
    extra_ids = raw.index.difference(original.index, sort=False)
    # Cache only the new extraction; receipts bind input histories and checkpoint.
    receipt_path = out / "extra_vector_receipt.json"
    fingerprints = {
        **input_hashes,
        str((S.TTM.MODEL_DIR / "model.safetensors").relative_to(ROOT)): S.TTM.sha256(
            S.TTM.MODEL_DIR / "model.safetensors"
        ),
        "scripts/70_ttm_analogue_comparison.py": S.TTM.sha256(
            ROOT / "scripts/70_ttm_analogue_comparison.py"
        ),
    }
    cached = False
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        cached = receipt["input_sha256"] == fingerprints and all(
            (out / name).exists() and S.TTM.sha256(out / name) == digest
            for name, digest in receipt["output_sha256"].items()
        )
    if not cached:
        model_info = {}
        paths = []
        for pooling in ["mean", "ordered"]:
            vectors, info = S.TTM.extract_embeddings(raw.loc[extra_ids], pooling=pooling)
            path = out / f"extra_ttm_{pooling}.parquet"
            vectors.to_parquet(path)
            paths.append(path)
            model_info[pooling] = info
        receipt = {
            "input_sha256": fingerprints,
            "new_history_events": len(extra_ids),
            "model_info": model_info,
            "output_sha256": {p.name: S.TTM.sha256(p) for p in paths},
        }
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    mean_original = representations["pooled"]["r2"]["representation_vectors"]
    ordered_original = pd.read_parquet(
        ROOT / "results/basin_ai_representation_checks/ordered_patch_embeddings.parquet"
    )
    for pooling, old in [("mean", mean_original), ("ordered", ordered_original)]:
        extra = pd.read_parquet(out / f"extra_ttm_{pooling}.parquet")
        if not extra.index.equals(extra_ids):
            raise ValueError("Extra extraction identity mismatch")
        all_vectors = pd.concat([old, extra]).loc[raw.index]
        pd.testing.assert_frame_equal(all_vectors.loc[old.index], old)
        if all_vectors.index.duplicated().any():
            raise ValueError("Duplicated embedding event")
        all_vectors.to_parquet(out / f"q_only_ttm_{pooling}.parquet")
    raw.to_parquet(out / "q_only_standardized_histories.parquet")
    checks.to_csv(out / "history_standardization.csv", index=False)
    state = S.discharge_state(index, windows, raw.index)
    old_state = pd.read_parquet(
        ROOT / "results/basin_ai_representation_checks/discharge_state_blocks.parquet"
    )
    pd.testing.assert_frame_equal(state.loc[old_state.index], old_state)
    state.to_parquet(out / "q_only_discharge_state.parquet")
    return len(raw), len(extra_ids)


def make_inventory(index, signatures, windows, original_samples):
    inventory = index.copy().set_index("event_id")
    sig = signatures.set_index("event_id")
    inventory["q_only_input_sample"] = sig.common_representation_sample
    inventory["q_only_scoring_sample"] = sig.complete_scoring_sample
    old_ids = set(
        original_samples["pooled"].loc[
            original_samples["pooled"].common_representation_sample, "event_id"
        ]
    )
    inventory["previous_temporal_input_sample"] = inventory.index.isin(old_ids)
    inventory["additional_q_only_input"] = (
        inventory.q_only_input_sample & ~inventory.previous_temporal_input_sample
    )
    q = windows.pivot(index="event_id", columns="relative_hour", values="target_discharge_m3s")
    normalized = q.div(inventory.p99_m3s, axis=0)
    for hour in [-24, -6, 0]:
        inventory[f"cutoff_q_over_p99_h{hour}"] = normalized[hour]
    for hours in [6, 24]:
        inventory[f"cutoff_q_change_{hours}h_over_p99"] = normalized[0] - normalized[-hours]
    history = normalized.loc[:, -511:0]
    inventory["cutoff_history_max_over_p99"] = history.max(axis=1).where(
        history.notna().all(axis=1)
    )
    for column in BASE.FEATURE_COLUMNS:
        inventory[f"cutoff_{column}"] = sig[column]
    inventory["reference_status"] = np.where(
        inventory.q_only_scoring_sample,
        "complete_exact_Q_response",
        np.where(
            inventory.q_only_input_sample,
            "input_ready_response_not_exact_scored",
            "history_incomplete_or_onset_uncertain",
        ),
    )
    scored = inventory.index[inventory.q_only_scoring_sample]
    response = normalized.loc[scored, 1:72]
    for eid, curve in response.iterrows():
        values = curve.to_numpy()
        reference = persistence_reference(normalized.loc[eid, 0], values)
        for name, value in reference.items():
            inventory.loc[eid, name] = value
        inventory.loc[eid, "response_peak_over_p99"] = values.max()
        inventory.loc[eid, "response_first_peak_hour"] = values.argmax() + 1
        inventory.loc[eid, "response_peak_at_first_hour"] = bool(values.argmax() == 0)
        inventory.loc[eid, "response_peak_at_last_hour"] = bool(values.argmax() == 71)
        inventory.loc[eid, "response_ends_above_p99"] = bool(values[-1] >= 1)
        inventory.loc[eid, "response_maximum_exceeds_onset"] = bool(
            values.max() > normalized.loc[eid, 0]
        )
        inventory.loc[eid, "response_high_water_hours_72h"] = int((values >= 1).sum())
    # Unscored descriptors stay missing; false would imply an observed negative.
    return inventory.reset_index()


def candidate_references(samples, inventory):
    rows = []
    meta = inventory.set_index("event_id")
    for cohort, sample in samples.items():
        for quality in [False, True]:
            analysis = "quality_sensitivity" if quality else "main"
            complete = sample.loc[sample.complete_scoring_sample].copy()
            if quality:
                complete = complete.loc[~complete.measurement_concern]
            complete["physical_river_group"] = complete.event_id.map(meta.physical_river_group)
            for scenario in ["all_rivers", "other_rivers"]:
                # Inventory all scorable queries, including zero/short donor archives.
                for event in sample.loc[sample.complete_scoring_sample].itertuples(index=False):
                    candidates = complete.loc[
                        (complete.onset_utc + pd.Timedelta(hours=72)).le(event.onset_utc)
                        & complete.storm_id.ne(event.storm_id)
                    ]
                    if scenario == "other_rivers":
                        candidates = candidates.loc[
                            candidates.physical_river_group.ne(
                                meta.loc[event.event_id, "physical_river_group"]
                            )
                        ]
                    count = len(candidates)
                    groups = candidates.storm_id.nunique()
                    balanced = group_balanced_median(
                        candidates.outcome_peak_over_p99_72h, candidates.storm_id
                    )
                    ordinary = (
                        float(candidates.outcome_peak_over_p99_72h.median()) if count else np.nan
                    )
                    excluded = quality and bool(event.measurement_concern)
                    peak = float(event.outcome_peak_over_p99_72h)
                    rows.append(
                        {
                            "cohort": cohort,
                            "scenario": scenario,
                            "analysis": analysis,
                            "query_event_id": event.event_id,
                            "query_storm_id": event.storm_id,
                            "query_onset_utc": event.onset_utc,
                            "query_country": meta.loc[event.event_id, "country"],
                            "query_river": meta.loc[event.event_id, "physical_river_group"],
                            "query_excluded_by_quality_sensitivity": excluded,
                            "candidate_events": count,
                            "candidate_groups": groups,
                            "available_distinct_donors_up_to_10": min(10, groups),
                            "archive_status": "none"
                            if groups == 0
                            else (
                                "short"
                                if count < 20 or groups < 10
                                else "matched_comparison_available"
                            ),
                            "matches_fixed_k_comparison": bool(
                                not excluded and count >= 20 and groups >= 10
                            ),
                            "event_weighted_median_peak": ordinary,
                            "group_balanced_median_peak": balanced,
                            "event_weighted_median_absolute_error": abs(ordinary - peak),
                            "group_balanced_median_absolute_error": abs(balanced - peak),
                            "persistence_peak_absolute_error": meta.loc[
                                event.event_id, "persistence_peak_absolute_error"
                            ],
                        }
                    )
    return pd.DataFrame(rows)


def match_existing_results(references, inventory):
    existing = pd.read_csv(
        ROOT / "results/basin_ai_cross_river_checks/query_diagnostics.csv",
        float_precision="round_trip",
    )
    keys = ["cohort", "scenario", "analysis", "query_event_id"]
    original = references.loc[references.cohort.isin(["dutch", "pooled", "context"])]
    merged = existing.merge(original, on=keys, validate="many_to_one", suffixes=("", "_reference"))
    if len(merged) != len(existing):
        raise ValueError("Existing result missing reference")
    for original_name, reference_name in [
        ("candidate_count", "candidate_events"),
        ("candidate_storm_count", "candidate_groups"),
        ("expanding_median_prediction", "event_weighted_median_peak"),
    ]:
        np.testing.assert_allclose(
            merged[original_name], merged[reference_name], rtol=0, atol=1e-12
        )
    merged["analogue_minus_persistence_peak_error"] = (
        merged.mean_donor_peak_absolute_error - merged.persistence_peak_absolute_error
    )
    merged["analogue_minus_group_balanced_median_peak_error"] = (
        merged.mean_donor_peak_absolute_error - merged.group_balanced_median_absolute_error
    )
    phase = inventory[
        [
            "event_id",
            "response_peak_at_first_hour",
            "response_peak_at_last_hour",
            "response_ends_above_p99",
            "response_maximum_exceeds_onset",
            "persistence_curve_level_rmse",
            "persistence_high_water_duration_absolute_error",
        ]
    ]
    matched = merged.merge(
        phase, left_on="query_event_id", right_on="event_id", validate="many_to_one"
    ).drop(columns="event_id")
    matched["analogue_minus_persistence_curve_error"] = (
        matched.ensemble_curve_level_rmse - matched.persistence_curve_level_rmse
    )
    return matched


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    original_manifest = json.loads(
        (ROOT / "results/basin_ai_cross_river_checks/manifest.json").read_text()
    )
    input_hashes = CROSS.verified_run_inputs(original_manifest)
    for name, sha in original_manifest["outputs_sha256"].items():
        if S.TTM.sha256(ROOT / "results/basin_ai_cross_river_checks" / name) != sha:
            raise ValueError("Changed existing results")
    samples, representations, index, windows = CROSS.REVIEW.load_inputs()
    broadened = index.copy()
    broadened["temporal_input_sample"] = (
        broadened.primary_usable & broadened.history_discharge_fraction.eq(1)
    )
    signatures = BASE.build_signatures(broadened, windows)
    vectors, extra = prepare_vectors(signatures, index, windows, representations, out, input_hashes)
    inventory = make_inventory(index, signatures, windows, samples)
    inventory.to_csv(out / "event_inventory.csv", index=False)
    signatures.to_csv(out / "q_only_signatures.csv", index=False)
    samples["q_only_pooled"] = signatures
    samples["q_only_dutch"] = signatures.loc[
        signatures.gauge.isin(index.loc[index.country.eq("NL"), "gauge"])
    ].copy()
    references = candidate_references(samples, inventory)
    references.to_csv(out / "archive_and_reference_inventory.csv", index=False)
    matched = match_existing_results(references, inventory)
    matched.to_csv(out / "existing_results_with_explicit_references.csv", index=False)
    measures = [
        "mean_donor_peak_absolute_error",
        "mean_peak_scaled_shape_rmse",
        "mean_peak_time_difference_h",
        "ensemble_curve_level_rmse",
        "persistence_curve_level_rmse",
        "analogue_minus_persistence_curve_error",
        "persistence_peak_absolute_error",
        "group_balanced_median_absolute_error",
        "analogue_minus_persistence_peak_error",
        "analogue_minus_group_balanced_median_peak_error",
    ]
    matched.groupby(["cohort", "scenario", "analysis", "arm", "k"])[
        measures
    ].mean().reset_index().to_csv(out / "reference_summary.csv", index=False)
    # Per-event review fields are intentionally blank and survive reruns.
    path = out / "event_interpretation_review.csv"
    review = inventory[
        [
            "event_id",
            "country",
            "physical_river_group",
            "onset_utc",
            "reference_status",
            "measurement_concern",
        ]
    ].copy()
    for field in [
        "history_only_assessment",
        "analogue_information_added",
        "observed_verification",
        "misleading_or_uncertain",
        "reviewer",
        "review_date",
    ]:
        review[field] = ""
    if path.exists():
        previous = pd.read_csv(path, keep_default_na=False).set_index("event_id")
        for field in review.columns[6:]:
            review[field] = review.event_id.map(previous[field]).fillna("")
    review.to_csv(path, index=False)
    manifest = {
        "status": "event-level interpretation prepared; expanded retrieval and human verdicts not run",
        "held_events": len(index),
        "q_only_input_events": vectors,
        "new_frozen_input_events": extra,
        "q_only_scoring_events": int(signatures.complete_scoring_sample.sum()),
        "new_scoring_events": int(
            (inventory.additional_q_only_input & inventory.q_only_scoring_sample).sum()
        ),
        "existing_scored_sets_reference_matched": len(matched),
        "all_availability_rows": len(references),
        "persistence": "constant cutoff Q/p99 for 72h; timing undefined; no fitting",
        "balanced_median": "equal mass per onset-linked group, equal events within group, midpoint half-mass rule",
        "archive_cutoffs": "tags for matched comparisons only; all scorable queries retained in inventory",
        "uncertainty": "empirical donor disagreement cue; no calibrated probabilities/refusal threshold",
        "source_sha256": {
            str(p.relative_to(ROOT)): S.TTM.sha256(p)
            for p in [
                Path(__file__),
                ROOT / "scripts/65_hydrological_analogue_baseline.py",
                ROOT / "scripts/78_cross_river_analogue_checks.py",
            ]
        },
        "input_sha256": input_hashes,
        "original_outputs_sha256": original_manifest["outputs_sha256"],
        "outputs_sha256": {
            p.name: S.TTM.sha256(p)
            for p in sorted(out.glob("*"))
            if p.suffix in [".csv", ".parquet"] and p.name != "event_interpretation_review.csv"
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if "sha256" not in k}, indent=2))


if __name__ == "__main__":
    main()
