"""Two CPU lanes plus one GPU, adopting an existing supplemental SatMAE run.

Numerical extraction/scoring sources are unchanged. One postprocessing writer
serializes aggregation, merging, scoring and review; extraction uses other lanes.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_integrity import validate_run

SPEC = importlib.util.spec_from_file_location(
    "supplemental_plan", ROOT / "scripts/131_run_eo_expansion_comparisons.py"
)
PLAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLAN)
OUT = ROOT / "logs/eo-expansion-comparisons"
GPU_NAMES = ["satmae_toa_qa60", "croma_ascending_15", "croma_ascending_161"]
CPU_NAMES = ["copernicus_fm_toa_qa60"]


def lanes(variants):
    by_name = {v[0]: v for v in variants}
    if len(by_name) != len(variants) or set(by_name) != set(GPU_NAMES + CPU_NAMES):
        raise ValueError("Every configured variant must occupy exactly one extraction lane")
    return [by_name[n] for n in GPU_NAMES], [by_name[n] for n in CPU_NAMES]


def engineering_context(contexts, jobs, observed_paths):
    """Select one held snapshot using source support only, never event outcomes."""
    windows = {j["window"]["id"] for j in jobs if j["relative_path"] in observed_paths}
    choices = [
        c
        for c in contexts
        if c["kind"] == "monthly_snapshot"
        and len(c["windows"]) == 1
        and c["windows"][0]["id"] in windows
    ]
    if not choices:
        raise ValueError("No observed snapshot available for engineering check")
    return min(choices, key=lambda c: (c["windows"][0]["start"], c["context_id"]))["context_id"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adopt-satmae-pid", type=int, required=True)
    parser.add_argument("--adopt-scoring-pid", type=int, default=0)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = json.loads((OUT / "progress.json").read_text())
        (OUT / "sequential-handoff-2026-10-26.json").write_text(json.dumps(old, indent=2) + "\n")
        state = {
            "pid": os.getpid(),
            "status": "running_parallel",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "scheduling": "one MPS extraction, one CPU extraction, one serialized CPU postprocessing",
            "adopted_satmae_pid": args.adopt_satmae_pid,
            "variants": {},
            "lanes": {},
        }
        mutex = threading.Lock()
        stop = threading.Event()
        ready = queue.Queue()
        failures = []
        baseline_path = ROOT / "config/limburg_eo_coherent_selected_runs.json"
        baseline = json.loads(baseline_path.read_text())
        contexts = [c["context_id"] for c in json.loads((ROOT / baseline["contexts"]).read_text())]
        runtime = str(ROOT / ".venvs-eo/terramind/bin/python")
        for dependency, expected in [
            (ROOT / "logs/eo-coherent-correction-v1/progress.json", "completed"),
            (ROOT / "logs/eo-expansion-followthrough/progress.json", "staged_and_audited"),
        ]:
            if json.loads(dependency.read_text())["status"] != expected:
                raise ValueError("Dependency not complete: " + str(dependency))

        def save():
            state["updated_utc"] = datetime.now(timezone.utc).isoformat()
            state["free_gib"] = round(shutil.disk_usage(ROOT).free / 2**30, 1)
            temp = OUT / "progress.partial"
            temp.write_text(json.dumps(state, indent=2) + "\n")
            temp.replace(OUT / "progress.json")

        def update(name, status, lane, **extra):
            with mutex:
                state["variants"].setdefault(name, {}).update(status=status, **extra)
                state["lanes"][lane] = {"variant": name, "status": status}
                save()

        def run(name, phase, lane, command):
            # Preserve practical headroom; never change the event/input population.
            while shutil.disk_usage(ROOT).free < 60 * 2**30:
                update(name, "waiting_for_disk_space", lane, pending_phase=phase)
                if stop.wait(20):
                    raise RuntimeError("Queue stopped after another lane failed")
            if (
                args.adopt_scoring_pid
                and name == "copernicus_fm_toa_qa60"
                and phase in {"aggregating", "merging", "scoring"}
            ):
                receipt = json.loads(
                    (ROOT / "results/eo_expansion_comparisons" / name / "manifest.json").read_text()
                )
                if receipt["status"] != "completed":
                    raise ValueError("Adopted scoring did not complete")
                update(name, phase + "_reused", lane)
                return
            update(name, phase, lane, command=command)
            env = {
                **os.environ,
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "VECLIB_MAXIMUM_THREADS": "1",
                "GDAL_NUM_THREADS": "1",
                "PYTORCH_ENABLE_MPS_FALLBACK": "0",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            with (OUT / (name + "_" + phase + ".log")).open("a") as log:
                child = subprocess.Popen(
                    command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
                )
                update(name, phase, lane, worker_pid=child.pid)
                code = child.wait()
            if code:
                raise ValueError(name + " " + phase + " exited " + str(code))

        def run_directory(name, model):
            paths = list(
                (ROOT / "data/processed/eo_expansion_sequences" / name / model).glob(
                    "*/manifest.json"
                )
            )
            if len(paths) != 1:
                raise ValueError("Expected one run: " + name)
            return paths[0].parent

        def adopt(name, model, lane):
            update(name, "extracting_adopted", lane, worker_pid=args.adopt_satmae_pid)
            while True:
                selected = run_directory(name, model)
                status = json.loads((selected / "status.json").read_text())
                if status["status"] == "completed":
                    validate_run(ROOT, selected, model=model, expected_contexts=contexts)
                    # Avoid overlapping the next GPU job with the adopted process exit.
                    while True:
                        try:
                            os.kill(args.adopt_satmae_pid, 0)
                        except ProcessLookupError:
                            break
                        if stop.wait(2):
                            raise RuntimeError("Queue stopped")
                    return
                if status["status"] in {"failed", "completed_with_errors"}:
                    raise ValueError("Adopted SatMAE failed")
                try:
                    os.kill(args.adopt_satmae_pid, 0)
                except ProcessLookupError:
                    raise ValueError("Adopted SatMAE disappeared before completion") from None
                if stop.wait(20):
                    raise RuntimeError("Queue stopped")

        def extraction(jobs, lane):
            for variant in jobs:
                if stop.is_set():
                    return
                name, model, route, environment, device = variant
                if name == "satmae_toa_qa60":
                    adopt(name, model, lane)
                else:
                    archive = PLAN.prepare_view(name, route)
                    output = ROOT / "data/processed/eo_expansion_sequences" / name
                    command = [
                        str(ROOT / f".venvs-eo/{environment}/bin/python"),
                        "-u",
                        "scripts/133_extract_supported_croma.py"
                        if model == "croma"
                        else "scripts/130_extract_eo_expansion.py",
                        "--model",
                        model,
                        "--device",
                        device,
                        "--archive",
                        str(archive),
                    ]
                    existing = list((output / model).glob("*/status.json"))
                    complete = (
                        len(existing) == 1
                        and json.loads(existing[0].read_text())["status"] == "completed"
                    )
                    if not complete:
                        if model == "croma":
                            jobs = json.loads((archive / "jobs.json").read_text())
                            observed = set()
                            with (
                                ROOT / "results/eo_expansion_audit/pixels.jsonl"
                            ).open() as stream:
                                for line in stream:
                                    row = json.loads(line)
                                    if row["joint_valid_pixels"] > 0:
                                        observed.add(row["relative_path"])
                            context = engineering_context(
                                json.loads((ROOT / baseline["contexts"]).read_text()),
                                jobs,
                                observed,
                            )
                            engineering_output = Path(
                                str(output) + "_engineering_observed_snapshot"
                            )
                            run(
                                name,
                                "engineering",
                                lane,
                                command
                                + [
                                    "--context",
                                    context,
                                    "--run",
                                    "--output",
                                    str(engineering_output),
                                ],
                            )
                            status_files = list((engineering_output / model).glob("*/status.json"))
                            if len(status_files) != 1:
                                raise ValueError("Engineering output missing")
                            check = json.loads(status_files[0].read_text())
                            if (
                                check["status"] != "completed"
                                or check["errors"]
                                or check["written"] + check["resumed"] == 0
                            ):
                                raise ValueError(
                                    "Engineering check produced no verified embeddings"
                                )
                        else:
                            run(
                                name,
                                "engineering",
                                lane,
                                command + ["--smoke", "--output", str(output) + "_engineering"],
                            )
                        run(name, "extracting", lane, command + ["--run", "--output", str(output)])
                    validate_run(
                        ROOT, run_directory(name, model), model=model, expected_contexts=contexts
                    )
                update(name, "awaiting_postprocessing", lane)
                ready.put(variant)
            with mutex:
                state["lanes"][lane] = {"status": "completed"}
                save()

        def postprocess():
            if args.adopt_scoring_pid:
                with mutex:
                    state["lanes"]["cpu_postprocess"] = {
                        "variant": "copernicus_fm_toa_qa60",
                        "status": "scoring_adopted",
                        "worker_pid": args.adopt_scoring_pid,
                    }
                    save()
                while True:
                    try:
                        os.kill(args.adopt_scoring_pid, 0)
                    except ProcessLookupError:
                        break
                    if stop.wait(20):
                        return
                receipt = json.loads(
                    (
                        ROOT
                        / "results/eo_expansion_comparisons/copernicus_fm_toa_qa60/manifest.json"
                    ).read_text()
                )
                if receipt["status"] != "completed":
                    raise ValueError("Adopted scorer failed")
                for path, expected in receipt["input_sha256"].items():
                    if sha256(ROOT / path) != expected:
                        raise ValueError("Adopted score input differs: " + path)
            while True:
                variant = ready.get()
                if variant is None:
                    return
                if stop.is_set():
                    continue
                name, model, route, _, _ = variant
                selected = run_directory(name, model)
                manifest, _ = validate_run(ROOT, selected, model=model, expected_contexts=contexts)
                aggregate = ROOT / "results/eo_expansion_representations" / name
                run(
                    name,
                    "aggregating",
                    "cpu_postprocess",
                    [
                        runtime,
                        "scripts/101_aggregate_limburg_eo_catchments.py",
                        "--model",
                        model,
                        "--run-directory",
                        str(selected),
                        "--out",
                        str(aggregate),
                    ],
                )
                selection = json.loads(json.dumps(baseline))
                selection["supplemental_sensitivity"] = {
                    "name": name,
                    "source_product": route,
                    "baseline_selection_sha256": sha256(baseline_path),
                    "scope": "one changed arm; other nine retained; no cross-orbit pooling",
                }
                selection["models"][model] = {
                    "run": str(selected.relative_to(ROOT)),
                    "aggregate": str((aggregate / "census").relative_to(ROOT)),
                    "mask_policy": manifest["mask_policy"],
                }
                selection_path = OUT / (name + "-selection.json")
                selection_path.write_text(json.dumps(selection, indent=2) + "\n")
                merged = aggregate / "selected/census"
                run(
                    name,
                    "merging",
                    "cpu_postprocess",
                    [
                        runtime,
                        "scripts/117_finalize_selected_eo_runs.py",
                        "--selection",
                        str(selection_path),
                        "--merge",
                        "--out",
                        str(merged),
                    ],
                )
                scores = ROOT / "results/eo_expansion_comparisons" / name
                run(
                    name,
                    "scoring",
                    "cpu_postprocess",
                    [
                        runtime,
                        "-u",
                        "scripts/102_connect_limburg_eo_experiments.py",
                        "--selection",
                        str(selection_path),
                        "--representations",
                        str(merged),
                        "--out",
                        str(scores),
                        "--run",
                    ],
                )
                run(
                    name,
                    "review",
                    "cpu_postprocess",
                    [
                        runtime,
                        "scripts/120_review_eo_analogues.py",
                        "--input",
                        str(scores),
                        "--out",
                        str(ROOT / "results/eo_expansion_reviews" / name),
                    ],
                )
                update(name, "completed", "cpu_postprocess", scores=str(scores.relative_to(ROOT)))

        def guarded(fn, *params):
            try:
                return fn(*params)
            except BaseException as exc:
                with mutex:
                    failures.append(str(exc))
                    state["errors"] = failures.copy()
                    save()
                stop.set()

        with mutex:
            save()
        gpu, cpu = lanes(PLAN.VARIANTS)
        with ThreadPoolExecutor(max_workers=3) as pool:
            post = pool.submit(guarded, postprocess)
            workers = [
                pool.submit(guarded, extraction, gpu, "mps"),
                pool.submit(guarded, extraction, cpu, "cpu_extract"),
            ]
            for future in workers:
                future.result()
            ready.put(None)
            post.result()
        with mutex:
            state["status"] = "failed" if failures else "completed"
            save()
        if failures:
            raise RuntimeError("; ".join(failures))


if __name__ == "__main__":
    main()
