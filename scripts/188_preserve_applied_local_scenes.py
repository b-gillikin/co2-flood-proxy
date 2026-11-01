"""Additively preserve individual local acquisitions in the private Blob store.

Use Azure CLI's Python. Every image/receipt pair is verified by remote SHA256
readback; nothing local or remote is deleted. Does not provision any compute.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/applied_study_v1/local_references"
BASE = ROOT / "data/raw/limburg_applied_tasks/local_scenes"


def main():
    from azure.core.credentials import AccessToken
    from azure.storage.blob import BlobServiceClient

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

    acquired = json.loads((OUT / "local-scene-progress.json").read_text())
    if acquired["status"] != "completed" or acquired["failures"]:
        raise ValueError("Wait for completed acquisition before preservation inventory")
    container = BlobServiceClient(
        "https://stkerkradeprod01bg.blob.core.windows.net", credential=Credential()
    ).get_container_client("limburg-compact-eo")
    progress = dict(status="running", total=acquired["total"], verified=0, bytes=0)
    with (OUT / "local-scene-azure.jsonl").open("a") as ledger:
        for receipt in sorted(BASE.rglob("*.receipt.json")):
            r = json.loads(receipt.read_text())
            relative = r["job"]["path"]
            path = BASE / relative
            if (
                Path(relative).is_absolute()
                or ".." in Path(relative).parts
                or path.resolve() != BASE.resolve() / relative
            ):
                raise ValueError("Unsafe acquisition path")
            if hashlib.sha256(path.read_bytes()).hexdigest() != r["sha256"]:
                raise ValueError("Local acquisition hash changed")
            name = "applied-v1/local-scenes/" + relative
            for file, blobname, digest in [
                (path, name, r["sha256"]),
                (
                    receipt,
                    name.removesuffix(".tif") + ".receipt.json",
                    hashlib.sha256(receipt.read_bytes()).hexdigest(),
                ),
            ]:
                blob = container.get_blob_client(blobname)
                if not blob.exists():
                    with file.open("rb") as stream:
                        blob.upload_blob(
                            stream, overwrite=False, max_concurrency=1, metadata={"sha256": digest}
                        )
                props = blob.get_blob_properties()
                if props.size != file.stat().st_size or props.metadata.get("sha256") != digest:
                    raise ValueError("Existing remote acquisition differs; refusing overwrite")
                if props.metadata.get("verified") != "sha256-readback":
                    h = hashlib.sha256()
                    for block in blob.download_blob(max_concurrency=1).chunks():
                        h.update(block)
                    if h.hexdigest() != digest:
                        raise ValueError("Remote acquisition readback mismatch")
                    blob.set_blob_metadata({**props.metadata, "verified": "sha256-readback"})
            ledger.write(
                json.dumps(
                    dict(
                        path=str(path.relative_to(ROOT)),
                        blob=name,
                        bytes=r["bytes"],
                        sha256=r["sha256"],
                        verified="sha256-readback",
                    )
                )
                + "\n"
            )
            ledger.flush()
            progress["verified"] += 1
            progress["bytes"] += r["bytes"]
            (OUT / "local-scene-azure-progress.json").write_text(
                json.dumps(progress, indent=2) + "\n"
            )
        if progress["verified"] != progress["total"]:
            raise ValueError("Preservation inventory is incomplete")
    progress["status"] = "completed"
    (OUT / "local-scene-azure-progress.json").write_text(json.dumps(progress, indent=2) + "\n")


if __name__ == "__main__":
    main()
