#!/usr/bin/env python3
"""Offload complete prediction groups with Azure readback before local cleanup."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/limburg_chapter_sized_v1/external"
ACCOUNT = "stkerkradeprod01bg"
CONTAINER = "limburg-compact-eo"
PREFIX = "limburg-chapter-v1/predictions"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_az(*arguments: str) -> None:
    subprocess.run(["az", "storage", "blob", *arguments,
                    "--account-name", ACCOUNT, "--container-name", CONTAINER,
                    "--auth-mode", "login", "--only-show-errors", "--output", "none"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def blob_exists(name: str) -> bool:
    result = subprocess.run(["az", "storage", "blob", "exists", "--name", name,
                             "--account-name", ACCOUNT, "--container-name", CONTAINER,
                             "--auth-mode", "login", "--query", "exists", "--output", "tsv",
                             "--only-show-errors"], check=True, text=True,
                            capture_output=True)
    return result.stdout.strip().lower() == "true"


def archived_members(output: Path) -> set[str]:
    members = set()
    for path in (output / "archives").glob("*.json"):
        record = json.loads(path.read_text())
        if record.get("status") != "remote_readback_verified":
            raise ValueError(f"Unverified archive ledger: {path}")
        members.update(record["members"])
    return members


def choose_groups(output: Path, max_groups: int) -> dict[str, dict]:
    done = archived_members(output)
    chosen = {}
    for receipt in sorted((output / "receipts").rglob("*.json")):
        data = json.loads(receipt.read_text())
        files = data["files"]
        if all(name in done for name in files):
            continue
        if any(name in done for name in files):
            raise ValueError(f"Incomplete group archive: {receipt}")
        for name, expected in files.items():
            path = output / name
            if not path.exists() or sha256(path) != expected:
                raise ValueError(f"Missing/changed unarchived prediction: {path}")
        chosen[str(receipt.relative_to(output))] = data
        if len(chosen) == max_groups:
            break
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-groups", type=int, default=50)
    parser.add_argument("--root", type=Path, default=OUT)
    parser.add_argument("--keep-local", action="store_true", help="Verify remote but retain local files")
    args = parser.parse_args()
    if args.max_groups < 1:
        parser.error("max-groups must be positive")
    output = args.root.resolve()
    if not output.is_relative_to(ROOT / "results/limburg_chapter_sized_v1"):
        raise ValueError("Archive root must be within the Limburg chapter result tree")
    groups = choose_groups(output, args.max_groups)
    if not groups:
        print(json.dumps({"groups": 0, "status": "nothing_to_offload"}))
        return
    members = {name: digest for data in groups.values() for name, digest in data["files"].items()}
    receipt_hashes = {name: sha256(output / name) for name in groups}
    bundle_members = {**members, **receipt_hashes}
    bytes_total = sum((output / name).stat().st_size for name in bundle_members)
    if shutil.disk_usage(ROOT).free < 50 * 1024**3 + 2 * bytes_total + 1024**3:
        raise RuntimeError("Archive and readback would breach 50 GiB reserve")
    temp_dir = output / "archive_work"
    temp_dir.mkdir(parents=True, exist_ok=True)
    bundle = temp_dir / f"pending-{int(time.time())}.tar"
    readback = bundle.with_suffix(".readback.tar")
    try:
        with tarfile.open(bundle, "w") as tar:
            for name in sorted(bundle_members):
                tar.add(output / name, arcname=name, recursive=False)
        digest = sha256(bundle)
        blob = f"{PREFIX}/{digest}.tar"
        if not blob_exists(blob):
            run_az("upload", "--name", blob, "--file", str(bundle), "--overwrite", "false")
        run_az("download", "--name", blob, "--file", str(readback))
        if readback.stat().st_size != bundle.stat().st_size or sha256(readback) != digest:
            raise ValueError("Azure readback differs from local prediction archive")
        with tarfile.open(readback) as tar:
            names = {entry.name for entry in tar if entry.isfile()}
        if names != set(bundle_members):
            raise ValueError("Azure readback member census differs")
        ledger = output / "archives" / f"{digest}.json"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        record = {"status": "remote_readback_verified", "account": ACCOUNT,
                  "container": CONTAINER, "blob": blob, "sha256": digest,
                  "archive_bytes": bundle.stat().st_size, "members": members,
                  "receipt_sha256": receipt_hashes,
                  "receipt_groups": list(groups), "verified_unix": time.time(),
                  "local_deleted": not args.keep_local}
        partial = ledger.with_suffix(".partial")
        partial.write_text(json.dumps(record, indent=2) + "\n")
        partial.replace(ledger)
        if not args.keep_local:
            for name in members:
                (output / name).unlink()
        print(json.dumps({"status": "remote_readback_verified", "groups": len(groups),
                          "files": len(members), "bytes": bundle.stat().st_size,
                          "blob": blob, "local_deleted": not args.keep_local}))
    finally:
        bundle.unlink(missing_ok=True)
        readback.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
