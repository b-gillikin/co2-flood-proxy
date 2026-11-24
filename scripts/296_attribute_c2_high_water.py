"""Attribute matched C2 high-water MAE differences to rivers and saved episodes."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.geoglows_experiment import sha, write_json

BASE = ROOT / "results/limburg_representation_extension_v1/c2_alphaearth_2017_v1"
INPUT = BASE / "paired_predictions.parquet"
REVIEW = BASE / "completion_review.json"
MEMBERSHIP = ROOT / "results/limburg_dise_repeatability_v1/episode_membership.csv"
POLICIES = ("native_rmse", "article_faithful")
ARMS = {
    "C2": "C2",
    "AlphaEarth 2020": "C2+AlphaEarth",
    "TESSERA 2020": "C2+TESSERA",
    "AlphaEarth 2017": "C2+AlphaEarth2017",
}


def high_water():
    review = json.loads(REVIEW.read_text())
    if review["status"] != "completed" or sha(INPUT) != review["paired_predictions_sha256"]:
        raise ValueError("The completed paired archive failed verification")
    frame = pd.read_parquet(INPUT)
    if len(frame) != review["paired_rows"] or frame.duplicated(["regime", "gauge", "day"]).any():
        raise ValueError("Unexpected paired prediction census")
    high = frame.loc[frame.high_water.eq(True).fillna(False)].copy()
    local = high.regime.map({"temporal": "local_temporal", "spatial": "local_spatial"})
    high["dataset"] = local.where(high.source_role.eq("local"), "external")
    high = high.reset_index(drop=True).rename_axis("row").reset_index()
    events = pd.read_csv(MEMBERSHIP, dtype={"gauge": str})
    events["dataset"] = events.dataset.replace({"external_transfer": "external"})
    for col in ("start", "end"):
        events[col] = pd.to_datetime(events[col], utc=True)
    joined = high.merge(events, on=["dataset", "river_group", "gauge"], how="left")
    joined = joined.loc[joined.day.between(joined.start, joined.end)].copy()
    if len(joined) != len(high) or joined.row.nunique() != len(high):
        raise ValueError("Each high-water prediction must map to exactly one inherited episode")
    return joined.drop(columns="row"), review


def summarize(paired, keys, selection, policy, label, reference):
    grouped = paired.groupby(keys, sort=True, observed=True)
    cells = grouped.agg(
        gauge_days=("day", "size"),
        dates=("day", "nunique"),
        gauges=("gauge", "nunique"),
        baseline_sum=("baseline_error", "sum"),
        candidate_sum=("candidate_error", "sum"),
    ).reset_index()
    totals = paired.groupby("dataset")[["baseline_error", "candidate_error"]].sum()
    cells["saved_error_sum"] = cells.baseline_sum - cells.candidate_sum
    cells["mae_reduction_pct"] = 100 * cells.saved_error_sum / cells.baseline_sum
    total_base = cells.dataset.map(totals.baseline_error)
    total_saved = total_base - cells.dataset.map(totals.candidate_error)
    cells["pooled_contribution_pp"] = 100 * cells.saved_error_sum / total_base
    cells["reduction_without_cell_pct"] = (
        100 * (total_saved - cells.saved_error_sum) / (total_base - cells.baseline_sum)
    )
    return cells.assign(population=selection, policy=policy, candidate=label, reference=reference)


def assess(out):
    rows, review = high_water()
    river, event, detail = [], [], []
    for policy in POLICIES:
        # Reuse the same paired cohort for every contrast and leave-out diagnostic.
        for name, ref in (
            ("AlphaEarth 2020", "C2"),
            ("TESSERA 2020", "C2"),
            ("AlphaEarth 2017", "C2"),
            ("AlphaEarth 2020", "AlphaEarth 2017"),
        ):
            base = rows[f"{policy}__{ARMS[ref]}"]
            candidate = rows[f"{policy}__{ARMS[name]}"]
            errors = rows.assign(
                baseline_q=base,
                candidate_q=candidate,
                baseline_error=(base - rows.q_observed).abs(),
                candidate_error=(candidate - rows.q_observed).abs(),
            )
            if not np.isfinite(errors[["baseline_error", "candidate_error"]]).all().all():
                raise ValueError("A paired high-water error is missing")
            detail.append(
                errors[
                    [
                        "dataset",
                        "river_group",
                        "episode",
                        "gauge",
                        "station",
                        "day",
                        "q_observed",
                        "clean_verification",
                        "baseline_q",
                        "candidate_q",
                        "baseline_error",
                        "candidate_error",
                        "overlap_stratum",
                        "location_stratum",
                    ]
                ].assign(policy=policy, candidate=name, reference=ref)
            )
            for stratum, g in (
                ("high_water", errors),
                ("clean_high_water", errors.loc[errors.clean_verification.eq(True).fillna(False)]),
            ):
                # Match the evaluation estimand: mean by gauge, then equal gauges
                # within river, then equal rivers within each evaluation regime.
                days = g.groupby(["dataset", "gauge"]).day.transform("size")
                gauges = g.groupby(["dataset", "river_group"]).gauge.transform("nunique")
                rivers = g.groupby("dataset").river_group.transform("nunique")
                weight = 1 / (days * gauges * rivers)
                weighted = g.assign(
                    baseline_error=g.baseline_error * weight,
                    candidate_error=g.candidate_error * weight,
                )
                for keys, records in (
                    (["dataset", "river_group"], river),
                    (["dataset", "river_group", "episode", "start", "end"], event),
                ):
                    records.append(summarize(weighted, keys, stratum, policy, name, ref))
    rivers = pd.concat(river, ignore_index=True)
    events = pd.concat(event, ignore_index=True)
    groups = ["dataset", "policy", "population", "candidate", "reference"]
    aggregation = rivers.groupby(groups)[["gauge_days", "pooled_contribution_pp"]].sum()
    event_totals = events.groupby(groups)[["gauge_days", "pooled_contribution_pp"]].sum()
    pd.testing.assert_frame_equal(aggregation, event_totals)
    for row in review["point_estimates"]:
        if (
            row["reference"] != "C2"
            or row["stratum"] == "all_days"
            or row["scope"] != "all"
            or row["metric"] != "mae"
            or row["rows"] == 0
        ):
            continue
        vintage = row["candidate"].removeprefix("C2+")
        key = (row["dataset"], row["policy"], row["stratum"], vintage, "C2")
        actual = aggregation.loc[key]
        if actual.gauge_days != row["rows"] or not np.isclose(
            actual.pooled_contribution_pp, row["reduction_pct"], atol=1e-9, rtol=0
        ):
            raise ValueError(f"Attribution does not reproduce the saved MAE change: {key}")
    out.mkdir(parents=True, exist_ok=True)
    rivers.to_csv(out / "rivers.csv", index=False)
    events.to_csv(out / "episodes.csv", index=False)
    pd.concat(detail, ignore_index=True).to_csv(out / "gauge_days.csv", index=False)
    counts = rows.groupby("dataset").agg(
        gauge_days=("day", "size"), episodes=("episode", "nunique")
    )
    write_json(
        out / "manifest.json",
        dict(
            sources={
                str(path.relative_to(ROOT)): sha(path) for path in (INPUT, REVIEW, MEMBERSHIP)
            },
            script_sha256=sha(Path(__file__)),
            counts=counts.to_dict(orient="index"),
            files={
                name: sha(out / name) for name in ("rivers.csv", "episodes.csv", "gauge_days.csv")
            },
            method="Paired absolute errors in mm/day with the published equal-river/equal-gauge weights. "
            "Positive contributions favor the candidate. Leave-outs retain pre-exclusion weights on "
            "the remaining observations. No new fit or event definition.",
        ),
    )
    print(counts.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BASE / "high_water_attribution")
    assess(parser.parse_args().output)
