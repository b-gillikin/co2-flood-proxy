"""Exercise actual archive publication/readback semantics without cloud billing."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "cloud_eo", Path(__file__).parents[1] / "infrastructure/compact_eo/cloud_worker.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeContainer:
    def __init__(self):
        self.objects = {}

    def list_blobs(self, **kwargs):
        return [
            SimpleNamespace(name=k, size=len(v[0]), metadata=v[1]) for k, v in self.objects.items()
        ]

    def get_blob_client(self, name):
        parent = self

        class Blob:
            def upload_blob(self, data, overwrite=False, metadata=None, **kwargs):
                assert overwrite or name not in parent.objects
                content = data.read() if hasattr(data, "read") else data
                parent.objects[name] = (content, metadata or {})

            def get_blob_properties(self):
                data, metadata = parent.objects[name]
                return SimpleNamespace(size=len(data), metadata=metadata)

            def download_blob(self, **kwargs):
                return SimpleNamespace(chunks=lambda: iter([parent.objects[name][0]]))

            def set_blob_metadata(self, metadata):
                parent.objects[name] = (parent.objects[name][0], metadata)

        return Blob()


def pair(tmp_path):
    data = tmp_path / "tile.tif"
    data.write_bytes(b"held satellite data")
    receipt = tmp_path / "tile.receipt.json"
    receipt.write_text(json.dumps({"sha256": hashlib.sha256(data.read_bytes()).hexdigest()}))
    return data, receipt


def test_seed_is_not_committed_until_remote_readback(tmp_path):
    container = FakeContainer()
    archive = MODULE.BlobArchive(container)
    data, receipt = pair(tmp_path)
    archive.publish_pair(data, "images/tile.tif", receipt, readback=False)
    assert not archive.ready("images/tile.tif")
    archive.verify_data("images/tile.tif", MODULE.sha256(data))
    assert archive.ready("images/tile.tif")
    assert data.exists() and receipt.exists()  # no laptop deletion


def test_verified_publish_resumes_without_duplicate_upload(tmp_path):
    container = FakeContainer()
    archive = MODULE.BlobArchive(container)
    data, receipt = pair(tmp_path)
    archive.publish_pair(data, "images/tile.tif", receipt, readback=True)
    used = archive.used
    archive.publish_pair(data, "images/tile.tif", receipt, readback=True)
    assert archive.used == used
    assert MODULE.BlobArchive(container).ready("images/tile.tif")


def test_tampered_remote_data_never_commits(tmp_path):
    container = FakeContainer()
    archive = MODULE.BlobArchive(container)
    data, receipt = pair(tmp_path)
    archive.publish_pair(data, "images/tile.tif", receipt, readback=False)
    _, metadata = container.objects["v1/images/tile.tif"]
    container.objects["v1/images/tile.tif"] = (b"corrupted", metadata)
    with pytest.raises(ValueError, match="readback SHA-256"):
        archive.verify_data("images/tile.tif", MODULE.sha256(data))
    assert not archive.ready("images/tile.tif")


def test_bad_local_receipt_and_storage_budget_do_not_publish(tmp_path):
    container = FakeContainer()
    archive = MODULE.BlobArchive(container, max_bytes=1)
    data, receipt = pair(tmp_path)
    with pytest.raises(RuntimeError, match="storage budget"):
        archive.publish_pair(data, "images/tile.tif", receipt, readback=True)
    assert not container.objects and archive.reserved == 0
    receipt.write_text(json.dumps({"sha256": "incorrect"}))
    with pytest.raises(ValueError, match="Local receipt"):
        archive.publish_pair(data, "images/tile.tif", receipt, readback=True)


def test_conflicting_existing_blob_is_not_overwritten(tmp_path):
    container = FakeContainer()
    archive = MODULE.BlobArchive(container)
    data, receipt = pair(tmp_path)
    archive.publish_pair(data, "images/tile.tif", receipt, readback=True)
    data.write_bytes(b"changed bytes")
    with pytest.raises(ValueError, match="Existing blob hash differs"):
        archive.put_file(data, "images/tile.tif", {})
    assert container.objects["v1/images/tile.tif"][0] == b"held satellite data"
