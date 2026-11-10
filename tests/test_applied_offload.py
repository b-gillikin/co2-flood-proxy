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


def test_compact_override_uses_exact_base_and_products(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "BASE", tmp_path)
    monkeypatch.setattr(mod, "PRODUCTS", {"hls", "s1_ascending", "s2_10m", "s2_20m"})
    assert mod.candidate({"relative_path": "images/w/hls/a.tif", "product": "hls"}) == tmp_path / "images/w/hls/a.tif"
    with pytest.raises(ValueError):
        mod.candidate({"relative_path": "images/w/hls/a.tif", "product": "s2_10m"})


def test_restore_only_exact_allowlisted_roots(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "restore", Path(__file__).parents[1] / "scripts/182_restore_offloaded_expansion.py"
    )
    restore = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(restore)
    for name in ("limburg_compact_eo", "limburg_eo_expansion"):
        assert restore.destination(f"data/raw/{name}/images/a.tif", tmp_path) == tmp_path / f"data/raw/{name}/images/a.tif"
    for path in ("data/raw/limburg_applied_tasks/a.tif", "../Peja/a.tif", "data/raw/limburg_compact_eo/../a.tif"):
        with pytest.raises(ValueError):
            restore.destination(path, tmp_path)


def test_offloaded_archive_cannot_become_missing_observations(tmp_path):
    from src.eo_individual_archive import Archive

    archive = tmp_path / "data/raw/limburg_compact_eo"
    archive.mkdir(parents=True)
    (archive / "OFFLOADED-2026-11-10.json").write_text("{}")
    with pytest.raises(RuntimeError, match="offloaded, not unobserved"):
        Archive(tmp_path, "dofa")
