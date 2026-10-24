"""Run compatible supplemental sensitivities after staging/audit and current queue.

No sensor/orbit pooling, new weights, tuning or event subsampling. Each alternative
replaces one arm in a separate ten-model comparison; the other nine are retained.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/limburg_eo_expansion"
OUT = ROOT / "logs/eo-expansion-comparisons"
VARIANTS = [
    ("satmae_toa_qa60", "satmae", "s2_toa", "satmae", "mps"),
    ("copernicus_fm_toa_qa60", "copernicus_fm", "s2_toa", "legacy", "cpu"),
    ("croma_ascending_15", "croma", "s1_ascending_15", "modern", "mps"),
    ("croma_ascending_161", "croma", "s1_ascending_161", "modern", "mps"),
]


def prepare_view(name, route):
    jobs = json.loads((BASE / "jobs.json").read_text())
    if route == "s2_toa":
        mapping = {"s2_toa_10m": "s2_10m", "s2_toa_20m": "s2_20m", "s2_toa_qa60": "s2_toa_qa60"}
    else:
        mapping = {route: "s1_ascending"}
    selected = [{**j, "product": mapping[j["product"]]} for j in jobs if j["product"] in mapping]
    dest = ROOT / "data/processed/eo_expansion_input_views" / name
    dest.mkdir(parents=True, exist_ok=True)
    image = dest / "images"
    if not image.exists():
        image.symlink_to(BASE / "images", target_is_directory=True)
    path = dest / "jobs.json"
    text = json.dumps(selected, indent=2) + "\n"
    if path.exists() and path.read_text() != text:
        raise ValueError("Existing input view differs")
    path.write_text(text)
    return dest


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {
            "pid": os.getpid(),
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "variants": {},
        }

        def save(status, **extra):
            state.update(status=status, updated_utc=datetime.now(timezone.utc).isoformat(), **extra)
            p = OUT / "progress.partial"
            p.write_text(json.dumps(state, indent=2) + "\n")
            p.replace(OUT / "progress.json")

        def wait_for(path, completed):
            while True:
                if path.exists():
                    s = json.loads(path.read_text())
                    if s["status"] == completed:
                        return s
                    if s["status"] in {
                        "failed",
                        "completed_with_failures",
                        "paused_storage_budget",
                    }:
                        raise ValueError("Dependency needs attention: " + str(path))
                time.sleep(20)

        def run(phase, command):
            save(phase, command=command)
            env = {
                **os.environ,
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "GDAL_NUM_THREADS": "1",
                "PYTORCH_ENABLE_MPS_FALLBACK": "0",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            with (OUT / (phase + ".log")).open("a") as log:
                code = subprocess.run(
                    command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
                ).returncode
            if code:
                raise ValueError(phase + " exited " + str(code))

        try:
            save("waiting_for_staging_and_audit")
            wait_for(ROOT / "logs/eo-expansion-followthrough/progress.json", "staged_and_audited")
            save("waiting_for_current_model_workflow")
            wait_for(ROOT / "logs/eo-coherent-correction-v1/progress.json", "completed")
            import sys

            sys.path.insert(0, str(ROOT))
            from src.eo_inputs import sha256
            from src.eo_integrity import validate_run

            baseline = json.loads(
                (ROOT / "config/limburg_eo_coherent_selected_runs.json").read_text()
            )
            contexts = [
                c["context_id"] for c in json.loads((ROOT / baseline["contexts"]).read_text())
            ]
            runtime = str(ROOT / ".venvs-eo/terramind/bin/python")
            for name, model, route, environment, device in VARIANTS:
                archive = prepare_view(name, route)
                output = ROOT / "data/processed/eo_expansion_sequences" / name
                py = str(ROOT / f".venvs-eo/{environment}/bin/python")
                command = [
                    py,
                    "-u",
                    "scripts/130_extract_eo_expansion.py",
                    "--model",
                    model,
                    "--device",
                    device,
                    "--archive",
                    str(archive),
                ]
                run(
                    name + "_engineering",
                    command + ["--smoke", "--output", str(output) + "_engineering"],
                )
                run(name + "_extracting", command + ["--run", "--output", str(output)])
                runs = list((output / model).glob("*/manifest.json"))
                if len(runs) != 1:
                    raise ValueError("Expected one supplemental run")
                selected = runs[0].parent
                manifest, _ = validate_run(ROOT, selected, model=model, expected_contexts=contexts)
                aggregate = ROOT / "results/eo_expansion_representations" / name
                run(
                    name + "_aggregating",
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
                    "baseline_selection_sha256": sha256(
                        ROOT / "config/limburg_eo_coherent_selected_runs.json"
                    ),
                    "scope": "one changed arm; other nine retained; no cross-orbit pooling",
                }
                selection["models"][model] = {
                    "run": str(selected.relative_to(ROOT)),
                    "aggregate": str((aggregate / "census").relative_to(ROOT)),
                    "mask_policy": manifest["mask_policy"],
                }
                selection_path = OUT / (name + "-selection.json")
                selection_path.write_text(json.dumps(selection, indent=2) + "\n")
                merged = ROOT / "results/eo_expansion_representations" / name / "selected/census"
                run(
                    name + "_merging",
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
                    name + "_scoring",
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
                    name + "_review",
                    [
                        runtime,
                        "scripts/120_review_eo_analogues.py",
                        "--input",
                        str(scores),
                        "--out",
                        str(ROOT / "results/eo_expansion_reviews" / name),
                    ],
                )
                state["variants"][name] = {
                    "status": "completed",
                    "scores": str(scores.relative_to(ROOT)),
                }
            save("completed")
        except BaseException as exc:
            save("failed", error=str(exc))
            raise


if __name__ == "__main__":
    main()
