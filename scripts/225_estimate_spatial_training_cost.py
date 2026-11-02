"""Training-only workload extrapolation from measured matching-batch profiles.

Not a calendar ETA: excludes initialization, validation, test, local application,
backup, interruptions and contention. No test accuracy enters this calculation.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd

from applied_execution import atomic, sha


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--plan",
        type=Path,
        default=ROOT / "results/applied_study_v4/full-label-tuning-reuse-v1/execution-plan.json",
    )
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("Version workload estimates")
    plan = json.loads(a.plan.read_text())
    evaluation = ROOT / plan.get("evaluation_directory", "results/applied_study_v1/evaluation")
    tables = {
        prefix: pd.read_parquet(evaluation / f"{prefix}-label-subsets.parquet")
        for prefix in ["sen1", "radar-change"]
    }
    profiles = ROOT / "results/applied_optimization_2026_11_02"
    jobs = []
    by_model = {}
    for job in plan["jobs"]:
        if job.get("worker_lane") != "mps":
            continue
        task, learner = job["task"], job["learner"]
        special = task in {"terramind", "prithvi", "copernicus"} and learner == "native"
        profile = (
            profiles / f"{task}-{learner}-pool-float32.json"
            if special
            else profiles / f"{task}-{learner}-mps-fast.json"
        )
        records = json.loads(profile.read_text())["profiles"]
        batch = int(job["command"][job["command"].index("--batch-size") + 1])
        row = next(r for r in records if r["batch"] == batch and r["status"] == "passed")
        table = tables["radar-change" if task == "copernicus" else "sen1"]
        selected = table[
            (table.fold == job["fold"])
            & (table.seed == job["seed"])
            & (table.budget == job["budget"])
        ]
        examples = len(selected) * (64 if task == "galileo" else 1)
        epochs = 100 if task == "terramind" else 50
        seconds = examples * epochs * job["learning_rate_candidates"] / row["examples_per_s"]
        key = f"{task}/{learner}"
        by_model[key] = by_model.get(key, 0) + seconds
        jobs.append(
            dict(
                job=job["id"],
                examples=examples,
                epochs=epochs,
                candidates=job["learning_rate_candidates"],
                training_seconds=seconds,
                profile=str(profile.relative_to(ROOT)),
                profile_sha256=sha(profile),
            )
        )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    atomic(
        a.output,
        dict(
            plan_sha256=sha(a.plan),
            status="full_epoch_training_workload_extrapolation_not_calendar_ETA_or_early_stop_prediction",
            gpu_training_days=sum(by_model.values()) / 86400,
            by_model_gpu_training_days={k: v / 86400 for k, v in by_model.items()},
            limitations=__doc__,
            jobs=jobs,
        ),
    )
    print(json.dumps(dict(gpu_training_days=sum(by_model.values()) / 86400)))


if __name__ == "__main__":
    main()
