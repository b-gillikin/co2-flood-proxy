import hashlib
import io
import json
import tarfile

import pytest

from src import derived_cache_offload as m
from src.cache_recovery_guard import require_local_cache


def held(tmp_path, name="tile.json", body=b'{"held":"scientific record"}'):
    p = tmp_path / m.ROOTS[1] / "model" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(body)
    s = p.stat()
    return p, dict(
        path=str(p.relative_to(tmp_path)),
        root=m.ROOTS[1],
        size=s.st_size,
        allocated=s.st_blocks * 512,
        mtime_ns=s.st_mtime_ns,
        ino=s.st_ino,
        dev=s.st_dev,
        nlink=s.st_nlink,
        mode=s.st_mode,
        suffix=p.suffix,
    )


def verified(records):
    return dict(
        status="remote_bytes_and_members_verified",
        records_sha256=hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest(),
    )


@pytest.mark.parametrize(
    "name",
    [
        "../other",
        "/tmp/file",
        "data/raw/gauges/q.csv",
        "data/processed/eo_expansion_sequences/../outside",
    ],
)
def test_only_exact_roots(tmp_path, name):
    with pytest.raises(ValueError):
        m.safe_path(tmp_path, name)


def test_symlink_parent_rejected(tmp_path):
    root = tmp_path / m.ROOTS[1]
    root.mkdir(parents=True)
    (root / "link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        m.safe_path(tmp_path, m.ROOTS[1] + "/link/outside")


def test_full_pack_restore_preserves_every_byte_and_metadata(tmp_path):
    p, row = held(tmp_path)
    archive = tmp_path / "archive.tar.gz"
    m.pack(tmp_path, archive, [row])
    dest = tmp_path / "restored"
    m.verify_tar(archive, [row], extract=dest)
    restored = dest / row["path"]
    assert restored.read_bytes() == p.read_bytes()
    assert restored.stat().st_mtime_ns == p.stat().st_mtime_ns


def test_corrupt_inventory_and_missing_members_rejected(tmp_path):
    _, row = held(tmp_path)
    row["sha256"] = "wrong"
    archive = tmp_path / "missing.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        body = json.dumps([row]).encode()
        info = tarfile.TarInfo(m.MEMBER)
        info.size = len(body)
        tar.addfile(info, io.BytesIO(body))
    with pytest.raises(ValueError, match="Incomplete"):
        m.verify_tar(archive, [row])


def test_readback_verification_required_before_retirement(tmp_path):
    p, row = held(tmp_path)
    row["sha256"] = m.sha(p)
    for receipt in [{}, {"status": "remote_bytes_and_members_verified", "records_sha256": "wrong"}]:
        with pytest.raises(ValueError):
            m.retire(tmp_path, [row], receipt, lambda **kw: None)
        assert p.exists()


def test_changed_file_prevents_entire_bundle_retirement(tmp_path):
    first, a = held(tmp_path, "first.json")
    second, b = held(tmp_path, "second.json")
    for p, r in [(first, a), (second, b)]:
        r["sha256"] = m.sha(p)
    second.write_bytes(b"changed")
    with pytest.raises(ValueError):
        m.retire(tmp_path, [a, b], verified([a, b]), lambda **kw: None)
    assert first.exists() and second.exists()


def test_same_stat_but_changed_bytes_rejected(tmp_path):
    import os

    p, row = held(tmp_path)
    row["sha256"] = m.sha(p)
    p.write_bytes(b"x" * row["size"])
    os.utime(p, ns=(row["mtime_ns"], row["mtime_ns"]))
    with pytest.raises(ValueError, match="bytes"):
        m.retire(tmp_path, [row], verified([row]), lambda **kw: None)
    assert p.exists()


def test_verified_retirement_resumes_after_one_file_removed(tmp_path):
    p, row = held(tmp_path)
    row["sha256"] = m.sha(p)
    receipt = verified([row])
    assert m.retire(tmp_path, [row], receipt, lambda **kw: None) == row["size"]
    assert m.retire(tmp_path, [row], receipt, lambda **kw: None) == 0


def test_cold_cache_raises_before_reading_missing_inputs(tmp_path):
    cache = tmp_path / m.ROOTS[1]
    cache.mkdir(parents=True)
    require_local_cache(cache / "not_present_yet")
    (cache / "OFFLOADED-DERIVED.json").write_text("{}")
    with pytest.raises(RuntimeError, match="offloaded, not missing"):
        require_local_cache(cache / "model/run")


def test_remote_corruption_never_becomes_verified(tmp_path, monkeypatch):
    p, row = held(tmp_path)
    row["sha256"] = m.sha(p)

    class Blob:
        def download_blob(self, **kwargs):
            return type("Download", (), {"chunks": lambda self: iter([b"corrupt"])})()

    class Cloud:
        def get_blob_client(self, name):
            return Blob()

    with pytest.raises(ValueError, match="readback"):
        m.verify_remote(
            Cloud(),
            dict(blob="x", kind="direct", archive_bytes=row["size"], sha256=row["sha256"]),
            tmp_path,
            lambda **kw: None,
        )
    assert p.exists()


def test_low_disk_space_stops_before_mutation(tmp_path, monkeypatch):
    monkeypatch.setattr(m.shutil, "disk_usage", lambda p: type("Disk", (), {"free": 49 * m.GIB})())
    with pytest.raises(RuntimeError, match="50-GiB"):
        m.reserve(tmp_path)
