"""Legacy queue for in-flight extraction and repaired selected-output handoff.

Future versioned extraction uses script 118; selected finalization uses script 117.

No model fitting/scoring, sampling, cloud compute or raw-data deletion. Each
model uses its pinned runtime and full held contexts. Reruns verify/resume patches.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import merge_selected, validate_aggregate

ORDER = [
    "prithvi",
    "croma",
    "terramind",
    "dofa",
    "copernicus_fm",
    "satmae",
    "olmoearth",
    "galileo",
    "anysat",
    "presto",
]


def atomic_json(path, data):
    tmp = path.with_suffix(".json.partial")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def merge_aggregates(base, models):
    selection = json.loads((ROOT / "config/limburg_eo_selected_runs.json").read_text())
    if set(models) != set(selection["models"]):
        raise ValueError("Incomplete model set; use script 117 to inspect selected readiness")
    return merge_selected(ROOT, selection, base / "selected/census")


def completed_aggregate(base, model, device=None, runtime_profile=None):
    selection_path = ROOT / "config/limburg_eo_selected_runs.json"
    selected = (
        json.loads(selection_path.read_text())["models"].get(model)
        if selection_path.exists()
        else None
    )
    folder = ROOT / selected["aggregate"] if selected else base / "per_model" / model / "census"
    try:
        saved, identity, _ = validate_aggregate(ROOT, folder, model, selected=selected)
        if saved["catchments_sha256"] != sha256(
            ROOT / "results/eo_comparison_preparation/catchments.gpkg"
        ):
            return False
        if device is not None and identity.get("execution_device", "cpu") != device:
            return False
        if runtime_profile is not None and identity.get("runtime_profile") != runtime_profile:
            return False
        return True
    except (ValueError, KeyError, FileNotFoundError):
        return False


def execution_settings(model, device, plan):
    profile = plan.get("runtime_profiles", {}).get(model)
    if profile is not None:
        if (model, device, profile) != ("presto", "cpu", "presto-torch291-cpu4"):
            raise ValueError("Unsupported explicit runtime profile")
        return dict(
            runtime=ROOT / ".venvs-eo/presto-torch291/bin/python",
            runner="scripts/109_extract_presto_cpu_sequences.py",
            sequences=ROOT / "data/processed/limburg_eo_presto_torch291_sequences",
            profile=profile,
        )
    return dict(
        runtime=ROOT / f".venvs-eo/{ROUTES[model][2]}/bin/python",
        runner="scripts/107_extract_limburg_mps_sequences.py"
        if device == "mps"
        else "scripts/100_extract_limburg_eo_sequences.py",
        sequences=ROOT
        / "data/processed"
        / ("limburg_eo_mps_sequences" if device == "mps" else "limburg_eo_sequences"),
        profile=None,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "infrastructure/eo_census/plan.json")
    parser.add_argument(
        "--adopt",
        action="append",
        default=[],
        help="Existing model:PID; extraction continues undisturbed",
    )
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    workers = plan["local_workers"]
    if workers not in (1, 2, 3):
        raise ValueError("Local scheduler supports one to three workers")
    limits = {"cpu": plan.get("cpu_workers", workers), "mps": plan.get("mps_workers", 0)}
    if min(limits.values()) < 0 or sum(limits.values()) != workers:
        raise ValueError("Device slots must equal the total worker count")
    adopted = dict(item.split(":", 1) for item in args.adopt)
    logdir = ROOT / "logs/eo-census"
    logdir.mkdir(parents=True, exist_ok=True)
    lock = (logdir / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    staging = json.loads((ROOT / "data/raw/limburg_compact_eo/staging-progress.json").read_text())
    if staging["status"] != "completed" or staging["failures"]:
        raise ValueError("Full local staging required for this census run")
    if set(ORDER) != set(ROUTES) or set(plan["owners"]) != set(ROUTES):
        raise ValueError("Queue does not account for all configured models")
    state = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "order": ORDER,
        "models": {},
        "active_models": [],
        "local_workers": workers,
        "device_limits": limits,
        "runtime_profiles": plan.get("runtime_profiles", {}),
        "scope": "Frozen extraction and exact-area aggregation only; no analogue scoring.",
    }
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = "/tmp/limburg-eo-matplotlib"
    base = ROOT / "results/eo_catchment_representations"
    completed = []

    def save():
        state["updated_utc"] = datetime.now(timezone.utc).isoformat()
        atomic_json(logdir / "progress.json", state)

    def run_model(model, device):
        model_lock = (logdir / f".{model}.lock").open("a")
        fcntl.flock(model_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        settings = execution_settings(model, device, plan)
        runtime = settings["runtime"]
        model_env = dict(env)
        if device == "mps":
            model_env["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"
        sequence_root = settings["sequences"]
        with (logdir / f"{model}.log").open("a") as output:
            if model in adopted:
                pid = int(adopted[model])
                while True:
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(5)
                statuses = []
                for manifest in (sequence_root / model).glob("*/manifest.json"):
                    identity = json.loads(manifest.read_text())
                    status = manifest.parent / "status.json"
                    if identity.get("purpose") == "context_census" and status.exists():
                        statuses.append(json.loads(status.read_text()))
                last = max(statuses, key=lambda x: x["updated_utc"], default={})
                extraction_exit = 0 if last.get("status") == "completed" else 1
            else:
                extraction_exit = subprocess.run(
                    [
                        str(runtime),
                        "-u",
                        settings["runner"],
                        "--model",
                        model,
                        "--run",
                    ],
                    cwd=ROOT,
                    env=model_env,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                ).returncode
            if extraction_exit != 0:
                return {"extraction_exit": extraction_exit, "aggregation_exit": None}
            aggregation_exit = subprocess.run(
                [
                    str(ROOT / ".venvs-eo/terramind/bin/python"),
                    "-u",
                    "scripts/101_aggregate_limburg_eo_catchments.py",
                    "--sequences",
                    str(sequence_root),
                    "--model",
                    model,
                    "--out",
                    str(base / "per_model" / model),
                ],
                cwd=ROOT,
                env=model_env,
                stdout=output,
                stderr=subprocess.STDOUT,
            ).returncode
        return {"extraction_exit": extraction_exit, "aggregation_exit": aggregation_exit}

    # A newly selected runtime may start while completed models' many receipts
    # are reverified. Their verification still precedes acceptance/merging.
    pending = sorted(ORDER, key=lambda model: model not in plan.get("runtime_profiles", {}))
    futures = {}
    paused = False
    save()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while pending or futures:
            live_plan = json.loads(args.plan.read_text())
            counts = {device: sum(d == device for _, d in futures.values()) for device in limits}
            for model in list(pending):
                if paused or len(futures) >= workers:
                    break
                device = live_plan.get("execution_devices", {}).get(model, "cpu")
                if model in live_plan.get("deferred_models", []):
                    state["models"][model] = {"status": "deferred_paused"}
                    pending.remove(model)
                    continue
                if device not in limits:
                    raise ValueError("Unknown execution device: " + device)
                if live_plan["owners"][model] != "local":
                    state["models"][model] = {"status": "assigned_azure"}
                    pending.remove(model)
                    continue
                settings = execution_settings(model, device, live_plan)
                if model not in adopted and completed_aggregate(
                    base, model, device, settings["profile"]
                ):
                    completed.append(model)
                    state["models"][model] = {
                        "status": "completed_verified",
                        "extraction_exit": 0,
                        "aggregation_exit": 0,
                        "device": device,
                    }
                    pending.remove(model)
                    continue
                if counts[device] >= limits[device]:
                    continue
                futures[pool.submit(run_model, model, device)] = (model, device)
                counts[device] += 1
                pending.remove(model)
            state["active_models"] = [model for model, _ in futures.values()]
            state["active_devices"] = {model: device for model, device in futures.values()}
            save()
            if not futures:
                break
            done, _ = wait(futures, timeout=10, return_when=FIRST_COMPLETED)
            for future in done:
                model, device = futures.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"extraction_exit": 1, "aggregation_exit": 1, "error": str(exc)}
                result["device"] = device
                state["models"][model] = result
                paused |= result["extraction_exit"] == 75
                if result.get("extraction_exit") == result.get("aggregation_exit") == 0:
                    completed.append(model)
            if paused and not futures:
                break
    state["active_models"] = []
    success = len(completed) == len(ROUTES) and all(
        v.get("extraction_exit") == v.get("aggregation_exit") == 0 for v in state["models"].values()
    )
    if success and not paused:
        merge_aggregates(base, completed)
    state["status"] = (
        "paused_free_space"
        if paused
        else "completed"
        if success
        else "finished_assigned_jobs_with_pending_or_errors"
    )
    save()
    return int(not success)


if __name__ == "__main__":
    raise SystemExit(main())
