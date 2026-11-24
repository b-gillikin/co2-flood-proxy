"""Verify 2020 native-grid inputs held for the catchment encoder pilot."""

import importlib
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely import box

held = importlib.import_module("290_audit_c1_held_inputs")
BASE = held.EXTENSION
OUT = BASE / "encoder_pilot_2020"
GAUGES = ("10.Q.29", "DE110470", "DEA10040")
YEAR = 2020
GRID_STEP = 0.1
DAILY_UNITS = {
    "tmin_c": "°C",
    "tmax_c": "°C",
    "vapour_pressure_pa": "Pa",
    "relative_humidity_pct": "%",
    "swe_mm": "mm water equivalent",
}


def native_cells(basin):
    west, south, east, north = basin.to_crs(4326).total_bounds
    # ERA5-Land cell centers are aligned to integer tenths of a degree.
    lon = np.arange(np.ceil((west - 0.05) * 10), np.floor((east + 0.05) * 10) + 1) / 10
    lat = np.arange(np.ceil((south - 0.05) * 10), np.floor((north + 0.05) * 10) + 1) / 10
    cells = pd.DataFrame([(x, y) for y in lat for x in lon], columns=["longitude", "latitude"])
    half = GRID_STEP / 2
    boxes = [box(x - half, y - half, x + half, y + half) for x, y in cells.itertuples(index=False)]
    projected = gpd.GeoSeries(boxes, crs=4326).segmentize(0.01).to_crs(basin.crs)
    polygon = basin.iloc[0]
    cells["overlap_km2"] = projected.intersection(polygon).area / 1e6
    cells = cells.loc[cells.overlap_km2.gt(0)].reset_index(drop=True)
    cells["fraction_of_basin"] = cells.overlap_km2 / (polygon.area / 1e6)
    if not np.isclose(cells.fraction_of_basin.sum(), 1, atol=1e-6, rtol=0):
        raise ValueError("Native pixel intersections do not cover the basin")
    return cells


def extract_year(folder, prefix, fields, cells, audit):
    blocks = []
    for month in range(1, 13):
        path = folder / f"{prefix}_{YEAR}_{month:02d}.nc"
        held.checked_hash(path, audit["file_sha256"][path.name])
        with xr.open_dataset(path) as data:
            time = "valid_time" if "valid_time" in data.coords else "time"
            block = data[list(fields)].sel(
                longitude=xr.DataArray(cells.longitude, dims="cell"),
                latitude=xr.DataArray(cells.latitude, dims="cell"),
                method="nearest",
                tolerance=1e-5,
            )
            if {name: block[name].attrs["units"] for name in fields} != {
                name: audit["units"][name] for name in fields
            }:
                raise ValueError(f"Changed units in {path.name}")
            if time != "time":
                block = block.rename({time: "time"})
            blocks.append(block.load().reset_coords(drop=True))
    result = xr.concat(blocks, dim="time", join="exact", coords="minimal", compat="equals")
    calendar = pd.date_range(f"{YEAR}-01-01", f"{YEAR + 1}-01-01", freq="h", inclusive="left")
    if not pd.DatetimeIndex(result.time.values).equals(calendar):
        raise ValueError("Pilot inputs must cover every UTC hour of the reference year")
    if not all(np.isfinite(result[name].values).all() for name in fields):
        raise ValueError("Missing native pilot forcing values")
    return result


def saturation_vapour_pressure(temp_c):
    return 610.94 * np.exp(17.625 * temp_c / (243.04 + temp_c))


def daily_pilot(data, cells):
    temp_c = data.t2m.astype("float64") - 273.15
    vapour_pressure = saturation_vapour_pressure(data.d2m.astype("float64") - 273.15)
    humidity = 100 * vapour_pressure / saturation_vapour_pressure(temp_c)
    daily = (
        xr.Dataset(
            {
                "tmin_c": temp_c.resample(time="1D").min(),
                "tmax_c": temp_c.resample(time="1D").max(),
                "vapour_pressure_pa": vapour_pressure.resample(time="1D").mean(),
                "relative_humidity_pct": humidity.resample(time="1D").mean(),
                "swe_mm": data.sd.astype("float64").resample(time="1D").mean() * 1000,
            }
        )
        .to_dataframe()
        .reset_index()
    )
    daily["day"] = pd.to_datetime(daily.pop("time"), utc=True)
    daily["longitude"] = daily.cell.map(cells.longitude)
    daily["latitude"] = daily.cell.map(cells.latitude)
    daily["gauge"] = GAUGES[0]
    columns = ["gauge", "day", "cell", "longitude", "latitude", *DAILY_UNITS]
    return daily[columns].sort_values(["day", "cell"]).reset_index(drop=True)


def main():
    audit_path = BASE / "c1_held_input_audit.json"
    audit = json.loads(audit_path.read_text())
    c2_source = json.loads((BASE / "c2_multiyear_v1/source_audit.json").read_text())
    snow_roundoff_mm = c2_source["coverage"]["state"]["swe_roundoff_tolerance_mm"]
    geometry = BASE / "catchments.gpkg"
    geokey = str(geometry.relative_to(held.ROOT))
    held.checked_hash(geometry, audit["input_sha256"][geokey])
    basins = gpd.read_file(geometry).set_index("gauge").loc[list(GAUGES)]
    pilots = []
    for gauge, row in basins.iterrows():
        basin = basins.loc[[gauge]].geometry
        cells = native_cells(basin)
        west, south, east, north = basin.total_bounds
        pilots.append(
            {
                "gauge": gauge,
                "station": row.station,
                "source_role": row.source_role,
                "area_km2": float(basin.area.iloc[0] / 1e6),
                "perimeter_km": float(basin.length.iloc[0] / 1000),
                "bbox_epsg3035_m": [west, south, east, north],
                "native_cells": cells.to_dict(orient="records"),
                "held_hourly_temperature_fraction": audit["hourly_temperature"][
                    "footprint_fraction_by_gauge"
                ][gauge],
                "held_hourly_snow_fraction": audit["soil_snow"]["footprint_fraction_by_gauge"][
                    gauge
                ],
            }
        )
    cells = pd.DataFrame(pilots[0]["native_cells"])
    weather = extract_year(
        held.ROOT / "data/raw/era5_land",
        "era5_land_limburg",
        ("t2m", "d2m"),
        cells,
        audit["hourly_temperature"],
    )
    snow = extract_year(held.LAND_STATE, "era5_land_monitoring", ("sd",), cells, audit["soil_snow"])
    daily = daily_pilot(xr.merge([weather, snow], join="exact"), cells)
    minimum_raw_swe = daily.swe_mm.min()
    snow_roundoff = daily.swe_mm.between(-snow_roundoff_mm, 0, inclusive="left")
    daily.loc[snow_roundoff, "swe_mm"] = 0
    if (
        not np.isfinite(daily[list(DAILY_UNITS)].to_numpy()).all()
        or not daily.tmin_c.le(daily.tmax_c).all()
        or daily.swe_mm.lt(0).any()
        or daily.duplicated(["day", "cell"]).any()
        or len(daily) != 366 * len(cells)
    ):
        raise ValueError("Invalid daily pilot census")
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "cottessen_era5_land_daily_2020.parquet"
    temporary = output.with_suffix(".partial")
    daily.to_parquet(temporary, index=False)
    temporary.replace(output)
    held.write_json(
        OUT / "pilot_audit.json",
        {
            "status": "source_pilot_verified",
            "year": YEAR,
            "geometry_sha256": audit["input_sha256"][geokey],
            "held_input_audit_sha256": held.sha(audit_path),
            "pilots": pilots,
            "cottessen_daily_source_sample": {
                "source_hours_per_cell": weather.sizes["time"],
                "days_per_cell": daily.day.nunique(),
                "rows": len(daily),
                "units": DAILY_UNITS,
                "range": daily[list(DAILY_UNITS)].agg(["min", "max"]).to_dict(orient="index"),
                "minimum_raw_swe_mm": float(minimum_raw_swe),
                "swe_roundoff_to_zero": int(snow_roundoff.sum()),
                "swe_roundoff_tolerance_mm": snow_roundoff_mm,
                "daily_reductions": {
                    "temperature": "UTC hourly extrema at each native cell",
                    "vapour_pressure": "Magnus saturation vapour pressure of hourly dewpoint, then UTC daily mean",
                    "relative_humidity": "Hourly vapour pressure divided by saturation vapour pressure at air temperature, then UTC daily mean",
                    "swe": "Mean hourly storage in each UTC day, converted from metres to mm of water equivalent",
                },
                "file": output.name,
                "sha256": held.sha(output),
            },
        },
    )
    print(f"Verified {len(daily):,} Cottessen cell-days across {len(cells)} native cells")


if __name__ == "__main__":
    main()
