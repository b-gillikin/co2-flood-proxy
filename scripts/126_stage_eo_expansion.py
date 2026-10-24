"""Stage the completed supplemental Azure archive; never modify the active archive.

Run with Azure CLI's Python (azure-storage-blob installed). Azure CLI login is
used without writing tokens. Default is inventory only; --run stages all jobs in
bounded batches, preserving the local archive and recording pending failures.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCH_FIELDS = ("relative_path", "bands", "bounds", "window", "asset_ids")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_receipt(job, receipt):
    relative = Path(job["relative_path"])
    if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "images":
        raise ValueError("Unsafe archive path")
    for field in MATCH_FIELDS:
        if receipt[field] != job[field]:
            raise ValueError(f"Receipt/job mismatch: {field}")
    digest = receipt["sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid SHA-256")


def check_existing(path, expected):
    if not path.exists():
        return False
    if sha256(path) != expected:
        raise ValueError(f"Existing file conflicts; retained for inspection: {path}")
    return True


def tree_bytes(path):
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--batch-gb", type=float, default=5)
    parser.add_argument("--max-local-gb", type=float, default=150)
    parser.add_argument("--reserve-gib", type=float, default=60)
    args = parser.parse_args()
    if min(args.batch_gb, args.max_local_gb, args.reserve_gib) <= 0:
        parser.error("Budgets must be positive")
    base = ROOT / "data/raw/limburg_eo_expansion"
    jobs_path = base / "jobs.json"
    jobs = json.loads(jobs_path.read_text())
    if not args.run:
        print(
            json.dumps(
                {
                    "planned_files": len(jobs),
                    "mode": "inventory",
                    "batch_gb": args.batch_gb,
                    "max_local_gb": args.max_local_gb,
                }
            )
        )
        return
    from azure.core.credentials import AccessToken
    from azure.storage.blob import BlobServiceClient

    class CliCredential:
        def get_token(self, *scopes, **kwargs):
            result = json.loads(
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
            return AccessToken(result["accessToken"], int(result["expires_on"]))

    lock = (base / ".staging.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    client = BlobServiceClient(
        "https://stkerkradeprod01bg.blob.core.windows.net", credential=CliCredential()
    )
    container = client.get_container_client("limburg-compact-eo")
    progress = json.loads(container.download_blob("expansion-v1/progress.json").readall())
    if progress["status"] != "completed" or progress["committed_files"] != len(jobs):
        raise ValueError("Remote completion does not match local ledger")
    index = {
        b.name: b
        for b in container.list_blobs(name_starts_with="expansion-v1/images/", include=["metadata"])
    }
    used = tree_bytes(base) + tree_bytes(ROOT / "data/raw/limburg_dynamic_model_weights")
    state = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "jobs_sha256": sha256(jobs_path),
        "remote_completion": progress,
        "planned_files": len(jobs),
        "verified_files": 0,
        "downloaded_files": 0,
        "failures": [],
        "batch_gb": args.batch_gb,
        "max_local_gb": args.max_local_gb,
        "reserve_gib": args.reserve_gib,
    }
    status_path = base / "staging-progress.json"

    def save():
        state["updated_utc"] = datetime.now(timezone.utc).isoformat()
        tmp = status_path.with_suffix(".json.partial")
        tmp.write_text(json.dumps(state, indent=2) + "\n")
        tmp.replace(status_path)
        print(
            json.dumps(
                {
                    k: state[k]
                    for k in ("status", "verified_files", "downloaded_files", "updated_utc")
                }
            ),
            flush=True,
        )

    def transfer(job):
        name = "expansion-v1/" + job["relative_path"]
        receipt_name = str(Path(name).with_suffix(".receipt.json"))
        item, receipt_item = index[name], index[receipt_name]
        expected = item.metadata["sha256"]
        if (
            item.metadata.get("verified") != "sha256-readback"
            or receipt_item.metadata["data_sha256"] != expected
        ):
            raise ValueError("Unverified remote pair")
        path = base / job["relative_path"]
        receipt_path = path.with_suffix(".receipt.json")
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
        else:
            raw = container.download_blob(receipt_name).readall()
            if hashlib.sha256(raw).hexdigest() != receipt_item.metadata["sha256"]:
                raise ValueError("Remote receipt checksum mismatch")
            receipt = json.loads(raw)
        validate_receipt(job, receipt)
        if receipt["sha256"] != expected:
            raise ValueError("Remote data/receipt checksum mismatch")
        downloaded = False
        if not check_existing(path, expected):
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix(".tif.partial")
            try:
                with partial.open("wb") as stream:
                    container.download_blob(name, max_concurrency=1).readinto(stream)
                if partial.stat().st_size != item.size or sha256(partial) != expected:
                    raise ValueError("Downloaded data checksum/size mismatch")
                partial.replace(path)
                downloaded = True
            finally:
                partial.unlink(missing_ok=True)
        if not receipt_path.exists():
            tmp = receipt_path.with_suffix(".json.partial")
            tmp.write_text(json.dumps(receipt, indent=2) + "\n")
            tmp.replace(receipt_path)
        return downloaded

    pending = list(jobs)
    save()
    while pending:
        batch, reserved = [], 0
        while pending:
            job = pending[0]
            name = "expansion-v1/" + job["relative_path"]
            # Reserve full data+receipt even for existing files; conservative bound.
            amount = index[name].size + index[str(Path(name).with_suffix(".receipt.json"))].size
            if batch and reserved + amount > args.batch_gb * 1e9:
                break
            if (
                used + reserved + amount > args.max_local_gb * 1e9
                or shutil.disk_usage(base).free - reserved - amount < args.reserve_gib * 2**30
            ):
                state["status"] = "paused_storage_budget"
                save()
                return
            batch.append(pending.pop(0))
            reserved += amount
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [(job, pool.submit(transfer, job)) for job in batch]
            for job, future in futures:
                try:
                    state["downloaded_files"] += int(future.result())
                    state["verified_files"] += 1
                except Exception as exc:
                    state["failures"].append({"path": job["relative_path"], "error": str(exc)})
                if (state["verified_files"] + len(state["failures"])) % 100 == 0:
                    save()
        used = tree_bytes(base) + tree_bytes(ROOT / "data/raw/limburg_dynamic_model_weights")
        state["local_archive_and_weights_bytes"] = used
        save()
    state["status"] = "completed" if not state["failures"] else "completed_with_failures"
    save()


if __name__ == "__main__":
    main()
