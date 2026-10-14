#!/usr/bin/env python3
"""Independent consistency audit; no retrieval change or new empirical model."""

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
    "cross", ROOT / "scripts/78_cross_river_analogue_checks.py"
)
CROSS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CROSS)
OUT = ROOT / "results/basin_ai_consistency_audit"


def check_response_arrays(query, donors):
    """Recompute six distances directly, separately from the census scorer."""
    qp, dp = query.max(axis=1), donors.max(axis=1)
    return {
        "level_rmse_p99": np.sqrt(((donors - query) ** 2).mean(axis=1)),
        "peak_scaled_shape_rmse": np.sqrt(
            ((donors / dp[:, None] - query / qp[:, None]) ** 2).mean(axis=1)
        ),
        "peak_time_difference_h": np.abs(donors.argmax(axis=1) - query.argmax(axis=1)),
        "high_water_duration_difference_h": np.abs(
            (donors >= 1).sum(axis=1) - (query >= 1).sum(axis=1)
        ),
        "excess_area_difference_p99_h": np.abs(
            np.maximum(donors - 1, 0).sum(axis=1) - np.maximum(query - 1, 0).sum(axis=1)
        ),
        "terminal_peak_ratio_difference": np.abs(
            donors[:, -24:].mean(axis=1) / dp - query[:, -24:].mean(axis=1) / qp
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    run = ROOT / "results/basin_ai_cross_river_checks"
    manifest = json.loads((run / "manifest.json").read_text())
    inputs = CROSS.verified_run_inputs(manifest)
    for name, digest in manifest["outputs_sha256"].items():
        if hashlib.sha256((run / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Changed output {name}")
    sets = pd.read_csv(run / "query_diagnostics.csv", float_precision="round_trip")
    pairs = pd.read_csv(run / "selected_donors.csv", float_precision="round_trip")
    samples, representations, index, windows = CROSS.REVIEW.load_inputs()
    meta = index.set_index("event_id")
    if not sets.query_country.eq(sets.query_event_id.map(meta.country)).all():
        raise ValueError("Wrong query country")
    if not sets.query_measurement_concern.eq(
        sets.query_event_id.map(meta.measurement_concern)
    ).all():
        raise ValueError("Wrong query measurement flag")
    if not pairs.cross_country.eq(
        pairs.query_event_id.map(meta.country).ne(pairs.analogue_event_id.map(meta.country))
    ).all():
        raise ValueError("Wrong cross-country flag")
    if index.event_id.duplicated().any() or windows.duplicated(["event_id", "relative_hour"]).any():
        raise ValueError("Duplicate event or event-hour")
    actual = pd.to_datetime(windows.timestamp_utc, utc=True)
    expected = pd.to_datetime(windows.event_id.map(meta.onset_utc), utc=True) + pd.to_timedelta(
        windows.relative_hour, unit="h"
    )
    if not actual.eq(expected).all():
        raise ValueError("UTC/hour offsets do not match event onset")
    if (
        not windows.groupby("event_id")
        .relative_hour.agg(["min", "max", "size"])
        .eq(pd.Series({"min": -511, "max": 72, "size": 584}), axis="columns")
        .all()
        .all()
    ):
        raise ValueError("Wrong event-window contract")
    for cohort, frame in samples.items():
        frame["physical_river_group"] = frame.event_id.map(meta.physical_river_group)
        selected = pairs.loc[pairs.cohort.eq(cohort)]
        lookup = frame.set_index("event_id")
        for role, key in [("query", "query_event_id"), ("analogue", "analogue_event_id")]:
            for field, stored in [
                ("onset_utc", f"{role}_onset_utc"),
                ("storm_id", f"{role}_storm_id"),
            ]:
                left = selected[stored]
                right = selected[key].map(lookup[field])
                if field == "onset_utc":
                    left = pd.to_datetime(left, utc=True)
                    right = pd.to_datetime(right, utc=True)
                if not left.eq(right).all():
                    raise ValueError(f"Wrong {cohort} {role} {field}")
            if not selected[f"{role}_river"].eq(selected[key].map(meta.physical_river_group)).all():
                raise ValueError("Wrong physical river identity")
    q = windows.pivot(index="event_id", columns="relative_hour", values="target_discharge_m3s")
    response = q.loc[:, 1:72].div(meta.p99_m3s, axis=0)
    raw = representations["pooled"]["r1"]["representation_vectors"]
    history = q.loc[raw.index, -511:0].to_numpy()
    standard_deviation = history.std(axis=1, ddof=0)
    standardized = (history - history.mean(axis=1)[:, None]) / np.where(
        standard_deviation == 0, 1, standard_deviation
    )[:, None]
    np.testing.assert_allclose(standardized, raw.to_numpy(), rtol=0, atol=1e-12)
    for path, dimension in [
        (ROOT / "results/basin_ai_ttm/event_embeddings.parquet", 192),
        (ROOT / "results/basin_ai_german_extension/german_ttm_embeddings.parquet", 192),
        (ROOT / "results/basin_ai_representation_checks/ordered_patch_embeddings.parquet", 1536),
    ]:
        vectors = pd.read_parquet(path)
        if vectors.shape[1] != dimension or not np.isfinite(vectors.to_numpy()).all():
            raise ValueError("Invalid frozen representation dimensions/values")
        # Stored vectors are float32; use float64 for the 1,536-term norm sum.
        np.testing.assert_allclose(
            np.linalg.norm(vectors.to_numpy(dtype=float), axis=1), 1, rtol=0, atol=1e-6
        )
    context = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/event_embeddings.parquet")
    context = context.loc[context.alphaearth_input_sample]
    prior_year = pd.to_datetime(context.event_id.map(meta.onset_utc), utc=True).dt.year - 1
    if not context.embedding_year.eq(prior_year).all():
        raise ValueError("Context is not from the prior year")
    keys = ["cohort", "scenario", "analysis", "arm", "k"]
    metric_checks = []
    for key, group in pairs.groupby(keys, sort=True):
        group = group.sort_values(["query_event_id", "rank"])
        donors = response.loc[group.analogue_event_id].to_numpy()
        queries = response.loc[group.query_event_id].to_numpy()
        if not np.isfinite(donors).all() or not np.isfinite(queries).all():
            raise ValueError("Incomplete response used for scoring")
        recalculated = check_response_arrays(queries, donors)
        for col, values in recalculated.items():
            np.testing.assert_allclose(values, group[col], rtol=0, atol=1e-12)
        k = key[-1]
        query_ids = group.query_event_id.drop_duplicates().to_numpy()
        cube = donors.reshape(len(query_ids), k, 72)
        query = response.loc[query_ids].to_numpy()
        selected_sets = sets
        for name, value in zip(keys, key, strict=True):
            selected_sets = selected_sets.loc[selected_sets[name].eq(value)]
        selected_sets = selected_sets.set_index("query_event_id").loc[query_ids]
        peaks = cube.max(axis=2)
        derived = {
            "analogue_prediction": peaks.mean(axis=1),
            "mean_donor_peak_absolute_error": np.abs(peaks.mean(axis=1) - query.max(axis=1)),
            "ensemble_curve_level_rmse": np.sqrt(((cube.mean(axis=1) - query) ** 2).mean(axis=1)),
            "peak_spread": peaks.std(axis=1, ddof=0),
            "curve_spread": np.sqrt(cube.var(axis=1, ddof=0).mean(axis=1)),
            "shape_spread": np.sqrt((cube / peaks[:, :, None]).var(axis=1, ddof=0).mean(axis=1)),
        }
        for col, values in derived.items():
            np.testing.assert_allclose(values, selected_sets[col], rtol=0, atol=1e-12)
        for col, values in recalculated.items():
            np.testing.assert_allclose(
                values.reshape(len(query_ids), k).mean(axis=1),
                selected_sets[f"mean_{col}"],
                rtol=0,
                atol=1e-12,
            )
        metric_checks.append(
            dict(zip(keys, key, strict=True))
            | {
                "queries": len(query_ids),
                "slots": len(group),
                "status": "all response metrics agree within 1e-12",
            }
        )
    pd.DataFrame(metric_checks).to_csv(out / "metric_checks.csv", index=False)
    # Reconstruct candidate eligibility independently for every actual query/pool.
    pools = []
    selected_members = (
        pairs.groupby(["cohort", "scenario", "analysis", "query_event_id"])
        .analogue_event_id.agg(set)
        .to_dict()
    )
    for (cohort, scenario, analysis), group in sets.groupby(["cohort", "scenario", "analysis"]):
        sample = samples[cohort]
        complete = sample.loc[sample.complete_scoring_sample].copy()
        if analysis == "quality_sensitivity":
            complete = complete.loc[~complete.measurement_concern]
        lookup = complete.set_index("event_id")
        for query_id, rows in group.groupby("query_event_id"):
            event = lookup.loc[query_id]
            candidates = complete.loc[
                (complete.onset_utc + pd.Timedelta(hours=72)).le(event.onset_utc)
                & complete.storm_id.ne(event.storm_id)
            ]
            if scenario == "other_rivers":
                candidates = candidates.loc[
                    candidates.physical_river_group.ne(event.physical_river_group)
                ]
            n = len(candidates)
            if not selected_members[cohort, scenario, analysis, query_id].issubset(
                set(candidates.event_id)
            ):
                raise ValueError("Selected donor lies outside its actual candidate pool")
            storms = candidates.storm_id.nunique()
            if (
                not rows.candidate_count.eq(n).all()
                or not rows.candidate_storm_count.eq(storms).all()
            ):
                raise ValueError("Candidate pool mismatch")
            np.testing.assert_allclose(
                rows.expanding_median_prediction,
                candidates.outcome_peak_over_p99_72h.median(),
                rtol=0,
                atol=1e-12,
            )
            if n < 20 or storms < 10:
                raise ValueError("Reported query violates its comparison eligibility")
            pools.append(
                {
                    "cohort": cohort,
                    "scenario": scenario,
                    "analysis": analysis,
                    "query_event_id": query_id,
                    "candidate_events": n,
                    "candidate_storms": storms,
                    "events_per_storm": n / storms,
                }
            )
    pd.DataFrame(pools).to_csv(out / "candidate_pool_checks.csv", index=False)
    nl = pd.read_csv(ROOT / "results/basin_ai_event_library/event_index.csv")
    q_only = nl.primary_usable & nl.history_discharge_fraction.eq(1)
    shared = nl.history_rainfall_fraction.eq(1) & nl.history_weather_fraction.eq(1)
    extra = nl.loc[q_only & ~shared].copy()
    extra["complete_72h_response"] = extra.outcome_discharge_fraction.eq(1)
    extra.to_csv(out / "q_only_outside_shared_cohort.csv", index=False)
    coverage = []
    # Count unique events per configuration; never count repeated arms/k as evidence.
    for (cohort, scenario, analysis), group in sets.groupby(["cohort", "scenario", "analysis"]):
        unique = group.drop_duplicates("query_event_id")
        curves = response.loc[unique.query_event_id].to_numpy()
        peak_hour = curves.argmax(axis=1) + 1
        coverage.append(
            {
                "cohort": cohort,
                "scenario": scenario,
                "analysis": analysis,
                "queries": len(unique),
                "peak_at_hour_1": int((peak_hour == 1).sum()),
                "peak_at_hour_72": int((peak_hour == 72).sum()),
                "still_above_p99_at_hour_72": int((curves[:, -1] >= 1).sum()),
                "countries": unique.query_country.nunique(),
                "physical_rivers": unique.query_river.nunique(),
            }
        )
    pd.DataFrame(coverage).to_csv(out / "response_segment_coverage.csv", index=False)
    storm_rows = []
    for cohort, sample in samples.items():
        stats = sample.groupby("storm_id").onset_utc.agg(["min", "max", "size"])
        stats["span_h"] = (stats["max"] - stats["min"]).dt.total_seconds() / 3600
        storm_rows.append(
            {
                "cohort": cohort,
                "groups": len(stats),
                "max_group_span_h": stats.span_h.max(),
                "groups_spanning_calendar_years": int(
                    stats["min"].dt.year.ne(stats["max"].dt.year).sum()
                ),
            }
        )
    pd.DataFrame(storm_rows).to_csv(out / "storm_group_coverage.csv", index=False)
    result = {
        "status": "independent consistency audit passed",
        "verified_input_files": len(inputs),
        "verified_output_csvs": len(manifest["outputs_sha256"]),
        "metric_configurations": len(metric_checks),
        "independently_checked_selected_slots": len(pairs),
        "independently_checked_query_sets": len(sets),
        "independently_reconstructed_pools": len(pools),
        "utc_event_hours_checked": len(windows),
        "raw_histories_recomputed": len(raw),
        "prior_year_context_events_checked": len(context),
        "scorable_events_before_archive_cutoffs": {
            cohort: int(sample.complete_scoring_sample.sum()) for cohort, sample in samples.items()
        },
        "weather_only_excluded_histories": int(
            (q_only & nl.history_rainfall_fraction.eq(1) & ~nl.history_weather_fraction.eq(1)).sum()
        ),
        "q_only_histories_outside_shared_sample": len(extra),
        "q_only_complete_responses_outside_shared_sample": int(extra.complete_72h_response.sum()),
        "limitations": [
            "retrospective rating-era p99 and revised provider records",
            "72-hour response segments, not necessarily full flood events",
            "storm labels are 72-hour onset-linkage groups, not independently verified meteorological storms",
            "historical median weights events while selected donors are one per storm",
            "no own-history-only outcome benchmark yet",
            "fixed-archive exploratory intervals do not include reused-donor uncertainty",
        ],
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (out / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
