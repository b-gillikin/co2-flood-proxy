"""Check receipt and measurement-date failures using real tiny rasters."""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "expansion_pixel_audit", ROOT / "scripts/127_audit_eo_expansion_pixels.py"
)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture(tmp_path, day=18262, valid=True):
    job = {
        "relative_path": "images/test/s1_descending_37/a.tif",
        "bands": ["VV", "VH", "angle", "acquired_day"],
        "bounds": [0, 0, 20, 20],
        "window": {
            "id": "test",
            "start": "2020-01-01T00:00:00+00:00",
            "end": "2020-01-08T00:00:00+00:00",
        },
        "asset_ids": ["example"],
        "acquisition_ms": [1577836800000],
        "product": "s1_descending_37",
    }
    p = tmp_path / job["relative_path"]
    p.parent.mkdir(parents=True)
    data = np.ones((5, 2, 2), dtype="float32")
    data[3] = day
    data[4] = 15 if valid else 0
    with rasterio.open(
        p,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=5,
        dtype="float32",
        crs="EPSG:32632",
        transform=from_origin(0, 20, 10, 10),
    ) as ds:
        ds.write(data)
    receipt = {**job, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    p.with_suffix(".receipt.json").write_text(json.dumps(receipt))
    return job, p


def test_valid_dates_and_joint_masks(tmp_path):
    job, _ = fixture(tmp_path)
    r = audit.inspect(job, tmp_path)
    assert r["joint_valid_pixels"] == 4


def test_outside_observed_dates_rejected(tmp_path):
    job, _ = fixture(tmp_path, day=18270)
    with pytest.raises(ValueError, match="Observed date"):
        audit.inspect(job, tmp_path)


def test_missing_pixels_not_observations(tmp_path):
    job, _ = fixture(tmp_path, day=0, valid=False)
    assert audit.inspect(job, tmp_path)["joint_valid_pixels"] == 0


def test_checksum_corruption_rejected(tmp_path):
    job, p = fixture(tmp_path)
    p.write_bytes(p.read_bytes() + b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        audit.inspect(job, tmp_path)


def test_qa_missing_cloudy_or_different_date_is_not_clear():
    from src.eo_expansion_inputs import clear_mask

    assert clear_mask(
        np.array([0, 1024, 2048, 0, 0]),
        np.array([True, True, True, False, True]),
        np.array([1, 1, 1, 1, 2]),
        np.ones(5),
    ).tolist() == [True, False, False, False, False]
