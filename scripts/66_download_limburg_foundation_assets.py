"""Download and hash the fixed public assets for the Limburg FM experiment.

Dry-run is the default. Add ``--download`` and select a group. AlphaEarth is
exported separately by script 67 because it requires an authenticated Earth
Engine project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
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


def existing_receipt(target: Path) -> dict | None:
    receipt = target.with_suffix(target.suffix + ".receipt.json")
    if not target.exists() or not receipt.exists():
        return None
    record = json.loads(receipt.read_text())
    if record.get("sha256") != sha256(target) or record.get("bytes") != target.stat().st_size:
        return None
    return record | {"status": "verified-existing"}


def download_one(asset: dict, force: bool = False) -> dict:
    target = DEST_ROOT / asset["destination"]
    receipt = target.with_suffix(target.suffix + ".receipt.json")
    if not force and (record := existing_receipt(target)):
        return record
    if target.exists() and not force:
        raise FileExistsError(
            f"Existing file has no valid receipt: {target}; inspect it, then use --force"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    if force:
        partial.unlink(missing_ok=True)
    resolved_url = asset["url"]
    if "hf_repo_id" in asset:
        try:
            from huggingface_hub import hf_hub_download
        except ImportError:
            pass
        else:
            downloaded = Path(
                hf_hub_download(
                    repo_id=asset["hf_repo_id"],
                    filename=asset["hf_filename"],
                    revision=asset["hf_revision"],
                    local_dir=target.parent,
                    force_download=force,
                )
            )
            if downloaded.resolve() != target.resolve():
                raise RuntimeError(f"Hugging Face returned unexpected path: {downloaded}")
            validate(target, asset["kind"])
            resolved_url = (
                f"hf://{asset['hf_repo_id']}@{asset['hf_revision']}/{asset['hf_filename']}"
            )
            return write_receipt(asset, target, receipt, resolved_url)
    # curl uses the macOS system certificate store and is more reliable than
    # CommandLineTools Python's urllib for Hugging Face's signed redirects.
    # Keep .part on failure so another run can resume it.
    command = [
        "curl",
        "--fail",
        "--location",
        "--retry",
        "5",
        "--connect-timeout",
        "30",
        "--max-time",
        "900",
        "--continue-at",
        "-",
        "--user-agent",
        "limburg-research/1",
        "--output",
        str(partial),
        "--silent",
        "--show-error",
        "--write-out",
        "%{url_effective}",
        asset["url"],
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or f"curl exited {error.returncode}"
        raise RuntimeError(
            f"Download failed for {asset['id']}; partial data, if any, remains at "
            f"{partial} for the next run. {detail}"
        ) from None
    resolved_url = result.stdout
    validate(partial, asset["kind"])
    partial.replace(target)
    return write_receipt(asset, target, receipt, resolved_url)


def write_receipt(asset: dict, target: Path, receipt: Path, resolved_url: str) -> dict:
    record = {
        "asset_id": asset["id"],
        "source_url": asset["url"],
        "resolved_url": resolved_url,
        "destination": str(target.relative_to(ROOT)),
        "downloaded_utc": datetime.now(timezone.utc).isoformat(),
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "status": "downloaded",
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
    parser.add_argument("--asset", help="download one manifest asset by ID")
    parser.add_argument("--download", action="store_true", help="perform downloads; otherwise print plan")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--fail-fast", action="store_true", help="stop after the first failed asset")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    assets = selected_assets(manifest, args.group)
    if args.asset:
        assets = [asset for asset in manifest["downloads"] if asset["id"] == args.asset]
        if not assets:
            parser.error(f"unknown asset ID: {args.asset}")
    failures = []
    for asset in assets:
        target = DEST_ROOT / asset["destination"]
        if not args.download:
            print(f"{asset['group']:9} {asset['id']:32} -> {target}")
        else:
            try:
                record = download_one(asset, args.force)
                print(
                    f"{record['status']} {record['asset_id']}: "
                    f"{record['bytes']} bytes {record['sha256']}"
                )
            except Exception as error:
                failures.append((asset["id"], str(error)))
                print(f"FAILED {asset['id']}: {error}", file=sys.stderr)
                if args.fail_fast:
                    break
    if failures:
        print("\nFailed assets:", file=sys.stderr)
        for asset_id, error in failures:
            print(f"- {asset_id}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
