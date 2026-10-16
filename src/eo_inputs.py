"""Read the pinned compact EO archive without confusing masks with observations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform

ROUTES = {
    "olmoearth": ("s1_ascending", 64, "modern"),
    "galileo": ("s2_10m", 64, "galileo"),
    "prithvi": ("hls", 224, "modern"),
    "anysat": ("s2_10m", 64, "modern"),
    "croma": ("s1_ascending", 120, "modern"),
    "dofa": ("s2_10m", 224, "legacy"),
    "copernicus_fm": ("s2_10m", 224, "legacy"),
    "terramind": ("s2_10m", 224, "terramind"),
    "presto": ("s2_10m", 64, "presto"),
    "satmae": ("s2_10m", 96, "satmae"),
}

S2_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
HLS_BANDS = ["blue", "green", "red", "nir", "swir1", "swir2"]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@dataclass
class Tile:
    values: np.ndarray
    valid: np.ndarray
    days: np.ndarray
    bands: list[str]
    transform: object
    crs: str
    sources: list[dict]
    window: dict


def read_product(root, job):
    path = Path(root) / job["relative_path"]
    receipt = json.loads(path.with_suffix(".receipt.json").read_text())
    actual = sha256(path)
    if actual != receipt["sha256"]:
        raise ValueError(f"Source receipt differs: {path}")
    for key in ("bands", "bounds", "window", "asset_ids", "relative_path"):
        if receipt[key] != job[key]:
            raise ValueError(f"Source receipt job mismatch: {key}")
    with rasterio.open(path) as ds:
        if str(ds.crs) != "EPSG:32632" or ds.transform.b or ds.transform.d:
            raise ValueError("Unexpected archive CRS or rotated grid")
        if not np.allclose(ds.bounds, job["bounds"], atol=1e-6, rtol=0):
            raise ValueError("Raster bounds differ from job")
        data = ds.read()
        names = list(ds.descriptions)
        if data.shape[0] != len(job["bands"]) + 1 or (
            any(names) and names != job["bands"] + ["valid_bits"]
        ):
            raise ValueError(f"Unexpected raster band contract: {names}")
        bits = data[-1].astype(np.uint32)
        valid = np.stack([(bits & (1 << i)) != 0 for i in range(len(job["bands"]))])
        valid &= np.isfinite(data[:-1])
        return (
            data[:-1],
            valid,
            ds.transform,
            ds.crs,
            {
                "relative_path": job["relative_path"],
                "sha256": actual,
                "asset_ids": job["asset_ids"],
                "acquisition_ms": job["acquisition_ms"],
                "window": job["window"],
                "observed_acquired_day_range": [
                    float(
                        data[job["bands"].index("acquired_day")][
                            valid[job["bands"].index("acquired_day")]
                        ].min()
                    ),
                    float(
                        data[job["bands"].index("acquired_day")][
                            valid[job["bands"].index("acquired_day")]
                        ].max()
                    ),
                ]
                if valid[job["bands"].index("acquired_day")].any()
                else None,
            },
        )


def read_tile(root, job, companions):
    data, masks, affine, crs, receipt = read_product(root, job)
    names = job["bands"]
    day = data[names.index("acquired_day")]
    selected = (
        HLS_BANDS
        if job["product"] == "hls"
        else (["VV", "VH"] if job["product"] == "s1_ascending" else ["B2", "B3", "B4", "B8"])
    )
    indices = [names.index(b) for b in selected]
    values = data[indices].astype(np.float32)
    valid = masks[indices].all(axis=0) & masks[names.index("acquired_day")]
    sources = [receipt]
    if job["product"] == "s2_10m":
        other = companions[(job["window"]["id"], tuple(job["bounds"]), "s2_20m")]
        coarse, coarse_masks, coarse_affine, coarse_crs, source = read_product(root, other)
        # The archive itself uses nearest-neighbour grids. Apply the same
        # explicit rule to 20m reflectance, masks and dates; no mixed valid/nodata averages.
        up = np.zeros((coarse.shape[0], *valid.shape), dtype=np.float32)
        up_masks = np.zeros(up.shape, dtype=np.uint8)
        for i in range(len(other["bands"])):
            reproject(
                coarse[i],
                up[i],
                src_transform=coarse_affine,
                src_crs=coarse_crs,
                dst_transform=affine,
                dst_crs=crs,
                resampling=Resampling.nearest,
            )
            reproject(
                coarse_masks[i].astype(np.uint8),
                up_masks[i],
                src_transform=coarse_affine,
                src_crs=coarse_crs,
                dst_transform=affine,
                dst_crs=crs,
                resampling=Resampling.nearest,
            )
        extra = ["B5", "B6", "B7", "B8A", "B11", "B12"]
        idx = [other["bands"].index(b) for b in extra]
        values = np.concatenate([values, up[idx]])
        selected += extra
        valid &= up_masks[idx].all(axis=0).astype(bool)
        day_idx = other["bands"].index("acquired_day")
        valid &= up_masks[day_idx].astype(bool)
        # Keep the latest acquisition across bands for the conservative age bound.
        # The earlier per-product date range is retained in source provenance.
        day = np.maximum(day, up[day_idx])
        order = [selected.index(b) for b in S2_BANDS]
        values, selected = values[order], S2_BANDS.copy()
        sources.append(source)
    dates = day[valid]
    if len(dates):
        start = datetime.fromisoformat(job["window"]["start"]).timestamp() / 86400
        end = datetime.fromisoformat(job["window"]["end"]).timestamp() / 86400
        if dates.min() < np.floor(start) or dates.max() >= end:
            raise ValueError("Observed acquisition falls outside its completed UTC window")
    return Tile(values, valid, day, selected, affine, str(crs), sources, job["window"])


def patch_origins(tile, size):
    h, w = tile.valid.shape
    return [(y, x) for y in range(0, h, size) for x in range(0, w, size)]


def get_patch(tile, row, col, size):
    values = np.zeros((len(tile.bands), size, size), dtype=np.float32)
    valid = np.zeros((size, size), dtype=bool)
    days = np.zeros((size, size), dtype=np.float64)
    source = tile.values[:, row : row + size, col : col + size]
    h, w = source.shape[-2:]
    values[:, :h, :w] = source
    valid[:h, :w] = tile.valid[row : row + size, col : col + size]
    days[:h, :w] = tile.days[row : row + size, col : col + size]
    x, y = tile.transform * (col + size / 2, row + size / 2)
    lon, lat = transform(tile.crs, "EPSG:4326", [x], [y])
    observed = days[valid]
    representative = float(np.median(observed)) if len(observed) else None
    dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=representative or 0)
    pixel_rows, pixel_cols = np.indices((size, size))
    xs = tile.transform.c + (col + pixel_cols + 0.5) * tile.transform.a
    ys = tile.transform.f + (row + pixel_rows + 0.5) * tile.transform.e
    lons, lats = transform(tile.crs, "EPSG:4326", xs[valid].tolist(), ys[valid].tolist())
    return {
        "observed_latlons": np.asarray([lats, lons], dtype=np.float32).T,
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
            "date_rule": "median of latest per-pixel band acquisition days in this completed composite",
            "representative_date": dt.isoformat() if len(observed) else None,
            "acquired_day_min": float(observed.min()) if len(observed) else None,
            "acquired_day_max": float(observed.max()) if len(observed) else None,
            "window": tile.window,
            "sources": tile.sources,
            "earliest_asof_eligibility": tile.window["end"],
            "availability_caveat": "Completed-window lower bound only; product publication latency must also be respected in any prospective evaluation.",
        },
    }


def standardize(values, valid, mean, std):
    """Missing pixels become normalized mean imputation, never observed zeros."""
    mean = np.asarray(mean, np.float32)[:, None, None]
    std = np.asarray(std, np.float32)[:, None, None]
    if np.any(std <= 0):
        raise ValueError("Nonpositive normalization scale")
    return np.where(valid[None], (values - mean) / std, 0).astype(np.float32)
