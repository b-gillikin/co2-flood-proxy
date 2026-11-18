"""Bounded, recoverable offload of two explicitly authorized historical caches.

Only stdlib is needed until connecting to Azure. Original research outputs and
run-level records stay local. Each removed file has a fully read-back remote
object plus independently verified inventory; no deletion based on an ETag.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import tarfile
import time
from pathlib import Path, PurePosixPath

ROOTS = (
    "data/processed/limburg_tensor_cache_v1",
    "data/processed/eo_expansion_sequences",
)
CONTROL = {"index.json", "manifest.json", "status.json"}
MEMBER = "DERIVED-CACHE-INVENTORY.json"
GIB = 1024**3


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(value, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(8 * 1024**2), b""):
        h.update(block)
    return h.hexdigest()


def sha(path):
    with Path(path).open("rb") as f:
        return digest(f)


def safe_path(root, name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or not any(name.startswith(base + "/") for base in ROOTS):
        raise ValueError("Outside exact authorized cache roots: " + name)
    path = Path(root) / p
    if path.is_symlink() or path.resolve() != Path(root).resolve() / p:
        raise ValueError("Symlink or escaping source: " + name)
    return path


def check_identity(path, row):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or (
        s.st_size,
        s.st_mtime_ns,
        s.st_ino,
        s.st_dev,
        s.st_nlink,
    ) != (row["size"], row["mtime_ns"], row["ino"], row["dev"], row["nlink"]):
        raise ValueError("Source changed since inventory: " + str(path))


def reserve(path, additional=0):
    if shutil.disk_usage(path).free < 50 * GIB + additional:
        raise RuntimeError("Preserve the existing 50-GiB free-space reserve")


def ensure_idle():
    text = subprocess.check_output(["ps", "-axo", "command="], text=True)
    names = (
        "130_extract_eo_expansion.py",
        "131_run_eo_expansion_comparisons.py",
        "132_parallel_eo_expansion.py",
        "133_extract_supported_croma.py",
        "101_aggregate_limburg_eo_catchments.py",
        "218_build_spatial_tensor_cache.py",
        "219_profile_fast_spatial.py",
        "220_cache_terramind_augmentations.py",
        "222_prepare_optimized_spatial_queue.py",
        "224_verify_fast_spatial_runtime.py",
        "234_calibrate_chapter_physical.py",
        "215_apply_local_spatial_models.py",
    )
    active = [
        line
        for line in text.splitlines()
        if "python" in line.lower() and any(n in line for n in names)
    ]
    if active:
        raise RuntimeError("Historical owning workflow is active: " + "\n".join(active))


def verify_tar(path, records, *, extract=None, only=None):
    expected = {r["path"]: r for r in records}
    seen = set()
    with tarfile.open(path, "r|gz") as archive:
        for m in archive:
            if not m.isfile() or m.name in seen:
                raise ValueError("Nonregular/duplicate archive member")
            seen.add(m.name)
            f = archive.extractfile(m)
            if m.name == MEMBER:
                if json.load(f) != records:
                    raise ValueError("Embedded inventory mismatch")
                continue
            if m.name not in expected or m.size != expected[m.name]["size"]:
                raise ValueError("Archive member census/size mismatch")
            row = expected[m.name]
            h = hashlib.sha256()
            target = None
            if extract is not None and (only is None or m.name == only):
                safe_path(Path(extract), m.name)
                target = Path(extract) / m.name
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise FileExistsError(target)
                output = target.open("xb")
            else:
                output = None
            try:
                for block in iter(lambda stream=f: stream.read(8 * 1024**2), b""):
                    h.update(block)
                    if output:
                        output.write(block)
            finally:
                if output:
                    output.close()
            if h.hexdigest() != row["sha256"]:
                if target:
                    target.unlink()
                raise ValueError("Archive member hash mismatch")
            if target:
                os.chmod(target, stat.S_IMODE(row["mode"]))
                os.utime(target, ns=(row["mtime_ns"], row["mtime_ns"]))
    if seen != set(expected) | {MEMBER}:
        raise ValueError("Incomplete archive census")


class HashReader:
    def __init__(self, stream):
        self.stream = stream
        self.hash = hashlib.sha256()

    def read(self, size):
        body = self.stream.read(size)
        self.hash.update(body)
        return body


def pack(root, output, records):
    # Stream both large NPY tensors and small JSON without full-array loading.
    with tarfile.open(output, "w:gz", compresslevel=1) as archive:
        for row in records:
            path = safe_path(root, row["path"])
            check_identity(path, row)
            info = tarfile.TarInfo(row["path"])
            info.size = row["size"]
            info.mode = stat.S_IMODE(row["mode"])
            info.mtime = row["mtime_ns"] // 10**9
            with path.open("rb") as source:
                reader = HashReader(source)
                archive.addfile(info, reader)
            check_identity(path, row)
            row["sha256"] = reader.hash.hexdigest()
        body = json.dumps(records, sort_keys=True).encode()
        info = tarfile.TarInfo(MEMBER)
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))
    verify_tar(output, records)


def credential():
    from azure.core.credentials import AccessToken

    class Credential:
        def get_token(self, *scopes, **kwargs):
            if not hasattr(self, "token") or self.token.expires_on < time.time() + 120:
                data = json.loads(
                    subprocess.check_output(
                        [
                            "az",
                            "account",
                            "get-access-token",
                            "--subscription",
                            "c7729fd0-7b35-4ec4-b1a3-ec7079b776fa",
                            "--resource",
                            "https://storage.azure.com/",
                            "-o",
                            "json",
                        ],
                        text=True,
                    )
                )
                self.token = AccessToken(data["accessToken"], int(data["expires_on"]))
            return self.token

    return Credential()


def cloud():
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient(
        "https://stunumeritphdbackupbg.blob.core.windows.net", credential=credential()
    ).get_container_client("dissertation-recovery")


def publish_json(container, name, value):
    body = json.dumps(value, sort_keys=True).encode()
    name = name + "-" + hashlib.sha256(body).hexdigest() + ".json"
    blob = container.get_blob_client(name)
    if not blob.exists():
        blob.upload_blob(body, overwrite=False)
    if blob.download_blob().readall() != body:
        raise ValueError("Remote recovery metadata readback failed")
    return name


def verify_remote(container, bundle, scratch, progress):
    blob = container.get_blob_client(bundle["blob"])
    h = hashlib.sha256()
    count = 0
    # Direct blobs need no second 7-GiB local copy. Archive readback stays bounded.
    readback = scratch / "readback.tar.gz" if bundle["kind"] == "tar" else None
    if readback:
        reserve(scratch, bundle["archive_bytes"] + 256 * 1024**2)
    with readback.open("wb") if readback else open(os.devnull, "wb") as f:
        for block in blob.download_blob(max_concurrency=1).chunks():
            f.write(block)
            h.update(block)
            count += len(block)
            progress(phase="remote_readback", transferred_bytes=count)
    if count != bundle["archive_bytes"] or h.hexdigest() != bundle["sha256"]:
        raise ValueError("Complete remote byte readback failed")
    if readback:
        verify_tar(readback, bundle["records"])
    return readback


def retire(root, records, verified, progress):
    if verified.get("status") != "remote_bytes_and_members_verified":
        raise ValueError("Retirement requires actual remote verification")
    if (
        verified.get("records_sha256")
        != hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    ):
        raise ValueError("Verification is for a different file census")
    # Whole bundle is checked before the first unlink. Its durable remote/local
    # inventory records intent; interruption never loses removed-file identity.
    for row in records:
        path = safe_path(root, row["path"])
        if path.exists():
            check_identity(path, row)
            if sha(path) != row["sha256"]:
                raise ValueError("Source bytes changed before retirement")
    removed = 0
    for i, row in enumerate(records):
        path = safe_path(root, row["path"])
        if path.exists():
            check_identity(path, row)
            path.unlink()
            removed += row["size"]
        if i % 1000 == 0:
            progress(phase="retiring", retired_in_bundle=i + 1)
    return removed


def open_inventory(out):
    db = sqlite3.connect(out / "inventory.sqlite")
    db.row_factory = sqlite3.Row
    columns = {r[1] for r in db.execute("PRAGMA table_info(files)")}
    if "bundle" not in columns:
        db.execute("ALTER TABLE files ADD COLUMN bundle TEXT")
        db.execute("CREATE INDEX files_bundle ON files(bundle)")
        db.commit()
    return db


def next_records(db, *, direct=False):
    condition = (
        "root=? AND suffix='.npy'"
        if direct
        else "root=? AND suffix='.json' AND path NOT LIKE '%/manifest.json' "
        "AND path NOT LIKE '%/status.json' AND path NOT LIKE '%/index.json'"
    )
    base = ROOTS[0] if direct else ROOTS[1]
    rows = db.execute(
        "SELECT * FROM files WHERE bundle IS NULL AND " + condition + " LIMIT ?",
        (base, 1 if direct else 10000),
    )
    result, total = [], 0
    for row in rows:
        row = dict(row)
        row.pop("bundle", None)
        if result and total + row["size"] > 512 * 1024**2:
            break
        result.append(row)
        total += row["size"]
    return result


def run(root, out, protection, *, direct=False):
    ensure_idle()
    reserve(root, 2 * GIB)
    container = cloud()
    db = open_inventory(out)
    scratch = out / "scratch"
    scratch.mkdir(exist_ok=True)
    bundles = out / "bundles"
    bundles.mkdir(exist_ok=True)
    prefix = "chapter1-co2/derived-eo/2026-11-18"
    progress_path = out / "progress.json"
    state = (
        json.loads(progress_path.read_text())
        if progress_path.exists()
        else {
            "status": "running",
            "free_before_gib": shutil.disk_usage(root).free / GIB,
            "completed_bundles": 0,
            "retired_files": 0,
            "retired_logical_bytes": 0,
            "started_unix": time.time(),
            "format": "direct" if direct else "tar",
        }
    )
    last_write = 0.0
    # Reconcile a possible crash between durable bundle completion and progress.
    state.update(status="running", completed_bundles=0, retired_files=0, retired_logical_bytes=0)
    for p in bundles.glob("*.json"):
        saved = json.loads(p.read_text())
        if saved["status"] == "completed":
            state["completed_bundles"] += 1
            state["retired_files"] += len(saved["records"])
            state["retired_logical_bytes"] += sum(r["size"] for r in saved["records"])

    def progress(**kwargs):
        nonlocal last_write
        state.update(kwargs)
        now = time.time()
        if now - last_write >= 5 or kwargs.get("force"):
            state.update(updated_unix=now, free_now_gib=shutil.disk_usage(root).free / GIB)
            atomic(progress_path, state)
            last_write = now

    def protect():
        ensure_idle()
        for name, value in protection.items():
            if sha(root / name) != value:
                raise ValueError("Protected current evidence changed: " + name)

    publish_json(container, prefix + "/protection", protection)
    for base in ROOTS:
        atomic(
            root / base / "OFFLOADED-DERIVED.json",
            {
                "status": "offload_started_or_partial",
                "output": str(out.relative_to(root)),
                "account": "stunumeritphdbackupbg",
                "container": "dissertation-recovery",
                "prefix": prefix,
                "restore": "scripts/278_offload_historical_derived.py --restore-path PROJECT_RELATIVE_FILE",
            },
        )
    try:
        while True:
            pending = [
                p
                for p in sorted(bundles.glob("*.json"))
                if json.loads(p.read_text())["status"] != "completed"
            ]
            if pending:
                path = pending[0]
                bundle = json.loads(path.read_text())
            else:
                records = next_records(db, direct=direct)
                if not records:
                    break
                ident = f"{len(list(bundles.glob('*.json'))):05d}"
                path = bundles / (ident + ".json")
                bundle = dict(
                    id=ident, kind="tar", status="planned", records=records
                )
                atomic(path, bundle)
            records = bundle["records"]
            is_direct = bundle["kind"] == "direct"
            db.executemany(
                "UPDATE files SET bundle=? WHERE path=?",
                [(bundle["id"], r["path"]) for r in records],
            )
            db.commit()
            progress(bundle=bundle["id"], phase="checking", force=True)
            protect()
            if bundle["status"] == "planned":
                if is_direct:
                    data = safe_path(root, records[0]["path"])
                    check_identity(data, records[0])
                    records[0]["sha256"] = sha(data)
                    check_identity(data, records[0])
                else:
                    reserve(root, 2 * sum(r["size"] for r in records) + 512 * 1024**2)
                    data = scratch / "packed.tar.gz"
                    progress(phase="packing", force=True)
                    pack(root, data, records)
                bundle.update(status="packed", sha256=sha(data), archive_bytes=data.stat().st_size)
                bundle["blob"] = (
                    prefix + "/objects/" + bundle["sha256"] + (".bin" if is_direct else ".tar.gz")
                )
                atomic(path, bundle)
            if bundle["status"] == "packed":
                data = (
                    safe_path(root, records[0]["path"]) if is_direct else scratch / "packed.tar.gz"
                )
                if not data.exists() or sha(data) != bundle["sha256"]:
                    bundle["status"] = "planned"
                    atomic(path, bundle)
                    continue
                blob = container.get_blob_client(bundle["blob"])
                progress(phase="uploading", force=True)
                if not blob.exists():
                    with data.open("rb") as f:
                        blob.upload_blob(
                            f,
                            overwrite=False,
                            length=bundle["archive_bytes"],
                            max_concurrency=4,
                            metadata={"sha256": bundle["sha256"]},
                            timeout=120,
                        )
                readback = verify_remote(container, bundle, scratch, progress)
                pilot_path = out / ("pilot-" + bundle["kind"] + ".json")
                pilot = not pilot_path.exists()
                if pilot:
                    restore = scratch / "pilot"
                    restore.mkdir(exist_ok=False)
                    if is_direct:
                        target = restore / "restored.bin"
                        reserve(root, records[0]["size"])
                        with target.open("wb") as f:
                            blob.download_blob(max_concurrency=1).readinto(f)
                        if sha(target) != records[0]["sha256"]:
                            raise ValueError("Pilot restore hash differs")
                    else:
                        verify_tar(readback, records, extract=restore)
                        for row in records:
                            if sha(restore / row["path"]) != row["sha256"]:
                                raise ValueError("Pilot restore differs")
                    atomic(
                        pilot_path,
                        dict(
                            status="full_bundle_restored_and_every_file_verified",
                            bundle=bundle["id"],
                            files=len(records),
                        ),
                    )
                    shutil.rmtree(restore)
                receipt = {
                    "status": "remote_bytes_and_members_verified",
                    "bundle": bundle["id"],
                    "blob": bundle["blob"],
                    "sha256": bundle["sha256"],
                    "records_sha256": hashlib.sha256(
                        json.dumps(records, sort_keys=True).encode()
                    ).hexdigest(),
                    "kind": bundle["kind"],
                    "records": records,
                    "verified_unix": time.time(),
                }
                bundle["receipt_blob"] = publish_json(
                    container, prefix + "/receipts/" + bundle["id"], receipt
                )
                bundle.update(status="remote_verified", verification=receipt)
                atomic(path, bundle)
                if readback:
                    readback.unlink()
            protect()
            progress(phase="retiring", force=True)
            retired = retire(root, records, bundle["verification"], progress)
            bundle.update(
                status="completed", removed_bytes_this_attempt=retired, completed_unix=time.time()
            )
            atomic(path, bundle)
            state["completed_bundles"] += 1
            state["retired_files"] += len(records)
            state["retired_logical_bytes"] += sum(r["size"] for r in records)
            (scratch / "packed.tar.gz").unlink(missing_ok=True)
            progress(force=True)
        state["status"] = "completed"
        progress(phase="complete", force=True)
        protect()
    except BaseException as e:
        progress(status="paused_error", error=str(e), force=True)
        raise
    finally:
        db.close()


def restore_path(root, out, name):
    target = safe_path(root, name)
    db = open_inventory(out)
    try:
        row = db.execute("SELECT bundle FROM files WHERE path=?", (name,)).fetchone()
    finally:
        db.close()
    if not row or not row["bundle"]:
        raise ValueError("Path has no archived bundle")
    bundle = json.loads((out / "bundles" / (row["bundle"] + ".json")).read_text())
    record = next(r for r in bundle["records"] if r["path"] == name)
    if target.exists():
        if sha(target) != record["sha256"]:
            raise FileExistsError("Refuse to overwrite different local bytes")
        return {"status": "already_restored", "path": name}
    container = cloud()
    scratch = out / "restore-scratch"
    scratch.mkdir(exist_ok=True)
    reserve(root, bundle["archive_bytes"] + record["size"])
    blob = container.get_blob_client(bundle["blob"])
    downloaded = scratch / "downloaded"
    with downloaded.open("wb") as f:
        blob.download_blob(max_concurrency=1).readinto(f)
    if sha(downloaded) != bundle["sha256"]:
        raise ValueError("Restored remote object checksum differs")
    if bundle["kind"] == "tar":
        verify_tar(downloaded, bundle["records"], extract=root, only=name)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        downloaded.rename(target)
        os.chmod(target, stat.S_IMODE(record["mode"]))
        os.utime(target, ns=(record["mtime_ns"], record["mtime_ns"]))
    downloaded.unlink(missing_ok=True)
    if sha(target) != record["sha256"]:
        raise ValueError("Restored file differs")
    return {"status": "restored_exact_bytes", "path": name, "sha256": record["sha256"]}
