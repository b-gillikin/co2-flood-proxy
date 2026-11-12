#!/usr/bin/env python3
"""Verify or recover pinned response-mapping literature and public references.

The small curated manifest is the scope. SAR cutouts have a separate EE runner
(259). This command does not fit models or overwrite changed local files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/limburg_response_mapping_resources_v1.json"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def recover(asset, download):
    path = ROOT / asset["path"]
    if not path.resolve().is_relative_to(ROOT / "data/raw"):
        raise ValueError("Resource must remain inside chapter raw data")
    if path.exists():
        if path.stat().st_size != asset["bytes"] or digest(path) != asset["sha256"]:
            raise ValueError(f"Changed local resource; preserved: {asset['path']}")
        return {"path": asset["path"], "status": "verified"}
    if not download:
        raise FileNotFoundError(asset["path"])
    if shutil.disk_usage(ROOT).free < 52 * 1024**3:
        raise RuntimeError("52 GiB acquisition reserve reached")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    try:
        with requests.get(asset["url"], timeout=120, stream=True) as response:
            response.raise_for_status()
            total = 0
            with partial.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    total += len(chunk)
                    if total > asset["bytes"]:
                        raise ValueError("Remote resource changed size")
                    stream.write(chunk)
        if partial.stat().st_size != asset["bytes"] or digest(partial) != asset["sha256"]:
            raise ValueError("Remote resource changed; do not silently replace pinned evidence")
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)
    return {"path": asset["path"], "status": "recovered_verified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Recover missing pinned files")
    args = parser.parse_args()
    assets = json.loads(MANIFEST.read_text())["assets"]

    def one(asset):
        try:
            return recover(asset, args.download)
        except Exception as error:
            return {"path": asset["path"], "status": "unresolved", "error": str(error)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(one, assets))
    failed = [r for r in results if r["status"] == "unresolved"]
    print(
        json.dumps(
            {"total": len(results), "verified": len(results) - len(failed), "unresolved": failed},
            indent=2,
        )
    )
    return bool(failed)


if __name__ == "__main__":
    raise SystemExit(main())
