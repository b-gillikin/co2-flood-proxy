"""Scientific timing, coverage and storage checks for compact EO acquisition."""

import importlib.util
from pathlib import Path

import pandas as pd
from shapely.geometry import box, mapping

SPEC = importlib.util.spec_from_file_location(
    "compact", Path(__file__).parents[1] / "scripts/96_acquire_limburg_compact_eo.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_all_events_retained_and_context_never_crosses_cutoff():
    storms = pd.DataFrame(
        {
            "storm_id": ["a", "b", "c"],
            "landmark_utc": [
                "2021-07-12 00:00:00+00:00",
                "2021-07-14 03:00:00+00:00",
                "2010-01-01 01:00:00+01:00",
            ],
        }
    )
    windows, events = MODULE.temporal_requests(storms)
    lookup = {w["id"]: w for w in windows}
    assert len(events) == 3
    assert len(windows) < 3 * 16  # overlapping context is shared, not re-exported
    for event in events:
        assert len(event["monthly"]) == 12 and len(event["recent"]) == 4
        for key in event["monthly"] + event["recent"]:
            w = lookup[key]
            assert (
                pd.Timestamp(w["start"])
                < pd.Timestamp(w["end"])
                <= pd.Timestamp(event["cutoff_utc"])
            )
            if w["kind"] == "recent":
                assert pd.Timestamp(w["end"]).weekday() == 0
                assert pd.Timestamp(w["end"]) - pd.Timestamp(w["start"]) == pd.Timedelta(days=7)


def test_budget_reserves_transient_files_and_other_working_assets():
    job = {"resolution": 10, "bands": ["VV", "VH", "angle", "acquired_day"], "dtype": "float32"}
    assert MODULE.raw_bound(job) == 960 * 960 * 5 * 4
    assert not MODULE.budget_allows(69e9, 0, job, 70e9, 100e9, 31e9)
    assert not MODULE.budget_allows(70e9 - 1, 0, job, 70e9, 100e9, 0)
    assert not MODULE.budget_allows(69e9, 1e9, job, 70e9, 100e9, 0)
    assert MODULE.budget_allows(1e9, 0, job, 70e9, 100e9, 1e9)


def test_jobs_exclude_future_scenes_wrong_orbits_and_nonintersecting_tiles():
    start = pd.Timestamp("2021-07-05", tz="UTC").timestamp() * 1000
    end = pd.Timestamp("2021-07-12", tz="UTC").timestamp() * 1000
    geometry = mapping(box(5.9, 50.8, 6.0, 50.9))

    def scene(name, time, orbit=88):
        return {
            "source": "s1",
            "collection": "COPERNICUS/S1_GRD",
            "id": name,
            "geometry": geometry,
            "properties": {
                "system:time_start": time,
                "relativeOrbitNumber_start": orbit,
                "orbitProperties_pass": "ASCENDING",
            },
        }

    records = [
        scene("allowed", start),
        scene("at_end", end),
        scene("after", end + 1),
        scene("wrong_orbit", start, 15),
    ]
    tiles = [
        {"id": "near", "bounds": [278400, 5625600, 288000, 5635200]},
        {"id": "far", "bounds": [0, 0, 9600, 9600]},
    ]
    windows = [
        {
            "id": "recent_20210705_20210712",
            "kind": "recent",
            "start": "2021-07-05T00:00:00+00:00",
            "end": "2021-07-12T00:00:00+00:00",
        }
    ]
    jobs, availability = MODULE.build_jobs(windows, records, tiles)
    assert len(jobs) == 1
    assert jobs[0]["asset_ids"] == ["COPERNICUS/S1_GRD/allowed"]
    assert jobs[0]["relative_path"].endswith("/near.tif")
    assert next(a for a in availability if a["product"] == "hls")["source_scene_count"] == 0


def test_reusing_archive_rejects_changed_scientific_inputs():
    import pytest

    previous = {
        key: "same"
        for key in [
            "storm_csv_sha256",
            "geometry_sha256",
            "products",
            "buffer_m",
            "composite",
            "quality",
            "s1_orbits",
        ]
    }
    MODULE.validate_plan(previous, previous | {"code_sha256": "refactored"})
    with pytest.raises(ValueError, match="geometry_sha256"):
        MODULE.validate_plan(previous, previous | {"geometry_sha256": "changed"})


def test_both_hls_instruments_feed_one_product_with_sensor_provenance():
    start = pd.Timestamp("2021-06-01", tz="UTC").timestamp() * 1000
    records = [
        {
            "source": source,
            "collection": MODULE.HLS[source],
            "id": source,
            "geometry": mapping(box(5.9, 50.8, 6.0, 50.9)),
            "properties": {"system:time_start": start},
        }
        for source in MODULE.HLS
    ]
    jobs, _ = MODULE.build_jobs(
        [
            {
                "id": "monthly_june",
                "kind": "monthly",
                "start": "2021-06-01T00:00:00+00:00",
                "end": "2021-07-01T00:00:00+00:00",
            }
        ],
        records,
        [{"id": "tile", "bounds": [278400, 5625600, 288000, 5635200]}],
    )
    assert len(jobs) == 1 and jobs[0]["product"] == "hls"
    assert len(jobs[0]["asset_ids"]) == 2
    assert "sensor_id" in jobs[0]["bands"]
    assert jobs[0]["dtype"] == "float32"  # do not truncate physical reflectance
