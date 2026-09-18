"""Build the ERA5-Land weather inputs for the case-crossover study (protocol §6).

For each candidate watercourse, take the ERA5-Land 0.1-degree cell nearest the
fixed catchment centroid (`data/interim/event_study_catchments.gpkg`) and derive:

- relative humidity (%) from 2 m temperature and dew point with the Magnus
  formula of Alduchov and Eskridge (1996), the one documented formula;
- surface pressure (hPa);
- six-hour surface-pressure change (hPa), p(t) - p(t - 6 h), only when both
  hours are observed on the hourly grid.

ERA5-Land values are instantaneous at the UTC timestamp. Cells shared by
several catchments are recorded as shared exposures. Writes the weather table
and the weather-sources table of the protocol's input contract.

Example: python scripts/40_build_event_study_weather.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
ERA5 = ROOT / "data/raw/era5_land"
CATCHMENTS = ROOT / "data/interim/event_study_catchments.gpkg"
WEATHER = ROOT / "data/interim/event_study_weather_hourly.csv"
SOURCES = ROOT / "data/interim/event_study_weather_sources.csv"
MAGNUS_A, MAGNUS_B = 17.625, 243.04  # Alduchov and Eskridge (1996), degC


def relative_humidity(temperature_c, dew_point_c):
    """Relative humidity (%) from temperature and dew point, capped at 100."""
    vapour = np.exp(MAGNUS_A * dew_point_c / (MAGNUS_B + dew_point_c))
    saturation = np.exp(MAGNUS_A * temperature_c / (MAGNUS_B + temperature_c))
    return np.minimum(100.0 * vapour / saturation, 100.0)


def pressure_change(pressure, hours=6):
    """p(t) - p(t - hours) on a complete hourly grid; missing if either end is missing."""
    index = pressure.index
    if len(index) > 1 and not index.to_series().diff().iloc[1:].eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Pressure change needs a complete hourly grid")
    return pressure - pressure.shift(hours)


def centroids():
    catchments = gpd.read_file(CATCHMENTS)
    points = catchments.geometry.centroid.to_crs("EPSG:4326")
    return pd.DataFrame(
        {
            "watercourse": catchments.watercourse,
            "centroid_lon": points.x.round(5),
            "centroid_lat": points.y.round(5),
        }
    )


def main():
    sites = centroids()
    files = sorted(ERA5.glob("era5_land_limburg_*.nc"))
    if not files:
        raise SystemExit("No ERA5-Land files found")
    with xr.open_dataset(files[0]) as first:
        lat = first.latitude.to_numpy()
        lon = first.longitude.to_numpy()
    sites["cell_lat"] = [lat[np.abs(lat - value).argmin()] for value in sites.centroid_lat]
    sites["cell_lon"] = [lon[np.abs(lon - value).argmin()] for value in sites.centroid_lon]
    cells = sites[["cell_lat", "cell_lon"]].drop_duplicates().reset_index(drop=True)

    parts = []
    for path in files:
        with xr.open_dataset(path) as ds:
            for cell in cells.itertuples(index=False):
                point = ds.sel(latitude=cell.cell_lat, longitude=cell.cell_lon)
                parts.append(
                    pd.DataFrame(
                        {
                            "timestamp_utc": pd.to_datetime(point.valid_time.to_numpy(), utc=True),
                            "cell_lat": cell.cell_lat,
                            "cell_lon": cell.cell_lon,
                            "t2m_c": point.t2m.to_numpy() - 273.15,
                            "d2m_c": point.d2m.to_numpy() - 273.15,
                            "sp_hpa": point.sp.to_numpy() / 100.0,
                        }
                    )
                )
    raw = pd.concat(parts, ignore_index=True)
    if raw.duplicated(["cell_lat", "cell_lon", "timestamp_utc"]).any():
        raise ValueError("Duplicate ERA5-Land timestamps")

    frames = []
    for cell, group in raw.groupby(["cell_lat", "cell_lon"]):
        group = group.set_index("timestamp_utc").sort_index()
        grid = pd.date_range(group.index.min(), group.index.max(), freq="h")
        group = group.reindex(grid)
        frame = pd.DataFrame(
            {
                "relative_humidity_pct": relative_humidity(group.t2m_c, group.d2m_c).round(2),
                "surface_pressure_hpa": group.sp_hpa.round(2),
                "pressure_change_6h_hpa": pressure_change(group.sp_hpa).round(2),
            },
            index=grid.rename("timestamp_utc"),
        )
        frame["cell_lat"], frame["cell_lon"] = cell
        frames.append(frame.reset_index())
    per_cell = pd.concat(frames, ignore_index=True)
    weather = sites[["watercourse", "cell_lat", "cell_lon"]].merge(
        per_cell, on=["cell_lat", "cell_lon"], how="left"
    )
    weather = weather[
        [
            "timestamp_utc",
            "watercourse",
            "relative_humidity_pct",
            "surface_pressure_hpa",
            "pressure_change_6h_hpa",
        ]
    ].sort_values(["watercourse", "timestamp_utc"])
    weather["timestamp_utc"] = weather.timestamp_utc.dt.strftime("%Y-%m-%dT%H:%MZ")
    weather.to_csv(WEATHER, index=False)

    shared = sites.groupby(["cell_lat", "cell_lon"]).watercourse.transform(
        lambda names: ";".join(sorted(names)) if len(names) > 1 else ""
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.read_bytes())
    sources = sites.assign(
        source_id="ERA5-Land hourly (Copernicus CDS), t2m/d2m/sp",
        source_type="reanalysis",
        spatial_assignment="nearest 0.1-degree cell to the fixed catchment centroid",
        shared_cell_with=shared,
        timezone_verified=True,
        units_verified=True,
        rh_formula="Magnus, Alduchov and Eskridge (1996): a=17.625, b=243.04 degC",
        archive_sha256=digest.hexdigest(),
    )
    sources.to_csv(SOURCES, index=False)
    print(sources.drop(columns="archive_sha256").to_string(index=False))
    print(
        weather.groupby("watercourse")[["relative_humidity_pct", "surface_pressure_hpa"]]
        .agg(["count", "min", "max"])
        .round(1)
        .to_string()
    )


if __name__ == "__main__":
    sys.exit(main())
