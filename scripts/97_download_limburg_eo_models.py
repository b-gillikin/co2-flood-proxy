"""Acquire only the pinned EO screening checkpoints and their source code.

No model is executed, trained or ranked. Files remain outside Git. Every asset
is checked against publisher byte counts and hashes before publication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/limburg_eo_model_assets.json"


def hashes(path):
    size = path.stat().st_size
    digests = {name: hashlib.new(name) for name in ("sha256", "md5", "sha1")}
    digests["sha1"].update(f"blob {size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            for digest in digests.values():
                digest.update(chunk)
    return {name: digest.hexdigest() for name, digest in digests.items()}


def verify(path, asset):
    if path.stat().st_size != asset["bytes"]:
        raise ValueError(f"Byte count differs: {path.name}")
    actual = hashes(path)
    for key, algorithm in (("sha256", "sha256"), ("md5", "md5"), ("git_blob_sha1", "sha1")):
        if key in asset and actual[algorithm] != asset[key]:
            raise ValueError(f"Publisher {key} differs: {path.name}")
    return actual["sha256"]


def acquire_file(destination, asset):
    target = destination / asset["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        partial = target.with_suffix(target.suffix + ".part")
        result = (
            None
            if asset.get("transport") == "requests"
            else subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--location",
                    "--retry",
                    "4",
                    "--retry-delay",
                    "2",
                    "--connect-timeout",
                    "30",
                    "--max-time",
                    "1800",
                    "--continue-at",
                    "-",
                    "--max-filesize",
                    str(max(asset["bytes"], 1024 * 1024)),
                    "--silent",
                    "--show-error",
                    "--output",
                    str(partial),
                    asset["url"],
                ],
                check=False,
            )
        )
        if result is None or result.returncode:
            # macOS curl uses LibreSSL; some publisher endpoints require the
            # OpenSSL-backed Python runtime. Preserve resumable partial bytes.
            import requests

            offset = partial.stat().st_size if partial.exists() else 0
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            with requests.get(
                asset["url"], headers=headers, stream=True, timeout=(30, 120)
            ) as response:
                response.raise_for_status()
                append = offset > 0 and response.status_code == 206
                if append and not response.headers.get("Content-Range", "").startswith(
                    f"bytes {offset}-"
                ):
                    raise ValueError("Publisher resumed at the wrong byte offset")
                written = offset if append else 0
                with partial.open("ab" if append else "wb") as output:
                    for chunk in response.iter_content(1024 * 1024):
                        written += len(chunk)
                        if written > asset["bytes"]:
                            raise ValueError("Response exceeds publisher byte count")
                        output.write(chunk)
        checksum = verify(partial, asset)
        partial.replace(target)
    else:
        checksum = verify(target, asset)
    receipt = asset | {
        "sha256": checksum,
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "destination": str(target.relative_to(ROOT)),
    }
    target.with_suffix(target.suffix + ".receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    return receipt


def acquire_source(source, destination):
    if not destination.exists():
        destination.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(destination)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(destination),
                "remote",
                "add",
                "origin",
                "https://github.com/" + source["repository"] + ".git",
            ],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(destination),
                "fetch",
                "--quiet",
                "--depth",
                "1",
                "origin",
                source["revision"],
            ],
            check=True,
            env=os.environ | {"GIT_LFS_SKIP_SMUDGE": "1"},
        )
        subprocess.run(
            ["git", "-C", str(destination), "checkout", "--quiet", "--detach", "FETCH_HEAD"],
            check=True,
            env=os.environ | {"GIT_LFS_SKIP_SMUDGE": "1"},
        )
    revision = subprocess.check_output(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if revision != source["revision"]:
        raise ValueError(f"Source revision differs: {destination.name}")


def acquire_model(model, destination):
    source = model.get("source")
    if source:
        acquire_source(source, destination / "code" / model["id"])
    records = [
        acquire_file(destination / "models" / model["id"], asset) for asset in model["assets"]
    ]
    return {
        "model": model["id"],
        "status": "downloaded_verified",
        "files": records,
        "inference_status": model.get("inference_status", "not_tested"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--model")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    models = [m for m in manifest["models"] if not args.model or m["id"] == args.model]
    if not models:
        parser.error("Unknown model")
    if not args.download:
        for model in models:
            print(model["id"], model["checkpoint"], sum(a["bytes"] for a in model["assets"]))
        return 0
    destination = ROOT / manifest["destination"]
    for source in manifest.get("support_sources", []):
        acquire_source(source, ROOT / source["path"])
    for case in manifest["unresolved"]:
        if case.get("source") and not case.get("status", "").startswith("excluded"):
            acquire_source(case["source"], destination / "code" / case["id"])
    records = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(acquire_model, m, destination): m["id"] for m in models}
        for future in as_completed(futures):
            try:
                record = future.result()
            except Exception as error:
                record = {"model": futures[future], "status": "failed", "error": str(error)}
            records.append(record)
            print(record["model"], record["status"], record.get("error", ""), flush=True)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "acquisition-status.json").write_text(
        json.dumps(
            {
                "updated_utc": datetime.now(timezone.utc).isoformat(),
                "models": records,
                "unresolved": manifest["unresolved"],
            },
            indent=2,
        )
        + "\n"
    )
    return int(any(r["status"] == "failed" for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
