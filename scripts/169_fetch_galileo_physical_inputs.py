"""Small exact-product Galileo extension: SRTM terrain and monthly ERA5-Land.

Default inventories requests; --download uses the existing Earth Engine project.
No discharge/labels are read, and signed download URLs are never logged.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--project", default="limburg-511403")
    args = parser.parse_args()
    os.environ.setdefault(
        "PROJ_DATA", "/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj"
    )
    import geopandas as gpd
    from pyproj import Transformer
    from shapely.geometry import box

    catchments = gpd.read_file(ROOT / "results/eo_comparison_preparation/catchments.gpkg").to_crs(
        "EPSG:32632"
    )
    geometry = catchments.geometry.union_all()
    jobs = json.loads((ROOT / "data/raw/limburg_compact_eo/jobs.json").read_text())
    bounds = sorted({tuple(j["bounds"]) for j in jobs if geometry.intersects(box(*j["bounds"]))})
    dest = ROOT / "data/raw/limburg_galileo_physical"
    dest.mkdir(parents=True, exist_ok=True)
    recipe = {
        "era5_collection": "ECMWF/ERA5_LAND/MONTHLY_AGGR",
        "climate_bands": ["temperature_2m", "total_precipitation_sum"],
        "period": ["2009-01-01", "2026-01-01"],
        "terrain": "USGS/SRTMGL1_003",
        "terrain_bands": ["elevation", "slope"],
        "bounds": bounds,
        "project": args.project,
    }
    print("Plan:", len(bounds), "terrain tiles and one multiband monthly climate image", flush=True)
    if not args.download:
        return
    import ee

    ee.Initialize(project=args.project)
    records = []

    def fetch(name, image, params, source):
        p = dest / name
        receipt = p.with_suffix(".receipt.json")
        if p.exists() and receipt.exists():
            r = json.loads(receipt.read_text())
            assert sha256(p) == r["sha256"]
            records.append(r)
            return
        url = image.getDownloadURL(
            {"name": p.stem, "format": "GEO_TIFF", "filePerBand": False, **params}
        )
        tmp = p.with_suffix(".partial")
        with urllib.request.urlopen(url, timeout=240) as stream, tmp.open("wb") as output:
            while block := stream.read(1024 * 1024):
                output.write(block)
        import rasterio

        with rasterio.open(tmp) as raster:
            if raster.count < 2:
                raise ValueError("Physical input has insufficient bands")
            description = list(raster.descriptions)
        tmp.replace(p)
        r = {
            "path": str(p.relative_to(ROOT)),
            "sha256": sha256(p),
            "bytes": p.stat().st_size,
            "source": source,
            "bands": description,
            "downloaded_utc": datetime.now(timezone.utc).isoformat(),
        }
        receipt.write_text(json.dumps(r, indent=2) + "\n")
        records.append(r)
        print("verified", name, flush=True)

    tr = Transformer.from_crs(32632, 4326, always_xy=True)
    elevation = ee.Image(recipe["terrain"]).select("elevation")
    terrain = elevation.addBands(ee.Terrain.slope(elevation).rename("slope")).toFloat()
    for b in bounds:
        x, y = b[0], b[1]
        region = ee.Geometry.Rectangle(list(b), proj="EPSG:32632", geodesic=False)
        fetch(
            f"srtm_{int(x)}_{int(y)}.tif",
            terrain,
            {"region": region, "crs": "EPSG:32632", "crs_transform": [30, 0, x, 0, -30, b[3]]},
            recipe["terrain"],
        )
    b = geometry.bounds
    lon0, lat0 = tr.transform(b[0], b[1])
    lon1, lat1 = tr.transform(b[2], b[3])
    region = ee.Geometry.Rectangle(
        [lon0 - 0.15, lat0 - 0.15, lon1 + 0.15, lat1 + 0.15], geodesic=False
    )
    climate = (
        ee.ImageCollection(recipe["era5_collection"])
        .filterDate(*recipe["period"])
        .select(recipe["climate_bands"])
        .toBands()
        .toFloat()
    )
    fetch(
        "era5_monthly_2009_2025.tif",
        climate,
        {"region": region, "crs": "EPSG:4326", "scale": 11132},
        recipe["era5_collection"],
    )
    names = climate.bandNames().getInfo()
    climate_receipt = dest / "era5_monthly_2009_2025.receipt.json"
    record = json.loads(climate_receipt.read_text())
    if len(names) != 408:
        raise ValueError("Unexpected monthly ERA5 band count")
    record["bands"] = names
    climate_receipt.write_text(json.dumps(record, indent=2) + "\n")
    records[-1] = record
    for record in records[:-1]:
        record["bands"] = ["elevation", "slope"]
        (ROOT / record["path"]).with_suffix(".receipt.json").write_text(
            json.dumps(record, indent=2) + "\n"
        )
    (dest / "manifest.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "recipe": recipe,
                "files": records,
                "code_sha256": sha256(Path(__file__)),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
