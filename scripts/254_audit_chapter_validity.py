#!/usr/bin/env python3
"""Audit all mapped acquisition geometries and fixed target-construction support.

Only small public product metadata may be downloaded (--fetch-metadata).
No fitting, label replacement, imagery acquisition or prediction changes.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from limburg_chapter_evaluation import BITS, atomic_json, packet, sha256
from limburg_chapter_validity import compare_geometry, label_transition_counts

BASE = ROOT / "results/limburg_chapter_sized_v1"
OUT = BASE / "validity"
CACHE = ROOT / "data/raw/limburg_chapter_validity_metadata_v1"
CATALOGUE = (
    ROOT
    / "data/raw/limburg_applied_tasks/local_references/geoid-flood-heldout-tile-catalog.parquet"
)
URL = "https://stac.dataspace.copernicus.eu/v1/collections/sentinel-1-grd/items/"


def metadata_index():
    index = {}
    old = ROOT / "data/processed/limburg_chapter_p1_inventory_v1/catalog"
    for folder in (old / "items", old / "search", CACHE):
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.json")):
            data = json.loads(path.read_text())
            items = data.get("features", []) if "features" in data else [data]
            for item in items:
                if "id" in item and "properties" in item:
                    index[item["id"]] = (item, path)
    return index


def fetch(product):
    path = CACHE / f"{product}.json"
    for attempt in range(4):
        try:
            with urlopen(URL + product, timeout=45) as response:
                item = json.load(response)
            if item.get("id") != product:
                raise ValueError(f"Metadata product mismatch: {product}")
            atomic_json(path, item)
            return product, None
        except (HTTPError, OSError) as exc:
            if isinstance(exc, HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                return product, str(exc)
            if attempt == 3:
                return product, str(exc)
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def traits(item):
    p = item["properties"]
    return {
        "platform": p.get("platform"),
        "relative_orbit": p.get("sat:relative_orbit"),
        "pass_direction": p.get("sat:orbit_state", "").lower(),
        "mode": p.get("sar:instrument_mode"),
        "polarizations": tuple(sorted(p.get("sar:polarizations", []))),
        "look": p.get("sar:observation_direction"),
        "incidence_angle": p.get("view:incidence_angle"),
    }


def comparisons(products, lookup):
    result = {}
    for a, b in (("p0", "p1"), ("p0", "post"), ("p1", "post")):
        x, y = lookup.get(products[a], {}), lookup.get(products[b], {})
        for k, value in compare_geometry(x, y).items():
            result[f"{a}_{b}_{k}"] = value
    for phase, product in products.items():
        result[f"{phase}_product"] = product
        for field, value in lookup.get(product, {}).items():
            result[f"{phase}_{field}"] = str(value) if isinstance(value, tuple) else value
    return result


def fetch_local_metadata():
    """Run with an Earth Engine-capable interpreter; fetch metadata, never pixels."""
    import ee

    path = CACHE / "local-ee-products.json"
    jobs = json.loads(
        (ROOT / "data/raw/limburg_chapter_local_triplets_v1/inventory.json").read_text()
    )["jobs"]
    products = sorted(
        {s for job in jobs if job.get("status") == "prepared" for s in job["products"].values()}
    )
    ee.Initialize(project="limburg-511403")
    fields = [
        "relativeOrbitNumber_start",
        "orbitProperties_pass",
        "instrumentMode",
        "transmitterReceiverPolarisation",
        "platform_number",
        "orbitNumber_start",
        "system:time_start",
    ]
    values = ee.Dictionary(
        {s: ee.Image("COPERNICUS/S1_GRD_FLOAT/" + s).toDictionary(fields) for s in products}
    ).getInfo()
    if set(values) != set(products):
        raise ValueError("Incomplete local product metadata")
    atomic_json(path, values)
    print(json.dumps({"local_acquisitions_verified": len(values)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-metadata", action="store_true")
    parser.add_argument(
        "--local-metadata-only",
        action="store_true",
        help="Fetch all local asset metadata using an Earth Engine-capable interpreter, then exit",
    )
    args = parser.parse_args()
    if args.local_metadata_only:
        fetch_local_metadata()
        return
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    catalogue = pd.read_parquet(CATALOGUE)
    catalogue["key"] = catalogue.event_id + "-" + catalogue.tile_id + "-" + catalogue.bbox_id
    receipts = {
        path.stem.removesuffix(".receipt"): path
        for path in (ROOT / "data/raw/limburg_chapter_ee_triplets_v1/tiles").rglob("*.receipt.json")
    }
    external = {}
    for row in catalogue.itertuples():
        products = {"p0": list(row.s1_pre_products), "post": list(row.s1_post_products)}
        if row.key in receipts:
            products = {
                k: [v] for k, v in json.loads(receipts[row.key].read_text())["products"].items()
            }
        external[row.key] = products
    needed = {p for products in external.values() for values in products.values() for p in values}
    index = metadata_index()
    missing = sorted(needed - set(index))
    failures = []
    if args.fetch_metadata:
        with ThreadPoolExecutor(max_workers=3) as pool:
            for done, (product, error) in enumerate(pool.map(fetch, missing), 1):
                if error:
                    failures.append({"product": product, "error": error})
                if done % 10 == 0 or done == len(missing):
                    print(json.dumps({"metadata_checked": done, "total": len(missing)}), flush=True)
        index = metadata_index()
    lookup = {key: traits(item) for key, (item, _) in index.items()}
    rows = []
    for row in catalogue.itertuples():
        products = external[row.key]
        record = {"key": row.key, "event": row.event_id, "paired": row.key in receipts}
        if all(len(values) == 1 for values in products.values()):
            scalar = {k: values[0] for k, values in products.items()}
            if "p1" not in scalar:
                scalar["p1"] = scalar["p0"]
            record.update(comparisons(scalar, lookup))
            record["single_products"] = True
        else:
            record["single_products"] = False
            pairs = [
                compare_geometry(lookup.get(a, {}), lookup.get(b, {}))
                for a in products["p0"]
                for b in products["post"]
            ]
            states = {value["status"] for value in pairs}
            record["p0_post_status"] = (
                "mismatch"
                if "mismatch" in states
                else "unknown"
                if "unknown" in states
                else "compatible"
            )
            record["p0_post_mismatched"] = ",".join(
                sorted(
                    {field for value in pairs for field in value["mismatched"].split(",") if field}
                )
            )
            record["p0_post_missing"] = ",".join(
                sorted({field for value in pairs for field in value["missing"].split(",") if field})
            )
            record["p0_product"] = "|".join(products["p0"])
            record["post_product"] = "|".join(products["post"])
        rows.append(record)
    frame = pd.DataFrame(rows)
    frame.to_parquet(OUT / "external_geometry.parquet", index=False)
    # Independently query the actual Earth Engine assets; do not infer P1 orbit
    # from the selection rule that this audit is supposed to verify.
    local_input = ROOT / "data/raw/limburg_chapter_local_triplets_v1/inventory.json"
    local_frame_path = (
        ROOT / "results/applied_study_v1/local_references/scoring/scene-reference-pairs.parquet"
    )
    local_metadata = CACHE / "local-ee-products.json"
    local_items = json.loads(local_metadata.read_text())
    local_lookup = {}
    for scene, props in local_items.items():
        local_lookup[scene] = dict(
            platform=f"sentinel-1{props['platform_number'].lower()}",
            relative_orbit=props["relativeOrbitNumber_start"],
            pass_direction=props["orbitProperties_pass"].lower(),
            mode=props["instrumentMode"],
            polarizations=tuple(sorted(props["transmitterReceiverPolarisation"])),
            look="right",  # Sentinel-1 sensor geometry, not inferred from orbit.
        )
    local_rows = []
    for job in json.loads(local_input.read_text())["jobs"]:
        if job.get("status") != "prepared":
            continue
        local_rows.append(
            {
                "key": job["key"],
                "aoi": job["aoi"],
                "updated": job["updated"],
                "metadata_basis": "actual Earth Engine asset properties; Sentinel-1 right-looking sensor",
                **comparisons(job["products"], local_lookup),
            }
        )
    pd.DataFrame(local_rows).to_parquet(OUT / "local_geometry.parquet", index=False)
    # Compare the already frozen primary and source-mask target constructions.
    coverage_path = BASE / "evaluation/support/tile_coverage.parquet"
    coverage = pd.read_parquet(coverage_path)
    label_rows = []
    for row in coverage.itertuples():
        data = packet(row.key)
        for support, bit in (("delivered", BITS["delivered_p0"]), ("paired", BITS["ee_common"])):
            owned = (data["owner"] & bit) != 0
            if not owned.any():
                continue
            counts = label_transition_counts(data["label"], data["mask_label"], owned)
            label_rows.append(
                {
                    "key": row.key,
                    "event": row.event,
                    "support": support,
                    **{f"y{a}_z{b}": int(counts[a, b]) for a in range(4) for b in range(4)},
                }
            )
    pd.DataFrame(label_rows).to_parquet(OUT / "target_construction.parquet", index=False)
    sources = {
        str(path.relative_to(ROOT)): sha256(path) for path in {path for _, path in index.values()}
    }
    for path in (
        CATALOGUE,
        local_input,
        local_metadata,
        local_frame_path,
        coverage_path,
        Path(__file__),
        ROOT / "src/limburg_chapter_validity.py",
        ROOT / "src/applied_change_task.py",
        ROOT / "src/applied_local_reference.py",
        ROOT / "scripts/248_run_chapter_local.py",
        ROOT
        / "data/raw/limburg_dynamic_model_weights/code/copernicus_fm/Copernicus-Bench/src/datasets/cobench_floods1_wrapper.py",
        ROOT / "docs/reviews/limburg-chapter-scope-audit-2026-11-10/sources/geoid-card-pinned.md",
        ROOT / "data/raw/limburg_chapter_geoid_code_v1/scripts/eval_flood_paired.py",
    ):
        sources[str(path.relative_to(ROOT))] = sha256(path)
    atomic_json(
        OUT / "audit.json",
        {
            "status": "metadata_and_target_audit_complete",
            "external_tiles": len(frame),
            "paired_tiles": int(frame.paired.sum()),
            "local_records": len(local_rows),
            "products_required": len(needed),
            "missing_product_metadata": sorted(needed - set(index)),
            "download_errors": failures,
            "geometry_caution": "Compatible metadata is necessary, not a per-pixel incidence or terrain-distortion equivalence test.",
            "sources": sources,
            "receipt_hashes": {key: sha256(path) for key, path in receipts.items()},
            "outputs": {
                name: sha256(OUT / name)
                for name in (
                    "external_geometry.parquet",
                    "local_geometry.parquet",
                    "target_construction.parquet",
                )
            },
        },
    )
    print(frame.groupby(["paired", "p0_post_status"], dropna=False).size().to_string())


if __name__ == "__main__":
    main()
