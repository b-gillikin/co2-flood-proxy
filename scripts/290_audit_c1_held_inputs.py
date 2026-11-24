"""Audit held C1 inputs and coverage without assembling a model feature table."""

import gzip
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from shapely import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dise_regional import WEATHER
from src.geoglows_experiment import sha, write_json

EXTENSION = ROOT / "results/limburg_representation_extension_v1"
RAW = ROOT / "data/raw/limburg_dise_v1"
REGIONAL = ROOT / "results/limburg_dise_v2/regional_inputs_resolved_v1"
BASELINE = ROOT / "results/limburg_dise_regional_benchmark_v1/preparation"
LAND_STATE = ROOT / "data/raw/limburg_monitoring_land_state"
ATTRIBUTES = [
    "a_elevation_m",
    "a_slope_deg",
    "a_tree_cover_fraction",
    "a_crop_cover_fraction",
    "a_urban_cover_fraction",
    "a_surface_field_capacity_pct",
]
DAILY_UNITS = dict(
    zip(WEATHER, ["m/day", "K", "K", "Pa", "m/s", "m/s", "J/m²/day", "J/m²/day"], strict=True)
)
ACCUMULATIONS = [column for column in WEATHER if column.endswith("_sum")]


def checked_hash(path, expected=None):
    actual = sha(path)
    if expected is not None and actual != expected:
        raise ValueError(f"Checksum mismatch for {path}")
    return actual


def census_coverage(frame, gauges):
    return (
        frame.reindex(gauges.index)
        .assign(role=gauges.source_role)
        .groupby("role")
        .sum(numeric_only=True)
        .astype(int)
        .to_dict(orient="index")
    )


def weather_audit(gauges, hashes):
    local_paths = sorted((RAW / "weather").glob("local_daily_*.parquet"))
    regional = REGIONAL / "weather.parquet"
    local = []
    for path in local_paths:
        receipt = json.loads(path.with_suffix(".parquet.receipt.json").read_text())
        hashes[str(path.relative_to(ROOT))] = checked_hash(path, receipt["sha256"])
        local.append(pd.read_parquet(path))
    weather = pd.concat([*local, pd.read_parquet(regional)], ignore_index=True)
    calendar = pd.date_range("2017-01-01", "2025-12-31", tz="UTC")
    expected = pd.MultiIndex.from_product([gauges.index, calendar], names=["gauge", "day"])
    actual = pd.MultiIndex.from_frame(weather[["gauge", "day"]])
    if not actual.is_unique or len(actual) != len(expected) or not actual.isin(expected).all():
        raise ValueError("Held weather rows differ from the gauge and UTC day census")
    if not np.isfinite(weather.sampled_area_m2).all() or not weather.sampled_area_m2.gt(0).all():
        raise ValueError("Weather zonal means have invalid sampled area")
    result = {"native_units": DAILY_UNITS, "gauges": len(gauges), "rows_2017_2025": len(weather)}
    for name, subset in (
        ("2017_2025", weather),
        ("2020", weather.loc[weather.day.dt.year.eq(2020)]),
    ):
        values = subset[list(WEATHER)]
        finite = np.isfinite(values)
        negative = values[ACCUMULATIONS].lt(0)
        usable = values.where(finite)
        usable[ACCUMULATIONS] = usable[ACCUMULATIONS].mask(negative)
        monthly = usable.groupby([subset.gauge, subset.day.dt.year, subset.day.dt.month]).count()
        result[name] = {
            "rows": len(subset),
            "nonfinite_by_band": (~finite).sum().to_dict(),
            "negative_accumulations": negative.sum().to_dict(),
            "gauges_complete_by_band": census_coverage(
                usable.notna().groupby(subset.gauge).all(), gauges
            ),
            "monthly_cells_with_no_usable_days_by_band": monthly.eq(0).sum().to_dict(),
        }
        if name == "2020":
            precip = usable["total_precipitation_sum"]
            summaries = usable.groupby(subset.gauge).mean()
            summaries["precip_total_mm"] = precip.groupby(subset.gauge).sum(min_count=366).mul(1000)
            summaries["days_precip_at_least_1mm"] = (
                precip.ge(0.001).where(precip.notna()).groupby(subset.gauge).sum(min_count=366)
            )
            result[name]["annual_audit_summary_coverage"] = census_coverage(
                summaries.notna(), gauges
            )
            result[name]["precip_total_mm_range"] = [
                float(summaries.precip_total_mm.min()),
                float(summaries.precip_total_mm.max()),
            ]
    return result


def footprint_coverage(gauges, boxes):
    bounds = gpd.GeoSeries(boxes, crs=4326).segmentize(0.01).to_crs(gauges.crs).union_all()
    fraction = (gauges.geometry.intersection(bounds).area / gauges.geometry.area).clip(0, 1)
    coverage = pd.DataFrame({"full": fraction.ge(1 - 1e-8), "none": fraction.le(1e-12)})
    coverage["partial"] = ~(coverage.full | coverage.none)
    return {
        "support_by_role": census_coverage(coverage, gauges),
        "footprint_fraction_by_gauge": fraction.to_dict(),
    }


def hourly_grid_audit(gauges, folder, prefix, first_year, fields):
    months = pd.period_range(f"{first_year}-01", "2025-12", freq="M")
    manifest_path = folder / "manifest.csv"
    manifest = (
        pd.read_csv(manifest_path).set_index(["year", "month"]) if manifest_path.exists() else None
    )
    receipts = {}
    grid = None
    units = None
    hours_2020 = 0
    for month in months:
        stem = f"{prefix}_{month.strftime('%Y_%m')}"
        path = folder / f"{stem}.nc"
        if manifest is None:
            receipt = json.loads((folder / f"{stem}.receipt.json").read_text())
        else:
            receipt = manifest.loc[(month.year, month.month)]
        receipts[path.name] = checked_hash(path, receipt["sha256"])
        if month.year != 2020:
            continue
        with xr.open_dataset(path) as ds:
            time = "valid_time" if "valid_time" in ds.coords else "time"
            target = pd.date_range(month.start_time, periods=month.days_in_month * 24, freq="h")
            if not pd.DatetimeIndex(ds[time].values).equals(target):
                raise ValueError(f"Incomplete 2020 hourly calendar in {path.name}")
            current_grid = (ds.longitude.to_numpy().tolist(), ds.latitude.to_numpy().tolist())
            current_units = {column: ds[column].attrs["units"] for column in fields}
            if grid is not None and (current_grid != grid or current_units != units):
                raise ValueError(f"Grid or units changed in {path.name}")
            grid, units = current_grid, current_units
            if not all(np.isfinite(ds[column].to_numpy()).all() for column in fields):
                raise ValueError(f"Found missing ERA5-Land pixels in {path.name}")
            hours_2020 += len(target)
    lon, lat = grid
    if not all(np.allclose(np.abs(np.diff(axis)), 0.1) for axis in grid):
        raise ValueError(f"Unexpected native grid spacing in {prefix}")
    cells = [box(x - 0.05, y - 0.05, x + 0.05, y + 0.05) for y in lat for x in lon]
    return {
        "verified_months": len(receipts),
        "period": [str(months[0]), str(months[-1])],
        "hours_checked_2020": hours_2020,
        "units": units,
        "cell_size_degrees": 0.1,
        "grid_shape": [len(lat), len(lon)],
        **footprint_coverage(gauges, cells),
        "file_sha256": receipts,
    }


def static_audit(gauges, hashes):
    path = RAW / "local_attributes_v2.parquet"
    local_receipt = json.loads(path.with_suffix(".parquet.receipt.json").read_text())
    hashes[str(path.relative_to(ROOT))] = checked_hash(path, local_receipt["sha256"])
    attrs = pd.concat(
        [pd.read_parquet(path), pd.read_parquet(REGIONAL / "attributes.parquet")]
    ).set_index("gauge")
    if not attrs.index.is_unique or set(attrs.index) != set(gauges.index):
        raise ValueError("Conventional attributes do not match the gauge census")
    values = attrs[ATTRIBUTES]
    if (
        not attrs.area_m2.gt(0).all()
        or not values.filter(like="fraction").apply(lambda s: s.between(0, 1)).all().all()
    ):
        raise ValueError("Invalid terrain/land-cover support or fraction")
    area_ratios = attrs.area_m2 / gauges.geometry.area
    paths = sorted((RAW / "camels").glob("*attributes.csv"))
    camels = {}
    for p in paths:
        receipt = json.loads(p.with_suffix(".csv.receipt.json").read_text())
        hashes[str(p.relative_to(ROOT))] = checked_hash(p, receipt["sha256"])
        data = pd.read_csv(p, dtype={"gauge_id": str}).set_index("gauge_id")
        if not data.index.is_unique:
            raise ValueError(f"Duplicate CAMELS gauge IDs in {p.name}")
        camels[p.stem.removeprefix("CAMELS_DE_1h_").removesuffix("_attributes")] = dict(
            direct_gauge_ids=census_coverage(
                pd.DataFrame({"matched": gauges.index.isin(data.index)}, index=gauges.index), gauges
            ),
            columns=data.columns.tolist(),
        )
    met_fields = {
        "air_temperature_mean",
        "air_temperature_min",
        "air_temperature_max",
        "precipitation_mean_gapfilled",
    }
    camels_root = ROOT / "data/raw/limburg_dise_v2"
    met_headers = {}
    for directory in ("camels_timeseries", "spatial_supplement_v1/observations"):
        for source in sorted((camels_root / directory).glob("*.csv.gz")):
            with gzip.open(source, "rt") as stream:
                met_headers[source.name.removesuffix(".csv.gz")] = met_fields.issubset(
                    stream.readline().strip().split(",")
                )
    terrain = {}
    for p in sorted((ROOT / "data/raw/dem/glo30").glob("*.tif")):
        with rasterio.open(p) as ds:
            if ds.crs.to_epsg() != 4326:
                raise ValueError(f"Unexpected GLO-30 CRS in {p.name}")
            terrain[p.name] = box(*ds.bounds)
        hashes[str(p.relative_to(ROOT))] = sha(p)
    geometry = pd.DataFrame(
        {
            "area_km2": gauges.geometry.area / 1e6,
            "perimeter_km": gauges.geometry.length / 1000,
            "compactness": 4 * np.pi * gauges.geometry.area / gauges.geometry.length.pow(2),
        }
    )
    return {
        "finite_values_by_role": census_coverage(np.isfinite(values), gauges),
        "geometry_check_by_role": census_coverage(np.isfinite(geometry), gauges),
        "common_sampled_to_processing_area_ratio": [
            float(area_ratios.min()),
            float(area_ratios.max()),
        ],
        "source_receipt": local_receipt["identity"],
        "camels_de_tables": camels,
        "camels_de_hourly_fields_present_by_role": census_coverage(
            gauges.index.to_series().map(met_headers).eq(True).to_frame("headers_present"), gauges
        ),
        "glo30": {"tiles": list(terrain), **footprint_coverage(gauges, list(terrain.values()))},
    }


def discharge_audit(gauges, manifest, hashes):
    path = BASELINE / "features.parquet"
    hashes[str(path.relative_to(ROOT))] = checked_hash(path, manifest["feature_sha256"])
    f = pd.read_parquet(
        path, columns=["gauge", "day", "source_role", "q_model_m3s", "q_observed_m3s"]
    )
    if len(f) != manifest["rows"] or not f.gauge.map(gauges.source_role).eq(f.source_role).all():
        raise ValueError("Discharge features do not match the saved census and roles")
    support = (
        f.assign(year=f.day.dt.year)
        .groupby(["source_role", "year"])
        .agg(
            calendar_rows=("day", "size"),
            observed_values=("q_observed_m3s", "count"),
            modelled_values=("q_model_m3s", "count"),
        )
    )
    return {"unit": "m³/s", "rows_by_role_year": support.reset_index().to_dict(orient="records")}


def main():
    geometry = EXTENSION / "catchments.gpkg"
    gauges = gpd.read_file(geometry).set_index("gauge")
    if not gauges.index.is_unique or len(gauges) != 394 or not gauges.geometry.is_valid.all():
        raise ValueError("Expected the 394 valid processing catchments")
    manifest = json.loads((BASELINE / "manifest.json").read_text())
    hashes = {str(geometry.relative_to(ROOT)): sha(geometry)}
    for path in (
        REGIONAL / "weather.parquet",
        REGIONAL / "attributes.parquet",
        REGIONAL / "geoglows.parquet",
        REGIONAL / "observations.parquet",
    ):
        rel = str(path.relative_to(ROOT))
        hashes[rel] = checked_hash(path, manifest["input_hashes"][rel])
    quality = json.loads((EXTENSION / "alphaearth_2020/quality_2020.json").read_text())
    checked_hash(geometry, quality["geometry_sha256"])
    for name, path, digest_key, prefix, dimensions in (
        (
            "AlphaEarth",
            EXTENSION / "alphaearth_2020/descriptors_2020.parquet",
            "alphaearth_parquet_sha256",
            "A",
            64,
        ),
        (
            "TESSERA",
            EXTENSION / "tessera_census_2020/descriptors_2020.csv",
            "tessera_csv_sha256",
            "tessera_",
            128,
        ),
    ):
        hashes[str(path.relative_to(ROOT))] = checked_hash(path, quality[digest_key])
        frame = (pd.read_csv(path) if path.suffix == ".csv" else pd.read_parquet(path)).set_index(
            "gauge"
        )
        vectors = frame.filter(regex=rf"^{prefix}[0-9]+$")
        if (
            not frame.index.is_unique
            or set(frame.index) != set(gauges.index)
            or vectors.shape[1] != dimensions
            or not np.isfinite(vectors).all().all()
        ):
            raise ValueError(f"Incomplete {name} vectors")
    result = {
        "status": "held_inputs_audited",
        "gauge_roles": gauges.source_role.value_counts().to_dict(),
        "weather": weather_audit(gauges, hashes),
        "static": static_audit(gauges, hashes),
        "discharge": discharge_audit(gauges, manifest, hashes),
        "soil_snow": hourly_grid_audit(
            gauges, LAND_STATE, "era5_land_monitoring", 2009, ["swvl1", "swvl2", "sd"]
        ),
        "hourly_temperature": hourly_grid_audit(
            gauges, ROOT / "data/raw/era5_land", "era5_land_limburg", 2001, ["t2m", "d2m", "sp"]
        ),
        "input_sha256": hashes,
        "baseline_predictors": [
            column for column in manifest["predictors"] if not column.startswith("e_")
        ],
        "model_fit_started": False,
        "downloads_started": False,
    }
    path = EXTENSION / "c1_held_input_audit.json"
    write_json(path, result)
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
