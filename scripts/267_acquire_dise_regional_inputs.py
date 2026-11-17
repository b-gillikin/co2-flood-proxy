"""Acquire matched regional Q, ERA5-Land, 2017 AlphaEarth and fair landscape controls.

Compact catchment tables only. Explicit spatial flags remain; no model fitting.
Use .venv-geoglows, whose existing Zarr/S3 runtime is isolated from fitted models.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.dise import daily_hour_end
from src.dise_regional_inputs import selected_mapping, spatial_table, weather_table
from src.geoglows_experiment import disk_check, hour_end, sha, write_json

CONFIG = ROOT / "config/limburg_dise_regional_inputs_v1.json"
PLAN = json.loads(CONFIG.read_text())
RAW = ROOT / PLAN["raw"]
OUT = ROOT / PLAN["output"]
BANDS = [f"A{i:02d}" for i in range(64)]
ATTRS = [
    "a_elevation_m",
    "a_slope_deg",
    "a_tree_cover_fraction",
    "a_crop_cover_fraction",
    "a_urban_cover_fraction",
    "a_surface_field_capacity_pct",
]
LOCK = threading.Lock()
PROGRESS = {}


def update(component, done, total, **extra):
    with LOCK:
        PROGRESS[component] = dict(
            done=done, total=total, percent=100 * done / total if total else 100, **extra
        )
        write_json(
            OUT / "progress.json",
            dict(
                updated_utc=datetime.now(timezone.utc).isoformat(),
                components=PROGRESS,
                free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
            ),
        )
    print(f"{component}: {done}/{total} ({100 * done / total if total else 100:.1f}%)", flush=True)


def identity(component, **extra):
    return dict(
        component=component,
        config_sha256=sha(CONFIG),
        mapping_sha256=sha(ROOT / PLAN["mapping"]),
        catchments_sha256=sha(ROOT / PLAN["catchments"]),
        **extra,
    )


def verified(path, expected):
    rec = path.with_suffix(path.suffix + ".receipt.json")
    if not path.exists():
        return False
    old = json.loads(rec.read_text())
    if old["identity"] != expected or old["sha256"] != sha(path):
        raise ValueError(f"Existing source differs; preserve/version rather than overwrite: {path}")
    return True


def save(frame, path, expected, **extra):
    path.parent.mkdir(parents=True, exist_ok=True)
    disk_check(ROOT, PLAN["reserve_gib"], max(2**20, int(frame.memory_usage(deep=True).sum())))
    tmp = path.with_suffix(path.suffix + ".partial")
    frame.to_parquet(tmp, index=False)
    tmp.replace(path)
    write_json(
        path.with_suffix(path.suffix + ".receipt.json"),
        dict(
            identity=expected,
            sha256=sha(path),
            rows=len(frame),
            acquired_utc=datetime.now(timezone.utc).isoformat(),
            **extra,
        ),
    )


def retry(func):
    for attempt in range(3):
        try:
            return func()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def acquire_q(mapping):
    import s3fs
    import xarray as xr

    fs = s3fs.S3FileSystem(
        anon=True, client_kwargs={"region_name": "us-west-2"}, default_fill_cache=False
    )
    prefix = PLAN["geoglows_uri"].removeprefix("s3://")
    metadata = fs.cat(prefix + "/.zmetadata")
    path = RAW / "geoglows-zarr-metadata.json"
    if path.exists() and path.read_bytes() != metadata:
        raise ValueError(
            "Remote Zarr metadata changed; retain pinned source and version acquisition"
        )
    path.write_bytes(metadata)
    ds = xr.open_zarr(fs.get_mapper(prefix), consolidated=True, chunks=None)
    if (
        ds.Q.attrs.get("units") not in ["m3 s-1", "m3/s"]
        or ds.Q.attrs.get("aggregation_method") != "mean"
    ):
        raise ValueError("Unexpected Q units/aggregation")
    ids = np.unique(mapping.best_river_id.to_numpy(dtype="int64"))
    coord = np.asarray(ds.river_id.values)
    index = pd.Index(coord).get_indexer(ids)
    if (index < 0).any():
        raise ValueError("Recorded model river absent from source coordinate")
    zmeta = json.loads(metadata)["metadata"]["Q/.zarray"]
    axis = list(ds.Q.dims).index("river_id")
    storage_groups = index // zmeta["chunks"][axis]
    first, last = f"{min(PLAN['years'])}-01-01", f"{max(PLAN['years'])}-12-31T23:00:00"
    expected_days = pd.date_range(first, f"{max(PLAN['years'])}-12-31", tz="UTC")
    done = 0
    update(
        "geoglows_reaches",
        done,
        len(ids),
        status="running",
        storage_groups=len(set(storage_groups)),
    )
    for group in np.unique(storage_groups):
        rivers = ids[storage_groups == group]
        pending = []
        for river in rivers:
            dest = RAW / "geoglows" / f"{river}.parquet"
            ident = identity(
                "geoglows_hourly_to_daily",
                river_id=int(river),
                metadata_sha256=sha(path),
                first=first,
                last=last,
                clock=PLAN["geoglows_clock"],
            )
            if verified(dest, ident):
                done += 1
            else:
                pending.append((river, dest, ident))
        if pending:
            # Read all requested rivers in this physical chunk together, avoiding
            # repeated decompression of the full 85-year/20-river source block.
            values = retry(
                lambda pending=pending: ds.Q.sel(
                    river_id=[int(x[0]) for x in pending], time=slice(first, last)
                ).load()
            )
            for river, dest, ident in pending:
                hourly = hour_end(values.sel(river_id=int(river)).to_series()).rename("q_model_m3s")
                daily, counts = daily_hour_end(hourly.to_frame())
                daily = daily.reindex(expected_days)
                frame = pd.DataFrame(
                    dict(
                        day=expected_days,
                        q_model_m3s=daily.iloc[:, 0].to_numpy(),
                        model_hours=counts.iloc[:, 0]
                        .reindex(expected_days, fill_value=0)
                        .to_numpy(),
                        river_id=int(river),
                    )
                )
                save(
                    frame,
                    dest,
                    ident,
                    finite_days=int(frame.q_model_m3s.notna().sum()),
                    clock=PLAN["geoglows_clock"],
                    attrs=dict(ds.Q.attrs),
                )
                done += 1
        update("geoglows_reaches", done, len(ids), status="running")
    if fs.cat(prefix + "/.zmetadata") != metadata:
        raise ValueError("GEOGLOWS metadata changed during source acquisition")
    update("geoglows_reaches", done, len(ids), status="completed")


def ee_features(ee, rows, geometries):
    features = []
    for row in rows.itertuples(index=False):
        geom = geometries.loc[row.gauge_id]
        props = dict(gauge=row.gauge_id, geometry_sha256=hashlib.sha256(geom.wkb).hexdigest())
        features.append(ee.Feature(ee.Geometry(geom.__geo_interface__), props))
    return ee.FeatureCollection(features)


def acquire_weather(ee, mapping, geometries):
    size = PLAN["weather_batch_size"]
    batches = [mapping.iloc[i : i + size] for i in range(0, len(mapping), size)]
    total = len(batches) * len(PLAN["years"])
    done = 0
    update("weather_batches", done, total, status="running")
    for year in PLAN["years"]:
        collection = ee.ImageCollection(PLAN["weather_collection"]).filterDate(
            f"{year}-01-01", f"{year + 1}-01-01"
        )
        projection = collection.first().select(PLAN["weather_bands"][0]).projection().getInfo()
        stacked = (
            collection.select(PLAN["weather_bands"])
            .map(lambda im: im.set("system:index", im.date().format("YYYYMMdd")))
            .toBands()
        )
        area = (
            ee.Image.pixelArea()
            .rename("sampled_area_m2")
            .updateMask(stacked.mask().reduce(ee.Reducer.min()))
        )
        image = stacked.multiply(area).addBands(area)
        for batch, rows in enumerate(batches):
            gauges = rows.gauge_id.tolist()
            dest = RAW / "weather" / f"{year}_batch{batch:03d}.parquet"
            ident = identity(
                "weather",
                year=year,
                gauges=gauges,
                collection=PLAN["weather_collection"],
                bands=PLAN["weather_bands"],
                projection=projection,
                aggregation="native-grid pixel-area/fraction-weighted mean; common valid support",
            )
            if not verified(dest, ident):
                fc = ee_features(ee, rows, geometries)
                data = retry(
                    lambda image=image, fc=fc, projection=projection: image.reduceRegions(
                        collection=fc,
                        reducer=ee.Reducer.sum(),
                        crs=projection["crs"],
                        crsTransform=projection["transform"],
                        tileScale=2,
                    ).getInfo()
                )
                frame = weather_table(data["features"], year, PLAN["weather_bands"], gauges)
                save(
                    frame,
                    dest,
                    ident,
                    missing_by_band=frame[PLAN["weather_bands"]].isna().sum().to_dict(),
                    negative_accumulations={
                        b: int(frame[b].lt(0).sum())
                        for b in PLAN["weather_bands"]
                        if b.endswith("_sum")
                    },
                    source_dates=retry(
                        lambda collection=collection: collection.aggregate_array(
                            "system:time_start"
                        ).getInfo()
                    ),
                )
            done += 1
            update("weather_batches", done, total, status="running")
    update("weather_batches", done, total, status="completed")


def acquire_spatial(ee, mapping, geometries):
    for kind in ["alphaearth", "attributes"]:
        size = PLAN[f"{kind}_batch_size"]
        done = 0
        batches = [mapping.iloc[i : i + size] for i in range(0, len(mapping), size)]
        update(kind + "_batches", done, len(batches), status="running")
        for batch, rows in enumerate(batches):
            gauges = rows.gauge_id.tolist()
            dest = RAW / kind / f"batch{batch:03d}.parquet"
            common = dict(gauges=gauges, crs=PLAN[f"{kind}_crs"], scale_m=PLAN[f"{kind}_scale_m"])
            if kind == "alphaearth":
                common.update(
                    collection=PLAN["alphaearth_collection"],
                    year=PLAN["alphaearth_year"],
                    bands=BANDS,
                )
            else:
                common.update(sources=PLAN["attributes_sources"], bands=ATTRS)
            ident = identity(kind, **common)
            if not verified(dest, ident):
                fc = ee_features(ee, rows, geometries)
                if kind == "alphaearth":
                    year = PLAN["alphaearth_year"]
                    collection = (
                        ee.ImageCollection(PLAN["alphaearth_collection"])
                        .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
                        .filterBounds(fc.geometry())
                    )
                    image = collection.mosaic().select(BANDS)
                    reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
                    source_ids = retry(
                        lambda collection=collection: collection.aggregate_array(
                            "system:index"
                        ).getInfo()
                    )
                else:
                    dem = ee.Image(PLAN["attributes_sources"][0]).select("elevation")
                    lc = ee.Image(PLAN["attributes_sources"][1])
                    image = ee.Image.cat(
                        [
                            dem.rename(ATTRS[0]),
                            ee.Terrain.slope(dem).rename(ATTRS[1]),
                            lc.select("tree-coverfraction").divide(100).rename(ATTRS[2]),
                            lc.select("crops-coverfraction").divide(100).rename(ATTRS[3]),
                            lc.select("urban-coverfraction").divide(100).rename(ATTRS[4]),
                            ee.Image(PLAN["attributes_sources"][2]).select("b0").rename(ATTRS[5]),
                        ]
                    )
                    area = (
                        ee.Image.pixelArea()
                        .rename("area_m2")
                        .updateMask(image.mask().reduce(ee.Reducer.min()))
                    )
                    image = image.multiply(area).addBands(area)
                    reducer = ee.Reducer.sum()
                    source_ids = PLAN["attributes_sources"]
                data = retry(
                    lambda image=image, fc=fc, reducer=reducer, common=common: image.reduceRegions(
                        collection=fc,
                        reducer=reducer,
                        crs=common["crs"],
                        scale=common["scale_m"],
                        tileScale=4,
                    ).getInfo()
                )
                frame = spatial_table(
                    data["features"], gauges, kind, BANDS if kind == "alphaearth" else ATTRS
                )
                if kind == "alphaearth":
                    frame["embedding_year"] = PLAN["alphaearth_year"]
                save(
                    frame,
                    dest,
                    ident,
                    source_ids=source_ids,
                    coverage_status=frame.coverage_status.value_counts().to_dict(),
                )
            done += 1
            update(kind + "_batches", done, len(batches), status="running")
        update(kind + "_batches", done, len(batches), status="completed")


def summarize(mapping):
    summary = {}
    for component in ["geoglows", "weather", "alphaearth", "attributes"]:
        paths = sorted((RAW / component).glob("*.parquet"))
        if not paths:
            raise ValueError(f"No {component} inputs")
        table = pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)
        if component == "geoglows":
            table = (
                mapping[
                    [
                        "gauge_id",
                        "best_river_id",
                        "resolved_role",
                        "geometry_review_flag",
                        "reference_area_km2",
                    ]
                ]
                .rename(columns={"gauge_id": "gauge", "best_river_id": "river_id"})
                .merge(table, on="river_id", validate="many_to_many")
            )
            if table.duplicated(["gauge", "day"]).any():
                raise ValueError("Duplicated matched model day")
            table["q_model"] = table.q_model_m3s * 86.4 / table.reference_area_km2
        elif component == "weather":
            if table.duplicated(["gauge", "day"]).any():
                raise ValueError("Duplicated weather day")
        else:
            if table.gauge.duplicated().any():
                raise ValueError("Duplicated spatial gauge")
        if set(table.gauge) != set(mapping.gauge_id):
            raise ValueError(f"{component} population differs")
        dest = OUT / f"{component}.parquet"
        save(
            table,
            dest,
            identity("combined_" + component),
            source_hashes={str(p.relative_to(ROOT)): sha(p) for p in paths},
        )
        summary[component] = dict(
            rows=len(table), gauges=int(table.gauge.nunique()), sha256=sha(dest)
        )
    write_json(
        OUT / "receipt.json",
        dict(
            status="completed",
            inputs=summary,
            source_inputs_acquired_not_a_final_validated_model_cohort=True,
            mapping_sha256=sha(ROOT / PLAN["mapping"]),
            free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
            no_model_fit_started=True,
        ),
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase", choices=["all", "q", "weather", "spatial", "summarize"], default="all", nargs="?"
    )
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    lock = (OUT / "acquisition.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    disk_check(ROOT, PLAN["reserve_gib"], 512 * 2**20)
    mapping = selected_mapping(pd.read_csv(ROOT / PLAN["mapping"]), PLAN["roles"])
    for component, total in [
        ("geoglows_reaches", mapping.best_river_id.nunique()),
        ("weather_batches", ((len(mapping) + 31) // 32) * len(PLAN["years"])),
        ("alphaearth_batches", (len(mapping) + 7) // 8),
        ("attributes_batches", (len(mapping) + 31) // 32),
    ]:
        PROGRESS[component] = dict(done=0, total=int(total), percent=0, status="queued")
    if args.phase in ["all", "weather", "spatial"]:
        import ee
        import geopandas as gpd

        ee.Initialize(project=PLAN["earth_engine_project"])
        geometry = (
            gpd.read_file(ROOT / PLAN["catchments"]).to_crs(4326).set_index("gauge_id").geometry
        )
        if set(mapping.gauge_id) - set(geometry.index):
            raise ValueError("Missing reference polygons")
    if args.phase == "all":
        jobs = {
            "geoglows": lambda: acquire_q(mapping),
            "weather": lambda: acquire_weather(ee, mapping, geometry),
            "spatial": lambda: acquire_spatial(ee, mapping, geometry),
        }
        failures = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            tasks = {pool.submit(fn): name for name, fn in jobs.items()}
            for future in as_completed(tasks):
                name = tasks[future]
                try:
                    future.result()
                except Exception as exc:
                    failures[name] = repr(exc)
                    print(name, repr(exc), flush=True)
                    write_json(OUT / "failures.json", failures)
        if failures:
            raise RuntimeError(f"Unresolved input acquisition: {failures}")
        print(json.dumps(summarize(mapping)), flush=True)
    elif args.phase == "q":
        acquire_q(mapping)
    elif args.phase == "weather":
        acquire_weather(ee, mapping, geometry)
    elif args.phase == "spatial":
        acquire_spatial(ee, mapping, geometry)
    else:
        print(json.dumps(summarize(mapping)), flush=True)


if __name__ == "__main__":
    main()
