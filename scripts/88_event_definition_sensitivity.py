#!/usr/bin/env python3
"""One-factor percentile/linkage sensitivities of the held analogue analysis.

All available cases; frozen p99 scale, histories, models and response endpoints.
No training, donor-policy search, input repair or overwrite of earlier runs.
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


def module(number, name):
    path = next((ROOT / "scripts").glob(f"{number}_*.py"))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


X = module("84", "cross_border_sensitivity")
R = module("46", "event_review_sensitivity")
G = module("72", "german_sensitivity")
INFO = module("82", "archive_sensitivity")
E, C, B, S = X.E, X.C, X.B, X.E.S
OUT = ROOT / "results/basin_ai_event_definition_sensitivity"
CONFIGS = {"p99_72": (0.99, 72), "p95_72": (0.95, 72), "p99_120": (0.99, 120)}
KEYS = ["cohort", "scenario", "analysis", "policy", "arm", "target_k", "query_country"]
METRICS = X.METRICS


def episode_definition(q, eras, table, quantile, merge_hours, literal=None):
    """Change selection only: p99 remains the common state/response normalizer."""
    _, scale = R.era_thresholds(q, eras, quantile=0.99)
    per_era, threshold = R.era_thresholds(q, eras, quantile=quantile)
    admissible = R.rating_domain_admissible(q, eras, table, threshold)
    episodes = R.episode_table(
        q, threshold, merge_hours, admissible, eras if literal is None else literal
    )
    return episodes, threshold, scale, admissible, per_era


def held_observations():
    paths = [
        ROOT / "data/interim/event_study_discharge_hourly.csv",
        ROOT / "data/interim/radolan_catchment_hourly.csv",
        ROOT / "data/interim/event_study_gauges.csv",
        ROOT / "data/interim/event_study_rating_eras.csv",
        ROOT / "data/processed/waterschap_station_source_qa.csv",
        G.PERIODS,
        X.OUT / "german_catchment_hourly_rainfall.csv",
    ]
    q = R.read_hourly(paths[0])
    rain = R.read_hourly(paths[1])
    gauges = pd.read_csv(paths[2])
    eras = pd.read_csv(paths[3])
    qa = pd.read_csv(paths[4]).set_index("series_key")
    observations = []
    for gauge in gauges.itertuples():
        table = eras[eras.gauge.eq(gauge.gauge)]
        labels = R.assign_eras(q.index, table)
        observations.append(
            dict(
                gauge=gauge.gauge,
                watercourse=gauge.watercourse,
                country="NL",
                q=q[gauge.gauge],
                rain=rain[gauge.watercourse],
                eras=labels,
                literal=labels,
                table=table,
                source_note=qa.loc[gauge.gauge, "july_2021_discharge_status"],
            )
        )
    german_rain = R.read_hourly(paths[-1])
    periods = G.read_periods()
    for station, (gauge, name) in G.STATIONS.items():
        (qpath,) = (G.SOURCE / station).glob(
            "*abfluss_mit_m_s_csv_export_mittelwerte_15minuten*.csv"
        )
        (spath,) = (G.SOURCE / station).glob(
            "*wasserstand_mit_cm_csv_export_mittelwerte_15minuten*.csv"
        )
        qs = G.complete_hourly(G.read_quarters(qpath, gauge, name, "Abfluss"))
        stage = G.complete_hourly(G.read_quarters(spath, gauge, name, "Wasserstand"))
        table = periods[periods.station.eq(station)]
        labels = R.assign_eras(qs.index, table)
        literal = R.assign_eras(qs.index, table.assign(era_id=table.period_id))
        observations.append(
            dict(
                gauge=gauge,
                watercourse="Wurm",
                country="DE",
                q=qs,
                stage=stage,
                rain=german_rain[X.GAUGES[gauge]],
                eras=labels,
                literal=literal,
                table=table,
                station_name=name,
            )
        )
        paths += [qpath, spath, ROOT / table.source_pdf.iloc[0]]
    hashes = {str(p.relative_to(ROOT)): S.TTM.sha256(p) for p in paths}
    return observations, hashes


def build_library(observations, quantile, merge_hours):
    metadata, windows, census, thresholds = [], [], [], []
    offsets = np.arange(-511, 73)
    for source in observations:
        q, eras, table = source["q"], source["eras"], source["table"]
        gauge, country = source["gauge"], source["country"]
        episodes, threshold, normalizer, admissible, per_era = episode_definition(
            q, eras, table, quantile, merge_hours, source["literal"]
        )
        p99, _ = R.era_thresholds(q, eras)
        for era, value in per_era.items():
            thresholds.append(
                dict(
                    gauge=gauge,
                    country=country,
                    era_id=era,
                    event_threshold_m3s=value,
                    p99_normalizer_m3s=p99[era],
                    observed_hours=int(q[eras.eq(era)].notna().sum()),
                )
            )
        for episode in episodes.itertuples(index=False):
            onset = pd.Timestamp(episode.onset_utc)
            eid = f"{gauge}|{onset.isoformat()}"
            census.append(
                dict(
                    event_id=eid,
                    gauge=gauge,
                    country=country,
                    **episode._asdict(),
                    event_threshold_m3s=threshold.loc[onset],
                    p99_m3s=normalizer.loc[onset],
                )
            )
            # The held NL event library contains exact onsets only. Preserve
            # unobserved entries above the threshold in the separate census.
            if country == "NL" and episode.onset_censored:
                continue
            times = onset + pd.to_timedelta(offsets, unit="h")
            values = q.reindex(times).to_numpy()
            rain = source["rain"].reindex(times)
            exact = not episode.onset_censored
            if country == "NL":
                review = R.inspect_episode(
                    q, eras, admissible, normalizer, table, episode, source["source_note"]
                )
                prior_rain = source["rain"].reindex(
                    pd.date_range(onset - pd.Timedelta(hours=72), periods=72, freq="h")
                )
                primary = bool(exact and prior_rain.notna().all())
                flags = dict(
                    measurement_concern=review["measurement_concern"],
                    outcome_score_admissible=True,
                    provider_status=source["source_note"],
                    review_flags=review["review_flags"],
                )
            else:
                flags = G.quality_for_window(
                    q, source["stage"], eras, source["literal"], table, onset
                )
                flags["provider_status"] = (
                    "provisional_high_flow"
                    if flags["provisional_high_flow"]
                    else "pre_flood_rating_documented"
                )
                primary = exact
            history_complete = np.isfinite(values[:512]).all()
            metadata.append(
                dict(
                    event_id=eid,
                    gauge=gauge,
                    watercourse=source["watercourse"],
                    country=country,
                    physical_river_group="Wurm/Worm"
                    if source["watercourse"] in ["Worm", "Wurm"]
                    else source["watercourse"],
                    onset_utc=onset,
                    p99_m3s=normalizer.loc[onset],
                    event_threshold_m3s=threshold.loc[onset],
                    primary_usable=primary,
                    onset_censored=episode.onset_censored,
                    n_crossings=episode.n_crossings,
                    chain_span_hours=episode.chain_span_hours,
                    last_crossing_utc=episode.last_crossing_utc,
                    temporal_input_sample=bool(primary and history_complete),
                    history_discharge_fraction=np.isfinite(values[:512]).mean(),
                    history_rainfall_fraction=rain.iloc[:512].notna().mean(),
                    outcome_discharge_fraction=np.isfinite(values[512:]).mean(),
                    **flags,
                )
            )
            windows.append(
                pd.DataFrame(
                    dict(
                        event_id=eid,
                        relative_hour=offsets,
                        timestamp_utc=times,
                        target_discharge_m3s=values,
                        catchment_rainfall_mm=rain.to_numpy(),
                    )
                )
            )
    index = R.cluster_regional_storms(pd.DataFrame(metadata), max_gap_hours=72)
    return (
        index,
        pd.concat(windows, ignore_index=True),
        pd.DataFrame(census),
        pd.DataFrame(thresholds),
    )


def prepare(index, windows, out):
    sample = B.build_signatures(index, windows)
    meta = index.set_index("event_id")
    for field in ["country", "physical_river_group", "history_rainfall_fraction"]:
        sample[field] = sample.event_id.map(meta[field])
    meta["cutoff_q_over_p99_h0"] = sample.set_index("event_id").q_over_p99_onset
    meta["q_only_input_sample"] = sample.set_index("event_id").common_representation_sample
    meta["q_only_scoring_sample"] = sample.set_index("event_id").complete_scoring_sample
    ids = sample.loc[sample.common_representation_sample, "event_id"]
    raw, checks = S.TTM.RAW.standardized_histories(ids, windows)
    state = S.discharge_state(index, windows, ids)
    old = pd.read_parquet(E.READY / "q_only_standardized_histories.parquet")
    shared = raw.index.intersection(old.index)
    pd.testing.assert_frame_equal(raw.loc[shared], old.loc[shared])
    added = raw.index.difference(old.index, sort=False)
    # Cache by actual numeric history and checkpoint, not event name alone.
    raw_path = out / "new_histories.parquet"
    fresh = raw.loc[added]
    if raw_path.exists():
        same = pd.read_parquet(raw_path).equals(fresh)
    else:
        same = False
    fresh.to_parquet(raw_path)
    fingerprint = {
        p.name: S.TTM.sha256(p)
        for p in [
            raw_path,
            S.TTM.MODEL_DIR / "model.safetensors",
            S.TTM.MODEL_DIR / "config.json",
            ROOT / "scripts/70_ttm_analogue_comparison.py",
        ]
    }
    receipt_path = out / "new_TTM_receipt.json"
    cached = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    if not (
        same
        and cached.get("input_sha256") == fingerprint
        and (out / "new_ordered_TTM.parquet").exists()
        and cached.get("output_sha256") == S.TTM.sha256(out / "new_ordered_TTM.parquet")
    ):
        if len(fresh):
            extra, receipt = S.TTM.extract_embeddings(fresh, pooling="ordered")
        else:
            extra, receipt = (
                pd.DataFrame(index=fresh.index),
                {"new_events": 0, "model_not_called": True},
            )
        extra.to_parquet(out / "new_ordered_TTM.parquet")
        cached = dict(
            input_sha256=fingerprint,
            model_info=receipt,
            output_sha256=S.TTM.sha256(out / "new_ordered_TTM.parquet"),
        )
        receipt_path.write_text(json.dumps(cached, indent=2) + "\n")
    old_ordered = pd.read_parquet(E.READY / "q_only_ttm_ordered.parquet")
    ordered = pd.concat(
        [old_ordered.loc[shared], pd.read_parquet(out / "new_ordered_TTM.parquet")]
    ).loc[ids]
    normalized = windows.pivot(
        index="event_id", columns="relative_hour", values="target_discharge_m3s"
    ).div(meta.p99_m3s, axis=0)
    response = normalized.loc[:, 1:72]
    sample.to_csv(out / "signatures.csv", index=False)
    meta.reset_index().to_csv(out / "event_inventory.csv", index=False)
    checks.to_csv(out / "history_checks.csv", index=False)
    raw.to_parquet(out / "raw_histories.parquet")
    ordered.to_parquet(out / "ordered_TTM.parquet")
    state.to_parquet(out / "discharge_state.parquet")
    response.to_parquet(out / "response_p99.parquet")
    return sample, meta, raw, state, ordered, response


def validate_baseline(index, sample, raw, state):
    old = pd.read_csv(E.READY / "event_inventory.csv").set_index("event_id")
    current = index.set_index("event_id")
    pd.testing.assert_index_equal(current.index.sort_values(), old.index.sort_values())
    old = old.loc[current.index]
    for field in ["p99_m3s", "history_discharge_fraction", "outcome_discharge_fraction"]:
        np.testing.assert_allclose(current[field], old[field], atol=1e-12, rtol=0)
    for field in [
        "primary_usable",
        "measurement_concern",
        "outcome_score_admissible",
        "storm_id",
    ]:
        assert current[field].equals(old[field]), field
    assert current.temporal_input_sample.equals(old.q_only_input_sample)
    old_sample = pd.read_csv(E.READY / "q_only_signatures.csv").set_index("event_id")
    new_sample = sample.set_index("event_id").loc[old_sample.index]
    for field in ["common_representation_sample", "complete_scoring_sample"]:
        assert new_sample[field].equals(old_sample[field]), field
    held_rain = (
        pd.read_csv(X.OUT / "rainfall_event_coverage.csv")
        .set_index("event_id")
        .loc[new_sample.index]
    )
    for field in [*B.FEATURE_COLUMNS, "outcome_peak_over_p99_72h"]:
        reference = held_rain[field] if field.startswith("rain_") else old_sample[field]
        np.testing.assert_allclose(new_sample[field], reference, equal_nan=True, atol=1e-12, rtol=0)
    np.testing.assert_allclose(
        new_sample.history_rainfall_fraction, held_rain.rain_history_fraction, atol=1e-12, rtol=0
    )
    assert (new_sample.complete_scoring_sample & new_sample.history_rainfall_fraction.eq(1)).equals(
        held_rain.complete_scoring_sample
    )
    pd.testing.assert_frame_equal(
        raw, pd.read_parquet(E.READY / "q_only_standardized_histories.parquet").loc[raw.index]
    )
    pd.testing.assert_frame_equal(
        state, pd.read_parquet(E.READY / "q_only_discharge_state.parquet").loc[state.index]
    )


def cohort_inputs(sample, raw, state, ordered, years):
    temporal = {
        "r1": {"representation_vectors": raw},
        "raw_state": {
            "distance_blocks": {"temporal": raw, "state": state},
            "robust_distance_blocks": ("state",),
        },
        "ttm_ordered_state": {
            "distance_blocks": {"temporal": ordered, "state": state},
            "robust_distance_blocks": ("state",),
        },
    }
    rain = sample.copy()
    rain["complete_scoring_sample"] &= rain.history_rainfall_fraction.eq(1)
    context = X.join_context(sample, years)
    context = context[context.context_available & context.common_representation_sample].copy()
    return {
        "q_only": (sample, temporal),
        "rain_matched": (rain, {"r0": {}, **temporal}),
        "context": (context, X.context_settings(context, ordered, state, years)),
    }


def add_archive_references(rows, cohorts, response):
    references = []
    for config, group in rows.groupby(["cohort", "scenario", "analysis"]):
        cohort, scenario, analysis = config
        sample = cohorts[cohort][0]
        eligible = sample[
            sample.complete_scoring_sample
            & (~sample.measurement_concern if analysis == "quality_sensitivity" else True)
        ]
        for eid in group.query_event_id.unique():
            query = eligible[eligible.event_id.eq(eid)].iloc[0]
            candidates = eligible[
                (eligible.onset_utc + pd.Timedelta(hours=72)).le(query.onset_utc)
                & eligible.storm_id.ne(query.storm_id)
            ]
            if scenario == "other_rivers":
                candidates = candidates[
                    candidates.physical_river_group.ne(query.physical_river_group)
                ]
            expected_count = group.loc[group.query_event_id.eq(eid), "candidate_count"].unique()
            assert len(expected_count) == 1 and expected_count[0] == len(candidates)
            evidence, _ = INFO.archive_evidence(
                response.loc[eid], response.loc[candidates.event_id], candidates.storm_id
            )
            references.append(
                dict(
                    cohort=cohort,
                    scenario=scenario,
                    analysis=analysis,
                    query_event_id=eid,
                    **evidence,
                )
            )
    return rows.merge(
        pd.DataFrame(references),
        on=["cohort", "scenario", "analysis", "query_event_id"],
        validate="many_to_one",
    )


def summarise(rows):
    fields = [*METRICS, *INFO.METRICS.values()]
    # Reference columns have repeated names across metric aliases only once.
    fields = list(dict.fromkeys(fields))
    return (
        rows.groupby(KEYS)
        .agg(
            events=("query_event_id", "size"),
            groups=("query_storm_id", "nunique"),
            actual_donors=("actual_donor_count", "mean"),
            **{m: (m, "mean") for m in fields},
        )
        .reset_index()
    )


def paired_intervals(rows):
    records = []
    for config, group in rows.groupby(
        ["cohort", "scenario", "analysis", "target_k", "query_country"]
    ):
        arms = {arm: g.set_index("query_event_id") for arm, g in group.groupby("arm")}
        contrasts = (
            [("raw_state", "ttm_ordered_state")]
            if config[0] != "context"
            else [(a, "alphaearth") for a in ["temporal", "area", "identity", "static_2017"]]
        )
        if config[0] == "rain_matched":
            contrasts += [("r0", "ttm_ordered_state"), ("r0", "raw_state")]
        contrasts += [("archive", a) for a in arms]
        for reference, challenger in contrasts:
            a = arms[challenger]
            b = arms[reference].loc[a.index] if reference != "archive" else a
            assert a.index.equals(b.index)
            assert a.actual_donor_count.eq(b.actual_donor_count).all()
            for metric in METRICS:
                if reference == "archive" and metric not in INFO.METRICS:
                    continue
                difference = a[metric] - (
                    a[INFO.METRICS[metric]] if reference == "archive" else b[metric]
                )
                frame = a[["query_storm_id", "query_onset_utc"]].copy()
                frame["difference"] = difference
                frame["storm_year"] = pd.to_datetime(
                    frame.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
                ).dt.year
                for unit in ["query_storm_id", "storm_year"]:
                    info = dict(
                        cohort=config[0],
                        scenario=config[1],
                        analysis=config[2],
                        target_k=config[3],
                        query_country=config[4],
                        reference=reference,
                        challenger=challenger,
                        metric=metric,
                        resampling_unit=unit,
                    )
                    if frame[unit].nunique() < 2:
                        info.update(
                            difference=difference.mean(),
                            lower=np.nan,
                            upper=np.nan,
                            query_count=len(frame),
                            cluster_count=frame[unit].nunique(),
                            draws=0,
                            finite_draws=0,
                            status="undefined_too_few_clusters",
                        )
                    else:
                        info.update(**C.REVIEW.cluster_interval(frame, unit), status="estimated")
                    records.append(info)
    return pd.DataFrame(records)


def fingerprints(paths):
    return {str(p.relative_to(ROOT)): S.TTM.sha256(p) for p in paths}


class ExactRowCache:
    """Cache exact non-robust unique rows; every scale still uses prior rows only.

    Global lexicographic row codes select precisely the same sorted subset as
    np.unique(prior, axis=0). Robust state blocks retain the original calculation.
    The cached arrays include later events but neither their values nor count
    enter a query's scale: only codes selected by its eligible archive do.
    """

    def __init__(self):
        self.blocks = {}

    def __call__(self, candidates, query, distance_blocks, robust_blocks=()):
        components = {}
        for name, vectors in distance_blocks.items():
            prior = vectors.loc[candidates.event_id].to_numpy(dtype=float)
            current = vectors.loc[query.event_id].to_numpy(dtype=float)
            if name in robust_blocks:
                center = np.median(prior, axis=0)
                divisor = np.quantile(prior, 0.75, axis=0) - np.quantile(prior, 0.25, axis=0)
                divisor = np.where(divisor == 0, 1.0, divisor)
                prior = (prior - center) / divisor
                current = (current - center) / divisor
                unique = np.unique(prior, axis=0)
            else:
                key = id(vectors)
                if key not in self.blocks:
                    unique, inverse = np.unique(
                        vectors.to_numpy(dtype=float), axis=0, return_inverse=True
                    )
                    self.blocks[key] = (vectors, unique, pd.Series(inverse, index=vectors.index))
                owner, all_unique, codes = self.blocks[key]
                assert owner is vectors
                unique = all_unique[np.unique(codes.loc[candidates.event_id].to_numpy())]
            scale = (
                np.sqrt(2 * len(unique) / (len(unique) - 1) * unique.var(axis=0).sum())
                if len(unique) > 1
                else 0.0
            )
            scale = float(scale) if scale > 0 else 1.0
            components[name + "_distance"] = np.linalg.norm(prior - current, axis=1)
            components[name + "_prior_scale"] = np.full(len(prior), scale)
        normalized = [
            components[name + "_distance"] / components[name + "_prior_scale"]
            for name in distance_blocks
        ]
        distance = np.sqrt(np.mean(np.square(normalized), axis=0))
        return pd.Series(distance, index=candidates.index), pd.DataFrame(
            components, index=candidates.index
        )


def replay_baseline(rows, donors):
    old = pd.read_csv(X.OUT / "event_assessments.csv", float_precision="round_trip")
    keys = [*KEYS, "query_event_id"]
    expected = old[old.policy.eq("pooled")].set_index(keys).sort_index()
    actual = rows.set_index(keys).sort_index()
    pd.testing.assert_index_equal(actual.index, expected.index)
    np.testing.assert_allclose(actual[METRICS], expected[METRICS], atol=1e-12, rtol=0)
    old = pd.read_csv(X.OUT / "selected_donors.csv", float_precision="round_trip", low_memory=False)
    keys = ["cohort", "scenario", "analysis", "policy", "arm", "query_event_id", "rank"]
    expected = old[old.policy.eq("pooled")].set_index(keys).sort_index()
    actual = donors.set_index(keys).sort_index()
    pd.testing.assert_index_equal(actual.index, expected.index)
    assert actual.analogue_event_id.equals(expected.analogue_event_id)
    np.testing.assert_allclose(actual.distance, expected.distance, atol=1e-12, rtol=0)
    return dict(
        event_rows=len(actual),
        baseline_donor_ids_identical=True,
        maximum_distance_difference=float((actual.distance - expected.distance).abs().max()),
        baseline_scores_within_1e_12=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    observations, hashes = held_observations()
    for name in [
        "manifest.json",
        "event_inventory.csv",
        "q_only_signatures.csv",
        "q_only_standardized_histories.parquet",
        "q_only_ttm_ordered.parquet",
        "q_only_discharge_state.parquet",
    ]:
        hashes.update(fingerprints([E.READY / name]))
    years_path = ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet"
    hashes.update(
        fingerprints(
            [
                years_path,
                S.TTM.MODEL_DIR / "model.safetensors",
                S.TTM.MODEL_DIR / "config.json",
                ROOT / "docs/limburg-event-definition-sensitivity-2026-10-14.md",
            ]
        )
    )
    years = pd.read_parquet(years_path)
    all_rows, all_counts = [], []
    for name, (quantile, gap) in CONFIGS.items():
        print(f"Preparing {name}", flush=True)
        out = args.output_dir / name
        out.mkdir(exist_ok=True)
        index, windows, census, thresholds = build_library(observations, quantile, gap)
        census.to_csv(out / "candidate_episodes.csv", index=False)
        thresholds.to_csv(out / "era_thresholds.csv", index=False)
        sample, meta, raw, state, ordered, response = prepare(index, windows, out)
        if name == "p99_72":
            validate_baseline(index, sample, raw, state)
        for country, group in index.groupby("country"):
            signatures = sample[sample.country.eq(country)]
            all_counts.append(
                dict(
                    run=name,
                    country=country,
                    candidate_episodes=int(census.country.eq(country).sum()),
                    model_inventory=len(group),
                    usable_inputs=int(signatures.common_representation_sample.sum()),
                    scorable_responses=int(signatures.complete_scoring_sample.sum()),
                    regional_groups=group.storm_id.nunique(),
                )
            )
        print(json.dumps(all_counts[-2:]), flush=True)
        if args.prepare_only:
            continue
        cohorts = cohort_inputs(sample, raw, state, ordered, years)
        original_distance = B.block_distances
        B.block_distances = ExactRowCache()
        try:
            outputs = [
                X.run_comparisons(subset, arms, cohort, response, meta, policies=("pooled",))
                for cohort, (subset, arms) in cohorts.items()
            ]
        finally:
            B.block_distances = original_distance
        rows = pd.concat([v[0] for v in outputs], ignore_index=True)
        donors = pd.concat([v[1] for v in outputs], ignore_index=True)
        coverage = pd.concat([v[2] for v in outputs], ignore_index=True)
        if name == "p99_72":
            (out / "baseline_replay.json").write_text(
                json.dumps(replay_baseline(rows, donors), indent=2) + "\n"
            )
            hashes.update(
                fingerprints(
                    [
                        X.OUT / f
                        for f in [
                            "event_assessments.csv",
                            "selected_donors.csv",
                            "archive_coverage.csv",
                        ]
                    ]
                )
            )
        print(f"Archive references {name}", flush=True)
        rows = add_archive_references(rows, cohorts, response)
        rows.to_csv(out / "event_assessments.csv", index=False)
        donors.to_csv(out / "selected_donors.csv", index=False)
        coverage.to_csv(out / "archive_coverage.csv", index=False)
        summarise(rows).to_csv(out / "summary_by_country.csv", index=False)
        print(f"Paired intervals {name}", flush=True)
        paired_intervals(rows).to_csv(out / "paired_intervals.csv", index=False)
        all_rows.append(rows.assign(run=name))
    pd.DataFrame(all_counts).to_csv(args.output_dir / "event_coverage.csv", index=False)
    if args.prepare_only:
        return
    compare_runs(pd.concat(all_rows, ignore_index=True), args.output_dir)
    manifest = dict(
        configurations=CONFIGS,
        event_selection_only=True,
        normalizer="fixed era p99",
        regional_grouping_hours=72,
        history_hours=512,
        response_hours=72,
        seed=20261013,
        bootstrap_draws=9999,
        sampled_events=0,
        trained_models=0,
        source_sha256=fingerprints(
            [
                Path(__file__),
                ROOT / "src/event_study.py",
                *[
                    ROOT / "scripts" / f
                    for f in [
                        "46_review_events.py",
                        "65_hydrological_analogue_baseline.py",
                        "70_ttm_analogue_comparison.py",
                        "72_german_wurm_analogue_extension.py",
                        "75_strengthen_foundation_representations.py",
                        "78_cross_river_analogue_checks.py",
                        "81_run_expanded_event_analogues.py",
                        "82_review_analogue_information.py",
                        "84_complete_cross_border_analogues.py",
                    ]
                ],
            ]
        ),
        input_sha256=hashes,
        code_version=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        outputs_sha256={
            str(p.relative_to(args.output_dir)): S.TTM.sha256(p)
            for p in args.output_dir.rglob("*")
            if p.is_file() and p.name not in ["manifest.json", "independent_audit.json"]
        },
    )
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(dict(completed_runs=list(CONFIGS), event_score_rows=sum(map(len, all_rows)))),
        flush=True,
    )


def compare_runs(rows, out):
    counts, common = [], []
    baseline = rows[rows.run.eq("p99_72")]
    for name in ["p95_72", "p99_120"]:
        alternative = rows[rows.run.eq(name)]
        for config, group in alternative.groupby(KEYS):
            mask = np.ones(len(baseline), dtype=bool)
            for field, value in zip(KEYS, config, strict=True):
                mask &= baseline[field].eq(value).to_numpy()
            base = baseline[mask]
            shared = set(group.query_event_id).intersection(base.query_event_id)
            counts.append(
                dict(
                    run=name,
                    **dict(zip(KEYS, config, strict=True)),
                    baseline_queries=len(base),
                    alternative_queries=len(group),
                    shared_queries=len(shared),
                    added_queries=len(group) - len(shared),
                    removed_queries=len(base) - len(shared),
                )
            )
            for label, g in [
                ("baseline", base[base.query_event_id.isin(shared)]),
                ("alternative", group[group.query_event_id.isin(shared)]),
            ]:
                common.append(
                    dict(
                        run=name,
                        population=label,
                        **dict(zip(KEYS, config, strict=True)),
                        events=len(g),
                        **{m: g[m].mean() for m in METRICS},
                    )
                )
    pd.DataFrame(counts).to_csv(out / "query_membership_changes.csv", index=False)
    pd.DataFrame(common).to_csv(out / "common_onset_summaries.csv", index=False)
    summary = pd.concat(
        [summarise(g).assign(run=name) for name, g in rows.groupby("run")], ignore_index=True
    )
    summary.to_csv(out / "all_run_summaries.csv", index=False)
    # A compact scientific comparison; different full cohorts remain explicit.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, country in zip(axes, ["NL", "DE"], strict=True):
        part = summary[
            summary.cohort.eq("q_only")
            & summary.scenario.eq("all_rivers")
            & summary.analysis.eq("main")
            & summary.target_k.eq(5)
            & summary.query_country.eq(country)
        ]
        for arm in ["r1", "raw_state", "ttm_ordered_state"]:
            g = part[part.arm.eq(arm)].set_index("run").reindex(CONFIGS)
            ax.plot(list(CONFIGS), g.mean_peak_scaled_shape_rmse, marker="o", label=arm)
        ax.set_title(country + ": full available query population")
        ax.set_ylabel("Mean donor response-shape RMSE")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "definition_shape_comparison.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
