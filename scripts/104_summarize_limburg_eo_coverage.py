"""Summarize the completed full-archive pixel audit; no model scoring."""

import json
from pathlib import Path

import pandas as pd

r = Path(__file__).resolve().parents[1]
base = r / "results/eo_comparison_preparation"
pixel = json.loads((base / "pixel_scan.json").read_text())
manifest = json.loads((base / "manifest.json").read_text())
w = pd.read_parquet(base / "observed_window_coverage.parquet")
e = pd.read_parquet(base / "event_model_context_coverage.parquet")
obs = pd.read_parquet(base / "observations.parquet")
e = e.merge(
    obs[["observation_id", "gauge", "country", "scoring_eligible"]],
    on="observation_id",
    validate="many_to_one",
)
rows = []
for key, g in w.groupby("product"):
    f = g.observed_fraction
    rows.append(
        {
            "product": key,
            "window_catchments": len(g),
            "zero_observed": int(f.eq(0).sum()),
            "partial_observed": int(((f > 0) & (f < 1 - 1e-7)).sum()),
            "full_observed": int((f >= 1 - 1e-7).sum()),
            "median_fraction": float(f.median()),
            "p10_fraction": float(f.quantile(0.1)),
        }
    )
# Identical source route across models: show one representative per product.
from sys import path

path.insert(0, str(r))
from src.eo_inputs import ROUTES, sha256

representatives = {}
for model, (product, *_) in ROUTES.items():
    representatives.setdefault(product, model)
contexts = []
for product, model in representatives.items():
    x = e[e.model.eq(model)]
    for (cohort, kind), g in x.groupby(["cohort", "kind"]):
        eligible = g[g.scoring_eligible.astype(bool)]
        complete = eligible[eligible.status.eq("local_context_observed")]
        contexts.append(
            {
                "product": product,
                "cohort": cohort,
                "kind": kind,
                "total": len(g),
                "eligible": len(eligible),
                "complete_any_area_all_slots": len(complete),
                "median_min_fraction_complete": float(complete.observed_min_fraction.median())
                if len(complete)
                else None,
                "median_age_days_complete": float(complete.mean_age_days_observed_slots.median())
                if len(complete)
                else None,
            }
        )
site = []
for product, model in representatives.items():
    x = e[e.model.eq(model) & e.cohort.eq("high_water") & e.scoring_eligible.astype(bool)]
    for (gauge, kind), g in x.groupby(["gauge", "kind"]):
        site.append(
            {
                "product": product,
                "gauge": gauge,
                "kind": kind,
                "eligible": len(g),
                "complete": int(g.status.eq("local_context_observed").sum()),
            }
        )
# Explicit date checks use timestamps, independent of pandas datetime units.
links = pd.read_parquet(base / "observation_windows.parquet")
date_rows = links.merge(
    obs[["observation_id", "catchment_gauge", "cutoff_utc"]], on="observation_id"
).merge(w, on=["window_id", "catchment_gauge"])
cutoff_days = date_rows.cutoff_utc.map(lambda t: t.timestamp() / 86400)
jobs = json.loads((r / "data/raw/limburg_compact_eo/jobs.json").read_text())
from datetime import datetime

source_errors = sum(
    any(
        t < datetime.fromisoformat(j["window"]["start"]).timestamp() * 1000
        or t >= datetime.fromisoformat(j["window"]["end"]).timestamp() * 1000
        for t in j["acquisition_ms"]
    )
    for j in jobs
)
all_ten = {}
for kind, g in e[e.cohort.eq("high_water") & e.scoring_eligible.astype(bool)].groupby("kind"):
    statuses = g.pivot(index="observation_id", columns="model", values="status")
    if set(statuses.columns) != set(ROUTES):
        raise ValueError("Missing model in common coverage comparison")
    all_ten[kind] = int(statuses.eq("local_context_observed").all(axis=1).sum())

result = {
    "input_sha256": {
        name: sha256(base / name)
        for name in [
            "manifest.json",
            "pixel_scan.json",
            "observed_window_coverage.parquet",
            "event_model_context_coverage.parquet",
            "observations.parquet",
        ]
    },
    "timing_checks": {
        "jobs_checked": len(jobs),
        "source_jobs_outside_window": source_errors,
        "event_pixel_date_links": len(date_rows),
        "latest_pixel_at_or_after_cutoff": int((date_rows.latest_day >= cutoff_days).sum()),
        "future_window_links": int(links.age_days.lt(0).sum()),
    },
    "all_ten_high_water_complete_contexts": all_ten,
    "pixel_scan": pixel,
    "local_file_status": manifest["local_coverage_status"],
    "product_coverage": rows,
    "context_coverage": contexts,
    "site_coverage": site,
    "note": "Complete here means some valid catchment area in every slot, not full catchment coverage or final encoder eligibility.",
}
(base / "full_archive_audit_summary.json").write_text(
    json.dumps(result, indent=2, allow_nan=False) + "\n"
)
print(json.dumps(result, indent=2, allow_nan=False))
