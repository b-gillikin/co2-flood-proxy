"""Stage the verified Flood-S1 subset with measured extraction and Azure recovery.

Use Azure CLI's Python. Wait for offloading headroom; never stage the full
Copernicus benchmark or exhaust disk. Extraction preserves original files.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import shutil
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/limburg_applied_tasks/flood_s1"
OUT = ROOT / "results/applied_study_v1/acquisition"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def main():
    from azure.core.credentials import AccessToken
    from azure.storage.blob import BlobServiceClient

    BASE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".flood-change.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    task = next(
        t
        for t in json.loads((ROOT / "config/limburg_applied_tasks_v1.json").read_text())["tasks"]
        if t["id"] == "AP02"
    )
    source = task["dataset"]
    state = dict(status="waiting_for_storage", source=source, downloaded_bytes=0)

    def save():
        state.update(updated_unix=time.time(), free_gib=shutil.disk_usage(ROOT).free / 1024**3)
        tmp = OUT / "flood-change-progress.partial"
        tmp.write_text(json.dumps(state, indent=2) + "\n")
        tmp.replace(OUT / "flood-change-progress.json")

    def wait_space(gib):
        while shutil.disk_usage(ROOT).free / 1024**3 < gib:
            save()
            time.sleep(10)

    path = BASE / "flood_s1.zip"
    if not path.exists():
        wait_space(70)
        temp = path.with_suffix(".zip.partial")
        state["status"] = "downloading"
        save()
        for attempt in range(4):
            try:
                offset = temp.stat().st_size if temp.exists() else 0
                req = urllib.request.Request(
                    source["url"], headers={"Range": f"bytes={offset}-"} if offset else {}
                )
                with urllib.request.urlopen(req, timeout=180) as response:
                    append = offset and response.status == 206
                    if append and not response.headers.get("Content-Range", "").startswith(
                        f"bytes {offset}-"
                    ):
                        raise ValueError("Invalid resume range")
                    state["downloaded_bytes"] = offset if append else 0
                    with temp.open("ab" if append else "wb") as stream:
                        while block := response.read(4 * 1024**2):
                            wait_space(51)
                            stream.write(block)
                            state["downloaded_bytes"] += len(block)
                            if state["downloaded_bytes"] % (64 * 1024**2) < len(block):
                                save()
                if temp.stat().st_size != source["bytes"] or sha(temp) != source["sha256_lfs"]:
                    raise ValueError("Source archive hash/size mismatch")
                temp.replace(path)
                break
            except Exception:
                if attempt == 3:
                    raise
                if temp.exists() and temp.stat().st_size >= source["bytes"]:
                    temp.unlink()
                time.sleep(2**attempt)
    if path.stat().st_size != source["bytes"] or sha(path) != source["sha256_lfs"]:
        raise ValueError("Existing archive conflicts with source")
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        for item in members:
            p = Path(item.filename)
            if (
                p.is_absolute()
                or ".." in p.parts
                or ((item.external_attr >> 16) & 0o170000) == 0o120000
            ):
                raise ValueError("Unsafe archive member")
        state.update(
            status="archive_verified",
            expanded_bytes=sum(i.file_size for i in members),
            members=len(members),
        )
        (OUT / "flood-change-zip-members.json").write_text(
            json.dumps(
                [
                    dict(
                        name=i.filename,
                        bytes=i.file_size,
                        compressed_bytes=i.compress_size,
                        crc=i.CRC,
                    )
                    for i in members
                ],
                indent=2,
            )
            + "\n"
        )
        save()

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
        blob = container.get_blob_client("applied-v1/sources/copernicus-bench/flood_s1.zip")
        state["status"] = "preserving_source_in_azure"
        save()
        if not blob.exists():
            with path.open("rb") as stream:
                blob.upload_blob(
                    stream,
                    overwrite=False,
                    max_concurrency=1,
                    validate_content=True,
                    metadata={"sha256": source["sha256_lfs"]},
                )
        props = blob.get_blob_properties()
        if props.size != source["bytes"] or props.metadata.get("sha256") != source["sha256_lfs"]:
            raise ValueError("Remote source archive conflict")
        if props.metadata.get("verified") != "sha256-readback":
            h = hashlib.sha256()
            for block in blob.download_blob(max_concurrency=1).chunks():
                h.update(block)
            if h.hexdigest() != source["sha256_lfs"]:
                raise ValueError("Remote source readback failed")
            blob.set_blob_metadata(dict(props.metadata) | {"verified": "sha256-readback"})
        state["azure_blob"] = blob.blob_name
        state["status"] = "waiting_for_expansion_space"
        save()
        # Account for the entire expansion, plus a 5-GiB allowance for active
        # writes. Do not shrink the scientific dataset to fit a guessed budget.
        wait_space(55 + state["expanded_bytes"] / 1024**3)
        state.update(status="extracting", extracted_files=0)
        save()
        extracted = BASE / "extracted"
        for item in members:
            if item.is_dir():
                continue
            target = extracted / item.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            # Read every member to validate CRC even when extraction is resumed.
            temp = target.with_suffix(target.suffix + ".partial")
            with z.open(item) as src, temp.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024**2)
            temp.replace(target)
            state["extracted_files"] += 1
            if state["extracted_files"] % 200 == 0:
                save()
        state.update(status="completed", extracted_root=str(extracted.relative_to(ROOT)))
        save()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        out = OUT / "flood-change-error.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps({"error": f"{type(exc).__name__}: {exc}", "unix": time.time()}, indent=2)
            + "\n"
        )
        raise
