"""Source-integrity checks for the separate supporting land-state download."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from requests import HTTPError, Response

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


def http_error(status, message):
    response = Response()
    response.status_code = status
    return HTTPError(message, response=response)


def test_policy_failure_stops_queue_and_retains_verified_progress(tmp_path):
    plan = tmp_path / "download-plan.json"
    plan.write_text("{}")
    previous = {"status": "paused", "completed_months": 1, "failures": {"old": "retained"}}
    (tmp_path / "manifest.json").write_text(json.dumps(previous))
    (tmp_path / "era5_land_monitoring_2012_01.nc").write_bytes(b"held source")
    calls = []

    def fetch(year, month, area, destination):
        calls.append(month)
        if month == 1:
            return {"bytes": 11, "file": "held source"}
        raise http_error(403, "Missing required site policy https://provider/?token=secret")

    with pytest.raises(SystemExit, match="account_or_policy"):
        LAND.run_downloads([(2012, m) for m in [1, 2, 3]], [], tmp_path, plan, fetch)
    saved = json.loads((tmp_path / "manifest.json").read_text())
    assert calls == [1, 2]  # No request for March after the service-wide failure.
    assert saved["completed_months"] == saved["existing_months_verified"] == 1
    assert saved["status"] == "blocked"
    assert saved["pending_months"] == ["2012-02", "2012-03"]
    assert "secret" not in json.dumps(saved)
    assert json.loads(next((tmp_path / "run-history").glob("*.json")).read_text()) == previous


def test_pause_is_explicit_and_does_not_destroy_existing_source(tmp_path):
    plan = tmp_path / "download-plan.json"
    plan.write_text("{}")

    def pause(*args):
        raise LAND.DownloadPaused()

    LAND.run_downloads([(2012, 1), (2012, 2)], [], tmp_path, plan, pause)
    saved = json.loads((tmp_path / "manifest.json").read_text())
    assert saved["status"] == "paused"
    assert saved["failures"] == {}
    assert saved["active_month"] == "2012-01"


@pytest.mark.parametrize(
    "code,kind",
    [
        (401, "account_or_policy"),
        (429, "provider_throttle_or_outage"),
        (503, "provider_throttle_or_outage"),
        (400, "invalid_request"),
    ],
)
def test_service_failure_classification(code, kind):
    assert LAND.failure_details(http_error(code, "provider message"))["kind"] == kind


@pytest.mark.parametrize("expiry", ["request", "result"])
def test_expired_cds_job_or_asset_renews_once_without_losing_request_history(
    tmp_path, monkeypatch, expiry
):
    ds, server_file = field_file(tmp_path)
    ds.to_netcdf(server_file)
    area = [51.1, 6.0, 51.0, 6.1]
    request = LAND.request_for_month(2012, 1, area)
    job_file = tmp_path / "era5_land_monitoring_2012_01.request.json"
    job_file.write_text(json.dumps({"request": request, "request_id": "old"}))
    submissions = []

    class Remote:
        status = "successful"

        def __init__(self, request_id):
            self.request_id = request_id

        def download(self, target):
            if self.request_id == "old":
                raise http_error(404, "Expired asset")
            shutil.copyfile(server_file, target)

    def get_remote(request_id):
        assert request_id == "old"
        if expiry == "request":
            raise http_error(404, "Expired request")
        return Remote("old")

    class Client:
        client = SimpleNamespace(get_remote=get_remote)

        def retrieve(self, dataset, fields):
            submissions.append((dataset, fields))
            return Remote("new")

    monkeypatch.setitem(sys.modules, "cdsapi", SimpleNamespace(Client=lambda **kw: Client()))
    receipt = LAND.fetch_one(2012, 1, area, tmp_path)
    saved = json.loads(job_file.read_text())
    assert saved["request_id"] == receipt["request_id"] == "new"
    assert saved["previous_request_ids"] == ["old"]
    assert submissions == [(LAND.DATASET, request)]
    assert receipt["sha256"] == LAND.digest(server_file)
