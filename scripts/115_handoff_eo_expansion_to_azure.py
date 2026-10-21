"""Seed the private supplemental EO archive using Azure CLI authentication.

No credentials enter the input bundle, Blob Storage, logs or Git. Completed local
files are retained; cloud processing must perform SHA-256 readback before use.
"""

import argparse
import importlib.util
import json
import subprocess
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/limburg_eo_expansion"


class CliCredential:
    def __init__(self):
        self.lock = threading.Lock()
        self.token = None

    def get_token(self, *scopes, **kwargs):
        from azure.core.credentials import AccessToken

        with self.lock:
            if self.token is None or self.token.expires_on < time.time() + 120:
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
                self.token = AccessToken(result["accessToken"], int(result["expires_on"]))
            return self.token


def worker_module():
    spec = importlib.util.spec_from_file_location(
        "shared_blob_archive", ROOT / "infrastructure/compact_eo/cloud_worker.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--bundle", action="store_true")
    modes.add_argument("--seed", action="store_true")
    modes.add_argument(
        "--status",
        action="store_true",
        help="Read live private Azure progress without listing data blobs",
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    from azure.storage.blob import BlobServiceClient

    shared = worker_module()
    container = BlobServiceClient(
        "https://stkerkradeprod01bg.blob.core.windows.net", credential=CliCredential()
    ).get_container_client("limburg-compact-eo")
    if args.status:
        report = json.loads(container.download_blob("expansion-v1/progress.json").readall())
        tmp = BASE / "cloud-progress.partial"
        tmp.write_text(json.dumps(report, indent=2) + "\n")
        tmp.replace(BASE / "cloud-progress.json")
        print(json.dumps(report, indent=2))
        return
    archive = shared.BlobArchive(container, "expansion-v1", 300_000_000_000)
    if args.bundle:
        plan = json.loads((BASE / "plan.json").read_text())
        paths = [ROOT / p for p in plan["input_sha256"]]
        paths += [
            BASE / "plan.json",
            BASE / "jobs.json",
            ROOT / "data/raw/limburg_compact_eo/roi.geojson",
            ROOT / "infrastructure/compact_eo/cloud_worker.py",
            ROOT / "infrastructure/eo_expansion/cloud_worker.py",
        ]
        # Explicit immutable allow-list; never recurse through credential/config dirs.
        bundle = BASE / "cloud-inputs.tar.gz"
        with tarfile.open(bundle, "w:gz") as tar:
            for path in sorted(set(paths)):
                if path.is_symlink() or not path.is_file():
                    raise ValueError("Unsafe bundle input: " + str(path))
                tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        archive.put_file(
            bundle, "_control/cloud-inputs.tar.gz", {"purpose": "nonsecret-acquisition-inputs"}
        )
        report = {
            "bundle_sha256": shared.sha256(bundle),
            "bundle_bytes": bundle.stat().st_size,
            "paths": [str(p.relative_to(ROOT)) for p in sorted(set(paths))],
        }
        (BASE / "cloud-bundle.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: report[k] for k in ["bundle_sha256", "bundle_bytes"]}), flush=True)
        return
    jobs = {j["relative_path"]: j for j in json.loads((BASE / "jobs.json").read_text())}
    receipts = sorted(BASE.glob("images/**/*.receipt.json"))
    pending = [str(p.with_suffix("").with_suffix(".tif").relative_to(BASE)) for p in receipts]
    archive.json_status("_control/seed_pending.json", pending)
    (BASE / "seed_pending.json").write_text(json.dumps(pending) + "\n")

    def publish(receipt):
        path = receipt.with_suffix("").with_suffix(".tif")
        relative = str(path.relative_to(BASE))
        record = json.loads(receipt.read_text())
        for key in [
            "relative_path",
            "bands",
            "bounds",
            "window",
            "asset_ids",
            "acquisition_ms",
            "resolution",
            "dtype",
        ]:
            if record[key] != jobs[relative][key]:
                raise ValueError("Seed/job mismatch: " + relative)
        archive.publish_pair(path, relative, receipt, readback=False)

    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(publish, receipt) for receipt in receipts]
        for future in as_completed(futures):
            future.result()
            completed += 1
            if completed % 50 == 0 or completed == len(receipts):
                report = {
                    "files": len(receipts),
                    "uploaded_pairs": completed,
                    "status": "uploaded_pending_cloud_readback"
                    if completed == len(receipts)
                    else "uploading",
                }
                (BASE / "seed-progress.json").write_text(json.dumps(report, indent=2) + "\n")
                archive.json_status("_control/seed.json", report)
                print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
