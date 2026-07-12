"""Small provenance helpers for frozen chapter-analysis runs."""

from __future__ import annotations

import hashlib
import json
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


def git_commit(root=ROOT):
    """Return the current git commit, or ``unknown`` outside a checkout."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def git_is_dirty(root=ROOT):
    """Return whether tracked or untracked files differ from ``git_commit``.

    ``None`` is used when the directory is not a readable Git checkout, so a
    manifest never mistakes unknown state for a clean immutable snapshot.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def sha256_file(path, chunk_size=1024 * 1024):
    """Hash one file without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_run_id(data_cutoff, commit=None):
    """Build a deterministic run ID from data cutoff and code commit."""
    cutoff = pd.Timestamp(data_cutoff)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    cutoff = cutoff.tz_convert("UTC")
    commit = commit or git_commit()
    return f"{cutoff.strftime('%Y%m%dT%H%M%SZ')}-{commit[:7]}"


def run_context(data_cutoff, commit=None, root=ROOT):
    """Return the columns shared by run-scoped analysis outputs."""
    commit = commit or git_commit(root)
    cutoff = pd.Timestamp(data_cutoff)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    cutoff = cutoff.tz_convert("UTC")
    return {
        "run_id": build_run_id(cutoff, commit),
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


def file_record(path, root=ROOT, include_coverage=False):
    """Return a manifest record for one existing file."""
    path = Path(path)
    record = {
        "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if include_coverage and path.suffix.lower() == ".csv":
        record.update(_csv_coverage(path))
    return record


def write_run_manifest(
    path,
    input_paths,
    output_paths,
    commands,
    data_cutoff,
    root=ROOT,
):
    """Write the run manifest used to freeze chapter artifacts."""
    context = run_context(data_cutoff, root=root)
    manifest = {
        **context,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_versions": runtime_versions(),
        "commands": list(commands),
        "inputs": [
            file_record(item, root=root, include_coverage=True)
            for item in input_paths
            if Path(item).exists()
        ],
        "outputs": [
            file_record(item, root=root, include_coverage=False)
            for item in output_paths
            if Path(item).exists()
        ],
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
