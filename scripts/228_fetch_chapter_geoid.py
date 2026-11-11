#!/usr/bin/env python3
"""Fetch only the pinned chapter GEOID heldout shards with resume and SHA-256.

No extraction, scientific selection or modification of other chapter data.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/limburg_chapter_sized_geoid_acquisition_v1.json"
OUTPUT = ROOT / "data/raw/limburg_chapter_geoid_heldout_v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(item: dict, root: Path, reserve_gib: int) -> dict:
    target = root / item["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt = target.with_suffix(target.suffix + ".receipt.json")
    if target.exists() and target.stat().st_size == item["bytes"] and sha256(target) == item["sha256"]:
        status = "reused_verified"
    else:
        partial = target.with_suffix(target.suffix + ".partial")
        needed = max(item["bytes"] - (partial.stat().st_size if partial.exists() else 0), 0)
        if shutil.disk_usage(root).free < needed + reserve_gib * 1024**3:
            raise RuntimeError(f"Disk reserve would be breached while fetching {item['path']}")
        subprocess.run(
            ["curl", "--fail", "--location", "--retry", "5", "--retry-all-errors",
             "--retry-delay", "5", "--continue-at", "-", "--output", str(partial), item["url"]],
            check=True,
        )
        if partial.stat().st_size != item["bytes"] or sha256(partial) != item["sha256"]:
            raise ValueError(f"Length or SHA-256 mismatch for {item['path']}; partial retained")
        partial.replace(target)
        status = "downloaded_verified"
    record = {
        "path": item["path"], "bytes": item["bytes"], "sha256": item["sha256"],
        "status": status, "manifest": str(MANIFEST.relative_to(ROOT)),
        "verified_unix": time.time(),
    }
    tmp = receipt.with_suffix(receipt.suffix + ".tmp")
    tmp.write_text(json.dumps(record, indent=2) + "\n")
    tmp.replace(receipt)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--reserve-gib", type=int, default=50)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 3:
        parser.error("Use one to three download workers")
    items = json.loads(MANIFEST.read_text())["shards"]
    args.output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch, item, args.output, args.reserve_gib): item for item in items}
        for future in as_completed(futures):
            result = future.result()
            print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
