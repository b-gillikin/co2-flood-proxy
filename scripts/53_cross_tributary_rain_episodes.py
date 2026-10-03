"""Exploratory rainfall-defined Limburg event-footprint analysis.

Rain episodes are defined without discharge. This is an internal diagnostic,
not a replacement for the registered case-crossover design or manuscript text.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.event_study import assign_eras, era_thresholds, rating_domain_admissible  # noqa: E402

DATA = ROOT / "data/interim"
REVIEW = ROOT / "results/event_study/real_data_v1/events.csv"
OUT = ROOT / "results/event_study/cross_tributary_rain_v1"
SITES = ("Eyserbeek", "Geul", "Gulp", "Voer", "Worm", "Geleenbeek")
WET_MM_H = 0.2
RESPONSE_HOURS = 24


def read_hourly(path):
    table = pd.read_csv(path)
    index = pd.DatetimeIndex(pd.to_datetime(table.pop("timestamp_utc"), utc=True))
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError(f"Bad hourly index: {path}")
    if not index.to_series().diff().iloc[1:].eq(pd.Timedelta(hours=1)).all():
        raise ValueError(f"Incomplete hourly index: {path}")
    return table.set_axis(index).apply(pd.to_numeric, errors="coerce")


def rain_episodes(rain, dry_gap_hours=12, material_mm_24h=10.0):
    """Cluster regional wet hours; qualify by within-cluster site 24 h rainfall."""
    wet = rain.max(axis=1, skipna=True).ge(WET_MM_H).to_numpy()
    positions = np.flatnonzero(wet)
    columns = [
        "episode_id",
        "rain_start_utc",
        "rain_end_utc",
        "response_end_utc",
        "peak_site_24h_mm",
        "duration_hours",
        "rain_year",
        "rain_month",
    ]
    if not len(positions):
        return pd.DataFrame(columns=columns)
    breaks = np.r_[0, np.flatnonzero(np.diff(positions) > dry_gap_hours) + 1, len(positions)]
    candidates = []
    for left, right in zip(breaks[:-1], breaks[1:], strict=True):
        start, end = positions[left], positions[right - 1]
        segment = rain.iloc[start : end + 1]
        peak = segment.rolling(24, min_periods=1).sum().max().max()
        next_start = (
            positions[breaks[np.searchsorted(breaks, right)]]
            if right < len(positions)
            else len(rain)
        )
        response_end = min(end + RESPONSE_HOURS, next_start - 1, len(rain) - 1)
        if peak >= material_mm_24h:
            candidates.append(
                {
                    "rain_start_utc": rain.index[start],
                    "rain_end_utc": rain.index[end],
                    "response_end_utc": rain.index[response_end],
                    "peak_site_24h_mm": float(peak),
                    "duration_hours": end - start + 1,
                    "rain_year": rain.index[start].year,
                    "rain_month": rain.index[start].month,
                }
            )
    result = pd.DataFrame(candidates)
    if result.empty:
        return pd.DataFrame(columns=columns)
    result.insert(0, "episode_id", [f"rain_{i:04d}" for i in range(1, len(result) + 1)])
    return result[columns]


def site_states(discharge, ratings):
    states = {}
    for gauge, site in GAUGE_SITE.items():
        series = discharge[gauge]
        era_table = ratings.loc[ratings.gauge.eq(gauge)]
        eras = assign_eras(series.index, era_table)
        _, threshold = era_thresholds(series, eras)
        valid = rating_domain_admissible(series, eras, era_table, threshold)
        states[site] = pd.DataFrame({"q": series, "p99": threshold, "valid": valid})
    return states


def footprint(episodes, reviewed, states, rain):
    reviewed = reviewed.loc[reviewed.review_decision.eq("include_exact")].copy()
    reviewed.onset_utc = pd.to_datetime(reviewed.onset_utc, utc=True)
    rows = []
    for episode in episodes.itertuples(index=False):
        for site in SITES:
            window = states[site].loc[episode.rain_start_utc : episode.response_end_utc]
            rain_window = rain[site].loc[episode.rain_start_utc : episode.rain_end_utc]
            matches = reviewed.loc[
                reviewed.watercourse.eq(site)
                & reviewed.onset_utc.between(episode.rain_start_utc, episode.response_end_utc)
            ].sort_values("onset_utc")
            observed = window.valid & window.q.notna() & window.p99.notna()
            above = observed & window.q.gt(window.p99)
            first = matches.iloc[0] if len(matches) else None
            start = window.iloc[0] if len(window) else None
            rows.append(
                {
                    "episode_id": episode.episode_id,
                    "watercourse": site,
                    "first_onset_utc": first.onset_utc if first is not None else pd.NaT,
                    "n_reviewed_onsets": len(matches),
                    "any_high_water": bool(above.any()),
                    "first_high_utc": window.index[above.to_numpy()][0] if above.any() else pd.NaT,
                    "site_rain_total_mm": float(rain_window.sum(min_count=1)),
                    "site_rain_peak_24h_mm": float(
                        rain_window.rolling(24, min_periods=1).sum().max()
                    ),
                    "rain_hour_fraction": float(rain_window.notna().mean()),
                    "measurement_concern": bool(matches.measurement_concern.any()),
                    "start_already_high": bool(start.valid and start.q > start.p99)
                    if start is not None
                    else False,
                    "start_q_over_p99": float(start.q / start.p99)
                    if start is not None and start.valid and start.p99 > 0
                    else np.nan,
                    "valid_hour_fraction": float(observed.mean()) if len(window) else np.nan,
                    "peak_q_over_p99": float((window.q[observed] / window.p99[observed]).max())
                    if observed.any()
                    else np.nan,
                }
            )
    return pd.DataFrame(rows)


def summarize(episodes, sites):
    per = sites.groupby("episode_id").agg(
        n_sites_high=("any_high_water", "sum"),
        n_sites_with_onset=("first_onset_utc", lambda x: int(x.notna().sum())),
        n_sites_preexisting=("start_already_high", "sum"),
        n_sites_low_coverage=("valid_hour_fraction", lambda x: int((x < 0.9).sum())),
        n_sites_incomplete_rain=("rain_hour_fraction", lambda x: int((x < 1.0).sum())),
        any_measurement_concern=("measurement_concern", "any"),
    )
    per = episodes.merge(per, left_on="episode_id", right_index=True)
    rainy_sites = sites.groupby("episode_id").site_rain_peak_24h_mm.agg(
        lambda x: int((x >= 10.0).sum())
    )
    per["n_sites_rain_10mm"] = per.episode_id.map(rainy_sites)
    initial_flow = sites.groupby("episode_id").start_q_over_p99.median()
    per["median_start_q_over_p99"] = per.episode_id.map(initial_flow)
    spread = (
        sites.loc[sites.first_onset_utc.notna()]
        .groupby("episode_id")
        .first_onset_utc.agg(lambda x: (x.max() - x.min()) / pd.Timedelta(hours=1))
    )
    per["onset_spread_hours"] = per.episode_id.map(spread)
    return per


def pair_order(sites):
    """Descriptive threshold-crossing order; no propagation interpretation."""
    wide = sites.pivot(index="episode_id", columns="watercourse", values="first_onset_utc")
    rows = []
    for a, b in itertools.combinations(SITES, 2):
        both = wide[[a, b]].dropna()
        lag = (both[b] - both[a]) / pd.Timedelta(hours=1)
        rows.append(
            {
                "first_site": a,
                "second_site": b,
                "n_joint_episodes": len(both),
                "median_second_minus_first_hours": float(lag.median()) if len(lag) else np.nan,
                "first_earlier_fraction": float((lag > 0).mean()) if len(lag) else np.nan,
                "simultaneous_fraction": float((lag == 0).mean()) if len(lag) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def episode_rain_contrast(episodes, sites):
    """Rainfall difference between high and non-high sites within mixed episodes."""
    mixed_ids = set(episodes.loc[episodes.n_sites_high.between(1, 5), "episode_id"])
    mixed = sites.loc[sites.episode_id.isin(mixed_ids)]
    rows = []
    for episode_id, group in mixed.groupby("episode_id"):
        rows.append(
            {
                "episode_id": episode_id,
                "mean_high_minus_other_24h_mm": float(
                    group.loc[group.any_high_water, "site_rain_peak_24h_mm"].mean()
                    - group.loc[~group.any_high_water, "site_rain_peak_24h_mm"].mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def year_block_bootstrap(episodes, contrast, draws=999, seed=20261003):
    """Exploratory intervals that keep all episodes of a calendar year together."""
    merged = episodes.merge(contrast, on="episode_id", how="left")
    years = np.sort(merged.rain_year.unique())
    rng = np.random.default_rng(seed)
    rows = []
    for draw in range(draws + 1):
        if draw == 0:
            sample = merged
        else:
            chosen = rng.choice(years, size=len(years), replace=True)
            sample = pd.concat([merged.loc[merged.rain_year.eq(year)] for year in chosen])
        mixed = sample.mean_high_minus_other_24h_mm.dropna()
        rows.append(
            {
                "draw": draw,
                "rain_footprint_high_water_spearman": float(
                    sample.n_sites_rain_10mm.corr(sample.n_sites_high, method="spearman")
                ),
                "mixed_positive_fraction": float(mixed.gt(0).mean()),
                "mixed_median_rain_difference_mm": float(mixed.median()),
            }
        )
    return pd.DataFrame(rows)


GAUGE_SITE = {
    "11.Q.32": "Eyserbeek",
    "10.Q.29": "Geul",
    "13.Q.34": "Gulp",
    "15.Q.41": "Voer",
    "18.Q.45": "Worm",
    "6.Q.18": "Geleenbeek",
}


def main():
    paths = {
        "rain": DATA / "radolan_catchment_hourly.csv",
        "discharge": DATA / "event_study_discharge_hourly.csv",
        "ratings": DATA / "event_study_rating_eras.csv",
        "review": REVIEW,
    }
    rain = read_hourly(paths["rain"])[list(SITES)]
    discharge = read_hourly(paths["discharge"])
    joint = rain.index.intersection(discharge.index)
    if len(joint) < 0.99 * min(len(rain), len(discharge)):
        raise ValueError("Rain and discharge axes have little overlap")
    rain = rain.loc[joint]
    # Keep the full discharge axis when reconstructing era-specific p99 ranks;
    # the review file used that axis, including its two non-overlapping hours.
    ratings = pd.read_csv(paths["ratings"])
    reviewed = pd.read_csv(paths["review"])
    states = site_states(discharge, ratings)
    OUT.mkdir(parents=True, exist_ok=True)
    sensitivity = []
    for gap in (12, 24):
        for cutoff in (5.0, 10.0, 20.0):
            episodes = rain_episodes(rain, gap, cutoff)
            sites = footprint(episodes, reviewed, states, rain)
            per = summarize(episodes, sites)
            stem = f"gap{gap}_rain{int(cutoff)}"
            if gap == 12 and cutoff == 10.0:
                episodes.to_csv(OUT / "rain_episodes.csv", index=False)
                sites.to_csv(OUT / "site_footprints.csv", index=False)
                per.to_csv(OUT / "episode_footprints.csv", index=False)
                pair_order(sites).to_csv(OUT / "pair_order.csv", index=False)
                eligible = per.loc[
                    per.n_sites_low_coverage.eq(0)
                    & per.n_sites_preexisting.eq(0)
                    & per.n_sites_incomplete_rain.eq(0)
                ]
                contrast = episode_rain_contrast(eligible, sites)
                contrast.to_csv(OUT / "mixed_episode_rain_contrast.csv", index=False)
                year_block_bootstrap(eligible, contrast).to_csv(
                    OUT / "year_block_bootstrap.csv", index=False
                )
            sensitivity.append(
                {
                    "rule": stem,
                    "n_episodes": len(per),
                    "n_with_high": int(per.n_sites_high.gt(0).sum()),
                    "n_multi_site_high": int(per.n_sites_high.ge(2).sum()),
                    "n_all_six_high": int(per.n_sites_high.eq(6).sum()),
                    "n_with_onset": int(per.n_sites_with_onset.gt(0).sum()),
                    "n_multi_site": int(per.n_sites_with_onset.ge(2).sum()),
                    "n_all_six": int(per.n_sites_with_onset.eq(6).sum()),
                    "n_any_low_coverage": int(per.n_sites_low_coverage.gt(0).sum()),
                    "n_any_preexisting": int(per.n_sites_preexisting.gt(0).sum()),
                    "n_complete_six": int(
                        (
                            per.n_sites_low_coverage.eq(0)
                            & per.n_sites_preexisting.eq(0)
                            & per.n_sites_incomplete_rain.eq(0)
                        ).sum()
                    ),
                }
            )
    pd.DataFrame(sensitivity).to_csv(OUT / "sensitivity.csv", index=False)
    manifest = {
        "status": "exploratory, not manuscript text",
        "wet_mm_h": WET_MM_H,
        "response_hours": RESPONSE_HOURS,
        "response_window": "rain start through last wet hour +24h, capped before next raw episode",
        "input_sha256": {key: hash_file(path) for key, path in paths.items()},
        "script_sha256": hash_file(Path(__file__)),
        "uncertainty": "999 calendar-year block bootstrap draws; exploratory intervals",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
