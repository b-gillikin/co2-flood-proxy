"""Inventory individual acquisitions for documented Meuse-basin CEMS AOIs.

No weekly composites and no pixel downloads. The three public Meuse-basin
AOIs are Venlo, Eschweiler and Wassenberg; other EMSR517 AOIs are not silently
treated as tributary cases. Records include all intersecting candidate scenes
in the stated window, not a performance-selected scene sample.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

BASE = ROOT / "data/raw/limburg_applied_tasks/local_references"
OUT = ROOT / "results/applied_study_v1/local_references"
AOIS = [
    (
        "EMSR520_AOI01",
        "Venlo",
        "NL",
        "2021-07-16T05:41:27Z",
        "Sentinel-1",
        "same-sensor reference; assess exact source overlap",
    ),
    (
        "EMSR517_AOI09",
        "Eschweiler",
        "DE",
        "2021-07-18T10:50:00Z",
        "Pleiades",
        "independent sensor; acquisition time mismatch still matters",
    ),
    (
        "EMSR517_AOI10",
        "Wassenberg",
        "DE",
        "2021-07-18T10:50:00Z",
        "Pleiades",
        "independent sensor; acquisition time mismatch still matters",
    ),
]


def metadata_files():
    receipts = []
    files = [
        ("main-tile-catalog.parquet", "geoid-flood-tile-catalog.parquet"),
        ("heldout-tile-catalog.parquet", "geoid-flood-heldout-tile-catalog.parquet"),
    ]
    # Exact repository paths are resolved through the dataset tree, rather
    # than inferred from informal filenames in the README.
    tree = json.load(
        urllib.request.urlopen(
            "https://huggingface.co/api/datasets/links-ads/geoid-flood/tree/main?recursive=true&limit=1000",
            timeout=60,
        )
    )
    catalogs = [r for r in tree if r["path"].endswith("tile_catalog.parquet")]
    for item in catalogs:
        heldout = "heldout" in item["path"].lower()
        dest = BASE / files[int(heldout)][1]
        url = "https://huggingface.co/datasets/links-ads/geoid-flood/resolve/main/" + item["path"]
        if not dest.exists():
            dest.write_bytes(urllib.request.urlopen(url, timeout=120).read())
        raw = dest.read_bytes()
        if len(raw) != item["size"]:
            raise ValueError("GEOID catalog size differs from source listing")
        receipts.append(
            dict(
                url=url,
                path=str(dest.relative_to(ROOT)),
                bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        )
        f = pd.read_parquet(dest)
        g = gpd.GeoDataFrame(f, geometry=gpd.GeoSeries.from_wkb(f.geometry), crs=4326)
        local = g.loc[g.event_id.isin(["EMSR517", "EMSR520"])]
        local.to_parquet(
            BASE
            / (
                "geoid-local-heldout-catalog.parquet"
                if heldout
                else "geoid-local-activation-catalog.parquet"
            ),
            index=False,
        )
    (OUT / "geoid-catalog-receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")


def scenes(collection, geometry, start, end, radar=False):
    col = ee.ImageCollection(collection).filterBounds(geometry).filterDate(start, end)
    if radar:
        col = (
            col.filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        )
    fields = ["system:index", "system:time_start", "system:footprint"]
    fields += (
        ["orbitProperties_pass", "relativeOrbitNumber_start", "platform_number"]
        if radar
        else ["CLOUDY_PIXEL_PERCENTAGE", "MGRS_TILE", "PRODUCT_ID"]
    )

    def record(image):
        # system:index is a reserved Feature ID and is omitted from returned
        # properties; retain the image identity under an ordinary property.
        return ee.Feature(None, image.toDictionary(fields)).set(
            "scene_id", image.get("system:index")
        )

    return [f["properties"] for f in col.map(record).getInfo()["features"]]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metadata_files()
    ee.Initialize(project="limburg-511403")
    inventory = []
    for prefix, name, country, observed, sensor, caveat in AOIS:
        (path,) = sorted(BASE.glob(prefix + "*_vector.zip"))
        with zipfile.ZipFile(path) as archive:
            (layer,) = [
                n for n in archive.namelist() if n.endswith(".shp") and "areaOfInterestA" in n
            ]
        frame = gpd.read_file(f"/vsizip/{path}/{layer}").to_crs(4326)
        geometry = frame.geometry.union_all()
        geojson = mapping(geometry)
        region = ee.Geometry(geojson)
        center = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        start = (center - timedelta(days=3)).date().isoformat()
        end = (center + timedelta(days=4)).date().isoformat()
        radar = scenes("COPERNICUS/S1_GRD", region, start, end, True)
        optical = scenes("COPERNICUS/S2_HARMONIZED", region, start, end)
        pre = scenes("COPERNICUS/S1_GRD", region, "2021-06-01", "2021-07-10", True)
        row = dict(
            aoi=prefix,
            name=name,
            country=country,
            geometry=geojson,
            reference_time=observed,
            reference_sensor=sensor,
            independence=caveat,
            source_archive=str(path.relative_to(ROOT)),
            event_window=dict(start_inclusive=start, end_exclusive=end),
            radar=radar,
            optical_l1c=optical,
            radar_pre=pre,
            policy="all catalogued scenes; intersecting footprint is not full valid coverage; dry/unknown reference coverage unresolved",
        )
        inventory.append(row)
        (OUT / "local-scene-inventory.json").write_text(
            json.dumps(dict(status="in_progress", aois=inventory), indent=2) + "\n"
        )
        print(
            json.dumps(dict(aoi=prefix, radar=len(radar), optical=len(optical), pre=len(pre))),
            flush=True,
        )
    (OUT / "local-scene-inventory.json").write_text(
        json.dumps(
            dict(
                status="complete",
                project="limburg-511403",
                created_utc=datetime.now(timezone.utc).isoformat(),
                aois=inventory,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
