"""Restore one or all verified derived-cache bundles, without model reruns.

Azure CLI Python supplies authentication/SDK. Every archive and restored member
is hash-checked. Existing different bytes are never overwritten. --all clears
the cold-cache markers only after every archived file has been restored.
"""

import argparse
import fcntl
import gzip
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.derived_cache_offload import (
    GIB,
    ROOTS,
    atomic,
    cloud,
    ensure_idle,
    reserve,
    safe_path,
    sha,
    verify_tar,
)

OUT = ROOT / "results/disk-cleanup-2026-11-18-derived"


def restore_bundle(root, out, container, entry):
    receipt = json.loads(container.get_blob_client(entry["receipt_blob"]).download_blob().readall())
    if receipt["sha256"] != entry["sha256"] or receipt["blob"] != entry["blob"]:
        raise ValueError("Remote mapping and completion catalogue differ")
    records = receipt["records"]
    if receipt["status"] != "remote_bytes_and_members_verified" or receipt["kind"] != "tar":
        raise ValueError("Unsupported or unverified recovery format")
    needed = []
    for row in records:
        p = safe_path(root, row["path"])
        if p.exists():
            if sha(p) != row["sha256"]:
                raise FileExistsError("Different local file: " + row["path"])
        else:
            needed.append(row)
    if not needed:
        return len(records)
    reserve(root, entry["bytes"] + sum(r["size"] for r in records) + 256 * 1024**2)
    scratch = out / "restore-bundle-scratch"
    if scratch.exists():
        shutil.rmtree(scratch)  # only this tool's interrupted temporary restore
    scratch.mkdir()
    archive = scratch / "bundle.tar.gz"
    with archive.open("wb") as f:
        container.get_blob_client(entry["blob"]).download_blob(max_concurrency=1).readinto(f)
    if sha(archive) != entry["sha256"]:
        raise ValueError("Downloaded archive checksum differs")
    stage = scratch / "members"
    verify_tar(archive, records, extract=stage)
    for row in records:
        source = stage / row["path"]
        target = safe_path(root, row["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if sha(target) != row["sha256"]:
                raise FileExistsError(target)
        else:
            # Atomic no-overwrite publication on this volume; original mode and
            # mtime were set during verified extraction.
            os.link(source, target)
        source.unlink()
    shutil.rmtree(scratch)
    return len(records)


def main():
    p = argparse.ArgumentParser(__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--bundle")
    args = p.parse_args()
    ensure_idle()
    OUT.mkdir(exist_ok=True)
    with (OUT / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = ROOT / "docs/reviews/derived-cache-offload-2026-11-18.json"
        summary = json.loads(path.read_text())
        if summary["status"] != "completed_verified_recoverable_offload":
            raise ValueError("Completed verified catalogue required")
        container = cloud()
        index = OUT / "inventory.sqlite"
        if not index.exists():
            reserve(ROOT, GIB)
            zipped = OUT / "restore-index.sqlite.gz"
            with zipped.open("wb") as f:
                container.get_blob_client(summary["index"]["blob"]).download_blob().readinto(f)
            if sha(zipped) != summary["index"]["gzip_sha256"]:
                raise ValueError("Recovery index archive differs")
            temp = OUT / "inventory.sqlite.partial"
            with gzip.open(zipped, "rb") as source, temp.open("wb") as dest:
                shutil.copyfileobj(source, dest, length=8 * 1024**2)
            if sha(temp) != summary["index"]["sqlite_sha256"]:
                raise ValueError("Recovered SQLite index differs")
            temp.rename(index)
            zipped.unlink()
        entries = summary["restore_map_receipts"]
        if args.bundle:
            entries = [e for e in entries if e["id"] == args.bundle]
            if not entries:
                raise ValueError("Bundle absent from completion catalogue")
        total = 0
        for i, entry in enumerate(entries):
            total += restore_bundle(ROOT, OUT, container, entry)
            print(
                json.dumps(
                    {
                        "bundles": i + 1,
                        "total_bundles": len(entries),
                        "files_verified_restored": total,
                    }
                ),
                flush=True,
            )
        if args.all:
            if total != summary["retired_files"]:
                raise ValueError("Full restore census differs")
            for base in ROOTS:
                (ROOT / base / "OFFLOADED-DERIVED.json").unlink(missing_ok=True)
            atomic(
                OUT / "full-restore.json",
                {"status": "completed_every_file_verified", "files": total},
            )


if __name__ == "__main__":
    main()
