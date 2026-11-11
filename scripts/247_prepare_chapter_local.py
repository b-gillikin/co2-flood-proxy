#!/usr/bin/env python3
"""Inventory and obtain same-chain local P0/P1/post inputs without scoring labels."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PROJ_DATA", "/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj")
sys.path.insert(0, str(ROOT / "src"))

import ee
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.warp import transform_bounds
from shapely.geometry import box, shape, Polygon

from limburg_chapter_evaluation import atomic_json, sha256

OUT = ROOT / "data/raw/limburg_chapter_local_triplets_v1"
BASE = ROOT / "data/raw/limburg_applied_tasks/local_scenes"
FRAME = ROOT / "results/applied_study_v1/local_references/scoring/scene-reference-pairs.parquet"
INVENTORY = ROOT / "results/applied_study_v1/local_references/local-scene-inventory.json"
COLLECTION = "COPERNICUS/S1_GRD_FLOAT"
CUTOFF = "2021-07-13T00:00:00Z"


def scene_time(scene):
    return datetime.strptime(scene.split("_")[4], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)


def candidates(aoi, region, pre_scene, orbit, direction):
    cache = OUT / "catalogue" / f"{aoi}-{pre_scene}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    coll = (ee.ImageCollection(COLLECTION).filterBounds(ee.Geometry(region))
            .filterDate(scene_time(pre_scene).isoformat(), CUTOFF)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.eq("platform_number", pre_scene[2]))
            .filter(ee.Filter.eq("relativeOrbitNumber_start", int(orbit)))
            .filter(ee.Filter.eq("orbitProperties_pass", direction))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))
    records = coll.map(lambda image: ee.Feature(None, image.toDictionary(
        ["system:time_start", "system:footprint"])).set("scene_id", image.get("system:index"))).getInfo()["features"]
    rows = [entry["properties"] for entry in records]
    atomic_json(cache, rows)
    return rows


def jobs():
    inventory = {row["aoi"]: row for row in json.loads(INVENTORY.read_text())["aois"]}
    frame = pd.read_parquet(FRAME)
    frame["time"] = pd.to_datetime(frame.acquisition_utc, utc=True, format="ISO8601")
    frame["grid"] = frame.path.map(lambda value: Path(value).stem)
    rows = []
    for event in frame.loc[frame.sensor == "s1_event"].sort_values("path").itertuples():
        pre = frame.loc[(frame.aoi == event.aoi) & (frame.grid == event.grid)
                        & (frame.sensor == "s1_pre") & (frame.relative_orbit == event.relative_orbit)
                        & (frame.orbit_pass == event.orbit_pass) & (frame.time < pd.Timestamp(CUTOFF))
                        & (frame.time < event.time)]
        if pre.empty:
            rows.append({"aoi": event.aoi, "post_path": event.path, "status": "no_held_compatible_p0"})
            continue
        baseline = pre.sort_values(["time", "path"]).iloc[-1]
        with rasterio.open(BASE / event.path) as ds:
            dimensions = [ds.width, ds.height]
            affine, crs = list(ds.transform)[:6], str(ds.crs)
            footprint = box(*transform_bounds(ds.crs, "EPSG:4326", *ds.bounds, densify_pts=21))
        relevant = footprint.intersection(shape(inventory[event.aoi]["geometry"]))
        choices = candidates(event.aoi, inventory[event.aoi]["geometry"], baseline.scene,
                             event.relative_orbit, event.orbit_pass)
        newer = []
        for candidate in choices:
            if scene_time(candidate["scene_id"]) <= scene_time(baseline.scene):
                continue
            geometry = shape(candidate["system:footprint"])
            if geometry.geom_type == "LinearRing":
                geometry = Polygon(geometry)
            if geometry.buffer(1e-8).covers(relevant):
                newer.append(candidate)
        chosen = max(newer, key=lambda row: (row["system:time_start"], row["scene_id"]))["scene_id"] if newer else baseline.scene
        key = f"{event.aoi}__{event.scene}__{event.grid}"
        rows.append({"key": key, "aoi": event.aoi, "grid": event.grid, "status": "prepared",
                     "post_path": event.path, "held_pre_path": baseline.path,
                     "held_pre_sha256": sha256(BASE / baseline.path), "held_post_sha256": sha256(BASE / event.path),
                     "reference_path": event.reference_path, "reference_sha256": sha256(ROOT / event.reference_path),
                     "reference_offset_hours": float(event.reference_offset_hours),
                     "reference_dependence": event.reference_dependence,
                     "products": {"p0": baseline.scene, "p1": chosen, "post": event.scene},
                     "updated": chosen != baseline.scene, "crs": crs, "transform": affine,
                     "dimensions": dimensions, "aoi_geometry": inventory[event.aoi]["geometry"]})
    return rows


def download(job):
    target = OUT / "tiles" / job["aoi"] / f"{job['key']}.tif"
    receipt = target.with_suffix(".receipt.json")
    if target.exists() and receipt.exists():
        old = json.loads(receipt.read_text())
        if old["job"] == job and old["sha256"] == sha256(target):
            return {"key": job["key"], "status": "verified", "updated": job["updated"]}
        raise ValueError("Existing local triplet or provenance changed")
    if shutil.disk_usage(ROOT).free < 52 * 1024**3:
        raise RuntimeError("Local triplet download approached disk reserve")
    images = [ee.Image(f"{COLLECTION}/{job['products'][role]}").select(["VV", "VH"]).rename([f"{role}_vv", f"{role}_vh"])
              for role in ("p0", "p1", "post")]
    image = ee.Image.cat(images).clip(ee.Geometry(job["aoi_geometry"])).unmask(0).toFloat()
    parameters = {"bands": [f"{role}_{pol}" for role in ("p0", "p1", "post") for pol in ("vv", "vh")],
                  "crs": job["crs"], "crs_transform": job["transform"],
                  "dimensions": job["dimensions"], "format": "GEO_TIFF"}
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial.tif")
    for attempt in range(1, 4):
        try:
            url = image.getDownloadURL(parameters)
            with requests.get(url, stream=True, timeout=(30, 240)) as response:
                response.raise_for_status()
                with partial.open("wb") as stream:
                    for block in response.iter_content(1024*1024):
                        stream.write(block)
            with rasterio.open(partial) as ds:
                if ds.count != 6 or [ds.width, ds.height] != job["dimensions"] or str(ds.crs) != job["crs"] or not np.allclose(list(ds.transform)[:6], job["transform"]):
                    raise ValueError("Local triplet grid/channel mismatch")
            partial.replace(target)
            atomic_json(receipt, {"job": job, "collection": COLLECTION, "sha256": sha256(target), "bytes": target.stat().st_size})
            return {"key": job["key"], "status": "verified", "updated": job["updated"]}
        except Exception:
            partial.unlink(missing_ok=True)
            if attempt == 3:
                raise
            time.sleep(5)


def main():
    ee.Initialize(project="limburg-511403")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "inventory.json"
    if path.exists():
        inventory = json.loads(path.read_text())
        if inventory["frame_sha256"] != sha256(FRAME) or inventory["source_inventory_sha256"] != sha256(INVENTORY):
            raise ValueError("Local source inventory changed")
        rows = inventory["jobs"]
    else:
        rows = jobs()
        atomic_json(path, {"jobs": rows, "frame_sha256": sha256(FRAME), "source_inventory_sha256": sha256(INVENTORY),
                          "conservative_pre_event_cutoff": CUTOFF,
                          "p0": "latest held preceding same-grid/orbit/pass reference; not GEOID delivered imagery",
                          "p1": "latest newer same-platform/orbit/pass full relevant-footprint scene before cutoff; otherwise P1=P0",
                          "case_role": "previously inspected July 2021 receiving cases; one dependent flood episode"})
    prepared = [row for row in rows if row["status"] == "prepared"]
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(download, row) for row in prepared]
        for future in as_completed(futures):
            results.append(future.result())
            if len(results) % 10 == 0 or len(results) == len(prepared):
                print(json.dumps({"verified": len(results), "total": len(prepared)}), flush=True)
    atomic_json(OUT / "complete.json", {"status": "local_triplets_complete", "held_post_grid_records": len(rows),
                "verified": len(prepared), "updated": sum(row["updated"] for row in prepared),
                "unavailable": len(rows)-len(prepared), "inventory_sha256": sha256(path)})


if __name__ == "__main__":
    main()
