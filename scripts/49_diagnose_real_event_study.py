"""Identify surprising fitted onsets and July 2021 influence without tuning models."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.case_crossover import (  # noqa: E402
    fit_conditional_poisson,
    prepare_problem,
    primary_estimand,
    seasonal_design,
)

spec = importlib.util.spec_from_file_location(
    "real_study", ROOT / "scripts/47_run_real_event_study.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def main():
    discharge = study.review_module.read_hourly(study.FILES["discharge"])
    rainfall = study.review_module.read_hourly(study.FILES["rainfall"])
    gauges = pd.read_csv(study.FILES["gauges"])
    gauges = gauges.loc[gauges.include_primary & gauges.natural_tributary]
    eras = pd.read_csv(study.FILES["rating_eras"])
    review = pd.read_csv(study.FILES["review"])
    review.onset_utc = pd.to_datetime(review.onset_utc, utc=True)
    rows, rain_cross, _, basis = study.make_rows(discharge, rainfall, gauges, eras, review)
    design = seasonal_design(rain_cross, rows.warm)
    complete = np.isfinite(design).all(axis=1)
    retained = rows.loc[complete].reset_index(drop=True)
    problem = prepare_problem(design[complete], retained.onset, retained.stratum, retained.block)
    coefficients = pd.read_csv(study.OUT / "point_coefficients_primary.csv").iloc[0].to_numpy()
    eta = problem["design"] @ coefficients
    top = np.full(problem["n_strata"], -np.inf)
    np.maximum.at(top, problem["codes"], eta)
    exp_eta = np.exp(eta - top[problem["codes"]])
    probability = exp_eta / (problem["operator"] @ exp_eta)[problem["codes"]]
    informative = retained.groupby("stratum").onset.transform("sum").gt(0)
    fit_rows = retained.loc[informative].copy()
    if len(fit_rows) != len(probability):
        raise AssertionError("prediction rows and likelihood rows differ")
    fit_rows["conditional_probability"] = probability
    fit_rows.loc[fit_rows.onset.eq(1)].nsmallest(20, "conditional_probability").to_csv(
        study.OUT / "least_expected_onsets.csv", index=False
    )

    contrast = float(
        json.loads((study.OUT / "analysis_run.json").read_text())[
            "rainfall_positive_p95_mm_per_hour"
        ]
    )
    support = []
    for site in gauges.watercourse:
        above = rainfall[site].ge(contrast).fillna(False).to_numpy()
        longest = current = 0
        for observed in above:
            current = current + 1 if observed else 0
            longest = max(longest, current)
        support.append(
            {
                "watercourse": site,
                "hourly_contrast_mm": contrast,
                "longest_consecutive_hours_at_or_above_contrast": longest,
                "required_hours_for_cumulative_contrast": 72,
            }
        )
    pd.DataFrame(support).to_csv(study.OUT / "rainfall_contrast_support.csv", index=False)
    comparisons = []
    for name, keep in [
        ("main", np.ones(len(rows), dtype=bool)),
        (
            "july_2021_event_hours_omitted",
            ~(rows.onset.eq(1) & rows.timestamp_utc.between("2021-07-13", "2021-07-17")).to_numpy(),
        ),
        (
            "july_2021_month_omitted",
            ~rows.timestamp_utc.between("2021-07-01", "2021-07-31 23:00").to_numpy(),
        ),
    ]:
        row = rows.loc[keep]
        selected_design = design[keep]
        valid = np.isfinite(selected_design).all(axis=1)
        fit = fit_conditional_poisson(
            selected_design[valid],
            row.onset.to_numpy()[valid],
            row.stratum.to_numpy()[valid],
        )
        comparisons.append(
            {
                "check": name,
                "n_onsets": fit["n_onsets"],
                **primary_estimand(fit, basis, contrast),
            }
        )
    pd.DataFrame(comparisons).to_csv(study.OUT / "july_2021_influence.csv", index=False)
    print("Wrote onset-probability and July 2021 point-estimate diagnostics")


if __name__ == "__main__":
    main()
