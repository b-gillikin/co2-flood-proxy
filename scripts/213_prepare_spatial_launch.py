"""Version the full1908-job grid after runtime/cache reconciliation; no fitting."""

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from applied_execution import sha


def refreshed_plan(old):
    plan = copy.deepcopy(old)
    caches = {
        "galileo": "data/processed/limburg_applied_galileo_spatial_v2",
        "copernicus": "data/processed/limburg_copernicus_spatial_v1",
    }
    for j in plan["jobs"]:
        if j["learner"] == "physical":
            continue
        c = j["command"]
        c[c.index("--device") + 1] = "mps"
        j["resource"] = "mps"
        if "--feature-cache" in c:
            c[c.index("--feature-cache") + 1] = caches[j["task"]]
        elif j["task"] == "copernicus" and j["learner"] == "native":
            c += ["--feature-cache", caches["copernicus"]]
        root = "results/applied_study_v3/tuning"
        c += ["--output-root", root]
        batch = int(c[c.index("--batch-size") + 1])
        epochs = 100 if j["task"] == "terramind" else 50
        j["output"] = f"{root}/{j['id']}-mps-b{batch}-e{epochs}"
        j["local_application"] = j["budget"] == 1.0
    first = {
        t: min(j["fold"] for j in plan["jobs"] if j["task"] == t)
        for t in caches | {"terramind": "", "prithvi": ""}
    }

    def order(j):
        if j["learner"] == "physical":
            return (-1, 0, 0, 0, "", 0)
        wave = j["budget"] == 1.0 and j["seed"] == 42 and j["fold"] == first[j["task"]]
        stage = 0 if wave else {1.0: 1, 0.2: 2, 0.05: 3}[j["budget"]]
        return (
            stage,
            {"linear": 0, "unet": 1, "native": 2, "unet_standard": 3}[j["learner"]],
            {"galileo": 0, "prithvi": 1, "terramind": 2, "copernicus": 3}[j["task"]],
            j["seed"],
            j["fold"],
            j["budget"],
        )

    plan["jobs"].sort(key=order)
    plan.update(
        schema_version=3,
        status="ready_to_launch",
        cache_paths=caches,
        scheduling="All neural fits use MPS; Copernicus frozen CPU Fourier features cached once. One device owner, one background verified-offload worker. First wave is first held fold/seed42/full labels in each task; all remaining folds/seeds/budgets retained.",
        local_application="Every full-label fit, all folds/seeds; low-label primary inference remains benchmark evaluation. Hold fixed source/QA/temporal pairing and reference limitations; no local-map tuning.",
    )
    return plan


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument(
        "--output", type=Path, default=ROOT / "results/applied_study_v3/execution-plan.json"
    )
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("Preserve existing launch manifest")
    old = ROOT / "results/applied_study_v2/execution-plan.json"
    plan = refreshed_plan(json.loads(old.read_text()))
    paths = list((ROOT / "src").glob("applied*.py"))
    paths += [
        ROOT / "scripts" / n
        for n in [
            "185_run_applied_water.py",
            "190_extract_applied_galileo.py",
            "192_tune_applied_water.py",
            "195_score_local_reference_agreement.py",
            "198_summarize_applied_comparisons.py",
            "202_profile_applied_supplements.py",
            "207_preserve_applied_results.py",
            "210_cache_copernicus_spatial.py",
            "211_check_copernicus_cached_runtime.py",
            "213_prepare_spatial_launch.py",
            "214_queue_spatial_comparisons.py",
            "215_apply_local_spatial_models.py",
            "216_summarize_local_comparisons.py",
            "217_update_spatial_readout.py",
        ]
    ]
    plan["source_hashes"] = {str(x.relative_to(ROOT)): sha(x) for x in paths}
    plan["parent_plan_sha256"] = sha(old)
    plan["cache_index_hashes"] = {
        t: sha(ROOT / p / "index.json") for t, p in plan["cache_paths"].items()
    }
    for t, p in plan["cache_paths"].items():
        index = json.loads((ROOT / p / "index.json").read_text())
        if index["status"] != "completed" or index["completed"] != (
            446 if t == "galileo" else 5000
        ):
            raise ValueError("Incomplete cache")
        for n, h in index["source_hashes"].items():
            if sha(ROOT / n) != h:
                raise ValueError("Cache contract changed: " + n)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                neural_jobs=plan["neural_tuning_jobs"],
                candidate_fits=plan["neural_candidate_fits"],
                physical_controls=53,
                first_wave=sum(
                    j.get("budget") == 1
                    and j.get("seed") == 42
                    and j.get("fold")
                    == min(x["fold"] for x in plan["jobs"] if x["task"] == j["task"])
                    for j in plan["jobs"]
                    if j["learner"] != "physical"
                ),
            )
        )
    )


if __name__ == "__main__":
    main()
