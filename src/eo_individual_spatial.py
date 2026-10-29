"""Fixed terrain zones and exact-source physical grids for streamed EO work."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform
from shapely.geometry import box

from src.eo_event_inputs import pixel_area_weights
from src.eo_inputs import Tile


class SpatialInputs:
    def __init__(self, root):
        self.root = Path(root)
        self.dem = [
            rasterio.open(p) for p in sorted((self.root / "data/raw/dem/glo30").glob("*.tif"))
        ]
        physical = self.root / "data/raw/limburg_galileo_physical"
        self.physical = physical
        climate = physical / "era5_monthly_2009_2025.tif"
        self.climate = rasterio.open(climate) if climate.exists() else None
        self.climate_bands = (
            json.loads(climate.with_suffix(".receipt.json").read_text())["bands"]
            if self.climate
            else []
        )

    def elevation(self, bounds, resolution):
        width = round((bounds[2] - bounds[0]) / resolution)
        height = round((bounds[3] - bounds[1]) / resolution)
        affine = from_origin(bounds[0], bounds[3], resolution, resolution)
        out = np.full((height, width), np.nan, np.float32)
        for source in self.dem:
            with WarpedVRT(
                source,
                crs="EPSG:32632",
                transform=affine,
                width=width,
                height=height,
                resampling=Resampling.nearest,
                nodata=-9999,
            ) as vrt:
                a = vrt.read(1, masked=True)
                keep = ~np.ma.getmaskarray(a)
                out[keep] = a.data[keep]
        return out

    def physical_tile(self, bounds, windows, resolution=10):
        p = self.physical / f"srtm_{int(bounds[0])}_{int(bounds[1])}.tif"
        h = round((bounds[3] - bounds[1]) / resolution)
        w = round((bounds[2] - bounds[0]) / resolution)
        affine = from_origin(bounds[0], bounds[3], resolution, resolution)
        with (
            rasterio.open(p) as source,
            WarpedVRT(
                source,
                crs="EPSG:32632",
                transform=affine,
                width=w,
                height=h,
                resampling=Resampling.nearest,
                nodata=-9999,
            ) as vrt,
        ):
            terrain = vrt.read(masked=True).filled(np.nan)
        if not self.climate:
            raise ValueError("Exact ERA5 monthly image missing")
        indexes = []
        for window in windows:
            month = window["start"][:7].replace("-", "")
            indexes.extend(
                [
                    self.climate_bands.index(month + "_" + band) + 1
                    for band in ["temperature_2m", "total_precipitation_sum"]
                ]
            )
        with WarpedVRT(
            self.climate,
            crs="EPSG:32632",
            transform=affine,
            width=w,
            height=h,
            resampling=Resampling.nearest,
            nodata=-9999,
        ) as vrt:
            climate = vrt.read(indexes, masked=True).filled(np.nan).reshape(len(windows), 2, h, w)
        return terrain, climate


def fixed_elevation_cuts(geometry, bounds_list, spatial):
    elevations = []
    areas = []
    for bounds in bounds_list:
        if not geometry.intersects(box(*bounds)):
            continue
        dem = spatial.elevation(bounds, 30)
        area = pixel_area_weights(geometry, bounds, 30)
        valid = np.isfinite(dem) & (area > 0)
        elevations.append(dem[valid])
        areas.append(area[valid])
    if not elevations or not sum(len(x) for x in elevations):
        return [float("nan")] * 2
    x = np.concatenate(elevations)
    w = np.concatenate(areas)
    order = np.argsort(x, kind="stable")
    x = x[order]
    w = w[order]
    cdf = np.cumsum(w) / w.sum()
    return [float(x[min(np.searchsorted(cdf, q), len(x) - 1)]) for q in (1 / 3, 2 / 3)]


def region_weights(geometry, bounds, resolution, dem, cuts):
    whole = pixel_area_weights(geometry, bounds, resolution).astype(np.float32)
    valid = np.isfinite(dem)
    zones = [
        whole * valid * (dem <= cuts[0]),
        whole * valid * (dem > cuts[0]) * (dem <= cuts[1]),
        whole * valid * (dem > cuts[1]),
    ]
    if np.isfinite(dem[whole > 0]).all():
        np.testing.assert_allclose(np.stack(zones).sum(0), whole, rtol=1e-6, atol=1e-5)
    return np.stack([whole, *zones])


def fast_patch(tile, row, col, size):
    """Same numerical input/grid/date contract as get_patch, without unused pixel lat/lons."""
    values = np.zeros((len(tile.bands), size, size), np.float32)
    valid = np.zeros((size, size), bool)
    days = np.zeros((size, size), float)
    source = tile.values[:, row : row + size, col : col + size]
    h, w = source.shape[-2:]
    values[:, :h, :w] = source
    valid[:h, :w] = tile.valid[row : row + size, col : col + size]
    days[:h, :w] = tile.days[row : row + size, col : col + size]
    x, y = tile.transform * (col + size / 2, row + size / 2)
    lon, lat = transform(tile.crs, "EPSG:4326", [x], [y])
    observed = days[valid]
    date = (
        (
            datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=float(np.median(observed)))
        ).isoformat()
        if len(observed)
        else None
    )
    return {
        "values": values,
        "valid": valid,
        "days": days,
        "metadata": {
            "row": row,
            "col": col,
            "patch_pixels": size,
            "bands": tile.bands,
            "valid_pixels": int(valid.sum()),
            "valid_fraction": float(valid.mean()),
            "padding_pixels": int(size * size - h * w),
            "latitude": lat[0],
            "longitude": lon[0],
            "crs": tile.crs,
            "resolution_m": abs(tile.transform.a),
            "bounds": [
                *(tile.transform * (col, row + size)),
                *(tile.transform * (col + size, row)),
            ],
            "representative_date": date,
            "acquired_day_min": float(observed.min()) if len(observed) else None,
            "acquired_day_max": float(observed.max()) if len(observed) else None,
            "window": tile.window,
            "sources": tile.sources,
            "earliest_asof_eligibility": tile.window["end"],
        },
    }


def blank_tile(reference, window):
    return Tile(
        np.zeros_like(reference.values),
        np.zeros_like(reference.valid),
        np.zeros_like(reference.days),
        reference.bands.copy(),
        reference.transform,
        reference.crs,
        [],
        window,
    )
