"""Check spatial coverage, source-band preservation, and archive integrity."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box
from shapely.ops import unary_union

SPEC = importlib.util.spec_from_file_location(
    "archive", Path(__file__).parents[1] / "scripts/95_acquire_limburg_satellite_archive.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_tiles_cover_irregular_catchment_and_align_all_spectral_grids():
    geometry = box(299900, 5600000, 310000, 5609700).difference(
        box(305000, 5600000, 310000, 5604000)
    )
    tiles = list(MODULE.tiles_for_geometry(geometry))
    assert geometry.difference(unary_union([box(*t["bounds"]) for t in tiles])).area == 0
    for tile in tiles:
        assert all(v % 60 == 0 for v in tile["bounds"])


def test_bands_retain_cloud_information_and_both_radiometric_levels():
    assert "SCL" in MODULE.SOURCES["s2_sr"][1][20]
    assert "QA60" in MODULE.SOURCES["s2_toa"][1][60]
    assert "B10" in MODULE.SOURCES["s2_toa"][1][60]
    assert MODULE.SOURCES["s1"][1][10] == ["VV", "VH", "angle"]
    for sensor in ["landsat5", "landsat7", "landsat8", "landsat9"]:
        assert "QA_PIXEL" in MODULE.SOURCES[sensor][1][30]


def test_validation_detects_truncated_band_stack(tmp_path):
    path = tmp_path / "image.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=2,
        dtype="uint16",
        crs="EPSG:32632",
        transform=from_origin(300000, 5600060, 30, 30),
    ) as ds:
        ds.write(np.ones((2, 2, 2), dtype="uint16"))
    MODULE.validate_raster(path, ["B1"], [300000, 5600000, 300060, 5600060], 30)
    with pytest.raises(ValueError, match="dimensions/bands"):
        MODULE.validate_raster(path, ["B1", "B2"], [300000, 5600000, 300060, 5600060], 30)


def test_lossless_compression_preserves_values_and_grid(tmp_path):
    source = tmp_path / "raw.tif"
    target = tmp_path / "packed.tif"
    values = np.arange(4 * 16 * 16, dtype="float32").reshape(4, 16, 16)
    values[:, :8] = 0
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        width=16,
        height=16,
        count=4,
        dtype="float32",
        crs="EPSG:32632",
        transform=from_origin(300000, 5600160, 10, 10),
    ) as ds:
        ds.write(values)
    MODULE.compress_raster(source, target)
    with rasterio.open(target) as ds:
        np.testing.assert_array_equal(ds.read(), values)
        assert ds.crs.to_epsg() == 32632
        assert ds.transform == from_origin(300000, 5600160, 10, 10)


def test_acquisition_order_preserves_census_and_interleaves_sensor_years():
    from datetime import datetime, timezone

    jobs = [
        {
            "source": source,
            "acquired_ms": datetime(year, 1, day, tzinfo=timezone.utc).timestamp() * 1000,
            "relative_path": f"{source}/{year}/{day}",
        }
        for source in ["s1", "s2_sr"]
        for year in [2015, 2025]
        for day in [1, 2]
    ]
    ordered = MODULE.archive_order(jobs)
    assert {j["relative_path"] for j in ordered} == {j["relative_path"] for j in jobs}
    assert len(ordered) == len(jobs)
    assert (
        len(
            {
                (j["source"], datetime.fromtimestamp(j["acquired_ms"] / 1000, timezone.utc).year)
                for j in ordered[:4]
            }
        )
        == 4
    )
