"""Finite one-CPU physical-control queue; does not launch neural fits or use MPS."""

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--plan", type=Path, default=ROOT / "results/applied_study_v2/execution-plan.json"
    )
    p.add_argument("--run", action="store_true")
    a = p.parse_args()
    plan = json.loads(a.plan.read_text())
    jobs = [dict(j, status="queued") for j in plan["jobs"] if j["learner"] == "physical"]
    print(
        json.dumps(dict(jobs=len(jobs), resource="one CPU worker", neural_jobs_launched=0)),
        flush=True,
    )
    if not a.run:
        return
    out = ROOT / "results/applied_study_v2/physical-queue"
    out.mkdir(parents=True, exist_ok=True)
    lock = (out / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    sources = [
        a.plan,
        Path(__file__),
        *[
            ROOT / n
            for n in [
                "scripts/197_run_applied_physical_controls.py",
                "src/applied_physical.py",
                "scripts/185_run_applied_water.py",
                "src/applied_spatial_models.py",
                "src/applied_water.py",
                "src/applied_selection.py",
                "src/applied_change_task.py",
                "src/applied_copernicus.py",
            ]
        ],
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    state = dict(status="running", pid=os.getpid(), jobs=jobs, source_hashes=hashes)

    def save():
        state["completed"] = sum(j["status"] == "completed" for j in jobs)
        state["failed"] = sum(j["status"] == "failed" for j in jobs)
        state["total"] = len(jobs)
        state["free_gib"] = shutil.disk_usage(ROOT).free / 1024**3
        temporary = out / "progress.tmp"
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(out / "progress.json")

    for job in jobs:
        while shutil.disk_usage(ROOT).free < 52 * 1024**3:
            state["status"] = "waiting_for_storage"
            save()
            time.sleep(30)
        state["status"] = "running"
        for name, digest in hashes.items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
                state["status"] = "source_changed"
                save()
                raise RuntimeError("Source changed during queue: " + name)
        destination = ROOT / job["output"]
        if destination.exists():
            if all(
                (destination / n).exists()
                for n in ["manifest.json", "selection.json", "selected-test.json"]
            ):
                prior = json.loads((destination / "manifest.json").read_text())
                if not all(
                    hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == v
                    for name, v in prior["source_hashes"].items()
                ):
                    raise ValueError(
                        "Existing output source hashes differ; preserve and version the run"
                    )
                job["status"] = "completed"
                job["reused"] = True
                save()
                continue
            job["status"] = "failed"
            job["error"] = "Incomplete existing directory retained; no overwrite"
            save()
            continue
        job["status"] = "running"
        job["started_unix"] = time.time()
        save()
        env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        with (out / f"{job['id']}.log").open("ab") as stream:
            process = subprocess.Popen(
                job["command"], cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT
            )
            job["pid"] = process.pid
            save()
            code = process.wait()
        job.update(
            status="completed" if code == 0 else "failed", returncode=code, ended_unix=time.time()
        )
        save()
    state["status"] = "completed" if not state["failed"] else "completed_with_failures"
    save()


if __name__ == "__main__":
    main()
