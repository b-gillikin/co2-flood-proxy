"""Protect source bytes from unsafe offload decisions; no cloud access."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "offload", Path(__file__).parents[1] / "scripts/177_offload_verified_expansion.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_no_escape_or_primary_or_link(tmp_path):
    for path, product in [
        ("../bad.tif", "landsat8_sr"),
        ("images/w/s2_toa_10m/a.tif", "s2_toa_10m"),
        ("/tmp/bad.tif", "landsat8_sr"),
    ]:
        with pytest.raises(ValueError):
            mod.candidate({"relative_path": path, "product": product}, tmp_path)
    target = tmp_path / "images/w/landsat8_sr/a.tif"
    target.parent.mkdir(parents=True)
    target.symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ValueError):
        mod.candidate(
            {"relative_path": str(target.relative_to(tmp_path)), "product": "landsat8_sr"}, tmp_path
        )


def test_remote_pair_requires_verified_bytes_and_linkage():
    job = dict(
        relative_path="images/w/landsat8_sr/a.tif",
        bands=["x"],
        bounds=[0, 0, 1, 1],
        window={},
        asset_ids=["a"],
    )
    receipt = job | {"sha256": "abc"}
    data = {"size": 3, "metadata": {"sha256": "abc", "verified": "sha256-readback"}}
    remote = {"metadata": {"data_sha256": "abc"}}
    mod.verified_pair(job, receipt, 3, "abc", data, remote)
    for bad in [
        data | {"size": 4},
        data | {"metadata": {"sha256": "abc", "verified": "transport-md5"}},
        data | {"metadata": {"sha256": "wrong", "verified": "sha256-readback"}},
    ]:
        with pytest.raises(ValueError):
            mod.verified_pair(job, receipt, 3, "abc", bad, remote)
    with pytest.raises(ValueError):
        mod.verified_pair(job, receipt, 3, "abc", data, {"metadata": {"data_sha256": "wrong"}})
    with pytest.raises(ValueError):
        mod.verified_pair(job, receipt | {"bands": ["other"]}, 3, "abc", data, remote)
