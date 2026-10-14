#!/usr/bin/env python3
"""Complete held-data country/archive, geographic and rainfall comparisons.

Retrospective, exploratory; no training, new download, human labels or raw disclosure.
Outputs stay separate from all earlier runs. Countries are confounded with rivers.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "context_review", ROOT / "scripts/83_review_alphaearth_event_information.py"
)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
E, C, B = A.E, A.C, A.B
OUT = ROOT / "results/basin_ai_cross_border_completion"
GAUGES = {"2828300000200": "herzogenrath_1", "2828900000200": "randerath"}
METRICS = A.METRICS


def radar_weights(catchments, manifest):
    """Exact full-catchment intersections; never normalize a truncated catchment."""
    xmin, ymin, xmax, ymax = manifest["crop_bounds_m"]
    size = manifest["cell_m"]
    nr, nc = round((ymax - ymin) / size), round((xmax - xmin) / size)
    cells = gpd.GeoSeries(
        [
            box(xmin + c * size, ymin + r * size, xmin + (c + 1) * size, ymin + (r + 1) * size)
            for r in range(nr)
            for c in range(nc)
        ],
        crs=manifest["crs"],
    )
    projected = catchments.to_crs(manifest["crs"])
    weights = []
    for row in projected.itertuples():
        w = cells.intersection(row.geometry).area.to_numpy().reshape(nr, nc)
        if not np.isclose(w.sum(), row.geometry.area, rtol=1e-6):
            raise ValueError(f"Catchment outside held crop: {row.gauge}")
        weights.append(w / w.sum())
    return np.stack(weights)


def weighted_rain(rain, weights):
    missing = rain < 0
    values = np.einsum("trc,krc->tk", np.where(missing, 0, rain).astype(float) / 10, weights)
    incomplete = np.einsum("trc,krc->tk", missing.astype(float), (weights > 0).astype(float)) > 0
    values[incomplete] = np.nan
    return values


def german_rainfall(out, hashes):
    radar = ROOT / "data/raw/radolan_rw"
    manifest_path = radar / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    geometry = ROOT / "data/interim/foundation_model_catchments.gpkg"
    hashes[str(manifest_path.relative_to(ROOT))] = E.S.TTM.sha256(manifest_path)
    hashes[str(geometry.relative_to(ROOT))] = E.S.TTM.sha256(geometry)
    catchments = gpd.read_file(geometry)
    catchments = catchments[catchments.jurisdiction.eq("DE")].sort_values("gauge")
    if set(catchments.gauge) != set(GAUGES.values()):
        raise ValueError("German catchment/station mapping changed")
    weights = radar_weights(catchments, manifest)
    frames = []
    for path in sorted((radar / "crops").glob("*_rw_*.npz")):
        digest = E.S.TTM.sha256(path)
        stamp = path.stem.rsplit("_", 1)[-1]
        month = stamp[:4] + "-" + stamp[4:6]
        if digest != manifest["months"][month]["crop_sha256"]:
            raise ValueError("Changed radar crop: " + str(path))
        hashes[str(path.relative_to(ROOT))] = digest
        with np.load(path) as data:
            ends = pd.DatetimeIndex(data["end_utc"]).tz_localize("UTC")
            values = weighted_rain(data["rain_0p1mm"], weights)
        frames.append(pd.DataFrame(values, index=ends.ceil("h"), columns=catchments.gauge))
    rainfall = pd.concat(frames).sort_index()
    if rainfall.index.has_duplicates:
        raise ValueError("Duplicate hour-end radar labels")
    rainfall = rainfall.reindex(
        pd.date_range(rainfall.index.min(), rainfall.index.max(), freq="h")
    ).round(3)
    rainfall.index.name = "timestamp_utc"
    rainfall.to_csv(out / "german_catchment_hourly_rainfall.csv")
    return rainfall


def add_rain_signatures(sample, rainfall):
    """Same full 512h rainfall completeness rule as original common input sample."""
    frame = sample.copy()
    complete, fractions = [], []
    for i, q in frame.iterrows():
        if q.country == "DE":
            dates = pd.date_range(q.onset_utc - pd.Timedelta(hours=511), q.onset_utc, freq="h")
            rain = rainfall[GAUGES[q.gauge]].reindex(dates)
            frac = rain.notna().mean()
            for hours in [6, 24, 72, 168]:
                recent = rain.iloc[-hours:]
                frame.loc[i, f"rain_sum_{hours}h_mm"] = (
                    recent.sum() if recent.notna().all() else np.nan
                )
            frame.loc[i, "rain_max_1h_24h_mm"] = (
                rain.iloc[-24:].max() if rain.iloc[-24:].notna().all() else np.nan
            )
        else:
            frac = q.history_rainfall_fraction
        fractions.append(frac)
        complete.append(bool(q.complete_scoring_sample and np.isclose(frac, 1)))
    frame["rain_history_fraction"] = fractions
    frame["complete_scoring_sample"] = complete
    return frame


def join_context(sample, years):
    frame = sample.copy()
    frame["event_year"] = frame.onset_utc.dt.year
    frame["embedding_year"] = frame.event_year - 1
    frame["context_gauge"] = frame.gauge.replace(GAUGES)
    bands = [f"A{i:02d}" for i in range(64)]
    geographic = years[["gauge", "embedding_year", "catchment_area_km2", *bands]].rename(
        columns={"gauge": "context_gauge"}
    )
    frame = frame.merge(
        geographic, on=["context_gauge", "embedding_year"], how="left", validate="many_to_one"
    )
    frame["context_available"] = frame[bands].notna().all(axis=1)
    # Do not impose Dutch rain/weather eligibility on this Q-only context comparison.
    return frame


def context_settings(sample, ordered, state, years):
    ids = sample.event_id
    bands = [f"A{i:02d}" for i in range(64)]
    annual = sample.set_index("event_id")[bands]
    annual = annual.div(np.linalg.norm(annual.to_numpy(), axis=1), axis=0)
    static = (
        years[years.embedding_year.eq(2017)]
        .set_index("gauge")[bands]
        .loc[sample.context_gauge]
        .copy()
    )
    static.index = ids
    static = static.div(np.linalg.norm(static.to_numpy(), axis=1), axis=0)
    area = pd.DataFrame({"log_area": np.log(sample.catchment_area_km2.to_numpy())}, index=ids)
    identity = pd.get_dummies(sample.set_index("event_id").gauge, dtype=float)
    base = {"temporal": ordered.loc[ids], "state": state.loc[ids]}
    arms = {}
    for name, context in [
        ("temporal", None),
        ("area", area),
        ("identity", identity),
        ("static_2017", static),
        ("alphaearth", annual),
    ]:
        arms[name] = {
            "distance_blocks": {**base, **({name: context} if context is not None else {})},
            "robust_distance_blocks": ("state",),
        }
    return arms


def run_comparisons(
    sample, arms, cohort, response, meta, policies=("pooled", "domestic", "foreign")
):
    rows, slots, coverage = [], [], []
    for scenario in ["all_rivers", "other_rivers"]:
        for quality in [False, True]:
            analysis = "quality_sensitivity" if quality else "main"
            eligible = sample[
                sample.complete_scoring_sample & (~sample.measurement_concern if quality else True)
            ]
            for policy in policies:
                expected_ids = None
                for arm, settings in arms.items():
                    scores, donors = B.retrieve_prior_analogues(
                        sample,
                        top_k=10,
                        min_candidates=1,
                        min_candidate_storms=1,
                        allow_short_archive=True,
                        exclude_same_river=scenario == "other_rivers",
                        exclude_measurement_concerns=quality,
                        donor_country=policy,
                        **settings,
                    )
                    ids = set(scores.query_event_id) if not scores.empty else set()
                    if expected_ids is not None and ids != expected_ids:
                        raise ValueError("Arm eligibility mismatch")
                    expected_ids = ids
                    for country, g in eligible.groupby("country"):
                        available = g.event_id.isin(ids)
                        coverage.append(
                            dict(
                                cohort=cohort,
                                scenario=scenario,
                                analysis=analysis,
                                policy=policy,
                                arm=arm,
                                country=country,
                                scorable_events=len(g),
                                available_events=int(available.sum()),
                                unavailable_events=int((~available).sum()),
                            )
                        )
                    if scores.empty:
                        continue
                    validate_donors(donors, meta, policy, scenario, quality)
                    for k in [5, 10]:
                        d = donors[donors["rank"].le(k)]
                        evaluated, scored = C.assess(scores, d, response, meta)
                        phases = pd.DataFrame(
                            [
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
                        )
                        evaluated = evaluated.merge(
                            phases, on="query_event_id", validate="one_to_one"
                        )
                        tags = dict(
                            cohort=cohort,
                            scenario=scenario,
                            analysis=analysis,
                            policy=policy,
                            arm=arm,
                            target_k=k,
                        )
                        rows.append(evaluated.assign(**tags))
                        if k == 10:
                            slots.append(scored.assign(**tags))
                    print(
                        f"{cohort}/{scenario}/{analysis}/{policy}/{arm}: {len(scores)}", flush=True
                    )
    return (
        pd.concat(rows, ignore_index=True),
        pd.concat(slots, ignore_index=True),
        pd.DataFrame(coverage),
    )


def validate_donors(donors, meta, policy, scenario, quality):
    q = meta.loc[donors.query_event_id].reset_index(drop=True)
    a = meta.loc[donors.analogue_event_id].reset_index(drop=True)
    assert (
        (pd.to_datetime(a.onset_utc, utc=True) + pd.Timedelta(hours=72))
        <= pd.to_datetime(q.onset_utc, utc=True)
    ).all()
    assert a.storm_id.ne(q.storm_id).all()
    assert not donors.duplicated(["query_event_id", "analogue_storm_id"]).any()
    if policy != "pooled":
        same = q.country.eq(a.country)
        assert (same if policy == "domestic" else ~same).all()
    if scenario == "other_rivers":
        assert a.physical_river_group.ne(q.physical_river_group).all()
    if quality:
        assert not q.measurement_concern.any() and not a.measurement_concern.any()
    assert a.q_only_scoring_sample.all() and q.q_only_scoring_sample.all()


def paired_differences(reference, challenger, metric, equal_counts):
    keys = ["query_event_id", "query_storm_id", "query_onset_utc", "actual_donor_count", metric]
    pair = reference[keys].merge(
        challenger[["query_event_id", "actual_donor_count", metric]],
        on="query_event_id",
        suffixes=("_ref", "_test"),
        validate="one_to_one",
    )
    if equal_counts:
        pair = pair[pair.actual_donor_count_ref.eq(pair.actual_donor_count_test)].copy()
    pair["difference"] = pair[metric + "_test"] - pair[metric + "_ref"]
    pair["storm_year"] = pd.to_datetime(
        pair.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
    ).dt.year
    return pair


def intervals(rows):
    records = []
    group_keys = ["cohort", "scenario", "analysis", "target_k", "query_country"]
    for config, g in rows.groupby(group_keys):
        comparisons = []
        for arm, a in g.groupby("arm"):
            for ref, test in [
                ("domestic", "pooled"),
                ("domestic", "foreign"),
                ("foreign", "pooled"),
            ]:
                comparisons.append(
                    (f"archive:{arm}:{ref}->{test}", a[a.policy.eq(ref)], a[a.policy.eq(test)])
                )
        for policy, a in g.groupby("policy"):
            refs = (
                [("raw_state", "ttm_ordered_state")]
                if config[0] != "context"
                else [(c, "alphaearth") for c in ["temporal", "area", "identity", "static_2017"]]
            )
            if config[0] == "rain_matched":
                refs += [("r0", "ttm_ordered_state"), ("r0", "raw_state")]
            for ref, test in refs:
                comparisons.append(
                    (f"model:{policy}:{ref}->{test}", a[a.arm.eq(ref)], a[a.arm.eq(test)])
                )
        for label, ref, test in comparisons:
            for mode in ["equal_donor_count", "all_shared_queries"]:
                for metric in METRICS:
                    pair = paired_differences(ref, test, metric, mode == "equal_donor_count")
                    if pair.empty:
                        records.append(
                            dict(
                                zip(group_keys, config, strict=True),
                                comparison=label,
                                pairing=mode,
                                metric=metric,
                                status="no_shared_queries",
                                query_count=0,
                            )
                        )
                        continue
                    for unit in ["query_storm_id", "storm_year"]:
                        if pair[unit].nunique() < 2:
                            estimate = dict(
                                difference=pair.difference.mean(),
                                query_count=len(pair),
                                cluster_count=pair[unit].nunique(),
                                draws=0,
                                lower=np.nan,
                                upper=np.nan,
                            )
                            status = "too_few_clusters_for_interval"
                        else:
                            estimate = C.REVIEW.cluster_interval(pair, unit)
                            status = "estimated"
                        records.append(
                            dict(
                                zip(group_keys, config, strict=True),
                                comparison=label,
                                pairing=mode,
                                metric=metric,
                                resampling_unit=unit,
                                status=status,
                                **estimate,
                            )
                        )
    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    manifest = json.loads((E.READY / "manifest.json").read_text())
    for name, digest in manifest["input_sha256"].items():
        assert E.S.TTM.sha256(ROOT / name) == digest, name
        hashes[name] = digest
    for name, digest in manifest["outputs_sha256"].items():
        assert E.S.TTM.sha256(E.READY / name) == digest, name
        hashes[str((E.READY / name).relative_to(ROOT))] = digest
    meta = pd.read_csv(E.READY / "event_inventory.csv").set_index("event_id")
    sample = pd.read_csv(E.READY / "q_only_signatures.csv", parse_dates=["onset_utc"])
    for field in ["country", "physical_river_group", "history_rainfall_fraction"]:
        sample[field] = sample.event_id.map(meta[field])
    _, _, index, windows = C.REVIEW.load_inputs()
    response, _, _ = C.CENSUS.load_curves(index, windows)
    raw = pd.read_parquet(E.READY / "q_only_standardized_histories.parquet")
    ordered = pd.read_parquet(E.READY / "q_only_ttm_ordered.parquet")
    state = pd.read_parquet(E.READY / "q_only_discharge_state.parquet")
    temporal = {"r1": {"representation_vectors": raw}}
    for name, v in [("raw_state", raw), ("ttm_ordered_state", ordered)]:
        temporal[name] = {
            "distance_blocks": {"temporal": v, "state": state},
            "robust_distance_blocks": ("state",),
        }
    outputs = [run_comparisons(sample, temporal, "q_only", response, meta)]
    rainfall = german_rainfall(out, hashes)
    rain = add_rain_signatures(sample, rainfall)
    rain[
        [
            "event_id",
            "country",
            "rain_history_fraction",
            "complete_scoring_sample",
            *B.FEATURE_COLUMNS,
        ]
    ].to_csv(out / "rainfall_event_coverage.csv", index=False)
    outputs.append(run_comparisons(rain, {"r0": {}, **temporal}, "rain_matched", response, meta))
    years_path = ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet"
    hashes[str(years_path.relative_to(ROOT))] = E.S.TTM.sha256(years_path)
    years = pd.read_parquet(years_path)
    context = join_context(sample, years)
    context[
        [
            "event_id",
            "gauge",
            "context_gauge",
            "country",
            "event_year",
            "embedding_year",
            "context_available",
            "complete_scoring_sample",
        ]
    ].to_csv(out / "context_event_coverage.csv", index=False)
    supported = context[context.context_available & context.common_representation_sample].copy()
    assert supported.embedding_year.eq(supported.event_year - 1).all()
    outputs.append(
        run_comparisons(
            supported, context_settings(supported, ordered, state, years), "context", response, meta
        )
    )
    rows = pd.concat([r[0] for r in outputs], ignore_index=True)
    donors = pd.concat([r[1] for r in outputs], ignore_index=True)
    coverage = pd.concat([r[2] for r in outputs], ignore_index=True)
    rows.to_csv(out / "event_assessments.csv", index=False)
    donors.to_csv(out / "selected_donors.csv", index=False)
    coverage.to_csv(out / "archive_coverage.csv", index=False)
    keys = ["cohort", "scenario", "analysis", "policy", "arm", "target_k", "query_country"]
    summary = (
        rows.groupby(keys)
        .agg(
            events=("query_event_id", "size"),
            groups=("query_storm_id", "nunique"),
            **{m: (m, "mean") for m in METRICS},
            actual_donors=("actual_donor_count", "mean"),
            cross_border_donor_share=("cross_country_share", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(out / "summary_by_country.csv", index=False)
    rows.groupby(keys + ["query_watercourse"])[METRICS].mean().reset_index().to_csv(
        out / "summary_by_watercourse.csv", index=False
    )
    print("Computing paired country/archive and model intervals", flush=True)
    intervals(rows).to_csv(out / "paired_intervals.csv", index=False)
    # Provider/quality differences retain the full inventory, not only scored events.
    fields = [
        "provider_status",
        "measurement_concern",
        "provisional_high_flow",
        "response_out_of_rating_domain",
        "response_crosses_rating_period",
        "response_stage_complete",
        "redundant_sensor_substitution_unflagged",
        "q_only_input_sample",
        "q_only_scoring_sample",
    ]
    quality = []
    for country, g in meta.groupby("country"):
        for field in fields:
            for value, n in (
                g[field].fillna("not_recorded_or_not_applicable").astype(str).value_counts().items()
            ):
                quality.append(dict(country=country, field=field, value=value, events=int(n)))
    pd.DataFrame(quality).to_csv(out / "measurement_inventory.csv", index=False)
    # Pooled Q-only scores/donors must reproduce held main results exactly.
    old = pd.read_csv(E.OUT / "event_assessments.csv", float_precision="round_trip")
    key = ["scenario", "analysis", "arm", "target_k", "query_event_id"]
    current = rows[rows.cohort.eq("q_only") & rows.policy.eq("pooled")].set_index(key).sort_index()
    saved = old[old.cohort.eq("q_only_pooled")].set_index(key).sort_index()
    pd.testing.assert_index_equal(current.index, saved.index)
    np.testing.assert_allclose(current[METRICS], saved[METRICS], rtol=0, atol=1e-12)
    old_pairs = pd.read_csv(E.OUT / "selected_donors.csv", float_precision="round_trip")
    dk = ["scenario", "analysis", "arm", "query_event_id", "rank"]
    a = donors[donors.cohort.eq("q_only") & donors.policy.eq("pooled")].set_index(dk).sort_index()
    b = (
        old_pairs[old_pairs.cohort.eq("q_only_pooled") & old_pairs.target_k.eq(10)]
        .set_index(dk)
        .sort_index()
    )
    pd.testing.assert_index_equal(a.index, b.index)
    assert a.analogue_event_id.eq(b.analogue_event_id).all()
    np.testing.assert_allclose(a.distance, b.distance, rtol=0, atol=1e-12)
    validation = {
        "pooled_q_only_exact_replay": True,
        "chronology_country_river_quality_checks": "pass",
        "selected_slots": len(donors),
        "score_sets": len(rows),
        "human_labels_assigned": 0,
    }
    (out / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    source_hashes = {
        str(p.relative_to(ROOT)): E.S.TTM.sha256(p)
        for p in [
            Path(__file__),
            ROOT / "scripts/65_hydrological_analogue_baseline.py",
            ROOT / "scripts/78_cross_river_analogue_checks.py",
            ROOT / "scripts/81_run_expanded_event_analogues.py",
            ROOT / "scripts/83_review_alphaearth_event_information.py",
        ]
    }
    receipt = {
        "input_sha256": hashes,
        "source_sha256": source_hashes,
        "code_version": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "bootstrap_draws": 9999,
        "seed": 20261013,
        "context_family": "ordered_state",
        "countries_confounded_with_rivers": True,
        "rain_hour_label": "HH:50 accumulation end ceil to HH+1:00 UTC",
        "outputs_sha256": {p.name: E.S.TTM.sha256(p) for p in out.iterdir() if p.suffix == ".csv"},
    }
    (out / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(validation), flush=True)


if __name__ == "__main__":
    main()
