#!/usr/bin/env python3
"""Continue six source-only final fits across sleep, interruption and reruns."""

from __future__ import annotations

import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venvs-applied/copernicus/bin/python"
FIT = ROOT / "scripts/233_fit_chapter_source.py"
OUT = ROOT / "results/limburg_chapter_sized_v1"
LOCK = ROOT / "results/applied_study_v3/.mps-owner.lock"
JOBS = [(kind, seed) for seed in (42, 1729, 31415) for kind in ("unet", "native")]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def completed(kind: str, seed: int) -> bool:
    folder = OUT / "final_source" / f"{kind}-{seed}"
    finish, model, manifest = (folder / name for name in ("complete.json", "model.pt", "manifest.json"))
    if not all(path.exists() for path in (finish, model, manifest)):
        return False
    record = json.loads(finish.read_text())
    return record["model_sha256"] == sha256(model) and record["manifest_sha256"] == sha256(manifest)


def status(state: str, job=None, detail=None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "final_queue_status.json"
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps({"status": state, "job": job, "detail": detail,
                                     "unix_time": time.time(),
                                     "complete_jobs": [f"{k}-{s}" for k, s in JOBS if completed(k, s)]}, indent=2) + "\n")
    temporary.replace(path)
    print(json.dumps({"status": state, "job": job, "detail": detail}), flush=True)


def wait_for_device() -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a") as stream:
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(stream, fcntl.LOCK_UN)
                return
            except BlockingIOError:
                time.sleep(30)


def main() -> None:
    for kind, seed in JOBS:
        job = f"{kind}-{seed}"
        if completed(kind, seed):
            status("skipped_completed", job)
            continue
        failures = 0
        while not completed(kind, seed):
            if shutil.disk_usage(ROOT).free < 52 * 1024**3:
                status("paused_disk_reserve", job)
                time.sleep(600)
                continue
            status("waiting_for_mps", job)
            wait_for_device()
            if completed(kind, seed):
                break
            status("running", job)
            log = OUT / "engineering" / f"final-{kind}-{seed}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            command = [str(PYTHON), str(FIT), "--model", kind, "--seed", str(seed),
                       "--device", "mps", "--workers", "2"]
            with log.open("a") as stream:
                result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            if result.returncode == 0 and completed(kind, seed):
                status("completed", job)
                break
            failures += 1
            status("retrying" if failures < 3 else "failed", job,
                   {"exit_code": result.returncode, "attempt": failures})
            if failures >= 3:
                return
            time.sleep(60)
    status("all_completed")


if __name__ == "__main__":
    main()
