#!/usr/bin/env python3
"""Independently verify downloaded harmonized radar triplets and paired support."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/raw/limburg_applied_tasks/local_references/geoid-flood-heldout-tile-catalog.parquet"
P1 = ROOT / "data/processed/limburg_chapter_p1_inventory_v1/tile_inventory.json"
TRIPLETS = ROOT / "data/raw/limburg_chapter_ee_triplets_v1/tiles"
LABELS = ROOT / "data/raw/limburg_chapter_geoid_heldout_v1/extracted"
OUT = ROOT / "data/processed/limburg_chapter_triplet_audit_v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sensing(product: str) -> datetime:
    return datetime.strptime(product.split("_")[4], "%Y%m%dT%H%M%S")


def main() -> None:
    catalog = pd.read_parquet(CATALOG)
    inventory = json.loads(P1.read_text())
    if len(catalog) != 1301 or len(inventory) != 1301:
        raise ValueError("External cohort changed")
    rows = []
    for row, choice in zip(catalog.itertuples(), inventory, strict=True):
        if not choice["p1_catalogue_candidate"] or not (
            len(row.s1_pre_products) == len(choice["p1_products"]) == len(row.s1_post_products) == 1
        ):
            continue
        key = f"{row.event_id}-{row.tile_id}-{row.bbox_id}"
        products = {"p0": str(row.s1_pre_products[0]), "p1": str(choice["p1_products"][0]),
                    "post": str(row.s1_post_products[0])}
        if not sensing(products["p0"]) < sensing(products["p1"]) < datetime.fromisoformat(row.event_time) < sensing(products["post"]):
            raise ValueError(f"Invalid sensing chronology: {key}")
        tile = TRIPLETS / row.event_id / f"{key}.tif"
        if not tile.exists():
            rows.append({"key": key, "event_id": row.event_id, "status": "missing_ee_product"})
            continue
        receipt = json.loads(tile.with_suffix(".receipt.json").read_text())
        if receipt["products"] != products or receipt["bytes"] != tile.stat().st_size or receipt["sha256"] != sha256(tile):
            raise ValueError(f"Triplet receipt mismatch: {key}")
        label = LABELS / f"{row.event_id}-{row.tile_id}" / "label" / f"{key}_label.tif"
        with rasterio.open(label) as ref, rasterio.open(tile) as ds:
            if ds.count != 6 or (ds.shape, ds.transform, ds.crs) != (ref.shape, ref.transform, ref.crs):
                raise ValueError(f"Triplet/target grid mismatch: {key}")
            data = ds.read()
            valid_p0 = np.all(np.isfinite(data[[0, 1, 4, 5]]) & (data[[0, 1, 4, 5]] > 0), axis=0)
            valid_p1 = np.all(np.isfinite(data[[2, 3, 4, 5]]) & (data[[2, 3, 4, 5]] > 0), axis=0)
            support = valid_p0 & valid_p1 & (ref.read(1) != 255)
        rows.append({"key": key, "event_id": row.event_id, "status": "verified",
                     "bytes": tile.stat().st_size, "valid_p0_pixels": int(valid_p0.sum()),
                     "valid_p1_pixels": int(valid_p1.sum()), "common_labeled_pixels": int(support.sum()),
                     "sha256": receipt["sha256"]})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(OUT / "tile_status.parquet", index=False)
    summary = {"single_product_metadata_candidates": len(rows),
               "statuses": dict(Counter(x["status"] for x in rows)),
               "events_verified": dict(Counter(x["event_id"] for x in rows if x["status"] == "verified")),
               "verified_bytes": sum(x.get("bytes", 0) for x in rows),
               "common_labeled_pixels": sum(x.get("common_labeled_pixels", 0) for x in rows),
               "min_common_labeled_pixels": min(x["common_labeled_pixels"] for x in rows if x["status"] == "verified"),
               "note": "Every retained triplet independently SHA-256 checked, grid matched and positive finite common pixel support counted."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
