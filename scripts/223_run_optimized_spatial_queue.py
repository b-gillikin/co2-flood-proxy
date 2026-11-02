"""Supervise two CPU queues and one exclusive MPS queue; publish global progress.

Each lane retains the existing durable fit→local→verified-backup state machine.
The GPU lane waits for inherited device ownership instead of killing that fit.
"""

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_execution import atomic, sha


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, TypeError):
        return False


def controller_exit_is_failure(child, state):
    if child.returncode is None or state.get("status") in {
        "complete",
        "complete_with_recorded_failures",
    }:
        return False
    owner = state.get("controller_pid")
    return not (owner != child.pid and alive(owner))


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--plan", type=Path, default=ROOT / "results/applied_study_v4/execution-plan.json"
    )
    p.add_argument("--run", action="store_true")
    a = p.parse_args()
    if not a.run:
        p.error("Choose --run")
    base = a.plan.parent
    lock = (base / ".supervisor.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan = json.loads(a.plan.read_text())
    for name, digest in plan["source_hashes"].items():
        if sha(ROOT / name) != digest:
            raise ValueError("Source changed before launch: " + name)
    children = {}
    for lane in ["cpu-0", "cpu-1", "mps"]:
        progress = base / lane / "queue/progress.json"
        held = json.loads(progress.read_text()) if progress.exists() else {}
        if held.get("status") in ["complete", "complete_with_recorded_failures"] or alive(
            held.get("controller_pid")
        ):
            continue
        with (base / f"{lane}-controller.log").open("ab") as log:
            children[lane] = subprocess.Popen(
                [
                    sys.executable,
                    "scripts/214_queue_spatial_comparisons.py",
                    "--plan",
                    str(base / lane / "execution-plan.json"),
                    "--run",
                    "--no-analysis",
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    atomic(
        ROOT / "results/applied_study_v3/current-queue.json",
        dict(
            plan=str(a.plan.relative_to(ROOT)),
            progress=str((base / "progress.json").relative_to(ROOT)),
            reason="Versioned cached/batched three-lane full-grid execution; v3 supporting runs retained",
        ),
    )
    analysis = None
    last_readout = 0.0
    last_count = -1
    while True:
        lanes = {}
        jobs = {}
        for lane in ["cpu-0", "cpu-1", "mps"]:
            f = base / lane / "queue/progress.json"
            state = json.loads(f.read_text()) if f.exists() else dict(status="starting")
            lanes[lane] = {
                k: state.get(k)
                for k in [
                    "status",
                    "actor",
                    "archiver",
                    "waiting_reason",
                    "neural_completed",
                    "neural_total",
                    "controller_pid",
                ]
            }
            if (
                lane in children
                and children[lane].poll() is not None
                and state.get("status") not in ["complete", "complete_with_recorded_failures"]
            ):
                if controller_exit_is_failure(children[lane], state):
                    lanes[lane]["controller_exitcode"] = children[lane].returncode
                    lanes[lane]["status"] = "controller_exited_inspect_log"
                else:
                    children.pop(lane)  # A live locked controller owns the lane; attach.
            jobs.update(
                {
                    k: v
                    for k, v in state.get("jobs", {}).items()
                    if not v.get("reused_audited_physical")
                }
            )
        done = sum(r.get("status") == "completed" for r in jobs.values())
        failed = sum(r.get("status") == "failed" for r in jobs.values())
        total = plan["neural_tuning_jobs"]
        terminal = all(
            s.get("status") in ["complete", "complete_with_recorded_failures"]
            for s in lanes.values()
        )
        halted = any("controller_exitcode" in s for s in lanes.values())
        status = (
            "complete_with_recorded_failures"
            if terminal
            and any(s.get("status") == "complete_with_recorded_failures" for s in lanes.values())
            else "complete"
            if terminal
            else "attention_required"
            if halted
            else "running"
        )
        atomic(
            base / "progress.json",
            dict(
                status=status,
                controller_pid=os.getpid(),
                lanes=lanes,
                jobs=jobs,
                neural_total=total,
                candidate_fits=plan["neural_candidate_fits"],
                neural_completed=done,
                neural_failed=failed,
                percent_completed=100 * done / total,
                free_gib=shutil.disk_usage(ROOT).free / 1024**3,
                updated_unix=time.time(),
                note="Whole-event census retained; seed repeats reuse validation tuning only on identical annotation masks.",
            ),
        )
        if analysis is not None and analysis.poll() is not None:
            analysis = None
        if (
            not terminal
            and analysis is None
            and done != last_count
            and time.time() - last_readout >= 1200
        ):
            target = base / "synthesis" / f"completed-{done:04d}-{time.time_ns()}"
            with (base / "readout.log").open("ab") as log:
                analysis = subprocess.Popen(
                    [
                        str(ROOT / ".venv-foundation/bin/python"),
                        "scripts/217_update_spatial_readout.py",
                        "--plan",
                        str(a.plan),
                        "--output",
                        str(target),
                    ],
                    cwd=ROOT,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            last_readout, last_count = time.time(), done
        if terminal:
            if analysis is not None:
                analysis.wait()
            subprocess.run(
                [
                    str(ROOT / ".venv-foundation/bin/python"),
                    "scripts/217_update_spatial_readout.py",
                    "--plan",
                    str(a.plan),
                    "--output",
                    str(base / "synthesis/final"),
                ],
                cwd=ROOT,
                check=True,
            )
            break
        time.sleep(10)


if __name__ == "__main__":
    main()
