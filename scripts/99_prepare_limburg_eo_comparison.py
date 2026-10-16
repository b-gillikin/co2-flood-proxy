"""Build a census of EO event windows, source coverage and additional-window jobs.

No imagery download or model fitting. Uses existing event definitions and held
source catalogues; retains absent/pre-mission/pending windows explicitly.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_event_inputs import GERMAN_GAUGES, SEQUENCES, completed_windows, context_id
from src.eo_inputs import ROUTES, sha256


def script(name):
    spec = importlib.util.spec_from_file_location("compact", ROOT / "scripts" / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def observations():
    inventory = pd.read_csv(
        ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv"
    )
    storms = pd.read_parquet(ROOT / "results/storm_response/storm_gauge_responses.parquet")
    frames = []
    for cohort, frame, id_col, cutoff, start, end, eligible, river in [
        (
            "high_water",
            inventory,
            "event_id",
            "onset_utc",
            "onset_utc",
            "outcome_end_utc",
            "q_only_scoring_sample",
            "physical_river_group",
        ),
        (
            "rainfall_episode",
            storms,
            "row_id",
            "landmark_utc",
            "start_utc",
            "followup_end_utc",
            "numeric_usable",
            "physical_river",
        ),
    ]:
        x = pd.DataFrame(
            {
                "observation_id": cohort + "|" + frame[id_col],
                "event_id": frame[id_col],
                "cohort": cohort,
                "gauge": frame.gauge.astype(str),
                "country": frame.country,
                "river": frame[river],
                "storm_id": frame.storm_id,
                "cutoff_utc": pd.to_datetime(frame[cutoff], utc=True),
                "start_utc": pd.to_datetime(frame[start], utc=True),
                "outcome_end_utc": pd.to_datetime(frame[end], utc=True),
                "scoring_eligible": frame[eligible],
                "measurement_concern": frame.measurement_concern,
            }
        )
        x["catchment_gauge"] = x.gauge.replace(GERMAN_GAUGES)
        frames.append(x)
    result = pd.concat(frames, ignore_index=True)
    if result.observation_id.duplicated().any():
        raise ValueError("Duplicate observation identifiers")
    return result


def scan_local(jobs, catchments, archive, out, obs, links):
    """Read actual source masks and area-weight acquisition age; no outcomes."""
    import numpy as np

    from src.eo_event_inputs import pixel_area_weights
    from src.eo_inputs import read_tile

    indexed = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
    weights_cache = ROOT / "data/processed/eo_pixel_area_weights" / sha256(out / "catchments.gpkg")
    weights_cache.mkdir(parents=True, exist_ok=True)
    records = []
    errors = []
    verified = 0
    for j in jobs:
        if j["product"] not in {"hls", "s1_ascending", "s2_10m"}:
            continue
        path = archive / j["relative_path"]
        if not path.exists() or not path.with_suffix(".receipt.json").exists():
            continue
        if j["product"] == "s2_10m":
            other = indexed.get((j["window"]["id"], tuple(j["bounds"]), "s2_20m"))
            if not other:
                continue
            partner = archive / other["relative_path"]
            if not partner.exists() or not partner.with_suffix(".receipt.json").exists():
                continue
        try:
            tile = read_tile(archive, j, indexed)
            for c in catchments.itertuples():
                if c.geometry.intersection(box(*j["bounds"])).area <= 0:
                    continue
                weightfile = weights_cache / f"{c.gauge}_{path.stem}_{j['resolution']}.npz"
                if weightfile.exists():
                    with np.load(weightfile) as a:
                        weights = a["area_m2"]
                else:
                    weights = pixel_area_weights(c.geometry, j["bounds"], j["resolution"])
                    np.savez_compressed(weightfile, area_m2=weights)
                observed = weights * tile.valid
                positive = observed > 0
                area = float(observed.sum())
                records.append(
                    {
                        "window_id": j["window"]["id"],
                        "catchment_gauge": c.gauge,
                        "product": j["product"],
                        "observed_area_m2": area,
                        "full_area_m2": c.geometry.area,
                        "area_day_sum": float((observed * tile.days).sum()),
                        "oldest_day": float(tile.days[positive].min())
                        if positive.any()
                        else np.nan,
                        "latest_day": float(tile.days[positive].max())
                        if positive.any()
                        else np.nan,
                    }
                )
            verified += 1
        except Exception as e:
            errors.append({"path": j["relative_path"], "error": f"{type(e).__name__}: {e}"})
    raw = pd.DataFrame(records)
    if raw.empty:
        raise ValueError("No verified local imagery for pixel scan")
    grouped = raw.groupby(["window_id", "catchment_gauge", "product"], as_index=False).agg(
        observed_area_m2=("observed_area_m2", "sum"),
        full_area_m2=("full_area_m2", "first"),
        area_day_sum=("area_day_sum", "sum"),
        oldest_day=("oldest_day", "min"),
        latest_day=("latest_day", "max"),
    )
    if (grouped.observed_area_m2 > grouped.full_area_m2 * (1 + 1e-7)).any():
        raise ValueError("Overlapping tile area in source scan")
    grouped["observed_fraction"] = grouped.observed_area_m2 / grouped.full_area_m2
    grouped["mean_acquired_day"] = grouped.area_day_sum / grouped.observed_area_m2.replace(
        0, np.nan
    )
    grouped.to_parquet(out / "observed_window_coverage.parquet", index=False)
    lookup = grouped.set_index(["window_id", "catchment_gauge", "product"]).to_dict("index")
    calendar = links.groupby(["observation_id", "kind"]).agg(
        context_id=("context_id", "first"), windows=("window_id", list)
    )
    observations = obs.set_index("observation_id")
    summaries = []
    for (eid, kind), row in calendar.iterrows():
        event = observations.loc[eid]
        cutoff = event.cutoff_utc.timestamp() / 86400
        for model, (product, _, _) in ROUTES.items():
            slots = [lookup.get((w, event.catchment_gauge, product), {}) for w in row.windows]
            fractions = [a.get("observed_fraction", 0.0) for a in slots]
            dates = [a.get("mean_acquired_day", np.nan) for a in slots]
            observed_dates = [d for d in dates if pd.notna(d)]
            summaries.append(
                {
                    "observation_id": eid,
                    "event_id": event.event_id,
                    "cohort": event.cohort,
                    "model": model,
                    "kind": kind,
                    "context_id": row.context_id,
                    "slots": len(slots),
                    "locally_observed_slots": sum(f > 0 for f in fractions),
                    "observed_min_fraction": min(fractions),
                    "observed_mean_fraction": float(np.mean(fractions)),
                    "mean_age_days_observed_slots": cutoff - float(np.mean(observed_dates))
                    if observed_dates
                    else np.nan,
                    "status": "local_context_observed"
                    if all(f > 0 for f in fractions)
                    else "incomplete_local_context",
                }
            )
    pd.DataFrame(summaries).to_parquet(out / "event_model_context_coverage.parquet", index=False)
    report = {
        "verified_primary_tiles": verified,
        "window_catchment_product_rows": len(grouped),
        "errors": errors,
        "scope": "Local held tiles only; cloud-only files remain pending locally, not failed acquisitions.",
    }
    (out / "pixel_scan.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "data/raw/limburg_compact_eo")
    parser.add_argument("--out", type=Path, default=ROOT / "results/eo_comparison_preparation")
    parser.add_argument(
        "--build-supplement",
        action="store_true",
        help="Prepare extra jobs from held catalogues; no network/download",
    )
    parser.add_argument(
        "--scan-local",
        action="store_true",
        help="Verify held rasters and compute actual pixel-area coverage and age",
    )
    parser.add_argument(
        "--jobs-ledger", type=Path, help="Use a preserved original ledger to reproduce a supplement"
    )
    args = parser.parse_args()
    args.archive = args.archive.resolve()
    if args.jobs_ledger is not None:
        args.jobs_ledger = args.jobs_ledger.resolve()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    obs = observations()
    obs.to_parquet(args.out / "observations.parquet", index=False)
    contexts = {}
    links = []
    windows = {}
    for r in obs.itertuples():
        for kind in SEQUENCES:
            sequence = completed_windows(r.cutoff_utc, kind)
            key = context_id(kind, sequence)
            contexts[key] = {"context_id": key, "kind": kind, "windows": sequence}
            for slot, w in enumerate(sequence):
                windows[w["id"]] = w
                links.append(
                    {
                        "observation_id": r.observation_id,
                        "context_id": key,
                        "kind": kind,
                        "slot": slot,
                        "window_id": w["id"],
                        "window_end": w["end"],
                        "age_days": (r.cutoff_utc - pd.Timestamp(w["end"])).total_seconds() / 86400,
                    }
                )
    links = pd.DataFrame(links)
    if links.age_days.lt(0).any():
        raise ValueError("Future composite in event inputs")
    links.to_parquet(args.out / "observation_windows.parquet", index=False)
    (args.out / "contexts.json").write_text(json.dumps(list(contexts.values()), indent=2) + "\n")
    jobs = json.loads((args.jobs_ledger or args.archive / "jobs.json").read_text())
    primary_paths = {j["relative_path"] for j in jobs}
    planned_windows = {j["window"]["id"] for j in jobs}
    availability_files = [args.archive / "availability.json"]
    if args.jobs_ledger is None:
        availability_files.append(args.archive / "high-water-supplement-availability.json")
    for availability_file in availability_files:
        if availability_file.exists():
            planned_windows.update(a["window"] for a in json.loads(availability_file.read_text()))
    additional = []
    missing = [
        w
        for key, w in sorted(windows.items())
        if key not in planned_windows and w["end"] >= "2013-04-01"
    ]
    if args.build_supplement:
        compact = script("96_acquire_limburg_compact_eo.py")
        records = []
        for source, collection in {
            "s1": compact.ARCHIVE.SOURCES["s1"][0],
            "s2_sr": compact.ARCHIVE.SOURCES["s2_sr"][0],
            **compact.HLS,
        }.items():
            for year in range(2013, 2026):
                file = args.archive / "catalogues" / f"{source}_{year}.json"
                if not file.exists():
                    file = ROOT / "data/raw/limburg_satellite_archive/catalogues" / file.name
                if not file.exists():
                    raise FileNotFoundError("Held catalogue absent: " + str(file))
                records.extend(
                    {"source": source, "collection": collection, **r}
                    for r in json.loads(file.read_text())
                )
        # Preserve exact tile domain of original acquisition; no spatial enlargement.
        tiles = {
            tuple(j["bounds"]): {"id": Path(j["relative_path"]).stem, "bounds": j["bounds"]}
            for j in jobs
        }
        additional, availability = compact.build_jobs(missing, records, list(tiles.values()))
        if primary_paths.intersection(j["relative_path"] for j in additional):
            raise ValueError("Supplement overlaps existing immutable jobs")
        (args.out / "supplement_jobs.json").write_text(json.dumps(additional) + "\n")
        (args.out / "supplement_availability.json").write_text(json.dumps(availability) + "\n")
        expanded = json.dumps(jobs + additional).encode() + b"\n"
        (args.out / "expanded_jobs.json").write_bytes(expanded)
        jobs += additional
    # Retain catalogue-empty vs not yet planned windows separately.
    catchments = gpd.read_file(ROOT / "data/interim/foundation_model_catchments.gpkg")
    catchments = catchments[catchments.experiment_role.ne("inventory")].to_crs(32632)
    if set(obs.catchment_gauge) - set(catchments.gauge):
        raise ValueError("Unmapped observation catchment")
    catchments.to_file(args.out / "catchments.gpkg", driver="GPKG")
    indexed = {}
    rows = []
    for j in jobs:
        indexed.setdefault((j["window"]["id"], j["product"]), []).append(j)
    records = []
    for j in jobs:
        path = args.archive / j["relative_path"]
        receipt = path.with_suffix(".receipt.json")
        status = (
            "local_receipt_present"
            if path.exists() and receipt.exists()
            else (
                "supplement_prepared"
                if j["relative_path"] not in primary_paths
                else "pending_local_or_cloud"
            )
        )
        rows.append(
            {
                "window_id": j["window"]["id"],
                "product": j["product"],
                "relative_path": j["relative_path"],
                "status": status,
            }
        )
    pd.DataFrame(rows).to_parquet(args.out / "tile_inventory.parquet", index=False)
    # A file being absent locally does not mean it is absent from Azure.
    for c in catchments.itertuples():
        for key in windows:
            for product in sorted({r[0] for r in ROUTES.values()}):
                relevant = [
                    j
                    for j in indexed.get((key, product), [])
                    if c.geometry.intersection(box(*j["bounds"])).area > 0
                ]
                local = 0
                companion_missing = 0
                for j in relevant:
                    path = args.archive / j["relative_path"]
                    ready = path.exists() and path.with_suffix(".receipt.json").exists()
                    if ready and product == "s2_10m":
                        companion = args.archive / str(
                            Path(j["relative_path"]).parent.parent
                            / "s2_20m"
                            / Path(j["relative_path"]).name
                        )
                        ready = (
                            companion.exists() and companion.with_suffix(".receipt.json").exists()
                        )
                        companion_missing += int(not ready)
                    local += int(ready)
                status = (
                    "local_files_ready_unverified_pixels"
                    if relevant and local == len(relevant)
                    else "partial_local"
                    if local
                    else "pending_local_or_cloud"
                    if relevant
                    else "pre_mission"
                    if windows[key]["end"] < "2013-04-01"
                    else "not_in_download_plan"
                    if key not in planned_windows and not args.build_supplement
                    else "no_catalogued_source_tiles"
                )
                records.append(
                    {
                        "catchment_gauge": c.gauge,
                        "window_id": key,
                        "product": product,
                        "catchment_area_m2": c.geometry.area,
                        "planned_source_tiles": len(relevant),
                        "local_tiles": local,
                        "local_companion_missing": companion_missing,
                        "status": status,
                    }
                )
    coverage = pd.DataFrame(records)
    coverage.to_parquet(args.out / "window_coverage.parquet", index=False)
    pixel_scan = (
        scan_local(jobs, catchments, args.archive, args.out, obs, links)
        if args.scan_local
        else None
    )
    counts = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "observations_by_cohort": obs.groupby("cohort").size().to_dict(),
        "scorable_by_cohort": obs.groupby("cohort").scoring_eligible.sum().astype(int).to_dict(),
        "pixel_scan": pixel_scan,
        "unique_contexts": len(contexts),
        "unique_windows": len(windows),
        "original_jobs": len(primary_paths),
        "additional_windows_considered": len(missing),
        "supplement_jobs": len(additional),
        "combined_jobs": len(jobs),
        "local_coverage_status": coverage.groupby("status").size().to_dict(),
        "limitations": [
            "Local-only inventory; cloud-only completed files are not errors.",
            "Scene/file availability does not establish valid-pixel or full-sequence coverage.",
            "Final comparisons wait for coverage checks; no outcomes scored here.",
        ],
    }
    inputs = [
        ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv",
        ROOT / "results/storm_response/storm_gauge_responses.parquet",
        ROOT / "data/interim/foundation_model_catchments.gpkg",
        args.jobs_ledger or args.archive / "jobs.json",
        args.archive / "plan.json",
    ]
    counts["input_sha256"] = {str(p.relative_to(ROOT)): sha256(p) for p in inputs}
    counts["git_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    (args.out / "manifest.json").write_text(json.dumps(counts, indent=2) + "\n")
    print(json.dumps(counts, indent=2))
    return int(bool(pixel_scan and pixel_scan["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
