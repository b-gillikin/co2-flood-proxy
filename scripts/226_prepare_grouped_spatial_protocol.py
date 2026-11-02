"""Prepare five-fold whole-event census, common labels, and a smaller fit grid.

Original leave-event-out records remain historical supporting analyses. No
raster/weight/feature extraction is repeated or input data removed.
"""

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd

from applied_execution import atomic, sha
from applied_grouped_protocol import grouped_partitions


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "results/applied_study_v5")
    a = p.parse_args()
    base = a.output.resolve()
    if (base / "execution-plan.json").exists():
        raise FileExistsError("Version frozen plans")
    parts = base / "evaluation"
    parts.mkdir(parents=True, exist_ok=True)
    original = ROOT / "results/applied_study_v1/evaluation"
    summaries = {}
    for prefix, name in [
        ("sen1", "sen1-chip-inventory.parquet"),
        ("radar-change", "radar-change-inventory.parquet"),
    ]:
        shutil.copyfile(original / name, parts / name)
        inventory = pd.read_parquet(parts / name)
        folds, subsets = grouped_partitions(inventory)
        folds.to_parquet(parts / f"{prefix}-grouped-folds.parquet", index=False)
        subsets.to_parquet(parts / f"{prefix}-label-subsets.parquet", index=False)
        summaries[prefix] = dict(
            records=len(inventory),
            events=int(inventory.event.nunique()),
            folds=5,
            role_counts=folds.groupby(["fold", "role"]).size().unstack().to_dict("index"),
            tested_once=not folds[folds.role == "test"].chip.duplicated().any(),
        )
    parentpath = ROOT / "results/applied_study_v4/full-label-tuning-reuse-v1/execution-plan.json"
    parent = json.loads(parentpath.read_text())
    neural = []
    physical = []
    cpu = 0
    for task in ["galileo", "prithvi", "terramind", "copernicus"]:
        templates = {
            j["learner"]: j
            for j in parent["jobs"]
            if j["task"] == task
            and j["learner"] != "physical"
            and j["budget"] == 1.0
            and j["seed"] == 42
        }
        for fold in [f"group{i:02d}" for i in range(1, 6)]:
            runtime = templates["linear"]["command"][0]
            physical.append(
                dict(
                    id=f"{task}-physical-{fold}",
                    task=task,
                    learner="physical",
                    fold=fold,
                    stage="physical",
                    resource="cpu",
                    command=[
                        runtime,
                        "scripts/197_run_applied_physical_controls.py",
                        "--task",
                        task,
                        "--fold",
                        fold,
                        "--evaluation-dir",
                        str(parts),
                        "--output-root",
                        str(base / "physical"),
                        "--run",
                        "--evaluate-selected",
                    ],
                    output=str((base / "physical" / f"{task}-{fold}").relative_to(ROOT)),
                )
            )
            for budget in [1.0, 0.2, 0.05]:
                for seed in [42, 1729, 31415]:
                    for learner in ["linear", "unet", "native", "unet_standard"]:
                        j = copy.deepcopy(templates[learner])
                        command = j["command"]
                        for flag in ["--fixed-lr-from"]:
                            if flag in command:
                                position = command.index(flag)
                                del command[position : position + 2]
                        is_cpu = j["resource"] == "cpu"
                        j.update(
                            id=f"{task}-{learner}-{fold}-{budget:g}-{seed}",
                            fold=fold,
                            budget=budget,
                            seed=seed,
                            worker_lane=f"cpu-{cpu % 2}" if is_cpu else "mps",
                            local_application=budget == 1.0,
                            stage="full-label" if budget == 1.0 else "reduced-label",
                        )
                        cpu += int(is_cpu)
                        for flag, value in [
                            ("--fold", fold),
                            ("--budget", str(budget)),
                            ("--seed", str(seed)),
                            ("--output-root", str(base / "tuning")),
                        ]:
                            command[command.index(flag) + 1] = value
                        epochs = 100 if task == "terramind" else 50
                        minimum = 30 if task == "terramind" else 15
                        command += [
                            "--evaluation-dir",
                            str(parts),
                            "--physical-root",
                            str(base / "physical"),
                            "--shared-label-mask",
                            "--early-stop-patience",
                            "10",
                            "--early-stop-min-epochs",
                            str(minimum),
                            "--early-stop-min-delta",
                            "0.0001",
                        ]
                        batch = command[command.index("--batch-size") + 1]
                        j["output"] = str(
                            (
                                base
                                / "tuning"
                                / f"{task}-{learner}-{fold}-{budget:g}-{seed}-{j['resource']}-b{batch}-e{epochs}"
                            ).relative_to(ROOT)
                        )
                        j.pop("previous_failed_output", None)
                        j.pop("tuning_source_output", None)
                        neural.append(j)
    # Keep first wave broad; never pick model order from accuracy.
    learner_order = {"linear": 0, "unet": 1, "native": 2, "unet_standard": 3}
    task_order = {"galileo": 0, "prithvi": 1, "terramind": 2, "copernicus": 3}
    neural.sort(
        key=lambda j: (
            j["budget"] != 1.0,
            j["budget"] == 0.05,
            j["fold"] != "group01",
            j["seed"] != 42,
            learner_order[j["learner"]],
            task_order[j["task"]],
            j["fold"],
            j["seed"],
        )
    )
    sources = {
        (j["task"], j["learner"], j["fold"], j["budget"]): j["output"]
        for j in neural
        if j["seed"] == 42
    }
    for j in neural:
        j["learning_rate_candidates"] = 3 if j["seed"] == 42 else 1
        if j["seed"] != 42:
            source = sources[j["task"], j["learner"], j["fold"], j["budget"]]
            j["tuning_source_output"] = source
            j["command"] += ["--fixed-lr-from", source]
    jobs = physical + neural
    extra = [
        "src/applied_grouped_protocol.py",
        "scripts/226_prepare_grouped_spatial_protocol.py",
        "scripts/225_estimate_spatial_training_cost.py",
        "scripts/227_launch_grouped_spatial_queue.py",
    ]
    plan = dict(
        parent,
        jobs=jobs,
        tuning_root=str((base / "tuning").relative_to(ROOT)),
        neural_tuning_jobs=len(neural),
        neural_candidate_fits=sum(j["learning_rate_candidates"] for j in neural),
        physical_calibrations=len(physical),
        parent_execution_plan_sha256=sha(parentpath),
        status="prepared_whole_event_grouped_cross_fitting",
        evaluation_directory=str(parts.relative_to(ROOT)),
        evaluation_summary=summaries,
    )
    plan["source_hashes"] = {
        n: sha(ROOT / n)
        for n in set(parent["source_hashes"])
        | set(extra)
        | {"scripts/197_run_applied_physical_controls.py"}
    }
    plan["scientific_scope"] = (
        "Same four tasks and all source events/chips; five whole-event test folds per task; three final seeds and three nested label budgets; no event subsampling"
    )
    plan["scheduling"] = (
        "Two CPU fit lanes and one exclusive MPS fit lane. Broad task/learner first wave, independent of accuracy. Inherited v4 fits drain separately. Verified checkpoint offload continues."
    )
    plan["optimization"] = dict(
        parent["optimization"],
        scientific_census="All 446 hand chips and 5000 radar-change records; every event/chip tested exactly once; five whole-event folds per task",
        tuning="Fixed nested labelled subsets across optimization seeds; tune three rates for seed42 within each fold/budget; repeat seeds reuse that same-mask validation winner",
        early_stopping=dict(
            metric="equal-event validation target-class IoU",
            patience_epochs=10,
            min_delta=0.0001,
            minimum_epochs=dict(terramind=30, others=15),
            ceilings=dict(terramind=100, others=50),
        ),
        tradeoffs="Training uses three of five event groups; seed spread is optimization variation conditional on one label subset, not label-selection uncertainty; fold models are dependent, event bootstrap retains exploratory interpretation",
    )
    plan["input_hashes"] = dict(
        parent["input_hashes"],
        **{str(f.relative_to(ROOT)): sha(f) for f in parts.glob("*.parquet")},
    )
    atomic(base / "execution-plan.json", plan)
    for lane in ["cpu-0", "cpu-1", "mps"]:
        sub = copy.deepcopy(plan)
        sub["jobs"] = physical + [j for j in neural if j["worker_lane"] == lane]
        sub["lane"] = lane
        sub["master_plan_sha256"] = sha(base / "execution-plan.json")
        directory = base / lane
        directory.mkdir(exist_ok=True)
        atomic(directory / "execution-plan.json", sub)
    atomic(
        base / "design-summary.json",
        dict(
            final_fits=len(neural),
            candidate_fits=plan["neural_candidate_fits"],
            physical_controls=len(physical),
            evaluation=summaries,
            policy=plan["optimization"],
        ),
    )
    print(
        json.dumps(
            dict(
                final_fits=len(neural),
                candidate_fits=plan["neural_candidate_fits"],
                physical_controls=len(physical),
            )
        )
    )


if __name__ == "__main__":
    main()
