"""Inspect or freeze-validate the manifest written by the pipeline runner.

This compatibility entry point no longer invents a command list from the
documented run order. Use ``15_run_analysis_pipeline.py`` to execute scripts
05-12 and create the manifest, then use this script for an explicit check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.provenance import frozen_run_errors

MANIFEST_PATH = Path("results/run_manifest.json")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Apply clean-tree, snapshot, ledger, output, and convergence gates.",
    )
    args = parser.parse_args()

    if not args.manifest.is_file():
        raise FileNotFoundError(
            f"{args.manifest} does not exist; run scripts/15_run_analysis_pipeline.py first"
        )
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("manifest_schema_version") != 2:
        raise RuntimeError("Manifest predates the verifiable Batch 3 schema; rerun the pipeline")
    commands = manifest.get("commands", [])
    if not commands or not all(isinstance(item, dict) for item in commands):
        raise RuntimeError("Manifest lacks an actual execution ledger; rerun the pipeline")
    if args.freeze:
        errors = frozen_run_errors(manifest, root=Path.cwd())
        if errors:
            raise RuntimeError("Frozen run refused:\n- " + "\n- ".join(errors))

    print(f"manifest: {args.manifest}")
    print(f"run_id: {manifest['run_id']}")
    print(f"snapshot_id: {manifest['snapshot_id']}")
    print(f"commands completed: {len(commands)}")
    print(f"outputs recorded: {len(manifest.get('outputs', []))}")
    print(f"scientific_output_sha256: {manifest['scientific_output_sha256']}")
    print(
        "status: frozen gates passed" if args.freeze else "status: verifiable development manifest"
    )


if __name__ == "__main__":
    main()
