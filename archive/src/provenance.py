"""Provenance, execution-ledger, and freeze checks for chapter runs."""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import platform
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP_CANDIDATES = (
    "timestamp_utc",
    "date_utc",
    "start_timestamp_utc",
    "eval_start_utc",
)
PACKAGE_NAMES = ("numpy", "pandas", "scipy", "statsmodels", "scikit-learn", "pyarrow")
VALID_FIT_STATUSES = {"ok", "non_converged", "failed", "insufficient_data"}


class FrozenRunError(RuntimeError):
    """Raised when a candidate frozen run violates an immutable-run gate."""


def _run_git(args, root=ROOT, *, text=True):
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=text,
        capture_output=True,
        check=True,
    )


def git_commit(root=ROOT):
    """Return the current git commit, or ``unknown`` outside a checkout."""
    try:
        return _run_git(["rev-parse", "HEAD"], root).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def git_status(root=ROOT):
    """Return porcelain status, or ``None`` outside a readable checkout."""
    try:
        return _run_git(["status", "--porcelain=v1", "--untracked-files=all"], root).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def git_is_dirty(root=ROOT):
    """Return whether tracked or untracked files differ from ``git_commit``."""
    status = git_status(root)
    return None if status is None else bool(status.strip())


def git_dirty_diff_hash(root=ROOT):
    """Hash tracked changes plus untracked paths and contents.

    A clean checkout has no dirty-diff hash. Unknown Git state is represented
    by ``None`` and is never accepted by frozen-run validation.
    """
    status = git_status(root)
    if status is None or not status.strip():
        return None
    digest = hashlib.sha256()
    digest.update(status.encode("utf-8"))
    try:
        diff = _run_git(["diff", "--binary", "HEAD", "--"], root, text=False).stdout
        digest.update(diff)
    except (OSError, subprocess.CalledProcessError):
        digest.update(b"git-diff-unavailable")
    for line in status.splitlines():
        if not line.startswith("?? "):
            continue
        path = Path(root) / line[3:]
        if path.is_file():
            digest.update(line[3:].encode("utf-8"))
            digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def sha256_file(path, chunk_size=1024 * 1024):
    """Hash one file without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def aggregate_hash(records):
    """Hash sorted path/hash pairs independently of record ordering."""
    pairs = sorted((record["path"], record["sha256"]) for record in records)
    payload = json.dumps(pairs, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_snapshot_id(input_records):
    """Build the immutable data-snapshot ID from raw and normalized inputs."""
    return f"sha256:{aggregate_hash(input_records)}"


def build_run_id(data_cutoff, commit=None, snapshot_id=None):
    """Build a deterministic run ID from cutoff, code, and data snapshot."""
    cutoff = pd.Timestamp(data_cutoff)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    cutoff = cutoff.tz_convert("UTC")
    commit = commit or git_commit()
    snapshot_token = f"-{snapshot_id.split(':')[-1][:8]}" if snapshot_id else ""
    return f"{cutoff.strftime('%Y%m%dT%H%M%SZ')}-{commit[:7]}{snapshot_token}"


def run_context(data_cutoff, commit=None, root=ROOT, snapshot_id=None):
    """Return the identifiers shared by run-scoped analysis outputs."""
    commit = os.getenv("CHAPTER_GIT_COMMIT") or commit or git_commit(root)
    snapshot_id = os.getenv("CHAPTER_SNAPSHOT_ID") or snapshot_id
    cutoff = pd.Timestamp(os.getenv("CHAPTER_DATA_CUTOFF_UTC") or data_cutoff)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    cutoff = cutoff.tz_convert("UTC")
    return {
        "run_id": os.getenv("CHAPTER_RUN_ID")
        or build_run_id(cutoff, commit, snapshot_id=snapshot_id),
        "snapshot_id": snapshot_id,
        "data_cutoff_utc": cutoff.isoformat(),
        "git_commit": commit,
        "git_dirty": git_is_dirty(root),
    }


def runtime_versions():
    """Return the Python and core scientific-package versions."""
    versions = {"python": platform.python_version()}
    for package in PACKAGE_NAMES:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def _csv_coverage(path):
    """Read lightweight row/time coverage metadata from a CSV."""
    header = pd.read_csv(path, nrows=0)
    timestamp_col = next((c for c in TIMESTAMP_CANDIDATES if c in header.columns), None)
    if timestamp_col is None:
        frame = pd.read_csv(path)
        return {"rows": len(frame)}
    timestamps = pd.read_csv(path, usecols=[timestamp_col])[timestamp_col]
    timestamps = pd.to_datetime(timestamps, utc=True, errors="coerce")
    return {
        "rows": len(timestamps),
        "timestamp_column": timestamp_col,
        "start_utc": timestamps.min().isoformat() if timestamps.notna().any() else None,
        "end_utc": timestamps.max().isoformat() if timestamps.notna().any() else None,
    }


def file_record(path, root=ROOT, include_coverage=False, category=None):
    """Return a manifest record for one existing file."""
    path = Path(path).resolve()
    root = Path(root).resolve()
    record = {
        "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if category is not None:
        record["category"] = category
    if include_coverage and path.suffix.lower() == ".csv":
        record.update(_csv_coverage(path))
    return record


def model_record(path, root=ROOT):
    """Read explicit model identity and convergence from a detector pickle."""
    path = Path(path)
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    diagnostics = payload.get("fit_diagnostics", {}) or {}
    record = file_record(path, root=root)
    record.update(
        {
            "detector": payload.get("detector_spec", {}).get("detector"),
            "model_family": payload.get("model_type"),
            "fit_status": payload.get("fit_status"),
            "fit_converged": diagnostics.get("converged"),
            "fit_warnings": diagnostics.get("warning_messages", ""),
        }
    )
    return record


def _records(paths, root, *, coverage=False, category=None):
    return [
        file_record(item, root=root, include_coverage=coverage, category=category)
        for item in paths
        if Path(item).is_file()
    ]


def scientific_output_hash(output_records):
    """Hash reviewable numerical/text outputs, excluding binary render details."""
    scientific = [
        record
        for record in output_records
        if Path(record["path"]).suffix.lower() in {".csv", ".json", ".txt", ".parquet"}
        and not record["path"].endswith("run_manifest.json")
        and "/run_logs/" not in f"/{record['path']}"
    ]
    return aggregate_hash(scientific)


def write_run_manifest(
    path,
    input_paths,
    output_paths,
    commands,
    data_cutoff,
    root=ROOT,
    *,
    raw_input_paths=(),
    normalized_input_paths=None,
    execution_ledger=None,
    snapshot_id=None,
    model_paths=(),
    frozen=False,
    git_root=None,
    analysis_scope=None,
):
    """Write a manifest that can prove one coherent chapter-analysis run."""
    normalized_input_paths = (
        input_paths if normalized_input_paths is None else normalized_input_paths
    )
    raw_records = _records(raw_input_paths, root, coverage=False, category="raw")
    normalized_records = _records(
        normalized_input_paths, root, coverage=True, category="normalized"
    )
    input_records = [*raw_records, *normalized_records]
    snapshot_id = snapshot_id or build_snapshot_id(input_records)
    git_root = Path(git_root) if git_root is not None else Path(root)
    context = run_context(data_cutoff, root=git_root, snapshot_id=snapshot_id)
    output_records = _records(output_paths, root)
    command_records = list(execution_ledger or commands)
    manifest = {
        "manifest_schema_version": 2,
        **context,
        "frozen": bool(frozen),
        "analysis_scope": analysis_scope or {},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_versions": runtime_versions(),
        "git_dirty_diff_sha256": git_dirty_diff_hash(git_root),
        "commands": command_records,
        "raw_inputs": raw_records,
        "normalized_inputs": normalized_records,
        "inputs": input_records,
        "outputs": output_records,
        "scientific_output_sha256": scientific_output_hash(output_records),
        "models": [model_record(item, root=root) for item in model_paths if Path(item).is_file()],
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    return manifest


def _path_from_record(record, root):
    path = Path(record["path"])
    return path if path.is_absolute() else Path(root).resolve() / path


def frozen_run_errors(manifest, root=ROOT):
    """Return every reason a manifest cannot be accepted as frozen."""
    errors = []
    if manifest.get("git_dirty") is not False:
        errors.append("Git worktree is dirty or its state is unknown")
    if manifest.get("git_dirty_diff_sha256") is not None:
        errors.append("Dirty-diff hash is present")
    if manifest.get("frozen"):
        scope = manifest.get("analysis_scope", {})
        direct_state = scope.get("direct_state")
        if direct_state not in {"included", "explicit_data_limited_omission"}:
            errors.append("Frozen manifest lacks an explicit direct-state scope")
        if scope.get("rolling_origin") != "included":
            errors.append("Frozen manifest omits rolling-origin evaluation")
    inputs = manifest.get("inputs", [])
    missing_inputs = []
    changed_inputs = []
    for record in inputs:
        path = _path_from_record(record, root)
        if not path.is_file():
            missing_inputs.append(record["path"])
        elif sha256_file(path) != record.get("sha256"):
            changed_inputs.append(record["path"])
    if missing_inputs:
        errors.append("Missing required inputs: " + ", ".join(missing_inputs))
    if changed_inputs:
        errors.append("Input hashes changed: " + ", ".join(changed_inputs))
    if inputs and manifest.get("snapshot_id") != build_snapshot_id(inputs):
        errors.append("Manifest snapshot ID does not match its input hashes")

    commands = manifest.get("commands", [])
    if not commands or not all(isinstance(item, dict) for item in commands):
        errors.append("No verifiable execution ledger is present")
        commands = []
    produced = {}
    for item in commands:
        if item.get("snapshot_id") != manifest.get("snapshot_id"):
            errors.append(f"Command {item.get('step', '?')} has a mismatched snapshot ID")
        if item.get("returncode") != 0:
            errors.append(f"Command {item.get('step', '?')} did not finish successfully")
        for record in item.get("outputs", []):
            produced[record["path"]] = record

    for record in manifest.get("outputs", []):
        path = _path_from_record(record, root)
        if not path.is_file():
            errors.append(f"Required output is missing: {record['path']}")
            continue
        current_hash = sha256_file(path)
        if current_hash != record.get("sha256"):
            errors.append(f"Output hash changed after the run: {record['path']}")
        ledger_record = produced.get(record["path"])
        if ledger_record is None:
            errors.append(f"Output was not recreated by this run: {record['path']}")
        elif ledger_record.get("sha256") != record.get("sha256"):
            errors.append(f"Ledger hash differs for output: {record['path']}")

    for model in manifest.get("models", []):
        status = model.get("fit_status")
        if status not in VALID_FIT_STATUSES:
            errors.append(f"Model {model.get('detector')} has invalid fit status: {status}")
        if status != "ok":
            errors.append(f"Model {model.get('detector')} is not valid: {status}")
        elif model.get("fit_converged") is not True:
            errors.append(f"Model {model.get('detector')} is labeled ok without convergence")
    return errors


def validate_frozen_run(manifest, root=ROOT):
    """Raise ``FrozenRunError`` unless the manifest is a coherent clean run."""
    errors = frozen_run_errors(manifest, root=root)
    if errors:
        raise FrozenRunError("Frozen run refused:\n- " + "\n- ".join(errors))
    return True
