"""Retire inactive expansion copies only after verified remote-byte reconciliation.

Run with Azure CLI's Python. No uploads of scientific source data are needed
when the existing immutable remote pair is verified. An additive remote intent
ledger is read back before unlinking each batch; receipts stay local.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/limburg_eo_expansion"
OUT = ROOT / "results/applied_study_v1/offload"
PREFIX = "expansion-v1"
PRODUCTS = {
    "landsat5_sr",
    "landsat7_sr",
    "landsat8_sr",
    "landsat9_sr",
    "s1_descending_37",
    "s1_descending_139",
    "s1_descending_141",
    "s1_descending_39",
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    temp = path.with_suffix(".partial")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def candidate(job, base=None):
    base = BASE if base is None else base
    p = Path(job["relative_path"])
    if p.is_absolute() or ".." in p.parts or len(p.parts) != 4 or p.parts[0] != "images":
        raise ValueError("Unsafe source path")
    if job["product"] not in PRODUCTS or p.parts[2] != job["product"]:
        raise ValueError("Product not in inactive allowlist")
    path = base / p
    if path.is_symlink() or path.resolve() != base.resolve() / p:
        raise ValueError("Symlink source not eligible")
    return path


def verified_pair(job, receipt, size, digest, data, remote_receipt):
    for field in ("relative_path", "bands", "bounds", "window", "asset_ids"):
        if receipt[field] != job[field]:
            raise ValueError("Source receipt/job mismatch: " + field)
    if receipt["sha256"] != digest or data["size"] != size:
        raise ValueError("Local data hash/size mismatch")
    if data["metadata"].get("sha256") != digest:
        raise ValueError("Remote data hash mismatch")
    if data["metadata"].get("verified") != "sha256-readback":
        raise ValueError("Remote bytes lack trusted SHA256 readback evidence")
    if remote_receipt["metadata"].get("data_sha256") != digest:
        raise ValueError("Remote receipt/data linkage mismatch")


def check_queue():
    p = json.loads(
        (ROOT / "results/limburg_individual_experiments_v1/queue/progress.json").read_text()
    )
    for name, digest in p["source_hashes"].items():
        if sha(ROOT / name) != digest:
            raise ValueError("Active source changed: " + name)
    # These are the only currently authorized active primary extractors.
    for name, state in p["tasks"].items():
        if state["status"] == "running" and name.startswith("extract_"):
            if name not in {"extract_presto", "extract_galileo"}:
                raise ValueError("New extraction requires dependency recheck: " + name)
    processes = subprocess.check_output(["ps", "-axo", "command="], text=True)
    for line in processes.splitlines():
        if "python" in line and any(
            x in line
            for x in ["126_stage_eo_expansion.py", "130_run_eo_expansion", "131_run_eo_expansion"]
        ):
            raise ValueError("Expansion staging/processing is active")


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--target-gib", type=float, default=55)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    jobs_file = BASE / "jobs.json"
    jobs_hash = sha(jobs_file)
    jobs = [j for j in json.loads(jobs_file.read_text()) if j["product"] in PRODUCTS]
    check_queue()
    progress = dict(
        status="inventory",
        planned_candidates=len(jobs),
        checked=0,
        removed_files=0,
        removed_logical_bytes=0,
        skipped_shared=0,
        free_before_gib=shutil.disk_usage(ROOT).free / 1024**3,
        jobs_sha256=jobs_hash,
        script_sha256=sha(__file__),
        products=sorted(PRODUCTS),
        failures=[],
    )
    if not args.run:
        print(json.dumps(progress, indent=2))
        return
    from azure.core.credentials import AccessToken
    from azure.storage.blob import BlobServiceClient

    class CliCredential:
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
        "https://stkerkradeprod01bg.blob.core.windows.net", credential=CliCredential()
    ).get_container_client("limburg-compact-eo")
    progress["status"] = "listing_remote_metadata"
    atomic(OUT / "progress.json", progress)
    required = set()
    for j in jobs:
        name = PREFIX + "/" + j["relative_path"]
        required.update([name, str(Path(name).with_suffix(".receipt.json"))])
    index = {}
    for item in container.list_blobs(name_starts_with=PREFIX + "/images/", include=["metadata"]):
        if item.name in required:
            index[item.name] = {
                "size": item.size,
                "metadata": dict(item.metadata or {}),
                "etag": item.etag,
            }
    progress["remote_objects_found"] = len(index)
    progress["status"] = "verifying"
    ledger = (OUT / "removed.jsonl").open("a", buffering=1)
    batch = []
    batch_number = 0
    run_id = str(time.time_ns())
    restored = False

    def remove_batch():
        nonlocal batch_number
        if not batch:
            return
        check_queue()
        if sha(jobs_file) != jobs_hash:
            raise ValueError("Source jobs changed")
        batch_number += 1
        content = ("\n".join(json.dumps(r, sort_keys=True) for r in batch) + "\n").encode()
        name = f"offload/{PREFIX}/{run_id}/intent-{batch_number:05d}.jsonl"
        blob = container.get_blob_client(name)
        blob.upload_blob(
            content, overwrite=False, metadata={"sha256": hashlib.sha256(content).hexdigest()}
        )
        if (
            hashlib.sha256(blob.download_blob().readall()).digest()
            != hashlib.sha256(content).digest()
        ):
            raise ValueError("Remote recovery ledger readback failed")
        for row in batch:
            path = ROOT / row["path"]
            before = path.lstat()
            if path.is_symlink() or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise ValueError("Source changed/link discovered before removal")
            if [before.st_size, before.st_mtime_ns, before.st_ino] != row["stat"]:
                raise ValueError("Source mutated before removal")
            row["intent_blob"] = name
            ledger.write(json.dumps(row) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())
            path.unlink()
            progress["removed_files"] += 1
            progress["removed_logical_bytes"] += row["bytes"]
        batch.clear()
        progress.update(
            free_now_gib=shutil.disk_usage(ROOT).free / 1024**3, updated_unix=time.time()
        )
        atomic(OUT / "progress.json", progress)
        print(
            json.dumps(
                {
                    k: progress[k]
                    for k in [
                        "status",
                        "checked",
                        "removed_files",
                        "removed_logical_bytes",
                        "free_now_gib",
                    ]
                }
            ),
            flush=True,
        )

    try:
        for job in jobs:
            path = candidate(job)
            if not path.exists():
                continue
            before = path.stat()
            if before.st_nlink != 1:
                progress["skipped_shared"] += 1
                continue
            name = PREFIX + "/" + job["relative_path"]
            receipt_name = str(Path(name).with_suffix(".receipt.json"))
            receipt_path = path.with_suffix(".receipt.json")
            receipt = json.loads(receipt_path.read_text())
            digest = sha(path)
            verified_pair(job, receipt, before.st_size, digest, index[name], index[receipt_name])
            local_receipt_sha = sha(receipt_path)
            remote_receipt_sha = index[receipt_name]["metadata"]["sha256"]
            if local_receipt_sha != remote_receipt_sha:
                # Seeded and cloud-generated receipts may retain different
                # telemetry. Preserve both and check their scientific contract.
                raw = container.download_blob(receipt_name).readall()
                if hashlib.sha256(raw).hexdigest() != remote_receipt_sha:
                    raise ValueError("Remote receipt readback hash failed")
                verified_pair(
                    job, json.loads(raw), before.st_size, digest, index[name], index[receipt_name]
                )
            if not restored:
                restored_path = OUT / "restore-test.tif"
                try:
                    with restored_path.open("wb") as stream:
                        container.download_blob(name, max_concurrency=1).readinto(stream)
                    if sha(restored_path) != digest:
                        raise ValueError("Independent restore test failed")
                    atomic(
                        OUT / "restore-test.json",
                        dict(blob=name, sha256=digest, bytes=before.st_size, status="verified"),
                    )
                    restored = True
                finally:
                    restored_path.unlink(missing_ok=True)
            batch.append(
                dict(
                    path=str(path.relative_to(ROOT)),
                    blob=name,
                    bytes=before.st_size,
                    sha256=digest,
                    receipt=str(receipt_path.relative_to(ROOT)),
                    local_receipt=receipt,
                    local_receipt_sha256=local_receipt_sha,
                    remote_receipt_sha256=remote_receipt_sha,
                    etag=index[name]["etag"],
                    stat=[before.st_size, before.st_mtime_ns, before.st_ino],
                )
            )
            progress["checked"] += 1
            if len(batch) >= 200:
                remove_batch()
            if (
                progress["removed_logical_bytes"] + sum(r["bytes"] for r in batch)
                >= args.target_gib * 1024**3
            ):
                break
        remove_batch()
        progress["status"] = "completed"
    except Exception as exc:
        progress.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        progress.update(
            free_now_gib=shutil.disk_usage(ROOT).free / 1024**3, updated_unix=time.time()
        )
        atomic(OUT / "progress.json", progress)
        ledger.close()


if __name__ == "__main__":
    main()
