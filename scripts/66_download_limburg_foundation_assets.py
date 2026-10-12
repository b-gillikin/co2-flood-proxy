"""Download and hash the fixed public assets for the Limburg FM experiment.

Dry-run is the default. Add ``--download`` and select a group. AlphaEarth is
exported separately by script 67 because it requires an authenticated Earth
Engine project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/limburg_foundation_assets.json"
DEST_ROOT = ROOT / "data/raw/foundation_assets"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(path: Path, kind: str) -> None:
    if path.stat().st_size == 0:
        raise ValueError(f"Empty download: {path}")
    if kind == "pdf" and path.read_bytes()[:4] != b"%PDF":
        raise ValueError(f"Not a PDF: {path}")
    if kind == "json":
        json.loads(path.read_text())
    if kind == "safetensors" and path.suffix != ".safetensors":
        raise ValueError(f"Unexpected weights format: {path}")
    if kind == "gzip" and path.read_bytes()[:2] != b"\x1f\x8b":
        raise ValueError(f"Not a gzip archive: {path}")


def download_one(asset: dict, force: bool = False) -> dict:
    target = DEST_ROOT / asset["destination"]
    receipt = target.with_suffix(target.suffix + ".receipt.json")
    if target.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {target}; use --force")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(asset["url"], headers={"User-Agent": "limburg-research/1"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output)
            resolved_url = response.geturl()
        validate(partial, asset["kind"])
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    record = {
        "asset_id": asset["id"],
        "source_url": asset["url"],
        "resolved_url": resolved_url,
        "destination": str(target.relative_to(ROOT)),
        "downloaded_utc": datetime.now(timezone.utc).isoformat(),
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "manifest": str(MANIFEST.relative_to(ROOT)),
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    return record


def selected_assets(manifest: dict, group: str) -> list[dict]:
    if group == "all":
        return manifest["downloads"]
    return [asset for asset in manifest["downloads"] if asset["group"] == group]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=["documents", "model", "code", "all"], default="all")
    parser.add_argument("--download", action="store_true", help="perform downloads; otherwise print plan")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    assets = selected_assets(manifest, args.group)
    for asset in assets:
        target = DEST_ROOT / asset["destination"]
        if not args.download:
            print(f"{asset['group']:9} {asset['id']:32} -> {target}")
        else:
            record = download_one(asset, args.force)
            print(f"downloaded {record['asset_id']}: {record['bytes']} bytes {record['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
