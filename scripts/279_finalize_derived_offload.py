"""Close the authorized offload with a verified recovery index and byte audit.

Waits for the existing single offloader; does not retire additional data or
launch compute. Uses Azure CLI's Python. If the offloader fails, leave a clear
incomplete receipt rather than report success.
"""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.derived_cache_offload import (
    GIB,
    ROOTS,
    atomic,
    cloud,
    digest,
    open_inventory,
    publish_json,
    reserve,
    sha,
)

OUT = ROOT / "results/disk-cleanup-2026-11-18-derived"
PREFIX = "chapter1-co2/derived-eo/2026-11-18"


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--wait-pid", type=int, required=True)
    args = parser.parse_args()
    while True:
        try:
            os.kill(args.wait_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(10)
    state = json.loads((OUT / "progress.json").read_text())
    if state["status"] != "completed":
        atomic(OUT / "closure.json", {"status": "incomplete_worker_stopped", "worker": state})
        raise SystemExit("Offloader did not complete; no success receipt created")
    container = cloud()
    db = open_inventory(OUT)
    retained, assigned, logical, allocated = 0, 0, 0, 0
    # Stream the million-row catalogue. No million-file dictionary in memory.
    for row in db.execute("SELECT * FROM files"):
        p = ROOT / row["path"]
        if row["bundle"] is not None:
            if os.path.lexists(p):
                raise ValueError("An assigned source remains local: " + row["path"])
            assigned += 1
            logical += row["size"]
            allocated += row["allocated"]
        else:
            s = p.lstat()
            if (s.st_size, s.st_mtime_ns, s.st_ino, s.st_dev) != (
                row["size"],
                row["mtime_ns"],
                row["ino"],
                row["dev"],
            ):
                raise ValueError("Preserved cache file changed: " + row["path"])
            retained += 1
    if assigned != state["retired_files"]:
        raise ValueError("Retired census and recovery index differ")
    selected_remaining = db.execute(
        "SELECT COUNT(*) FROM files WHERE bundle IS NULL AND "
        "((root=? AND suffix='.npy') OR (root=? AND suffix='.json' "
        "AND path NOT LIKE '%/manifest.json' AND path NOT LIKE '%/status.json' "
        "AND path NOT LIKE '%/index.json'))",
        ROOTS,
    ).fetchone()[0]
    if selected_remaining:
        raise ValueError("Unprocessed authorized cache files remain")
    db.close()
    protection = json.loads((OUT / "protection.json").read_text())
    for path, expected in protection.items():
        if sha(ROOT / path) != expected:
            raise ValueError("Protected current evidence changed: " + path)
    archives, compressed, receipts = 0, 0, []
    for path in sorted((OUT / "bundles").glob("*.json")):
        b = json.loads(path.read_text())
        if b["status"] != "completed":
            raise ValueError("Unfinished bundle")
        r = json.loads(container.get_blob_client(b["receipt_blob"]).download_blob().readall())
        if r != b["verification"]:
            raise ValueError("Durable remote file-mapping receipt differs")
        archives += 1
        compressed += b["archive_bytes"]
        receipts.append(
            {
                "id": b["id"],
                "blob": b["blob"],
                "sha256": b["sha256"],
                "bytes": b["archive_bytes"],
                "receipt_blob": b["receipt_blob"],
            }
        )
    # The exact SQLite mapping is portable and is not covered by ordinary raw
    # data backups. Preserve it remotely, in addition to embedded inventories.
    reserve(ROOT, GIB)
    index = OUT / "inventory.sqlite"
    index_sha = sha(index)
    compressed_index = OUT / "inventory.sqlite.gz"
    with index.open("rb") as source, gzip.open(compressed_index, "wb", compresslevel=1) as target:
        shutil.copyfileobj(source, target, length=8 * 1024**2)
    archive_sha = sha(compressed_index)
    name = PREFIX + "/catalogue/" + archive_sha + ".sqlite.gz"
    blob = container.get_blob_client(name)
    if not blob.exists():
        with compressed_index.open("rb") as source:
            blob.upload_blob(source, overwrite=False, max_concurrency=4)
    readback = OUT / "index-readback.sqlite.gz"
    h = hashlib.sha256()
    with readback.open("wb") as target:
        for block in blob.download_blob(max_concurrency=1).chunks():
            h.update(block)
            target.write(block)
    if h.hexdigest() != archive_sha:
        raise ValueError("Remote compressed recovery index differs")
    with gzip.open(readback, "rb") as restored:
        if digest(restored) != index_sha:
            raise ValueError("Restored SQLite mapping differs")
    summary = {
        "status": "completed_verified_recoverable_offload",
        "date": "2026-11-18",
        "completed_unix": time.time(),
        "authorization": "Brian approved the first 40–60 GiB offload from inactive Limburg caches.",
        "roots": list(ROOTS),
        "retired_files": assigned,
        "retained_cache_files": retained,
        "retired_logical_gib": logical / GIB,
        "retired_allocated_gib": allocated / GIB,
        "compressed_payload_gib": compressed / GIB,
        "bundles": archives,
        "free_before_gib": state["free_before_gib"],
        "free_after_gib": shutil.disk_usage(ROOT).free / GIB,
        "observed_gain_note": "Includes local recovery-index/scratch overhead and unrelated APFS/disk activity.",
        "remote": {
            "account": "stunumeritphdbackupbg",
            "container": "dissertation-recovery",
            "prefix": PREFIX,
        },
        "index": {"blob": name, "gzip_sha256": archive_sha, "sqlite_sha256": index_sha},
        "protected_current_hashes_reverified": protection,
        "pilot": json.loads((OUT / "pilot-tar.json").read_text()),
        "archive_format": "lossless tar.gz; embedded per-member hashes, mode and original mtime; full remote readback and member verification before retirement",
        "restore": "/opt/homebrew/Cellar/azure-cli/2.83.0/libexec/bin/python scripts/278_offload_historical_derived.py --restore-path EXACT_PROJECT_RELATIVE_FILE",
        "preserved": "Run-level indexes/manifests/status, all compact catchment representations/results, raw observations/weather/landscape sources and model weights remain local.",
        "other_chapters_untouched": True,
        "restore_map_receipts": receipts,
    }
    summary_blob = publish_json(container, PREFIX + "/catalogue/completion", summary)
    summary["remote_summary_blob"] = summary_blob
    atomic(OUT / "closure.json", summary)
    atomic(ROOT / "docs/reviews/derived-cache-offload-2026-11-18.json", summary)
    for root in ROOTS:
        marker = ROOT / root / "OFFLOADED-DERIVED.json"
        data = json.loads(marker.read_text())
        data.update(
            status="completed_recoverable_offload",
            index_blob=name,
            closure="docs/reviews/derived-cache-offload-2026-11-18.json",
        )
        atomic(marker, data)
    # These are our verified temporary transport copies, not research data.
    readback.unlink()
    compressed_index.unlink()
    print(
        json.dumps(
            {
                k: summary[k]
                for k in [
                    "status",
                    "retired_files",
                    "retired_logical_gib",
                    "compressed_payload_gib",
                    "free_after_gib",
                ]
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
