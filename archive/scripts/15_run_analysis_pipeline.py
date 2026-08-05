"""Run core modelling and available direct-state analysis with a verifiable manifest."""

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
GROUNDWATER_INPUTS = (
    "data/interim/groundwater_daily.csv",
    "data/interim/groundwater_series.csv",
)


def analysis_cutoff(workspace):
    """Read the data cutoff from the canonical analysis grid."""
    path = Path(workspace) / "data/interim/analysis_hourly.csv"
    timestamps = pd.read_csv(path, usecols=["timestamp_utc"])["timestamp_utc"]
    return pd.to_datetime(timestamps, utc=True).max()


def direct_state_scope(workspace, mode, frozen=False):
    """Resolve the direct-state lane without silently weakening a frozen run."""
    paths = [Path(workspace) / path for path in GROUNDWATER_INPUTS]
    present = [path.is_file() for path in paths]
    if any(present) and not all(present):
        raise FileNotFoundError("Direct-state inputs are incomplete: " + ", ".join(map(str, paths)))
    if mode == "required" and not all(present):
        raise FileNotFoundError("Direct-state mode is required but normalized inputs are missing")
    if frozen and mode == "auto" and not all(present):
        raise RuntimeError(
            "Frozen run requires direct-state data or explicit --direct-state omit "
            "for the prespecified data-limited outcome"
        )
    include = all(present) and mode != "omit"
    return include, paths if include else []


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
    parser.add_argument(
        "--direct-state",
        choices=("auto", "required", "omit"),
        default="auto",
        help="Auto-run normalized water data, require it, or explicitly freeze data-limited.",
    )
    parser.add_argument("--freeze", action="store_true", help="Require all immutable-run gates.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    raw_candidates = args.raw_input or [workspace / "data/raw"]
    normalized_candidates = args.normalized_input or [
        workspace / path for path in DEFAULT_NORMALIZED_INPUTS
    ]
    include_direct_state, groundwater_inputs = direct_state_scope(
        workspace,
        args.direct_state,
        frozen=args.freeze,
    )
    normalized_candidates.extend(groundwater_inputs)
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
        include_direct_state=include_direct_state,
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
        analysis_scope={
            "direct_state": (
                "included" if include_direct_state else "explicit_data_limited_omission"
            ),
            "rolling_origin": (
                "omitted_development_only" if args.skip_rolling or args.fixture else "included"
            ),
            "transfer": "omitted_secondary" if args.skip_transfer else "included_secondary",
        },
    )
    if args.freeze:
        validate_frozen_run(manifest, root=workspace)
    print(f"wrote {output_path}")
    print(f"run_id: {manifest['run_id']}")
    print(f"snapshot_id: {manifest['snapshot_id']}")
    print(f"scientific_output_sha256: {manifest['scientific_output_sha256']}")


if __name__ == "__main__":
    main()
