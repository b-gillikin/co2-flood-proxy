"""Check real archive contracts with tiny georeferenced fixtures, no model downloads."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src.eo_inputs import Tile, get_patch, read_product, read_tile, sha256, standardize

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "extract_eo", ROOT / "scripts/98_extract_limburg_eo_embeddings.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def fixture(tmp_path, day=17800):
    job = {
        "relative_path": "tile.tif",
        "bands": ["VV", "VH", "acquired_day"],
        "bounds": [300000, 5623960, 300040, 5624000],
        "asset_ids": ["fixture"],
        "acquisition_ms": [day * 86400000],
        "product": "s1_ascending",
        "window": {
            "id": "test",
            "start": "2018-09-01T00:00:00+00:00",
            "end": "2018-10-01T00:00:00+00:00",
        },
    }
    data = np.ones((4, 4, 4), dtype="float32")
    data[0] *= -10
    data[1] *= -20
    data[2] *= day
    data[3] *= 7
    # A physically zero measurement is valid; mask, not value, determines coverage.
    data[0, 0, 0] = 0
    data[3, 0, 1] = 5
    path = tmp_path / "tile.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=4,
        width=4,
        count=4,
        dtype="float32",
        crs="EPSG:32632",
        transform=from_origin(300000, 5624000, 10, 10),
    ) as ds:
        ds.write(data)
    path.with_suffix(".receipt.json").write_text(json.dumps({**job, "sha256": sha256(path)}))
    return job


def test_bit_masks_valid_zero_and_padding(tmp_path):
    job = fixture(tmp_path)
    tile = read_tile(tmp_path, job, {})
    assert tile.valid[0, 0] and tile.values[0, 0, 0] == 0
    assert not tile.valid[0, 1]
    patch = get_patch(tile, 2, 2, 4)
    assert patch["valid"].sum() == 4
    assert patch["metadata"]["padding_pixels"] == 12
    assert patch["observed_latlons"].shape == (4, 2)
    assert patch["metadata"]["earliest_asof_eligibility"] == job["window"]["end"]


def test_receipt_and_job_integrity(tmp_path):
    job = fixture(tmp_path)
    with pytest.raises(ValueError, match="job mismatch"):
        read_product(tmp_path, {**job, "bands": ["VH", "VV", "acquired_day"]})
    with (tmp_path / "tile.tif").open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(ValueError, match="receipt differs"):
        read_product(tmp_path, job)


def test_acquisition_outside_completed_window_rejected(tmp_path):
    job = fixture(tmp_path, day=19000)
    with pytest.raises(ValueError, match="outside"):
        read_tile(tmp_path, job, {})


def test_normalization_imputes_mean_without_treating_zero_as_missing():
    x = np.array([[[0.0, 20.0], [100.0, -999.0]]], dtype=np.float32)
    mask = np.array([[True, True], [True, False]])
    actual = standardize(x, mask, [20], [10])
    np.testing.assert_array_equal(actual, [[[-2, 0], [8, 0]]])
    with pytest.raises(ValueError):
        standardize(x, mask, [20], [0])


def test_all_missing_patch_has_no_representative_date():
    tile = Tile(
        np.zeros((2, 4, 4)),
        np.zeros((4, 4), bool),
        np.zeros((4, 4)),
        ["VV", "VH"],
        from_origin(300000, 5624000, 10, 10),
        "EPSG:32632",
        [],
        {"end": "2018-10-01T00:00:00+00:00"},
    )
    patch = get_patch(tile, 0, 0, 4)
    assert patch["metadata"]["representative_date"] is None
    assert patch["metadata"]["valid_pixels"] == 0


def test_cache_requires_identity_receipt_and_file_integrity(tmp_path):
    path = tmp_path / "out.npz"
    path.write_bytes(b"example")
    identity = {"source": "x", "adapter": "v1"}
    runner.atomic_json(path.with_suffix(".json"), {"identity": identity, "sha256": sha256(path)})
    assert runner.valid_cached(path, identity)
    assert not runner.valid_cached(path, {**identity, "adapter": "v2"})
    path.write_bytes(b"changed")
    assert not runner.valid_cached(path, identity)


def test_empty_patch_never_calls_encoder():
    from src.eo_encoders import Encoder

    encoder = Encoder.__new__(Encoder)
    with pytest.raises(ValueError, match="No observed pixels"):
        encoder({"valid": np.zeros((4, 4), bool)})


def test_hls_physical_reflectance_is_scaled_once():
    import torch

    from src.eo_encoders import Encoder

    encoder = Encoder.__new__(Encoder)
    encoder.name = "prithvi"

    class Capture:
        encoder = type("EncoderConfig", (), {"num_frames": 1})()

        def forward_features(self, x, temporal, location):
            expected = (1000.0 - np.array([1087, 1342, 1433, 2734, 1958, 1363])) / np.array(
                [2248, 2179, 2178, 1850, 1242, 1049]
            )
            np.testing.assert_allclose(x.numpy()[0, :, 0, 0, 0], expected, rtol=1e-6)
            assert temporal.tolist() == [[[2018.0, 244.0]]]
            return [torch.ones(1, 3, 4)]

    encoder.model = Capture()
    out = encoder(
        {
            "values": np.full((6, 2, 2), 0.1, dtype="float32"),
            "valid": np.ones((2, 2), bool),
            "metadata": {
                "representative_date": "2018-09-01T00:00:00+00:00",
                "latitude": 51.0,
                "longitude": 6.0,
            },
        }
    )
    assert out.shape == (4,)


def test_s2_grids_masks_band_order_and_dates_align(tmp_path):
    base = fixture(tmp_path)
    jobs = []
    for product, size, bands, value, day in [
        ("s2_10m", 4, ["B2", "B3", "B4", "B8", "acquired_day"], 1000, 17800),
        ("s2_20m", 2, ["B5", "B6", "B7", "B8A", "B11", "B12", "SCL", "acquired_day"], 2000, 17801),
    ]:
        job = {**base, "relative_path": product + ".tif", "product": product, "bands": bands}
        data = np.full((len(bands) + 1, size, size), value, dtype="float32")
        data[-2] = day
        data[-1] = 2 ** len(bands) - 1
        if product == "s2_20m":
            data[-1, 0, 0] = 0
        path = tmp_path / job["relative_path"]
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=size,
            width=size,
            count=len(bands) + 1,
            dtype="float32",
            crs="EPSG:32632",
            transform=from_origin(300000, 5624000, 40 / size, 40 / size),
        ) as ds:
            ds.write(data)
        path.with_suffix(".receipt.json").write_text(json.dumps({**job, "sha256": sha256(path)}))
        jobs.append(job)
    companions = {(j["window"]["id"], tuple(j["bounds"]), j["product"]): j for j in jobs}
    tile = read_tile(tmp_path, jobs[0], companions)
    assert tile.bands == ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
    assert not tile.valid[:2, :2].any() and tile.valid.sum() == 12
    assert np.all(tile.values[6] == 1000) and np.all(tile.values[3] == 2000)
    assert np.all(tile.days[tile.valid] == 17801)
    assert tile.sources[0]["observed_acquired_day_range"] == [17800, 17800]
