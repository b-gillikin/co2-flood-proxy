"""Read-only execution/storage check. Never launch fits or remove checkpoints."""

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def check_plan(plan):
    jobs = plan["jobs"]
    if len({j["id"] for j in jobs}) != len(jobs):
        raise ValueError("Duplicate job ID")
    if len({j["output"] for j in jobs}) != len(jobs):
        raise ValueError("Duplicate output directory")
    expected_folds = {"terramind": 11, "galileo": 11, "prithvi": 11, "copernicus": 20}
    for task, folds in expected_folds.items():
        rows = [j for j in jobs if j["task"] == task]
        for learner in ["native", "unet", "unet_standard", "linear"]:
            subset = [j for j in rows if j["learner"] == learner]
            combinations = set()
            for j in subset:
                c = j["command"]
                combinations.add(
                    (j["fold"], float(c[c.index("--budget") + 1]), int(c[c.index("--seed") + 1]))
                )
                if "--evaluate-selected" not in c or "--run" not in c:
                    raise ValueError("Missing selected-test scoring")
                if not Path(c[0]).is_file():
                    raise ValueError("Missing runtime")
            required = {
                (f, b, s)
                for f in {j["fold"] for j in rows}
                for b in [1.0, 0.2, 0.05]
                for s in [42, 1729, 31415]
            }
            if (
                len(required) != folds * 9
                or combinations != required
                or len(subset) != len(required)
            ):
                raise ValueError(f"Incomplete crossproduct: {task}/{learner}")
    return Counter(j["task"] + "/" + j["learner"] for j in jobs)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--output", type=Path, default=ROOT / "results/applied_study_v2/execution-audit.json"
    )
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("Choose a versioned audit output")
    path = ROOT / "results/applied_study_v2/execution-plan.json"
    plan = json.loads(path.read_text())
    counts = check_plan(plan)
    for relative, expected in plan["input_hashes"].items():
        if digest(ROOT / relative) != expected:
            raise ValueError("Execution partition changed")
    queues = []
    for path in (ROOT / "results").rglob("progress.json"):
        if (
            "supplemental-profile-queue" not in str(path)
            and "profile-queue" not in str(path)
            and "profile_queue" not in str(path)
            and "individual_experiments_v1/queue" not in str(path)
        ):
            continue
        r = json.loads(path.read_text())
        checks = {
            name: digest(ROOT / name) == value for name, value in r.get("source_hashes", {}).items()
        }
        # Completed queues retain their original code version. A documented
        # later repair must not silently rewrite that historical provenance.
        terminal = {"complete", "complete_with_failures", "completed", "finished_with_failures"}
        if not all(checks.values()) and r.get("status") not in terminal:
            raise ValueError("Active protected queue source changed")
        queues.append(
            dict(path=str(path.relative_to(ROOT)), status=r.get("status"), source_checks=checks)
        )
    profiles = []
    for path in (ROOT / "results/applied_study_v2/supplemental-profiles").glob("*/complete.json"):
        r = json.loads(path.read_text())
        n = counts[f"{r['task']}/{r['learner']}"]
        profiles.append(
            dict(
                task=r["task"],
                learner=r["learner"],
                device=r["device"],
                state_bytes=r["model_state_bytes"],
                tuning_jobs=n,
                full_grid_tensor_checkpoint_bytes=3 * n * r["model_state_bytes"],
                one_job_tensor_checkpoint_bytes=3 * r["model_state_bytes"],
                receipt=str(path.relative_to(ROOT)),
            )
        )
    result = dict(
        status="checked_not_launched",
        job_counts=dict(counts),
        total_jobs=len(plan["jobs"]),
        candidate_fits=plan["neural_candidate_fits"],
        profiles=profiles,
        protected_queues=queues,
        free_gib=shutil.disk_usage(ROOT).free / 1024**3,
        measured_checkpoint_archive_lower_bound_gib=sum(
            r["full_grid_tensor_checkpoint_bytes"] for r in profiles
        )
        / 1024**3,
        checkpoint_storage_note="Lower bound: only measured supplemental profiles; excludes other task states, serialization overhead, predictions and optimizer memory. No activation-memory or whole-grid ETA claim.",
        execution_contract=[
            "One MPS owner; existing extraction and original profiles precede supplemental MPS profiles.",
            "Run all 1908 tuning jobs/5724 candidates, full labels then20/5%, all folds/seeds.",
            "Require measured device/batch feasibility; CPU Copernicus timings cannot be ranked directly against MPS tasks.",
            "Retain50GiB reserve. Archive each completed tuning directory with checksummed readback before any later local removal; never remove active jobs or source inputs.",
            "No epoch-level resume: checkpoints contain inference state only, not optimizer/RNG. Preserve failed output and restart into a versioned directory.",
            "Source code/weights/partitions, all candidate logs, validation selection, selected checkpoint and every test prediction travel together.",
            "Do not infer accuracy from profiling; do not tune after viewing held-event errors.",
        ],
    )
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "status",
                    "total_jobs",
                    "candidate_fits",
                    "free_gib",
                    "measured_checkpoint_archive_lower_bound_gib",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
