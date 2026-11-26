"""Check the active Limburg catchments, routed supports and saved C2 predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from math import ceil, floor
from pathlib import Path

# The chapter's Conda-backed virtual environment keeps PROJ in the base prefix.
proj_data = Path(sys.base_prefix) / "share" / "proj"
if (proj_data / "proj.db").is_file():
    os.environ.setdefault("PROJ_DATA", str(proj_data))

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dise_corrected import population, score
from src.geoglows_experiment import sha, write_json

EXTENSION = ROOT / "results/limburg_representation_extension_v1"
NETWORK = ROOT / "data/raw/limburg_geoglows_stages12_v1"
REGIONAL = ROOT / "results/limburg_dise_v2"
PAIRED = EXTENSION / "c2_alphaearth_2017_v1"
TARGET = EXTENSION / "c2_multiyear_v1"
FILES = {
    "reference": EXTENSION / "catchments.gpkg",
    "inventory": EXTENSION / "catchment_inventory.csv",
    "network": NETWORK / "streams_209.gpkg",
    "increments": NETWORK / "catchments_209.parquet",
    "local_routes": ROOT / "config/limburg_geoglows_reaches_v1.json",
    "local_sites": ROOT / "config/limburg_geoglows_stages12_v2.json",
    "regional_routes": REGIONAL / "spatial_review_v1/resolved_mapping_ledger.csv",
    "alphaearth": EXTENSION / "alphaearth_2020/descriptors_2020.parquet",
    "descriptor_receipt": EXTENSION / "alphaearth_2020/quality_2020.json",
    "tessera": EXTENSION / "tessera_census_2020/descriptors_2020.csv",
    "landscape": TARGET / "inputs/landscape.parquet",
    "state": TARGET / "inputs/antecedent_state.parquet",
    "state_receipt": TARGET / "source_audit.json",
    "weather": REGIONAL / "regional_inputs_resolved_v1/weather.parquet",
    "features": TARGET / "preparation/features.parquet",
    "predictions": PAIRED / "paired_predictions.parquet",
    "prediction_receipt": PAIRED / "completion_review.json",
}
LOCAL_WEATHER = sorted((ROOT / "data/raw/limburg_dise_v1/weather").glob("local_daily_*.parquet"))


def routed_polygons(routes):
    graph = gpd.read_file(FILES["network"], ignore_geometry=True).set_index("LINKNO")
    polygons = gpd.read_parquet(FILES["increments"]).set_index("LINKNO").to_crs(3035)
    if (
        not graph.index.is_unique
        or not polygons.index.is_unique
        or set(graph.index) != set(polygons.index)
    ):
        raise ValueError("GEOGLOWS component polygons and routing lines fail the LINKNO join")
    incoming = defaultdict(list)
    for node, downstream in graph.DSLINKNO.items():
        incoming[int(downstream)].append(node)
    result = {}
    for outlet in sorted(set(routes)):
        seen = set()
        stack = [outlet]
        while stack:
            node = stack.pop()
            if node in seen:
                raise ValueError(f"Repeated upstream component for {outlet}: {node}")
            seen.add(node)
            stack.extend(incoming[node])
        result[outlet] = polygons.loc[sorted(seen)].geometry.union_all()
    return gpd.GeoSeries(routes.map(result), index=routes.index, crs=3035)


def cross_support(reference, routed):
    fields = (
        "basis",
        "target",
        "target_role",
        "source_role",
        "source",
        "overlap_km2",
        "target_fraction",
        "source_fraction",
    )
    rows = []
    for basis, geometry in (("reference", reference.geometry), ("GEOGLOWS routed", routed)):
        for target, polygon in geometry.items():
            target_role = reference.at[target, "source_role"]
            if target_role == "regional_donor":
                continue
            for source in geometry.index[geometry.sindex.query(polygon, predicate="intersects")]:
                source_role = reference.at[source, "source_role"]
                if source_role == target_role or source_role == "reserved_external":
                    continue
                source_polygon = geometry.loc[source]
                area = polygon.intersection(source_polygon).area
                if area > 1:
                    rows.append(
                        {
                            "basis": basis,
                            "target": target,
                            "target_role": target_role,
                            "source_role": source_role,
                            "source": source,
                            "overlap_km2": area / 1e6,
                            "target_fraction": area / polygon.area,
                            "source_fraction": area / source_polygon.area,
                        }
                    )
    return pd.DataFrame(rows, columns=fields).sort_values(
        ["basis", "target_fraction"], ascending=[True, False]
    )


def score_sensitivity(overlaps):
    receipt = json.loads(FILES["prediction_receipt"].read_text())
    if receipt["status"] != "completed" or (
        sha(FILES["predictions"]) != receipt["paired_predictions_sha256"]
    ):
        raise ValueError("Archived predictions fail their receipt")
    frame = pd.read_parquet(FILES["predictions"])
    if len(frame) != receipt["paired_rows"] or frame.duplicated(["regime", "gauge", "day"]).any():
        raise ValueError("Unexpected paired prediction census")
    frame = frame.loc[frame.source_role.eq("reserved_external")]
    columns = {
        "GEOGLOWS": "q_model",
        "C2": "native_rmse__C2",
        "C2 + AlphaEarth 2020": "native_rmse__C2+AlphaEarth",
        "C2 + TESSERA 2020": "native_rmse__C2+TESSERA",
    }
    external_overlap = overlaps.loc[overlaps.target_role.eq("reserved_external")]
    panels = {"all_external": set()}
    for fraction in (0.01, 0.10):
        panels[f"omit_targets_with_at_least_{fraction:g}_target_overlap"] = set(
            external_overlap.loc[external_overlap.target_fraction.ge(fraction), "target"]
        )
    rows = []
    for panel, excluded in panels.items():
        kept = frame.loc[~frame.gauge.isin(excluded)]
        for label, eligible in (
            ("all_days", kept),
            ("high_water", kept.loc[kept.high_water.eq(True)]),
        ):
            gauges = population(eligible)
            metrics = {arm: score(eligible, eligible[col], gauges) for arm, col in columns.items()}
            baseline = metrics["C2"]["mae"]
            for arm, result in metrics.items():
                mae = result["mae"]
                rows.append(
                    dict(
                        panel=panel,
                        stratum=label,
                        arm=arm,
                        gauge_days=len(eligible),
                        gauges=eligible.gauge.nunique(),
                        rivers=eligible.river_group.nunique(),
                        omitted_gauges=" ".join(sorted(excluded)),
                        score_status=result["status"],
                        score_reason=result["reason"],
                        mae=mae,
                        rmse=result["rmse"],
                        mae_reduction_vs_c2_pct=(
                            100 * (1 - mae / baseline) if mae is not None and baseline else None
                        ),
                    )
                )
    return pd.DataFrame(rows)


def raster_support(reference, areas):
    receipt = json.loads(FILES["descriptor_receipt"].read_text())
    for name, key in (
        ("reference", "geometry_sha256"),
        ("alphaearth", "alphaearth_parquet_sha256"),
        ("tessera", "tessera_csv_sha256"),
    ):
        if sha(FILES[name]) != receipt[key]:
            raise ValueError(f"{name} differs from the matched 2020 descriptor receipt")
    frame = pd.read_parquet(FILES["landscape"]).set_index("gauge")
    state = pd.read_parquet(FILES["state"], columns=["gauge", "state_valid_m2"])
    weather = pd.concat(
        [
            pd.read_parquet(path, columns=["gauge", "sampled_area_m2"])
            for path in [FILES["weather"], *LOCAL_WEATHER]
        ]
    )
    if set(weather.gauge) != set(reference.index):
        raise ValueError("Weather support does not cover the catchment census")
    alpha = pd.read_parquet(FILES["alphaearth"]).set_index("gauge")
    tessera = pd.read_csv(FILES["tessera"], dtype={"gauge": str}).set_index("gauge")
    for data in (frame, alpha, tessera):
        if not data.index.is_unique or set(data.index) != set(reference.index):
            raise ValueError("Static feature keys do not match the catchment census")
    digest = reference.to_crs(4326).geometry.map(
        lambda polygon: hashlib.sha256(polygon.wkb).hexdigest()
    )
    if (
        not alpha.geometry_sha256.eq(digest).all()
        or not tessera.role.eq(reference.source_role).all()
    ):
        raise ValueError("2020 descriptor geometry or role mismatch")
    cover_sum = frame.filter(regex=r"^c2_cover_.*_fraction$").sum(axis=1, skipna=False)
    if not np.isclose(cover_sum, 1, atol=1e-6, rtol=0).all():
        raise ValueError("WorldCover fractions do not close over their common valid support")
    support = frame[["cover_valid_m2", "terrain_valid_m2", "clay_valid_m2"]].div(areas, axis=0)
    support.columns = ["worldcover_area_ratio", "terrain_area_ratio", "clay_valid_area_fraction"]
    support["weather_min_area_ratio"] = weather.groupby("gauge").sampled_area_m2.min() / areas
    support["state_min_area_ratio"] = state.groupby("gauge").state_valid_m2.min() / areas
    support["state_max_area_ratio"] = state.groupby("gauge").state_valid_m2.max() / areas
    support["alphaearth_pixel_count_area_ratio"] = alpha.valid_pixel_count * 100 / areas
    support["tessera_coverage_fraction"] = tessera.coverage_fraction
    return support


def local_checks(reference, routed):
    local = reference.loc[reference.source_role.eq("local")]
    sites = pd.DataFrame(json.loads(FILES["local_sites"].read_text())["sites"]).set_index("gauge")
    sites = sites.loc[local.index]
    points = gpd.GeoSeries(
        gpd.points_from_xy(sites.longitude, sites.latitude), index=local.index, crs=4326
    ).to_crs(3035)
    projection = json.loads(FILES["state_receipt"].read_text())["projections"]["state"]
    if projection["crs"] != "EPSG:4326" or projection["transform"] != [
        0.1,
        0,
        -180.05,
        0,
        -0.1,
        90.05,
    ]:
        raise ValueError("Expected the verified 0.1-degree ERA5-Land grid")
    records = []
    for gauge, polygon in local.to_crs(4326).geometry.items():
        west, south, east, north = polygon.bounds
        # Grid centres lie on integer multiples of 0.1 degrees. Densify the
        # cell edges before projecting so area is measured on the same grid.
        cells = (
            gpd.GeoSeries(
                [
                    box(i / 10 - 0.05, j / 10 - 0.05, i / 10 + 0.05, j / 10 + 0.05)
                    for i in range(floor(west * 10), ceil(east * 10) + 1)
                    for j in range(floor(south * 10), ceil(north * 10) + 1)
                ],
                crs=4326,
            )
            .segmentize(0.005)
            .to_crs(3035)
        )
        weights = cells.intersection(local.geometry.at[gauge]).area / local.geometry.at[gauge].area
        if not np.isclose(weights.sum(), 1):
            raise ValueError(f"ERA5-Land grid cells do not cover {gauge}")
        records.append(
            dict(
                gauge=gauge,
                distance_to_reference_m=points.at[gauge].distance(local.geometry.at[gauge]),
                intersecting_ERA5_Land_cells=weights.gt(0).sum(),
                largest_ERA5_Land_cell_fraction=weights.max(),
                effective_ERA5_Land_cells=1 / weights.pow(2).sum(),
            )
        )
    pairs = []
    for basis, areas in (
        ("reference", local.geometry),
        ("GEOGLOWS routed", routed.loc[local.index]),
    ):
        for gauge, polygon in areas.items():
            for other in areas.index[areas.index > gauge]:
                shared = polygon.intersection(areas.at[other]).area
                pairs.append(
                    dict(
                        basis=basis,
                        gauge=gauge,
                        other=other,
                        same_river=sites.at[gauge, "river"] == sites.at[other, "river"],
                        overlap_m2=shared,
                    )
                )
    return pd.DataFrame(records).set_index("gauge"), pd.DataFrame(pairs)


def assess(out):
    reference = gpd.read_file(FILES["reference"]).set_index("gauge")
    if reference.crs.to_epsg() != 3035 or not reference.index.is_unique:
        raise ValueError("Invalid reference CRS or duplicate gauge keys")
    if not reference.is_valid.all() or reference.is_empty.any():
        raise ValueError("Invalid or empty reference polygon")
    areas = reference.area
    inventory = pd.read_csv(FILES["inventory"], dtype={"gauge": str}).set_index("gauge")
    digest = reference.geometry.map(lambda polygon: hashlib.sha256(polygon.wkb).hexdigest())
    if not digest.eq(inventory.processing_geometry_sha256_epsg3035).all():
        raise ValueError("Reference geometry differs from the pinned inventory")
    local = pd.read_json(FILES["local_routes"]).dropna(subset="river_id").set_index("gauge")
    regional = pd.read_csv(FILES["regional_routes"]).set_index("gauge_id")
    routes = pd.concat([local.river_id, regional.best_river_id]).reindex(reference.index)
    if routes.isna().any():
        raise ValueError("Active catchment without a routed outlet")
    routed = routed_polygons(routes.astype(int))
    if not routed.is_valid.all() or routed.is_empty.any():
        raise ValueError("Invalid or empty contributing polygon")
    overlaps = cross_support(reference, routed)
    scores = score_sensitivity(overlaps)
    support = raster_support(reference, areas)
    local, local_pairs = local_checks(reference, routed)
    geometry_check = reference[["station", "source_role", "reference_area_km2"]].copy()
    groups = pd.read_parquet(FILES["features"], columns=["gauge", "river_group"])
    groups = groups.drop_duplicates().set_index("gauge")
    if set(groups.index) != set(reference.index) or groups.river_group.isna().any():
        raise ValueError("River-group assignments do not cover the catchment census")
    geometry_check = geometry_check.join(groups, validate="one_to_one")
    geometry_check["geometry_sha256_epsg3035"] = digest
    geometry_check["polygon_area_km2"] = areas / 1e6
    geometry_check["GEOGLOWS_river_id"] = routes.astype(int)
    geometry_check["GEOGLOWS_area_km2"] = routed.area / 1e6
    shared_area = reference.geometry.intersection(routed).area
    geometry_check["reference_area_in_GEOGLOWS_fraction"] = shared_area / areas
    geometry_check["GEOGLOWS_area_in_reference_fraction"] = shared_area / routed.area
    out.mkdir(parents=True, exist_ok=True)
    tables = {
        "catchment_support.csv": geometry_check.join(support).join(local),
        "cross_role_overlap.csv": overlaps,
        "local_pair_overlap.csv": local_pairs,
        "external_sensitivity.csv": scores,
    }
    for name, table in tables.items():
        table.to_csv(out / name, index=name == "catchment_support.csv")
    write_json(
        out / "manifest.json",
        {
            "sha256": {
                str(p.relative_to(ROOT)): sha(p)
                for p in [
                    Path(__file__),
                    ROOT / "src/dise_corrected.py",
                    *FILES.values(),
                    *LOCAL_WEATHER,
                ]
            },
            "outputs": {name: sha(out / name) for name in tables},
            "note": "Geometry census and fixed-fit, river- and gauge-balanced error sensitivity",
        },
    )
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=TARGET / "geospatial_audit")
    assess(parser.parse_args().output)
