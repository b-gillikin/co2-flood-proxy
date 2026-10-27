"""Execute the authorized audit follow-up; preserve all original empirical runs."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256

LOG = ROOT / "logs/eo-followup-2026-10-27"
RUNTIME = str(ROOT / ".venvs-eo/terramind/bin/python")
VARIANTS = [
    "satmae_toa_qa60",
    "copernicus_fm_toa_qa60",
    "croma_ascending_15",
    "croma_ascending_161",
]


def verify_review_preserves_numbers(old, new):
    """Exact file checks first; equivalent parquet serialization is acceptable."""
    import itertools

    import pandas as pd
    import pyarrow.parquet as pq

    before = json.loads((old / "manifest.json").read_text())
    for name in before["outputs_sha256"]:
        if name.endswith(".html"):
            continue
        if sha256(old / name) == sha256(new / name):
            continue
        if not name.endswith(".parquet"):
            raise ValueError("Non-HTML review table changed: " + name)
        a = pq.ParquetFile(old / name)
        b = pq.ParquetFile(new / name)
        if a.metadata.num_rows != b.metadata.num_rows:
            raise ValueError("Review row count changed")
        for x, y in itertools.zip_longest(
            a.iter_batches(batch_size=100000), b.iter_batches(batch_size=100000)
        ):
            if x is None or y is None:
                raise ValueError("Review batch count changed")
            pd.testing.assert_frame_equal(x.to_pandas(), y.to_pandas(), check_exact=True)


def write_memo():
    import pandas as pd

    out = ROOT / "results/eo_followup_2026_10_27"
    support = json.loads((out / "common_route_support.json").read_text())
    lines = [
        "# Limburg audit follow-up: results for interpretation",
        "",
        "All original runs remain unchanged. This is an internal research aid, not dissertation prose.",
        "",
        "## What changed",
        "- Review-page provenance now comes from each selected extraction contract; existing numerical review tables were checked unchanged.",
        "- Conventional rainfall eligibility uses actual required predictors (maximum 168 hours), retaining Q/history/target validity.",
        "- Generic historical references use the exact eligible prior archive, with equal mass per storm and equal members within storms.",
        "- Main/supplemental contrasts use common query AND donor universes, not merely equal donor counts.",
        "- No model weights, embeddings, event definitions or encoder settings were changed.",
        "",
        "## Common-route support (before policy/quality restrictions)",
        "| Variant | Context | Cohort | Common eligible events |",
        "|---|---|---|---:|",
    ]
    seen = set()
    for row in support:
        key = (row["variant"], row["kind"], row["cohort"])
        if key in seen:
            continue
        seen.add(key)
        lines.append("| " + " | ".join(map(str, [*key, row["common_eligible_events"]])) + " |")
    lines += [
        "",
        "## Generic-reference contrasts",
        "",
        "Negative differences favor targeted retrieval; positive differences favor the generic archive. The following is the fixed main/pooled/five-donor/all-river available-model view, not a selected best slice. Country and context remain separate. Full other-river, quality, donor-policy and k=10 tables/intervals are retained.",
        "",
        "| Run | Context | Cohort | Arm | Country | Queries | Shape difference | Curve RMSE difference | Duration-error difference (h) |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    f = pd.read_parquet(out / "archive_summary.parquet")
    chosen = f[
        (f.analysis == "main")
        & (f.policy == "pooled")
        & (f.target_k == 5)
        & (f.scenario == "all_rivers")
    ]
    mapping = {
        "main": None,
        "satmae_toa_qa60": "satmae",
        "copernicus_fm_toa_qa60": "copernicus_fm",
        "croma_ascending_15": "croma",
        "croma_ascending_161": "croma",
        "rain168": None,
    }
    for row in chosen.itertuples():
        model = mapping[row.run]
        if row.run in ["main", "rain168"]:
            if row.cohort not in [
                "q_only_all_ten_matched",
                "rain_all_ten_matched",
            ] or not row.arm.endswith("_ttm_state"):
                continue
        elif row.cohort != "q_only_available_" + model or row.arm != model + "_ttm_state":
            continue
        lines.append(
            "| "
            + " | ".join(
                map(
                    str,
                    [
                        row.run,
                        row.kind,
                        row.cohort,
                        row.arm,
                        row.query_country,
                        row.queries,
                        f"{row.mean_peak_scaled_shape_rmse_minus_archive:.5f}",
                        f"{row.ensemble_curve_level_rmse_minus_archive:.5f}",
                        f"{row.duration_estimate_absolute_error_h_minus_archive:.3f}",
                    ],
                )
            )
            + " |"
        )
    route_path = out / "common_route_pairs.parquet"
    if route_path.exists():
        route = pd.read_parquet(route_path)
        selected = route[
            (route.analysis == "main")
            & (route.policy == "pooled")
            & (route.target_k == 5)
            & (route.scenario == "all_rivers")
            & (route.contrast == "supplement_ttm_state_minus_main_ttm_state")
        ]
        keys = ["variant", "kind", "cohort", "query_country"]
        table = (
            selected.groupby(keys, observed=True)
            .agg(
                queries=("query_event_id", "nunique"),
                shape=("mean_peak_scaled_shape_rmse_difference", "mean"),
                curve=("ensemble_curve_level_rmse_difference", "mean"),
            )
            .reset_index()
        )
        lines += [
            "",
            "## Direct supplemental-route differences on common archives",
            "",
            "Fixed main/pooled/five-donor/all-river EO-plus-TTM/state view. Differences are supplemental minus main: negative favors the supplemental route. Both queries and candidate universes are common. These descriptive means are not significance claims; use the paired interval artifact.",
            "",
            "| Variant | Context | Cohort | Country | Queries | Shape difference | Curve RMSE difference |",
            "|---|---|---|---|---:|---:|---:|",
        ]
        for row in table.itertuples():
            lines.append(
                "| "
                + " | ".join(
                    map(
                        str,
                        [
                            row.variant,
                            row.kind,
                            row.cohort,
                            row.query_country,
                            row.queries,
                            f"{row.shape:.5f}",
                            f"{row.curve:.5f}",
                        ],
                    )
                )
                + " |"
            )
    lines += [
        "",
        "## Interpretation boundaries",
        "Use archive_intervals.parquet and common_route_intervals.parquet for paired storm/year uncertainty. A point estimate is not a significance finding. Undefined small-cluster intervals remain undefined.",
        "The direct source-route contrasts isolate a fixed common archive, but TOA/QA support and radar viewing geometry are still complete input-route changes, not causal architecture effects.",
        "Shape matching, ensemble-mean accuracy, duration, timing and peak error remain different outcomes. Check actual selected cases in the corrected review pages; no independent human relevance verdict is generated here.",
        "Retrospective full-era p99 and pretrained exposure remain limitations. These are not calibrated warning probabilities, verified inundation labels or operator-benefit estimates.",
    ]
    (out / "results-memo.md").write_text("\n".join(lines) + "\n")


def main():
    LOG.mkdir(parents=True, exist_ok=True)
    with (LOG / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = {
            "pid": os.getpid(),
            "status": "running",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "tasks": {},
        }
        mutex = threading.Lock()

        def save():
            state["updated_utc"] = datetime.now(timezone.utc).isoformat()
            state["free_gib"] = round(shutil.disk_usage(ROOT).free / 2**30, 1)
            temp = LOG / "progress.partial"
            temp.write_text(json.dumps(state, indent=2) + "\n")
            temp.replace(LOG / "progress.json")

        def update(task, status, **extra):
            with mutex:
                state["tasks"].setdefault(task, {}).update(status=status, **extra)
                save()

        def run(task, args):
            if shutil.disk_usage(ROOT).free < 60 * 2**30:
                raise RuntimeError(
                    "Disk reserve reached before " + task + "; use authorized Limburg-only cleanup"
                )
            command = [RUNTIME, "-u", *args]
            update(task, "running", command=command)
            env = {
                **os.environ,
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "VECLIB_MAXIMUM_THREADS": "1",
                "GDAL_NUM_THREADS": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PROJ_DATA": "/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj",
            }
            with (LOG / (task + ".log")).open("a") as log:
                child = subprocess.Popen(
                    command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
                )
                update(task, "running", worker_pid=child.pid, command=command)
                code = child.wait()
            if code:
                raise RuntimeError(task + " exited " + str(code))
            update(task, "completed")

        def reviews():
            specs = [
                (
                    "main",
                    ROOT / "results/eo_analogue_comparison_coherent_v1",
                    ROOT / "results/eo_analogue_review_coherent_v1",
                )
            ]
            specs += [
                (
                    name,
                    ROOT / "results/eo_expansion_comparisons" / name,
                    ROOT / "results/eo_expansion_reviews" / name,
                )
                for name in VARIANTS
            ]
            for name, comparison, old in specs:
                new = ROOT / "results/eo_review_provenance_v2" / name
                run(
                    "review_" + name,
                    [
                        "scripts/135_review_eo_followup.py",
                        "--input",
                        str(comparison),
                        "--out",
                        str(new),
                    ],
                )
                verify_review_preserves_numbers(old, new)
                update("review_" + name, "completed_numeric_equivalence_verified")

        try:
            with mutex:
                save()
            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = [
                    pool.submit(reviews),
                    pool.submit(
                        run,
                        "rainfall_benchmark",
                        ["scripts/136_rain_feature_complete_comparison.py", "--run"],
                    ),
                ]
                for job in jobs:
                    job.result()
            run(
                "review_rain168",
                [
                    "scripts/135_review_eo_followup.py",
                    "--input",
                    str(ROOT / "results/eo_analogue_comparison_rain168_v1"),
                    "--out",
                    str(ROOT / "results/eo_review_provenance_v2/rain168"),
                ],
            )
            run("matched_archives_and_routes", ["scripts/137_eo_archive_and_route_followup.py"])
            write_memo()
            with mutex:
                state["status"] = "completed"
                save()
        except BaseException as exc:
            with mutex:
                state["status"] = "failed"
                state["error"] = str(exc)
                save()
            raise


if __name__ == "__main__":
    main()
