"""Four CPU Copernicus profiles now; three MPS U-Nets after protected queues.

One profile subprocess at a time. Preserve original nine-job controller and all
source hashes. No neural scientific fitting grid is launched by this controller.
"""

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
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    out = ROOT / "results/applied_study_v2/supplemental-profile-queue"
    out.mkdir(parents=True, exist_ok=True)
    lock = (out / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (out / "progress.json").exists() and not args.resume:
        raise FileExistsError("Preserve previous controller receipt")
    jobs = [
        dict(
            task="copernicus",
            learner=learner,
            device="cpu",
            batch=2,
            runtime="copernicus",
            status="queued",
        )
        for learner in ["native", "unet", "linear", "unet_standard"]
    ]
    jobs += [
        dict(task=t, learner="unet_standard", device="mps", batch=b, runtime=r, status="queued")
        for t, b, r in [
            ("terramind", 8, "spatial"),
            ("galileo", 64, "galileo"),
            ("prithvi", 2, "spatial"),
        ]
    ]
    sources = [
        Path(__file__),
        ROOT / "scripts/202_profile_applied_supplements.py",
        ROOT / "src/applied_unet.py",
        ROOT / "src/applied_evaluation.py",
        ROOT / "scripts/185_run_applied_water.py",
        ROOT / "src/applied_water.py",
        ROOT / "src/applied_spatial_models.py",
        ROOT / "src/applied_change_task.py",
        ROOT / "src/applied_copernicus.py",
    ]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    if args.resume:
        previous = json.loads((out / "progress.json").read_text())
        try:
            os.kill(previous["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("Previous controller still alive")
        if any(j["status"] == "running" for j in previous["jobs"]):
            raise RuntimeError("Inspect unfinished child before resuming")
        for path, digest in previous["source_hashes"].items():
            if Path(path) != Path(__file__) and hashes[path] != digest:
                raise ValueError("Profile input changed; version outputs instead")
        jobs = previous["jobs"]
        (out / f"previous-controller-{previous['pid']}.json").write_text(
            json.dumps(previous, indent=2)
        )
    state = dict(status="running", pid=os.getpid(), jobs=jobs, source_hashes=hashes)

    def save():
        state["free_gib"] = shutil.disk_usage(ROOT).free / 1024**3
        temporary = out / "progress.tmp"
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(out / "progress.json")

    for job in jobs:
        if job["status"] == "completed":
            continue
        while True:
            prior = json.loads(
                (ROOT / "results/applied_study_v1/profile_queue/progress.json").read_text()
            )
            owner = json.loads(
                (ROOT / "results/limburg_individual_experiments_v1/queue/progress.json").read_text()
            )
            busy = any(
                t.get("status") == "running" and t.get("resource") == "mps"
                for t in owner["tasks"].values()
            )
            profiles_done = prior["status"] in ["complete", "complete_with_failures"]
            if state.get("free_gib", shutil.disk_usage(ROOT).free / 1024**3) >= 55 and (
                job["device"] == "cpu" or (not busy and profiles_done)
            ):
                break
            state["status"] = "waiting_for_device_or_storage"
            save()
            time.sleep(30)
        for path, digest in hashes.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Queued source changed: " + path)
        cmd = [
            str(ROOT / f".venvs-applied/{job['runtime']}/bin/python"),
            "-u",
            "scripts/202_profile_applied_supplements.py",
            "--task",
            job["task"],
            "--learner",
            job["learner"],
            "--device",
            job["device"],
            "--batch-size",
            str(job["batch"]),
        ]
        with (out / f"{job['task']}-{job['learner']}.log").open("ab") as stream:
            proc = subprocess.Popen(
                cmd,
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                env=dict(
                    os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1"
                ),
            )
            job.update(status="running", pid=proc.pid)
            state["status"] = "profiling"
            save()
            code = proc.wait()
        job.update(status="completed" if code == 0 else "failed", returncode=code)
        save()
    state["status"] = (
        "complete" if all(j["status"] == "completed" for j in jobs) else "complete_with_failures"
    )
    save()


if __name__ == "__main__":
    main()
