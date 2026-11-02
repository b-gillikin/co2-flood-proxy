"""Prepare matching physical controls, start GPU, then reuse freed CPU slots.

Existing supporting fits are allowed to finish. No source rasters or frozen
features are regenerated; new grouped fits use separate output directories.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_execution import atomic, sha


def predecessor_active(pid):
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True
    )
    return result.returncode == 0 and "192_tune_applied_water.py" in result.stdout


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--cpu-predecessor", action="append", type=int, default=[])
    p.add_argument("--run", action="store_true")
    a = p.parse_args()
    if not a.run:
        p.error("Choose --run")
    base = a.plan.parent
    out = base / "preparation"
    out.mkdir(exist_ok=True)
    plan = json.loads(a.plan.read_text())
    for name, digest in plan["source_hashes"].items():
        if sha(ROOT / name) != digest:
            raise ValueError("Source changed before preparation: " + name)
    physical = [j for j in plan["jobs"] if j["learner"] == "physical"]
    status = dict(
        status="preparing_grouped_physical_controls",
        controller_pid=os.getpid(),
        neural_total=plan["neural_tuning_jobs"],
        neural_completed=0,
        candidate_fits=plan["neural_candidate_fits"],
        physical_total=len(physical),
        physical_completed=0,
        cpu_predecessors=a.cpu_predecessor,
    )
    atomic(out / "progress.json", status)
    atomic(
        ROOT / "results/applied_study_v3/current-queue.json",
        dict(
            plan=str(a.plan.relative_to(ROOT)),
            progress=str((out / "progress.json").relative_to(ROOT)),
            reason="Five-fold whole-event census; matching physical controls and orderly worker transition",
        ),
    )
    for job in physical:
        directory = ROOT / job["output"]
        if not (directory / "selected-test.json").exists():
            with (out / f"{job['id']}.log").open("ab") as log:
                result = subprocess.run(
                    job["command"],
                    cwd=ROOT,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"),
                )
            if result.returncode:
                status.update(
                    status="physical_control_failed",
                    failed_job=job["id"],
                    returncode=result.returncode,
                )
                atomic(out / "progress.json", status)
                raise RuntimeError("Keep partial outputs; inspect physical log " + job["id"])
        manifest = json.loads((directory / "manifest.json").read_text())
        name = "radar-change" if job["task"] == "copernicus" else "sen1"
        foldpath = ROOT / plan["evaluation_directory"] / f"{name}-grouped-folds.parquet"
        if manifest["source_hashes"][str(foldpath.relative_to(ROOT))] != sha(foldpath):
            raise ValueError("Physical control uses different grouped folds")
        status["physical_completed"] += 1
        atomic(out / "progress.json", status)
    # Start the exclusive GPU lane as soon as inherited GPU ownership is free.
    with (base / "mps-controller.log").open("ab") as log:
        child = subprocess.Popen(
            [
                sys.executable,
                "scripts/214_queue_spatial_comparisons.py",
                "--plan",
                str(base / "mps/execution-plan.json"),
                "--run",
                "--no-analysis",
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    status.update(
        status="gpu_queue_started_waiting_inherited_cpu_fits", mps_controller_pid=child.pid
    )
    progress = base / "mps/queue/progress.json"
    # Publish device-controller ownership before the shared supervisor checks
    # for an existing lane. Otherwise a harmless lock-rejected duplicate can
    # briefly be mistaken for a failed queue.
    while (
        not progress.exists() or json.loads(progress.read_text()).get("controller_pid") != child.pid
    ):
        if child.poll() is not None:
            raise RuntimeError("GPU controller exited before publishing ownership")
        time.sleep(0.2)
    while any(predecessor_active(pid) for pid in a.cpu_predecessor):
        progress = base / "mps/queue/progress.json"
        if progress.exists():
            s = json.loads(progress.read_text())
            status["mps_actor"] = s.get("actor")
            status["neural_completed"] = s.get("neural_completed", 0)
        if child.poll() is not None:
            status.update(status="gpu_controller_exited", returncode=child.returncode)
            atomic(out / "progress.json", status)
            raise RuntimeError("GPU controller exited during worker transition")
        status["updated_unix"] = time.time()
        atomic(out / "progress.json", status)
        time.sleep(10)
    with (base / "supervisor.log").open("ab") as log:
        supervisor = subprocess.Popen(
            [
                sys.executable,
                "scripts/223_run_optimized_spatial_queue.py",
                "--plan",
                str(a.plan),
                "--run",
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    status.update(status="three_lane_supervisor_started", supervisor_pid=supervisor.pid)
    atomic(out / "progress.json", status)


if __name__ == "__main__":
    main()
