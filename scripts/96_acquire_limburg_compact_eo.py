"""Prepare and acquire compact past-only EO sequences for the event census.

Default is a manifest-only run. Imagery remains in Earth Engine until exported.
No model fitting, event outcome selection, TOA duplication or legacy Landsat
archive. The full-archive worker must remain paused.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/limburg_compact_eo"
LEGACY = ROOT / "data/raw/limburg_satellite_archive"
SPEC = importlib.util.spec_from_file_location(
    "eo_archive", ROOT / "scripts/95_acquire_limburg_satellite_archive.py"
)
ARCHIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ARCHIVE)
HLS = {"hls_s30": "NASA/HLS/HLSS30/v002", "hls_l30": "NASA/HLS/HLSL30/v002"}
# Exact six-band Prithvi order, matched to the two HLS instruments.
HLS_BANDS = {
    "hls_s30": ["B2", "B3", "B4", "B8A", "B11", "B12"],
    "hls_l30": ["B2", "B3", "B4", "B5", "B6", "B7"],
}
PRODUCTS = {
    "s2_10m": {
        "source": "s2_sr",
        "bands": ["B2", "B3", "B4", "B8", "acquired_day"],
        "resolution": 10,
    },
    "s2_20m": {
        "source": "s2_sr",
        "bands": ["B5", "B6", "B7", "B8A", "B11", "B12", "SCL", "acquired_day"],
        "resolution": 20,
    },
    "s1_ascending": {
        "source": "s1",
        "bands": ["VV", "VH", "angle", "acquired_day"],
        "resolution": 10,
        "orbit": 88,
        "direction": "ASCENDING",
        "dtype": "float32",
    },
    "hls": {
        "source": "hls",
        "bands": [
            "blue",
            "green",
            "red",
            "nir",
            "swir1",
            "swir2",
            "Fmask",
            "sensor_id",
            "acquired_day",
        ],
        "resolution": 30,
        "dtype": "float32",
    },
}


def temporal_requests(storms):
    """Completed months and four completed UTC Monday-to-Monday weeks only."""
    import pandas as pd

    windows = {}
    events = []
    for row in storms.itertuples():
        cutoff = pd.Timestamp(row.landmark_utc)
        if cutoff.tzinfo is None:
            raise ValueError("Event cutoffs must be timezone-aware")
        cutoff = cutoff.tz_convert("UTC")
        month_end = cutoff.normalize().replace(day=1)
        week_end = cutoff.normalize() - pd.Timedelta(days=cutoff.weekday())
        mapping = {
            "storm_id": row.storm_id,
            "cutoff_utc": cutoff.isoformat(),
            "monthly": [],
            "recent": [],
        }
        for kind, n, end in [("monthly", 12, month_end), ("recent", 4, week_end)]:
            for _ in range(n):
                start = end - (
                    pd.DateOffset(months=1) if kind == "monthly" else pd.Timedelta(days=7)
                )
                key = f"{kind}_{start:%Y%m%d}_{end:%Y%m%d}"
                windows[key] = {
                    "id": key,
                    "kind": kind,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                }
                mapping[kind].append(key)
                end = start
        events.append(mapping)
    return sorted(windows.values(), key=lambda w: (w["start"], w["kind"])), events


def size_bytes(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file()) if root.exists() else 0


def raw_bound(job):
    return (
        (9600 // job["resolution"]) ** 2
        * (len(job["bands"]) + 1)
        * (4 if job.get("dtype") == "float32" else 2)
    )


def budget_allows(used, reserved, candidate, image_limit, working_limit, other):
    # Download and packed file can coexist. Compression can expand slightly.
    needed = raw_bound(candidate) * 2.2 + 65536
    return used + reserved + needed <= min(image_limit, working_limit - other)


def validate_plan(previous, current):
    for key in (
        "storm_csv_sha256",
        "geometry_sha256",
        "products",
        "buffer_m",
        "composite",
        "quality",
        "s1_orbits",
    ):
        if previous.get(key) != current.get(key):
            raise ValueError(
                f"Compact archive scientific specification changed: {key}; use a separate destination"
            )


def catalogues(ee, region, first_year, last_year, destination):
    records = []
    sources = {"s1": ARCHIVE.SOURCES["s1"][0], "s2_sr": ARCHIVE.SOURCES["s2_sr"][0], **HLS}
    for source, collection in sources.items():
        for year in range(first_year, last_year + 1):
            local = destination / "catalogues" / f"{source}_{year}.json"
            original = LEGACY / "catalogues" / f"{source}_{year}.json"
            if local.exists():
                features = json.loads(local.read_text())
            elif original.exists():
                features = json.loads(original.read_text())
                ARCHIVE.write_json(local, features)
            else:
                images = (
                    ee.ImageCollection(collection)
                    .filterBounds(region)
                    .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
                )
                if source == "s1":
                    images = (
                        images.filter(ee.Filter.eq("instrumentMode", "IW"))
                        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
                    )
                fields = [*ARCHIVE.METADATA, "REF_SCALE_FACTOR", "ADD_OFFSET", "CLOUD_COVERAGE"]
                features = ee.FeatureCollection(
                    images.map(
                        lambda im, properties=fields: ee.Feature(
                            im.geometry(), im.toDictionary(properties)
                        )
                    )
                ).getInfo()["features"]
                ARCHIVE.write_json(local, features)
            records.extend({"source": source, "collection": collection, **f} for f in features)
            print(f"catalogue {source} {year}: {len(features)}", flush=True)
    return records


def build_jobs(windows, records, tiles):
    import pandas as pd
    from pyproj import Transformer
    from shapely.geometry import box, shape
    from shapely.ops import transform

    project = Transformer.from_crs(4326, 32632, always_xy=True).transform
    indexed = []
    for record in records:
        properties = record["properties"]
        scene_id = properties.get("system:index", record.get("id"))
        indexed.append(
            (
                record["source"],
                properties["system:time_start"],
                record["collection"] + "/" + scene_id,
                properties,
                transform(project, shape(record["geometry"])),
            )
        )
    jobs = []
    availability = []
    for window in windows:
        start = pd.Timestamp(window["start"]).timestamp() * 1000
        end = pd.Timestamp(window["end"]).timestamp() * 1000
        candidates = [r for r in indexed if start <= r[1] < end]
        for product, settings in PRODUCTS.items():
            selected = [
                r
                for r in candidates
                if (r[0] == settings["source"] or (settings["source"] == "hls" and r[0] in HLS))
                and (
                    settings["source"] != "s1"
                    or (
                        r[3].get("relativeOrbitNumber_start") == settings["orbit"]
                        and r[3].get("orbitProperties_pass") == settings["direction"]
                    )
                )
            ]
            availability.append(
                {"window": window["id"], "product": product, "source_scene_count": len(selected)}
            )
            for tile in tiles:
                overlapping = [r for r in selected if r[4].intersects(box(*tile["bounds"]))]
                if not overlapping:
                    continue
                jobs.append(
                    {
                        **settings,
                        "product": product,
                        "window": window,
                        "bounds": tile["bounds"],
                        "asset_id": "computed/" + window["id"] + "/" + product,
                        "asset_ids": [r[2] for r in overlapping],
                        "acquisition_ms": [r[1] for r in overlapping],
                        "source_metadata": [r[3] for r in overlapping],
                        "relative_path": f"images/{window['id']}/{product}/{tile['id']}.tif",
                    }
                )
    return jobs, availability


def composite(ee, job):
    def prepare(image, source):
        if source == "s2_sr":
            quality = image.select("SCL")
            good = (
                quality.neq(0)
                .And(quality.neq(1))
                .And(quality.neq(3))
                .And(quality.lt(8).Or(quality.eq(11)))
            )
            data = image.select([b for b in job["bands"] if b != "acquired_day"]).updateMask(good)
        elif source.startswith("hls_"):
            flags = image.select("Fmask")
            # Keep snow and water; exclude cloud, adjacent cloud and shadow.
            good = flags.bitwiseAnd(14).eq(0)
            names = ["blue", "green", "red", "nir", "swir1", "swir2"]
            sensor = ee.Image.constant(1 if source == "hls_s30" else 2).rename("sensor_id")
            data = (
                image.select(HLS_BANDS[source], names)
                .addBands(flags)
                .addBands(sensor)
                .updateMask(good)
            )
        else:
            data = image.select(["VV", "VH", "angle"])
        day = (
            ee.Image.constant(ee.Number(image.get("system:time_start")).divide(86400000))
            .rename("acquired_day")
            .toDouble()
        )
        # Latest usable actual observation per pixel, not an invented mean spectrum.
        return data.addBands(day.updateMask(data.mask().reduce(ee.Reducer.min()))).toDouble()

    collection = ee.ImageCollection(
        [
            prepare(
                ee.Image(asset),
                ("hls_s30" if asset.startswith(HLS["hls_s30"] + "/") else "hls_l30")
                if job["source"] == "hls"
                else job["source"],
            )
            for asset in job["asset_ids"]
        ]
    )
    return collection.qualityMosaic("acquired_day").select(job["bands"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="limburg-511403")
    parser.add_argument("--destination", type=Path, default=DEST)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--image-budget-gb", type=float, default=70)
    parser.add_argument("--max-working-gb", type=float, default=100)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    worker_lock = (args.destination / ".worker.lock").open("a")
    try:
        fcntl.flock(worker_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(
            "A compact manifest/download worker already holds this archive lock"
        ) from None
    proj = Path(sys.base_prefix) / "share/proj"
    if "PROJ_DATA" not in os.environ and (proj / "proj.db").exists():
        os.environ["PROJ_DATA"] = str(proj)
    import ee
    import geopandas as gpd
    import pandas as pd

    ee.Initialize(project=args.project)
    frame = gpd.read_file(ROOT / "data/interim/foundation_model_catchments.gpkg")
    frame = frame[frame.experiment_role != "inventory"].to_crs(32632)
    geometry = frame.geometry.union_all().buffer(320)
    region_frame = gpd.GeoSeries([geometry], crs=32632).to_crs(4326)
    region = ee.Geometry(region_frame.iloc[0].__geo_interface__)
    storms_path = ROOT / "results/storm_response/storms.csv"
    windows, events = temporal_requests(pd.read_csv(storms_path))
    destination = args.destination
    destination.mkdir(parents=True, exist_ok=True)
    # Empty pre-mission windows remain in the map but need no imagery export.
    live_windows = [w for w in windows if w["end"] >= "2013-04-01"]
    records = catalogues(ee, region, 2013, 2025, destination)
    tiles = list(ARCHIVE.tiles_for_geometry(geometry))
    jobs, availability = build_jobs(live_windows, records, tiles)
    # Monthly context first, then recent weeks; retain the complete manifest.
    jobs.sort(
        key=lambda j: (
            0 if j["window"]["kind"] == "monthly" else 1,
            j["window"]["start"],
            j["product"],
            j["relative_path"],
        )
    )
    plan = {
        "event_count": len(events),
        "windows_requested": len(windows),
        "export_windows_with_source_scenes": len({j["window"]["id"] for j in jobs}),
        "planned_files": len(jobs),
        "uncompressed_gb": sum(raw_bound(j) for j in jobs) / 1e9,
        "image_budget_gb": args.image_budget_gb,
        "max_working_gb": args.max_working_gb,
        "storm_csv_sha256": ARCHIVE.digest(storms_path),
        "geometry_sha256": __import__("hashlib").sha256(geometry.wkb).hexdigest(),
        "code_sha256": ARCHIVE.digest(Path(__file__)),
        "helper_sha256": ARCHIVE.digest(ROOT / "scripts/95_acquire_limburg_satellite_archive.py"),
        "products": PRODUCTS,
        "buffer_m": 320,
        "selection": "all supplied catalogue events; no outcome filtering",
        "composite": "latest usable acquisition per pixel within completed calendar bins",
        "quality": "SCL excludes 0,1,3,8,9,10; HLS Fmask excludes bits 1,2,3; keep snow and water",
        "s2_acquired_day": "floored UTC epoch day stored uint16; exact candidate timestamps in receipts",
        "hls_reflectance": "stored Earth Engine HLS values, not cast to integers; verify units against source metadata before inference",
        "s1_orbits": "ascending 88 covers held catchments in 2017 catalogue geometry; descending 37 deferred",
        "monthly_context": "up to 12 completed months; not a universal model requirement",
        "recent_context": "four completed weeks; partial current week deliberately excluded; record age",
        "not_ready_for_models": [
            "S1 GRD is not RTC",
            "checkpoint input and normalisation checks pending",
            "TOA and special bands deferred",
        ],
    }
    if (destination / "plan.json").exists():
        validate_plan(json.loads((destination / "plan.json").read_text()), plan)
    ARCHIVE.write_json(destination / "event_windows.json", events)
    ARCHIVE.write_json(destination / "jobs.json", jobs)
    ARCHIVE.write_json(destination / "availability.json", availability)
    ARCHIVE.write_json(destination / "plan.json", plan)
    print(json.dumps(plan, indent=2), flush=True)
    if not args.download:
        return 0
    other = size_bytes(LEGACY) + size_bytes(ROOT / "data/raw/limburg_dynamic_model_weights")
    used = size_bytes(destination)
    reserved = 0
    iterator = iter(jobs)
    counts = {"downloaded": 0, "existing": 0, "failed": 0}
    halted = None
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        active = {}

        def replenish():
            nonlocal reserved, halted
            while not halted and len(active) < args.workers:
                job = next(iterator, None)
                if job is None:
                    break
                target = destination / job["relative_path"]
                existing = target.exists() and target.with_suffix(".receipt.json").exists()
                if not existing and not budget_allows(
                    used,
                    reserved,
                    job,
                    args.image_budget_gb * 1e9,
                    args.max_working_gb * 1e9,
                    other,
                ):
                    halted = "storage_budget"
                    break
                reservation = 0 if existing else raw_bound(job) * 2.2 + 65536
                reserved += reservation
                image = composite(ee, job)
                future = pool.submit(ARCHIVE.download_job, job, destination, 60, region, image)
                active[future] = (job, reservation)

        replenish()
        while active:
            completed, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in completed:
                job, reservation = active.pop(future)
                reserved -= reservation
                try:
                    status = future.result()
                    counts[status] += 1
                    if status == "downloaded":
                        used += (destination / job["relative_path"]).stat().st_size
                        used += (
                            (destination / job["relative_path"])
                            .with_suffix(".receipt.json")
                            .stat()
                            .st_size
                        )
                except Exception as error:
                    counts["failed"] += 1
                    ARCHIVE.write_json(
                        destination
                        / "errors"
                        / (
                            __import__("hashlib").sha256(job["relative_path"].encode()).hexdigest()
                            + ".json"
                        ),
                        {"job": job["relative_path"], "error": str(error).split("https://")[0]},
                    )
                    print(f"failed {job['relative_path']}: {str(error)[:160]}", flush=True)
                    if counts["failed"] >= 10 or "Disk reserve" in str(error):
                        halted = "failures_or_disk_reserve"
            ARCHIVE.write_json(
                destination / "progress.json",
                counts
                | {
                    "estimated_archive_bytes": used,
                    "other_budgeted_bytes": other,
                    "planned_files": len(jobs),
                    "halted": halted,
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                },
            )
            if sum(counts.values()) % 10 == 0:
                print(counts, flush=True)
            other = size_bytes(LEGACY) + size_bytes(ROOT / "data/raw/limburg_dynamic_model_weights")
            replenish()
    print(counts, "halted", halted, flush=True)
    return 1 if halted or counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
