"""Immutable staging must reject corrupt or mismatched local sources."""

import hashlib
import runpy
import tempfile
import unittest
from pathlib import Path

M = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/103_stage_limburg_eo_archive.py")
)


class StagingTests(unittest.TestCase):
    def test_existing_corruption_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tile.tif"
            path.write_bytes(b"held data")
            digest = hashlib.sha256(b"held data").hexdigest()
            self.assertTrue(M["check_existing"](path, digest))
            with self.assertRaises(ValueError):
                M["check_existing"](path, "0" * 64)
            self.assertEqual(path.read_bytes(), b"held data")

    def test_receipt_identity_and_path(self):
        job = {
            "relative_path": "images/window/product/tile.tif",
            "bands": ["VV"],
            "bounds": [0, 0, 1, 1],
            "window": {"id": "window"},
            "asset_ids": ["source"],
        }
        receipt = dict(job, sha256="a" * 64)
        M["validate_receipt"](job, receipt)
        with self.assertRaises(ValueError):
            M["validate_receipt"](job, dict(receipt, bands=["VH"]))
        for path in ["/tmp/tile.tif", "images/../../tile.tif"]:
            with self.assertRaises(ValueError):
                M["validate_receipt"](
                    dict(job, relative_path=path), dict(receipt, relative_path=path)
                )
