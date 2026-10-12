"""Export catchment-year AlphaEarth means from Google Earth Engine.

The export is a small table, not imagery. Authentication and an Earth Engine
Cloud project are intentionally supplied at run time.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATCHMENTS = ROOT / "data/interim/foundation_model_catchments.gpkg"
COLLECTION = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
YEARS = tuple(range(2017, 2025))
BANDS = tuple(f"A{i:02d}" for i in range(64))


def alphaearth_year(event_year: int) -> int | None:
    """Prior-year information rule; None means outside the primary comparison."""
    if event_year < 2018:
        return None
    return min(event_year - 1, 2024)


def expected_output_columns() -> list[str]:
    return [
        "gauge",
        "gauge_name",
        "watercourse",
        "jurisdiction",
        "experiment_role",
        "embedding_year",
        "valid_pixel_count",
        "geometry_sha256",
        *BANDS,
    ]


def geometry_hash(geometry) -> str:
    return hashlib.sha256(geometry.wkb).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project", required=True, help="Google Cloud project enabled for Earth Engine"
    )
    parser.add_argument("--catchments", type=Path, default=DEFAULT_CATCHMENTS)
    parser.add_argument("--drive-folder", default="limburg_foundation_assets")
    parser.add_argument("--description", default="limburg_alphaearth_catchment_year_v1")
    args = parser.parse_args()

    import ee
    import geopandas as gpd

    ee.Initialize(project=args.project)
    frame = gpd.read_file(args.catchments).to_crs("EPSG:4326")
    features = []
    properties = ["gauge", "gauge_name", "watercourse", "jurisdiction", "experiment_role"]
    for _, row in frame.iterrows():
        props = {key: row[key] for key in properties}
        props["geometry_sha256"] = geometry_hash(row.geometry)
        features.append(ee.Feature(ee.Geometry(row.geometry.__geo_interface__), props))
    catchments = ee.FeatureCollection(features)

    annual_tables = []
    for year in YEARS:

        def add_embedding_year(feature, embedding_year=year):
            return feature.set("embedding_year", embedding_year)

        image = (
            ee.ImageCollection(COLLECTION)
            .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
            .mosaic()
            .select(list(BANDS))
        )
        means = image.reduceRegions(
            collection=catchments,
            reducer=ee.Reducer.mean(),
            scale=10,
            tileScale=4,
        ).map(add_embedding_year)
        counts = image.select("A00").reduceRegions(
            collection=catchments,
            reducer=ee.Reducer.count().setOutputs(["valid_pixel_count"]),
            scale=10,
            tileScale=4,
        )
        joined = ee.Join.saveFirst("count_feature").apply(
            means,
            counts,
            ee.Filter.equals(leftField="gauge", rightField="gauge"),
        )
        joined = ee.FeatureCollection(joined).map(
            lambda feature: feature.set(
                "valid_pixel_count",
                ee.Feature(feature.get("count_feature")).get("valid_pixel_count"),
            ).select(expected_output_columns())
        )
        annual_tables.append(joined)

    table = ee.FeatureCollection(annual_tables).flatten()
    task = ee.batch.Export.table.toDrive(
        collection=table,
        description=args.description,
        folder=args.drive_folder,
        fileNamePrefix=args.description,
        fileFormat="CSV",
        selectors=expected_output_columns(),
    )
    task.start()
    print(f"Earth Engine export started: {task.id}")
    print(task.status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
