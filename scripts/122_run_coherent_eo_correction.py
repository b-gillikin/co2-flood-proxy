"""Queue seven same-day S2 reruns after held-archive scoring: two CPU plus one MPS.

Keeps held inputs/results and the three unaffected model aggregates intact.
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
    if saved.get("input_policy") != POLICY:
        raise ValueError("Selected run lacks coherent S2 input policy")
    return run, saved


def main():
    scheduled = [m for jobs in LANES.values() for m, _, _ in jobs]
    if len(scheduled) != len(set(scheduled)) or set(scheduled) != {
        m for m, route in ROUTES.items() if route[0] == "s2_10m"
    }:
        raise ValueError("Queue must assign each of the seven S2 models exactly once")
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / ".lock").open("w") as queue_lock:
        fcntl.flock(queue_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {
            "pid": os.getpid(),
            "status": "waiting_for_current_workflow",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "cpu_workers": 2,
            "mps_workers": 1,
            "models": {},
            "lanes": LANES,
            "reused_models": ["prithvi", "croma", "olmoearth"],
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
                current = json.loads(
                    (ROOT / "logs/eo-current-archive-workflow-2026-10-22.json").read_text()
                )
                if current["status"] in {"completed", "failed"}:
                    break
                time.sleep(20)
            if current["step_2"] != "completed":
                raise ValueError(
                    "Held comparison failed; inspect its error before starting correction"
                )
            if current["status"] == "failed":
                update(prior_review_warning=current.get("error", "review did not complete"))
            base_output = ROOT / "results/eo_analogue_comparison"
            receipt = json.loads((base_output / "manifest.json").read_text())
            if receipt["status"] != "completed":
                raise ValueError("Held comparison has no completed receipt")
            for name, digest in receipt["outputs_sha256"].items():
                if sha256(base_output / name) != digest:
                    raise ValueError("Held output changed: " + name)
            original = json.loads((ROOT / "config/limburg_eo_selected_runs.json").read_text())
            context_path = ROOT / original["contexts"]
            if sha256(context_path) != original["contexts_sha256"]:
                raise ValueError("Held context population changed")
            contexts = [c["context_id"] for c in json.loads(context_path.read_text())]
            update(
                status="extracting",
                held_comparison_manifest_sha256=sha256(base_output / "manifest.json"),
                held_selection=original,
                archive_jobs_sha256=sha256(ROOT / "data/raw/limburg_compact_eo/jobs.json"),
                context_count=len(contexts),
            )

            def lane(name, jobs):
                for model, device, runtime in jobs:
                    model_update(
                        model,
                        status="smoke",
                        lane=name,
                        device=device,
                        command=extraction_command(model, device, runtime),
                    )
                    code = run(
                        extraction_command(model, device, runtime, smoke=True),
                        LOGS / f"{model}.log",
                    )
                    if not code:
                        model_update(model, status="extracting")
                        code = run(
                            extraction_command(model, device, runtime), LOGS / f"{model}.log"
                        )
                    model_update(
                        model, status="extraction_failed" if code else "extracted", exit_code=code
                    )

            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [pool.submit(lane, name, jobs) for name, jobs in LANES.items()]
                for future in futures:
                    future.result()
            update(status="aggregating")
            revised = copy.deepcopy(original)
            revised.update(
                version="held_archive_same_day_s2_v1",
                purpose="Same held archive/context census; seven coherent S2 reruns, three unchanged native-product models",
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
