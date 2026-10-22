"""Restart eight corrected EO routes after retiring superseded patch caches.

Two CPU workers plus one MPS; reuse Prithvi and repaired OlmoEarth.
No Azure observations, new weights, model tuning or event subsampling enter.
"""

from __future__ import annotations

import copy
import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_coherent_inputs import POLICY
from src.eo_encoder_corrections import VERSION as INPUT_CORRECTIONS
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import validate_run

LANES = {
    "cpu_1": [
        ("dofa", "cpu", "legacy"),
        ("copernicus_fm", "cpu", "legacy"),
        ("terramind", "cpu", "terramind"),
    ],
    "cpu_2": [("presto", "cpu", "presto-torch291")],
    "mps_1": [
        ("croma", "mps", "modern"),
        ("satmae", "mps", "satmae"),
        ("anysat", "mps", "modern"),
        ("galileo", "mps", "galileo"),
    ],
}
LOGS = ROOT / "logs/eo-coherent-correction-v1"
SEQUENCES = ROOT / "data/processed/limburg_eo_coherent_census_v1"
AGGREGATES = ROOT / "results/eo_catchment_representations/coherent_v1"
SELECTION = ROOT / "config/limburg_eo_coherent_selected_runs.json"


def extraction_command(model, device, runtime, *, smoke=False):
    args = [
        str(ROOT / f".venvs-eo/{runtime}/bin/python"),
        "-u",
        str(ROOT / "scripts/118_extract_versioned_eo_sequences.py"),
        "--model",
        model,
        "--device",
        device,
    ]
    if model == "presto":
        args += ["--runtime-profile", "presto-torch291-cpu4"]
    args += [
        "--output",
        str(SEQUENCES.with_name(SEQUENCES.name + "_engineering") if smoke else SEQUENCES),
    ]
    args += ["--smoke", "--smoke-kind", "two"] if smoke else ["--run"]
    return args


def verified_model_run(model, expected_contexts):
    runs = list((SEQUENCES / model).glob("*/manifest.json"))
    if len(runs) != 1:
        raise ValueError(
            f"Expected exactly one versioned census run for {model}; found {len(runs)}"
        )
    run = runs[0].parent
    saved, _ = validate_run(ROOT, run, model=model, expected_contexts=expected_contexts)
    policy = POLICY if ROUTES[model][0] == "s2_10m" else "native_product_v1"
    if saved.get("input_policy") != policy:
        raise ValueError("Selected run lacks coherent S2 input policy")
    if saved.get("input_corrections") != INPUT_CORRECTIONS:
        raise ValueError("Selected run lacks publisher input corrections")
    return run, saved


def main():
    scheduled = [m for jobs in LANES.values() for m, _, _ in jobs]
    if len(scheduled) != len(set(scheduled)) or set(scheduled) != {
        m for m, route in ROUTES.items() if route[0] == "s2_10m"
    } | {"croma"}:
        raise ValueError("Queue must assign all seven S2 models and CROMA exactly once")
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / ".lock").open("w") as queue_lock:
        fcntl.flock(queue_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {
            "pid": os.getpid(),
            "status": "waiting_for_retirement",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "cpu_workers": 2,
            "mps_workers": 1,
            "models": {},
            "lanes": LANES,
            "reused_models": ["prithvi", "olmoearth"],
            "input_corrections": INPUT_CORRECTIONS,
        }
        mutex = threading.Lock()

        def update(**values):
            with mutex:
                state.update(values, updated_utc=datetime.now(timezone.utc).isoformat())
                temporary = LOGS / "progress.tmp"
                temporary.write_text(json.dumps(state, indent=2) + "\n")
                temporary.replace(LOGS / "progress.json")

        def model_update(model, **values):
            with mutex:
                state["models"].setdefault(model, {}).update(values)
            update()

        def run(command, logfile):
            env = {
                **os.environ,
                "OPENBLAS_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "VECLIB_MAXIMUM_THREADS": "1",
                "PYTORCH_ENABLE_MPS_FALLBACK": "0",
                "MPLCONFIGDIR": str(LOGS / "matplotlib"),
            }
            with logfile.open("a") as log:
                return subprocess.run(
                    command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
                ).returncode

        update()
        try:
            while True:
                retired = json.loads(
                    (ROOT / "logs/eo-retirement-2026-10-22/progress.json").read_text()
                )
                if retired["status"] == "completed":
                    break
                if retired["status"] == "failed":
                    raise ValueError("Retirement failed; retained sources need inspection")
                time.sleep(20)
            original = json.loads((ROOT / "config/limburg_eo_selected_runs.json").read_text())
            context_path = ROOT / original["contexts"]
            if sha256(context_path) != original["contexts_sha256"]:
                raise ValueError("Held context population changed")
            contexts = [c["context_id"] for c in json.loads(context_path.read_text())]
            update(
                status="checking_real_readouts",
                retirement_receipt_sha256=sha256(
                    ROOT / retired["archive"] / "retirement-receipt.json"
                ),
                held_selection=original,
                archive_jobs_sha256=sha256(ROOT / "data/raw/limburg_compact_eo/jobs.json"),
                context_count=len(contexts),
            )

            def lane(name, jobs, *, checks_only):
                for model, device, runtime in jobs:
                    model_update(
                        model,
                        status="checking_real_readouts" if checks_only else "extracting",
                        lane=name,
                        device=device,
                        command=extraction_command(model, device, runtime),
                    )
                    if checks_only:
                        command = [
                            str(ROOT / f".venvs-eo/{runtime}/bin/python"),
                            "-u",
                            str(ROOT / "scripts/125_check_corrected_eo_readouts.py"),
                            "--model",
                            model,
                            "--device",
                            device,
                        ]
                        if model == "presto":
                            command += ["--runtime-profile", "presto-torch291-cpu4"]
                        code = run(command, LOGS / f"{model}.log")
                        if not code:
                            code = run(
                                extraction_command(model, device, runtime, smoke=True),
                                LOGS / f"{model}.log",
                            )
                    else:
                        code = run(
                            extraction_command(model, device, runtime), LOGS / f"{model}.log"
                        )
                    model_update(
                        model,
                        status=("engineering_failed" if checks_only else "extraction_failed")
                        if code
                        else ("engineering_checked" if checks_only else "extracted"),
                        exit_code=code,
                    )

            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [
                    pool.submit(lane, name, jobs, checks_only=True) for name, jobs in LANES.items()
                ]
                for future in futures:
                    future.result()
            if any(s["status"] != "engineering_checked" for s in state["models"].values()):
                raise ValueError("Real-input checks need attention; no full extraction started")
            update(status="extracting")
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [
                    pool.submit(lane, name, jobs, checks_only=False) for name, jobs in LANES.items()
                ]
                for future in futures:
                    future.result()
            update(status="aggregating")
            revised = copy.deepcopy(original)
            revised.update(
                version="held_archive_publisher_inputs_and_same_day_s2_v1",
                purpose="Same held archive/context census; eight corrected routes, Prithvi and repaired OlmoEarth reused",
            )
            for model in [m for jobs in LANES.values() for m, _, _ in jobs]:
                if state["models"][model]["status"] != "extracted":
                    continue
                model_update(model, status="aggregating")
                selected, saved = verified_model_run(model, contexts)
                dest = AGGREGATES / "per_model" / model
                code = run(
                    [
                        str(ROOT / ".venvs-eo/terramind/bin/python"),
                        "-u",
                        "scripts/101_aggregate_limburg_eo_catchments.py",
                        "--model",
                        model,
                        "--run-directory",
                        str(selected),
                        "--out",
                        str(dest),
                    ],
                    LOGS / f"{model}.log",
                )
                model_update(
                    model,
                    status="aggregation_failed" if code else "completed",
                    aggregation_exit=code,
                )
                if not code:
                    revised["models"][model] = {
                        "run": str(selected.relative_to(ROOT)),
                        "aggregate": str((dest / "census").relative_to(ROOT)),
                        "mask_policy": saved["mask_policy"],
                    }
            failed = [m for m, status in state["models"].items() if status["status"] != "completed"]
            if failed:
                raise ValueError(
                    "Correction attempts need attention; old affected runs were not substituted: "
                    + ", ".join(failed)
                )
            SELECTION.write_text(json.dumps(revised, indent=2) + "\n")
            update(status="merging", selection=str(SELECTION.relative_to(ROOT)))
            merged = AGGREGATES / "selected/census"
            runtime = str(ROOT / ".venvs-eo/terramind/bin/python")
            commands = [
                (
                    "merge",
                    [
                        runtime,
                        "scripts/117_finalize_selected_eo_runs.py",
                        "--selection",
                        str(SELECTION),
                        "--merge",
                        "--out",
                        str(merged),
                    ],
                ),
                (
                    "scoring",
                    [
                        runtime,
                        "-u",
                        "scripts/102_connect_limburg_eo_experiments.py",
                        "--selection",
                        str(SELECTION),
                        "--representations",
                        str(merged),
                        "--out",
                        str(ROOT / "results/eo_analogue_comparison_coherent_v1"),
                        "--run",
                    ],
                ),
                (
                    "review",
                    [
                        runtime,
                        "-u",
                        "scripts/120_review_eo_analogues.py",
                        "--input",
                        str(ROOT / "results/eo_analogue_comparison_coherent_v1"),
                        "--out",
                        str(ROOT / "results/eo_analogue_review_coherent_v1"),
                    ],
                ),
            ]
            for phase, command in commands:
                update(status=phase)
                code = run(command, LOGS / f"{phase}.log")
                if code:
                    raise ValueError(f"{phase} exited {code}; see its log")
            update(status="completed")
        except BaseException as exc:
            update(status="failed", error=str(exc))
            raise


if __name__ == "__main__":
    main()
