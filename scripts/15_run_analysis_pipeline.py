"""Run scripts 05-12 offline and write a verifiable run manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.pipeline import execute_pipeline
from src.provenance import validate_frozen_run, write_run_manifest

DEFAULT_NORMALIZED_INPUTS = (
    "data/interim/analysis_hourly.csv",
    "data/interim/knmi_hourly.csv",
    "data/interim/rivm_hourly.csv",
    "data/processed/signal_characterization_frame.csv",
    "data/processed/event_catalogue.csv",
    "data/processed/hourly_soft_labels.csv",
)
MODEL_PATHS = (
    "results/models/sarimax.pkl",
    "results/models/kalman.pkl",
    "results/models/iforest.pkl",
)


def analysis_cutoff(workspace):
    """Read the data cutoff from the canonical analysis grid."""
    path = Path(workspace) / "data/interim/analysis_hourly.csv"
    timestamps = pd.read_csv(path, usecols=["timestamp_utc"])["timestamp_utc"]
    return pd.to_datetime(timestamps, utc=True).max()


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument(
        "--python",
        type=Path,
        default=Path(sys.executable),
        help="Python 3.11 chapter-environment executable used for scripts 05-12.",
    )
    parser.add_argument("--output", type=Path, default=Path("results/run_manifest.json"))
    parser.add_argument("--raw-input", action="append", type=Path)
    parser.add_argument("--normalized-input", action="append", type=Path)
    parser.add_argument("--fixture", action="store_true", help="Use bounded offline test settings.")
    parser.add_argument("--skip-rolling", action="store_true")
    parser.add_argument(
        "--skip-transfer",
        action="store_true",
        help="Omit secondary script 11 when shared-feature coverage is inadequate.",
    )
    parser.add_argument("--freeze", action="store_true", help="Require all immutable-run gates.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    raw_candidates = args.raw_input or [workspace / "data/raw"]
    normalized_candidates = args.normalized_input or [
        workspace / path for path in DEFAULT_NORMALIZED_INPUTS
    ]
    cutoff = analysis_cutoff(workspace)
    execution = execute_pipeline(
        workspace,
        ROOT,
        raw_candidates,
        normalized_candidates,
        cutoff,
        fixture=args.fixture,
        skip_rolling=args.skip_rolling,
        skip_transfer=args.skip_transfer,
        frozen=args.freeze,
        python_executable=args.python,
    )
    output_paths = []
    for command in execution["ledger"]:
        output_paths.extend(workspace / record["path"] for record in command["outputs"])
    output_path = args.output if args.output.is_absolute() else workspace / args.output
    manifest = write_run_manifest(
        output_path,
        execution["normalized_inputs"],
        sorted(set(output_paths)),
        [],
        cutoff,
        root=workspace,
        raw_input_paths=execution["raw_inputs"],
        normalized_input_paths=execution["normalized_inputs"],
        execution_ledger=execution["ledger"],
        snapshot_id=execution["snapshot_id"],
        model_paths=[workspace / path for path in MODEL_PATHS],
        frozen=args.freeze,
        git_root=ROOT,
    )
    if args.freeze:
        validate_frozen_run(manifest, root=workspace)
    print(f"wrote {output_path}")
    print(f"run_id: {manifest['run_id']}")
    print(f"snapshot_id: {manifest['snapshot_id']}")
    print(f"scientific_output_sha256: {manifest['scientific_output_sha256']}")


if __name__ == "__main__":
    main()
