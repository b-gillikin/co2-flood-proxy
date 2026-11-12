#!/usr/bin/env python3
"""Acquire bounded EMSR497 SAR pairs for regional adaptation preparation.

No labels are inferred or model fitted. Candidate products come from the held
catalogue; actual assets, geometry, masks and download hashes are recorded.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import ee
import numpy as np
import pandas as pd
import rasterio
import requests
from pyproj import Transformer
from shapely import from_wkb, intersects
from shapely.geometry import box
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import atomic_json, sha256

OUT = ROOT / "data/raw/limburg_response_mapping_sources_v1/EMSR497_sar"
COLLECTION = "COPERNICUS/S1_GRD_FLOAT"


def resolve(product, geometry):
    cache = OUT / "asset_metadata" / f"{product}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    prefix = product.removesuffix("_COG").rsplit("_", 1)[0]
    date = datetime.strptime(prefix.split("_")[4][:8], "%Y%m%d")
    point = from_wkb(geometry).representative_point()
    collection = (
        ee.ImageCollection(COLLECTION)
        .filterDate(date.strftime("%Y-%m-%d"), (date + timedelta(days=1)).strftime("%Y-%m-%d"))
        .filterBounds(ee.Geometry.Point([point.x, point.y]))
    )
    matches = [
        s
        for s in collection.aggregate_array("system:index").getInfo()
        if s.startswith(prefix + "_")
    ]
    if len(matches) != 1:
        result = dict(product=product, status="unavailable_in_selected_collection", matches=matches)
    else:
        asset = COLLECTION + "/" + matches[0]
        props = (
            ee.Image(asset)
            .toDictionary(
                [
                    "relativeOrbitNumber_start",
                    "orbitProperties_pass",
                    "instrumentMode",
                    "transmitterReceiverPolarisation",
                    "platform_number",
                    "system:time_start",
                ]
            )
            .getInfo()
        )
        result = dict(product=product, status="resolved", asset=asset, properties=props)
    atomic_json(cache, result)
    return result


def acquire(row, assets):
    key = f"{row.event_id}-{row.tile_id}-{row.bbox_id}"
    path = OUT / "tiles" / f"{key}.tif"
    receipt = path.with_suffix(".receipt.json")
    if receipt.exists() and path.exists():
        record = json.loads(receipt.read_text())
        if sha256(path) == record["sha256"]:
            return record
        raise ValueError("Existing regional raster changed")
    if shutil.disk_usage(ROOT).free < 52 * 1024**3:
        raise RuntimeError("52GiB acquisition reserve reached")
    bounds = transform(
        Transformer.from_crs(4326, row.utm_crs, always_xy=True).transform, from_wkb(row.geometry)
    ).bounds
    xmin, ymin, xmax, ymax = [round(v / 10) * 10 for v in bounds]
    width, height = round((xmax - xmin) / 10), round((ymax - ymin) / 10)
    if (width, height) != (1024, 1024):
        raise ValueError(f"Unexpected regional grid: {key} {width}x{height}")
    roles = {"pre": list(row.s1_pre_products), "post": list(row.s1_post_products)}
    available = {
        role: [assets[p] for p in products if assets[p]["status"] == "resolved"]
        for role, products in roles.items()
    }
    if not all(available.values()):
        return dict(key=key, status="no_available_pre_or_post", requested_products=roles)
    traits = {
        (
            a["properties"].get("relativeOrbitNumber_start"),
            a["properties"].get("orbitProperties_pass"),
            a["properties"].get("instrumentMode"),
            tuple(sorted(a["properties"].get("transmitterReceiverPolarisation", []))),
        )
        for values in available.values()
        for a in values
    }
    if len(traits) != 1:
        return dict(key=key, status="incompatible_geometry", requested_products=roles)
    images = []
    for role in ("pre", "post"):
        # Deterministic same-track mosaics of available listed source slices.
        image = ee.ImageCollection.fromImages(
            [
                ee.Image(a["asset"]).select(["VV", "VH"])
                for a in sorted(available[role], key=lambda v: v["asset"])
            ]
        ).mosaic()
        images.append(image.rename([role + "_vv", role + "_vh"]))
    stack = ee.Image.cat(images).toFloat()
    grid = dict(
        crs=row.utm_crs,
        crs_transform=[10, 0, xmin, 0, -10, ymax],
        dimensions=[width, height],
        format="GEO_TIFF",
    )
    for attempt in range(3):
        try:
            response = requests.get(stack.getDownloadURL(dict(grid)), timeout=180)
            response.raise_for_status()
            partial = path.with_suffix(".partial.tif")
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(response.content)
            with rasterio.open(partial) as ds:
                if ds.count != 4 or ds.shape != (height, width) or str(ds.crs) != row.utm_crs:
                    raise ValueError("Regional grid/band contract")
                data = ds.read()
                valid = np.isfinite(data).all(axis=0) & (data > 0).all(axis=0)
            partial.replace(path)
            record = dict(
                key=key,
                status="downloaded_verified",
                bytes=path.stat().st_size,
                sha256=sha256(path),
                grid=grid,
                requested_products=roles,
                actual_assets={role: [a["asset"] for a in v] for role, v in available.items()},
                unavailable_requested_products=[
                    p
                    for values in roles.values()
                    for p in values
                    if assets[p]["status"] != "resolved"
                ],
                valid_joint_pixels=int(valid.sum()),
                total_pixels=height * width,
                label_status="Reference vector acquired separately; not rasterized or validated here",
                processing=COLLECTION,
            )
            atomic_json(receipt, record)
            return record
        except (requests.RequestException, OSError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ee.Initialize(project="limburg-511403")
    catalogue = (
        ROOT / "data/raw/limburg_applied_tasks/local_references/geoid-flood-tile-catalog.parquet"
    )
    frame = pd.read_parquet(catalogue)
    # Fixed regional receiving footprint; do not expand geography based on scores.
    frame = frame.loc[
        (frame.event_id == "EMSR497")
        & intersects(from_wkb(frame.geometry.values), box(5.25, 50.45, 6.8, 51.65))
    ]
    representatives = {}
    for row in frame.itertuples():
        for p in list(row.s1_pre_products) + list(row.s1_post_products):
            representatives.setdefault(p, row.geometry)
    assets = {p: resolve(p, g) for p, g in representatives.items()}
    atomic_json(OUT / "assets.json", assets)
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(acquire, row, assets): row for row in frame.itertuples()}
        for future in as_completed(futures):
            row = futures[future]
            try:
                record = future.result()
            except Exception as e:
                record = dict(
                    key=f"{row.event_id}-{row.tile_id}-{row.bbox_id}", status="failed", error=str(e)
                )
            results.append(record)
            atomic_json(
                OUT / "progress.json",
                dict(total=len(frame), completed=len(results), results=results),
            )
            print(
                json.dumps(
                    {k: v for k, v in record.items() if k in ["key", "status", "bytes", "error"]}
                ),
                flush=True,
            )
    atomic_json(
        OUT / "acquisition.json",
        dict(
            date="2026-11-12",
            catalogue_sha256=sha256(catalogue),
            runner_sha256=sha256(Path(__file__)),
            regional_bbox=[5.25, 50.45, 6.8, 51.65],
            total=len(frame),
            results=results,
        ),
    )
    return int(any(r["status"] != "downloaded_verified" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
