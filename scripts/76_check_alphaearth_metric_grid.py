#!/usr/bin/env python3
"""Download a separate metric-grid AlphaEarth catchment table for projection QA."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "export", ROOT / "scripts/67_export_alphaearth_embeddings.py"
)
EXPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORT)
CRS = "EPSG:3035"
SCALE = 10
OUT = ROOT / "data/raw/foundation_assets/alphaearth/limburg_alphaearth_metric_grid_v2.csv"


def metric_table(ee, catchments):
    features = []
    fields = ["gauge", "gauge_name", "watercourse", "jurisdiction", "experiment_role"]
    for row in catchments.to_crs(4326).itertuples():
        properties = {column: getattr(row, column) for column in fields}
        properties["geometry_sha256"] = EXPORT.geometry_hash(row.geometry)
        features.append(ee.Feature(ee.Geometry(row.geometry.__geo_interface__), properties))
    regions = ee.FeatureCollection(features)
    tables = []
    for year in EXPORT.YEARS:
        image = (
            ee.ImageCollection(EXPORT.COLLECTION)
            .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
            .mosaic()
            .select(list(EXPORT.BANDS))
        )
        stats = image.reduceRegions(
            collection=regions,
            reducer=ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True),
            crs=CRS,
            scale=SCALE,
            tileScale=4,
        )

        def rename(feature, embedding_year=year):
            values = {band: feature.get(f"{band}_mean") for band in EXPORT.BANDS}
            values.update(
                embedding_year=embedding_year,
                valid_pixel_count=feature.get("A00_count"),
                aggregation_crs=CRS,
                aggregation_scale_m=SCALE,
            )
            return feature.set(values).select(
                EXPORT.expected_output_columns() + ["aggregation_crs", "aggregation_scale_m"]
            )

        tables.append(stats.map(rename))
    return ee.FeatureCollection(tables).flatten()


def validate_and_compare(path, catchments, out_dir):
    new = pd.read_csv(path)
    old_path = (
        EXPORT.ROOT
        / "data/raw/foundation_assets/alphaearth/limburg_alphaearth_catchment_year_v1.csv"
    )
    old = pd.read_csv(old_path)
    if new.duplicated(["gauge", "embedding_year"]).any() or set(
        zip(new.gauge, new.embedding_year, strict=True)
    ) != set(zip(old.gauge, old.embedding_year, strict=True)):
        raise ValueError("Metric aggregation must cover the identical catchment/year grid")
    geometry = catchments.to_crs(4326).set_index("gauge").geometry.map(EXPORT.geometry_hash)
    if not new.geometry_sha256.eq(new.gauge.map(geometry)).all():
        raise ValueError("Metric export geometry differs from its own verified source")
    if not new.aggregation_crs.eq(CRS).all() or not new.aggregation_scale_m.eq(SCALE).all():
        raise ValueError("Metric export projection/scale mismatch")
    bands = list(EXPORT.BANDS)
    if not np.isfinite(new[bands].to_numpy()).all() or not new.valid_pixel_count.gt(0).all():
        raise ValueError("Incomplete metric-grid embedding vectors")
    old = old.set_index(["gauge", "embedding_year"])
    new = new.set_index(["gauge", "embedding_year"]).loc[old.index]
    a, b = old[bands].to_numpy(), new[bands].to_numpy()
    norm_a, norm_b = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)
    if (norm_b == 0).any():
        raise ValueError("Undefined metric-grid catchment direction")
    normalized_a, normalized_b = a / norm_a[:, None], b / norm_b[:, None]
    comparisons = pd.DataFrame(
        {
            "old_pixel_count": old.valid_pixel_count,
            "metric_pixel_count": new.valid_pixel_count,
            "old_mean_norm": norm_a,
            "metric_mean_norm": norm_b,
            "direction_cosine": (normalized_a * normalized_b).sum(axis=1),
            "normalized_vector_distance": np.linalg.norm(normalized_a - normalized_b, axis=1),
            "largest_axis_mean_difference": np.max(np.abs(a - b), axis=1),
        }
    ).reset_index()
    comparisons["area_km2"] = comparisons.gauge.map(catchments.set_index("gauge").area_km2)
    comparisons["metric_count_area_ratio"] = comparisons.metric_pixel_count / (
        comparisons.area_km2 * 10000
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    comparisons.to_csv(out_dir / "projection_comparison.csv", index=False)
    new.reset_index().to_parquet(out_dir / "metric_catchment_year_embeddings.parquet", index=False)
    manifest = {
        "status": "metric aggregation compared; retrieval effect still requires the representation runner",
        "crs": CRS,
        "scale_m": SCALE,
        "rows": len(new),
        "catchments": new.reset_index().gauge.nunique(),
        "minimum_direction_cosine": float(comparisons.direction_cosine.min()),
        "maximum_direction_difference": float(comparisons.normalized_vector_distance.max()),
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [path, old_path, EXPORT.DEFAULT_CATCHMENTS, Path(__file__)]
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "input_sha256"}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="limburg-511403")
    parser.add_argument("--download", action="store_true")
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "results/basin_ai_alphaearth_projection"
    )
    args = parser.parse_args()
    catchments = gpd.read_file(EXPORT.DEFAULT_CATCHMENTS)
    if args.download and not OUT.exists():
        import ee

        ee.Initialize(project=args.project)
        ee.data.setDeadline(600000)
        table = metric_table(ee, catchments)
        url = table.getDownloadURL(
            filetype="csv",
            selectors=EXPORT.expected_output_columns() + ["aggregation_crs", "aggregation_scale_m"],
        )
        partial = OUT.with_suffix(".csv.part")
        print("Downloading 72 catchment/year rows on a 10-m EPSG:3035 grid", flush=True)
        with urllib.request.urlopen(url, timeout=600) as source, partial.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
        # Validate before replacing any final delivery.
        validate_and_compare(partial, catchments, args.output_dir)
        partial.replace(OUT)
    if OUT.exists():
        validate_and_compare(OUT, catchments, args.output_dir)
    else:
        print(
            "Use --download to retrieve the separate metric-grid table; original export is preserved."
        )


if __name__ == "__main__":
    main()
