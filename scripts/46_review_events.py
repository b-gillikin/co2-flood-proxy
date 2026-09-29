"""Outcome-only review of every Limburg candidate high-water episode.

This script deliberately does not read rainfall or weather. Its review flags
identify measurements to inspect; they are not automatic reasons to delete an
otherwise observed threshold crossing. The output is an internal audit aid,
not a replacement for the provider's station notes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import (  # noqa: E402
    assign_eras,
    cluster_regional_storms,
    episode_table,
    era_thresholds,
    rating_domain_admissible,
    storm_table,
)

INPUTS = {
    "discharge": ROOT / "data/interim/event_study_discharge_hourly.csv",
    "gauges": ROOT / "data/interim/event_study_gauges.csv",
    "rating_eras": ROOT / "data/interim/event_study_rating_eras.csv",
    "source_qa": ROOT / "data/processed/waterschap_station_source_qa.csv",
}
OUTPUT = ROOT / "results/event_study/real_data_v1"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_hourly(path):
    table = pd.read_csv(path)
    index = pd.DatetimeIndex(pd.to_datetime(table.pop("timestamp_utc"), utc=True))
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError(f"non-unique or unordered hourly axis: {path}")
    if not index.to_series().diff().iloc[1:].eq(pd.Timedelta(hours=1)).all():
        raise ValueError(f"incomplete hourly axis: {path}")
    return table.set_axis(index).apply(pd.to_numeric, errors="coerce")


def inspect_episode(series, eras, admissible, threshold, era_table, row, source_note):
    onset = pd.Timestamp(row.onset_utc)
    prior = onset - pd.Timedelta(hours=1)
    peak_window = series.loc[onset : pd.Timestamp(row.last_crossing_utc) + pd.Timedelta(hours=72)]
    era_id = eras.loc[onset]
    p99 = float(threshold.loc[onset]) if pd.notna(threshold.loc[onset]) else np.nan
    value = series.loc[onset]
    before = series.loc[prior] if prior in series.index else np.nan
    known_pair = bool(
        prior in series.index
        and admissible.loc[onset]
        and admissible.loc[prior]
        and pd.notna(era_id)
        and eras.loc[prior] == era_id
    )
    # A large instantaneous jump is a *review flag*, not evidence of failure.
    abrupt = bool(known_pair and before >= 0 and value > 5 * max(float(before), 0.05 * p99))
    nearby = series.loc[onset - pd.Timedelta(hours=3) : onset + pd.Timedelta(hours=3)]
    nearby_gap = bool(nearby.isna().any())
    nearby_era_change = bool(
        eras.loc[onset - pd.Timedelta(hours=72) : onset + pd.Timedelta(hours=72)].nunique(
            dropna=True
        )
        > 1
    )
    july = bool(
        pd.Timestamp("2021-07-13", tz="UTC") <= onset <= pd.Timestamp("2021-07-17", tz="UTC")
    )
    peak = float(peak_window.max()) if peak_window.notna().any() else np.nan
    era_limits = era_table.loc[era_table.era_id.astype(str).eq(str(era_id))].iloc[0]
    lower, upper = era_limits.domain_min_m3s, era_limits.domain_max_m3s
    onset_within_domain = bool(
        (pd.isna(lower) or value >= lower) and (pd.isna(upper) or value <= upper)
    )
    prior_within_domain = bool(
        pd.notna(before)
        and (pd.isna(lower) or before >= lower)
        and (pd.isna(upper) or before <= upper)
    )
    peak_outside_domain = bool(pd.notna(upper) and peak > upper)
    source_concern = bool(
        july
        and source_note
        in {
            "exclude_out_of_range",
            "exclude_peak_outside_rating_domain",
            "rating_relation_uncertain",
        }
    )
    gulp_calibration = bool(source_note == "rating_relation_uncertain" and peak > 3.0)
    flags = []
    if row.onset_censored:
        flags.append("unobserved_entry")
    if nearby_gap:
        flags.append("nearby_gap")
    if nearby_era_change:
        flags.append("near_era_boundary")
    if abrupt:
        flags.append("abrupt_rise_review")
    if july:
        flags.append("july_2021")
    if source_concern:
        flags.append("provider_july_concern")
    if peak_outside_domain:
        flags.append("peak_outside_rating_domain")
    if gulp_calibration:
        flags.append("gulp_above_documented_calibration")
    status = "censored_descriptive" if row.onset_censored else "include_exact"
    measurement_concern = bool(source_concern or gulp_calibration or abrupt or peak_outside_domain)
    return {
        "era_id": era_id,
        "p99_m3s": p99,
        "prior_q_m3s": before,
        "onset_q_m3s": value,
        "episode_observed_peak_m3s": peak,
        "domain_min_m3s": lower,
        "domain_max_m3s": upper,
        "onset_within_domain": onset_within_domain,
        "prior_within_domain": prior_within_domain,
        "peak_outside_rating_domain": peak_outside_domain,
        "onset_pair_admissible": known_pair,
        "nearby_gap": nearby_gap,
        "nearby_era_change": nearby_era_change,
        "abrupt_rise_review": abrupt,
        "provider_july_concern": source_concern,
        "gulp_above_documented_calibration": gulp_calibration,
        "measurement_concern": measurement_concern,
        "review_flags": ";".join(flags),
        "review_decision": status,
        "decision_basis": (
            "unobserved threshold entry; timing censored"
            if row.onset_censored
            else "adjacent admissible crossing; retain despite later peak uncertainty"
        ),
    }


def build_review(discharge, gauges, rating_eras, source_qa):
    rows = []
    for gauge in gauges.itertuples(index=False):
        series = discharge[gauge.gauge]
        table = rating_eras.loc[rating_eras.gauge.eq(gauge.gauge)]
        eras = assign_eras(series.index, table)
        _, threshold = era_thresholds(series, eras)
        admissible = rating_domain_admissible(series, eras, table, threshold)
        episodes = episode_table(series, threshold, 72, admissible, eras)
        note = source_qa.loc[gauge.gauge, "july_2021_discharge_status"]
        for episode in episodes.itertuples(index=False):
            row = {"gauge": gauge.gauge, "watercourse": gauge.watercourse, **episode._asdict()}
            row.update(inspect_episode(series, eras, admissible, threshold, table, episode, note))
            row["provider_status"] = note
            rows.append(row)
    reviewed = pd.DataFrame(rows).sort_values(["onset_utc", "gauge"]).reset_index(drop=True)
    reviewed.insert(
        0, "event_id", [f"{row.gauge}|{row.onset_utc.isoformat()}" for row in reviewed.itertuples()]
    )
    reviewed = cluster_regional_storms(reviewed)
    if (reviewed.onset_censored & reviewed.review_decision.ne("censored_descriptive")).any():
        raise AssertionError("censored event included")
    if (~reviewed.onset_censored & ~reviewed.onset_pair_admissible).any():
        raise AssertionError("exact onset has an inadmissible pair")
    return reviewed


def plot_review_windows(discharge, reviewed):
    """Contact sheets for inspecting every flagged measurement without signals."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    flagged = reviewed.loc[reviewed.measurement_concern | reviewed.nearby_gap].reset_index(
        drop=True
    )
    for page, first in enumerate(range(0, len(flagged), 12), start=1):
        subset = flagged.iloc[first : first + 12]
        figure, axes = plt.subplots(4, 3, figsize=(16, 12), squeeze=False)
        for ax, event in zip(axes.flat, subset.itertuples(), strict=False):
            onset = pd.Timestamp(event.onset_utc)
            window = discharge[event.gauge].loc[
                onset - pd.Timedelta(hours=18) : onset + pd.Timedelta(hours=36)
            ]
            ax.plot((window.index - onset) / pd.Timedelta(hours=1), window, linewidth=1.2)
            ax.axvline(0, color="black", linewidth=0.8)
            ax.axhline(event.p99_m3s, color="red", linestyle="--", linewidth=0.8)
            ax.set_title(f"{event.watercourse} {onset:%Y-%m-%d %H} UTC", fontsize=9)
            ax.set_xlabel("hours from onset")
            ax.set_ylabel("m³/s")
            ax.grid(alpha=0.2)
        for ax in axes.flat[len(subset) :]:
            ax.axis("off")
        figure.tight_layout()
        figure.savefig(OUTPUT / f"measurement_review_{page:02d}.png", dpi=135)
        plt.close(figure)


def main():
    discharge = read_hourly(INPUTS["discharge"])
    gauges = pd.read_csv(INPUTS["gauges"])
    gauges = gauges.loc[gauges.include_primary & gauges.natural_tributary]
    rating_eras = pd.read_csv(INPUTS["rating_eras"])
    source_qa = pd.read_csv(INPUTS["source_qa"]).set_index("series_key")
    reviewed = build_review(discharge, gauges, rating_eras, source_qa)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    reviewed.to_csv(OUTPUT / "events.csv", index=False)
    storm_table(reviewed).to_csv(OUTPUT / "storms.csv", index=False)
    plot_review_windows(discharge, reviewed)
    summary = {
        "input_sha256": {name: sha256(path) for name, path in INPUTS.items()},
        "n_events": len(reviewed),
        "n_censored": int(reviewed.onset_censored.sum()),
        "n_measurement_concern": int(reviewed.measurement_concern.sum()),
        "n_storms": reviewed.storm_id.nunique(),
        "flag_counts": {
            flag: int(reviewed.review_flags.str.contains(flag, regex=False).sum())
            for flag in [
                "unobserved_entry",
                "nearby_gap",
                "near_era_boundary",
                "abrupt_rise_review",
                "july_2021",
                "provider_july_concern",
                "peak_outside_rating_domain",
                "gulp_above_documented_calibration",
            ]
        },
    }
    (OUTPUT / "event_review_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
