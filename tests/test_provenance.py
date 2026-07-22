"""Offline checks for deterministic run provenance."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.provenance import (
    FrozenRunError,
    build_run_id,
    build_snapshot_id,
    file_record,
    git_is_dirty,
    validate_frozen_run,
    write_run_manifest,
)


class ProvenanceTests(unittest.TestCase):
    def test_non_git_directory_has_unknown_dirty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(git_is_dirty(Path(directory)))

    def test_run_id_is_deterministic(self):
        cutoff = pd.Timestamp("2026-09-08T00:00:00Z")
        self.assertEqual(
            build_run_id(cutoff, commit="abcdef123456"),
            "20260908T000000Z-abcdef1",
        )

    def test_file_hash_is_stable_across_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_text("timestamp_utc,value\n2026-01-01T00:00:00Z,1\n", encoding="utf-8")

            first = file_record(path, root=Path(directory), include_coverage=True)
            second = file_record(path, root=Path(directory), include_coverage=True)

            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first["rows"], 1)

    def test_manifest_records_inputs_outputs_and_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.csv"
            output = root / "summary.txt"
            manifest_path = root / "run_manifest.json"
            source.write_text("timestamp_utc,value\n2026-01-01T00:00:00Z,1\n", encoding="utf-8")
            output.write_text("result\n", encoding="utf-8")

            write_run_manifest(
                manifest_path,
                [source],
                [output],
                ["python scripts/example.py"],
                pd.Timestamp("2026-01-01T00:00:00Z"),
                root=root,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest["commands"], ["python scripts/example.py"])
            self.assertIsNone(manifest["git_dirty"])
            self.assertEqual(manifest["inputs"][0]["path"], "source.csv")
            self.assertEqual(manifest["outputs"][0]["path"], "summary.txt")

    def valid_frozen_manifest(self, root):
        """Build the smallest coherent manifest accepted by the freeze gate."""
        source = root / "source.csv"
        output = root / "summary.csv"
        source.write_text("timestamp_utc,value\n2026-01-01T00:00:00Z,1\n", encoding="utf-8")
        output.write_text("metric,value\nmean,1\n", encoding="utf-8")
        inputs = [file_record(source, root=root, category="normalized")]
        outputs = [file_record(output, root=root)]
        snapshot_id = build_snapshot_id(inputs)
        return {
            "git_dirty": False,
            "git_dirty_diff_sha256": None,
            "snapshot_id": snapshot_id,
            "inputs": inputs,
            "outputs": outputs,
            "commands": [
                {
                    "step": "fixture",
                    "snapshot_id": snapshot_id,
                    "returncode": 0,
                    "outputs": outputs,
                }
            ],
            "models": [],
        }

    def assert_frozen_refused(self, manifest, root, text):
        with self.assertRaisesRegex(FrozenRunError, text):
            validate_frozen_run(manifest, root=root)

    def test_valid_frozen_manifest_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertTrue(validate_frozen_run(self.valid_frozen_manifest(root), root=root))

    def test_dirty_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.valid_frozen_manifest(root)
            manifest["git_dirty"] = True
            manifest["git_dirty_diff_sha256"] = "abc123"
            self.assert_frozen_refused(manifest, root, "worktree is dirty")

    def test_missing_required_input_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.valid_frozen_manifest(root)
            (root / "source.csv").unlink()
            self.assert_frozen_refused(manifest, root, "Missing required inputs")

    def test_stale_output_not_recreated_by_run_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.valid_frozen_manifest(root)
            manifest["commands"][0]["outputs"] = []
            self.assert_frozen_refused(manifest, root, "not recreated by this run")

    def test_mismatched_command_snapshot_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.valid_frozen_manifest(root)
            manifest["commands"][0]["snapshot_id"] = "sha256:other"
            self.assert_frozen_refused(manifest, root, "mismatched snapshot ID")

    def test_nonconverged_model_cannot_be_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.valid_frozen_manifest(root)
            manifest["models"] = [
                {
                    "detector": "sarimax",
                    "fit_status": "non_converged",
                    "fit_converged": False,
                }
            ]
            self.assert_frozen_refused(manifest, root, "is not valid: non_converged")

    def test_ok_model_requires_explicit_convergence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.valid_frozen_manifest(root)
            manifest["models"] = [
                {"detector": "kalman", "fit_status": "ok", "fit_converged": False}
            ]
            self.assert_frozen_refused(manifest, root, "labeled ok without convergence")


if __name__ == "__main__":
    unittest.main()
