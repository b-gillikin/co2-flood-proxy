"""Download DWD hourly radar rainfall (RADKLIM-RW or RADOLAN RW) cropped to South Limburg.

Protocol draft 0.9 §6: use RADKLIM-RW if it covers the cohort over the joint
period, otherwise operational RADOLAN RW throughout, never spliced. RADKLIM is
masked outside a band around Germany and leaves the Voer entirely and the Gulp
in part unobserved (`results/radar/`), so RADOLAN RW is the product that can
serve the cohort. Both are supported here so the choice stays auditable.

Each archive is downloaded, checksummed, decoded, cropped and discarded; only
the crop is stored. Missing codes stay missing.

Examples:
    python scripts/37_fetch_radar.py --product radolan --start 2010-01 --end 2025-12
    python scripts/37_fetch_radar.py --product radklim --start 2010-01 --end 2025-12

Product facts, from the DWD archive and the products' own ASCII headers:
- binary files carry an ASCII header ending in ETX, then little-endian uint16
  cells stored from the south-west corner, row by row northward;
- the lower 12 bits hold rain in 0.1 mm (`PR E-01`), bit 0x2000 marks no data
  and bit 0x8000 marks clutter;
- the grid is RADOLAN polar stereographic with 1 km cells. The 900 x 900 grid
  has lower-left corner (-523462, -4658645) m and the 1100 x 900 grid
  (-443462, -4758645) m; the two share one 1 km lattice, so crops align;
- a file stamped HH:50 holds the accumulation over the preceding 60 minutes.
  Newer operational archives also hold 10-minute updates; only HH:50 is kept.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import io
import json
import re
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
DWD = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan"
PRODUCTS = {
    "radklim": {"name": "RADKLIM-RW 2017.002", "output": ROOT / "data/raw/radklim"},
    "radolan": {"name": "RADOLAN RW (operational)", "output": ROOT / "data/raw/radolan_rw"},
}
RADOLAN_CRS = "+proj=stere +lat_0=90 +lat_ts=60 +lon_0=10 +a=6370040 +b=6370040 +units=m +no_defs"
GRIDS = {
    "GP 900x 900": (900, 900, -523462.0, -4658645.0),
    "GP1100x 900": (1100, 900, -443462.0, -4758645.0),
}
CELL = 1000.0
# Limburg tributaries plus their Belgian and German headwaters, with margin.
BBOX = {"lon_min": 5.45, "lon_max": 6.45, "lat_min": 50.50, "lat_max": 51.15}
NODATA_BIT, CLUTTER_BIT, VALUE_MASK = 0x2000, 0x8000, 0x0FFF
STAMP = re.compile(r"10000-(\d{10})-dwd")


def crop_bounds():
    """Projected crop bounds on the shared 1 km lattice covering the box."""
    to_grid = Transformer.from_crs("EPSG:4326", RADOLAN_CRS, always_xy=True)
    lon = np.linspace(BBOX["lon_min"], BBOX["lon_max"], 50)
    lat = np.linspace(BBOX["lat_min"], BBOX["lat_max"], 50)
    x, y = (np.asarray(v) for v in to_grid.transform(*np.meshgrid(lon, lat)))
    x0, y0 = GRIDS["GP 900x 900"][2:]
    xmin = x0 + np.floor((x.min() - x0) / CELL) * CELL
    ymin = y0 + np.floor((y.min() - y0) / CELL) * CELL
    xmax = x0 + np.ceil((x.max() - x0) / CELL) * CELL
    ymax = y0 + np.ceil((y.max() - y0) / CELL) * CELL
    return xmin, ymin, xmax, ymax


def decode(payload, bounds):
    """Return (rain in 0.1 mm as int16, -1 for no data; clutter cell count)."""
    if payload[:2] == b"\x1f\x8b":
        payload = gzip.decompress(payload)
    header_end = payload.index(b"\x03") + 1
    header = payload[:header_end].decode("latin-1")
    grid = next((GRIDS[key] for key in GRIDS if key in header), None)
    if grid is None or "PR E-01" not in header or "INT  60" not in header:
        raise ValueError(f"Unexpected RW header: {header[:80]}")
    nrows, ncols, x0, y0 = grid
    raw = np.frombuffer(payload[header_end:], dtype="<u2")
    if raw.size != nrows * ncols:
        raise ValueError("Unexpected RW payload size")
    xmin, ymin, xmax, ymax = bounds
    rows = slice(round((ymin - y0) / CELL), round((ymax - y0) / CELL))
    cols = slice(round((xmin - x0) / CELL), round((xmax - x0) / CELL))
    crop = raw.reshape(nrows, ncols)[rows, cols]
    value = (crop & VALUE_MASK).astype(np.int16)
    value[(crop & NODATA_BIT) > 0] = -1
    return value, int(((crop & CLUTTER_BIT) > 0).sum())


def fetch(url, attempts=8):
    """Download with exponential backoff; transient DNS and network failures recur."""
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=300) as response:
                return response.read()
        except Exception:  # pragma: no cover - network failures vary
            if attempt == attempts - 1:
                raise
            time.sleep(min(600, 15 * 2**attempt))
    return b""


def iter_archive(archive):
    """Yield (name, bytes) for every file, unpacking nested daily archives."""
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            payload = tar.extractfile(member).read()
            if member.name.endswith((".tar.gz", ".tgz", ".tar")):
                yield from iter_archive(payload)
            else:
                yield member.name, payload


def monthly_files(product, month):
    """Yield (source, name, payload) for one month of HH:50 files."""
    if product == "radklim":
        name = f"RW2017.002_{month:%Y%m}.tar.gz"
        url = f"{DWD}/reproc/2017_002/bin/{month:%Y}/{name}"
    elif month.year <= 2024:
        name = f"RW{month:%Y%m}.tar.gz"
        url = f"{DWD}/historical/bin/{month:%Y}/{name}"
    else:
        name = None
    if name is not None:
        archive = fetch(url)
        source = {"archive": name, "sha256": hashlib.sha256(archive).hexdigest()}
        for member, payload in iter_archive(archive):
            yield source, member, payload
        return
    # Operational files after the last yearly archive are served one by one.
    hours = pd.date_range(month, month + pd.offsets.MonthBegin(1), freq="h", inclusive="left")
    names = [f"raa01-rw_10000-{hour:%y%m%d%H}50-dwd---bin.gz" for hour in hours]

    def get(filename):
        try:
            return filename, fetch(f"{DWD}/recent/bin/{filename}", attempts=4)
        except Exception:  # pragma: no cover - a missing hour stays missing
            return filename, None

    digest = hashlib.sha256()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = sorted(pool.map(get, names))
    for _, payload in results:
        if payload is not None:
            digest.update(payload)
    source = {"archive": "recent/bin (individual files)", "sha256": digest.hexdigest()}
    for filename, payload in results:
        if payload is not None:
            yield source, filename, payload


def process_month(product, month, bounds):
    stamps, grids, clutter, source = [], [], 0, {}
    for archive_source, name, payload in monthly_files(product, month):
        source = archive_source
        match = STAMP.search(name)
        if not match or not match.group(1).endswith("50"):
            continue
        value, flagged = decode(payload, bounds)
        stamps.append(pd.to_datetime(match.group(1), format="%y%m%d%H%M", utc=True))
        grids.append(value)
        clutter += flagged
    end = pd.DatetimeIndex(stamps)
    order = end.argsort()
    end = end[order]
    shape = (round((bounds[3] - bounds[1]) / CELL), round((bounds[2] - bounds[0]) / CELL))
    data = np.stack(grids)[order] if grids else np.empty((0, *shape), dtype=np.int16)
    keep = ~end.duplicated()
    expected = pd.date_range(
        month, month + pd.offsets.MonthBegin(1), freq="h", tz="UTC", inclusive="left"
    ) + pd.Timedelta(minutes=50)
    return source | {
        "end_utc": end[keep],
        "data": data[keep],
        "n_files": int(keep.sum()),
        "n_expected": len(expected),
        "missing_end_utc": [str(stamp) for stamp in expected.difference(end)],
        "duplicate_stamps": int((~keep).sum()),
        "clutter_cells": clutter,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--product", choices=sorted(PRODUCTS), default="radolan")
    parser.add_argument("--start", default="2010-01")
    parser.add_argument("--end", default="2025-12")
    args = parser.parse_args()
    bounds = crop_bounds()
    output = PRODUCTS[args.product]["output"]
    crops = output / "crops"
    crops.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest.update(
        {
            "product": PRODUCTS[args.product]["name"],
            "source": DWD,
            "crs": RADOLAN_CRS,
            "crop_bounds_m": list(bounds),
            "cell_m": CELL,
            "bbox_wgs84": BBOX,
            "units": "0.1 mm per hour; -1 = no data",
            "timestamp": "end of the 60-minute accumulation (HH:50 UTC)",
        }
    )
    months = manifest.setdefault("months", {})
    prefix = "radklim_rw" if args.product == "radklim" else "radolan_rw"
    for month in pd.date_range(args.start, args.end, freq="MS"):
        key = f"{month:%Y-%m}"
        target = crops / f"{prefix}_{month:%Y%m}.npz"
        if key in months and target.exists():
            continue
        result = process_month(args.product, month, bounds)
        np.savez_compressed(
            target,
            end_utc=result["end_utc"].tz_convert(None).to_numpy(dtype="datetime64[m]"),
            rain_0p1mm=result["data"],
        )
        months[key] = {k: v for k, v in result.items() if k not in {"data", "end_utc"}} | {
            "crop_sha256": hashlib.sha256(target.read_bytes()).hexdigest()
        }
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
        print(
            f"{key}: {result['n_files']}/{result['n_expected']} hours, "
            f"{len(result['missing_end_utc'])} missing, clutter cells {result['clutter_cells']}",
            flush=True,
        )


if __name__ == "__main__":
    sys.exit(main())
