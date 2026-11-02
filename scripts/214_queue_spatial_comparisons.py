"""Durable full-census spatial queue: one MPS fit/application and one offload.

Resume attaches to surviving children; it never resets a running fit to pending.
No epoch resume or silent retry of failed/incomplete scientific runs. Source
versions and all planned folds/labels/seeds remain in the ledger.
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
from applied_execution import atomic, retire_verified_checkpoints, sha

AZPY = Path("/opt/homebrew/Cellar/azure-cli/2.83.0/libexec/bin/python")


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, TypeError):
        return False


def spawn(command, log):
    with log.open("ab") as stream:
        child = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=stream,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=dict(
                os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1"
            ),
        )
    return child


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--run", action="store_true")
    p.add_argument("--status", action="store_true")
    a = p.parse_args()
    out = a.plan.parent / "queue"
    if a.status:
        print((out / "progress.json").read_text())
        return
    if not a.run:
        p.error("Choose --run or --status")
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    (out / "recovery").mkdir(exist_ok=True)
    lock = (out / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan = json.loads(a.plan.read_text())
    jobs = {j["id"]: j for j in plan["jobs"]}
    for j in jobs.values():
        if j["learner"] != "physical" and not (ROOT / j["output"]).resolve().is_relative_to(
            (ROOT / "results/applied_study_v3/tuning").resolve()
        ):
            raise ValueError("Fit/cleanup output escapes this chapter's dedicated run directory")
    statepath = out / "progress.json"
    if statepath.exists():
        state = json.loads(statepath.read_text())
        if state["plan_sha256"] != sha(a.plan):
            raise ValueError("Changed plan; version rather than rewrite queue")
    else:
        statuses = {}
        for key, j in jobs.items():
            if j["learner"] == "physical":
                result = ROOT / j["output"] / "selected-test.json"
                if not result.exists():
                    raise ValueError("Missing already-audited physical control")
                statuses[key] = dict(
                    status="completed", reused_audited_physical=True, result_sha256=sha(result)
                )
            else:
                statuses[key] = dict(status="pending", phase="fit", output=j["output"])
        state = dict(
            plan_sha256=sha(a.plan),
            jobs=statuses,
            actor=None,
            archiver=None,
            source_hashes=plan["source_hashes"],
            started_unix=time.time(),
        )
    state["controller_pid"] = os.getpid()
    state["status"] = "running"
    processes = {}
    snapshot = out / "source-snapshot"
    for name, digest in plan["source_hashes"].items():
        if sha(ROOT / name) != digest:
            raise ValueError("Source drift before launch: " + name)
        target = snapshot / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        if sha(target) != digest:
            raise ValueError("Source snapshot changed")
    for task, digest in plan["cache_index_hashes"].items():
        if sha(ROOT / plan["cache_paths"][task] / "index.json") != digest:
            raise ValueError("Cache index changed")
    inhibitor = (
        subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
        if shutil.which("caffeinate")
        else None
    )

    def save():
        values = [r for k, r in state["jobs"].items() if jobs[k]["learner"] != "physical"]
        state.update(
            free_gib=shutil.disk_usage(ROOT).free / 1024**3,
            neural_total=len(values),
            neural_completed=sum(r["status"] == "completed" for r in values),
            neural_failed=sum(r["status"] == "failed" for r in values),
            neural_running=sum(r["status"] == "running" for r in values),
            updated_unix=time.time(),
        )
        atomic(statepath, state)

    def launch_actor(key, phase):
        j = jobs[key]
        r = state["jobs"][key]
        d = ROOT / j["output"]
        py = j["command"][0]
        if phase == "fit":
            command = j["command"]
        elif phase == "local":
            command = [py, "scripts/215_apply_local_spatial_models.py", str(d)]
        else:
            command = [py, "scripts/215_apply_local_spatial_models.py", str(d), "--physical"]
        log = out / "logs" / f"{key}-{phase}.log"
        child = spawn(command, log)
        processes[child.pid] = child
        state["actor"] = dict(
            job=key,
            phase=phase,
            pid=child.pid,
            command=command,
            log=str(log.relative_to(ROOT)),
            started_unix=time.time(),
        )
        r.update(status="running", phase=phase, pid=child.pid)
        print(json.dumps(dict(event="started", job=key, phase=phase, pid=child.pid)), flush=True)

    def finish_actor(actor, code):
        key = actor["job"]
        phase = actor["phase"]
        r = state["jobs"][key]
        j = jobs[key]
        d = ROOT / j["output"]
        marker = (
            d
            / (
                {
                    "fit": "complete.json",
                    "local": "local/complete.json",
                    "physical": "local-physical/complete.json",
                }[phase]
            )
        )
        if code != 0 or not marker.exists():
            if phase == "fit":
                r.update(
                    status="failed",
                    fit_status="failed",
                    returncode=code,
                    error="See phase log; incomplete outputs preserved",
                )
            else:
                r.update(
                    status="completed",
                    local_status="failed",
                    local_error=f"{phase} failed; keep checkpoints for follow-up",
                    returncode=code,
                )
            state["actor"] = None
            return
        if phase == "fit":
            r.update(fit_status="completed", completion_sha256=sha(marker))
            if j["budget"] == 1.0:
                launch_actor(key, "local")
                return
        elif phase == "local":
            r["local_status"] = "completed"
            if j["learner"] == "linear" and j["seed"] == 42:
                launch_actor(key, "physical")
                return
        r.update(status="completed", completed_unix=time.time())
        state["actor"] = None
        print(json.dumps(dict(event="completed", job=key)), flush=True)

    try:
        while True:
            for name, digest in plan["source_hashes"].items():
                if sha(ROOT / name) != digest:
                    state.update(
                        status="source_change_requires_versioned_reconciliation", error=name
                    )
                    save()
                    return
            actor = state.get("actor")
            if actor:
                pid = actor["pid"]
                child = processes.get(pid)
                code = child.poll() if child else None
                if (child and code is not None) or (not child and not alive(pid)):
                    # A detached surviving child may finish while its controller
                    # restarts. Its completion marker, not an invented exit code,
                    # determines recovery success.
                    if child is None:
                        code = 0
                    finish_actor(actor, code)
            arch = state.get("archiver")
            if arch:
                child = processes.get(arch["pid"])
                code = child.poll() if child else None
                if (child and code is not None) or (not child and not alive(arch["pid"])):
                    r = state["jobs"][arch["job"]]
                    receipt = Path(arch["receipt"])
                    d = ROOT / r["output"]
                    if (code in [0, None]) and receipt.exists():
                        r["recovery_receipt"] = str(receipt.relative_to(ROOT))
                        r["offload_status"] = "verified"
                        if r.get("local_status") != "failed":
                            r["retired_checkpoints"] = retire_verified_checkpoints(d, receipt)
                        remote = json.loads(receipt.read_text())
                        atomic(
                            d / "remote-recovery.json",
                            {k: v for k, v in remote.items() if k != "inventory"},
                        )
                        for field in ["local_bundle", "restored_readback"]:
                            path = Path(remote[field]).resolve()
                            if path.is_relative_to((out / "recovery").resolve()):
                                path.unlink(missing_ok=True)
                    else:
                        r.update(
                            offload_status="failed",
                            offload_error="Preserve local files; read archive log",
                        )
                    state["archiver"] = None
            if state.get("archiver") is None:
                ready = next(
                    (
                        k
                        for k, r in state["jobs"].items()
                        if jobs[k]["learner"] != "physical"
                        and r["status"] == "completed"
                        and "offload_status" not in r
                    ),
                    None,
                )
                if ready:
                    bundle = out / "recovery" / f"{ready}.tar.gz"
                    command = [
                        str(AZPY),
                        "scripts/207_preserve_applied_results.py",
                        "--include",
                        jobs[ready]["output"],
                        "--include",
                        str(out / "logs" / f"{ready}-fit.log"),
                        "--output",
                        str(bundle),
                    ]
                    child = spawn(command, out / "logs" / f"{ready}-offload.log")
                    processes[child.pid] = child
                    state["archiver"] = dict(
                        job=ready, pid=child.pid, receipt=str(bundle.with_suffix(".recovery.json"))
                    )
                    state["jobs"][ready]["offload_status"] = "running"
            analysis = state.get("analysis_worker")
            if analysis:
                child = processes.get(analysis["pid"])
                code = child.poll() if child else None
                if (child and code is not None) or (not child and not alive(analysis["pid"])):
                    state["last_analysis_neural_completed"] = analysis["completed_count"]
                    state["last_analysis_output"] = analysis["output"]
                    state["last_analysis_status"] = (
                        "completed"
                        if code in [0, None]
                        and (ROOT / analysis["output"] / "local/ledger.json").exists()
                        else "failed"
                    )
                    state["analysis_worker"] = None
            completed_count = sum(
                r["status"] == "completed"
                for k, r in state["jobs"].items()
                if jobs[k]["learner"] != "physical"
            )
            if (
                state.get("analysis_worker") is None
                and state.get("last_analysis_neural_completed", -1) != completed_count
            ):
                target = (
                    a.plan.parent
                    / "synthesis"
                    / f"completed-{completed_count:04d}-{time.time_ns()}"
                )
                command = [
                    str(ROOT / ".venv-foundation/bin/python"),
                    "scripts/217_update_spatial_readout.py",
                    "--plan",
                    str(a.plan),
                    "--output",
                    str(target),
                ]
                child = spawn(command, out / "logs" / f"synthesis-{completed_count:04d}.log")
                processes[child.pid] = child
                state["analysis_worker"] = dict(
                    pid=child.pid,
                    completed_count=completed_count,
                    output=str(target.relative_to(ROOT)),
                )
            if state.get("actor") is None:
                pending = next(
                    (k for k, r in state["jobs"].items() if r["status"] == "pending"), None
                )
                if pending and shutil.disk_usage(ROOT).free >= 55 * 1024**3:
                    launch_actor(pending, "fit")
                elif pending:
                    state["waiting_reason"] = (
                        "50GiB reserve plus5GiB working headroom; verified offload pending"
                    )
                elif state.get("archiver") is None and state.get("analysis_worker") is None:
                    state["status"] = (
                        "complete_with_recorded_failures"
                        if any(
                            r["status"] == "failed"
                            or r.get("local_status") == "failed"
                            or r.get("offload_status") == "failed"
                            for r in state["jobs"].values()
                        )
                        else "complete"
                    )
                    save()
                    break
            save()
            time.sleep(5)
    finally:
        if inhibitor:
            inhibitor.terminate()


if __name__ == "__main__":
    main()
