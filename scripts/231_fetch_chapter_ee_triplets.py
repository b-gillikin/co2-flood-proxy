#!/usr/bin/env python3
"""Fetch harmonized P0/P1/post SAR triplets on the released GEOID native grid.

Only catalogue-selected, single-product scenes are eligible. Earth Engine
processes all three dates through COPERNICUS/S1_GRD_FLOAT. No target labels or
performance enter selection. Downloads are resumable and grid-checked.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import time

import ee
import pandas as pd
import rasterio
import requests
from shapely import wkb

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/raw/limburg_applied_tasks/local_references/geoid-flood-heldout-tile-catalog.parquet"
P1 = ROOT / "data/processed/limburg_chapter_p1_inventory_v1/tile_inventory.json"
LABEL = ROOT / "data/raw/limburg_chapter_geoid_heldout_v1/extracted"
OUT = ROOT / "data/raw/limburg_chapter_ee_triplets_v1"
COLLECTION = "COPERNICUS/S1_GRD_FLOAT"


def key(row) -> str:
    return f"{row.event_id}-{row.tile_id}-{row.bbox_id}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cohort() -> list[dict]:
    frame = pd.read_parquet(CATALOG)
    inventory = json.loads(P1.read_text())
    if len(frame) != len(inventory) or len(frame) != 1301:
        raise ValueError("Pinned cohort mismatch")
    chosen = []
    for row, entry in zip(frame.itertuples(), inventory, strict=True):
        if (row.event_id, str(row.tile_id), str(row.bbox_id)) != (
            entry["event_id"], str(entry["tile_id"]), str(entry["bbox_id"])
        ):
            raise ValueError("P1 inventory row alignment changed")
        if not entry["p1_catalogue_candidate"]:
            continue
        if not (len(row.s1_pre_products) == len(entry["p1_products"]) == len(row.s1_post_products) == 1):
            continue
        chosen.append({
            "key": key(row), "event_id": row.event_id, "tile_id": str(row.tile_id),
            "bbox_id": str(row.bbox_id), "geometry": row.geometry,
            "products": {
                "p0": str(row.s1_pre_products[0]), "p1": str(entry["p1_products"][0]),
                "post": str(row.s1_post_products[0]),
            },
        })
    return chosen


def resolve_product(product: str, geometry) -> str:
    """Match a CDSE COG product to EE's counterpart without relying on the final hash."""
    prefix = product.removesuffix("_COG").rsplit("_", 1)[0]
    day = datetime.strptime(prefix.split("_")[4][:8], "%Y%m%d")
    point = wkb.loads(geometry).representative_point()
    coll = (ee.ImageCollection(COLLECTION)
            .filterDate(day.strftime("%Y-%m-%d"), (day + timedelta(days=1)).strftime("%Y-%m-%d"))
            .filterBounds(ee.Geometry.Point([point.x, point.y])))
    matches = [x for x in coll.aggregate_array("system:index").getInfo() if x.startswith(prefix + "_")]
    if len(matches) != 1:
        raise ValueError(f"Expected one EE scene for {product}, found {len(matches)}")
    return COLLECTION + "/" + matches[0]


def map_assets(rows: list[dict], output: Path, workers: int) -> dict:
    path = output / "asset_map.json"
    failures = output / "asset_map_failures.jsonl"
    mapping = json.loads(path.read_text()) if path.exists() else {}
    representatives = {}
    for row in rows:
        for product in row["products"].values():
            representatives.setdefault(product, row["geometry"])
    todo = [(product, geom) for product, geom in representatives.items() if product not in mapping]
    for start in range(0, len(todo), workers):
        group = todo[start : start + workers]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(resolve_product, product, geom): product for product, geom in group}
            for future in as_completed(futures):
                product = futures[future]
                try:
                    mapping[product] = future.result()
                except Exception as exc:
                    with failures.open("a") as stream:
                        stream.write(json.dumps({"product": product, "error": f"{type(exc).__name__}: {exc}"}) + "\n")
                    continue
                temp = path.with_suffix(".partial")
                temp.write_text(json.dumps(mapping, indent=2) + "\n")
                temp.replace(path)
        print(f"mapped {len(mapping)}/{len(representatives)} distinct products", flush=True)
    return mapping


def download_one(row: dict, mapping: dict, output: Path, reserve_gib: int) -> dict:
    target = output / "tiles" / row["event_id"] / f"{row['key']}.tif"
    receipt = target.with_suffix(".receipt.json")
    label = LABEL / f"{row['event_id']}-{row['tile_id']}" / "label" / f"{row['key']}_label.tif"
    target.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(label) as ref:
        expected = (ref.shape, ref.transform, ref.crs)
        params = {
            "bands": ["p0_vv", "p0_vh", "p1_vv", "p1_vh", "post_vv", "post_vh"],
            "crs": ref.crs.to_string(), "crs_transform": list(ref.transform)[:6],
            "dimensions": [ref.width, ref.height], "format": "GEO_TIFF",
        }
    if target.exists() and receipt.exists():
        old = json.loads(receipt.read_text())
        if old.get("sha256") == sha256(target) and old.get("products") == row["products"]:
            with rasterio.open(target) as ds:
                if (ds.shape, ds.transform, ds.crs) == expected and ds.count == 6:
                    return {"key": row["key"], "status": "reused_verified"}
    if shutil.disk_usage(output).free < (reserve_gib + 0.05) * 1024**3:
        raise RuntimeError("50 GiB disk reserve approached; stop before another tile")
    images = [
        ee.Image(mapping[row["products"][role]]).select(["VV", "VH"]).rename([role + "_vv", role + "_vh"])
        for role in ("p0", "p1", "post")
    ]
    image = ee.Image.cat(images)
    last_error = None
    for attempt in range(5):
        try:
            url = image.getDownloadURL(json.loads(json.dumps(params)))
            response = requests.get(url, timeout=180)
            response.raise_for_status()
            partial = target.with_suffix(".partial")
            partial.write_bytes(response.content)
            with rasterio.open(partial) as ds:
                if (ds.shape, ds.transform, ds.crs) != expected or ds.count != 6:
                    raise ValueError(f"Native grid or six-band contract failed for {row['key']}")
            partial.replace(target)
            record = {
                "key": row["key"], "products": row["products"],
                "ee_assets": {role: mapping[p] for role, p in row["products"].items()},
                "sha256": sha256(target), "bytes": target.stat().st_size,
                "collection": COLLECTION, "grid": params, "verified_unix": time.time(),
            }
            tmp = receipt.with_suffix(".partial")
            tmp.write_text(json.dumps(record, indent=2) + "\n")
            tmp.replace(receipt)
            return {"key": row["key"], "status": "downloaded_verified", "bytes": record["bytes"]}
        except (requests.RequestException, ee.EEException, ValueError) as exc:
            last_error = exc
            time.sleep(min(3 * 2**attempt, 30))
    raise RuntimeError(f"Failed {row['key']} after five attempts: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="limburg-511403")
    parser.add_argument("--mode", choices=["map", "download"], required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--reserve-gib", type=int, default=50)
    args = parser.parse_args()
    if not 1 <= args.workers <= 3:
        parser.error("Use one to three EE workers")
    ee.Initialize(project=args.project)
    rows = cohort()
    if args.limit is not None:
        rows = rows[: args.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    mapping = map_assets(rows, OUT, args.workers)
    if args.mode == "map":
        print(f"Mapped {len(mapping)} source products for {len(rows)} eligible tiles")
        return
    rows = [row for row in rows if all(product in mapping for product in row["products"].values())]
    completed = 0
    failures = OUT / "download_failures.jsonl"
    for start in range(0, len(rows), args.workers):
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(download_one, row, mapping, OUT, args.reserve_gib): row for row in rows[start:start+args.workers]}
            for future in as_completed(futures):
                row = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"key": row["key"], "status": "failed", "error": f"{type(exc).__name__}: {exc}"}
                    with failures.open("a") as stream:
                        stream.write(json.dumps(result) + "\n")
                    if "disk reserve" in result["error"]:
                        raise RuntimeError(result["error"]) from exc
                completed += 1
                print(json.dumps({"completed": completed, "total": len(rows), **result}), flush=True)


if __name__ == "__main__":
    main()
