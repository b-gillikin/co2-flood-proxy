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

from src.provenance import build_run_id, file_record, git_is_dirty, write_run_manifest


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


if __name__ == "__main__":
    unittest.main()
