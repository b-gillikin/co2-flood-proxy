"""Restore selected offloaded Limburg images, with SHA256 and disk checks.

Use Azure CLI's Python; defaults to listing only. Paths are project-relative
and must appear in the retained removal ledger. No other chapter is touched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "results/applied_study_v1/offload/removed.jsonl"


def destination(relative, root=ROOT):
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts or p.parts[:3] != ("data", "raw", "limburg_eo_expansion"):
        raise ValueError("Not an offloaded expansion path")
    target = root / p
    if target.resolve() != root.resolve() / p or target.is_symlink():
        raise ValueError("Restore target crosses a symlink")
    return target


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "--path",
        action="append",
        required=True,
        help="Exact project-relative image path; repeatable",
    )
    parser.add_argument(
        "--restore", action="store_true", help="Otherwise report selected bytes only"
    )
    args = parser.parse_args()
    wanted = set(args.path)
    rows = {
        r["path"]: r
        for line in LEDGER.read_text().splitlines()
        if (r := json.loads(line))["path"] in wanted
    }
    if set(rows) != wanted:
        raise ValueError("Requested path missing from verified offload ledger")
    for relative in rows:
        destination(relative)
    total = sum(r["bytes"] for r in rows.values())
    print(
        json.dumps(
            dict(files=len(rows), bytes=total, free_gib=shutil.disk_usage(ROOT).free / 1024**3)
        )
    )
    if not args.restore:
        return
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

    container = BlobServiceClient(
        "https://stkerkradeprod01bg.blob.core.windows.net", credential=Credential()
    ).get_container_client("limburg-compact-eo")
    for row in rows.values():
        target = destination(row["path"])
        if target.exists():
            h = hashlib.sha256(target.read_bytes()).hexdigest()
            if h != row["sha256"]:
                raise ValueError("Existing local file differs; refusing overwrite")
            continue
        if shutil.disk_usage(ROOT).free - row["bytes"] < 52 * 1024**3:
            raise RuntimeError("Insufficient room above 50 GiB reserve and 2 GiB headroom")
        temp = target.with_suffix(".restore.partial")
        if temp.exists() or temp.is_symlink():
            raise ValueError("Partial restore already exists; inspect before retrying")
        target.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256()
        try:
            with temp.open("xb") as stream:
                for block in container.download_blob(row["blob"], max_concurrency=1).chunks():
                    stream.write(block)
                    h.update(block)
                    if shutil.disk_usage(ROOT).free < 51 * 1024**3:
                        raise RuntimeError("Reserve approached during restore")
            if temp.stat().st_size != row["bytes"] or h.hexdigest() != row["sha256"]:
                raise ValueError("Restored bytes do not match verified ledger")
            if target.exists():
                raise ValueError("Target appeared during restore; refusing overwrite")
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
        print(json.dumps(dict(restored=row["path"], sha256=h.hexdigest())), flush=True)


if __name__ == "__main__":
    main()
