"""Run the pinned supplemental acquisition into private Blob Storage.

Shared immutable publication/readback contracts come from the original cloud
worker. Local seed uploads are deferred and refreshed before verification.
"""

import argparse
import hashlib
import importlib.util
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load(ROOT / "infrastructure/compact_eo/cloud_worker.py", "original_blob_worker")


def refresh_pair(archive, relative):
    """See seed pairs uploaded after worker start; no token or SAS persistence."""
    from azure.core.exceptions import ResourceNotFoundError

    names = [archive.name(relative), archive.name(str(Path(relative).with_suffix(".receipt.json")))]
    for name in names:
        try:
            p = archive.container.get_blob_client(name).get_blob_properties()
        except ResourceNotFoundError:
            continue
        with archive.lock:
            old = archive.index.get(name, {}).get("bytes", 0)
            archive.index[name] = {"bytes": p.size, "metadata": p.metadata or {}}
            archive.used += p.size - old


def run(args, archive):
    import ee

    expansion = load(ROOT / "scripts/114_expand_limburg_eo_acquisition.py", "expansion_source")
    plan = json.loads((args.manifest / "plan.json").read_text())
    for name, expected in plan["input_sha256"].items():
        if BASE.sha256(ROOT / name) != expected:
            raise ValueError("Pinned acquisition input changed: " + name)
    ee.Initialize(project=args.project)
    region = ee.Geometry(json.loads((ROOT / "data/raw/limburg_compact_eo/roi.geojson").read_text()))
    jobs = json.loads((args.manifest / "jobs.json").read_text())
    deferred = set(json.loads(args.defer_list.read_text())) if args.defer_list else set()
    if args.smoke:
        choices = {}
        for job in reversed(jobs):
            if job["relative_path"] not in deferred:
                choices.setdefault(job["product"], job)
        jobs = list(choices.values())
    else:
        jobs.sort(key=lambda j: j["relative_path"] in deferred)
    ready = {j["relative_path"] for j in jobs if archive.ready(j["relative_path"])}
    counts = {
        "planned_files": len(jobs),
        "committed_files": len(ready),
        "new_downloads": 0,
        "seed_verified": 0,
        "failed": 0,
    }
    state_name = "_control/smoke.json" if args.smoke else "progress.json"
    args.cache.mkdir(parents=True, exist_ok=True)
    import fcntl

    with (args.cache / ".worker.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

        def progress(status):
            archive.json_status(
                state_name,
                {
                    **counts,
                    "status": status,
                    "archive_bytes": archive.used,
                    "max_archive_bytes": archive.max_bytes,
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                },
            )

        def process(job):
            relative = job["relative_path"]
            if relative in deferred:
                refresh_pair(archive, relative)
            if archive.ready(relative):
                return "seed_verified"  # A concurrent seed verifier may finish a pair.
            data = archive.index.get(archive.name(relative))
            receipt = archive.index.get(
                archive.name(str(Path(relative).with_suffix(".receipt.json")))
            )
            if (
                data
                and receipt
                and receipt["metadata"].get("data_sha256") == data["metadata"].get("sha256")
            ):
                archive.verify_data(relative, data["metadata"]["sha256"])
                if not archive.ready(relative):
                    raise ValueError("Seed readback incomplete")
                return "seed_verified"
            if relative in deferred:
                raise RuntimeError("Local seed pair not uploaded yet; retained for retry")
            image = expansion.composite(ee, job)
            expansion.A.download_job(job, args.cache, 1, region, image)
            path = args.cache / relative
            receipt_path = path.with_suffix(".receipt.json")
            archive.publish_pair(path, relative, receipt_path, readback=True)
            path.unlink()
            receipt_path.unlink()
            return "new_downloads"

        progress("running")
        halted = None
        for offset in range(0, len(jobs), args.workers):
            if time.time() >= args.deadline_epoch:
                halted = "deadline"
                break
            batch = [
                j for j in jobs[offset : offset + args.workers] if j["relative_path"] not in ready
            ]
            if not batch:
                continue
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(process, j): j for j in batch}
                for future in as_completed(futures):
                    job = futures[future]
                    try:
                        result = future.result()
                        counts[result] += 1
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
                        if "budget reached" in message or counts["failed"] >= 10:
                            halted = "storage_or_failures"
            progress(halted or "running")
            if halted:
                break
        complete = not halted and not counts["failed"] and counts["committed_files"] == len(jobs)
        progress("completed" if complete else halted or "incomplete_with_errors")
        if not complete:
            raise RuntimeError("Explicitly incomplete acquisition; inspect remote progress/errors")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", default="stkerkradeprod01bg")
    parser.add_argument("--container", default="limburg-compact-eo")
    parser.add_argument("--prefix", default="expansion-v1")
    parser.add_argument("--max-gb", type=float, default=300)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--project", default="limburg-511403")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/limburg_eo_expansion")
    parser.add_argument("--cache", type=Path, default=ROOT / "data/expansion_cache")
    parser.add_argument("--deadline-epoch", type=float, required=True)
    parser.add_argument("--defer-list", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--deallocate", action="store_true")
    args = parser.parse_args()
    from azure.identity import ManagedIdentityCredential
    from azure.storage.blob import BlobServiceClient

    credential = ManagedIdentityCredential()
    try:
        client = BlobServiceClient(
            f"https://{args.account}.blob.core.windows.net", credential=credential
        )
        archive = BASE.BlobArchive(
            client.get_container_client(args.container), args.prefix, int(args.max_gb * 1e9)
        )
        run(args, archive)
    finally:
        if args.deallocate and not args.smoke:
            BASE.deallocate(credential)


if __name__ == "__main__":
    main()
