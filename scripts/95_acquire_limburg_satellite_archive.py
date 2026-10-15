"""Acquire a shared, dated EO archive; no model compatibility filtering.

All scenes, including cloudy scenes, are retained. Native-resolution band
families are exported separately on aligned UTM grids. Catalogue and receipts
are local/ignored; no credentials or temporary download URLs are persisted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import time
from collections import defaultdict, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/limburg_satellite_archive"
SOURCES = {
    "s1": ("COPERNICUS/S1_GRD", {10: ["VV", "VH", "angle"]}),
    "s2_sr": (
        "COPERNICUS/S2_SR_HARMONIZED",
        {
            10: ["B2", "B3", "B4", "B8"],
            20: ["B5", "B6", "B7", "B8A", "B11", "B12", "SCL", "AOT", "WVP"],
            60: ["B1", "B9", "QA60"],
        },
    ),
    "s2_toa": (
        "COPERNICUS/S2_HARMONIZED",
        {
            10: ["B2", "B3", "B4", "B8"],
            20: ["B5", "B6", "B7", "B8A", "B11", "B12"],
            60: ["B1", "B9", "B10", "QA60"],
        },
    ),
    "landsat5": (
        "LANDSAT/LT05/C02/T1_L2",
        {30: ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7", "QA_PIXEL", "QA_RADSAT"]},
    ),
    "landsat7": (
        "LANDSAT/LE07/C02/T1_L2",
        {30: ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7", "QA_PIXEL", "QA_RADSAT"]},
    ),
    "landsat8": (
        "LANDSAT/LC08/C02/T1_L2",
        {
            30: [
                "SR_B1",
                "SR_B2",
                "SR_B3",
                "SR_B4",
                "SR_B5",
                "SR_B6",
                "SR_B7",
                "QA_PIXEL",
                "QA_RADSAT",
            ]
        },
    ),
    "landsat9": (
        "LANDSAT/LC09/C02/T1_L2",
        {
            30: [
                "SR_B1",
                "SR_B2",
                "SR_B3",
                "SR_B4",
                "SR_B5",
                "SR_B6",
                "SR_B7",
                "QA_PIXEL",
                "QA_RADSAT",
            ]
        },
    ),
}
METADATA = [
    "system:time_start",
    "system:time_end",
    "system:index",
    "orbitProperties_pass",
    "relativeOrbitNumber_start",
    "platform_number",
    "CLOUDY_PIXEL_PERCENTAGE",
    "MGRS_TILE",
    "PROCESSING_BASELINE",
    "SPACECRAFT_ID",
    "LANDSAT_PRODUCT_ID",
    "CLOUD_COVER",
    "WRS_PATH",
    "WRS_ROW",
]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    part.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    part.replace(path)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tiles_for_geometry(geometry, size=9600):
    from shapely.geometry import box

    xmin, ymin, xmax, ymax = geometry.bounds
    for x in range(math.floor(xmin / size) * size, math.ceil(xmax / size) * size, size):
        for y in range(math.floor(ymin / size) * size, math.ceil(ymax / size) * size, size):
            tile = box(x, y, x + size, y + size)
            if tile.intersects(geometry):
                yield {"id": f"{x}_{y}", "bounds": [x, y, x + size, y + size]}


def validate_raster(path, bands, bounds, resolution):
    import rasterio

    with rasterio.open(path) as ds:
        expected = round((bounds[2] - bounds[0]) / resolution)
        if ds.count != len(bands) + 1 or ds.width != expected or ds.height != expected:
            raise ValueError(f"Unexpected raster dimensions/bands: {path}")
        if ds.crs.to_epsg() != 32632 or tuple(ds.bounds) != tuple(bounds):
            raise ValueError(f"Unexpected raster grid: {path}")
        ds.read(1, window=((0, 1), (0, 1)))


def compress_raster(source, target):
    """Lossless compression, including validity bits and zero-filled margins."""
    import rasterio

    with rasterio.open(source) as src:
        profile = src.profile | {
            "compress": "deflate",
            "predictor": 3 if src.dtypes[0] == "float32" else 2,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        }
        with rasterio.open(target, "w", **profile) as dst:
            for _, window in src.block_windows(1):
                dst.write(src.read(window=window), window=window)
            dst.descriptions = src.descriptions


def archive_order(jobs):
    """Interleave sensor-years; ordering never excludes an acquisition."""
    groups = defaultdict(deque)
    for job in sorted(jobs, key=lambda j: (-j["acquired_ms"], j["relative_path"])):
        year = datetime.fromtimestamp(job["acquired_ms"] / 1000, timezone.utc).year
        groups[(job["source"], year)].append(job)
    ordered = []
    while groups:
        for key in list(sorted(groups)):
            ordered.append(groups[key].popleft())
            if not groups[key]:
                del groups[key]
    return ordered


def download_job(job, destination, minimum_free_gib, region=None):
    import ee
    import requests

    target = destination / job["relative_path"]
    receipt = target.with_suffix(".receipt.json")
    if target.exists() and receipt.exists():
        record = json.loads(receipt.read_text())
        if target.stat().st_size == record["bytes"] and digest(target) == record["sha256"]:
            return "existing"
        raise ValueError(f"Existing archive file failed hash check: {target}")
    if shutil.disk_usage(destination).free < minimum_free_gib * 1024**3:
        raise RuntimeError("Disk reserve reached; resume after freeing space")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".tif.part")
    x, y, xmax, ymax = job["bounds"]
    resolution = job["resolution"]
    image = ee.Image(job["asset_id"]).select(job["bands"])
    if region is not None:
        image = image.clip(region)
    # Preserve stored optical DN/QA and SAR dB/angle values. No radiometric
    # normalisation, cloud masking, terrain flattening, or interpolation here.
    validity = (
        image.mask()
        .multiply(ee.Image.constant([2**i for i in range(len(job["bands"]))]))
        .reduce(ee.Reducer.sum())
        .rename("valid_bits")
    )
    image = image.unmask(0, sameFootprint=False).addBands(validity.unmask(0, sameFootprint=False))
    image = image.toFloat() if job["source"] == "s1" else image.toUint16()
    last_error = None
    for attempt in range(4):
        try:
            url = image.getDownloadURL(
                {
                    "bands": [*job["bands"], "valid_bits"],
                    "crs": "EPSG:32632",
                    "crs_transform": [resolution, 0, x, 0, -resolution, ymax],
                    "dimensions": [round((xmax - x) / resolution), round((ymax - y) / resolution)],
                    "format": "GEO_TIFF",
                    "filePerBand": False,
                }
            )
            with requests.get(url, stream=True, timeout=(30, 180)) as response:
                response.raise_for_status()
                with partial.open("wb") as output:
                    for block in response.iter_content(1024 * 1024):
                        output.write(block)
            validate_raster(partial, job["bands"], job["bounds"], resolution)
            packed = target.with_suffix(".packed.tif")
            compress_raster(partial, packed)
            validate_raster(packed, job["bands"], job["bounds"], resolution)
            packed.replace(target)
            partial.unlink()
            write_json(
                receipt,
                job
                | {
                    "bytes": target.stat().st_size,
                    "sha256": digest(target),
                    "downloaded_utc": datetime.now(timezone.utc).isoformat(),
                },
            )
            return "downloaded"
        except Exception as error:
            last_error = f"{type(error).__name__}: {str(error).split('https://')[0]}"
            partial.unlink(missing_ok=True)
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(last_error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="limburg-511403")
    parser.add_argument("--start-year", type=int, default=2009)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--destination", type=Path, default=DEST)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--minimum-free-gib", type=float, default=60)
    parser.add_argument(
        "--limit", type=int, help="Optional smoke-test job limit; omit for full archive"
    )
    args = parser.parse_args()
    # Some local venvs inherit conda pyproj but not its data-directory setting.
    proj = Path(sys.base_prefix) / "share/proj"
    if "PROJ_DATA" not in os.environ and (proj / "proj.db").exists():
        os.environ["PROJ_DATA"] = str(proj)
    import ee
    import geopandas as gpd
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform

    ee.Initialize(project=args.project)
    frame = gpd.read_file(ROOT / "data/interim/foundation_model_catchments.gpkg")
    frame = frame[frame.experiment_role != "inventory"].to_crs(32632)
    geometry = frame.geometry.union_all().buffer(1000)
    geo_wgs84 = transform(Transformer.from_crs(32632, 4326, always_xy=True).transform, geometry)
    region = ee.Geometry(geo_wgs84.__geo_interface__)
    tiles = list(tiles_for_geometry(geometry))
    destination = args.destination
    destination.mkdir(parents=True, exist_ok=True)
    spec = {
        "schema": 1,
        "project": args.project,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "gauges": frame.gauge.tolist(),
        "geometry_sha256": hashlib.sha256(geometry.wkb).hexdigest(),
        "buffer_m": 1000,
        "crs": "EPSG:32632",
        "tiles": tiles,
        "sources": SOURCES,
        "cloud_filter": None,
        "event_selection": "all dates, no event sampling",
        "storage": "native-resolution spectral band groups; nearest-neighbour UTM regridding; DN/QA or SAR dB; final valid_bits band marks validity of each preceding band; zero fill is not valid without its bit; S1 incidence angle is ancillary coarse data resampled to the radar grid",
        "code_sha256": digest(Path(__file__)),
    }
    spec_path = destination / "acquisition_spec.json"
    if spec_path.exists():
        prior = json.loads(spec_path.read_text())
        for key in ("geometry_sha256", "start_year", "end_year"):
            if prior[key] != spec[key]:
                raise ValueError(
                    f"Archive specification changed: {key}; use a separate destination"
                )
    write_json(spec_path, spec)
    scenes = []
    for source, (collection, _) in SOURCES.items():
        for year in range(args.start_year, args.end_year + 1):
            catalogue = destination / "catalogues" / f"{source}_{year}.json"
            if catalogue.exists():
                records = json.loads(catalogue.read_text())
            else:
                images = (
                    ee.ImageCollection(collection)
                    .filterBounds(region)
                    .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
                )
                if source == "s1":
                    images = (
                        images.filter(ee.Filter.eq("instrumentMode", "IW"))
                        .filter(ee.Filter.eq("resolution_meters", 10))
                        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
                    )
                records = ee.FeatureCollection(
                    images.map(
                        lambda image: ee.Feature(
                            image.geometry(),
                            image.toDictionary(METADATA).set("asset_id", image.id()),
                        )
                    )
                ).getInfo()["features"]
                write_json(catalogue, records)
            scenes.extend({"source": source, **record} for record in records)
            print(f"catalogue {source} {year}: {len(records)} scenes", flush=True)
    jobs = []
    project_shape = Transformer.from_crs(4326, 32632, always_xy=True).transform
    from shapely.geometry import box

    for scene in scenes:
        props = scene["properties"]
        footprint = transform(project_shape, shape(scene["geometry"]))
        source = scene["source"]
        scene_id = props.get("system:index", scene.get("id"))
        asset_id = SOURCES[source][0] + "/" + scene_id
        for tile in tiles:
            if not box(*tile["bounds"]).intersects(footprint):
                continue
            for resolution, bands in SOURCES[source][1].items():
                jobs.append(
                    {
                        "source": source,
                        "asset_id": asset_id,
                        "acquired_ms": props["system:time_start"],
                        "metadata": props,
                        "bounds": tile["bounds"],
                        "resolution": resolution,
                        "bands": bands,
                        "relative_path": f"images/{source}/{scene_id}/{tile['id']}_{resolution}m.tif",
                    }
                )
    jobs = archive_order(jobs)
    write_json(destination / "jobs.json", jobs)
    raw_bytes = sum(
        (9600 // j["resolution"]) ** 2 * (len(j["bands"]) + 1) * (4 if j["source"] == "s1" else 2)
        for j in jobs
    )
    print(
        f"{len(scenes)} scenes; {len(tiles)} tiles; {len(jobs)} files; "
        f"{raw_bytes / 1024**3:.1f} GiB uncompressed raster estimate",
        flush=True,
    )
    if not args.download:
        return 0
    counts = {"downloaded": 0, "existing": 0, "failed": 0}
    selected = jobs if args.limit is None else jobs[: args.limit]
    iterator = iter(selected)
    consecutive_failures = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        active = {}

        def replenish():
            while len(active) < args.workers:
                job = next(iterator, None)
                if job is None:
                    break
                active[
                    pool.submit(download_job, job, destination, args.minimum_free_gib, region)
                ] = job

        replenish()
        halted = False
        while active:
            completed, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in completed:
                job = active.pop(future)
                try:
                    status = future.result()
                    counts[status] += 1
                    consecutive_failures = 0
                except Exception as error:
                    counts["failed"] += 1
                    consecutive_failures += 1
                    write_json(
                        destination
                        / "errors"
                        / (hashlib.sha256(job["relative_path"].encode()).hexdigest() + ".json"),
                        {"job": job, "error": str(error).split("https://")[0]},
                    )
                    print(f"failed {job['relative_path']}: {str(error)[:180]}", flush=True)
                    if "Disk reserve reached" in str(error) or consecutive_failures >= 10:
                        halted = True
                write_json(
                    destination / "progress.json",
                    counts
                    | {
                        "planned_files": len(jobs),
                        "selected_files": len(selected),
                        "halted": halted,
                        "updated_utc": datetime.now(timezone.utc).isoformat(),
                    },
                )
                if sum(counts.values()) % 10 == 0:
                    print(counts, flush=True)
            if not halted:
                replenish()
    print(counts, flush=True)
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
