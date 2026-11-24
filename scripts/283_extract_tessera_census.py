"""Stream and aggregate native TESSERA embeddings for the full Limburg census."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import resource
import shutil
import sys
import time
from importlib.metadata import version
from pathlib import Path
from subprocess import run

import geopandas as gpd
import numpy as np
import zarr
from exactextract import exact_extract
from exactextract.raster import NumPyRasterSource
from geotessera.icechunk import _years, open_session
from geotessera.zarr import valid_scale_mask

HELPER_PATH = Path(__file__).with_name("282_pilot_tessera.py")
HELPER_SPEC = importlib.util.spec_from_file_location("limburg_tessera_pilot", HELPER_PATH)
HELPER = importlib.util.module_from_spec(HELPER_SPEC)
HELPER_SPEC.loader.exec_module(HELPER)
BANDS, PIXEL_M, WINDOW = HELPER.BANDS, HELPER.PIXEL_M, HELPER.WINDOW
ROOT, CONFIG = HELPER.ROOT, HELPER.CONFIG
window_index, zone_basins = HELPER.window_index, HELPER.zone_basins


SNAPSHOT = "VTS86NCZ0NT7DK59V390"
BASE = ROOT / "results/limburg_representation_extension_v1"
GEOMETRY = ROOT / "results/limburg_representation_extension_v1/catchments.gpkg"
CHECKPOINT_EVERY = 50


def atomic_npz(path, **arrays):
    temporary = path.with_name(path.name + ".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    os.replace(temporary, path)


def extract_zone(group, basins, checkpoint, identity, year):
    attrs = group.attrs
    pixel, x_skew, west, y_skew, neg_pixel, top = attrs["spatial:transform"]
    if (pixel, x_skew, y_skew, neg_pixel) != (PIXEL_M, 0, 0, -PIXEL_M):
        raise ValueError("Expected the published north-up 10 m zone grid")
    if attrs["proj:code"] != basins.crs.to_string() or year not in attrs["years_complete"]:
        raise ValueError(f"Expected a complete {year} group in the catchment piece CRS")
    year_index = _years(group["time"]).index(year)
    embeddings, scales = group["embeddings"], group["scales"]
    if (
        embeddings.metadata.dimension_names != ("time", "northing", "easting", "band")
        or scales.metadata.dimension_names != ("time", "northing", "easting")
        or embeddings.shape != (*scales.shape, BANDS)
        or embeddings.dtype != np.int8
    ):
        raise ValueError("Unexpected TESSERA embedding array layout")
    height, width = scales.shape[1:]
    basins = basins.sort_index()
    gauge_ids = list(basins.index)
    gauge_index = {gauge: index for index, gauge in enumerate(gauge_ids)}
    areas = basins.area.to_numpy(dtype=np.float64)
    sums = np.zeros((len(gauge_ids), BANDS), dtype=np.float64)
    squares = np.zeros_like(sums)
    totals = np.zeros((len(gauge_ids), 5), dtype=np.float64)
    windows = window_index(basins, west, top, height, width, WINDOW)
    ordered_windows = sorted(windows.items())
    blank = np.ones((WINDOW, WINDOW), dtype=np.uint8)
    wkt = basins.crs.to_wkt()
    first_window = 0
    pixels_read = local_bytes_read = shared_windows = 0
    read_seconds = elapsed_before = 0.0

    if checkpoint.exists():
        with np.load(checkpoint, allow_pickle=False) as saved:
            saved_identity = str(saved["identity"].item())
            if saved_identity != json.dumps(identity, sort_keys=True):
                raise ValueError(f"Run identity changed for {checkpoint}")
            if list(saved["gauge_ids"].astype(str)) != gauge_ids:
                raise ValueError(f"Catchment order changed for {checkpoint}")
            first_window = int(saved["completed_windows"])
            if int(saved["total_windows"]) != len(ordered_windows):
                raise ValueError(f"Window inventory changed for {checkpoint}")
            sums, squares, totals = saved["sums"], saved["squares"], saved["totals"]
            pixels_read = int(saved["pixels_read"])
            local_bytes_read = int(saved["local_bytes_read"])
            shared_windows = int(saved["shared_windows"])
            read_seconds = float(saved["read_seconds"])
            elapsed_before = float(saved["elapsed_seconds"])
    if not 0 <= first_window <= len(ordered_windows):
        raise ValueError("Invalid checkpoint window index")

    started = time.monotonic()
    for position in range(first_window, len(ordered_windows)):
        (row, col), gauges = ordered_windows[position]
        r0, c0 = row * WINDOW, col * WINDOW
        r1, c1 = min(r0 + WINDOW, height), min(c0 + WINDOW, width)
        raster = NumPyRasterSource(
            blank[: r1 - r0, : c1 - c0],
            west + c0 * PIXEL_M,
            top - r1 * PIXEL_M,
            west + c1 * PIXEL_M,
            top - r0 * PIXEL_M,
            srs_wkt=wkt,
        )
        weights = exact_extract(raster, basins.loc[gauges], ["cell_id", "coverage"])
        if any(len(item["properties"]["cell_id"]) for item in weights):
            shared_windows += len(gauges) > 1
            read_started = time.monotonic()
            scale = scales[year_index, r0:r1, c0:c1].ravel()
            codes = embeddings[year_index, r0:r1, c0:c1, :].reshape(-1, BANDS)
            read_seconds += time.monotonic() - read_started
            pixels_read += len(scale)
            local_bytes_read += scale.nbytes + codes.nbytes
            valid = valid_scale_mask(scale)
            for gauge, feature in zip(gauges, weights, strict=True):
                index = gauge_index[gauge]
                cells = feature["properties"]["cell_id"]
                cell_areas = feature["properties"]["coverage"] * PIXEL_M**2
                keep = valid[cells]
                nodata = np.isnan(scale[cells])
                selected = cells[keep]
                area = cell_areas[keep]
                decoded = codes[selected].astype(np.float32) * scale[selected, None]
                sums[index] += np.einsum("ij,i->j", decoded, area, dtype=np.float64)
                squares[index] += np.einsum(
                    "ij,ij,i->j", decoded, decoded, area, dtype=np.float64
                )
                totals[index] += [
                    cell_areas.sum(),
                    area.sum(),
                    cell_areas[nodata].sum(),
                    cell_areas[~(keep | nodata)].sum(),
                    len(selected),
                ]

        completed = position + 1
        if completed % CHECKPOINT_EVERY == 0 or completed == len(ordered_windows):
            atomic_npz(
                checkpoint,
                identity=np.asarray(json.dumps(identity, sort_keys=True)),
                gauge_ids=np.asarray(gauge_ids),
                completed_windows=np.asarray(completed),
                total_windows=np.asarray(len(ordered_windows)),
                sums=sums,
                squares=squares,
                totals=totals,
                pixels_read=np.asarray(pixels_read),
                local_bytes_read=np.asarray(local_bytes_read),
                shared_windows=np.asarray(shared_windows),
                read_seconds=np.asarray(read_seconds),
                elapsed_seconds=np.asarray(elapsed_before + time.monotonic() - started),
            )
            print(
                f"{year} {group.basename}: {completed}/{len(ordered_windows)} windows",
                flush=True,
            )

    result = {}
    for index, gauge in enumerate(gauge_ids):
        area, valid_area, nodata_area, invalid_area, pixel_count = totals[index]
        if not math.isclose(area, areas[index], rel_tol=1e-6):
            raise ValueError(f"Weighted areas do not reproduce {gauge}'s projected polygon")
        if not math.isclose(area, valid_area + nodata_area + invalid_area, rel_tol=1e-9):
            raise ValueError(f"Pixel validity accounting does not close for {gauge}")
        mean = sums[index] / valid_area if valid_area else np.full(BANDS, np.nan)
        if not np.isfinite(mean).all():
            raise ValueError(f"No finite full-census descriptor for {gauge}")
        result[gauge] = {
            "area_m2": float(area),
            "valid_m2": float(valid_area),
            "source_nodata_m2": float(nodata_area),
            "other_invalid_scale_m2": float(invalid_area),
            "coverage_fraction": float(valid_area / area),
            "valid_pixel_count": int(pixel_count),
            "weighted_sum": sums[index].tolist(),
            "weighted_sum_squares": squares[index].tolist(),
            "mean": mean.tolist(),
        }
    return {
        "group": group.basename,
        "source_run": attrs["runs"][str(year)]["run_id"],
        "planned_windows": len(ordered_windows),
        "completed_windows": len(ordered_windows),
        "shared_windows": int(shared_windows),
        "decoded_window_pixels": int(pixels_read),
        "local_array_bytes_read": int(local_bytes_read),
        "read_seconds": float(read_seconds),
        "elapsed_seconds": float(elapsed_before + time.monotonic() - started),
        "basins": result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default=SNAPSHOT)
    parser.add_argument("--year", type=int, choices=(2018, 2020), default=2018)
    args = parser.parse_args()
    if args.snapshot != SNAPSHOT:
        raise ValueError("This frozen descriptor run is pinned to its reviewed source and year")

    year = args.year
    output = BASE / ("tessera_census_v1" if year == 2018 else f"tessera_census_{year}")
    output.mkdir(parents=True, exist_ok=True)
    with (output / "worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config = json.loads(CONFIG.read_text())
        geometry_hash = hashlib.sha256(GEOMETRY.read_bytes()).hexdigest()
        runner_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        helper_hash = hashlib.sha256(HELPER_PATH.read_bytes()).hexdigest()
        identity = {
            "store": config["models"]["tessera"]["public_store"],
            "snapshot_id": args.snapshot,
            "year": args.year,
            "geometry_sha256": geometry_hash,
            "runner_sha256": runner_hash,
            "helper_sha256": helper_hash,
            "method": "pixelwise int8*scale decoding; exactextract area weights; 128-d area mean and second moment",
        }
        basins = gpd.read_file(GEOMETRY).set_index("gauge").sort_index()
        if len(basins) != 394 or not basins.index.is_unique or not basins.geometry.is_valid.all():
            raise ValueError("Expected the verified, valid 394-catchment processing census")
        basins.geometry = basins.geometry.segmentize(100).to_crs(epsg=4326)
        session = open_session(config["models"]["tessera"]["public_store"], snapshot_id=args.snapshot)
        if str(session.snapshot_id) != args.snapshot:
            raise ValueError("Opened source snapshot does not match the frozen run")
        root = zarr.open_group(session.store, mode="r", use_consolidated=False)
        started = time.monotonic()
        free_before = shutil.disk_usage(ROOT).free
        zones = []
        with zarr.config.set({"async.concurrency": 8}):
            for zone in (31, 32):
                checkpoint = output / f"checkpoint_{year}_{zone}N.npz"
                zones.append(
                    extract_zone(root[f"{zone}N"], zone_basins(basins, zone), checkpoint, identity, year)
                )

        census = {}
        for gauge, source in basins.iterrows():
            pieces = [zone["basins"][gauge] for zone in zones if gauge in zone["basins"]]
            area = sum(piece["area_m2"] for piece in pieces)
            valid_area = sum(piece["valid_m2"] for piece in pieces)
            weighted_sum = np.sum([piece["weighted_sum"] for piece in pieces], axis=0)
            weighted_squares = np.sum([piece["weighted_sum_squares"] for piece in pieces], axis=0)
            mean = weighted_sum / valid_area if valid_area else np.full(BANDS, np.nan)
            if not np.isfinite(mean).all():
                raise ValueError(f"Non-finite descriptor for {gauge}")
            census[gauge] = {
                "station": source["station"],
                "role": source["source_role"],
                "reference_area_km2": float(source["geometry_area_km2"]),
                "area_m2": area,
                "valid_m2": valid_area,
                "coverage_fraction": valid_area / area,
                "source_nodata_m2": sum(piece["source_nodata_m2"] for piece in pieces),
                "other_invalid_scale_m2": sum(piece["other_invalid_scale_m2"] for piece in pieces),
                "valid_pixel_count": sum(piece["valid_pixel_count"] for piece in pieces),
                "weighted_sum": weighted_sum.tolist(),
                "weighted_sum_squares": weighted_squares.tolist(),
                "mean": mean.tolist(),
                "zones": [zone["group"] for zone in zones if gauge in zone["basins"]],
            }

        receipt = {
            "status": "complete",
            **identity,
            "coverage_scan_reference": f"results/limburg_representation_extension_v1/tessera_coverage_v1/receipt_{year}_direct.json",
            "coverage_only": False,
            "packages": {
                package: version(package)
                for package in ("geotessera", "icechunk", "zarr", "exactextract", "geopandas", "numpy")
            },
            "elapsed_seconds": time.monotonic() - started,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == "darwin"
            else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "free_before_bytes": free_before,
            "free_after_bytes": shutil.disk_usage(ROOT).free,
            "zones": zones,
            "basins": census,
        }
        receipt_path = output / f"receipt_{year}_direct.json"
        temporary = receipt_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
        temporary.replace(receipt_path)

        run(
            [sys.executable, str(Path(__file__).with_name("284_validate_tessera_descriptors.py")),
             "--year", str(year)],
            check=True,
        )
        print(f"Full TESSERA census complete: {receipt_path}", flush=True)


if __name__ == "__main__":
    main()
