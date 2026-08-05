"""Offline execution ledger for core modelling plus optional direct state."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.provenance import (
    build_run_id,
    build_snapshot_id,
    file_record,
    git_commit,
    git_is_dirty,
)


@dataclass(frozen=True)
class PipelineStep:
    """One actual script invocation and every artifact lane it owns."""

    name: str
    script: str
    arguments: tuple[str, ...]
    output_targets: tuple[str, ...]


def chapter_steps(
    *,
    fixture=False,
    skip_rolling=False,
    skip_transfer=False,
    include_direct_state=False,
):
    """Return the locked core sequence plus requested optional lanes."""
    quick_maxiter = ("--maxiter", "0") if fixture else ()
    rolling = ("--skip-rolling",) if skip_rolling or fixture else ()
    bootstrap = ("--bootstrap-replicates", "50") if fixture else ()
    steps = [
        PipelineStep(
            "05_sarimax",
            "scripts/05_sarimax.py",
            quick_maxiter,
            (
                "results/sarimax",
                "results/models/sarimax.pkl",
                "results/models/sarimax_order_search.csv",
                "data/processed/sarimax-residuals.csv",
                "data/processed/sarimax-anomalies.csv",
            ),
        ),
        PipelineStep(
            "06_kalman",
            "scripts/06_kalman.py",
            quick_maxiter,
            (
                "results/kalman",
                "results/models/kalman.pkl",
                "data/processed/kalman-innovations.csv",
                "data/processed/kalman-anomalies.csv",
            ),
        ),
        PipelineStep(
            "07_isolation_forest",
            "scripts/07_isolation_forest.py",
            (),
            (
                "results/iforest",
                "results/models/iforest.pkl",
                "data/processed/iforest-scores.csv",
                "data/processed/iforest-anomalies.csv",
            ),
        ),
        PipelineStep(
            "08_ensemble_agreement",
            "scripts/08_ensemble_agreement.py",
            (),
            ("results/ensemble", "data/processed/ensemble_anomaly_flags.csv"),
        ),
        PipelineStep(
            "09_synthetic_injection",
            "scripts/09_synthetic_injection.py",
            (),
            ("results/synthetic_injection",),
        ),
        PipelineStep(
            "10_evaluation",
            "scripts/10_evaluation.py",
            rolling,
            ("results/evaluation", "data/processed/api.csv"),
        ),
        PipelineStep(
            "12_distributed_lag",
            "scripts/12_distributed_lag.py",
            bootstrap,
            ("results/distributed_lag",),
        ),
    ]
    if include_direct_state:
        steps.insert(
            -1,
            PipelineStep(
                "16_direct_state",
                "scripts/16_direct_state.py",
                ("--bootstrap-replicates", "50") if fixture else (),
                ("results/direct_state",),
            ),
        )
    if not skip_transfer:
        steps.append(
            PipelineStep(
                "11_transfer_stress_test",
                "scripts/11_transfer_stress_test.py",
                ("--min-transfer-hours", "24") if fixture else (),
                (
                    "results/transfer",
                    "results/figures/figure_manifest.csv",
                    "results/models/sarimax-transfer.pkl",
                    "results/models/kalman-transfer.pkl",
                    "results/models/iforest-transfer.pkl",
                    "data/processed/transfer-anomalies",
                    "data/processed/events-transfer-heerlen_looierstraat_nl10136.csv",
                    "data/processed/events-transfer-heerlen_jamboreepad_nl10138.csv",
                ),
            )
        )
    return tuple(steps)


def collect_files(paths):
    """Expand files and directories to a stable unique file inventory."""
    files = []
    for value in paths:
        path = Path(value).resolve()
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
    return sorted(set(files))


def invalidate_outputs(workspace, targets):
    """Remove every artifact owned by a step before that step starts."""
    for target in targets:
        path = Path(workspace) / target
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def execute_pipeline(
    workspace,
    repo_root,
    raw_inputs,
    normalized_inputs,
    data_cutoff,
    *,
    fixture=False,
    skip_rolling=False,
    skip_transfer=False,
    include_direct_state=False,
    frozen=False,
    python_executable=None,
):
    """Run actual script entry points and return a snapshot-scoped ledger."""
    workspace = Path(workspace).resolve()
    repo_root = Path(repo_root).resolve()
    python_executable = str(python_executable or sys.executable)
    raw_candidates = [Path(path) for path in raw_inputs]
    normalized_candidates = [Path(path) for path in normalized_inputs]
    missing = [path for path in normalized_candidates if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required normalized inputs: " + ", ".join(str(path) for path in missing)
        )
    raw_inputs = collect_files(raw_candidates)
    normalized_inputs = collect_files(normalized_candidates)
    if not raw_inputs:
        raise FileNotFoundError("No raw input files were found for the snapshot")
    input_records = [
        *[file_record(path, root=workspace, category="raw") for path in raw_inputs],
        *[
            file_record(path, root=workspace, include_coverage=True, category="normalized")
            for path in normalized_inputs
        ],
    ]
    if not normalized_inputs:
        raise FileNotFoundError("No normalized input files were found for the snapshot")
    if frozen and (skip_rolling or fixture):
        raise RuntimeError(
            "Frozen run refused before execution: fixture/skip mode omits rolling evaluation"
        )
    if frozen and git_is_dirty(repo_root) is not False:
        raise RuntimeError("Frozen run refused before execution: Git worktree is not clean")

    snapshot_id = build_snapshot_id(input_records)
    commit = git_commit(repo_root)
    run_id = build_run_id(data_cutoff, commit, snapshot_id=snapshot_id)
    environment = os.environ.copy()
    environment.update(
        {
            "CHAPTER_SNAPSHOT_ID": snapshot_id,
            "CHAPTER_RUN_ID": run_id,
            "CHAPTER_DATA_CUTOFF_UTC": pd.Timestamp(data_cutoff).isoformat(),
            "CHAPTER_GIT_COMMIT": commit,
            "MPLCONFIGDIR": str(workspace / ".matplotlib"),
            "PYTHONHASHSEED": "0",
        }
    )
    (workspace / "results/run_logs").mkdir(parents=True, exist_ok=True)
    ledger = []
    for step in chapter_steps(
        fixture=fixture,
        skip_rolling=skip_rolling,
        skip_transfer=skip_transfer,
        include_direct_state=include_direct_state,
    ):
        invalidate_outputs(workspace, step.output_targets)
        command = [python_executable, str(repo_root / step.script), *step.arguments]
        started = datetime.now(timezone.utc)
        result = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        finished = datetime.now(timezone.utc)
        log_path = workspace / "results/run_logs" / f"{step.name}.log"
        log_path.write_text(
            result.stdout + ("\nSTDERR\n" + result.stderr if result.stderr else ""),
            encoding="utf-8",
        )
        produced = collect_files(workspace / target for target in step.output_targets)
        record = {
            "step": step.name,
            "command": [python_executable, step.script, *step.arguments],
            "snapshot_id": snapshot_id,
            "started_at_utc": started.isoformat(),
            "finished_at_utc": finished.isoformat(),
            "returncode": result.returncode,
            "outputs": [file_record(path, root=workspace) for path in produced],
            "log_path": str(log_path.relative_to(workspace)),
        }
        ledger.append(record)
        if result.returncode != 0:
            raise RuntimeError(
                f"{step.name} failed with exit {result.returncode}; see {log_path}\n"
                + result.stderr[-2000:]
            )
        if not produced:
            raise RuntimeError(f"{step.name} completed without recreating any owned output")
    return {
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "git_commit": commit,
        "raw_inputs": raw_inputs,
        "normalized_inputs": normalized_inputs,
        "ledger": ledger,
    }
