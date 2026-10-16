"""Publisher hashes protect large checkpoint downloads from silent corruption."""

import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "eo_assets", Path(__file__).parents[1] / "scripts/97_download_limburg_eo_models.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_hashes_use_publisher_git_blob_convention(tmp_path):
    path = tmp_path / "config.json"
    path.write_bytes(b"{}\n")
    asset = {"bytes": 3, "git_blob_sha1": hashlib.sha1(b"blob 3\0{}\n").hexdigest()}
    assert MODULE.verify(path, asset) == hashlib.sha256(b"{}\n").hexdigest()
    path.write_bytes(b"[]\n")
    with pytest.raises(ValueError, match="Publisher git_blob_sha1"):
        MODULE.verify(path, asset)


def test_corrupt_checkpoint_and_truncation_are_rejected(tmp_path):
    path = tmp_path / "weights.pt"
    path.write_bytes(b"checkpoint")
    asset = {"bytes": 10, "sha256": hashlib.sha256(b"checkpoint").hexdigest()}
    MODULE.verify(path, asset)
    path.write_bytes(b"corruption")
    with pytest.raises(ValueError, match="Publisher sha256"):
        MODULE.verify(path, asset)
    path.write_bytes(b"short")
    with pytest.raises(ValueError, match="Byte count"):
        MODULE.verify(path, asset)


def test_zenodo_md5_and_resumable_existing_asset(tmp_path, monkeypatch):
    monkeypatch.setattr(MODULE, "ROOT", tmp_path)
    path = tmp_path / "weights.pt"
    path.write_bytes(b"checkpoint")
    asset = {
        "path": "weights.pt",
        "url": "https://example.invalid/weights.pt",
        "bytes": 10,
        "md5": hashlib.md5(b"checkpoint").hexdigest(),
    }
    # A valid existing file is hashed/adopted without another network request.
    monkeypatch.setattr(MODULE.subprocess, "run", lambda *a, **k: pytest.fail("Redownload"))
    receipt = MODULE.acquire_file(tmp_path, asset)
    assert receipt["sha256"] == hashlib.sha256(b"checkpoint").hexdigest()
    assert path.with_suffix(".pt.receipt.json").exists()


@pytest.mark.parametrize("oversized", [False, True])
def test_fallback_restarts_when_publisher_ignores_range(tmp_path, monkeypatch, oversized):
    import requests

    monkeypatch.setattr(MODULE, "ROOT", tmp_path)
    monkeypatch.setattr(MODULE.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=35))
    (tmp_path / "weights.pt.part").write_bytes(b"old")
    content = b"checkpoint" + (b"extra" if oversized else b"")

    class Response:
        status_code = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def raise_for_status(self):
            pass

        def iter_content(self, *args):
            yield content

    monkeypatch.setattr(requests, "get", lambda *a, **k: Response())
    asset = {
        "path": "weights.pt",
        "url": "https://example.invalid/weights.pt",
        "bytes": 10,
        "sha256": hashlib.sha256(b"checkpoint").hexdigest(),
    }
    if oversized:
        with pytest.raises(ValueError, match="exceeds publisher byte count"):
            MODULE.acquire_file(tmp_path, asset)
        assert not (tmp_path / "weights.pt").exists()
    else:
        MODULE.acquire_file(tmp_path, asset)
        assert (tmp_path / "weights.pt").read_bytes() == b"checkpoint"
