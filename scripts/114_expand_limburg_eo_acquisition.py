"""Acquire additional held-catalogue EO sources without mutating the running archive.

All existing assessment windows and spatial tiles; separate SAR orbits, Landsat
sensors and S2 TOA bands. No outcome-based scene selection or automatic model use.
"""

import argparse
import bisect
import fcntl
import hashlib
import importlib.util
import json
import shutil
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/limburg_eo_expansion"
SPEC = importlib.util.spec_from_file_location(
    "held_acquisition", ROOT / "scripts/95_acquire_limburg_satellite_archive.py"
)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
LANDSAT_BANDS = {
    "old": ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"],
    "new": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
}
NAMES = ["blue", "green", "red", "nir", "swir1", "swir2"]


def route(record):
    source = record["source"]
    if source == "s1":
        p = record["properties"]
        direction, orbit = p.get("orbitProperties_pass"), p.get("relativeOrbitNumber_start")
        if direction not in {"ASCENDING", "DESCENDING"} or orbit is None:
            raise ValueError("Radar scene lacks orbit identity")
        if direction == "ASCENDING" and orbit == 88:
            return []  # Already fully held in the original archive.
        return [
            (
                f"s1_{direction.lower()}_{orbit}",
                ["VV", "VH", "angle", "acquired_day"],
                10,
                "float32",
            )
        ]
    if source.startswith("landsat"):
        return [
            (
                source + "_sr",
                [*NAMES, "QA_PIXEL", "QA_RADSAT", "sensor_id", "acquired_day"],
                30,
                "float32",
            )
        ]
    if source == "s2_toa":
        return [
            ("s2_toa_10m", ["B2", "B3", "B4", "B8", "acquired_day"], 10, "uint16"),
            ("s2_toa_20m", ["B5", "B6", "B7", "B8A", "B11", "B12", "acquired_day"], 20, "uint16"),
            ("s2_toa_qa60", ["QA60", "acquired_day"], 60, "uint16"),
        ]
    return []


def plan(destination):
    from pyproj import Transformer
    from shapely.geometry import box, shape
    from shapely.ops import transform

    contexts_path = ROOT / "results/eo_comparison_preparation/contexts.json"
    windows = {w["id"]: w for c in json.loads(contexts_path.read_text()) for w in c["windows"]}
    original = ROOT / "data/raw/limburg_compact_eo/jobs.json"
    tiles = sorted({tuple(j["bounds"]) for j in json.loads(original.read_text())})
    project = Transformer.from_crs(4326, 32632, always_xy=True).transform
    records, hashes = [], {}
    for source in ["s1", "s2_toa", "landsat5", "landsat7", "landsat8", "landsat9"]:
        for year in range(2009, 2026):
            candidates = [
                ROOT / f"data/raw/limburg_compact_eo/catalogues/{source}_{year}.json",
                ROOT / f"data/raw/limburg_satellite_archive/catalogues/{source}_{year}.json",
            ]
            path = next((p for p in candidates if p.exists()), None)
            if path is None:
                # Missing catalogue is not declared no acquisition. Fail and recover it.
                raise FileNotFoundError(f"Missing held catalogue {source} {year}")
            hashes[str(path.relative_to(ROOT))] = A.digest(path)
            for feature in json.loads(path.read_text()):
                record = {**feature, "source": source}
                settings = route(record)
                if settings:
                    p = feature["properties"]
                    records.append(
                        (
                            p["system:time_start"],
                            source,
                            A.SOURCES[source][0] + "/" + p.get("system:index", feature.get("id")),
                            p,
                            transform(project, shape(feature["geometry"])),
                            settings,
                        )
                    )
    records.sort(key=lambda r: r[0])
    times = [r[0] for r in records]
    jobs = []
    for window in sorted(windows.values(), key=lambda w: (w["kind"] != "recent", w["start"])):
        start = datetime.fromisoformat(window["start"]).timestamp() * 1000
        end = datetime.fromisoformat(window["end"]).timestamp() * 1000
        selected = records[bisect.bisect_left(times, start) : bisect.bisect_left(times, end)]
        grouped = {}
        for record in selected:
            for settings in record[-1]:
                grouped.setdefault(
                    tuple([settings[0], tuple(settings[1]), *settings[2:]]), []
                ).append(record)
        for (product, bands, resolution, dtype), group in sorted(grouped.items()):
            for bounds in tiles:
                overlapping = [r for r in group if r[4].intersection(box(*bounds)).area > 0]
                if not overlapping:
                    continue
                source = group[0][1]
                jobs.append(
                    {
                        "source": source,
                        "product": product,
                        "bands": list(bands),
                        "resolution": resolution,
                        "dtype": dtype,
                        "window": window,
                        "bounds": list(bounds),
                        "asset_ids": [r[2] for r in overlapping],
                        "acquisition_ms": [r[0] for r in overlapping],
                        "source_metadata": [r[3] for r in overlapping],
                        "relative_path": f"images/{window['id']}/{product}/{int(bounds[0])}_{int(bounds[1])}.tif",
                    }
                )
    # Weekly SAR first, then weekly optical, then every requested monthly window.
    jobs.sort(
        key=lambda j: (
            j["window"]["kind"] != "recent",
            j["source"] != "s1",
            j["product"] != "s1_descending_37",
            j["window"]["start"],
            j["relative_path"],
        )
    )
    if len({j["relative_path"] for j in jobs}) != len(jobs):
        raise ValueError("Duplicate expansion paths")
    hashes.update(
        {
            str(p.relative_to(ROOT)): A.digest(p)
            for p in [
                contexts_path,
                original,
                Path(__file__).resolve(),
                ROOT / "scripts/95_acquire_limburg_satellite_archive.py",
            ]
        }
    )
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_sha256": hashes,
        "windows": len(windows),
        "tiles": len(tiles),
        "planned_files": len(jobs),
        "files_by_product": dict(Counter(j["product"] for j in jobs)),
        "uncompressed_bytes": sum(
            (9600 // j["resolution"]) ** 2
            * (len(j["bands"]) + 1)
            * (4 if j["dtype"] == "float32" else 2)
            for j in jobs
        ),
        "selection": "All held-catalogue scenes overlapping the existing windows and tiles; no outcome selection.",
        "radar": "Separate direction/relative-orbit products, VV/VH dB and angle. Ascending 88 already held, not duplicated.",
        "landsat": "Per-sensor six-band surface reflectance scaled 0.0000275*x-0.2, QA_PIXEL/QA_RADSAT, sensor identity. Latest clear valid pixel, excluding fill/dilated cloud/cirrus/cloud/shadow/saturation; retain snow/water.",
        "toa": "S2 harmonized L1C DN at native spectral resolutions, separate from surface reflectance. Latest valid pixel; no cloud-free claim. QA60 separate because its availability changes over time.",
        "scope": "Supplemental acquisition only; no automatic replacement, pooling of SAR orbits, model rerun or event-definition change.",
    }
    existing = destination / "plan.json"
    if existing.exists() and json.loads(existing.read_text())["input_sha256"] != hashes:
        raise ValueError(
            "Expansion inputs changed; preserve existing ledger and use a separate destination"
        )
    A.write_json(destination / "jobs.json", jobs)
    A.write_json(existing, report)
    return report


def composite(ee, job):
    def prepare(asset):
        image = ee.Image(asset)
        source = job["source"]
        if source == "s1":
            data = image.select(["VV", "VH", "angle"])
        elif source.startswith("landsat"):
            quality, saturation = image.select("QA_PIXEL"), image.select("QA_RADSAT")
            clear = quality.bitwiseAnd(31).eq(0).And(saturation.eq(0))
            data = image.select(
                LANDSAT_BANDS["old" if source in {"landsat5", "landsat7"} else "new"], NAMES
            )
            data = data.multiply(0.0000275).add(-0.2).addBands(quality).addBands(saturation)
            data = data.addBands(
                ee.Image.constant(int(source.removeprefix("landsat"))).rename("sensor_id")
            ).updateMask(clear)
        else:
            data = image.select([b for b in job["bands"] if b != "acquired_day"])
        # Native UTC epoch days and source timestamps are both retained.
        day = ee.Image.constant(ee.Number(image.get("system:time_start")).divide(86400000)).rename(
            "acquired_day"
        )
        return data.addBands(day.updateMask(data.mask().reduce(ee.Reducer.min()))).toDouble()

    return (
        ee.ImageCollection([prepare(a) for a in job["asset_ids"]])
        .qualityMosaic("acquired_day")
        .select(job["bands"])
    )


def download(args):
    import ee

    ee.Initialize(project=args.project)
    region = ee.Geometry(json.loads((ROOT / "data/raw/limburg_compact_eo/roi.geojson").read_text()))
    jobs = json.loads((args.destination / "jobs.json").read_text())
    if args.smoke:
        chosen = {}
        for job in jobs:
            chosen.setdefault(job["product"], job)
        jobs = list(chosen.values())
    counts = {"downloaded": 0, "existing": 0, "failed": 0}
    failed_jobs = []
    started = datetime.now(timezone.utc).isoformat()
    iterator = iter(jobs)
    state = {"status": "running", "planned_files": len(jobs), "started_utc": started}

    progress_path = args.destination / ("smoke-progress.json" if args.smoke else "progress.json")

    def save():
        A.write_json(
            progress_path,
            {
                **state,
                **counts,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
                "failed_jobs": failed_jobs,
            },
        )

    save()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        active = {}

        def replenish():
            while len(active) < args.workers:
                if shutil.disk_usage(args.destination).free < args.minimum_free_gib * 2**30:
                    state["status"] = "paused_disk_reserve"
                    break
                job = next(iterator, None)
                if job is None:
                    break
                image = composite(ee, job)
                active[
                    pool.submit(
                        A.download_job, job, args.destination, args.minimum_free_gib, region, image
                    )
                ] = job

        replenish()
        while active:
            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                job = active.pop(future)
                try:
                    result = future.result()
                    counts[result] += 1
                except Exception as error:
                    counts["failed"] += 1
                    failed_jobs.append(job["relative_path"])
                    A.write_json(
                        args.destination
                        / "errors"
                        / (hashlib.sha256(job["relative_path"].encode()).hexdigest() + ".json"),
                        {"job": job["relative_path"], "error": str(error).split("https://")[0]},
                    )
                save()
            replenish()
    if state["status"] == "running":
        state["status"] = "completed" if not failed_jobs else "completed_with_errors"
    save()
    return int(state["status"] != "completed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEST)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--download", action="store_true")
    modes.add_argument(
        "--smoke",
        action="store_true",
        help="Download one real job per product before the full census",
    )
    parser.add_argument("--project", default="limburg-511403")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--minimum-free-gib", type=float, default=60)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    with (args.destination / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not (args.download or args.smoke):
            print(json.dumps(plan(args.destination), indent=2))
            return 0
        manifest = json.loads((args.destination / "plan.json").read_text())
        for path, digest in manifest["input_sha256"].items():
            if A.digest(ROOT / path) != digest:
                raise ValueError("Expansion provenance changed: " + path)
        return download(args)


if __name__ == "__main__":
    raise SystemExit(main())
