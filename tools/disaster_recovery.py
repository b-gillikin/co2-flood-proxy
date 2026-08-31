#!/usr/bin/env python3
"""Inventory, back up, restore, and verify chapter source data.

The remote operation is deliberately ``rclone copy`` rather than ``sync``:
deleting a local file can never delete its remote backup. Replaced remote
objects are moved into a timestamped ``_versions`` directory.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "recovery" / "config.json"
MANIFEST_PATH = ROOT / "recovery" / "data-manifest.tsv"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        config = json.load(handle)
    required = {"chapter_id", "remote", "remote_root", "paths"}
    missing = required - config.keys()
    if missing:
        raise SystemExit(f"Missing recovery config keys: {', '.join(sorted(missing))}")
    return config


def iter_files(config: dict):
    for relative in config["paths"]:
        source = ROOT / relative
        if not source.exists():
            continue
        if source.is_symlink():
            raise SystemExit(f"Refusing to inventory symlink: {relative}")
        if source.is_file():
            yield source
            continue
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise SystemExit(f"Refusing to inventory symlink: {path.relative_to(ROOT)}")
            if path.is_file():
                yield path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(config: dict) -> list[tuple[str, int, str]]:
    return [
        (sha256(path), path.stat().st_size, path.relative_to(ROOT).as_posix())
        for path in iter_files(config)
    ]


def write_manifest(rows: list[tuple[str, int, str]], destination: Path = MANIFEST_PATH) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = "sha256\tsize_bytes\tpath\n" + "".join(
        f"{digest}\t{size}\t{path}\n" for digest, size, path in rows
    )
    destination.write_text(content, encoding="utf-8")


def read_manifest(path: Path) -> list[tuple[str, int, str]]:
    rows = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "sha256\tsize_bytes\tpath":
        raise SystemExit(f"Invalid recovery manifest: {path}")
    for line in lines[1:]:
        digest, size, relative = line.split("\t", 2)
        rows.append((digest, int(size), relative))
    return rows


def verify(manifest: Path) -> int:
    missing: list[str] = []
    changed: list[str] = []
    for expected_hash, expected_size, relative in read_manifest(manifest):
        path = ROOT / relative
        if not path.is_file():
            missing.append(relative)
        elif path.stat().st_size != expected_size or sha256(path) != expected_hash:
            changed.append(relative)
    print(f"Verified manifest: {manifest}")
    print(f"Missing: {len(missing)}; changed: {len(changed)}")
    for label, items in (("missing", missing), ("changed", changed)):
        for item in items[:20]:
            print(f"  {label}: {item}")
        if len(items) > 20:
            print(f"  ... and {len(items) - 20} more")
    return 1 if missing or changed else 0


def require_rclone(remote: str) -> None:
    if not shutil.which("rclone"):
        raise SystemExit("rclone is not installed; install it before backup or restore")
    result = subprocess.run(
        ["rclone", "listremotes"], capture_output=True, text=True, check=True
    )
    if f"{remote}:" not in result.stdout.splitlines():
        raise SystemExit(
            f"rclone remote '{remote}' is not configured. Run: rclone config"
        )


def remote_base(config: dict) -> str:
    remote = os.environ.get("DISSERTATION_BACKUP_REMOTE", config["remote"])
    root = os.environ.get("DISSERTATION_BACKUP_ROOT", config["remote_root"])
    return f"{remote}:{root.rstrip('/')}/{config['chapter_id']}"


def azure_base(config: dict) -> str:
    return f"{config['remote_root'].strip('/')}/{config['chapter_id']}"


def azure_common(config: dict) -> list[str]:
    return [
        "--account-name", config["azure_account"],
        "--auth-mode", "login",
        "--only-show-errors",
    ]


def require_azure(config: dict) -> None:
    if not shutil.which("az"):
        raise SystemExit("Azure CLI is not installed; install it and run: az login")
    result = subprocess.run(
        ["az", "account", "show", "--query", "id", "-o", "tsv"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise SystemExit("Azure CLI is not authenticated; run: az login")
    expected = config.get("azure_subscription_id")
    if expected and result.stdout.strip() != expected:
        raise SystemExit(
            f"Wrong Azure subscription: {result.stdout.strip()}; expected {expected}"
        )


def azure_blob_exists(config: dict, name: str) -> bool:
    result = subprocess.run(
        [
            "az", "storage", "blob", "exists",
            "--container-name", config["azure_container"],
            "--name", name,
            *azure_common(config),
            "--query", "exists", "-o", "tsv",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().lower() == "true"


def fetch_azure_manifest(config: dict, destination: Path) -> list[tuple[str, int, str]] | None:
    name = f"{azure_base(config)}/_recovery/data-manifest.tsv"
    if not azure_blob_exists(config, name):
        return None
    run([
        "az", "storage", "blob", "download",
        "--container-name", config["azure_container"],
        "--name", name,
        "--file", str(destination),
        "--overwrite", "true",
        "--no-progress",
        *azure_common(config),
        "-o", "none",
    ])
    return read_manifest(destination)


def azure_upload_file(config: dict, source: Path, relative: str) -> None:
    run([
        "az", "storage", "blob", "upload",
        "--container-name", config["azure_container"],
        "--name", f"{azure_base(config)}/{relative}",
        "--file", str(source),
        "--overwrite", "true",
        "--no-progress",
        *azure_common(config),
        "-o", "none",
    ])


def backup_azure(
    config: dict, rows: list[tuple[str, int, str]], dry_run: bool
) -> int:
    require_azure(config)
    with tempfile.TemporaryDirectory(prefix="dissertation-azure-manifest-") as temp_dir:
        remote_rows = fetch_azure_manifest(config, Path(temp_dir) / "data-manifest.tsv")
    if remote_rows is None:
        for relative in config["paths"]:
            source = ROOT / relative
            if not source.exists():
                print(f"skip missing path: {relative}")
                continue
            if dry_run:
                print(f"would upload initial path: {relative}")
            elif source.is_dir():
                run([
                    "az", "storage", "blob", "upload-batch",
                    "--destination", config["azure_container"],
                    "--destination-path", f"{azure_base(config)}/{relative}",
                    "--source", str(source),
                    "--overwrite", "true",
                    "--no-progress",
                    *azure_common(config),
                    "-o", "none",
                ])
            else:
                azure_upload_file(config, source, relative)
        changed = rows
    else:
        remote = {path: (digest, size) for digest, size, path in remote_rows}
        changed = [row for row in rows if remote.get(row[2]) != (row[0], row[1])]
        for _digest, _size, relative in changed:
            if dry_run:
                print(f"would upload changed file: {relative}")
            else:
                azure_upload_file(config, ROOT / relative, relative)
    if not dry_run and (remote_rows is None or remote_rows != rows):
        azure_upload_file(config, MANIFEST_PATH, "_recovery/data-manifest.tsv")
    total = sum(size for _digest, size, _path in rows)
    print(
        f"Azure destination: {config['azure_account']}/"
        f"{config['azure_container']}/{azure_base(config)}"
    )
    print(
        f"Inventory: {len(rows)} files, {total / (1024**3):.2f} GiB; "
        f"uploaded or changed: {len(changed)}"
    )
    return 0


def restore_azure(config: dict, overwrite: bool) -> int:
    require_azure(config)
    with tempfile.TemporaryDirectory(prefix="dissertation-azure-restore-") as temp_dir:
        temp = Path(temp_dir)
        remote_manifest_path = temp / "remote-manifest.tsv"
        remote_rows = fetch_azure_manifest(config, remote_manifest_path)
        if remote_rows is None:
            raise SystemExit("Azure recovery manifest is missing; run backup first")
        run([
            "az", "storage", "blob", "download-batch",
            "--destination", str(temp),
            "--source", config["azure_container"],
            "--pattern", f"{azure_base(config)}/*",
            "--max-connections", "8",
            "--no-progress",
            *azure_common(config),
            "-o", "none",
        ])
        downloaded_root = temp / azure_base(config)
        for _digest, _size, relative in remote_rows:
            source = downloaded_root / relative
            destination = ROOT / relative
            if destination.exists() and not overwrite:
                continue
            copy_local(source, destination)
        return verify(remote_manifest_path)


def local_base(config: dict) -> Path | None:
    explicit = os.environ.get("DISSERTATION_BACKUP_LOCAL_ROOT")
    if explicit:
        onedrive_root = Path(explicit).expanduser()
    else:
        cloud = Path.home() / "Library" / "CloudStorage"
        candidates = sorted(path for path in cloud.glob("OneDrive-*") if path.is_dir())
        if len(candidates) != 1:
            return None
        onedrive_root = candidates[0]
    return onedrive_root / config["remote_root"] / config["chapter_id"]


def copy_local(source: Path, destination: Path, version: Path | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and source.stat().st_size == destination.stat().st_size:
        if sha256(source) == sha256(destination):
            return
    if destination.exists() and version is not None:
        version.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, version)
    shutil.copy2(source, destination)


def backup_local(config: dict, rows: list[tuple[str, int, str]], dry_run: bool) -> int:
    base = local_base(config)
    if base is None:
        raise SystemExit("No OneDrive CloudStorage folder found; sign in to OneDrive first")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for _digest, _size, relative in rows:
        source = ROOT / relative
        destination = base / relative
        version = base / "_versions" / timestamp / relative
        if dry_run:
            print(f"would copy: {relative}")
        else:
            copy_local(source, destination, version)
    if not dry_run:
        copy_local(MANIFEST_PATH, base / "_recovery" / "data-manifest.tsv")
    total = sum(size for _digest, size, _path in rows)
    print(f"OneDrive destination: {base}")
    print(f"Inventory: {len(rows)} files, {total / (1024**3):.2f} GiB")
    return 0


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def backup(config: dict, dry_run: bool) -> int:
    rows = build_inventory(config)
    write_manifest(rows)
    if config.get("azure_account"):
        return backup_azure(config, rows, dry_run)
    if local_base(config) is not None:
        return backup_local(config, rows, dry_run)
    remote = os.environ.get("DISSERTATION_BACKUP_REMOTE", config["remote"])
    require_rclone(remote)
    base = remote_base(config)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    common = ["--checksum", "--metadata", "--create-empty-src-dirs"]
    if dry_run:
        common.append("--dry-run")
    for relative in config["paths"]:
        source = ROOT / relative
        if not source.exists():
            print(f"skip missing path: {relative}")
            continue
        destination = f"{base}/{relative}"
        version_dir = f"{base}/_versions/{timestamp}/{relative}"
        if source.is_dir():
            run(["rclone", "copy", str(source), destination, *common, "--backup-dir", version_dir])
        else:
            run(["rclone", "copyto", str(source), destination, *common, "--backup-dir", version_dir])
    run([
        "rclone", "copyto", str(MANIFEST_PATH), f"{base}/_recovery/data-manifest.tsv",
        "--metadata", *(["--dry-run"] if dry_run else []),
    ])
    total = sum(size for _digest, size, _path in rows)
    print(f"Inventory: {len(rows)} files, {total / (1024**3):.2f} GiB")
    return 0


def restore(config: dict, overwrite: bool) -> int:
    if config.get("azure_account"):
        return restore_azure(config, overwrite)
    local = local_base(config)
    if local is not None:
        remote_manifest = local / "_recovery" / "data-manifest.tsv"
        if not remote_manifest.is_file():
            raise SystemExit(f"Remote manifest not found: {remote_manifest}")
        for _digest, _size, relative in read_manifest(remote_manifest):
            source = local / relative
            destination = ROOT / relative
            if destination.exists() and not overwrite:
                continue
            copy_local(source, destination)
        return verify(remote_manifest)
    remote = os.environ.get("DISSERTATION_BACKUP_REMOTE", config["remote"])
    require_rclone(remote)
    base = remote_base(config)
    common = ["--checksum", "--metadata", "--create-empty-src-dirs"]
    if not overwrite:
        common.append("--ignore-existing")
    with tempfile.TemporaryDirectory(prefix="dissertation-restore-") as temp_dir:
        remote_manifest = Path(temp_dir) / "data-manifest.tsv"
        run(["rclone", "copyto", f"{base}/_recovery/data-manifest.tsv", str(remote_manifest)])
        for relative in config["paths"]:
            run(["rclone", "copy", f"{base}/{relative}", str(ROOT / relative), *common])
        return verify(remote_manifest)


def doctor(config: dict) -> int:
    print(f"Chapter: {config['chapter_id']}")
    print(f"Repository: {ROOT}")
    print(f"Protected paths: {', '.join(config['paths'])}")
    if config.get("azure_account"):
        print(
            f"Azure destination: {config['azure_account']}/"
            f"{config['azure_container']}/{azure_base(config)}"
        )
        try:
            require_azure(config)
            subprocess.run(
                [
                    "az", "storage", "container", "show",
                    "--name", config["azure_container"],
                    *azure_common(config),
                    "-o", "none",
                ],
                check=True,
            )
        except (SystemExit, subprocess.CalledProcessError) as exc:
            print(f"Azure check: FAILED ({exc})")
            return 1
        print("Azure check: OK")
        return 0
    local = local_base(config)
    if local is not None:
        print(f"OneDrive destination: {local}")
        print("OneDrive check: OK")
        return 0
    print(f"Remote destination: {remote_base(config)}")
    remote = os.environ.get("DISSERTATION_BACKUP_REMOTE", config["remote"])
    try:
        require_rclone(remote)
    except (SystemExit, subprocess.CalledProcessError) as exc:
        print(f"Remote check: FAILED ({exc})")
        return 1
    result = subprocess.run(
        ["rclone", "lsd", f"{remote}:"], capture_output=True, text=True
    )
    if result.returncode:
        print(f"Remote check: FAILED ({result.stderr.strip()})")
        return 1
    print("Remote check: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inventory", help="hash protected local files and write the manifest")
    verify_parser = subparsers.add_parser("verify", help="verify local files against the manifest")
    verify_parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    backup_parser = subparsers.add_parser("backup", help="copy protected paths to remote storage")
    backup_parser.add_argument("--dry-run", action="store_true")
    restore_parser = subparsers.add_parser("restore", help="restore protected paths from remote storage")
    restore_parser.add_argument(
        "--overwrite", action="store_true", help="replace differing local files; default preserves them"
    )
    subparsers.add_parser("doctor", help="check local tooling and remote connectivity")
    args = parser.parse_args()
    config = load_config()
    if args.command == "inventory":
        rows = build_inventory(config)
        write_manifest(rows)
        print(f"Wrote {MANIFEST_PATH.relative_to(ROOT)} with {len(rows)} files")
        return 0
    if args.command == "verify":
        return verify(args.manifest)
    if args.command == "backup":
        return backup(config, args.dry_run)
    if args.command == "restore":
        return restore(config, args.overwrite)
    return doctor(config)


if __name__ == "__main__":
    raise SystemExit(main())
