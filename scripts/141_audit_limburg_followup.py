"""Read-only integrity, metric and interval audit of the new downstream results."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_followup import METRICS
from src.eo_inputs import sha256


def main():
    out = ROOT / "results/chapter_reaudit_2026_10_27"
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "issues": [],
        "manifests": {},
        "metrics": {},
        "intervals": {},
    }
    memo = {}

    def digest(p):
        p = p.resolve()
        if p not in memo:
            memo[p] = sha256(p)
        return memo[p]

    aliases = {
        "event_inventory": ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv",
        "response": ROOT
        / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet",
    }
    folders = [
        ROOT / "results/eo_analogue_comparison_rain168_v1",
        ROOT / "results/eo_followup_independent_2026_10_27",
    ]
    folders += sorted((ROOT / "results/eo_review_provenance_v2").iterdir())
    final = ROOT / "results/eo_followup_2026_10_27"
    report["pending_final_combination"] = not (final / "manifest.json").exists()
    if not report["pending_final_combination"]:
        folders.append(final)
    for folder in folders:
        path = folder / "manifest.json"
        m = json.loads(path.read_text())
        if m["status"] != "completed":
            report["issues"].append({"path": str(path), "issue": "incomplete"})
        for section in ["input_sha256", "source_sha256", "outputs_sha256"]:
            for name, expected in m.get(section, {}).items():
                p = folder / name if section == "outputs_sha256" else aliases.get(name, ROOT / name)
                if not p.is_file() or digest(p) != expected:
                    report["issues"].append({"path": str(p), "issue": "hash mismatch"})
        report["manifests"][str(folder.relative_to(ROOT))] = digest(path)
    for folder, name in [
        (folders[0], "event_assessments.parquet"),
        (folders[1], "common_route_assessments.parquet"),
    ]:
        path = folder / name
        columns = METRICS + [
            "actual_donor_count",
            "target_k",
            "candidate_storm_count",
            "candidate_count",
        ]
        rows = invalid = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=100000, columns=columns):
            f = batch.to_pandas()
            values = f[METRICS].to_numpy()
            bad = (~np.isfinite(values) | (values < 0)).any(axis=1)
            bad |= (f.actual_donor_count < 1) | (f.actual_donor_count > f.target_k)
            bad |= (f.actual_donor_count > f.candidate_storm_count) | (
                f.candidate_storm_count > f.candidate_count
            )
            rows += len(f)
            invalid += int(bad.sum())
        report["metrics"][str(path.relative_to(ROOT))] = {"rows": rows, "invalid": invalid}
        if invalid:
            report["issues"].append({"path": str(path), "issue": "metric/donor-count contract"})
    interval_paths = [
        (name, folders[1] / name)
        for name in ["common_route_intervals.parquet", "archive_intervals.parquet"]
    ]
    if not report["pending_final_combination"]:
        interval_paths.append(
            ("final/archive_intervals.parquet", final / "archive_intervals.parquet")
        )
    for name, path in interval_paths:
        rows = invalid = undefined = 0
        for batch in pq.ParquetFile(path).iter_batches(
            batch_size=100000,
            columns=[
                "difference",
                "query_count",
                "cluster_count",
                "draws",
                "finite_draws",
                "lower",
                "upper",
            ],
        ):
            f = batch.to_pandas()
            enough = f.cluster_count.ge(2)
            bad = (
                ~np.isfinite(f.difference)
                | f.query_count.lt(f.cluster_count)
                | f.cluster_count.lt(1)
            )
            bad |= enough & (
                ~np.isfinite(f.lower)
                | ~np.isfinite(f.upper)
                | f.lower.gt(f.upper)
                | f.draws.ne(9999)
                | f.finite_draws.ne(9999)
            )
            bad |= ~enough & (f.lower.notna() | f.upper.notna() | f.draws.ne(0))
            rows += len(f)
            invalid += int(bad.sum())
            undefined += int((~enough).sum())
        report["intervals"][name] = {
            "rows": rows,
            "invalid": invalid,
            "undefined_small_cluster_intervals": undefined,
        }
        if invalid:
            report["issues"].append({"path": str(path), "issue": "interval contract"})
    # Preserve an audit-time index of the actual matched-route donor trace. This
    # supplements the parent manifest; it is not a retroactive run-time receipt.
    cache = ROOT / "data/processed/eo_followup_route_retrieval_cache"
    ledger = {}
    for path in sorted(cache.glob("*/manifest.json")):
        m = json.loads(path.read_text())
        ledger[str(path.relative_to(ROOT))] = digest(path)
        for name, expected in m["outputs_sha256"].items():
            p = path.parent / name
            ledger[str(p.relative_to(ROOT))] = digest(p)
            if digest(p) != expected:
                report["issues"].append({"path": str(p), "issue": "route-cache hash mismatch"})
    report["route_trace"] = {
        "cache_entries": len(ledger) // 3,
        "files": len(ledger),
        "role": "audit-time donor-trace preservation index, not a new empirical run",
    }
    report["rainfall_scored_query_union"] = {}
    for label, folder in [
        ("original", ROOT / "results/eo_review_provenance_v2/main"),
        ("actual_feature_complete", ROOT / "results/eo_review_provenance_v2/rain168"),
    ]:
        f = pq.read_table(
            folder / "browser_case_index.parquet", columns=["cohort", "query_event_id"]
        ).to_pandas()
        report["rainfall_scored_query_union"][label] = int(
            f.loc[f.cohort.str.startswith("rain"), "query_event_id"].nunique()
        )
    (out / "route-cache-hashes.json").write_text(json.dumps(ledger, indent=2) + "\n")
    report["unique_files_hashed"] = len(memo)
    report["audit_source_sha256"] = sha256(Path(__file__))
    (out / "followup-integrity.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return bool(report["issues"])


if __name__ == "__main__":
    raise SystemExit(main())
