#!/usr/bin/env python3
"""Inventory local annotation support without selecting any labels or fitting."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import atomic_json, sha256


def main():
    base = ROOT / "results/limburg_chapter_sized_v1/local"
    coverage_path = base / "coverage.parquet"
    inventory_path = ROOT / "data/raw/limburg_chapter_local_triplets_v1/inventory.json"
    coverage = pd.read_parquet(coverage_path)
    jobs = {
        j["key"]: j
        for j in json.loads(inventory_path.read_text())["jobs"]
        if j.get("status") == "prepared"
    }
    cases = coverage.groupby(["aoi", "case"], as_index=False).agg(
        min_offset=("reference_offset_hours", "min"), max_offset=("reference_offset_hours", "max")
    )
    # Adjacent SAR slices have different sensing seconds. Use the worst
    # absolute offset within a case and retain the full range.
    cases["absolute_offset"] = cases[["min_offset", "max_offset"]].abs().max(axis=1)
    # Metadata-only nearest-time case, not a score/coverage/positive-label choice.
    chosen = cases.sort_values(["absolute_offset", "case"]).groupby("aoi", as_index=False).first()
    rows, sources = [], {}
    for case in chosen.itertuples():
        group = coverage.loc[coverage.case == case.case]
        grids = []
        for record in group.itertuples():
            job = jobs[record.key]
            support = base / "support" / f"{record.key}.npz"
            if sha256(support) != record.support_sha256:
                raise ValueError("Local support has changed")
            with np.load(support, allow_pickle=False) as data:
                owned, label = data["owner"], data["label"]
            path = ROOT / job["reference_path"]
            if sha256(path) != job["reference_sha256"]:
                raise ValueError("Local label has changed")
            with rasterio.open(path) as ds:
                transform, crs = ds.transform, str(ds.crs)
            pixel_area = abs(transform.a * transform.e - transform.b * transform.d)
            item = dict(
                key=record.key,
                reference=job["reference_path"],
                crs=crs,
                transform=list(transform)[:6],
                known_owned_pixels=int(owned.sum()),
                flood_owned_pixels=int((owned & (label == 2)).sum()),
                known_area_km2=float(owned.sum() * pixel_area / 1e6),
                flood_area_km2=float((owned & (label == 2)).sum() * pixel_area / 1e6),
            )
            # Diagnostic granularity, not independently sampled annotation units.
            for size in (32, 64, 128):
                complete = partial = positive = 0
                for top in range(0, owned.shape[0], size):
                    for left in range(0, owned.shape[1], size):
                        mask = owned[top : top + size, left : left + size]
                        if not mask.any():
                            continue
                        full = mask.shape == (size, size) and mask.all()
                        complete += int(full)
                        partial += int(not full)
                        positive += int(
                            full and (label[top : top + size, left : left + size] == 2).any()
                        )
                item[f"patch{size}_fully_known"] = complete
                item[f"patch{size}_partial"] = partial
                item[f"patch{size}_fully_known_with_reference_flood"] = positive
            grids.append(item)
            sources[str(support.relative_to(ROOT))] = sha256(support)
            sources[str(path.relative_to(ROOT))] = sha256(path)
        numeric = [
            k
            for k in grids[0]
            if k.endswith("pixels") or k.endswith("km2") or k.startswith("patch")
        ]
        rows.append(
            dict(
                aoi=case.aoi,
                case=case.case,
                reference_offset_hours_min=case.min_offset,
                reference_offset_hours_max=case.max_offset,
                grid_records=len(grids),
                totals={k: sum(g[k] for g in grids) for k in numeric},
                grids=grids,
            )
        )
    for path in (coverage_path, inventory_path, Path(__file__)):
        sources[str(path.relative_to(ROOT))] = sha256(path)
    result = dict(
        date="2026-11-12",
        status="local_spatial_support_inventory_complete_no_labels_selected",
        selection="nearest listed reference time per AOI, ties by case ID; no scores or labels used",
        diagnostic_patch_sizes_pixels=[32, 64, 128],
        limits=[
            "One physical flood episode; no later-event generalization established.",
            "Patch counts are diagnostic, not independent observations or annotation-hours.",
            "No adaptation/test split, buffer or label budget has been selected.",
            "Flood-positive patch counts describe existing references and cannot be used to secretly balance a random query pool.",
        ],
        cases=rows,
        sources=sources,
    )
    atomic_json(ROOT / "docs/reviews/limburg-local-adaptation-support-2026-11-12.json", result)
    for row in rows:
        print(json.dumps({k: v for k, v in row.items() if k != "grids"}))


if __name__ == "__main__":
    main()
