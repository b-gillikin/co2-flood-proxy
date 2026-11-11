#!/usr/bin/env python3
"""Audit the pinned external flood cohort without altering imagery or labels."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import tarfile

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/limburg_chapter_geoid_heldout_v1"
CATALOG = ROOT / "data/raw/limburg_applied_tasks/local_references/geoid-flood-heldout-tile-catalog.parquet"
PIN = ROOT / "config/limburg_chapter_sized_geoid_acquisition_v1.json"
OUT = ROOT / "data/processed/limburg_chapter_geoid_audit_v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    pinned = json.loads(PIN.read_text())["shards"]
    checked = []
    for item in pinned:
        path = DATA / item["path"]
        if not path.exists() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Unverified shard: {path}")
        checked.append({"path": item["path"], "bytes": item["bytes"], "sha256": item["sha256"]})
    tar_members = defaultdict(dict)
    for item in pinned:
        if "/s1grd/" not in item["path"]:
            continue
        archive = DATA / item["path"]
        with tarfile.open(archive) as tar:
            for member in tar:
                if member.isfile() and member.name.endswith(".tif"):
                    stem = member.name.split("/")[-1].split("_s1grd_")[0]
                    role = "pre" if "_s1grd_pre_" in member.name else "post" if "_s1grd_post_" in member.name else None
                    if role:
                        if role in tar_members[stem]:
                            raise ValueError(f"Duplicate {role} radar file for {stem}")
                        tar_members[stem][role] = f"/vsitar/{archive}/{member.name}"
    frame = pd.read_parquet(CATALOG)
    p1 = json.loads((ROOT / "data/processed/limburg_chapter_p1_inventory_v1/tile_inventory.json").read_text())
    if len(frame) != 1301 or len(p1) != len(frame):
        raise ValueError("Cohort inventory mismatch")
    p1_lookup = {(r["event_id"], str(r["tile_id"]), str(r["bbox_id"])): r for r in p1}
    rows = []
    for row in frame.itertuples():
        area = f"{row.event_id}-{row.tile_id}"
        stem = f"{area}-{row.bbox_id}"
        records = tar_members.get(stem, {})
        if set(records) != {"pre", "post"}:
            raise ValueError(f"Missing pre/post radar: {stem}")
        ref = None
        arrays = {}
        for role in ("label", "floodmask", "permwater", "validity"):
            path = DATA / "extracted" / area / role / f"{stem}_{role}.tif"
            if not path.exists():
                raise ValueError(f"Missing extracted {role}: {path}")
            with rasterio.open(path) as ds:
                info = (ds.shape, ds.transform, ds.crs)
                if ref is not None and info != ref:
                    raise ValueError(f"Label/mask grid mismatch: {stem}/{role}")
                ref = info
                arrays[role] = ds.read(1)
        for role in ("pre", "post"):
            with rasterio.open(records[role]) as ds:
                if (ds.shape, ds.transform, ds.crs) != ref or ds.count != 2:
                    raise ValueError(f"Radar/label grid or channel mismatch: {stem}/{role}")
                if not ds.tags().get("SOURCE_PRODUCTS"):
                    raise ValueError(f"Missing radar product provenance: {stem}/{role}")
        label, flood, perm, valid = (arrays[x] for x in ("label", "floodmask", "permwater", "validity"))
        classes = set(np.unique(label).tolist())
        if not classes <= {0, 1, 2, 255}:
            raise ValueError(f"Unexpected label classes: {stem}: {classes}")
        if not set(np.unique(valid).tolist()) <= {0, 1}:
            raise ValueError(f"Unexpected validity mask: {stem}")
        key = (row.event_id, str(row.tile_id), str(row.bbox_id))
        candidate = p1_lookup[key]
        rows.append({
            "event_id": row.event_id, "tile_id": str(row.tile_id), "bbox_id": str(row.bbox_id),
            "label_valid_pixels": int(np.count_nonzero(label != 255)),
            "flood_pixels": int(np.count_nonzero(label == 2)),
            "permanent_water_pixels": int(np.count_nonzero(label == 1)),
            "mask_valid_pixels": int(np.count_nonzero(valid == 1)),
            "floodmask_disagreement_pixels": int(np.count_nonzero(((label == 2) != (flood == 1)) & (label != 255))),
            "permwater_disagreement_pixels": int(np.count_nonzero(((label == 1) != (perm == 1)) & (label != 255))),
            "p1_metadata_candidate": candidate["p1_catalogue_candidate"],
            "p0_mixed_orbit_pass": not candidate["baseline_traits_consistent"],
            "pre_vsi": records["pre"], "post_vsi": records["post"],
        })
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(OUT / "tile_audit.parquet", index=False)
    summary = {
        "tiles": len(rows), "events": dict(Counter(x["event_id"] for x in rows)),
        "verified_shards": checked,
        "p1_metadata_candidates": sum(x["p1_metadata_candidate"] for x in rows),
        "p0_mixed_orbit_pass_tiles": sum(x["p0_mixed_orbit_pass"] for x in rows),
        "floodmask_disagreement_tiles": sum(x["floodmask_disagreement_pixels"] > 0 for x in rows),
        "permwater_disagreement_tiles": sum(x["permwater_disagreement_pixels"] > 0 for x in rows),
        "no_flood_label_tiles": sum(x["flood_pixels"] == 0 for x in rows),
        "total_valid_label_pixels": sum(x["label_valid_pixels"] for x in rows),
        "total_flood_label_pixels": sum(x["flood_pixels"] for x in rows),
        "note": "Mask disagreements retained; label TIFF is target, masks are provenance diagnostics only.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
