"""Download individual local acquisitions on a fixed 10m grid, with receipts.

All event-window scenes from the reference inventory are retained. Radar pre-
event data are the closest available pre-window date per matching orbit/pass.
512px tiles intersect the AOI and source footprint; coverage is never invented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)

import ee
import numpy as np
import rasterio
from pyproj import Transformer
from shapely.geometry import box, shape
from shapely.ops import transform

BASE = ROOT / "data/raw/limburg_applied_tasks/local_scenes"
OUT = ROOT / "results/applied_study_v1/local_references"
BANDS = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B10", "B11", "B12"]


def prepare():
    source = OUT / "local-scene-inventory.json"
    state = json.loads(source.read_text())
    if state["status"] != "complete":
        raise ValueError("Local scene inventory is not complete")
    project = Transformer.from_crs(4326, 32631, always_xy=True).transform
    jobs, pairs = {}, []
    for a in state["aois"]:
        region = transform(project, shape(a["geometry"]))
        pres = {}
        for post in a["radar"]:
            candidates = [
                p
                for p in a["radar_pre"]
                if p["relativeOrbitNumber_start"] == post["relativeOrbitNumber_start"]
                and p["orbitProperties_pass"] == post["orbitProperties_pass"]
            ]
            if not candidates:
                pairs.append(
                    dict(aoi=a["aoi"], post=post["scene_id"], pre=[], status="no_same_orbit_pre")
                )
                continue
            date = max(p["system:time_start"] // 86400000 for p in candidates)
            selected = [p for p in candidates if p["system:time_start"] // 86400000 == date]
            for p in selected:
                pres[p["scene_id"]] = p
            pairs.append(
                dict(
                    aoi=a["aoi"],
                    post=post["scene_id"],
                    pre=[p["scene_id"] for p in selected],
                    status="same_orbit_closest_pre_date",
                )
            )
        for sensor, rows in [
            ("s1_event", a["radar"]),
            ("s1_pre", list(pres.values())),
            ("s2_event", a["optical_l1c"]),
        ]:
            for scene in rows:
                footprint = shape(scene["system:footprint"])
                if footprint.geom_type == "LinearRing":
                    from shapely.geometry import Polygon

                    footprint = Polygon(footprint)
                observed = region.intersection(transform(project, footprint))
                if observed.is_empty:
                    continue
                w, s, e, n = observed.bounds
                for x in range(math.floor(w / 5120) * 5120, math.ceil(e / 5120) * 5120, 5120):
                    for y in range(math.floor(s / 5120) * 5120, math.ceil(n / 5120) * 5120, 5120):
                        if observed.intersection(box(x, y, x + 5120, y + 5120)).area == 0:
                            continue
                        key = f"{a['aoi']}/{sensor}/{scene['scene_id']}/{x}_{y}.tif"
                        jobs[key] = dict(
                            path=key,
                            aoi=a["aoi"],
                            sensor=sensor,
                            scene=scene,
                            collection="COPERNICUS/S2_HARMONIZED"
                            if sensor.startswith("s2")
                            else "COPERNICUS/S1_GRD",
                            crs="EPSG:32631",
                            transform=[10, 0, x, 0, -10, y + 5120],
                            width=512,
                            height=512,
                            aoi_geometry=a["geometry"],
                            bands=BANDS + ["QA60", "source_valid"]
                            if sensor.startswith("s2")
                            else ["VV", "VH", "angle", "source_valid"],
                            resampling="Earth Engine default nearest; coarse bands retain native information support",
                            nodata=-9999,
                            composite=False,
                        )
    manifest = dict(
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        status="prepared",
        jobs=list(jobs.values()),
        pairs=pairs,
        upper_uncompressed_bytes=sum(512 * 512 * 4 * len(j["bands"]) for j in jobs.values()),
    )
    (OUT / "local-scene-jobs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def download(job):
    path = BASE / job["path"]
    receipt = path.with_suffix(".receipt.json")
    if path.exists():
        r = json.loads(receipt.read_text())
        if r["job"] != job or hashlib.sha256(path.read_bytes()).hexdigest() != r["sha256"]:
            raise ValueError("Existing local scene/receipt differs")
        return r
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        temp = path.with_suffix(".partial")
        try:
            while shutil.disk_usage(ROOT).free < 53 * 1024**3:
                time.sleep(10)
            image = ee.Image(job["collection"] + "/" + job["scene"]["scene_id"])
            physical = BANDS if job["sensor"].startswith("s2") else ["VV", "VH", "angle"]
            valid = image.select(physical).mask().reduce(ee.Reducer.min()).rename("source_valid")
            # Preserve QA60 bits separately; they do not become water labels.
            image = (
                image.select(job["bands"][:-1])
                .addBands(valid)
                .clip(ee.Geometry(job["aoi_geometry"]))
                .unmask(-9999)
                .toFloat()
            )
            url = image.getDownloadURL(
                dict(
                    crs=job["crs"],
                    crs_transform=job["transform"],
                    dimensions=[512, 512],
                    format="GEO_TIFF",
                    filePerBand=False,
                )
            )
            with urllib.request.urlopen(url, timeout=180) as stream, temp.open("wb") as dest:
                while block := stream.read(1024**2):
                    if shutil.disk_usage(ROOT).free < 51 * 1024**3:
                        raise RuntimeError("Disk reserve approached")
                    dest.write(block)
            with rasterio.open(temp) as ds:
                if (
                    ds.shape != (512, 512)
                    or ds.count != len(job["bands"])
                    or ds.crs.to_epsg() != 32631
                ):
                    raise ValueError("Local scene export grid/band count differs")
                if not np.allclose(tuple(ds.transform)[:6], job["transform"], atol=1e-8, rtol=0):
                    raise ValueError("Local scene affine differs")
            r = dict(
                job=job,
                bytes=temp.stat().st_size,
                sha256=hashlib.sha256(temp.read_bytes()).hexdigest(),
            )
            temp.replace(path)
            receipt.write_text(json.dumps(r, indent=2) + "\n")
            return r
        except Exception:
            temp.unlink(missing_ok=True)
            if attempt == 3:
                raise
            time.sleep(2**attempt)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    manifest = prepare()
    print(
        json.dumps(
            dict(
                jobs=len(manifest["jobs"]),
                upper_uncompressed_gib=manifest["upper_uncompressed_bytes"] / 1024**3,
            )
        ),
        flush=True,
    )
    if not args.download:
        return
    ee.Initialize(project="limburg-511403")
    progress = dict(status="running", total=len(manifest["jobs"]), completed=0, failures=[])
    with (
        (OUT / "local-scene-downloads.jsonl").open("a") as ledger,
        ThreadPoolExecutor(max_workers=3) as pool,
    ):
        futures = {pool.submit(download, j): j for j in manifest["jobs"]}
        for future in as_completed(futures):
            job = futures[future]
            try:
                ledger.write(json.dumps(future.result()) + "\n")
                ledger.flush()
                progress["completed"] += 1
            except Exception as exc:
                progress["failures"].append(dict(path=job["path"], error=str(exc)))
            progress["free_gib"] = shutil.disk_usage(ROOT).free / 1024**3
            (OUT / "local-scene-progress.json").write_text(json.dumps(progress, indent=2) + "\n")
    progress["status"] = "completed" if not progress["failures"] else "completed_with_failures"
    (OUT / "local-scene-progress.json").write_text(json.dumps(progress, indent=2) + "\n")


if __name__ == "__main__":
    main()
