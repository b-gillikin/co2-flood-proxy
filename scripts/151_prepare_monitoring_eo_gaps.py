#!/usr/bin/env python3
"""Inventory EO additions for causal rainfall clocks, without changing old runs."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_event_inputs import completed_windows, context_id

OUT = ROOT / "results/monitoring_acquisition_2026_10_28"
COMPACT = ROOT / "data/raw/limburg_compact_eo"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observed_qualification(rain, start, end):
    """First prefix-known 10mm; do not use eventual totals to time an issue."""
    cumulative = rain.loc[start:end].cumsum(skipna=False)
    crossed = cumulative.ge(10).any(axis=1)
    if not crossed.any():
        raise ValueError("Catalogue episode lacks prefix-known rainfall qualification")
    return cumulative.index[np.flatnonzero(crossed.to_numpy())[0]]


def supplemental_jobs(windows, records, tiles, expansion):
    """Same TOA and separate ascending-orbit routes already evaluated; no new model."""
    from pyproj import Transformer
    from shapely.geometry import box, shape
    from shapely.ops import transform

    allowed = {"s2_toa_10m", "s2_toa_20m", "s2_toa_qa60", "s1_ascending_15", "s1_ascending_161"}
    project = Transformer.from_crs(4326, 32632, always_xy=True).transform
    indexed = []
    for r in records:
        settings = [x for x in expansion.route(r) if x[0] in allowed]
        if not settings:
            continue
        props = r["properties"]
        asset = r["collection"] + "/" + props.get("system:index", r.get("id"))
        indexed.append(
            (
                props["system:time_start"],
                asset,
                props,
                r["source"],
                transform(project, shape(r["geometry"])),
                settings,
            )
        )
    jobs = []
    for w in windows:
        start, end = (pd.Timestamp(w[k]).timestamp() * 1000 for k in ["start", "end"])
        groups = defaultdict(list)
        for r in indexed:
            if start <= r[0] < end:
                for setting in r[5]:
                    groups[setting[0]].append((r, setting))
        for product, selected in groups.items():
            _, bands, resolution, dtype = selected[0][1]
            for tile in tiles:
                overlap = [
                    r for r, _ in selected if r[4].intersection(box(*tile["bounds"])).area > 0
                ]
                if not overlap:
                    continue
                jobs.append(
                    {
                        "source": overlap[0][3],
                        "product": product,
                        "bands": bands,
                        "resolution": resolution,
                        "dtype": dtype,
                        "window": w,
                        "bounds": tile["bounds"],
                        "asset_ids": [r[1] for r in overlap],
                        "acquisition_ms": [r[0] for r in overlap],
                        "source_metadata": [r[2] for r in overlap],
                        "relative_path": f"images/{w['id']}/{product}/{tile['id']}.tif",
                    }
                )
    return jobs


def main():
    import geopandas as gpd

    catalogue = load_script("92_build_storm_response_catalogue.py")
    acquisition = load_script("96_acquire_limburg_compact_eo.py")
    expansion = load_script("114_expand_limburg_eo_acquisition.py")
    OUT.mkdir(parents=True, exist_ok=True)
    rain_path = ROOT / "results/storm_response/hourly_rainfall.parquet"
    storms_path = ROOT / "results/storm_response/storm_gauge_responses.parquet"
    rain = pd.read_parquet(rain_path)
    original = pd.read_parquet(storms_path).drop_duplicates("storm_id")
    core = [c for c in rain if not c.startswith("282")]
    regional = catalogue.storm_catalogue(rain)
    rows, contexts = [], {}
    for label, storms, fields in [
        ("held_six_core_catalogue", original, core),
        ("eight_gauge_regional_candidate", regional, list(rain.columns)),
    ]:
        for row in storms.itertuples():
            cutoff = observed_qualification(rain[fields], row.start_utc, row.end_utc)
            record = {
                "calendar": label,
                "storm_id": row.storm_id,
                "start_utc": row.start_utc,
                "end_utc": row.end_utc,
                "old_six_hour_landmark": row.landmark_utc,
                "cutoff_utc": cutoff,
                "boundary_known": bool(row.boundary_known),
            }
            for kind in ["monthly_snapshot", "recent"]:
                sequence = completed_windows(cutoff, kind)
                key = context_id(kind, sequence)
                if any(pd.Timestamp(w["end"]) > cutoff for w in sequence):
                    raise ValueError("Future EO window attached to causal issue")
                contexts[key] = {"context_id": key, "kind": kind, "windows": sequence}
                record[kind + "_context_id"] = key
            rows.append(record)
    pd.DataFrame(rows).to_parquet(OUT / "rainfall_landmarks.parquet", index=False)
    (OUT / "contexts.json").write_text(json.dumps(list(contexts.values()), indent=2) + "\n")
    existing = json.loads((ROOT / "results/eo_comparison_preparation/contexts.json").read_text())
    existing_ids = {c["context_id"] for c in existing}
    existing_windows = {w["id"] for c in existing for w in c["windows"]}
    needed_windows = {w["id"]: w for c in contexts.values() for w in c["windows"]}
    new_windows = [w for k, w in needed_windows.items() if k not in existing_windows]
    # A new sequence may consist entirely of windows already downloaded for other events.
    geometry_path = ROOT / "data/interim/foundation_model_catchments.gpkg"
    frame = gpd.read_file(geometry_path)
    frame = frame.loc[frame.experiment_role.ne("inventory")].to_crs(32632)
    geometry = frame.geometry.union_all().buffer(320)
    tiles = list(acquisition.ARCHIVE.tiles_for_geometry(geometry))
    records, catalogue_paths = [], []
    sources = {"s1": "COPERNICUS/S1_GRD", "s2_sr": "COPERNICUS/S2_SR_HARMONIZED", **acquisition.HLS}
    for source, collection in sources.items():
        for p in sorted((COMPACT / "catalogues").glob(source + "_*.json")):
            catalogue_paths.append(p)
            records.extend(
                {"source": source, "collection": collection, **f} for f in json.loads(p.read_text())
            )
    jobs, availability = (
        acquisition.build_jobs(new_windows, records, tiles) if new_windows else ([], [])
    )
    more_records = [r for r in records if r["source"] == "s1"]
    for p in sorted((ROOT / "data/raw/limburg_satellite_archive/catalogues").glob("s2_toa_*.json")):
        catalogue_paths.append(p)
        more_records.extend(
            {"source": "s2_toa", "collection": "COPERNICUS/S2_HARMONIZED", **f}
            for f in json.loads(p.read_text())
        )
    additional_jobs = supplemental_jobs(new_windows, more_records, tiles, expansion)
    all_jobs = jobs + additional_jobs
    if len({j["relative_path"] for j in all_jobs}) != len(all_jobs):
        raise ValueError("Duplicate primary/supplemental export identities")
    manifest = {
        "status": "gap_inventory_prepared_no_model_extraction",
        "source_calendars": {
            "held_six_core_catalogue": len(original),
            "eight_gauge_regional_candidate": len(regional),
        },
        "calendar_note": "Eight-gauge catalogue is a versioned preparation candidate; regrouping changes storm identities, not simply 13 independent added storms. Old results untouched.",
        "contexts_needed": len(contexts),
        "contexts_already_indexed": sum(k in existing_ids for k in contexts),
        "new_sequence_contexts": sorted(set(contexts) - existing_ids),
        "windows_needed": len(needed_windows),
        "windows_already_indexed": len(set(needed_windows) & existing_windows),
        "new_windows": new_windows,
        "new_primary_jobs": len(jobs),
        "new_supplemental_jobs": len(additional_jobs),
        "total_new_jobs": len(all_jobs),
        "raw_tile_upper_bound_bytes": sum(acquisition.raw_bound(j) for j in all_jobs),
        "new_window_source_availability": availability,
        "input_sha256": {
            str(p.relative_to(ROOT)): acquisition.ARCHIVE.digest(p)
            for p in [
                rain_path,
                storms_path,
                geometry_path,
                Path(__file__),
                ROOT / "scripts/96_acquire_limburg_compact_eo.py",
                ROOT / "scripts/114_expand_limburg_eo_acquisition.py",
                *catalogue_paths,
            ]
        },
        "limits": "Known window/catalogue inventory, not pixel-valid or finite-embedding coverage. Reuse requires matching source/transform receipts. Clouds/pre-mission absence are not failed downloads.",
    }
    (OUT / "eo-gap-inventory.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "eo-new-window-jobs.json").write_text(json.dumps(all_jobs, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in [
                    "source_calendars",
                    "contexts_needed",
                    "contexts_already_indexed",
                    "windows_needed",
                    "windows_already_indexed",
                    "new_windows",
                    "new_primary_jobs",
                    "new_supplemental_jobs",
                    "total_new_jobs",
                    "raw_tile_upper_bound_bytes",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
