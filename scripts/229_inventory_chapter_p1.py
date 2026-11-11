#!/usr/bin/env python3
"""Inventory label-blind, same-orbit updated SAR references for GEOID tiles.

Queries public CDSE STAC metadata only. This does not establish raster-processing
parity or download P1 pixels. All raw responses are cached for reproducibility.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import urlopen

import pandas as pd
from shapely import wkb
from shapely.geometry import shape
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/raw/limburg_applied_tasks/local_references/geoid-flood-heldout-tile-catalog.parquet"
OUT = ROOT / "data/processed/limburg_chapter_p1_inventory_v1"
BASE = "https://stac.dataspace.copernicus.eu/v1"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def acquisition_from_id(product: str) -> datetime:
    """Sentinel-1 sensing start, unaffected by catalogue reissue timestamps."""
    return datetime.strptime(product.split("_")[4], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)


def fetch_json(url: str, cache: Path) -> dict:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return json.loads(cache.read_text())
    for attempt in range(8):
        try:
            with urlopen(url, timeout=45) as response:
                data = response.read()
            value = json.loads(data)
            tmp = cache.with_suffix(cache.suffix + ".partial")
            tmp.write_bytes(data)
            tmp.replace(cache)
            time.sleep(0.5)  # polite catalogue pace; cached reruns do not delay
            return value
        except HTTPError as exc:
            if exc.code != 429 or attempt == 7:
                raise
            retry_after = exc.headers.get("Retry-After", "")
            delay = float(retry_after) if retry_after.isdigit() else min(10 * 2 ** attempt, 120)
            time.sleep(delay)
        except Exception:
            if attempt == 7:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise AssertionError("unreachable")


def item_id(product: str, cache: Path) -> dict:
    url = f"{BASE}/collections/sentinel-1-grd/items/{product}"
    return fetch_json(url, cache / "items" / f"{product}.json")


def search(product: str, event: str, group: pd.DataFrame, base_item: dict, cache: Path) -> list[dict]:
    bounds = unary_union([wkb.loads(g) for g in group.geometry]).bounds
    onset = min(parse_time(v) for v in group.event_time)
    baseline = parse_time(base_item["properties"]["datetime"])
    if baseline >= onset:
        return []
    prop = base_item["properties"]
    params = {
        "collections": "sentinel-1-grd",
        "bbox": ",".join(f"{v:.8f}" for v in bounds),
        "datetime": f"{(baseline + timedelta(seconds=1)).isoformat().replace('+00:00','Z')}/{onset.isoformat().replace('+00:00','Z')}",
        "limit": "100",
        "filter": (
            f"sat:relative_orbit = {prop['sat:relative_orbit']} AND "
            f"platform = '{prop['platform']}' AND "
            f"sat:orbit_state = '{prop['sat:orbit_state']}'"
        ),
    }
    url = f"{BASE}/search?{urlencode(params)}"
    results = []
    page = 0
    while url:
        data = fetch_json(url, cache / "search" / f"{event}-{product}-{page}.json")
        results.extend(data.get("features", []))
        url = next((link["href"] for link in data.get("links", []) if link.get("rel") == "next"), None)
        page += 1
        if page > 100:
            raise RuntimeError(f"Unexpectedly many STAC pages for {event}/{product}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if not 1 <= args.workers <= 6:
        parser.error("Use one to six metadata workers")
    frame = pd.read_parquet(CATALOG)
    if len(frame) != 1301:
        raise ValueError("Pinned external cohort count changed")
    args.output.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    for row in frame.itertuples():
        for product in row.s1_pre_products:
            groups[(product, row.event_id)].append(row.Index)
    products = sorted({product for product, _ in groups})
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        base_future = {pool.submit(item_id, product, args.output / "catalog"): product for product in products}
        base = {base_future[fut]: fut.result() for fut in as_completed(base_future)}
        search_future = {
            pool.submit(search, product, event, frame.loc[indices], base[product], args.output / "catalog"): (product, event)
            for (product, event), indices in groups.items()
        }
        found = {search_future[fut]: fut.result() for fut in as_completed(search_future)}
    rows = []
    for row in frame.itertuples():
        tile = wkb.loads(row.geometry)  # the GeoParquet geometry is WGS84; utm_crs describes raster grid
        base_items = [base[p] for p in row.s1_pre_products]
        traits = {
            (x["properties"]["platform"], x["properties"]["sat:relative_orbit"], x["properties"]["sat:orbit_state"])
            for x in base_items
        }
        delivered_coverage = tile.intersection(unary_union([shape(x["geometry"]) for x in base_items])).area / tile.area
        delivered_time = max(acquisition_from_id(p) for p in row.s1_pre_products)
        candidates = {x["id"]: x for product in row.s1_pre_products for x in found[(product, row.event_id)]}
        by_day = defaultdict(list)
        for x in candidates.values():
            prop = x["properties"]
            if not {"VV", "VH"}.issubset(set(prop.get("sar:polarizations", []))):
                continue
            key = (
                prop["platform"], prop["sat:relative_orbit"], prop["sat:orbit_state"],
                parse_time(prop["datetime"]).date().isoformat(),
            )
            by_day[key].append(x)
        options = []
        if len(traits) == 1:
            for key, scenes in by_day.items():
                if key[:3] not in traits:
                    continue
                # Prefer a single complete scene. STAC search can return two
                # overlapping granules even when either alone covers the tile.
                single = [
                    (x, tile.intersection(shape(x["geometry"])).area / tile.area)
                    for x in scenes
                ]
                complete = [(x, c) for x, c in single if c + 1e-4 >= delivered_coverage]
                if complete:
                    best_single, coverage = max(
                        complete, key=lambda pair: (parse_time(pair[0]["properties"]["datetime"]), pair[0]["id"])
                    )
                    used = [best_single]
                else:
                    used = scenes
                    coverage = tile.intersection(unary_union([shape(x["geometry"]) for x in used])).area / tile.area
                if coverage + 1e-4 < delivered_coverage:
                    continue
                if any(acquisition_from_id(x["id"]) <= delivered_time for x in used):
                    continue
                options.append((max(parse_time(x["properties"]["datetime"]) for x in used), key, used, coverage))
        options.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best = options[0] if options else None
        rows.append({
            "event_id": row.event_id, "tile_id": row.tile_id, "bbox_id": row.bbox_id,
            "delivered_products": list(row.s1_pre_products),
            "delivered_sensing_time": delivered_time.isoformat(),
            "delivered_coverage_fraction": round(delivered_coverage, 6),
            "baseline_traits_consistent": len(traits) == 1,
            "p1_catalogue_candidate": best is not None,
            "p1_time": best[0].isoformat() if best else None,
            "p1_products": [x["id"] for x in best[2]] if best else [],
            "p1_footprint_coverage_fraction": round(best[3], 6) if best else None,
            "event_time_provisional": row.event_time,
            "processing_parity_verified": False,
        })
    output = args.output / "tile_inventory.json"
    tmp = output.with_suffix(".partial")
    tmp.write_text(json.dumps(rows, indent=2) + "\n")
    tmp.replace(output)
    summary = {
        "source_catalog": str(CATALOG.relative_to(ROOT)),
        "source_catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        "stac_endpoint": BASE, "tiles": len(rows), "baseline_products": len(products),
        "search_groups": len(groups),
        "p1_catalogue_candidates": sum(r["p1_catalogue_candidate"] for r in rows),
        "inconsistent_baseline_traits": sum(not r["baseline_traits_consistent"] for r in rows),
        "processing_parity_verified": False,
        "note": "Metadata candidates only; no P1 imagery or same-chain P0/P1 raster verification",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
