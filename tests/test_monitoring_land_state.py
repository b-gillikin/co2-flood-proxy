"""Source-integrity checks for the separate supporting land-state download."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

SPEC = importlib.util.spec_from_file_location(
    "land_state", Path(__file__).resolve().parents[1] / "scripts/150_fetch_monitoring_land_state.py"
)
LAND = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAND)


def field_file(tmp_path):
    times = LAND.expected_times(2012, 1)
    values = np.zeros((len(times), 2, 2), dtype=np.float32)
    ds = xr.Dataset(
        {
            "swvl1": (("valid_time", "latitude", "longitude"), values + 0.2),
            "swvl2": (("valid_time", "latitude", "longitude"), values + 0.3),
            "sd": (("valid_time", "latitude", "longitude"), values),
        },
        coords={"valid_time": times, "latitude": [51.1, 51.0], "longitude": [6.0, 6.1]},
    )
    for name in ["swvl1", "swvl2"]:
        ds[name].attrs["units"] = "m**3 m**-3"
    ds.sd.attrs["units"] = "m"
    path = tmp_path / "source.nc"
    return ds, path


def test_real_month_clock_includes_leap_day():
    clock = LAND.expected_times(2012, 2)
    assert len(clock) == 29 * 24
    assert pd.Timestamp("2012-02-29 23:00") in clock
    assert clock[-1] == pd.Timestamp("2012-02-29 23:00")


def test_covering_grid_covers_extents_and_cell_margin():
    west, south, east, north = [5.7358, 50.6503, 6.2342, 51.03]
    area = LAND.covering_area([west, south, east, north])
    assert area == [51.2, 5.6, 50.5, 6.4]
    assert area[0] > north and area[1] < west and area[2] < south and area[3] > east


def test_native_zero_snow_is_valid(tmp_path):
    ds, path = field_file(tmp_path)
    ds.to_netcdf(path)
    receipt = LAND.validate(path, 2012, 1, [51.1, 6.0, 51.0, 6.1])
    assert receipt["hours"] == 744
    assert receipt["fields"]["sd"]["minimum"] == 0


@pytest.mark.parametrize("defect", ["missing_hour", "nonfinite", "wrong_units", "wrong_grid"])
def test_bad_source_is_not_accepted(tmp_path, defect):
    ds, path = field_file(tmp_path)
    if defect == "missing_hour":
        ds = ds.isel(valid_time=slice(1, None))
    elif defect == "nonfinite":
        ds.swvl1.values[0, 0, 0] = np.nan
    elif defect == "wrong_units":
        ds.sd.attrs["units"] = "cm"
    else:
        ds = ds.assign_coords(longitude=[6.1, 6.2])
    ds.to_netcdf(path)
    with pytest.raises(ValueError):
        LAND.validate(path, 2012, 1, [51.1, 6.0, 51.0, 6.1])
