"""Regenerate the November 10 review from completed benchmark and reference files."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

SOURCE = Path("results/applied_study_v5/ready-v2/synthesis/final")
OUTPUT = Path("results/findings-review-2026-11-10/summary.json")
TASKS = ("terramind", "galileo", "prithvi", "copernicus")
BUDGETS = (1.0, 0.2, 0.05)
LEARNERS = ("native", "unet", "unet_standard", "linear", "physical")


def timing_range(rows, field):
    values = [row[field] for row in rows if isinstance(row.get(field), (float, int))]
    return [min(values), median(values), max(values)] if values else None


def benchmark_summary(jobs, task, budget, learner):
    # The physical baseline uses no labels, so it enters every budget comparison.
    prefix = f"{task}-{learner}-group"
    rows = [
        row
        for key, row in jobs.items()
        if key.startswith(prefix) and (learner == "physical" or f"-{budget:g}-" in key)
    ]
    event_scores = defaultdict(list)
    for row in rows:
        for event, metrics in row["target_event_metrics"].items():
            if metrics["iou"] is not None:
                event_scores[event].append(metrics["iou"])
    # Give each event equal weight after averaging its repeated scores.
    event_iou = {event: mean(values) for event, values in event_scores.items()}
    fractions = [row["label_accounting"].get("combined_selection_label_fraction") for row in rows]
    fractions = [fraction for fraction in fractions if fraction is not None]
    return {
        "jobs": len(rows),
        "mean_event_iou": mean(event_iou.values()),
        "event_iou": event_iou,
        "tuning_seconds_min_median_max": timing_range(rows, "tuning_wall_s"),
        "scoring_seconds_min_median_max": timing_range(rows, "test_scoring_wall_s"),
        "lr_boundary": sum(bool(row.get("learning_rate_boundary")) for row in rows),
        "epoch_at_ceiling": sum(bool(row.get("epoch_at_ceiling")) for row in rows),
        "failed_candidates": sum(row.get("failed_candidates", 0) for row in rows),
        "combined_label_fraction_range": [min(fractions), max(fractions)] if fractions else None,
    }


def local_summary(task):
    scores = defaultdict(lambda: defaultdict(list))
    metadata = {}
    for path in (SOURCE / "local").glob(f"{task}-*-reference-agreement.json"):
        for row in json.loads(path.read_text())["case_summaries"]:
            case = row["case"]
            metrics = row["support"]["common"]
            scores[case][row["model"]].append(metrics["iou"])
            metadata[case] = {
                "offset_hours": row["reference_offset_hours"],
                "dependence": row["reference_dependence"],
                "coverage": metrics["coverage_fraction"],
                "support_pixels": metrics["support_pixels"],
                "reference_positive_pixels": metrics["tp"] + metrics["fn"],
            }
    return {
        case: {
            "meta": metadata[case],
            "mean_iou": {
                model: mean(values) if all(value is not None for value in values) else None
                for model, values in models.items()
            },
            "repeats": {model: len(values) for model, values in models.items()},
        }
        for case, models in scores.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    output = parser.parse_args().output

    source = (SOURCE / "benchmark.json").read_bytes()
    jobs = json.loads(source)["job_ledger"]
    benchmark = {
        task: {
            str(budget): {
                learner: benchmark_summary(jobs, task, budget, learner) for learner in LEARNERS
            }
            for budget in BUDGETS
        }
        for task in TASKS
    }
    print("BENCHMARK IOU native/unet/standard/linear/physical")
    for task, budgets in benchmark.items():
        for budget, models in budgets.items():
            reference = models["native"]
            print(
                task,
                budget,
                [round(row["mean_event_iou"], 3) for row in models.values()],
                "labels",
                reference["combined_label_fraction_range"],
                "flags",
                [reference[key] for key in ("lr_boundary", "epoch_at_ceiling")],
            )

    local = {task: local_summary(task) for task in TASKS}
    for task, cases in local.items():
        offsets = [row["meta"]["offset_hours"] for row in cases.values()]
        print("LOCAL", task, "cases", len(cases), "offset range", min(offsets), max(offsets))
        for case, row in cases.items():
            metadata = row["meta"]
            print(
                case.split(":")[0],
                round(metadata["offset_hours"], 1),
                round(metadata["coverage"], 3),
                metadata["reference_positive_pixels"],
                {
                    model: round(value, 3) if value is not None else None
                    for model, value in row["mean_iou"].items()
                },
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "benchmark": benchmark,
                "local": local,
                "source_sha256": hashlib.sha256(source).hexdigest(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
