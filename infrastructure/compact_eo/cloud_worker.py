"""Resume the pinned compact EO manifest into private Azure Blob Storage.

Seed mode uploads only hash-checked local EO files. Worker mode reads uploads
back and verifies SHA-256 before committing receipts or deleting its VM cache.
No Earth Engine credentials are uploaded to Blob Storage or logged.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class BlobArchive:
    def __init__(self, container, prefix="v1", max_bytes=70_000_000_000):
        self.container = container
        self.prefix = prefix.rstrip("/")
        self.max_bytes = max_bytes
        self.lock = threading.Lock()
        self.index = {
            b.name: {"bytes": b.size, "metadata": b.metadata or {}}
            for b in container.list_blobs(name_starts_with=self.prefix + "/", include=["metadata"])
        }
        self.used = sum(b["bytes"] for b in self.index.values())
        self.reserved = 0

    def name(self, relative):
        return self.prefix + "/" + relative

    def ready(self, relative):
        data = self.index.get(self.name(relative))
        receipt = self.index.get(self.name(str(Path(relative).with_suffix(".receipt.json"))))
        return bool(
            data
            and receipt
            and data["metadata"].get("verified") == "sha256-readback"
            and data["metadata"].get("sha256") == receipt["metadata"].get("data_sha256")
        )

    def put_file(self, path, relative, metadata):
        name = self.name(relative)
        checksum = sha256(path)
        size = path.stat().st_size
        with self.lock:
            previous = self.index.get(name)
            if previous:
                if previous["bytes"] != size or previous["metadata"].get("sha256") != checksum:
                    raise ValueError(f"Existing blob hash differs: {relative}")
                return
            if self.used + self.reserved + size > self.max_bytes:
                raise RuntimeError("Blob archive storage budget reached")
            self.reserved += size
        try:
            blob = self.container.get_blob_client(name)
            with path.open("rb") as stream:
                blob.upload_blob(
                    stream,
                    overwrite=False,
                    metadata=metadata | {"sha256": checksum},
                    validate_content=True,
                    max_concurrency=1,
                )
            properties = blob.get_blob_properties()
            if properties.size != size or properties.metadata.get("sha256") != checksum:
                raise ValueError(f"Upload size/metadata verification failed: {relative}")
            with self.lock:
                self.index[name] = {"bytes": size, "metadata": dict(properties.metadata)}
                self.used += size
        finally:
            with self.lock:
                self.reserved -= size

    def verify_data(self, relative, expected):
        name = self.name(relative)
        entry = self.index[name]
        if entry["metadata"].get("sha256") != expected:
            raise ValueError(f"Expected blob hash differs: {relative}")
        if entry["metadata"].get("verified") == "sha256-readback":
            return
        blob = self.container.get_blob_client(name)
        h = hashlib.sha256()
        for block in blob.download_blob(max_concurrency=1).chunks():
            h.update(block)
        if h.hexdigest() != expected:
            raise ValueError(f"Blob readback SHA-256 failed: {relative}")
        metadata = entry["metadata"] | {"verified": "sha256-readback"}
        blob.set_blob_metadata(metadata)
        with self.lock:
            self.index[name]["metadata"] = metadata

    def publish_pair(self, path, relative, receipt, readback):
        expected = json.loads(receipt.read_text())["sha256"]
        if sha256(path) != expected:
            raise ValueError(f"Local receipt hash failed: {relative}")
        self.put_file(path, relative, {"verified": "transport-md5"})
        if readback:
            self.verify_data(relative, expected)
        self.put_file(
            receipt,
            str(Path(relative).with_suffix(".receipt.json")),
            {"data_sha256": expected, "verified": "transport-md5"},
        )
        if readback and not self.ready(relative):
            raise ValueError(f"Remote commit incomplete: {relative}")

    def json_status(self, relative, value):
        content = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        # Small mutable progress/state objects; scientific data blobs are immutable.
        self.container.get_blob_client(self.name(relative)).upload_blob(content, overwrite=True)


def deallocate(credential):
    import requests

    vm = os.environ["AZURE_VM_RESOURCE_ID"]
    token = credential.get_token("https://management.azure.com/.default").token
    response = requests.post(
        "https://management.azure.com" + vm + "/deallocate?api-version=2024-07-01",
        headers={"Authorization": "Bearer " + token},
        timeout=60,
    )
    response.raise_for_status()
    print("VM deallocation requested", flush=True)


def run(args, archive, credential):
    spec = importlib.util.spec_from_file_location(
        "compact_eo", ROOT / "scripts/96_acquire_limburg_compact_eo.py"
    )
    compact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compact)
    manifest = args.manifest
    jobs = json.loads((manifest / "jobs.json").read_text())
    plan = json.loads((manifest / "plan.json").read_text())
    if args.defer_list:
        deferred = set(json.loads(args.defer_list.read_text()))
        jobs.sort(key=lambda job: job["relative_path"] in deferred)
    if sha256(ROOT / "scripts/95_acquire_limburg_satellite_archive.py") != plan["helper_sha256"]:
        raise ValueError("Pinned raster helper differs from acquisition manifest")
    if sha256(ROOT / "scripts/96_acquire_limburg_compact_eo.py") != plan["code_sha256"]:
        raise ValueError("Pinned composite code differs from acquisition manifest")
    import ee

    ee.Initialize(project=args.project)
    region = ee.Geometry(json.loads((manifest / "roi.geojson").read_text()))
    if args.smoke:
        jobs = [
            next(j for j in reversed(jobs) if j["product"] == product)
            for product in compact.PRODUCTS
        ]
    initially_ready = {j["relative_path"] for j in jobs if archive.ready(j["relative_path"])}
    counts = {
        "planned_files": len(jobs),
        "committed_files": len(initially_ready),
        "new_downloads": 0,
        "seed_verified": 0,
        "failed": 0,
        "mode": "smoke" if args.smoke else "production",
    }
    args.cache.mkdir(parents=True, exist_ok=True)
    import fcntl

    lock = (args.cache / ".worker.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_name = "_control/smoke.json" if args.smoke else "progress.json"

    def progress(status):
        archive.json_status(
            state_name,
            counts
            | {
                "status": status,
                "archive_bytes": archive.used,
                "max_archive_bytes": archive.max_bytes,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            },
        )

    def process(job):
        relative = job["relative_path"]
        if archive.ready(relative):
            return "existing"
        data = archive.index.get(archive.name(relative))
        receipt = archive.index.get(archive.name(str(Path(relative).with_suffix(".receipt.json"))))
        if (
            data
            and receipt
            and receipt["metadata"].get("data_sha256") == data["metadata"].get("sha256")
        ):
            archive.verify_data(relative, data["metadata"]["sha256"])
            if not archive.ready(relative):
                raise ValueError("Seed data/receipt commit failed")
            return "seed_verified"
        image = compact.composite(ee, job)
        compact.ARCHIVE.download_job(job, args.cache, 1, region, image)
        path = args.cache / relative
        local_receipt = path.with_suffix(".receipt.json")
        archive.publish_pair(path, relative, local_receipt, readback=True)
        # Only disposable VM cache, after complete verified Blob publication.
        path.unlink()
        local_receipt.unlink()
        return "new_downloads"

    progress("running")
    halted = None
    # Bounded batches keep memory/cache bounded and let failures/deadlines stop work.
    for offset in range(0, len(jobs), args.workers):
        if time.time() >= args.deadline_epoch:
            halted = "runtime_budget"
            break
        batch = [
            j
            for j in jobs[offset : offset + args.workers]
            if j["relative_path"] not in initially_ready
        ]
        if not batch:
            continue
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(process, j): j for j in batch}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    status = future.result()
                    if status != "existing":
                        counts[status] += 1
                        counts["committed_files"] += 1
                except Exception as error:
                    counts["failed"] += 1
                    message = f"{type(error).__name__}: {str(error).split('https://')[0]}"
                    archive.json_status(
                        "_errors/"
                        + hashlib.sha256(job["relative_path"].encode()).hexdigest()
                        + ".json",
                        {"job": job["relative_path"], "error": message},
                    )
                    print("Failed", job["relative_path"], message, flush=True)
                    if "budget reached" in message or counts["failed"] >= 10:
                        halted = "storage_budget_or_failures"
        progress(halted or "running")
        if offset % 30 == 0:
            print(counts, flush=True)
        if halted:
            break
    if not halted and counts["failed"] == 0 and counts["committed_files"] == len(jobs):
        progress("completed")
        print("All planned files committed and verified", flush=True)
    else:
        progress(halted or "incomplete_with_errors")
        raise RuntimeError("Acquisition stopped with explicit incomplete status")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", default="stkerkradeprod01bg")
    parser.add_argument("--container", default="limburg-compact-eo")
    parser.add_argument("--prefix", default="v1")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/limburg_compact_eo")
    parser.add_argument("--cache", type=Path, default=ROOT / "data/eo_cache")
    parser.add_argument("--project", default="limburg-511403")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--max-gb", type=float, default=70)
    parser.add_argument("--deadline-epoch", type=float, default=float("inf"))
    parser.add_argument("--seed", type=Path)
    parser.add_argument("--defer-list", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--deallocate", action="store_true")
    parser.add_argument("--deallocate-only", action="store_true")
    args = parser.parse_args()
    from azure.identity import AzureCliCredential, ManagedIdentityCredential

    credential = AzureCliCredential() if args.seed else ManagedIdentityCredential()
    if args.deallocate_only:
        deallocate(credential)
        return
    from azure.storage.blob import BlobServiceClient

    container = BlobServiceClient(
        f"https://{args.account}.blob.core.windows.net", credential=credential
    ).get_container_client(args.container)
    if args.seed:
        archive = BlobArchive(container, args.prefix, int(args.max_gb * 1e9))
        receipts = list(args.seed.glob("images/**/*.receipt.json"))

        def seed(receipt):
            data = receipt.with_suffix("").with_suffix(".tif")
            relative = data.relative_to(args.seed).as_posix()
            archive.publish_pair(data, relative, receipt, readback=False)

        with ThreadPoolExecutor(max_workers=6) as pool:
            for i, future in enumerate(as_completed([pool.submit(seed, r) for r in receipts]), 1):
                future.result()
                if i % 100 == 0:
                    print(f"Seeded {i}/{len(receipts)} files", flush=True)
        archive.json_status(
            "_control/seed.json",
            {"files": len(receipts), "status": "uploaded_pending_cloud_readback"},
        )
        print("Seed uploads complete", len(receipts), flush=True)
        return
    try:
        archive = BlobArchive(container, args.prefix, int(args.max_gb * 1e9))
        run(args, archive, credential)
    finally:
        if args.deallocate and not args.smoke:
            deallocate(credential)


if __name__ == "__main__":
    main()
