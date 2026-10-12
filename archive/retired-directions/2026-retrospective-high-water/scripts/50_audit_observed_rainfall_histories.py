"""Describe observed rainfall before Limburg onsets and their matched hours.

This is a diagnostic of the first fit, not a new fitted model. The windows are
lags 1–24 and 25–72 hours, with the onset hour excluded. Outputs stay local.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "real_study", ROOT / "scripts/47_run_real_event_study.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def rainfall_windows(rain: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Complete sums at lags 1–24 and 25–72 for each possible onset hour."""
    recent = rain.shift(1).rolling(24, min_periods=24).sum()
    earlier = rain.shift(25).rolling(48, min_periods=48).sum()
    return recent, earlier


def main() -> None:
    discharge = study.review_module.read_hourly(study.FILES["discharge"])
    rainfall = study.review_module.read_hourly(study.FILES["rainfall"])
    gauges = pd.read_csv(study.FILES["gauges"])
    gauges = gauges.loc[gauges.include_primary & gauges.natural_tributary]
    eras = pd.read_csv(study.FILES["rating_eras"])
    review = pd.read_csv(study.FILES["review"])
    review.onset_utc = pd.to_datetime(review.onset_utc, utc=True)
    rows, _, _, _ = study.make_rows(discharge, rainfall, gauges, eras, review)

    pieces = []
    for site, part in rows.groupby("watercourse", sort=False):
        rain = rainfall[site]
        recent, earlier = rainfall_windows(rain)
        frame = part.copy()
        frame["rain_1_24_mm"] = recent.reindex(frame.timestamp_utc).to_numpy()
        frame["rain_25_72_mm"] = earlier.reindex(frame.timestamp_utc).to_numpy()
        pieces.append(frame)
    frame = pd.concat(pieces, ignore_index=True)
    if not frame.loc[frame.complete_rain, ["rain_1_24_mm", "rain_25_72_mm"]].notna().all().all():
        raise AssertionError("a complete 72-hour history lacks a window total")
    frame = frame.loc[frame.complete_rain].copy()
    frame["rain_1_72_mm"] = frame.rain_1_24_mm + frame.rain_25_72_mm
    all_blocks = sorted(frame.block.unique())

    # Restrict comparisons to the same informative strata used by the fit.
    counts = frame.groupby("stratum").onset.transform("sum")
    frame = frame.loc[counts.gt(0)].copy()
    controls = frame.loc[frame.onset.eq(0)].groupby("stratum")
    means = controls[["rain_1_24_mm", "rain_25_72_mm", "rain_1_72_mm"]].mean()
    cases = frame.loc[frame.onset.eq(1)].copy()
    for column in means:
        cases[f"matched_control_mean_{column}"] = means[column].reindex(cases.stratum).to_numpy()
        cases[f"case_minus_control_{column}"] = (
            cases[column] - cases[f"matched_control_mean_{column}"]
        )
    if cases[[f"matched_control_mean_{column}" for column in means]].isna().any().any():
        raise AssertionError("onset without a matched non-onset hour")

    records = []
    for (site, warm), group in cases.groupby(["watercourse", "warm"], sort=True):
        for column in means:
            delta = group[f"case_minus_control_{column}"]
            records.append(
                {
                    "watercourse": site,
                    "season": "warm" if warm else "cold",
                    "window": column,
                    "onsets": len(group),
                    "storms": review.loc[
                        review.watercourse.eq(site) & review.onset_utc.isin(group.timestamp_utc),
                        "storm_id",
                    ].nunique(),
                    "case_median_mm": group[column].median(),
                    "matched_control_mean_median_mm": group[
                        f"matched_control_mean_{column}"
                    ].median(),
                    "paired_difference_median_mm": delta.median(),
                    "paired_difference_positive_fraction": delta.gt(0).mean(),
                }
            )
    output = study.OUT
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"block": all_blocks}).to_csv(
        output / "observed_window_all_blocks.csv", index=False
    )
    frame.to_csv(output / "observed_rainfall_windows_matched_rows.csv", index=False)
    pd.DataFrame(records).to_csv(output / "observed_rainfall_windows_by_site.csv", index=False)
    cases.to_csv(output / "observed_rainfall_windows_onsets.csv", index=False)

    summary = []
    for warm, group in cases.groupby("warm"):
        for column in means:
            delta = group[f"case_minus_control_{column}"]
            summary.append(
                {
                    "season": "warm" if warm else "cold",
                    "window": column,
                    "onsets": len(group),
                    "case_median_mm": group[column].median(),
                    "case_p90_mm": group[column].quantile(0.9),
                    "case_max_mm": group[column].max(),
                    "matched_control_mean_median_mm": group[
                        f"matched_control_mean_{column}"
                    ].median(),
                    "paired_difference_median_mm": delta.median(),
                    "paired_difference_p10_mm": delta.quantile(0.1),
                    "paired_difference_p90_mm": delta.quantile(0.9),
                    "paired_difference_positive_fraction": delta.gt(0).mean(),
                }
            )
    pd.DataFrame(summary).to_csv(output / "observed_rainfall_windows_summary.csv", index=False)
    # Show what the fitted 72-hour constant-intensity contrast would mean in
    # rainfall volume, alongside observed complete-history volumes.
    contrast = json.loads((study.OUT / "analysis_run.json").read_text())[
        "rainfall_positive_p95_mm_per_hour"
    ]
    support = pd.DataFrame(
        [
            {
                "sustained_model_contrast_72h_mm": contrast * 72,
                "observed_case_72h_p50_mm": cases.rain_1_72_mm.median(),
                "observed_case_72h_p90_mm": cases.rain_1_72_mm.quantile(0.9),
                "observed_case_72h_max_mm": cases.rain_1_72_mm.max(),
                "observed_control_72h_p90_mm": frame.loc[
                    frame.onset.eq(0), "rain_1_72_mm"
                ].quantile(0.9),
            }
        ]
    )
    support.to_csv(output / "observed_rainfall_volume_support.csv", index=False)
    print(pd.DataFrame(summary).to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(support.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


if __name__ == "__main__":
    main()
