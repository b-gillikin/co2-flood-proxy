#!/usr/bin/env python3
"""Check completed maps and freeze label-blind native overlap/support ownership."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import binary_erosion
from shapely import STRtree, from_wkb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import BITS, OUT, atomic_json, remove_prior_coverage, sha256


def physical_valid(key, dataset, reference, calibration):
    event = key.split("-")[0]
    base = ROOT / "results/limburg_chapter_sized_v1/physical_external"
    receipt = json.loads((base / f"receipts/{dataset}/{event}/{key}-{reference}.json").read_text())
    path = base / f"maps/{dataset}/{event}/{key}-{reference}.npz"
    if receipt["output_sha256"] != sha256(path) or receipt["calibration_sha256"] != calibration:
        raise ValueError(f"Changed physical output/calibration: {key}")
    with np.load(path) as data:
        return data["radar_valid"]


def main():
    contract = ROOT / "config/limburg_chapter_evaluation_v1.json"
    fit_module = __import__("importlib.util", fromlist=["util"])
    spec = fit_module.spec_from_file_location(
        "source_queue", ROOT / "scripts/236_run_chapter_final_queue.py"
    )
    source = fit_module.module_from_spec(spec)
    spec.loader.exec_module(source)
    if not all(source.completed(kind, seed) for kind, seed in source.JOBS):
        raise ValueError("Final source fits are not verified complete")
    external = ROOT / "results/limburg_chapter_sized_v1/external"
    for kind in ("unet", "native"):
        complete = json.loads((external / f"{kind}-complete.json").read_text())
        if complete["jobs"] != 2214 or complete["status"] != "full_external_predictions_complete":
            raise ValueError(f"Incomplete mapping census: {kind}")
        for seed in (42, 1729, 31415):
            if complete["checkpoints"][str(seed)] != sha256(
                ROOT / f"results/limburg_chapter_sized_v1/final_source/{kind}-{seed}/model.pt"
            ):
                raise ValueError("Mapping/final-checkpoint mismatch")
    archived = {}
    for ledger in (external / "archives").glob("*.json"):
        record = json.loads(ledger.read_text())
        if record["status"] != "remote_readback_verified":
            raise ValueError("Unverified archive ledger")
        for name, digest in record["members"].items():
            if name in archived:
                raise ValueError(f"Duplicate archived output: {name}")
            archived[name] = digest
    receipts = list((external / "receipts").rglob("*.json"))
    if len(receipts) != 4428 or len(archived) != 18762:
        raise ValueError("Prediction/receipt census differs")
    for path in receipts:
        for name, digest in json.loads(path.read_text())["files"].items():
            if archived.get(name) != digest:
                raise ValueError(f"Output missing from verified archive: {name}")
    calibration = sha256(ROOT / "results/limburg_chapter_sized_v1/physical/calibration.json")
    catalogue_path = (
        ROOT
        / "data/raw/limburg_applied_tasks/local_references/geoid-flood-heldout-tile-catalog.parquet"
    )
    metadata_path = (
        ROOT / "docs/reviews/limburg-chapter-scope-audit-2026-11-10/external-metadata.csv"
    )
    catalogue = pd.read_parquet(catalogue_path)
    catalogue["key"] = catalogue.event_id + "-" + catalogue.tile_id + "-" + catalogue.bbox_id
    metadata = pd.read_csv(metadata_path, dtype={"tile": str, "bbox_id": str})
    metadata["key"] = metadata.event + "-" + metadata.tile + "-" + metadata.bbox_id
    frame = catalogue.merge(
        metadata[["key", "post_label_offset_days", "source_bbox_intersection"]],
        on="key",
        validate="one_to_one",
    )
    pairs = pd.read_parquet(
        ROOT / "data/processed/limburg_chapter_triplet_audit_v1/tile_status.parquet"
    )
    paired_keys = set(pairs.loc[pairs.status == "verified", "key"])
    out = OUT / "support"
    (out / "tiles").mkdir(parents=True, exist_ok=True)
    manifest = {
        "evaluation_contract_sha256": sha256(contract),
        "catalogue_sha256": sha256(catalogue_path),
        "metadata_sha256": sha256(metadata_path),
        "calibration_sha256": calibration,
        "preparer_sha256": sha256(Path(__file__)),
        "code_sha256": sha256(ROOT / "src/limburg_chapter_evaluation.py"),
    }
    atomic_json(out / "manifest.json", manifest)
    rows = []
    for event, group in frame.groupby("event_id", sort=True):
        group = (
            group.assign(priority=group.post_label_offset_days.abs())
            .sort_values(["priority", "key"])
            .reset_index(drop=True)
        )
        geometries = from_wkb(group.geometry.to_numpy())
        tree = STRtree(geometries)
        previous = {}
        for index, row in enumerate(group.itertuples()):
            base = (
                ROOT / f"data/raw/limburg_chapter_geoid_heldout_v1/extracted/{event}-{row.tile_id}"
            )
            arrays = {}
            for role in ("label", "floodmask", "permwater", "validity"):
                with rasterio.open(base / role / f"{row.key}_{role}.tif") as ds:
                    arrays[role] = ds.read(1)
                    transform, crs = ds.transform, ds.crs
            if not np.allclose(
                [transform.a, transform.e, transform.b, transform.d], [10, -10, 0, 0], atol=1e-7
            ):
                raise ValueError("Expected axis-aligned 10-m native grid")
            label = arrays["label"]
            if not set(np.unique(arrays["floodmask"])) <= {0, 1, 255} or not set(
                np.unique(arrays["permwater"])
            ) <= {0, 1, 255}:
                raise ValueError("Unexpected source-mask classes")
            radar = physical_valid(row.key, "delivered", "p0", calibration).astype(np.uint8)
            if row.key in paired_keys:
                p0 = physical_valid(row.key, "ee", "p0", calibration)
                p1 = physical_valid(row.key, "ee", "p1", calibration)
                radar |= p0.astype(np.uint8) * BITS["ee_p0"]
                radar |= p1.astype(np.uint8) * BITS["ee_p1"]
                radar |= (p0 & p1).astype(np.uint8) * BITS["ee_common"]
            eligible = np.where(label != 255, radar, 0).astype(np.uint8)
            neighbors = [
                int(i)
                for i in tree.query(geometries[index], predicate="intersects")
                if int(i) < index
            ]
            owner = remove_prior_coverage(
                eligible, transform, crs, [previous[i] for i in neighbors]
            )
            previous[index] = (eligible, transform, crs)
            mask_label = np.where(
                arrays["floodmask"] == 1, 2, np.where(arrays["permwater"] == 1, 1, 0)
            ).astype(np.uint8)
            mask_label[
                (label == 255) | (arrays["floodmask"] == 255) | (arrays["permwater"] == 255)
            ] = 255
            interior = np.zeros_like(label, dtype=bool)
            for category in (0, 1, 2):
                interior |= binary_erosion(
                    label == category, structure=np.ones((3, 3)), border_value=0
                )
            target = out / "tiles" / f"{row.key}.npz"
            partial = target.with_suffix(".partial.npz")
            np.savez_compressed(
                partial,
                label=label,
                mask_label=mask_label,
                strict_validity=arrays["validity"] == 1,
                boundary_interior=interior,
                owner=owner,
                radar=radar,
            )
            partial.replace(target)
            record = {
                "key": row.key,
                "event": event,
                "country": row.countries,
                "crs": str(crs),
                "transform": list(transform)[:6],
                "paired_available": row.key in paired_keys,
                "post_label_offset_days": row.post_label_offset_days,
                "source_bbox_intersection": bool(row.source_bbox_intersection),
                "overlap_neighbors": len(neighbors),
                "sha256": sha256(target),
            }
            for name, bit in BITS.items():
                record[f"{name}_eligible"] = int(((eligible & bit) != 0).sum())
                record[f"{name}_owned"] = int(((owner & bit) != 0).sum())
            rows.append(record)
        print(
            json.dumps({"event": event, "tiles": len(group), "total_prepared": len(rows)}),
            flush=True,
        )
    pd.DataFrame(rows).to_parquet(out / "tile_coverage.parquet", index=False)
    atomic_json(
        out / "complete.json",
        {
            "status": "support_census_complete",
            "tiles": len(rows),
            "paired_tiles": len(paired_keys),
            "verified_prediction_files": len(archived),
            "verified_archives": len(list((external / "archives").glob("*.json"))),
            "manifest_sha256": sha256(out / "manifest.json"),
            "coverage_sha256": sha256(out / "tile_coverage.parquet"),
        },
    )


if __name__ == "__main__":
    main()
