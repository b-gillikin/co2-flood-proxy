"""Delineate cross-border upstream catchments from Copernicus GLO-30 (protocol §6).

The Geul, Gulp and Voer rise in Belgium and the Worm drains Aachen, so
catchments come from a DEM that crosses national borders. Pour points are the
gauge coordinates published on Waterschap Limburg's public portal
(`data/interim/waterschap_locations.csv`), provisional until the numerical
coordinates requested from Waterschap arrive. Each pour point snaps to the
highest-accumulation cell within a fixed radius.

The delineation is checked against provider-reported catchment areas listed
in EStreams, at cohort gauges where available and at upstream gauges on the
Geul and Wurm. No discharge, rainfall or weather value is read.

Example: python scripts/39_delineate_catchments.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.merge import merge
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
DEM_DIR = ROOT / "data/raw/dem/glo30"
DEM_SOURCE = "Copernicus GLO-30 DSM (AWS open data, 1 arc-second)"
OUTPUT = ROOT / "data/interim/event_study_catchments.gpkg"
REPORT = ROOT / "results/catchments"
BBOX = (5.45, 50.50, 6.45, 51.15)
EQUAL_AREA = "EPSG:3035"
SNAP_RADIUS_CELLS = 15
CHANNEL_KM2 = 5.0

# Candidate cohort gauges (protocol §3); coordinates from the public portal.
COHORT = {
    "11.Q.32": "Eyserbeek",
    "10.Q.29": "Geul",
    "13.Q.34": "Gulp",
    "15.Q.41": "Voer",
    "18.Q.45": "Worm",
    "6.Q.18": "Geleenbeek",
    "6.Q.25": "Vloedgraaf",
}
# Provider-reported areas (km2) from EStreams gauging-station metadata.
CHECKS = [
    ("Eyserbeek, Eys (NL000003)", 5.929363, 50.825340, 27.11),
    ("Gulp, Azijnfabriek (NL000005)", 5.891548, 50.814140, 46.05),
    ("Voer, Mesch (NL000006)", 5.736490, 50.764106, 56.95),
    ("Selzerbeek, Partij (NL000004)", 5.921758, 50.810588, 28.74),
    ("Geul, Sippenaeken (BEWA0140)", 5.940755, 50.750476, 121.00),
    ("Wurm, Kalkofen (DENW1131)", 6.111801, 50.782571, 33.63),
    ("Wurm, Herzogenrath 1 (DENW1116)", 6.094843, 50.866518, 96.29),
]


def mosaic(path):
    """Merge the GLO-30 tiles, crop to the study box and write one GeoTIFF."""
    sources = [rasterio.open(tile) for tile in sorted(DEM_DIR.glob("Copernicus_DSM_*.tif"))]
    data, transform = merge(sources, bounds=BBOX)
    profile = sources[0].profile | {
        "driver": "GTiff",
        "height": data.shape[1],
        "width": data.shape[2],
        "transform": transform,
        "count": 1,
        "compress": "deflate",
    }
    profile.pop("blockxsize", None)
    profile.pop("blockysize", None)
    profile["tiled"] = False
    with rasterio.open(path, "w", **profile) as target:
        target.write(data[0], 1)
    for source in sources:
        source.close()


def conditioned_grid(path):
    # pysheds 0.5 still calls np.in1d, removed in NumPy 2; np.isin is its successor.
    if not hasattr(np, "in1d"):
        np.in1d = np.isin
    from pysheds.grid import Grid

    grid = Grid.from_raster(str(path))
    dem = grid.read_raster(str(path))
    dem = grid.fill_depressions(grid.fill_pits(dem))
    dem = grid.resolve_flats(dem)
    direction = grid.flowdir(dem)
    accumulation = grid.accumulation(direction)
    return grid, direction, accumulation


def snap(grid, accumulation, lon, lat):
    """Nearest channel cell (column, row) to the pour point.

    A channel cell drains at least CHANNEL_KM2; every cohort catchment is far
    larger. Snapping to the nearest channel, rather than to the largest
    accumulation in a window, avoids drifting the outlet downstream. Channels
    are one cell wide, so the index, not a coordinate, goes to the trace.
    """
    col, row = grid.nearest_cell(lon, lat, snap="center")
    acc = np.asarray(accumulation)
    cell_km2 = (30.87 / 1000) * (30.87 / 1000) * np.cos(np.radians(lat))
    r0, c0 = max(0, row - SNAP_RADIUS_CELLS), max(0, col - SNAP_RADIUS_CELLS)
    window = acc[r0 : row + SNAP_RADIUS_CELLS + 1, c0 : col + SNAP_RADIUS_CELLS + 1]
    rows, cols = np.nonzero(window * cell_km2 >= CHANNEL_KM2)
    if not len(rows):
        raise ValueError(f"No channel within the snap radius of ({lon}, {lat})")
    distance = np.hypot(
        (r0 + rows - row) * 30.87, (c0 + cols - col) * 30.87 * np.cos(np.radians(lat))
    )
    nearest = np.argmin(distance)
    return c0 + cols[nearest], r0 + rows[nearest]


def catchment_polygon(grid, direction, col, row):
    mask = grid.catchment(x=col, y=row, fdir=direction, xytype="index")
    clipped = grid.view(mask, nodata=0)
    shapes = [shape(geom) for geom, value in grid.polygonize(clipped) if value]
    polygon = unary_union(shapes)
    return polygon


def delineate(grid, direction, accumulation, lon, lat):
    col, row = snap(grid, accumulation, lon, lat)
    polygon = catchment_polygon(grid, direction, col, row)
    x, y = grid.affine * (col + 0.5, row + 0.5)
    frame = gpd.GeoSeries([polygon], crs="EPSG:4326").to_crs(EQUAL_AREA)
    offset = gpd.GeoSeries(gpd.points_from_xy([lon, x], [lat, y]), crs="EPSG:4326").to_crs(
        EQUAL_AREA
    )
    return polygon, float(frame.area.iloc[0] / 1e6), float(offset.iloc[0].distance(offset.iloc[1]))


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    dem_path = REPORT / "glo30_limburg.tif"
    if not dem_path.exists():
        mosaic(dem_path)
    grid, direction, accumulation = conditioned_grid(dem_path)

    checks = []
    for name, lon, lat, reference in CHECKS:
        _, area, moved = delineate(grid, direction, accumulation, lon, lat)
        checks.append(
            {
                "check_point": name,
                "reference_area_km2": reference,
                "delineated_area_km2": round(area, 2),
                "relative_difference": round(area / reference - 1, 3),
                "snap_distance_m": round(moved),
            }
        )
    checks = pd.DataFrame(checks)
    checks.to_csv(REPORT / "area_checks.csv", index=False)
    print(checks.to_string(index=False))

    locations = pd.read_csv(ROOT / "data/interim/waterschap_locations.csv").set_index(
        "ExternalReference"
    )
    rows = []
    for key, watercourse in COHORT.items():
        location = locations.loc[key]
        polygon, area, moved = delineate(
            grid, direction, accumulation, location.Longitude, location.Latitude
        )
        rows.append(
            {
                "watercourse": watercourse,
                "gauge": key,
                "gauge_name": location.Name,
                "pour_point_source": "Waterschap Limburg public portal (provisional)",
                "snap_distance_m": round(moved),
                "area_km2": round(area, 2),
                "dem_source": DEM_SOURCE,
                "geometry": polygon,
            }
        )
    catchments = gpd.GeoDataFrame(rows, crs="EPSG:4326").to_crs(EQUAL_AREA)
    overlaps = []
    for i, left in catchments.iterrows():
        for j, right in catchments.iterrows():
            if i < j:
                shared = left.geometry.intersection(right.geometry).area / 1e6
                if shared > 0.01:
                    overlaps.append(
                        {
                            "a": left.watercourse,
                            "b": right.watercourse,
                            "shared_km2": round(shared, 2),
                        }
                    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    catchments.to_file(OUTPUT, driver="GPKG")
    catchments.drop(columns="geometry").to_csv(REPORT / "catchments.csv", index=False)
    print(catchments.drop(columns="geometry").to_string(index=False))
    print("overlaps:", overlaps)
    (REPORT / "manifest.json").write_text(
        json.dumps(
            {
                "dem_source": DEM_SOURCE,
                "tiles": sorted(tile.name for tile in DEM_DIR.glob("*.tif")),
                "bbox_wgs84": BBOX,
                "conditioning": "pysheds fill_pits, fill_depressions, resolve_flats; D8",
                "snap_radius_cells": SNAP_RADIUS_CELLS,
                "snap_rule": f"nearest cell draining >= {CHANNEL_KM2} km2",
                "area_crs": EQUAL_AREA,
                "overlaps_km2": overlaps,
                "status": "provisional pour points; replace when numerical coordinates arrive",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    sys.exit(main())
