"""Build compact C2 raster summaries on the existing 394 reference catchments."""

import argparse
import fcntl
import importlib.util
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))

import ee
import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dise_regional_inputs import check_ids
from src.geoglows_experiment import disk_check, sha, write_json

BASE = ROOT / "results/limburg_representation_extension_v1"
OUT = BASE / "c2_multiyear_v1"
CATCHMENTS = BASE / "catchments.gpkg"
INVENTORY = BASE / "catchment_inventory.csv"
PROJECT = "limburg-511403"
WORLD = "ESA/WorldCover/v100"
TERRAIN = "CGIAR/SRTM90_V4"
CLAY = "projects/soilgrids-isric/clay_mean"
ERA = "ECMWF/ERA5_LAND/DAILY_AGGR"
COVER = dict(
    tree=10,
    shrub=20,
    grass=30,
    crop=40,
    built=50,
    bare=60,
    ice=70,
    water=80,
    wetland=90,
    mangrove=95,
    moss=100,
)
CLAY_NAMES = ("c2_clay_0_5cm_pct", "c2_clay_5_15cm_pct")
ERA_BANDS = tuple(f"volumetric_soil_water_layer_{i}" for i in range(1, 5)) + (
    "snow_depth_water_equivalent",
)
STATE = tuple(f"c2_prior_soil_water_layer_{i}" for i in range(1, 5)) + ("c2_prior_swe_mm",)
STATIC = tuple(f"c2_cover_{name}_fraction" for name in COVER) + (
    "c2_elevation_p90_minus_p10_m",
    *CLAY_NAMES,
)
DATES = pd.date_range("2017-12-31", "2025-12-30", tz="UTC")

# Reuse the established source acquisition retry and parquet receipts.
spec = importlib.util.spec_from_file_location(
    "regional_acquisition", ROOT / "scripts/267_acquire_dise_regional_inputs.py"
)
regional = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regional)


def summed_image(values, area_name):
    area = ee.Image.pixelArea().rename(area_name)
    area = area.updateMask(values.mask().reduce(ee.Reducer.min()))
    return values.multiply(area).addBands(area)


def reduce(image, reducer, gauges, projection):
    crs = projection.get("crs") or projection["wkt"]
    payload = regional.retry(
        lambda: image.reduceRegions(
            collection=gauges,
            reducer=reducer,
            crs=crs,
            crsTransform=projection["transform"],
            tileScale=4,
        ).getInfo()
    )
    return pd.DataFrame([feature["properties"] for feature in payload["features"]])


def static_task(kind, image, projection, gauges):
    if kind == "terrain":
        # Percentiles use Earth Engine's native-grid polygon-boundary weights.
        values = reduce(image, ee.Reducer.percentile([10, 90]), gauges, projection)
        area = reduce(
            ee.Image.pixelArea().rename("terrain_valid_m2").updateMask(image.mask()),
            ee.Reducer.sum().setOutputs(["terrain_valid_m2"]),
            gauges,
            projection,
        )
        values["c2_elevation_p90_minus_p10_m"] = values["p90"] - values["p10"]
        return values[["gauge", "c2_elevation_p90_minus_p10_m"]].merge(
            area[["gauge", "terrain_valid_m2"]], on="gauge", validate="one_to_one"
        )
    area_name = f"{kind}_valid_m2"
    values = reduce(summed_image(image, area_name), ee.Reducer.sum(), gauges, projection)
    cols = STATIC[: len(COVER)] if kind == "cover" else CLAY_NAMES
    cols = list(cols)
    values[cols] = values[cols].div(values[area_name].where(values[area_name].gt(0)), axis=0)
    return values[["gauge", area_name, *cols]]


def state_task(image, projection, gauges, dates):
    values = reduce(image, ee.Reducer.sum(), gauges, projection).set_index("gauge")
    records = []
    for day in dates:
        prefix = day.strftime("%Y%m%d_")
        part = values.reindex(columns=[prefix + name for name in (*STATE, "state_valid_m2")])
        part.columns = [*STATE, "state_valid_m2"]
        part = part.astype(float)
        part[list(STATE)] = part[list(STATE)].div(
            part.state_valid_m2.where(part.state_valid_m2.gt(0)), axis=0
        )
        records.append(part.assign(source_day=day).reset_index())
    return pd.concat(records, ignore_index=True)


def batch(kind, image, ids, geometry, dates=None):
    # Reproject the original polygons without replacing them by bounding boxes.
    fc = ee.FeatureCollection(
        [
            ee.Feature(
                ee.Geometry(geometry.loc[gauge].__geo_interface__, geodesic=False), {"gauge": gauge}
            )
            for gauge in ids
        ]
    )
    if dates is None:
        frame = static_task(kind, image[0], image[1], fc)
        check_ids(frame, ids)
    else:
        frame = state_task(image[0], image[1], fc, dates)
        keys = pd.MultiIndex.from_frame(frame[["gauge", "source_day"]])
        expected = pd.MultiIndex.from_product([ids, dates])
        if not keys.is_unique or len(keys) != len(expected) or not keys.isin(expected).all():
            raise ValueError("Changed antecedent-state gauge/day census")
    return frame


def acquire(extraction_sha=None):
    OUT.mkdir(exist_ok=True)
    disk_check(ROOT, 50, 2**30)
    inventory = pd.read_csv(INVENTORY, dtype={"gauge": str}).set_index("gauge")
    basins = gpd.read_file(CATCHMENTS).set_index("gauge")
    if not basins.index.is_unique or set(basins.index) != set(inventory.index):
        raise ValueError("Catchment geometry differs from the pinned inventory")
    geometry = basins.geometry.segmentize(1000).to_crs(4326)
    ee.Initialize(project=PROJECT)
    cover = ee.Image("ESA/WorldCover/v100/2020").select("Map")
    elevation = ee.Image(TERRAIN).select("elevation")
    clay = ee.Image(CLAY).select(["clay_0-5cm_mean", "clay_5-15cm_mean"], list(CLAY_NAMES))
    images = {
        "cover": (
            ee.Image.cat(
                [cover.eq(code).rename(f"c2_cover_{name}_fraction") for name, code in COVER.items()]
            ),
            cover.projection().getInfo(),
            6,
            WORLD,
        ),
        "terrain": (elevation, elevation.projection().getInfo(), 20, TERRAIN),
        "clay": (clay.divide(10), clay.select(0).projection().getInfo(), 20, CLAY),
    }
    era = ee.ImageCollection(ERA).filterDate("2017-12-31", "2025-12-31").sort("system:time_start")
    calendar = pd.to_datetime(
        era.aggregate_array("system:time_start").getInfo(), unit="ms", utc=True
    )
    if not calendar.equals(DATES):
        raise ValueError("Unexpected ERA5-Land daily source calendar")
    projection = era.first().select(ERA_BANDS[0]).projection().getInfo()
    common = {
        str(path.relative_to(ROOT)): sha(path)
        for path in (
            CATCHMENTS,
            INVENTORY,
            Path(__file__),
            Path(regional.__file__),
            ROOT / "src/dise_regional_inputs.py",
            ROOT / "src/geoglows_experiment.py",
        )
    }
    batch_inputs = dict(common)
    if extraction_sha is not None:
        batch_inputs[str(Path(__file__).relative_to(ROOT))] = extraction_sha

    def data_batch(kind, tag, ids, image, transform, source, dates):
        path = OUT / "inputs" / kind / f"{tag}.parquet"
        ident = dict(
            kind=kind, gauges=ids, source=source, projection=transform, inputs=batch_inputs
        )
        if dates is not None:
            ident.update(
                start=str(dates[0].date()), end=str(dates[-1].date()), bands=list(ERA_BANDS)
            )
        receipt = path.with_suffix(".parquet.receipt.json")
        if not receipt.exists() or not regional.verified(path, ident):
            if extraction_sha is not None:
                raise ValueError(f"Cannot resume finalization without a verified batch: {path}")
            frame = batch(kind, (image, transform), ids, geometry, dates)
            regional.save(frame, path, ident)
        return path

    def reduce_batches(pool, kind, image, transform, size, source, prefix, dates=None):
        ids = sorted(geometry.index)
        paths = list(
            pool.map(
                lambda item: data_batch(
                    kind, f"{prefix}{item[0]:03d}", item[1], image, transform, source, dates
                ),
                enumerate([ids[i : i + size] for i in range(0, len(ids), size)]),
            )
        )
        print(f"{kind} {prefix}: verified {len(paths)} batches", flush=True)
        return paths

    with ThreadPoolExecutor(max_workers=2) as pool:
        static = []
        for kind, (image, transform, size, source) in images.items():
            paths = reduce_batches(pool, kind, image, transform, size, source, "batch_")
            static.append(pd.concat(map(pd.read_parquet, paths)).set_index("gauge"))
        static = pd.concat(static, axis=1, join="outer").reset_index()
        check_ids(static, geometry.index)
        state = []
        for year in sorted(set(DATES.year)):
            dates = DATES[DATES.year == year]
            daily = era.filterDate(
                str(dates[0].date()), str((dates[-1] + pd.Timedelta(days=1)).date())
            )
            stack = daily.map(
                lambda img: summed_image(
                    img.select(list(ERA_BANDS), list(STATE)).multiply(
                        ee.Image.constant([1, 1, 1, 1, 1000])
                    ),
                    "state_valid_m2",
                ).set("system:index", img.date().format("YYYYMMdd"))
            ).toBands()
            paths = reduce_batches(pool, "state", stack, projection, 24, ERA, f"{year}_", dates)
            state.extend(map(pd.read_parquet, paths))
        state = pd.concat(state, ignore_index=True)

    # ERA5-Land returns tiny negative numerical residues where snow is absent.
    # Correct only values indistinguishable from zero in millimetres.
    swe = state[STATE[-1]]
    roundoff_mm = 1e-12
    roundoff = swe.ge(-roundoff_mm) & swe.lt(0)
    state[STATE[-1]] = swe.mask(roundoff, 0)
    audit = {}
    area_m2 = basins.area.rename("polygon_m2")
    for name in ("cover", "terrain", "clay"):
        ratio = static.set_index("gauge")[f"{name}_valid_m2"].div(area_m2)
        audit[name] = dict(
            missing=int(ratio.isna().sum()),
            zero=int(ratio.eq(0).sum()),
            min=float(ratio.min()),
            median=float(ratio.median()),
            max=float(ratio.max()),
        )
    ratio = state.state_valid_m2.div(state.gauge.map(area_m2))
    audit["state"] = dict(
        missing=int(ratio.isna().sum()),
        zero=int(ratio.eq(0).sum()),
        min=float(ratio.min()),
        median=float(ratio.median()),
        max=float(ratio.max()),
        snow_zero=int(state[STATE[-1]].eq(0).sum()),
        swe_roundoff_to_zero=int(roundoff.sum()),
        swe_roundoff_tolerance_mm=roundoff_mm,
        minimum_raw_swe_mm=float(swe.min()),
    )
    if not np.allclose(static[list(STATIC[: len(COVER)])].dropna().sum(axis=1), 1, atol=1e-6):
        raise ValueError("WorldCover class fractions do not account for mapped area")
    for frame, ranges in (
        (static, {**dict.fromkeys(CLAY_NAMES, (0, 100)), STATIC[-3]: (0, 9000)}),
        (state, {**dict.fromkeys(STATE[:-1], (0, 1)), STATE[-1]: (0, 15000)}),
    ):
        for col, (low, high) in ranges.items():
            if not frame[col].dropna().between(low, high).all():
                raise ValueError(f"Out-of-range values for {col}")
    audit["missing_predictors"] = {
        **static[list(STATIC)].isna().sum().to_dict(),
        **state[list(STATE)].isna().sum().to_dict(),
    }
    for name, frame in (("landscape", static), ("antecedent_state", state)):
        regional.save(frame, OUT / "inputs" / f"{name}.parquet", common)
    write_json(
        OUT / "source_audit.json",
        dict(
            status="completed",
            gauges=len(basins),
            state_rows=len(state),
            extraction_inputs=batch_inputs,
            finalization_inputs=common,
            coverage=audit,
            projections={**{k: v[1] for k, v in images.items()}, "state": projection},
            sources={**{k: v[3] for k, v in images.items()}, "state": ERA},
            files={
                name: sha(OUT / "inputs" / name)
                for name in ("landscape.parquet", "antecedent_state.parquet")
            },
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-extraction-sha")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    with (OUT / "acquisition.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not (OUT / "source_audit.json").exists():
            acquire(args.reuse_extraction_sha)
