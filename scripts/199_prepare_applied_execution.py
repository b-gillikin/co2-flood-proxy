"""Prepare the COMPLETE event/label/seed grid; do not launch training.

Full-label stage first, then20/5% stages, preserving every event and seed.
Commands are explicit per task; physical controls calibrate once per fold and
are reused across neural budgets/seeds. Profiles determine device/batch choices.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--output", type=Path, default=ROOT / "results/applied_study_v2/execution-plan.json"
    )
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("Preserve the execution plan; choose a versioned output")
    jobs = []
    inputs = {}
    for task in ["terramind", "galileo", "prithvi", "copernicus"]:
        prefix = "radar-change" if task == "copernicus" else "sen1"
        path = ROOT / f"results/applied_study_v1/evaluation/{prefix}-grouped-folds.parquet"
        folds = pd.read_parquet(path)
        inputs[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        runtime = {"galileo": "galileo", "copernicus": "copernicus"}.get(task, "spatial")
        python = str(ROOT / f".venvs-applied/{runtime}/bin/python")
        batch = 64 if task == "galileo" else (8 if task == "terramind" else 2)
        device = "cpu" if task == "copernicus" else "mps"
        epochs = 100 if task == "terramind" else 50
        for fold in sorted(folds.fold.unique()):
            # CPU physical preprocessing does not require model-specific MMCV.
            command = [
                str(ROOT / ".venvs-applied/spatial/bin/python"),
                "scripts/197_run_applied_physical_controls.py",
                "--task",
                task,
                "--fold",
                str(fold),
                "--run",
                "--evaluate-selected",
            ]
            jobs.append(
                dict(
                    id=f"{task}-physical-{fold}",
                    task=task,
                    learner="physical",
                    fold=str(fold),
                    stage="full-label",
                    resource="cpu",
                    command=command,
                    output=f"results/applied_study_v2/physical/{task}-{fold}",
                )
            )
        for budget, stage in [
            (1.0, "full-label"),
            (0.2, "20pct-training-labels"),
            (0.05, "5pct-training-labels"),
        ]:
            for fold in sorted(folds.fold.unique()):
                for seed in [42, 1729, 31415]:
                    for learner in ["native", "unet", "unet_standard", "linear"]:
                        command = [
                            python,
                            "scripts/192_tune_applied_water.py",
                            "--task",
                            task,
                            "--learner",
                            learner,
                            "--fold",
                            str(fold),
                            "--budget",
                            str(budget),
                            "--seed",
                            str(seed),
                            "--batch-size",
                            str(batch),
                            "--device",
                            device,
                            "--run",
                            "--evaluate-selected",
                        ]
                        if task == "galileo" and learner == "native":
                            command += [
                                "--feature-cache",
                                "data/processed/limburg_applied_galileo_spatial_v1",
                            ]
                        ident = f"{task}-{learner}-{fold}-{budget:g}-{seed}"
                        jobs.append(
                            dict(
                                id=ident,
                                task=task,
                                learner=learner,
                                fold=str(fold),
                                budget=budget,
                                seed=seed,
                                stage=stage,
                                resource=device,
                                command=command,
                                output=f"results/applied_study_v2/tuning/{ident}-{device}-b{batch}-e{epochs}",
                            )
                        )
    priority = {"full-label": 0, "20pct-training-labels": 1, "5pct-training-labels": 2}
    jobs.sort(key=lambda j: priority[j["stage"]])
    n = sum(j["learner"] != "physical" for j in jobs)
    output = dict(
        schema_version=2,
        status="prepared_not_launched",
        jobs=jobs,
        input_hashes=inputs,
        neural_tuning_jobs=n,
        neural_candidate_fits=n * 3,
        physical_calibrations=len(jobs) - n,
        scheduling="One MPS owner. Native Copernicus CPU until device profile. Preserve existing workers. Run all stages; staging does not reduce the census.",
        storage="50GiB reserve; verified offload completed task outputs before rotating. Do not delete other chapters. Never crop test census for storage.",
        scientific_scope="Same four task pipelines, all446 water chips/5000 radar records, all folds and three seeds/budgets; stronger conventional U-Net added alongside compact control.",
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k not in ["jobs", "input_hashes"]}))


if __name__ == "__main__":
    main()
