"""Additive, content-addressed result bundles with full remote SHA256 readback.

Supply explicit completed directories/files. No VM provision, overwrite, or
local deletion. CLI Python supplies Azure SDK; other dependencies are stdlib.
"""

import argparse
import fcntl
import hashlib
import io
import json
import subprocess
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(8 * 1024**2), b""):
        h.update(block)
    return h.hexdigest()


def inventory(paths):
    files = set()
    for item in paths:
        p = (ROOT / item).resolve()
        if not p.is_relative_to(ROOT) or not p.exists():
            raise ValueError("Only existing chapter files may be bundled")
        files.update([p] if p.is_file() else (x for x in p.rglob("*") if x.is_file()))
    records = {}
    for p in sorted(files):
        if not p.resolve().is_relative_to(ROOT):
            raise ValueError("Escaping symlink")
        with p.open("rb") as stream:
            records[str(p.relative_to(ROOT))] = dict(bytes=p.stat().st_size, sha256=digest(stream))
    if not records:
        raise ValueError("Empty bundle")
    return records


def verify_bundle(path, expected):
    with tarfile.open(path, "r:gz") as archive:
        files = {m.name: m for m in archive.getmembers()}
        if len(files) != len(archive.getmembers()) or set(files) != set(expected) | {
            "BUNDLE-INVENTORY.json"
        }:
            raise ValueError("Archive member census differs")
        for name, r in expected.items():
            member = files[name]
            if not member.isfile() or member.size != r["bytes"]:
                raise ValueError("Invalid archive member")
            with archive.extractfile(member) as stream:
                if digest(stream) != r["sha256"]:
                    raise ValueError("Archive member hash differs")
        with archive.extractfile("BUNDLE-INVENTORY.json") as stream:
            if json.load(stream) != expected:
                raise ValueError("Embedded inventory differs")


def main():
    from azure.core.credentials import AccessToken
    from azure.storage.blob import BlobServiceClient

    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--include", action="append", required=True)
    p.add_argument(
        "--output", type=Path, required=True, help="New bundle path outside included trees"
    )
    a = p.parse_args()
    # Concurrent fit lanes share one compressor/upload/readback worker.
    lock_path = ROOT / "results/applied_study_v3/.archive-owner.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    archive_lock = lock_path.open("a")
    fcntl.flock(archive_lock, fcntl.LOCK_EX)
    if a.output.exists() or a.output.with_suffix(".recovery.json").exists():
        raise FileExistsError("Preserve previous recovery bundle")
    records = inventory(a.include)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(a.output, "w:gz") as archive:
        for name in records:
            archive.add(ROOT / name, arcname=name, recursive=False)
        content = json.dumps(records, sort_keys=True).encode()
        member = tarfile.TarInfo("BUNDLE-INVENTORY.json")
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))
    verify_bundle(a.output, records)
    with a.output.open("rb") as stream:
        sha = digest(stream)

    class Credential:
        def get_token(self, *scopes, **kwargs):
            if not hasattr(self, "token") or self.token.expires_on < time.time() + 120:
                r = json.loads(
                    subprocess.check_output(
                        [
                            "az",
                            "account",
                            "get-access-token",
                            "--resource",
                            "https://storage.azure.com/",
                            "-o",
                            "json",
                        ]
                    )
                )
                self.token = AccessToken(r["accessToken"], int(r["expires_on"]))
            return self.token

    container = BlobServiceClient(
        "https://stkerkradeprod01bg.blob.core.windows.net", credential=Credential()
    ).get_container_client("limburg-compact-eo")
    name = f"applied-v2/results/{sha}.tar.gz"
    blob = container.get_blob_client(name)
    if not blob.exists():
        with a.output.open("rb") as stream:
            blob.upload_blob(stream, overwrite=False, max_concurrency=1, metadata={"sha256": sha})
    h = hashlib.sha256()
    readback = a.output.with_suffix(".readback.tar.gz")
    if readback.exists():
        raise FileExistsError("Previous readback exists")
    with readback.open("xb") as stream:
        for block in blob.download_blob(max_concurrency=1).chunks():
            stream.write(block)
            h.update(block)
    if h.hexdigest() != sha:
        raise ValueError("Remote readback hash mismatch")
    verify_bundle(readback, records)
    receipt = dict(
        status="remote_readback_and_every_member_verified",
        blob=name,
        account="stkerkradeprod01bg",
        container="limburg-compact-eo",
        sha256=sha,
        archive_bytes=a.output.stat().st_size,
        files=len(records),
        inventory=records,
        local_bundle=str(a.output),
        restored_readback=str(readback),
        note="All members restored to a downloaded archive and independently hashed; no local/remote deletion. Inference-state recovery, not optimizer/epoch resume.",
    )
    a.output.with_suffix(".recovery.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "inventory"}))


if __name__ == "__main__":
    main()
