"""Measure native TESSERA reads, coverage, and catchment descriptors."""

import argparse
import fcntl
import hashlib
import json
import math
import resource
import shutil
import sys
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit

import geopandas as gpd
import icechunk
import numpy as np
import requests
import zarr
from exactextract import exact_extract
from exactextract.raster import NumPyRasterSource
from geotessera.icechunk import _years, open_session
from geotessera.zarr import valid_scale_mask
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/limburg_representation_extension_v1.json"
GAUGES = ("6.Q.18", "10.Q.29", "DEA10950", "DEA13140")
BANDS = 128
PIXEL_M = 10
WINDOW = 512


@contextmanager
def metered_http(store):
    """Count actual public object response bodies via a local read-only relay."""
    url = urlsplit(store)
    upstream = f"https://{url.netloc}.s3.us-west-2.amazonaws.com{url.path}"
    totals = {"response_body_bytes": 0, "get_requests": 0, "head_requests": 0}
    lock = threading.Lock()
    clients = threading.local()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def relay(self):
            if not hasattr(clients, "session"):
                clients.session = requests.Session()
            headers = {"Accept-Encoding": "identity"}
            if self.headers.get("Range"):
                headers["Range"] = self.headers["Range"]
            try:
                response = clients.session.request(
                    self.command, upstream + self.path, headers=headers, stream=True, timeout=60
                )
            except requests.RequestException:
                self.send_error(502)
                return
            with response:
                self.send_response(response.status_code)
                for name in (
                    "Content-Type",
                    "Content-Length",
                    "Content-Range",
                    "ETag",
                    "Last-Modified",
                ):
                    if name in response.headers:
                        self.send_header(name, response.headers[name])
                if "Content-Length" not in response.headers:
                    self.send_header("Connection", "close")
                    self.close_connection = True
                self.end_headers()
                length = 0
                try:
                    if self.command == "GET":
                        for block in response.raw.stream(256 * 1024, decode_content=False):
                            length += len(block)
                            self.wfile.write(block)
                finally:
                    with lock:
                        totals["response_body_bytes"] += length
                        totals[f"{self.command.lower()}_requests"] += 1

        do_GET = relay
        do_HEAD = relay

        def log_message(self, *_):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", totals
        finally:
            server.shutdown()
            thread.join()


def zone_basins(basins, zone):
    west = (zone - 31) * 6
    pieces = basins.copy()
    # Densify before changing CRS and along the newly cut meridian.
    pieces.geometry = pieces.geometry.intersection(box(west, 0, west + 6, 84))
    pieces = pieces.loc[~pieces.geometry.is_empty].copy()
    pieces.geometry = pieces.geometry.segmentize(0.001)
    return pieces.to_crs(epsg=32600 + zone)


def write_json(path, result):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def window_index(basins, west, top, height, width, window=WINDOW):
    covered = defaultdict(list)
    footprint = box(west, top - height * PIXEL_M, west + width * PIXEL_M, top)
    for gauge, geom in basins.geometry.items():
        if not footprint.covers(geom):
            raise ValueError(f"{gauge} extends outside the published zone raster")
        x0, y0, x1, y1 = geom.bounds
        col0 = math.floor((x0 - west) / PIXEL_M / window)
        col1 = math.ceil((x1 - west) / PIXEL_M / window)
        row0 = math.floor((top - y1) / PIXEL_M / window)
        row1 = math.ceil((top - y0) / PIXEL_M / window)
        for row in range(row0, row1):
            for col in range(col0, col1):
                x = west + col * window * PIXEL_M
                y = top - row * window * PIXEL_M
                if geom.intersects(box(x, y - window * PIXEL_M, x + window * PIXEL_M, y)):
                    covered[row, col].append(gauge)
    return covered


def accumulate_zone(group, basins, year, *, coverage_only=False, checkpoint=None, identity=None):
    attrs = group.attrs
    pixel, x_skew, west, y_skew, neg_pixel, top = attrs["spatial:transform"]
    if (pixel, x_skew, y_skew, neg_pixel) != (PIXEL_M, 0, 0, -PIXEL_M):
        raise ValueError("Expected a north-up provider grid with 10 m pixels")
    if attrs["proj:code"] != basins.crs.to_string() or year not in attrs["years_complete"]:
        raise ValueError(f"Expected a complete {year} group in the catchment piece's CRS")
    year_index = _years(group["time"]).index(year)
    emb, scales = group["embeddings"], group["scales"]
    if (
        emb.metadata.dimension_names != ("time", "northing", "easting", "band")
        or scales.metadata.dimension_names != ("time", "northing", "easting")
        or emb.shape != (*scales.shape, BANDS)
        or emb.dtype != np.int8
    ):
        raise ValueError("Unexpected provider embedding layout")
    height, width = scales.shape[1:]
    areas = basins.area
    sums = {g: np.zeros(BANDS, dtype=np.float64) for g in basins.index}
    squares = {g: np.zeros(BANDS, dtype=np.float64) for g in basins.index}
    totals = {g: np.zeros(5, dtype=np.float64) for g in basins.index}
    # Scale-only windows do not allocate the 128-channel pixel array.
    window = 1024 if coverage_only else WINDOW
    windows = window_index(basins, west, top, height, width, window)
    pixels_read = shared = raw_array_bytes = 0
    blank = np.ones((window, window), dtype=np.uint8)
    wkt = basins.crs.to_wkt()
    read_seconds = previous_seconds = 0.0
    done = 0
    if checkpoint and checkpoint.exists():
        saved = json.loads(checkpoint.read_text())
        if saved["identity"] != identity or saved["total_windows"] != len(windows):
            raise ValueError(f"Run identity changed for {checkpoint}")
        done = saved["completed_windows"]
        if not 0 <= done <= len(windows) or saved["totals"].keys() != totals.keys():
            raise ValueError(f"Invalid checkpoint membership in {checkpoint}")
        totals = {g: np.asarray(values, dtype=np.float64) for g, values in saved["totals"].items()}
        pixels_read = saved["pixels_read"]
        shared = saved["shared_windows"]
        raw_array_bytes = saved["local_array_bytes_read"]
        read_seconds = saved["read_seconds"]
        previous_seconds = saved["elapsed_seconds"]
        print(f"{year} {group.basename} resuming at {done}/{len(windows)}", flush=True)
    started = time.monotonic()
    for count, ((row, col), gauges) in enumerate(sorted(windows.items())[done:], done + 1):
        r0, c0 = row * window, col * window
        r1, c1 = min(r0 + window, height), min(c0 + window, width)
        raster = NumPyRasterSource(
            blank[: r1 - r0, : c1 - c0],
            west + c0 * PIXEL_M,
            top - r1 * PIXEL_M,
            west + c1 * PIXEL_M,
            top - r0 * PIXEL_M,
            srs_wkt=wkt,
        )
        weights = exact_extract(raster, basins.loc[gauges], ["cell_id", "coverage"])
        if any(len(feature["properties"]["cell_id"]) for feature in weights):
            shared += len(gauges) > 1
            reading = time.monotonic()
            scale = scales[year_index, r0:r1, c0:c1].ravel()
            codes = None if coverage_only else emb[year_index, r0:r1, c0:c1, :].reshape(-1, BANDS)
            read_seconds += time.monotonic() - reading
            pixels_read += len(scale)
            raw_array_bytes += scale.nbytes + (0 if codes is None else codes.nbytes)
            valid = valid_scale_mask(scale)
            for gauge, feature in zip(gauges, weights, strict=True):
                cells = feature["properties"]["cell_id"]
                cell_areas = feature["properties"]["coverage"] * PIXEL_M**2
                keep = valid[cells]
                nodata = np.isnan(scale[cells])
                verified = cells[keep]
                area = cell_areas[keep]
                if codes is not None:
                    decoded = codes[verified].astype(np.float32) * scale[verified, None]
                    sums[gauge] += np.einsum("ij,i->j", decoded, area, dtype=np.float64)
                    squares[gauge] += np.einsum(
                        "ij,ij,i->j", decoded, decoded, area, dtype=np.float64
                    )
                totals[gauge] += [
                    cell_areas.sum(),
                    area.sum(),
                    cell_areas[nodata].sum(),
                    cell_areas[~(keep | nodata)].sum(),
                    len(verified),
                ]
        interval = 10 if coverage_only else 5
        if count == 1 or count % interval == 0 or count == len(windows):
            if checkpoint:
                write_json(
                    checkpoint,
                    {
                        "identity": identity,
                        "completed_windows": count,
                        "total_windows": len(windows),
                        "pixels_read": pixels_read,
                        "shared_windows": shared,
                        "local_array_bytes_read": raw_array_bytes,
                        "read_seconds": read_seconds,
                        "elapsed_seconds": previous_seconds + time.monotonic() - started,
                        "totals": {g: value.tolist() for g, value in totals.items()},
                    },
                )
            print(f"{year} {group.basename} windows {count}/{len(windows)}", flush=True)
    stats = {}
    for gauge, (area, valid, nodata, other_invalid, pixel_count) in totals.items():
        if not math.isclose(area, areas[gauge], rel_tol=1e-6):
            raise ValueError(f"Weighted areas do not reproduce {gauge}'s projected polygon")
        if not math.isclose(area, valid + nodata + other_invalid, rel_tol=1e-9):
            raise ValueError(f"Pixel validity accounting does not close for {gauge}")
        stats[gauge] = {
            "area_m2": area,
            "valid_m2": valid,
            "source_nodata_m2": nodata,
            "other_invalid_scale_m2": other_invalid,
            "valid_pixel_count": int(pixel_count),
        }
        if not coverage_only:
            stats[gauge]["weighted_sum"] = sums[gauge].tolist()
            stats[gauge]["weighted_sum_squares"] = squares[gauge].tolist()
    return {
        "group": group.basename,
        "transform": attrs["spatial:transform"],
        "source_run": attrs["runs"][str(year)]["run_id"],
        "embedding_chunks": emb.chunks,
        "embedding_shards": emb.shards,
        "planned_windows": len(windows),
        "shared_windows": shared,
        "decoded_window_pixels": pixels_read,
        "local_array_bytes_read": raw_array_bytes,
        "read_seconds": read_seconds,
        "elapsed_seconds": previous_seconds + time.monotonic() - started,
        "basins": stats,
    }


def combine(gauge, zones, source):
    parts = [zone["basins"][gauge] for zone in zones if gauge in zone["basins"]]
    keys = (
        "area_m2",
        "valid_m2",
        "source_nodata_m2",
        "other_invalid_scale_m2",
        "valid_pixel_count",
    )
    result = {k: sum(part[k] for part in parts) for k in keys}
    result["coverage_fraction"] = result["valid_m2"] / result["area_m2"]
    if "weighted_sum" in parts[0]:
        for key in ("weighted_sum", "weighted_sum_squares"):
            result[key] = np.sum([part[key] for part in parts], axis=0).tolist()
        result["mean"] = (
            [v / result["valid_m2"] for v in result["weighted_sum"]] if result["valid_m2"] else None
        )
    return {
        "station": source.station,
        "role": source.source_role,
        "reference_area_km2": source.geometry_area_km2,
        "zones": [zone["group"] for zone in zones if gauge in zone["basins"]],
        **result,
    }


def run(snapshot, year, meter=None, *, coverage_only=False):
    config = json.loads(CONFIG.read_text())
    store = config["models"]["tessera"]["public_store"]
    geometry = ROOT / config["processing_catchments"]
    out = ROOT / config["output"] / ("tessera_coverage_v1" if coverage_only else "tessera_pilot_v1")
    out.mkdir(parents=True, exist_ok=True)
    basins = gpd.read_file(geometry).set_index("gauge")
    if coverage_only:
        if not basins.index.is_unique or len(basins) != config["study"]["reference_catchments"]:
            raise ValueError("Processing polygons differ from the declared census")
    else:
        basins = basins.loc[list(GAUGES)].copy()
    if not basins.geometry.is_valid.all():
        raise ValueError("TESSERA aggregation requires valid processing geometries")
    basins.geometry = basins.geometry.segmentize(100)
    basins = basins.to_crs(epsg=4326)
    free_before = shutil.disk_usage(ROOT).free
    started = time.monotonic()
    if meter is None:
        session = open_session(store, snapshot_id=snapshot)
        transfer = None
    else:
        endpoint, transfer = meter
        storage = icechunk.http_storage(endpoint, opts={"allow_http": "true"})
        repo = icechunk.Repository.open(storage)
        session = repo.readonly_session(snapshot_id=snapshot)
    root = zarr.open_group(session.store, mode="r", use_consolidated=False)
    print(f"Reading {year} snapshot {session.snapshot_id}", flush=True)
    identity = {
        "store": store,
        "snapshot_id": session.snapshot_id,
        "year": year,
        "geometry_sha256": hashlib.sha256(geometry.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    zones = []
    with zarr.config.set({"async.concurrency": 8}):
        for zone in (31, 32):
            checkpoint = out / f"checkpoint_{year}_{zone}N.json" if coverage_only else None
            zones.append(
                accumulate_zone(
                    root[f"{zone}N"],
                    zone_basins(basins, zone),
                    year,
                    coverage_only=coverage_only,
                    checkpoint=checkpoint,
                    identity=identity,
                )
            )
    # macOS's process peak RSS is reported in bytes. Linux reports KiB.
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {
        "status": "complete",
        **identity,
        "coverage_only": coverage_only,
        "packages": {
            p: version(p)
            for p in ("geotessera", "icechunk", "zarr", "exactextract", "geopandas", "numpy")
        },
        "window_pixels": 1024 if coverage_only else WINDOW,
        "elapsed_seconds": time.monotonic() - started,
        "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
        "http_transfer": transfer,
        "free_before_bytes": free_before,
        "free_after_bytes": shutil.disk_usage(ROOT).free,
        "zones": zones,
        "basins": {g: combine(g, zones, basins.loc[g]) for g in basins.index},
    }
    mode = "metered" if meter else "direct"
    name = f"receipt_{year}_{mode}.json"
    write_json(out / name, result)
    print(f"Pilot complete in {result['elapsed_seconds']:.1f}s: {out / name}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, help="Use this Icechunk snapshot")
    parser.add_argument("--year", type=int, choices=tuple(range(2017, 2026)), action="append")
    parser.add_argument("--meter-http", action="store_true", help="Count public S3 body bytes")
    parser.add_argument(
        "--census-coverage", action="store_true", help="Read scales for all 394 basins"
    )
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    directory = "tessera_coverage_v1" if args.census_coverage else "tessera_pilot_v1"
    out = ROOT / config["output"] / directory
    out.mkdir(parents=True, exist_ok=True)
    with (out / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for year in args.year or [2017]:
            if args.meter_http:
                with metered_http(config["models"]["tessera"]["public_store"]) as meter:
                    run(args.snapshot, year, meter, coverage_only=args.census_coverage)
            else:
                run(args.snapshot, year, coverage_only=args.census_coverage)


if __name__ == "__main__":
    main()
