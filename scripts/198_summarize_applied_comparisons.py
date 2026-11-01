"""Consolidate selected tests, event uncertainty and seed variation.

Reads only frozen selection/test receipts, never selects a model or rate.
Partial runs remain a ledger of missing folds/seeds, not a smaller final census.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from applied_evaluation import count_metrics, paired_event_summary


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("Preserve the previous readout")
    plan = json.loads(a.plan.read_text())
    observed, ledger, hashes = {}, {}, {}
    for job in plan["jobs"]:
        directory = ROOT / job["output"]
        result = directory / "selected-test.json"
        selection = directory / "selection.json"
        manifest = directory / "manifest.json"
        key = job["id"]
        if not all(f.exists() for f in [result, selection, manifest]):
            ledger[key] = dict(status="pending_or_failed", test_present=result.exists())
            continue
        for f in [result, selection, manifest]:
            name = str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f)
            hashes[name] = hashlib.sha256(f.read_bytes()).hexdigest()
        r = json.loads(result.read_text())
        m = json.loads(manifest.read_text())
        s = json.loads(selection.read_text())
        if s["status"] != "completed":
            raise ValueError("A failed candidate cannot provide a selected test: " + key)
        observed[key] = dict(result=r, manifest=m, job=job)
        ledger[key] = dict(
            status="completed",
            learning_rate_boundary=s.get("learning_rate_grid_boundary"),
            epoch_at_ceiling=s.get("best_epoch_at_ceiling"),
            test_scoring_wall_s=r.get("test_scoring_wall_s"),
            label_accounting=m.get("label_accounting"),
            shared_feature_preparation=m.get("shared_feature_preparation"),
        )
        trials = directory / "trials.json"
        if trials.exists():
            rows = json.loads(trials.read_text())
            ledger[key]["failed_candidates"] = sum(t["status"] != "completed" for t in rows)
            ledger[key]["tuning_wall_s"] = (
                s.get("validation_wall_s")
                if job["learner"] == "physical"
                else sum(t.get("elapsed_s", 0) + t.get("setup_s", 0) for t in rows)
            )
            hashes[str(trials)] = hashlib.sha256(trials.read_bytes()).hexdigest()
        cls = 2 if job["task"] == "copernicus" else 1
        per_event = {}
        for event, matrix in r["confusion"].items():
            matrix = np.asarray(matrix)
            tp = int(matrix[cls, cls])
            fn = int(matrix[cls].sum()) - tp
            fp = int(matrix[:, cls].sum()) - tp
            per_event[event] = count_metrics(
                dict(tp=tp, fn=fn, fp=fp, tn=int(matrix.sum()) - tp - fn - fp)
            )
        ledger[key]["target_event_metrics"] = per_event
        ledger[key]["retained_checkpoint_bytes"] = sum(
            p.stat().st_size for p in directory.glob("trial-*.pt")
        )
        ledger[key]["cost_caveat"] = (
            "Wall time includes the named pipeline stages under recorded contention; not isolated model-only latency. RSS units and training-seed variation remain separate."
        )
    comparisons = []
    # Each event's seed mean is formed first; bootstrap units are events.
    for task in ["terramind", "galileo", "prithvi", "copernicus"]:
        for budget in [1.0, 0.2, 0.05]:
            for baseline in ["unet", "unet_standard", "linear", "physical"]:
                left, right, per_seed, missing = {}, {}, {}, []
                for job in plan["jobs"]:
                    if job["task"] != task or job["learner"] != "native" or job["budget"] != budget:
                        continue
                    refid = (
                        f"{task}-physical-{job['fold']}"
                        if baseline == "physical"
                        else job["id"].replace("-native-", f"-{baseline}-")
                    )
                    if job["id"] not in observed or refid not in observed:
                        missing.append(dict(native=job["id"], control=refid))
                        continue
                    arow, brow = observed[job["id"]], observed[refid]
                    acount, bcount = arow["result"]["confusion"], brow["result"]["confusion"]
                    if set(acount) != set(bcount):
                        raise ValueError("Different event support")
                    # Both pipelines must use the identical source chip census.
                    if (
                        arow["manifest"]["partitions"]["test"]
                        != brow["manifest"]["partitions"]["test"]
                    ):
                        raise ValueError("Different held chips")
                    for event in acount:
                        am, bm = np.array(acount[event]), np.array(bcount[event])
                        if not np.array_equal(am.sum(1), bm.sum(1)):
                            raise ValueError("Different class/reference support")
                        cls = 2 if task == "copernicus" else 1

                        def iou(m, cls=cls):
                            denominator = m[cls].sum() + m[:, cls].sum() - m[cls, cls]
                            return float(m[cls, cls] / denominator) if denominator else None

                        av, bv = iou(am), iou(bm)
                        left.setdefault(event, []).append(av)
                        right.setdefault(event, []).append(bv)
                        per_seed.setdefault(str(job["seed"]), {})[event] = (
                            None if av is None or bv is None else av - bv
                        )
                complete = not missing and bool(left)

                def means(d):
                    # Do not silently drop an undefined seed for one model.
                    return {
                        e: float(np.mean(v)) if all(x is not None for x in v) else None
                        for e, v in d.items()
                    }

                comparisons.append(
                    dict(
                        task=task,
                        budget=budget,
                        control=baseline,
                        complete_census=complete,
                        missing_jobs=missing,
                        per_seed_event_differences=per_seed,
                        seed_mean_differences={
                            seed: float(np.mean(list(values.values())))
                            if values and all(v is not None for v in values.values())
                            else None
                            for seed, values in per_seed.items()
                        },
                        summary=paired_event_summary(means(left), means(right))
                        if complete
                        else None,
                    )
                )
    output = dict(
        job_ledger=ledger,
        comparisons=comparisons,
        input_hashes=hashes,
        interpretation="All planned folds/seeds retained. Incomplete contrasts remain pending. Event bootstrap is exploratory; no pixel/seed independence, country ranking or equivalence claim.",
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
