"""Render fixed post-hoc examples from completed main runs; no reranking or fitting."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output

# Illustrative successes, failures, metric disagreement and limited support.
# Chosen after viewing existing posthoc_illustrations; not a validation sample.
CASES = [
    ("monthly", "croma", "2828300000200|2018-09-23T16:00:00+00:00"),
    ("monthly", "terramind", "2828900000200|2019-03-14T16:00:00+00:00"),
    ("recent", "anysat", "13.Q.34|2017-09-30T14:00:00+00:00"),
    ("monthly", "prithvi", "15.Q.41|2024-05-17T07:00:00+00:00"),
    ("monthly_snapshot", "olmoearth", "10.Q.29|2015-01-03T20:00:00+00:00"),
    ("monthly", "olmoearth", "11.Q.32|2017-10-29T06:00:00+00:00"),
]
METRICS = [
    "mean_peak_scaled_shape_rmse",
    "ensemble_curve_level_rmse",
    "duration_estimate_absolute_error_h",
    "mean_peak_time_difference_h",
]


def main():
    paths = [
        ROOT / "results/eo_review_provenance_v2/main/browser_case_index.parquet",
        ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv",
        ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet",
    ]
    frame = pd.read_parquet(paths[0])
    meta = pd.read_csv(paths[1], parse_dates=["onset_utc"]).set_index("event_id")
    responses = pd.read_parquet(paths[2])
    target = ROOT / "results/eo_actual_case_review_2026_10_27"
    with fresh_output(target) as out:
        rows, donors = [], []
        fig, axes = plt.subplots(len(CASES), 2, figsize=(15, 17), sharex=True)
        for number, (kind, model, qid) in enumerate(CASES):
            arms = ["ttm_state", model + "_ttm_state"]
            selected = frame[
                frame.kind.eq(kind)
                & frame.cohort.eq("q_only_available_" + model)
                & frame.scenario.eq("other_rivers")
                & frame.analysis.eq("main")
                & frame.policy.eq("pooled")
                & frame.target_k.eq(5)
                & frame.query_event_id.eq(qid)
                & frame.arm.isin(arms)
            ].set_index("arm", verify_integrity=True)
            if set(selected.index) != set(arms):
                raise ValueError("Missing comparison for " + qid)
            if selected.actual_donor_count.nunique() != 1:
                raise ValueError("Unequal actual donor count")
            q = responses.loc[qid].to_numpy(float)
            for column, arm in enumerate(arms):
                record = selected.loc[arm]
                ids = list(record.donor_ids)
                d = responses.loc[ids].to_numpy(float)
                checks = {
                    "mean_peak_scaled_shape_rmse": np.sqrt(
                        ((d / d.max(1)[:, None] - q / q.max()) ** 2).mean(1)
                    ).mean(),
                    "ensemble_curve_level_rmse": np.sqrt(((d.mean(0) - q) ** 2).mean()),
                    "duration_estimate_absolute_error_h": abs(
                        (d >= 1).sum(1).mean() - (q >= 1).sum()
                    ),
                    "mean_peak_time_difference_h": np.abs(d.argmax(1) - q.argmax()).mean(),
                }
                for metric, value in checks.items():
                    if not np.isclose(value, record[metric], rtol=1e-10, atol=1e-10):
                        raise ValueError("Stored score mismatch: " + metric)
                rows.append(
                    {
                        "case": number + 1,
                        "kind": kind,
                        "model": model,
                        "query_event_id": qid,
                        "arm": arm,
                        "actual_donor_count": len(ids),
                        "query_measurement_concern": bool(meta.loc[qid, "measurement_concern"]),
                        "provider_status": meta.loc[qid, "provider_status"],
                        "query_peak_over_p99": q.max(),
                        "query_first_peak_hour": int(q.argmax()) + 1,
                        "query_hours_at_or_above_p99": int((q >= 1).sum()),
                        **checks,
                    }
                )
                for rank, eid in enumerate(ids, 1):
                    donors.append(
                        {
                            "case": number + 1,
                            "arm": arm,
                            "rank": rank,
                            "donor_event_id": eid,
                            "donor_country": meta.loc[eid, "country"],
                            "donor_river": meta.loc[eid, "physical_river_group"],
                            "donor_measurement_concern": bool(meta.loc[eid, "measurement_concern"]),
                            "donor_provider_status": meta.loc[eid, "provider_status"],
                        }
                    )
                ax = axes[number, column]
                hours = np.arange(1, 73)
                ax.plot(hours, d.T, color="0.65", linewidth=0.7, alpha=0.65)
                ax.plot(hours, d.mean(0), color="tab:blue", linewidth=1.5, label="donor mean")
                ax.plot(hours, q, color="black", linewidth=1.8, label="query")
                ax.axhline(1, color="tab:red", linestyle=":", linewidth=0.8)
                ax.set_title(f"{number + 1}. {qid}\n{kind}; {arm}; n={len(ids)}", fontsize=8)
                ax.set_ylabel("Discharge / gauge-era p99")
                ax.grid(alpha=0.15)
                ax.legend(fontsize=7, loc="upper right")
            limits = [ax.get_ylim() for ax in axes[number]]
            for ax in axes[number]:
                ax.set_ylim(min(v[0] for v in limits), max(v[1] for v in limits))
        for ax in axes[-1]:
            ax.set_xlabel("Hours after query cutoff")
        fig.suptitle(
            "Post-hoc illustrations from the completed main archive: equal-count, other-river retrieval\n"
            "Different model-available cohorts; examples establish neither prevalence nor model rankings",
            fontsize=11,
        )
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(out / "actual_analogue_cases.png", dpi=140)
        plt.close(fig)
        pd.DataFrame(rows).to_parquet(out / "case_scores.parquet", index=False)
        pd.DataFrame(donors).to_parquet(out / "case_donors.parquet", index=False)
        manifest = {
            "purpose": "fixed post-hoc internal interpretation aid; not a representative sample",
            "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in paths},
            "source_sha256": sha256(Path(__file__)),
            "outputs_sha256": {p.name: sha256(p) for p in out.iterdir() if p.is_file()},
            "score_recomputation": "all four displayed metrics match stored scores for all 12 rows",
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(target)


if __name__ == "__main__":
    main()
