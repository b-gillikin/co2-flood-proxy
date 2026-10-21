"""Audit completed aggregates and census comparison populations, without model scoring."""

import json
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_coverage_review import coverage_issues, donor_support, membership_table
from src.eo_inputs import ROUTES, sha256

MODELS = ["prithvi", "croma", "terramind", "dofa", "copernicus_fm", "satmae", "anysat", "olmoearth"]


def main():
    preparation = ROOT / "results/eo_comparison_preparation"
    out = ROOT / "results/eo_completed_coverage_review"
    out.mkdir(parents=True, exist_ok=True)
    obs = pd.read_parquet(preparation / "observations.parquet")
    links = pd.read_parquet(preparation / "observation_windows.parquet")
    contexts = {c["context_id"]: c for c in json.loads((preparation / "contexts.json").read_text())}
    joins = obs.merge(
        links[["observation_id", "kind", "context_id"]].drop_duplicates(),
        on="observation_id",
        validate="one_to_many",
    )
    geometry_hash = sha256(preparation / "catchments.gpkg")
    provenance, ledgers, hashes = [], [], {}
    for model in MODELS:
        folder = ROOT / "results/eo_catchment_representations/per_model" / model
        folder /= "token_consistent/census" if model == "olmoearth" else "census"
        manifest_path = folder / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        errors = []
        hashes[str(manifest_path.relative_to(ROOT))] = sha256(manifest_path)
        for name, digest in manifest["outputs_sha256"].items():
            if sha256(folder / name) != digest:
                errors.append("aggregate_checksum:" + name)
        if manifest["engineering"] or manifest["errors"]:
            errors.append("engineering_or_aggregation_errors")
        if manifest["catchments_sha256"] != geometry_hash:
            errors.append("catchment_geometry_changed")
        runs = []
        for name, digest in manifest["source_sha256"].items():
            if not name.endswith("/manifest.json"):
                continue
            path = ROOT / name
            if sha256(path) != digest:
                errors.append("run_manifest_checksum:" + name)
            run = json.loads(path.read_text())
            for code, expected in run["code"].items():
                if sha256(ROOT / code) != expected:
                    errors.append("run_code_changed:" + code)
            status = json.loads(path.with_name("status.json").read_text())
            if (
                run["purpose"] != "context_census"
                or status["status"] != "completed"
                or status["errors"]
            ):
                errors.append("extraction_incomplete:" + name)
            runs.append(
                {
                    "manifest": name,
                    "run": path.parent.name,
                    "device": run.get("execution_device", "cpu"),
                    "mask_policy": run.get("mask_policy", "original_adapter"),
                    "status": status,
                }
            )
        if not runs:
            errors.append("missing_extraction_run_provenance")
        rep = pd.read_parquet(folder / (model + ".parquet"))
        cov = pd.read_parquet(folder / "coverage.parquet")
        errors.extend(coverage_issues(cov))
        features = [c for c in rep if c.startswith("e") and c[1:].isdigit()]
        v = rep[features].to_numpy(float)
        if not np.isfinite(v).all() or (np.linalg.norm(v, axis=1) == 0).any():
            errors.append("invalid_vectors")
        if rep.duplicated(["context_id", "catchment_gauge"]).any():
            errors.append("duplicate_representation")
        expected = cov.loc[
            cov.status.eq("available_partial_or_full_area"), ["context_id", "catchment_gauge"]
        ]
        actual = rep[["context_id", "catchment_gauge"]]
        if set(map(tuple, expected.to_numpy())) != set(map(tuple, actual.to_numpy())):
            errors.append("representation_coverage_disagreement")
        for row in cov.itertuples():
            windows = [w["id"] for w in contexts[row.context_id]["windows"]]
            if list(row.window_ids) != windows or row.n_frames != len(windows):
                errors.append("calendar_slots_differ:" + row.context_id)
        ledger = joins.merge(
            cov.drop(columns=["kind"]),
            on=["context_id", "catchment_gauge"],
            how="left",
            validate="many_to_one",
        )
        ledger["model"] = model
        ledger["available"] = ledger.status.eq("available_partial_or_full_area")
        ledger["status"] = ledger.status.fillna("no_encoded_catchment_support")
        ledgers.append(ledger)
        provenance.append(
            {
                "model": model,
                "aggregate": str(folder.relative_to(ROOT)),
                "representation_rows": len(rep),
                "dimensions": len(features),
                "coverage_rows": len(cov),
                "receipt_hashes_recorded": len(manifest["source_sha256"]),
                "runs": runs,
                "issues": sorted(set(errors)),
            }
        )
        print(model, len(rep), "issues", sorted(set(errors)), flush=True)
    ledger = pd.concat(ledgers, ignore_index=True)
    ledger.to_parquet(out / "observation_coverage.parquet", index=False)
    summaries = []
    for key, group in ledger.groupby(["model", "cohort", "kind", "country", "gauge"], dropna=False):
        eligible = group[group.scoring_eligible]
        supported = eligible[eligible.available]
        summaries.append(
            {
                **dict(zip(["model", "cohort", "kind", "country", "gauge"], key, strict=True)),
                "total": len(group),
                "eligible": len(eligible),
                "available": len(supported),
                "measurement_concerns_available": int(supported.measurement_concern.sum()),
                "median_mean_fraction": supported.observed_mean_fraction.median(),
                "median_min_fraction": supported.observed_min_fraction.median(),
                "median_common_fraction": supported.observed_common_fraction.median(),
            }
        )
    pd.DataFrame(summaries).to_parquet(out / "coverage_summary.parquet", index=False)
    # Exact pre-existing Q-only representation population, not a new event filter.
    ready = ROOT / "results/basin_ai_event_interpretation_ready"
    sample = pd.read_csv(ready / "q_only_signatures.csv")
    baseline = set(sample.loc[sample.complete_scoring_sample, "event_id"])
    for name in ["q_only_standardized_histories", "q_only_ttm_ordered", "q_only_discharge_state"]:
        baseline &= set(pd.read_parquet(ready / (name + ".parquet")).index)
    metadata = pd.read_csv(ready / "event_inventory.csv")
    high = obs[obs.cohort.eq("high_water") & obs.event_id.isin(baseline)].merge(
        metadata[["event_id", "physical_river_group"]], on="event_id", validate="one_to_one"
    )
    membership, pairs, donor_rows = [], [], []
    for kind in ["monthly_snapshot", "monthly", "recent"]:
        selected = ledger[ledger.cohort.eq("high_water") & ledger.kind.eq(kind) & ledger.available]
        available = {
            m: set(selected.loc[selected.model.eq(m), "event_id"]) & baseline for m in MODELS
        }
        table = membership_table(baseline, available, MODELS)
        table["kind"] = kind
        membership.append(table)
        for a, b in combinations(MODELS, 2):
            ids = available[a] & available[b]
            pairs.append(
                {
                    "kind": kind,
                    "first": a,
                    "second": b,
                    "first_available": len(available[a]),
                    "second_available": len(available[b]),
                    "same_event_population": len(ids),
                }
            )
        populations = {
            **available,
            "eight_completed_common": set(table.loc[table.common, "event_id"]),
        }
        for label, ids in populations.items():
            population = high[high.event_id.isin(ids)]
            for scenario in ["all_rivers", "other_rivers"]:
                for policy in ["pooled", "domestic", "foreign"]:
                    for quality in [False, True]:
                        donors = donor_support(population, scenario, policy, quality)
                        counts = donors.candidate_storms
                        donor_rows.append(
                            {
                                "kind": kind,
                                "population": label,
                                "scenario": scenario,
                                "policy": policy,
                                "quality": quality,
                                "queries": len(donors),
                                "no_prior_storm": int(counts.eq(0).sum()),
                                "at_least_5_storms": int(counts.ge(5).sum()),
                                "at_least_10_storms": int(counts.ge(10).sum()),
                            }
                        )
    pd.concat(membership).to_parquet(out / "high_water_membership.parquet", index=False)
    pd.DataFrame(pairs).to_parquet(out / "pairwise_populations.parquet", index=False)
    pd.DataFrame(donor_rows).to_parquet(out / "donor_support.parquet", index=False)
    # Reuse the full raw-pixel date audit; its latest date is a conservative
    # upper bound for the retained encoder support, not a model-specific date.
    raw = pd.read_parquet(preparation / "observed_window_coverage.parquet")
    dates = links.merge(
        obs[["observation_id", "catchment_gauge", "cutoff_utc"]], on="observation_id"
    ).merge(raw, on=["window_id", "catchment_gauge"])
    cutoff = dates.cutoff_utc.map(lambda t: t.timestamp() / 86400)
    timing = {
        "raw_pixel_links_checked": len(dates),
        "latest_raw_pixel_at_or_after_cutoff": int(dates.latest_day.ge(cutoff).sum()),
        "window_ends_after_cutoff": int(
            (pd.to_datetime(dates.window_end, utc=True) > dates.cutoff_utc).sum()
        ),
    }
    context_dates = links.merge(obs[["observation_id", "cutoff_utc"]], on="observation_id")
    context_dates["age_days"] = (
        context_dates.cutoff_utc - pd.to_datetime(context_dates.window_end, utc=True)
    ).dt.total_seconds() / 86400
    context_dates.groupby("kind").age_days.agg(["min", "median", "max"]).to_parquet(
        out / "window_age_summary.parquet"
    )
    for name in [
        "observations.parquet",
        "observation_windows.parquet",
        "contexts.json",
        "observed_window_coverage.parquet",
        "catchments.gpkg",
    ]:
        hashes[str((preparation / name).relative_to(ROOT))] = sha256(preparation / name)
    jobs_path = ROOT / "data/raw/limburg_compact_eo/jobs.json"
    jobs = json.loads(jobs_path.read_text())
    timing["source_jobs_checked"] = len(jobs)
    timing["source_jobs_outside_window"] = sum(
        any(
            t < datetime.fromisoformat(j["window"]["start"]).timestamp() * 1000
            or t >= datetime.fromisoformat(j["window"]["end"]).timestamp() * 1000
            for t in j["acquisition_ms"]
        )
        for j in jobs
    )
    for path in [
        Path(__file__).resolve(),
        ROOT / "src/eo_coverage_review.py",
        jobs_path,
        ready / "event_inventory.csv",
        ready / "q_only_signatures.csv",
        *[
            ready / (n + ".parquet")
            for n in [
                "q_only_standardized_histories",
                "q_only_ttm_ordered",
                "q_only_discharge_state",
            ]
        ],
    ]:
        hashes[str(path.relative_to(ROOT))] = sha256(path)
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "completed_models": MODELS,
        "pending_models": [m for m in ROUTES if m not in MODELS],
        "baseline_events": len(baseline),
        "provenance": provenance,
        "timing": timing,
        "input_sha256": hashes,
        "scope": "Aggregate checksums, vector/coverage/calendar integrity and run source fingerprints rechecked. Patch receipts and raw imagery were verified by the held extraction/aggregation/full-pixel audit; not independently reread here.",
        "outputs_sha256": {p.name: sha256(p) for p in out.glob("*.parquet")},
    }
    (out / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "issues": {p["model"]: p["issues"] for p in provenance},
                "timing": timing,
                "baseline_events": len(baseline),
            },
            indent=2,
        )
    )
    return int(
        any(p["issues"] for p in provenance)
        or any(
            timing[k]
            for k in [
                "latest_raw_pixel_at_or_after_cutoff",
                "window_ends_after_cutoff",
                "source_jobs_outside_window",
            ]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
