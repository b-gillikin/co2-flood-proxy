"""Version the full comparison grid into two CPU lanes and one GPU lane.

No event/label/seed/learning-rate/epoch pruning. Batch changes are explicit
optimizer-protocol changes; caches and prefetch are execution-only changes.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_execution import atomic, sha

BATCH = {"terramind": 8, "prithvi": 2, "galileo": 256, "copernicus": 16}
EVAL_BATCH = {"terramind": 4, "prithvi": 8, "galileo": 512, "copernicus": 32}
FEATURES = {
    "terramind": "limburg_terramind_encoder_v1",
    "galileo": "limburg_applied_galileo_spatial_v2",
    "copernicus": "limburg_copernicus_spatial_v1",
}


def optimized_plan(parent, root=ROOT):
    plan = copy.deepcopy(parent)
    plan["tuning_root"] = "results/applied_study_v4/tuning"
    plan["status"] = "prepared_optimized_full_grid"
    plan["parent_execution_plan_sha256"] = sha(
        root / "results/applied_study_v3/local-date-recovery-v1/execution-plan.json"
    )
    plan["optimization"] = dict(
        scientific_census="All parent tasks, learners, folds, budgets and final seeds retained",
        common_task_training_batch=BATCH,
        evaluation_batch=EVAL_BATCH,
        precision="float32 throughout; mixed precision profiling not adopted",
        batch_interpretation="Copernicus 2→16 and Galileo 64→256 change optimization; versioned v4, do not pool v3 fitted results",
        cached_encoders="Only frozen encoders; all 8 existing TerraMind augmentations retained; trainable neck/decoder remain live",
        lanes="Two CPU fit/application lanes with two Torch threads each; one MPS lane with two input workers",
        tuning="Full-label seed42 tunes three rates; repeat full-label seeds reuse its winner. Reduced-label seeds tune independently",
        archived_v3="Preserved supporting runs; current Copernicus process left running",
    )
    extra = [
        "src/applied_fast_data.py",
        "src/applied_fast_pool.py",
        "src/applied_tuning_reuse.py",
        "scripts/218_build_spatial_tensor_cache.py",
        "scripts/219_profile_fast_spatial.py",
        "scripts/220_cache_terramind_augmentations.py",
        "scripts/222_prepare_optimized_spatial_queue.py",
        "scripts/223_run_optimized_spatial_queue.py",
        "scripts/224_verify_fast_spatial_runtime.py",
    ]
    plan["source_hashes"] = {
        name: sha(root / name) for name in list(parent["source_hashes"]) + extra
    }
    plan["cache_paths"] = {t: f"data/processed/{name}" for t, name in FEATURES.items()}
    plan["cache_index_hashes"] = {
        t: sha(root / p / "index.json") for t, p in plan["cache_paths"].items()
    }
    plan["tensor_cache_index_hashes"] = {
        t: sha(root / f"data/processed/limburg_tensor_cache_v1/{t}/index.json") for t in BATCH
    }
    cpu_count = 0
    for j in plan["jobs"]:
        if j["learner"] == "physical":
            continue
        task = j["task"]
        cpu = j["learner"] == "linear" or (task == "galileo" and j["learner"] == "native")
        j["worker_lane"] = f"cpu-{cpu_count % 2}" if cpu else "mps"
        cpu_count += int(cpu)
        device = "cpu" if cpu else "mps"
        j["resource"] = device
        command = j["command"]
        command[command.index("--batch-size") + 1] = str(BATCH[task])
        command[command.index("--device") + 1] = device
        command[command.index("--output-root") + 1] = plan["tuning_root"]
        command += [
            "--tensor-cache",
            f"data/processed/limburg_tensor_cache_v1/{task}",
            "--eval-batch-size",
            str(EVAL_BATCH[task]),
            "--data-workers",
            "0" if cpu else "2",
            "--threads",
            "2" if cpu else "1",
            "--on-device-pool",
        ]
        if not (task == "galileo" and device == "mps"):
            command += ["--foreach"]
        if j["learner"] == "native" and task in FEATURES:
            if "--feature-cache" in command:
                command[command.index("--feature-cache") + 1] = plan["cache_paths"][task]
            else:
                command += ["--feature-cache", plan["cache_paths"][task]]
        epochs = 100 if task == "terramind" else 50
        j["output"] = (
            f"{plan['tuning_root']}/{task}-{j['learner']}-{j['fold']}-{j['budget']:g}-{j['seed']}-{device}-b{BATCH[task]}-e{epochs}"
        )
    apply_tuning_reuse(plan)
    return plan


def apply_tuning_reuse(plan):
    sources = {
        (j["task"], j["learner"], j["fold"]): j["output"]
        for j in plan["jobs"]
        if j["learner"] != "physical" and j["budget"] == 1.0 and j["seed"] == 42
    }
    candidates = 0
    for j in plan["jobs"]:
        if j["learner"] == "physical":
            continue
        repeat = j["budget"] == 1.0 and j["seed"] != 42
        if repeat:
            source = sources[j["task"], j["learner"], j["fold"]]
            j["tuning_source_output"] = source
            if "--fixed-lr-from" in j["command"]:
                j["command"][j["command"].index("--fixed-lr-from") + 1] = source
            else:
                j["command"] += ["--fixed-lr-from", source]
        j["learning_rate_candidates"] = 1 if repeat else 3
        candidates += j["learning_rate_candidates"]
    plan["neural_candidate_fits"] = candidates
    plan["optimization"]["tuning"] = (
        "User-approved full-label seed42 tuning reused for repeat seeds; reduced-label masks remain independently tuned"
    )


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "results/applied_study_v4")
    a = p.parse_args()
    if (a.output / "execution-plan.json").exists():
        raise FileExistsError("Do not overwrite a frozen execution plan")
    parent = json.loads(
        (ROOT / "results/applied_study_v3/local-date-recovery-v1/execution-plan.json").read_text()
    )
    plan = optimized_plan(parent)
    a.output.mkdir(parents=True, exist_ok=True)
    atomic(a.output / "execution-plan.json", plan)
    for lane in ["cpu-0", "cpu-1", "mps"]:
        sub = copy.deepcopy(plan)
        sub["jobs"] = [
            j for j in plan["jobs"] if j["learner"] == "physical" or j["worker_lane"] == lane
        ]
        sub["lane"] = lane
        sub["master_plan_sha256"] = sha(a.output / "execution-plan.json")
        (a.output / lane).mkdir(exist_ok=True)
        atomic(a.output / lane / "execution-plan.json", sub)
    print(
        json.dumps(
            {
                lane: sum(j.get("worker_lane") == lane for j in plan["jobs"])
                for lane in ["cpu-0", "cpu-1", "mps"]
            }
        )
    )


if __name__ == "__main__":
    main()
