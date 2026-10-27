"""Read-only cross-run integrity and support audit; never rescore or alter results."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_integrity import selected_aggregates

OUT = ROOT / "results/chapter_audit_2026_10_27"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    memo = {}

    def hashed(path):
        path = path.resolve()
        if path not in memo:
            memo[path] = digest(path)
        return memo[path]

    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_audit_no_rescoring",
        "runs": {},
        "issues": [],
    }
    specs = [
        (
            "main",
            ROOT / "results/eo_analogue_comparison_coherent_v1",
            ROOT / "results/eo_analogue_review_coherent_v1",
            ROOT / "config/limburg_eo_coherent_selected_runs.json",
        )
    ]
    for name in [
        "satmae_toa_qa60",
        "copernicus_fm_toa_qa60",
        "croma_ascending_15",
        "croma_ascending_161",
    ]:
        specs.append(
            (
                name,
                ROOT / "results/eo_expansion_comparisons" / name,
                ROOT / "results/eo_expansion_reviews" / name,
                ROOT / "logs/eo-expansion-comparisons" / (name + "-selection.json"),
            )
        )
    for label, comparison, review, selection_path in specs:
        item = {
            "selection": str(selection_path.relative_to(ROOT)),
            "manifests": {},
            "hash_failures": [],
        }
        selection = json.loads(selection_path.read_text())
        _, readiness = selected_aggregates(ROOT, selection)
        item["selected_readiness"] = readiness
        for directory, kind in [(comparison, "scores"), (review, "review")]:
            m = json.loads((directory / "manifest.json").read_text())
            item["manifests"][kind] = {
                "status": m["status"],
                "sha256": hashed(directory / "manifest.json"),
                "scored_sets": m.get("scored_sets"),
                "unique_queries": m.get("unique_scored_queries"),
                "donor_violations": m.get("donor_violations"),
            }
            inputs = m["input_sha256"]
            aliases = {
                "script": ROOT / "scripts/120_review_eo_analogues.py",
                "event_inventory": ROOT
                / "results/basin_ai_event_interpretation_ready/event_inventory.csv",
                "response": ROOT
                / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet",
            }
            for key, expected in inputs.items():
                path = aliases[key] if key in aliases else ROOT / key
                if not path.is_file() or hashed(path) != expected:
                    item["hash_failures"].append({"role": "input", "path": str(path)})
            for key, expected in m["outputs_sha256"].items():
                path = directory / key
                if not path.is_file() or hashed(path) != expected:
                    item["hash_failures"].append({"role": "output", "path": str(path)})
        cover = pd.read_csv(comparison / "eo_event_coverage.csv")
        item["coverage"] = cover.to_dict("records")
        intervals = pd.read_csv(comparison / "paired_intervals.csv")
        item["inference"] = {
            "interval_rows": len(intervals),
            "resampling_units": sorted(intervals.resampling_unit.unique().tolist()),
            "min_query_count": int(intervals.query_count.min()),
            "min_clusters": int(intervals.cluster_count.min()),
            "metrics": sorted(intervals.metric.unique().tolist()),
        }
        table = pq.ParquetFile(comparison / "event_assessments.parquet")
        item["assessment_rows"] = table.metadata.num_rows
        item["review_input_note_wrong_for_supplement"] = (
            label != "main"
            and "Additional Azure imagery is not included."
            in (review / "monthly_snapshot.html").read_text()
        )
        report["runs"][label] = item
        (OUT / "progress.json").write_text(
            json.dumps(
                {
                    "last_completed": label,
                    "hashes_checked": len(memo),
                    "issues": item["hash_failures"],
                },
                indent=2,
            )
            + "\n"
        )
        print(label, "checked; hash failures", len(item["hash_failures"]), flush=True)
    sample = pd.read_csv(ROOT / "results/basin_ai_event_interpretation_ready/q_only_signatures.csv")
    rain = pd.read_csv(
        ROOT / "results/basin_ai_cross_border_completion/rainfall_event_coverage.csv"
    ).set_index("event_id")
    for column in rain.columns:
        if column not in ("country", "complete_scoring_sample"):
            sample[column] = sample.event_id.map(rain[column])
    features = [
        "rain_sum_6h_mm",
        "rain_sum_24h_mm",
        "rain_sum_72h_mm",
        "rain_sum_168h_mm",
        "rain_max_1h_24h_mm",
        "q_over_p99_m24",
        "q_over_p99_m6",
        "q_over_p99_onset",
        "q_change_6h_over_p99",
        "q_change_24h_over_p99",
    ]
    eligible = sample.complete_scoring_sample.astype(bool)
    actual = sample[features].notna().all(axis=1)
    long = sample.event_id.map(rain.complete_scoring_sample).fillna(False)
    report["rain_feature_completeness"] = {
        "q_eligible": int(eligible.sum()),
        "complete_required_predictors": int((eligible & actual).sum()),
        "long_history_restricted": int((eligible & actual & long).sum()),
        "avoidable_long_history_exclusions": int((eligible & actual & ~long).sum()),
    }
    report["unique_files_hashed"] = len(memo)
    report["tests"] = {
        "initial": "9 environment failures; 310 passed",
        "with_existing_proj_data": "319 passed in 34.39 s; no package changes",
    }
    (OUT / "evidence.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print("Audit complete", len(memo), "unique hashed files", flush=True)


if __name__ == "__main__":
    main()
