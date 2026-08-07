"""Test whether indoor CO2 carries precursor skill for tributary high-flow events.

The early-warning premise requires that something observable in the CO2 record
changes before an event, often enough to be useful and rarely enough when no
event follows. This script frames that as a forecasting problem:

    outcome: does an episode onset fall in the next LEAD_HOURS?
    predictors: rolling summaries of CO2, of pressure, and of rainfall

and scores each predictor by AUROC over every hour with complete coverage.

Two design points carry the argument:

1. **Barometric comparison is the point, not a control.** Storms arrive with
   falling pressure, and falling pressure drives soil gas indoors regardless of
   hydrology. A CO2 predictor that does not beat pressure tendency has no
   warning value, because pressure is already measured everywhere and forecast
   days ahead. The pressure-separated residual is therefore scored alongside
   raw CO2, and rainfall is scored as the operational comparator.

2. **Hours inside events are excluded.** Detecting a flood while it happens is
   not a precursor. Only pre-onset and quiet hours are scored.

Episodes with no pre-onset pressure fall are selected by rule. They are reported
separately because they are the only cases where a CO2 signature could not be
barometric in origin.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval import deduplicate_event_episodes
from src.models.signal_frame import CO2_COL, TARGET_COL, load_signal_frame

EVENTS_PATH = Path("data/processed/event_catalogue.csv")
OUTPUT_DIR = Path("results/precursor")
LEAD_HOURS = 24
# Episodes whose 24 h pre-onset window contains no meaningful pressure fall, so
# any CO2 excursion in them cannot be barometric. Selected by rule, not by hand.
#
# These were previously three hard-coded POSITIONAL indices (7, 17, 18) into a
# catalogue that is rebuilt on every data refresh. The catalogue has since grown
# from 19 episodes to 20, so those positions silently pointed at different
# storms than the ones originally chosen. A derived criterion cannot drift.
NO_PRESSURE_DROP_HPA = 2.0

# Hourly observations are strongly autocorrelated, so resampling them
# independently would understate uncertainty badly. Blocks of one week preserve
# local dependence; the effective sample size is the number of blocks, not the
# number of hours.
BOOTSTRAP_BLOCK_HOURS = 168
BOOTSTRAP_REPLICATES = 1000
RANDOM_STATE = 42


def episodes():
    """Independent episodes with CO2 coverage during and before onset."""
    events = pd.read_csv(EVENTS_PATH, parse_dates=["start_timestamp_utc", "end_timestamp_utc"])
    covered = events.loc[events["iot_overlap_hours"].gt(0) & events["iot_pre_event_hours"].ge(60)]
    frame = deduplicate_event_episodes(covered).sort_values("start_timestamp_utc")
    return frame.reset_index(drop=True)


def build_features(frame):
    """Rolling predictors available to a forecaster at each hour."""
    out = pd.DataFrame(index=frame.index)
    out["co2_residual_24h"] = frame[TARGET_COL].rolling("24h").mean()
    out["co2_residual_72h"] = frame[TARGET_COL].rolling("72h").mean()
    out["co2_raw_24h"] = frame[CO2_COL].rolling("24h").mean()
    pressure = frame["knmi_pressure_hpa"]
    out["pressure_change_24h"] = pressure - pressure.shift(24)
    out["pressure_level"] = pressure
    rain = frame["knmi_precip_mm"]
    out["rain_24h"] = rain.rolling("24h").sum()
    out["rain_72h"] = rain.rolling("72h").sum()
    return out


def label_hours(index, frame):
    """1 when an onset falls in the next LEAD_HOURS; NaN during events."""
    outcome = pd.Series(0, index=index, dtype=float)
    for row in frame.itertuples(index=False):
        onset = row.start_timestamp_utc
        window = (index > onset - pd.Timedelta(hours=LEAD_HOURS)) & (index <= onset)
        outcome.loc[window] = 1.0
        during = (index > onset) & (index <= row.end_timestamp_utc)
        outcome.loc[during] = np.nan
    return outcome


def block_bootstrap_auroc(scores, outcome, rng, block_hours=BOOTSTRAP_BLOCK_HOURS):
    """Moving-block bootstrap interval for AUROC.

    Resampling individual hours treats an autocorrelated series as independent
    and produces intervals several times too narrow. Contiguous blocks keep the
    dependence structure, at the cost of a much smaller effective sample: the
    scored record holds only about ``len(scores) / block_hours`` blocks.
    """
    values = scores.to_numpy()
    labels = outcome.to_numpy()
    count = len(values)
    if count < block_hours * 2:
        return np.nan, np.nan, 0
    starts = np.arange(count - block_hours + 1)
    blocks_needed = int(np.ceil(count / block_hours))
    estimates = []
    for _ in range(BOOTSTRAP_REPLICATES):
        picks = rng.choice(starts, blocks_needed, replace=True)
        index = np.concatenate([np.arange(s, s + block_hours) for s in picks])[:count]
        sampled = labels[index]
        if len(np.unique(sampled)) < 2:
            continue
        estimates.append(roc_auc_score(sampled, values[index]))
    if not estimates:
        return np.nan, np.nan, 0
    low, high = np.percentile(estimates, [2.5, 97.5])
    return float(low), float(high), len(estimates)


def alarm_rates(scores, outcome, target_hit_rate=0.5):
    """False-alarm rate at the threshold achieving the target hit rate."""
    positives = scores[outcome.eq(1)]
    negatives = scores[outcome.eq(0)]
    if positives.empty or negatives.empty:
        return np.nan, np.nan
    threshold = positives.quantile(1 - target_hit_rate)
    return float((negatives >= threshold).mean()), float(threshold)


def main():
    frame = load_signal_frame()
    frame = frame.loc[frame[TARGET_COL].notna()]
    features = build_features(frame)
    catalogue = episodes()
    outcome = label_hours(features.index, catalogue)

    scored = features.join(outcome.rename("y")).dropna()
    positives = int(scored["y"].sum())
    lines = ["Precursor Skill for Tributary High-Flow Events", ""]
    lines.append(f"Lead window: {LEAD_HOURS} h before onset")
    lines.append(f"Episodes: {len(catalogue)}")
    lines.append(
        f"Scored hours: {len(scored)} "
        f"({positives} pre-event, {len(scored) - positives} quiet); "
        "hours inside events excluded"
    )
    blocks = len(scored) // BOOTSTRAP_BLOCK_HOURS
    lines.append(
        f"Bootstrap: moving block, {BOOTSTRAP_BLOCK_HOURS} h blocks "
        f"(about {blocks} independent blocks), {BOOTSTRAP_REPLICATES} replicates"
    )
    lines.append("")
    lines.append("AUROC by predictor (0.5 = no skill):")

    rng = np.random.default_rng(RANDOM_STATE)
    results = []
    for column in features.columns:
        auc = roc_auc_score(scored["y"], scored[column])
        far, _ = alarm_rates(scored[column], scored["y"])
        low, high, valid = block_bootstrap_auroc(scored[column], scored["y"], rng)
        results.append((column, auc, low, high, far, valid))
    for column, auc, low, high, far, _ in sorted(results, key=lambda r: -abs(r[1] - 0.5)):
        skill = "" if (low <= 0.5 <= high) else "  skill"
        lines.append(
            f"  {column:22} AUROC {auc:.3f}  95% CI [{low:.3f}, {high:.3f}]"
            f"  FAR@50% hit {far:.3f}{skill}"
        )

    lines.append("")
    lines.append(
        f"Episodes with no pre-onset pressure fall (< {NO_PRESSURE_DROP_HPA:.0f} hPa over "
        f"{LEAD_HOURS} h, so barometrically clean):"
    )
    lines.append(f"  {'episode':22} {'resid 24h':>10} {'quiet mean':>11} {'z':>7}")
    quiet = scored.loc[scored["y"].eq(0), "co2_residual_24h"]
    baseline_mean, baseline_sd = quiet.mean(), quiet.std()
    for position, row in enumerate(catalogue.itertuples(), start=1):
        onset = row.start_timestamp_utc
        window = features.loc[onset - pd.Timedelta(hours=LEAD_HOURS) : onset]
        if window.empty or window["co2_residual_24h"].isna().all():
            continue
        # Barometrically clean: pressure did not fall materially before onset.
        # Absence of the column is a programming error, not a reason to skip the
        # filter — a silent skip would report every episode as clean.
        if "pressure_level" not in window:
            raise KeyError("pressure_level missing; cannot identify clean episodes")
        fall = window["pressure_level"].iloc[0] - window["pressure_level"].min()
        if not (pd.notna(fall) and fall < NO_PRESSURE_DROP_HPA):
            continue
        number = position
        value = window["co2_residual_24h"].mean()
        z = (value - baseline_mean) / baseline_sd if baseline_sd else np.nan
        lines.append(
            f"  {f'episode {number} ({onset:%Y-%m-%d})':22} {value:10.1f} "
            f"{baseline_mean:11.1f} {z:7.2f}"
        )

    lines.extend(
        [
            "",
            "Reading these numbers:",
            "  - A CO2 predictor is only useful if it beats pressure_change_24h.",
            "    Pressure is already observed and forecast; CO2 must add skill.",
            "  - rain_24h and rain_72h are the operational comparator any real",
            "    warning system would already have.",
            "  - Quiet hours outnumber pre-event hours heavily, so AUROC near 0.5",
            "    means the predictor cannot separate them at any threshold.",
        ]
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "precursor_skill.txt").write_text("\n".join(lines) + "\n")
    pd.DataFrame(
        results,
        columns=[
            "predictor",
            "auroc",
            "ci_low",
            "ci_high",
            "false_alarm_at_50pct_hit",
            "bootstrap_replicates_valid",
        ],
    ).to_csv(OUTPUT_DIR / "precursor_auroc.csv", index=False)
    print("\n".join(lines))
    print(f"\nwrote {OUTPUT_DIR}/precursor_skill.txt")


if __name__ == "__main__":
    main()
