"""Resumable local DAG: one MPS worker, at most two CPU workers, no cloud.

--run starts the authorized primary experiments and declared matched ablations.
No outcome-dependent queue ordering or model-winner stopping rule is used.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "PROJ_DATA", str((ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj")
)
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256

OUT = ROOT / "results/limburg_individual_experiments_v1"
QUEUE = OUT / "queue"
MODELS = {
    "anysat": ("modern", "mps"),
    "prithvi": ("modern", "mps"),
    "olmoearth": ("modern", "mps"),
    "croma": ("modern", "mps"),
    "galileo": ("galileo", "mps"),
    "presto": ("presto-torch291", "cpu"),
    "satmae": (None, "cpu"),
    "dofa": (None, "cpu"),
    "copernicus_fm": ("legacy", "cpu"),
    "terramind": ("terramind", "cpu"),
}
ABLATIONS = {"presto", "anysat", "galileo", "prithvi", "copernicus_fm", "terramind"}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_name(path.name + f".{os.getpid()}.tmp")
    stage.write_text(json.dumps(value, indent=2) + "\n")
    stage.replace(path)


def task_graph():
    foundation = str(ROOT / ".venv-foundation/bin/python")
    tasks = {
        "preflight": dict(
            command=[foundation, "-u", str(Path(__file__).resolve()), "--preflight"],
            resource="cpu",
            dependencies=[],
            priority=0,
        )
    }
    for rank, (model, (runtime, device)) in enumerate(MODELS.items()):
        python = str(
            ROOT / (f".venvs-eo/{runtime}/bin/python" if runtime else ".venv-foundation/bin/python")
        )
        for phase in ["smoke", "benchmark", "extract"]:
            key = phase + "_" + model
            dependencies = (
                ["preflight"]
                if phase == "smoke"
                else ["smoke_" + model]
                if phase == "benchmark"
                else ["benchmark_" + model]
            )
            flag = {"smoke": "--smoke", "benchmark": "--benchmark", "extract": "--run"}[phase]
            tasks[key] = dict(
                command=[
                    python,
                    "-u",
                    str(ROOT / "scripts/170_extract_individual_features.py"),
                    "--model",
                    model,
                    "--device",
                    device,
                    flag,
                ],
                resource=device,
                dependencies=dependencies,
                priority={"smoke": 1, "benchmark": 2, "extract": 4}[phase] + rank / 100,
                model=model,
                phase=phase,
            )
        scenario_jobs = []
        for scenario in ["local_q_absent", "rich_basin", "all_q_absent"]:
            key = f"score_{model}__{scenario}"
            tasks[key] = dict(
                command=[
                    foundation,
                    "-u",
                    str(ROOT / "scripts/171_run_individual_heads.py"),
                    "--model",
                    model,
                    "--scenario",
                    scenario,
                ],
                resource="cpu",
                dependencies=["extract_" + model],
                priority=3 + rank / 100,
                model=model,
                phase="score",
            )
            if not (model == "dofa" and scenario == "rich_basin"):
                review = f"review_{model}__{scenario}"
                tasks[review] = dict(
                    command=[
                        foundation,
                        "-u",
                        str(ROOT / "scripts/172_review_individual_experiments.py"),
                        "--job",
                        model + "__" + scenario,
                    ],
                    resource="cpu",
                    dependencies=[key],
                    priority=3.5 + rank / 100,
                    model=model,
                    phase="review",
                )
                scenario_jobs.append(review)
        if model in ABLATIONS:
            key = "ablation_" + model
            tasks[key] = dict(
                command=[
                    foundation,
                    "-u",
                    str(ROOT / "scripts/171_run_individual_heads.py"),
                    "--model",
                    model,
                    "--scenario",
                    "local_q_absent",
                    "--ablation",
                ],
                resource="cpu",
                dependencies=scenario_jobs,
                priority=5 + rank / 100,
                model=model,
                phase="ablation",
            )
            tasks["review_ablation_" + model] = dict(
                command=[
                    foundation,
                    "-u",
                    str(ROOT / "scripts/172_review_individual_experiments.py"),
                    "--job",
                    model + "__local_q_absent__ablation",
                ],
                resource="cpu",
                dependencies=[key],
                priority=5.5 + rank / 100,
                model=model,
                phase="review",
            )
    tasks["review_all"] = dict(
        command=[foundation, "-u", str(ROOT / "scripts/172_review_individual_experiments.py")],
        resource="cpu",
        dependencies=[k for k in tasks if k.startswith(("review_", "score_"))],
        priority=6,
        phase="review",
    )
    return tasks


def eligible_tasks(tasks, states, running):
    active = {
        resource: sum(tasks[k]["resource"] == resource for k in running)
        for resource in ["cpu", "mps"]
    }
    free = dict(cpu=2 - active["cpu"], mps=1 - active["mps"])
    chosen = []
    for key in sorted(tasks, key=lambda k: (tasks[k]["priority"], k)):
        if states.get(key, {}).get("status", "pending") != "pending":
            continue
        if not all(
            states.get(d, {}).get("status") == "completed" for d in tasks[key]["dependencies"]
        ):
            continue
        resource = tasks[key]["resource"]
        if free[resource] > 0:
            chosen.append(key)
            free[resource] -= 1
    return chosen


def freeze_sources():
    paths = [
        *sorted((ROOT / "src").glob("eo_individual*.py")),
        *sorted((ROOT / "scripts").glob("17[0-3]_*.py")),
        ROOT / "scripts/168_prepare_individual_experiments.py",
        ROOT / "config/limburg_individual_encoder_experiments_v1.json",
        ROOT / "src/eo_experiment_readiness.py",
        ROOT / "src/scarcity.py",
        ROOT / "scripts/162_review_scarcity.py",
        ROOT / "tests/test_eo_individual_core.py",
    ]
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths}


def preflight():
    # Actual canonical bank/output verification, not manifest presence alone.
    plan = json.loads((ROOT / "config/limburg_individual_encoder_experiments_v1.json").read_text())
    prep = ROOT / plan["shared"]["source"] / "preparation"
    source = json.loads((prep / "manifest.json").read_text())
    for name, h in source["outputs_sha256"].items():
        p = prep / name if (prep / name).exists() else ROOT / name
        assert sha256(p) == h, f"Canonical data changed: {name}"
    refs = OUT / "preparation"
    manifest = json.loads((refs / "manifest.json").read_text())
    for name, h in manifest["outputs"].items():
        assert sha256(refs / name) == h
    proof_path = OUT / "readiness/shared_backbone_validated.json"
    if proof_path.exists():
        proof = json.loads(proof_path.read_text())
        if (
            proof.get("status") == "validated"
            and proof.get("test_scope") == "full_repository_suite"
            and proof.get("source_hashes") == freeze_sources()
            and proof.get("canonical_output_hashes") == source["outputs_sha256"]
            and proof.get("reference_output_hashes") == manifest["outputs"]
        ):
            print(
                "Verified unchanged full-suite proof and all canonical outputs; no repeated tests",
                flush=True,
            )
            return
    command = [
        str(ROOT / ".venv-foundation/bin/python"),
        "-m",
        "pytest",
        "-q",
    ]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, flush=True)
    result.check_returncode()
    atomic_json(
        OUT / "readiness/shared_backbone_validated.json",
        dict(
            status="validated",
            test_scope="full_repository_suite",
            source_hashes=freeze_sources(),
            canonical_output_hashes=source["outputs_sha256"],
            reference_output_hashes=manifest["outputs"],
            test_command=command,
            test_output=result.stdout,
            conventional_replay=json.loads((refs / "baseline-audit.json").read_text()),
        ),
    )


def after_task(key, task):
    if task.get("phase") != "benchmark":
        return
    model = task["model"]
    path = OUT / "features" / model
    bench = json.loads((path / "benchmark.json").read_text())
    identity = json.loads((path / "identity.json").read_text())
    smokes = list((OUT / "engineering" / model).glob("*/smoke.json"))
    smoke = next(
        p for p in smokes if json.loads(p.read_text())["fingerprint"] == bench["fingerprint"]
    )
    assert bench["status"] == "completed" and bench["contexts"] == 1
    assert bench["projected_compact_gib"] < shutil.disk_usage(ROOT).free / 1024**3, (
        "Measured output exceeds available storage; preserve results and reassess storage"
    )
    atomic_json(
        OUT / f"readiness/{model}_contract_and_benchmark.json",
        dict(
            status="validated",
            source_hashes={
                str(p.relative_to(ROOT)): sha256(p)
                for p in [path / "benchmark.json", path / "identity.json", smoke]
            },
            fingerprint=identity["fingerprint"],
            projection_gib=bench["projected_compact_gib"],
            peak_rss_gib=bench["peak_rss_gib"],
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        preflight()
        return
    state_path = QUEUE / "progress.json"
    if args.status:
        print(state_path.read_text() if state_path.exists() else "Not launched")
        return
    QUEUE.mkdir(parents=True, exist_ok=True)
    lock = (QUEUE / ".lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    tasks = task_graph()
    sources = freeze_sources()
    fingerprint = hashlib.sha256(
        json.dumps(dict(tasks=tasks, sources=sources), sort_keys=True).encode()
    ).hexdigest()
    state = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else dict(
            fingerprint=fingerprint,
            source_hashes=sources,
            tasks={},
            started_utc=datetime.now(timezone.utc).isoformat(),
        )
    )
    assert state["fingerprint"] == fingerprint, (
        "Queue code/design changed. Version or explicitly reconcile before resuming."
    )
    states = state["tasks"]
    for value in states.values():
        if value["status"] == "running" or (
            args.retry_failed and value["status"] in ["failed", "dependency_failed"]
        ):
            value["status"] = "pending"
    active = {}
    state["controller_pid"] = os.getpid()
    state.setdefault(
        "git_commit_at_launch",
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    )
    log_root = ROOT / "logs/individual-experiments-v1"
    log_root.mkdir(parents=True, exist_ok=True)

    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"Controller signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    sleep_inhibitor = (
        subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
        if shutil.which("caffeinate")
        else None
    )
    try:
        while True:
            assert freeze_sources() == sources, (
                "Source drift detected; preserve work, resume with versioned code"
            )
            for key, (process, stream, began) in list(active.items()):
                code = process.poll()
                if code is None:
                    continue
                stream.close()
                value = states[key]
                value.update(
                    status="completed" if code == 0 else "failed",
                    returncode=code,
                    elapsed_s=time.time() - began,
                )
                if code == 0:
                    try:
                        after_task(key, tasks[key])
                    except Exception as error:
                        value.update(status="failed", error=repr(error))
                print(key, value["status"], flush=True)
                del active[key]
            for key, task in tasks.items():
                if states.get(key, {}).get("status", "pending") == "pending" and any(
                    states.get(d, {}).get("status") in ["failed", "dependency_failed"]
                    for d in task["dependencies"]
                ):
                    states[key] = dict(
                        status="dependency_failed",
                        reason="Required engineering/data computation failed; other independent models continue",
                    )
            for key in eligible_tasks(tasks, states, active):
                env = os.environ.copy()
                env.update(
                    OPENBLAS_NUM_THREADS="2",
                    OMP_NUM_THREADS="2",
                    MKL_NUM_THREADS="2",
                    VECLIB_MAXIMUM_THREADS="2",
                    PROJ_DATA=str(
                        (ROOT / ".venv-foundation/bin/python").resolve().parents[1] / "share/proj"
                    ),
                )
                stream = (log_root / (key + ".log")).open("a")
                process = subprocess.Popen(
                    tasks[key]["command"],
                    cwd=ROOT,
                    env=env,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                )
                active[key] = (process, stream, time.time())
                states[key] = dict(
                    status="running",
                    pid=process.pid,
                    resource=tasks[key]["resource"],
                    log=str((log_root / (key + ".log")).relative_to(ROOT)),
                    started_utc=datetime.now(timezone.utc).isoformat(),
                )
                print(key, "started", process.pid, flush=True)
            terminal = all(
                states.get(k, {}).get("status") in ["completed", "failed", "dependency_failed"]
                for k in tasks
            )
            state.update(
                status="completed"
                if terminal and all(states[k]["status"] == "completed" for k in tasks)
                else "finished_with_failures"
                if terminal
                else "running",
                tasks_total=len(tasks),
                tasks_done=sum(v["status"] == "completed" for v in states.values()),
                disk_free_gib=shutil.disk_usage(ROOT).free / 1024**3,
                updated_utc=datetime.now(timezone.utc).isoformat(),
                supporting_mask_replay="not_launched; primary checks first",
            )
            atomic_json(state_path, state)
            if terminal:
                return
            time.sleep(5)
    except BaseException as error:
        state.update(
            status="interrupted" if isinstance(error, KeyboardInterrupt) else "controller_error",
            error=repr(error),
            updated_utc=datetime.now(timezone.utc).isoformat(),
        )
        for key in active:
            states[key]["status"] = "pending"
        atomic_json(state_path, state)
        raise
    finally:
        if sleep_inhibitor is not None:
            sleep_inhibitor.terminate()
        # A controller interruption must not leave invisible orphan workers.
        for process, stream, _ in active.values():
            process.terminate()
            process.wait()
            stream.close()


if __name__ == "__main__":
    main()
