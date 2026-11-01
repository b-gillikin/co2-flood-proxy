"""Run native spatial engineering profiles after the current MPS owner exits.

One foreground subprocess at a time. This finite queue does not silently
submit hundreds of fitted comparisons: it measures the full-epoch time and
memory first, and writes the extrapolation inputs for the scientific run.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/applied_study_v1/profile_queue"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    jobs = []
    for task, runtime, batch in [
        ("terramind", "spatial", 8),
        ("galileo", "galileo", 64),
        ("prithvi", "spatial", 2),
    ]:
        for learner in ["native", "unet", "linear"]:
            jobs.append(
                dict(task=task, runtime=runtime, batch_size=batch, learner=learner, status="queued")
            )
    sources = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in [
            "scripts/185_run_applied_water.py",
            "src/applied_spatial_models.py",
            "src/applied_water.py",
        ]
    }
    progress = dict(
        status="waiting_for_current_mps",
        controller_pid=os.getpid(),
        source_hashes=sources,
        jobs=jobs,
    )

    def save():
        progress["free_gib"] = shutil.disk_usage(ROOT).free / 1024**3
        (OUT / "progress.json").write_text(json.dumps(progress, indent=2) + "\n")

    save()
    for job in jobs:
        while True:
            existing = json.loads(
                (ROOT / "results/limburg_individual_experiments_v1/queue/progress.json").read_text()
            )
            cache = ROOT / "data/processed/limburg_applied_galileo_spatial_v1/index.json"
            cache_ready = (
                job["task"] != "galileo"
                or job["learner"] != "native"
                or (cache.exists() and json.loads(cache.read_text()).get("status") == "completed")
            )
            alive = []
            for k, t in existing["tasks"].items():
                if t["status"] == "running" and t.get("resource") == "mps":
                    # A stale status file cannot be used to claim an active
                    # device owner has finished; keep waiting in that case.
                    alive.append(k)
            if not alive and progress.get("free_gib", 0) >= 55 and cache_ready:
                break
            progress.update(
                status="waiting_for_current_mps"
                if alive
                else "waiting_for_spatial_cache"
                if not cache_ready
                else "waiting_for_storage",
                current_device_owners=alive,
            )
            save()
            time.sleep(30)
        for name, digest in sources.items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Task source changed while queued: " + name)
        log = OUT / f"{job['task']}-{job['learner']}.log"
        cmd = [
            str(ROOT / ".venvs-applied" / job["runtime"] / "bin/python"),
            "-u",
            "scripts/185_run_applied_water.py",
            "--task",
            job["task"],
            "--learner",
            job["learner"],
            "--device",
            "mps",
            "--mode",
            "profile",
            "--batch-size",
            str(job["batch_size"]),
            "--profile-batches",
            "0",
        ]
        if job["task"] == "galileo" and job["learner"] == "native":
            cmd.extend(
                ["--feature-cache", str(ROOT / "data/processed/limburg_applied_galileo_spatial_v1")]
            )
        with log.open("ab") as stream:
            worker = subprocess.Popen(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            job.update(
                status="running",
                pid=worker.pid,
                log=str(log.relative_to(ROOT)),
                started_unix=time.time(),
            )
            progress["status"] = "profiling"
            save()
            code = worker.wait()
        job.update(
            status="completed" if code == 0 else "failed", returncode=code, ended_unix=time.time()
        )
        save()
        # A failing model does not prevent independent tasks from being checked.
    progress["status"] = (
        "complete" if all(j["status"] == "completed" for j in jobs) else "complete_with_failures"
    )
    progress["next"] = (
        "Review native full-epoch profiles, measured cost and unresolved Copernicus portability before scheduling fitted comparison grid; no mapping findings yet"
    )
    save()


if __name__ == "__main__":
    main()
