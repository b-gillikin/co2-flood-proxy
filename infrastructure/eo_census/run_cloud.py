"""One-model Azure worker. Benchmark first; never provision a VM.

Requires provision-time watchdog and self-deallocation role on this VM. Images,
weights and Linux runtimes must be staged before running; no raw gauge inputs.
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import ROUTES  # noqa: E402

spec = importlib.util.spec_from_file_location("eo_budget", Path(__file__).with_name("budget.py"))
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


def deallocate():
    import requests
    from azure.identity import DefaultAzureCredential

    resource = os.environ["AZURE_VM_RESOURCE_ID"]
    token = DefaultAzureCredential().get_token("https://management.azure.com/.default").token
    response = requests.post(
        "https://management.azure.com" + resource + "/deallocate?api-version=2024-07-01",
        headers={"Authorization": "Bearer " + token},
        timeout=60,
    )
    response.raise_for_status()


def compare_devices(model, kind):
    import numpy as np

    root = ROOT / "data/processed/limburg_eo_sequences" / model
    vectors = {}
    for manifest in root.glob("*/manifest.json"):
        identity = json.loads(manifest.read_text())
        if identity.get("purpose") != "engineering" or identity.get("device") not in {
            "cpu",
            "cuda",
        }:
            continue
        for path in manifest.parent.glob(f"engineering_{kind}_real_months/*/*.npz"):
            with np.load(path) as data:
                vectors[identity["device"]] = data["embedding"].copy()
    if set(vectors) != {"cpu", "cuda"} or vectors["cpu"].shape != vectors["cuda"].shape:
        raise ValueError("Missing CPU/GPU benchmark pair or unequal dimensions")
    a, b = vectors["cpu"], vectors["cuda"]
    difference = float(np.linalg.norm(a - b) / max(float(np.linalg.norm(a)), 1e-12))
    return {
        "relative_l2": difference,
        "max_absolute_difference": float(np.max(np.abs(a - b))),
        "allclose": bool(np.allclose(a, b, rtol=1e-3, atol=1e-5)),
        "engineering_tolerance": {"rtol": 1e-3, "atol": 1e-5},
    }


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--benchmark", action="store_true")
    p.add_argument("--models", nargs="+", required=True, choices=list(ROUTES))
    args = p.parse_args()
    plan_path = ROOT / "infrastructure/eo_census/plan.json"
    plan = json.loads(plan_path.read_text())
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable: no CPU fallback on a paid GPU VM")
    if not os.environ.get("LIMBURG_CLOUD_WATCHDOG_ARMED") or not os.environ.get(
        "AZURE_VM_RESOURCE_ID"
    ):
        raise RuntimeError("Provision-time watchdog and self-deallocation identity required")
    allocation = os.environ["AZURE_VM_ALLOCATED_UTC"]
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    client = BlobServiceClient(
        "https://stkerkradeprod01bg.blob.core.windows.net", credential=DefaultAzureCredential()
    )
    ledger_blob = client.get_blob_client("limburg-compact-eo", "v1/results/budget-ledger.json")
    if ledger_blob.exists():
        ledger = json.loads(ledger_blob.download_blob().readall())
        plan["compute_spent_usd"] = ledger["compute_spent_usd"]
        plan["billed_vm_sessions"] = ledger.get("billed_vm_sessions", {})
    # Recompute this allocation's full elapsed charge without counting it twice.
    previous_session_charge = plan.get("billed_vm_sessions", {}).get(allocation, 0)
    prior_compute = plan["compute_spent_usd"] - previous_session_charge
    plan["compute_spent_usd"] = prior_compute
    remaining = budget.deadline_seconds(plan, allocation) - 1800
    if remaining <= 0:
        deallocate()
        return 75
    elapsed_hours = max(
        0,
        (
            datetime.now(timezone.utc) - datetime.fromisoformat(allocation.replace("Z", "+00:00"))
        ).total_seconds()
        / 3600,
    )
    pilot_seconds = budget.benchmark_seconds(plan, elapsed_hours)
    deadline = time.monotonic() + min(remaining, pilot_seconds if args.benchmark else remaining)
    logdir = ROOT / "logs/eo-cloud"
    logdir.mkdir(parents=True, exist_ok=True)
    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "benchmark" if args.benchmark else "production",
        "models": {},
        "status": "running",
    }
    env = os.environ.copy()
    env["LIMBURG_EO_DEVICE"] = "cuda"
    env["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    env["MPLCONFIGDIR"] = "/tmp/limburg-eo-matplotlib"

    def save():
        report["updated_utc"] = datetime.now(timezone.utc).isoformat()
        tmp = logdir / "progress.partial"
        tmp.write_text(json.dumps(report, indent=2) + "\n")
        tmp.replace(logdir / "progress.json")

    def execute(command, output):
        seconds = deadline - time.monotonic()
        if seconds <= 0:
            raise subprocess.TimeoutExpired(command, 0)
        subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=seconds,
            check=True,
        )

    try:
        for model in args.models:
            if not args.benchmark:
                refreshed = json.loads(plan_path.read_text())
                plan["owners"] = refreshed["owners"]
                plan["model_estimate_hours"] = refreshed.get("model_estimate_hours", {})
                if plan["owners"][model] != "azure":
                    raise ValueError("Model not assigned exclusively to Azure: " + model)
                elapsed = (
                    datetime.now(timezone.utc)
                    - datetime.fromisoformat(allocation.replace("Z", "+00:00"))
                ).total_seconds() / 3600
                if not plan.get("benchmarks", {}).get(model, {}).get("passed"):
                    raise ValueError("CPU/GPU benchmark not passed for " + model)
                estimate = plan.get("model_estimate_hours", {}).get(model)
                if not budget.can_start_model(plan, estimate, elapsed):
                    report["status"] = "paused_before_model_budget"
                    break
            runtime = ROOT / f".venvs-eo/{ROUTES[model][2]}/bin/python"
            started = time.monotonic()
            report["current_model"] = model
            save()
            with (logdir / f"{model}.log").open("a") as output:
                command = [
                    str(runtime),
                    "-u",
                    "scripts/100_extract_limburg_eo_sequences.py",
                    "--model",
                    model,
                    "--smoke" if args.benchmark else "--run",
                ]
                if args.benchmark:
                    checks = {}
                    kinds = (
                        ["two", "monthly"]
                        if model in {"olmoearth", "galileo", "anysat", "prithvi", "presto"}
                        else ["two"]
                    )
                    for kind in kinds:
                        for device in ["cpu", "cuda"]:
                            env["LIMBURG_EO_DEVICE"] = device
                            execute(command + ["--smoke-kind", kind], output)
                        checks[kind] = compare_devices(model, kind)
                    plan.setdefault("benchmarks", {})[model] = {
                        "checks": checks,
                        "passed": all(x["allclose"] for x in checks.values()),
                    }
                    report.setdefault("numerical_checks", {})[model] = checks
                    if not plan["benchmarks"][model]["passed"]:
                        raise ValueError("CPU/GPU differences need review; retain CPU route")
                else:
                    execute(command, output)
                if not args.benchmark:
                    execute(
                        [
                            str(ROOT / ".venvs-eo/terramind/bin/python"),
                            "scripts/101_aggregate_limburg_eo_catchments.py",
                            "--model",
                            model,
                            "--out",
                            str(ROOT / "results/eo_catchment_representations/per_model" / model),
                        ],
                        output,
                    )
                    execute(
                        [
                            str(ROOT / ".venvs-eo/terramind/bin/python"),
                            "infrastructure/eo_census/package_results.py",
                            "--model",
                            model,
                        ],
                        output,
                    )
            report["models"][model] = {"seconds": time.monotonic() - started, "status": "completed"}
            save()
        else:
            report["status"] = "completed"
    except Exception as exc:
        report["status"] = "stopped"
        report["error"] = str(exc)
        raise
    finally:
        # Preserve elapsed VM charges across restarts; allocate-time includes setup/idle.
        allocated = datetime.fromisoformat(allocation.replace("Z", "+00:00"))
        elapsed = max(0, (datetime.now(timezone.utc) - allocated).total_seconds() / 3600)
        report["session_compute_estimate_usd"] = elapsed * plan["azure_hourly_usd"]
        plan.setdefault("billed_vm_sessions", {})[allocation] = report[
            "session_compute_estimate_usd"
        ]
        plan["compute_spent_usd"] = prior_compute + report["session_compute_estimate_usd"]
        plan_path.write_text(json.dumps(plan, indent=2) + "\n")
        report["billing_note"] = (
            "Retail-rate estimate; Azure billing may lag. External reserve and provision-time watchdog also apply."
        )
        save()
        # Publish compact results and ledger before stopping paid compute.
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient

            client = BlobServiceClient(
                "https://stkerkradeprod01bg.blob.core.windows.net",
                credential=DefaultAzureCredential(),
            )
            ledger_blob.upload_blob(json.dumps(plan, indent=2).encode(), overwrite=True)
            for path in [
                logdir / "progress.json",
                *sorted((ROOT / "results/eo_result_packages").glob("*")),
            ]:
                with path.open("rb") as source:
                    client.get_blob_client(
                        "limburg-compact-eo", "v1/results/" + path.name
                    ).upload_blob(source, overwrite=True)
        finally:
            deallocate()
    return int(report["status"] != "completed")


if __name__ == "__main__":
    raise SystemExit(main())
