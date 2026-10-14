#!/usr/bin/env python3
"""Full native-record census and phase-conditioned historical analogue analysis.

Current supplied thresholds applied retrospectively; no inferred flood impacts,
training, sampled events, threshold tuning or changes to earlier numerical runs.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cross_border", ROOT / "scripts/84_complete_cross_border_analogues.py"
)
X = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(X)
E, C, B = X.E, X.C, X.B
OUT = ROOT / "results/warning_threshold_progression"
THRESHOLDS = (
    ROOT / "data/raw/external_deliveries/waterschap_limburg/2026-09-29/warning tresholds(Blad1).csv"
)
LEVELS = ["H1", "H2", "H3"]
STEP = pd.Timedelta(minutes=15)


def load_module(number, name):
    path = next((ROOT / "scripts").glob(f"{number}_*.py"))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_thresholds(path):
    raw = pd.read_csv(path, header=None)
    rows = raw[raw[1].astype(str).str.match(r"^\d+\.Q\.\d+$")].copy()
    result = rows[[0, 1, 3, 4, 5]].set_axis(["station", "gauge", *LEVELS], axis=1)
    result[LEVELS] = result[LEVELS].apply(pd.to_numeric, errors="raise")
    if (
        result.gauge.duplicated().any()
        or not ((result.H1 > 0) & (result.H2 > result.H1) & (result.H3 > result.H2)).all()
    ):
        raise ValueError("Unique, ordered positive thresholds required")
    return result.set_index("gauge")


def crossing_entries(series, threshold):
    above = series.ge(threshold)
    prior = series.shift(1)
    entry = above & ~above.shift(1, fill_value=False)
    result = pd.DataFrame(
        {
            "timestamp_utc": series.index[entry],
            "adjacent_below": prior[entry].notna().to_numpy()
            & prior[entry].lt(threshold).to_numpy(),
            "q_m3s": series[entry].to_numpy(),
        }
    )
    result["entry_status"] = np.where(
        result.adjacent_below, "adjacent_interval_entry", "entry_after_gap_or_record_start"
    )
    return result


def reach_label(values, threshold, trusted=None):
    """A observed positive survives later gaps; absence requires a complete window."""
    q = np.asarray(values, float)
    valid = np.isfinite(q) & (q >= 0)
    if trusted is not None:
        valid &= np.asarray(trusted, bool)
    positive = valid & (q >= threshold)
    if positive.any():
        return 1.0, (int(np.flatnonzero(positive)[0]) + 1) / 4
    return (0.0, np.nan) if valid.all() and len(q) else (np.nan, np.nan)


def reliable_mask(series, gauge, eras, qa, capacity):
    """Sensitivity only: documentary upper/calibration limits and provider concerns."""
    table = eras[eras.gauge.eq(gauge)]
    if table.empty:
        return pd.Series(False, index=series.index)
    upper = np.full(len(series), np.nan)
    for row in table.itertuples():
        start = pd.Timestamp(row.valid_from_utc)
        end = (
            pd.Timestamp(row.valid_to_utc)
            if pd.notna(row.valid_to_utc)
            else series.index[-1] + STEP
        )
        covered = (series.index >= start) & (series.index < end)
        upper[covered] = row.domain_max_m3s if pd.notna(row.domain_max_m3s) else np.inf
    valid = series.notna().to_numpy() & ((series.to_numpy() <= upper) | series.eq(0).to_numpy())
    if gauge == "13.Q.34":
        valid &= series.le(3).to_numpy()
    if gauge == "10.Q.29":
        valid &= series.le(capacity).to_numpy()
    status = str(qa.loc[gauge, "july_2021_discharge_status"])
    if status in {
        "exclude_out_of_range",
        "exclude_peak_outside_rating_domain",
        "rating_relation_uncertain",
        "exclude_failed_and_disturbed",
    }:
        july = (series.index >= pd.Timestamp("2021-07-13", tz="UTC")) & (
            series.index < pd.Timestamp("2021-07-18", tz="UTC")
        )
        valid &= ~july
    return pd.Series(valid, index=series.index)


def read_native():
    ingest = load_module("45", "threshold_ingest")
    audit = ingest.load_audit_module()
    data = audit.read_source()
    # Preserve the last interval of 2025, not only the audit's endpoint-excluded view.
    with audit.SOURCE.open("rb") as stream:
        stream.seek(-4096, 2)
        last = stream.read().decode("utf-8-sig").strip().splitlines()[-1]
    end = pd.read_csv(io.StringIO(last), header=None, names=data.columns)
    end["timestamp_source"] = pd.to_datetime(end.timestamp_source, format="%d/%m/%Y %H:%M")
    if end.timestamp_source.iloc[0] != audit.END:
        raise ValueError("Unexpected final native interval")
    data = pd.concat([data, end], ignore_index=True)
    utc = pd.DatetimeIndex(ingest.convert_timestamps(data.timestamp_source, "fixed_utc_plus_1"))
    if utc.has_duplicates or not utc.to_series().diff().iloc[1:].eq(STEP).all():
        raise ValueError("Native record is not a unique 15-minute grid")
    values = (
        data.drop(columns="timestamp_source").apply(pd.to_numeric, errors="coerce").set_axis(utc)
    )
    return values, audit, ingest


def episode_catalogue(series, thresholds, series_key, gauge, primary, masks):
    positions = np.flatnonzero(series.ge(thresholds.H1).to_numpy())
    if not len(positions):
        return pd.DataFrame(), pd.DataFrame()
    # Link recorded active intervals, not a single arbitrary peak or a sample.
    groups = np.cumsum(np.r_[True, np.diff(positions) > 288])
    records, phases = [], []
    for group in np.unique(groups):
        active = positions[groups == group]
        first, last = int(active[0]), int(active[-1])
        end = min(last + 288, len(series) - 1)
        window = series.iloc[first : end + 1]
        before = series.iloc[first - 1] if first else np.nan
        closed = last + 288 < len(series) and series.iloc[last + 1 : last + 289].notna().all()
        eid = f"{series_key}|{series.index[first].isoformat()}"
        row = {
            "episode_id": eid,
            "series_key": series_key,
            "gauge": gauge,
            "primary": primary,
            "onset_utc": series.index[first],
            "last_H1_interval_utc": series.index[last],
            "review_end_utc": series.index[end],
            "onset_status": "adjacent_interval_entry"
            if np.isfinite(before) and before < thresholds.H1
            else "entry_after_gap_or_record_start",
            "recovery_observed": bool(closed),
            "record_end_censored": last + 288 >= len(series),
            "missing_review_intervals": int(window.isna().sum()),
            "observed_peak_m3s": float(window.max()),
            "review_span_h": len(window) / 4,
            "is_july_2021": bool(
                (window.index >= pd.Timestamp("2021-07-13", tz="UTC")).any()
                and (window.index < pd.Timestamp("2021-07-18", tz="UTC")).any()
            ),
            "duplicate_station_series": gauge == "6.Q.27",
        }
        for level in LEVELS:
            threshold = float(thresholds[level])
            label, _ = reach_label(window, threshold)
            if label == 0 and not closed:
                label = np.nan
            hits = np.flatnonzero(window.ge(threshold).to_numpy())
            when = window.index[hits[0]] if len(hits) else pd.NaT
            prior = (
                series.loc[when - STEP]
                if pd.notna(when) and when - STEP in series.index
                else np.nan
            )
            earlier_unknown = window.iloc[: hits[0]].isna().any() if len(hits) else False
            status = (
                "not_observed_complete_recovery"
                if label == 0
                else "unknown_gap_or_censoring"
                if pd.isna(label)
                else "adjacent_interval_entry"
                if np.isfinite(prior) and prior < threshold and not earlier_unknown
                else "first_recorded_entry_time_uncertain"
            )
            row[f"{level}_observed"] = label
            row[f"first_{level}_utc"] = when
            row[f"{level}_elapsed_from_first_H1_h"] = (
                (when - series.index[first]) / pd.Timedelta(hours=1) if pd.notna(when) else np.nan
            )
            row[f"{level}_observed_hours"] = float(window.ge(threshold).sum() / 4)
            for name, mask in masks.items():
                y, _ = reach_label(window, threshold, mask.iloc[first : end + 1])
                if y == 0 and not closed:
                    y = np.nan
                row[f"{level}_{name}"] = y
            phases.append(
                {
                    "episode_id": eid,
                    "series_key": series_key,
                    "gauge": gauge,
                    "primary": primary,
                    "level": level,
                    "threshold_m3s": threshold,
                    "observed_reach": label,
                    "first_recorded_utc": when,
                    "entry_status": status,
                    "elapsed_h": row[f"{level}_elapsed_from_first_H1_h"],
                    "reported_duration_h": row[f"{level}_observed_hours"],
                    "missing_review_intervals": row["missing_review_intervals"],
                    "recovery_observed": closed,
                }
            )
        row["range_sensitive"] = any(
            pd.isna(row[f"{level}_{n}"]) or row[f"{level}_{n}"] != row[f"{level}_observed"]
            for level in LEVELS
            for n in masks
        )
        records.append(row)
    return pd.DataFrame(records), pd.DataFrame(phases)


def all_event_outcomes(meta, native, hourly, thresholds, masks):
    rows = []
    for event in meta[meta.country.eq("NL")].itertuples():
        t = pd.Timestamp(event.onset_utc)
        future = pd.date_range(t + STEP, t + pd.Timedelta(hours=72), freq="15min")
        history = pd.date_range(t - pd.Timedelta(hours=24) + STEP, t, freq="15min")
        series = native[event.gauge]
        q = series.reindex(future)
        past = series.reindex(history)
        cutoff = series.get(t, np.nan)
        means = hourly[event.gauge].reindex(
            pd.date_range(t + pd.Timedelta(hours=1), periods=72, freq="h")
        )
        row = {
            "event_id": event.event_id,
            "gauge": event.gauge,
            "storm_id": event.storm_id,
            "onset_utc": t,
            "q_only_input_sample": event.q_only_input_sample,
            "q_only_scoring_sample": getattr(
                event, "q_only_scoring_sample", getattr(event, "phase_base_available", False)
            ),
            "measurement_concern": event.measurement_concern,
            "cutoff_native_q_m3s": cutoff,
            "prior24_complete": past.notna().all(),
            "response_observed_quarters": int(q.notna().sum()),
            "response_observed_hours": int(means.notna().sum()),
            "reported_native_peak_72h": q.max(),
            "reported_hourly_peak_72h": means.max(),
        }
        for level in LEVELS:
            threshold = float(thresholds.loc[event.gauge, level])
            y, h = reach_label(q, threshold)
            row[f"{level}_native"] = y
            row[f"{level}_first_response_h"] = h
            row[f"{level}_first_response_time_certain"] = bool(
                y == 1
                and np.isfinite(cutoff)
                and cutoff < threshold
                and q.iloc[: int(h * 4)].notna().all()
            )
            row[f"{level}_at_cutoff"] = (
                float(cutoff >= threshold) if np.isfinite(cutoff) else np.nan
            )
            row[f"{level}_below_cutoff"] = bool(
                np.isfinite(cutoff) and cutoff >= 0 and cutoff < threshold
            )
            row[f"{level}_previous24_reached"] = bool(past.ge(threshold).any())
            row[f"{level}_hourly"] = reach_label(means, threshold)[0]
            for name, mask in masks[event.gauge].items():
                row[f"{level}_{name}"] = reach_label(
                    q, threshold, mask.reindex(future, fill_value=False)
                )[0]
        rows.append(row)
    return pd.DataFrame(rows).set_index("event_id")


def group_mean(values, groups):
    return float(
        pd.DataFrame({"value": np.asarray(values, float), "group": np.asarray(groups)})
        .groupby("group")
        .value.mean()
        .mean()
    )


def squared_error_bounds(lower, upper, label):
    if np.isfinite(label):
        smallest = 0 if lower <= label <= upper else min((lower - label) ** 2, (upper - label) ** 2)
        largest = max((lower - label) ** 2, (upper - label) ** 2)
    else:
        smallest = min(lower**2, (1 - upper) ** 2)
        largest = max(upper**2, (1 - lower) ** 2)
    return smallest, largest


def phase_sample(sample, response_labels, level):
    frame = sample.copy()
    frame["complete_scoring_sample"] &= frame.event_id.map(
        response_labels[f"{level}_below_cutoff"]
    ).fillna(False)
    frame["complete_scoring_sample"] &= frame.event_id.map(
        response_labels[f"{level}_native"]
    ).notna()
    return frame


def validate_phase_donors(donors, meta, labels, level, scenario, quality):
    q = meta.loc[donors.query_event_id].reset_index(drop=True)
    a = meta.loc[donors.analogue_event_id].reset_index(drop=True)
    assert q.country.eq("NL").all() and a.country.eq("NL").all()
    assert (
        (pd.to_datetime(a.onset_utc, utc=True) + pd.Timedelta(hours=72))
        <= pd.to_datetime(q.onset_utc, utc=True)
    ).all()
    assert a.storm_id.ne(q.storm_id).all()
    assert not donors.duplicated(["query_event_id", "analogue_storm_id"]).any()
    assert donors.query_event_id.map(labels[f"{level}_below_cutoff"]).all()
    assert donors.analogue_event_id.map(labels[f"{level}_below_cutoff"]).all()
    assert donors.analogue_event_id.map(labels[f"{level}_native"]).notna().all()
    if scenario == "other_rivers":
        assert a.physical_river_group.ne(q.physical_river_group).all()
    if quality:
        assert not a.measurement_concern.any() and not q.measurement_concern.any()


def analyse_analogues(sample, arms, cohort, response_labels, meta, saved=None):
    output, pairs, coverage = [], [], []
    for level in ["H2", "H3"]:
        eligible = phase_sample(sample, response_labels, level)
        for scenario in ["all_rivers", "other_rivers"]:
            settings_to_run = [("main", False, False), ("quality_sensitivity", True, False)]
            if cohort.startswith("h1_"):
                settings_to_run.append(("complete_followup", False, True))
                settings_to_run.append(("observed_history_only", False, False))
            for analysis, quality, require_complete in settings_to_run:
                if require_complete:
                    eligible = phase_sample(sample, response_labels, level)
                    eligible["complete_scoring_sample"] &= eligible.event_id.map(
                        response_labels.response_observed_quarters
                    ).eq(288)
                else:
                    eligible = phase_sample(sample, response_labels, level)
                if analysis == "observed_history_only":
                    eligible["complete_scoring_sample"] &= eligible.event_id.map(
                        meta.unrepaired_history_complete
                    )
                complete = eligible[
                    eligible.complete_scoring_sample
                    & (~eligible.measurement_concern if quality else True)
                ]
                expected = None
                archive_cache = {}
                for arm, settings in arms.items():
                    if saved is None:
                        scores, donors = B.retrieve_prior_analogues(
                            eligible,
                            top_k=10,
                            min_candidates=1,
                            min_candidate_storms=1,
                            allow_short_archive=True,
                            exclude_same_river=scenario == "other_rivers",
                            exclude_measurement_concerns=quality,
                            **settings,
                        )
                    else:
                        cached_scores, cached_donors = saved
                        mask = (
                            cached_scores.scenario.eq(scenario)
                            & cached_scores.analysis.eq(analysis)
                            & cached_scores.arm.eq(arm)
                            & cached_scores.target_k.eq(10)
                        )
                        scores = cached_scores[mask].copy()
                        mask = (
                            cached_donors.scenario.eq(scenario)
                            & cached_donors.analysis.eq(analysis)
                            & cached_donors.arm.eq(arm)
                        )
                        donors = cached_donors[mask].copy()
                        if "target_k" in donors:
                            donors = donors[donors.target_k.eq(10)].copy()
                        if (
                            not scores.query_event_id.isin(complete.event_id).all()
                            or not donors.analogue_event_id.isin(complete.event_id).all()
                        ):
                            raise ValueError("Cached archive does not match phase eligibility")
                    ids = set(scores.query_event_id) if not scores.empty else set()
                    if expected is not None and ids != expected:
                        raise ValueError("Phase-matched arm coverage differs")
                    expected = ids
                    coverage.append(
                        dict(
                            cohort=cohort,
                            level=level,
                            scenario=scenario,
                            analysis=analysis,
                            arm=arm,
                            complete_base_events=int(sample.complete_scoring_sample.sum()),
                            below_at_cutoff_events=len(complete),
                            available_queries=len(ids),
                            unavailable_queries=len(complete) - len(ids),
                        )
                    )
                    if scores.empty:
                        continue
                    validate_phase_donors(donors, meta, response_labels, level, scenario, quality)
                    if not donors.analogue_event_id.map(
                        response_labels[f"{level}_below_cutoff"]
                    ).all():
                        raise ValueError("Already-above donor entered escalation archive")
                    donors = donors.copy()
                    donors["donor_native_reach"] = donors.analogue_event_id.map(
                        response_labels[f"{level}_native"]
                    )
                    donors["donor_hourly_reach"] = donors.analogue_event_id.map(
                        response_labels[f"{level}_hourly"]
                    )
                    donors["donor_first_time_certain"] = donors.analogue_event_id.map(
                        response_labels[f"{level}_first_response_time_certain"]
                    )
                    donors["donor_first_reach_h"] = donors.analogue_event_id.map(
                        response_labels[f"{level}_first_response_h"]
                    )
                    for name in ["range26", "range27_5"]:
                        donors["donor_" + name] = donors.analogue_event_id.map(
                            response_labels[f"{level}_{name}"]
                        )
                    tag = dict(
                        cohort=cohort, level=level, scenario=scenario, analysis=analysis, arm=arm
                    )
                    pairs.append(donors.assign(**tag))
                    score_index = scores.set_index("query_event_id")
                    for eid, g in donors.groupby("query_event_id"):
                        q = complete[complete.event_id.eq(eid)].iloc[0]
                        candidates = complete[
                            (complete.onset_utc + pd.Timedelta(hours=72)).le(q.onset_utc)
                            & complete.storm_id.ne(q.storm_id)
                        ]
                        if scenario == "other_rivers":
                            candidates = candidates[
                                candidates.physical_river_group.ne(q.physical_river_group)
                            ]
                        if len(candidates) != int(score_index.loc[eid, "candidate_count"]):
                            raise ValueError("Candidate count differs")
                        labels = response_labels.loc[candidates.event_id]
                        for k in [5, 10]:
                            chosen = g[g["rank"].le(k)]
                            y = response_labels.loc[eid, f"{level}_native"]
                            p = chosen.donor_native_reach.mean()
                            if eid not in archive_cache:
                                archive_cache[eid] = group_mean(
                                    labels[f"{level}_native"], candidates.storm_id
                                )
                            archive = archive_cache[eid]
                            same = candidates[candidates.gauge.eq(q.gauge)]
                            same_share = (
                                group_mean(
                                    response_labels.loc[same.event_id, f"{level}_native"],
                                    same.storm_id,
                                )
                                if len(same)
                                else np.nan
                            )
                            pred_hourly = chosen.donor_hourly_reach.mean()
                            true_hourly = response_labels.loc[eid, f"{level}_hourly"]
                            row = {
                                **tag,
                                "target_k": k,
                                "query_event_id": eid,
                                "query_storm_id": q.storm_id,
                                "query_onset_utc": q.onset_utc,
                                "gauge": q.gauge,
                                "query_river": q.physical_river_group,
                                "observed_reach": y,
                                "donor_reach_share": p,
                                "generic_archive_share": archive,
                                "same_gauge_archive_share": same_share,
                                "same_gauge_candidate_events": len(same),
                                "same_gauge_squared_error": (same_share - y) ** 2,
                                "share_squared_error": (p - y) ** 2 if np.isfinite(y) else np.nan,
                                "archive_squared_error": (archive - y) ** 2
                                if np.isfinite(y)
                                else np.nan,
                                "actual_donors": len(chosen),
                                "positive_donors": int(chosen.donor_native_reach.eq(1).sum()),
                                "unknown_donors": int(chosen.donor_native_reach.isna().sum()),
                                "prior24_reached": response_labels.loc[
                                    eid, f"{level}_previous24_reached"
                                ],
                                "first_escalation_24h": not response_labels.loc[
                                    eid, f"{level}_previous24_reached"
                                ],
                                "query_first_reach_h": response_labels.loc[
                                    eid, f"{level}_first_response_h"
                                ],
                                "observed_hourly_reach": true_hourly,
                                "hourly_share_squared_error": (pred_hourly - true_hourly) ** 2
                                if np.isfinite(true_hourly)
                                else np.nan,
                                "candidate_events": len(candidates),
                                "candidate_groups": candidates.storm_id.nunique(),
                            }
                            hitting = chosen[
                                chosen.donor_native_reach.eq(1) & chosen.donor_first_time_certain
                            ]
                            row["hitting_donor_timing_mismatch_h"] = (
                                abs(hitting.donor_first_reach_h - row["query_first_reach_h"]).mean()
                                if y == 1
                                and len(hitting)
                                and response_labels.loc[eid, f"{level}_first_response_time_certain"]
                                else np.nan
                            )
                            for name in ["range26", "range27_5"]:
                                v = chosen["donor_" + name]
                                lower = v.eq(1).sum() / len(v)
                                upper = (v.eq(1).sum() + v.isna().sum()) / len(v)
                                truth = response_labels.loc[eid, f"{level}_{name}"]
                                row[name + "_query_label"] = truth
                                row[name + "_share_lower"] = lower
                                row[name + "_share_upper"] = upper
                                row[name + "_loss_lower"], row[name + "_loss_upper"] = (
                                    squared_error_bounds(lower, upper, truth)
                                )
                            output.append(row)
                    print(f"{cohort}/{level}/{scenario}/{analysis}/{arm}: {len(ids)}", flush=True)
    return pd.DataFrame(output), pd.concat(pairs, ignore_index=True), pd.DataFrame(coverage)


def summarise(rows):
    keys = ["cohort", "level", "scenario", "analysis", "arm", "target_k"]
    summary = []
    for config, g in rows.groupby(keys):
        known = g[g.observed_reach.notna()]
        pos = known[known.observed_reach.eq(1)]
        neg = known[known.observed_reach.eq(0)]
        p_loss = pos.share_squared_error.mean()
        n_loss = neg.share_squared_error.mean()
        summary.append(
            {
                **dict(zip(keys, config, strict=True)),
                "queries": len(g),
                "known_labels": len(known),
                "positive_events": len(pos),
                "negative_events": len(neg),
                "positive_query_groups": pos.query_storm_id.nunique(),
                "mean_squared_error": known.share_squared_error.mean(),
                "archive_mean_squared_error": known.archive_squared_error.mean(),
                "same_gauge_reference_queries": int(known.same_gauge_squared_error.notna().sum()),
                "same_gauge_mean_squared_error": known.same_gauge_squared_error.mean(),
                "matched_analogue_error_same_gauge_available": known.loc[
                    known.same_gauge_squared_error.notna(), "share_squared_error"
                ].mean(),
                "positive_squared_error": p_loss,
                "negative_squared_error": n_loss,
                "balanced_squared_error": (p_loss + n_loss) / 2
                if len(pos) and len(neg)
                else np.nan,
                "positive_with_any_positive_donor": int(pos.positive_donors.gt(0).sum()),
                "negative_with_any_positive_donor": int(neg.positive_donors.gt(0).sum()),
                "known_target_timing_queries": int(g.hitting_donor_timing_mismatch_h.notna().sum()),
                "mean_hitting_donor_timing_mismatch_h": g.hitting_donor_timing_mismatch_h.mean(),
                "range26_unknown_query_labels": int(g.range26_query_label.isna().sum()),
                "range27_5_unknown_query_labels": int(g.range27_5_query_label.isna().sum()),
                "range26_mean_loss_lower": g.range26_loss_lower.mean(),
                "range26_mean_loss_upper": g.range26_loss_upper.mean(),
            }
        )
    return pd.DataFrame(summary)


def paired_intervals(rows):
    records = []
    keys = ["cohort", "level", "scenario", "analysis", "target_k"]
    for config, g in rows.groupby(keys):
        arms = {a: f.set_index("query_event_id") for a, f in g.groupby("arm")}
        contrasts = [("archive", a) for a in arms]
        if "raw_state" in arms and "ttm_ordered_state" in arms:
            contrasts.append(("raw_state", "ttm_ordered_state"))
        if "r0" in arms and "ttm_ordered_state" in arms:
            contrasts.append(("r0", "ttm_ordered_state"))
        if "alphaearth" in arms:
            contrasts += [
                (a, "alphaearth") for a in ["temporal", "area", "identity", "static_2017"]
            ]
        for ref, test in contrasts:
            a = arms[test]
            b = a if ref == "archive" else arms[ref]
            if set(a.index) != set(b.index):
                raise ValueError("Paired query sets differ")
            b = b.loc[a.index]
            if not a.actual_donors.eq(b.actual_donors).all():
                raise ValueError("Paired donor counts differ")
            difference = a.share_squared_error - (
                a.archive_squared_error if ref == "archive" else b.share_squared_error
            )
            for subset in ["all_known", "positive", "negative", "first_escalation_24h"]:
                select = a.observed_reach.notna()
                if subset in {"positive", "negative"}:
                    select &= a.observed_reach.eq(1 if subset == "positive" else 0)
                if subset == "first_escalation_24h":
                    select &= a.first_escalation_24h
                f = a.loc[select, ["query_storm_id", "query_onset_utc"]].copy()
                f["difference"] = difference[select]
                f["storm_year"] = pd.to_datetime(
                    f.groupby("query_storm_id").query_onset_utc.transform("min"), utc=True
                ).dt.year
                for unit in ["query_storm_id", "storm_year"]:
                    base = {
                        **dict(zip(keys, config, strict=True)),
                        "reference": ref,
                        "challenger": test,
                        "subset": subset,
                        "resampling_unit": unit,
                    }
                    if f[unit].nunique() < 2:
                        estimate = dict(
                            difference=f.difference.mean(),
                            lower=np.nan,
                            upper=np.nan,
                            query_count=len(f),
                            cluster_count=f[unit].nunique(),
                            draws=0,
                            status="undefined_or_too_few_clusters",
                        )
                    else:
                        estimate = {**C.REVIEW.cluster_interval(f, unit), "status": "estimated"}
                    records.append({**base, **estimate})
    return pd.DataFrame(records)


def plot_census(episodes, phases, native, hourly, thresholds, out):
    core = episodes[episodes.primary].copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    table = core.groupby("gauge")[[f"{level}_observed" for level in LEVELS]].sum()
    table.columns = LEVELS
    table.plot.bar(ax=ax)
    ax.set_ylabel("H1-linked episodes with a recorded threshold reach")
    ax.set_title("Current thresholds on all held native records; not observed flood impacts")
    fig.tight_layout()
    fig.savefig(out / "threshold_episode_counts.png", dpi=150)
    plt.close(fig)
    directory = out / "episode_atlas"
    directory.mkdir(exist_ok=True)
    selected = core[
        core.H2_observed.eq(1)
        | core.H3_observed.eq(1)
        | core.range_sensitive
        | core.onset_status.ne("adjacent_interval_entry")
    ].sort_values("onset_utc")
    index = []
    for page, start in enumerate(range(0, len(selected), 6), 1):
        block = selected.iloc[start : start + 6]
        fig, axes = plt.subplots(3, 2, figsize=(14, 11), squeeze=False)
        for ax, e in zip(axes.flat, block.itertuples(), strict=False):
            t = pd.Timestamp(e.onset_utc)
            end = pd.Timestamp(e.review_end_utc)
            q = native[e.series_key].loc[t - pd.Timedelta(hours=24) : end]
            h = hourly[e.series_key].loc[q.index[0] : end]
            ax.plot((q.index - t) / pd.Timedelta(hours=1), q, label="15-minute means", lw=1)
            ax.plot((h.index - t) / pd.Timedelta(hours=1), h, label="Hourly means", lw=1, alpha=0.7)
            for level, color in zip(LEVELS, ["#b8991e", "#e47722", "#b52929"], strict=True):
                ax.axhline(thresholds.loc[e.gauge, level], color=color, ls="--", label=level)
            ax.axvline(0, color="grey", lw=0.6)
            ax.set_title(
                f"{e.gauge} {t:%Y-%m-%d %H:%M} UTC\n{e.onset_status}; range concern={e.range_sensitive}",
                fontsize=9,
            )
            ax.set_xlabel("Hours from first recorded H1 interval")
            ax.set_ylabel("m³/s")
            index.append(
                {
                    "episode_id": e.episode_id,
                    "page": page,
                    "figure": f"episode_atlas/page_{page:03d}.png",
                }
            )
        for ax in list(axes.flat)[len(block) :]:
            ax.axis("off")
        axes.flat[0].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(directory / f"page_{page:03d}.png", dpi=110)
        plt.close(fig)
    pd.DataFrame(index).to_csv(out / "episode_atlas_index.csv", index=False)
    # Full table, not just the illustrated measurement-concern subset.
    body = core.to_html(index=False, escape=True)
    links = "".join(
        f'<p><a href="episode_atlas/page_{p:03d}.png">Review page {p}</a></p>'
        for p in range(1, (len(selected) + 5) // 6 + 1)
    )
    (out / "census_browser.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Current threshold census</title><h1>All primary H1-linked episodes</h1><p>Reported current-threshold categories, not historical warnings or measured flood impacts.</p>'
        + links
        + body
    )
    return len(selected)


def repair_isolated_history(history, native, cutoff, h1):
    """Repair only an isolated old low-flow hour; never endpoints or outcomes.

    Available native quarters and both complete neighboring hours must be below
    H1. Missing hours cannot be adjacent, and the last 24h remain untouched.
    Linear interpolation uses the original neighbors, never another repair.
    This is an input sensitivity, not evidence about an unobserved water level.
    """
    result, repairs = history.copy(), []
    for i in range(1, len(history) - 1):
        t = history.index[i]
        left, value, right = history.iloc[i - 1 : i + 2]
        if pd.notna(value) or t >= cutoff - pd.Timedelta(hours=24):
            continue
        quarters = native.reindex(pd.date_range(t - pd.Timedelta(minutes=45), t, freq="15min"))
        observed = quarters.dropna()
        if not (np.isfinite(left) and np.isfinite(right) and max(left, right) < h1):
            continue
        if observed.empty or observed.ge(h1).any():
            continue
        result.iloc[i] = (left + right) / 2
        repairs.append(
            {
                "timestamp_utc": t,
                "replacement_hourly_m3s": result.iloc[i],
                "observed_native_quarters": len(observed),
                "hours_before_assessment": (cutoff - t) / pd.Timedelta(hours=1),
            }
        )
    return result, repairs


def build_h1_library(episodes, old_hourly, rainfall, native, thresholds, masks, eras, out):
    source = load_module("46", "h1_event_semantics")
    scales = {}
    for gauge in thresholds.index.intersection(old_hourly.columns):
        era = source.assign_eras(old_hourly.index, eras[eras.gauge.eq(gauge)])
        _, scales[gauge] = source.era_thresholds(old_hourly[gauge], era)
    metadata, windows, repair_log = [], [], []
    for episode in episodes[episodes.primary].itertuples():
        cutoff = pd.Timestamp(episode.onset_utc).ceil("h")
        gauge = episode.gauge
        history_times = pd.date_range(cutoff - pd.Timedelta(hours=511), cutoff, freq="h")
        future_times = pd.date_range(cutoff + STEP, periods=288, freq="15min")
        history = old_hourly[gauge].reindex(history_times)
        unrepaired_complete = history.notna().all()
        history, repairs = repair_isolated_history(
            history, native[gauge], cutoff, thresholds.loc[gauge, "H1"]
        )
        repair_log.extend({"gauge": gauge, "assessment_utc": cutoff, **r} for r in repairs)
        future = native[gauge].reindex(future_times)
        scale = scales[gauge].get(cutoff, np.nan)
        complete = history.notna().all() and np.isfinite(scale) and scale > 0
        times = pd.date_range(
            cutoff - pd.Timedelta(hours=511), cutoff + pd.Timedelta(hours=72), freq="h"
        )
        watercourse = {
            "11.Q.32": "Eyserbeek",
            "10.Q.29": "Geul",
            "13.Q.34": "Gulp",
            "15.Q.41": "Voer",
            "18.Q.45": "Worm",
            "6.Q.18": "Geleenbeek",
        }[gauge]
        rain = rainfall[watercourse].reindex(times)
        eid = f"H1|{gauge}|{cutoff.isoformat()}"
        era_rows = eras[eras.gauge.eq(gauge)]
        upper = float(era_rows.domain_max_m3s.max())
        concern = (
            episode.range_sensitive
            or episode.observed_peak_m3s > upper
            or (gauge == "13.Q.34" and episode.observed_peak_m3s > 3)
        )
        metadata.append(
            {
                "event_id": eid,
                "episode_id": episode.episode_id,
                "gauge": gauge,
                "watercourse": watercourse,
                "country": "NL",
                "physical_river_group": "Wurm/Worm" if gauge == "18.Q.45" else watercourse,
                "onset_utc": cutoff,
                "native_H1_entry_utc": episode.onset_utc,
                "assessment_delay_h": (cutoff - pd.Timestamp(episode.onset_utc))
                / pd.Timedelta(hours=1),
                "p99_m3s": scale,
                "primary_usable": True,
                "measurement_concern": bool(concern),
                "unrepaired_history_complete": bool(unrepaired_complete),
                "history_repaired_hours": len(repairs),
                "history_discharge_fraction": history.notna().mean(),
                "history_rainfall_fraction": rain.iloc[:512].notna().mean(),
                "outcome_discharge_fraction": future.notna().mean(),
                "temporal_input_sample": bool(complete),
                "q_only_input_sample": bool(complete),
                "phase_base_available": bool(complete and future.notna().any()),
                "native_response_complete": future.notna().all(),
                "native_observed_peak_72h": future.max(),
            }
        )
        windows.append(
            pd.DataFrame(
                {
                    "event_id": eid,
                    "relative_hour": np.arange(-511, 73),
                    "target_discharge_m3s": pd.concat(
                        [history, old_hourly[gauge].reindex(times[512:])]
                    ).to_numpy(),
                    "catchment_rainfall_mm": rain.to_numpy(),
                }
            )
        )
    index = source.cluster_regional_storms(pd.DataFrame(metadata))
    window = pd.concat(windows, ignore_index=True)
    sample = B.build_signatures(index, window)
    details = index.set_index("event_id")
    sample["complete_scoring_sample"] = sample.event_id.map(details.phase_base_available)
    sample["outcome_peak_over_p99_72h"] = sample.event_id.map(
        details.native_observed_peak_72h / details.p99_m3s
    )
    sample["country"] = "NL"
    sample["physical_river_group"] = sample.event_id.map(details.physical_river_group)
    ids = sample.loc[sample.common_representation_sample, "event_id"]
    raw, checks = E.S.TTM.RAW.standardized_histories(ids, window)
    state = E.S.discharge_state(index, window, ids)
    ordered, receipt = E.S.TTM.extract_embeddings(raw, pooling="ordered")
    pd.DataFrame(repair_log).to_csv(out / "H1_history_repairs.csv", index=False)
    index.to_csv(out / "H1_assessment_inventory.csv", index=False)
    sample.to_csv(out / "H1_assessment_signatures.csv", index=False)
    checks.to_csv(out / "H1_history_checks.csv", index=False)
    raw.to_parquet(out / "H1_standardized_histories.parquet")
    state.to_parquet(out / "H1_discharge_state.parquet")
    ordered.to_parquet(out / "H1_ordered_TTM.parquet")
    (out / "H1_TTM_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return index, sample, raw, state, ordered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    thresholds = read_thresholds(THRESHOLDS)
    native, audit, ingest = read_native()
    cohort = pd.read_csv(ROOT / "config/event_study_cohort.csv")
    core = set(cohort.gauge)
    eras = pd.read_csv(ROOT / "data/interim/event_study_rating_eras.csv")
    qa = pd.read_csv(ROOT / "data/processed/waterschap_station_source_qa.csv").set_index(
        "series_key"
    )
    masks = {}
    hourly = {}
    catalogues = []
    phase_tables = []
    crossings = []
    occupancy = []
    coverage = []
    for key, gauge, watercourse, station, note in audit.SERIES:
        if gauge not in thresholds.index:
            continue
        series = native[key]
        ts = thresholds.loc[gauge]
        hourly[key] = ingest.four_quarter_hour_mean(series, pd.Series(series.index))
        mask = {
            name: reliable_mask(series, gauge, eras, qa, cap)
            for name, cap in [("range26", 26), ("range27_5", 27.5)]
        }
        if key == gauge:
            masks[gauge] = mask
        ep, phase = episode_catalogue(series, ts, key, gauge, key in core, mask)
        if len(ep):
            catalogues.append(ep)
            phase_tables.append(phase)
        for level in LEVELS:
            entries = crossing_entries(series, float(ts[level]))
            entries["series_key"] = key
            entries["gauge"] = gauge
            entries["primary"] = key in core
            entries["level"] = level
            crossings.append(entries)
            for resolution, q, step in [("native15", series, 0.25), ("hourly", hourly[key], 1)]:
                for year, year_q in q.groupby(q.index.year):
                    occupancy.append(
                        {
                            "series_key": key,
                            "gauge": gauge,
                            "primary": key in core,
                            "resolution": resolution,
                            "year_utc": year,
                            "level": level,
                            "observed_hours": year_q.notna().sum() * step,
                            "threshold_hours": year_q.ge(ts[level]).sum() * step,
                            "missing_hours": year_q.isna().sum() * step,
                        }
                    )
        coverage.append(
            {
                "series_key": key,
                "gauge": gauge,
                "station": station,
                "watercourse": watercourse,
                "primary": key in core,
                "duplicate_station_series": gauge == "6.Q.27",
                "structural_note": note,
                "observed_intervals": int(series.notna().sum()),
                "missing_intervals": int(series.isna().sum()),
                "first_record_utc": series.index[0],
                "last_record_utc": series.index[-1],
                "H1_linked_episodes": len(ep),
            }
        )
    hourly = pd.DataFrame(hourly)
    old = pd.read_csv(
        ROOT / "data/interim/event_study_discharge_hourly.csv", index_col=0, parse_dates=True
    )
    differences = []
    for gauge in core:
        new = hourly[gauge].reindex(old.index)
        np.testing.assert_allclose(
            new[old[gauge].notna()], old.loc[old[gauge].notna(), gauge], rtol=0, atol=1e-12
        )
        for t in old.index[new.notna() & old[gauge].isna()]:
            differences.append(
                {
                    "gauge": gauge,
                    "timestamp_utc": t,
                    "reason": "native analysis includes supplied final midnight endpoint",
                }
            )
    pd.DataFrame(differences, columns=["gauge", "timestamp_utc", "reason"]).to_csv(
        out / "extra_complete_endpoint_hours.csv", index=False
    )
    thresholds.reset_index().to_csv(out / "current_thresholds.csv", index=False)
    episodes = pd.concat(catalogues, ignore_index=True)
    phases = pd.concat(phase_tables, ignore_index=True)
    episodes.to_csv(out / "episodes.csv", index=False)
    phases.to_csv(out / "episode_phase_progression.csv", index=False)
    pd.concat(crossings, ignore_index=True).to_csv(out / "all_threshold_entries.csv", index=False)
    pd.DataFrame(occupancy).to_csv(out / "phase_occupancy_by_year.csv", index=False)
    pd.DataFrame(coverage).to_csv(out / "source_coverage.csv", index=False)
    meta = pd.read_csv(E.READY / "event_inventory.csv").set_index("event_id")
    labels = all_event_outcomes(meta.reset_index(), native, hourly, thresholds, masks)
    labels.to_csv(out / "all_p99_event_phase_outcomes.csv")
    primary = episodes[episodes.primary]
    summary = (
        primary.groupby("gauge")
        .agg(
            episodes=("episode_id", "size"),
            onset_censored=("onset_status", lambda v: v.ne("adjacent_interval_entry").sum()),
            unknown_recovery=("recovery_observed", lambda v: (~v).sum()),
            **{
                f"{level}_reached": (f"{level}_observed", lambda v: v.eq(1).sum())
                for level in LEVELS
            },
            **{
                f"{level}_unknown": (f"{level}_observed", lambda v: v.isna().sum())
                for level in LEVELS
            },
        )
        .reset_index()
    )
    summary.to_csv(out / "primary_episode_summary.csv", index=False)
    plot_census(episodes, phases, native, hourly, thresholds, out)
    # Bind held preparation before retrieval, never regenerate earlier vectors/results.
    hashes = {}
    prepared = json.loads((E.READY / "manifest.json").read_text())
    for name, digest in prepared["input_sha256"].items():
        if E.S.TTM.sha256(ROOT / name) != digest:
            raise ValueError("Changed prepared input " + name)
        hashes[name] = digest
    for name, digest in prepared["outputs_sha256"].items():
        if E.S.TTM.sha256(E.READY / name) != digest:
            raise ValueError("Changed prepared output " + name)
        hashes[str((E.READY / name).relative_to(ROOT))] = digest
    paths = [
        THRESHOLDS,
        audit.SOURCE,
        ROOT / "config/event_study_cohort.csv",
        ROOT / "data/interim/event_study_rating_eras.csv",
        ROOT / "data/processed/waterschap_station_source_qa.csv",
        ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet",
        X.OUT / "rainfall_event_coverage.csv",
        ROOT / "docs/limburg-warning-threshold-analysis-2026-10-14.md",
    ]
    for path in paths:
        hashes[str(path.relative_to(ROOT))] = E.S.TTM.sha256(path)
    sample = pd.read_csv(E.READY / "q_only_signatures.csv", parse_dates=["onset_utc"])
    sample = sample[sample.gauge.isin(core)].copy()
    sample["country"] = "NL"
    sample["physical_river_group"] = sample.event_id.map(meta.physical_river_group)
    raw = pd.read_parquet(E.READY / "q_only_standardized_histories.parquet")
    ordered = pd.read_parquet(E.READY / "q_only_ttm_ordered.parquet")
    state = pd.read_parquet(E.READY / "q_only_discharge_state.parquet")
    arms = {
        "r1": {"representation_vectors": raw},
        "raw_state": {
            "distance_blocks": {"temporal": raw, "state": state},
            "robust_distance_blocks": ("state",),
        },
        "ttm_ordered_state": {
            "distance_blocks": {"temporal": ordered, "state": state},
            "robust_distance_blocks": ("state",),
        },
    }
    rainfall = pd.read_csv(
        ROOT / "data/interim/radolan_catchment_hourly.csv", index_col=0, parse_dates=True
    )
    h1_index, h1_sample, h1_raw, h1_state, h1_ordered = build_h1_library(
        episodes, old, rainfall, native, thresholds, masks, eras, out
    )
    h1_meta = h1_index.set_index("event_id")
    h1_labels = all_event_outcomes(h1_index, native, hourly, thresholds, masks)
    h1_labels.to_csv(out / "H1_assessment_phase_outcomes.csv")
    h1_arms = {
        "r1": {"representation_vectors": h1_raw},
        "raw_state": {
            "distance_blocks": {"temporal": h1_raw, "state": h1_state},
            "robust_distance_blocks": ("state",),
        },
        "ttm_ordered_state": {
            "distance_blocks": {"temporal": h1_ordered, "state": h1_state},
            "robust_distance_blocks": ("state",),
        },
    }
    result = [analyse_analogues(h1_sample, h1_arms, "h1_q_only", h1_labels, h1_meta)]
    h1_rain = h1_sample.copy()
    h1_rain["complete_scoring_sample"] &= h1_rain.event_id.map(
        h1_meta.history_rainfall_fraction
    ).eq(1)
    result.append(
        analyse_analogues(
            h1_rain,
            {"r0": {}, **{a: v for a, v in h1_arms.items() if a != "r1"}},
            "h1_rain_matched",
            h1_labels,
            h1_meta,
        )
    )
    r0_maximal = h1_sample.copy()
    r0_maximal["complete_scoring_sample"] = (
        r0_maximal[B.FEATURE_COLUMNS].notna().all(axis=1)
        & r0_maximal.event_id.map(h1_meta.native_observed_peak_72h).notna()
    )
    result.append(analyse_analogues(r0_maximal, {"r0": {}}, "h1_r0_maximal", h1_labels, h1_meta))
    years = pd.read_parquet(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
    h1_context = X.join_context(h1_sample, years)
    h1_context = h1_context[
        h1_context.context_available & h1_context.common_representation_sample
    ].copy()
    result.append(
        analyse_analogues(
            h1_context,
            X.context_settings(h1_context, h1_ordered, h1_state, years),
            "h1_context",
            h1_labels,
            h1_meta,
        )
    )
    # These frozen p99 cohorts have identical phase-eligible archives. Replay
    # exact saved donor sets instead of silently changing their representation.
    saved_scores = pd.read_csv(E.OUT / "event_assessments.csv", float_precision="round_trip")
    saved_donors = pd.read_csv(E.OUT / "selected_donors.csv", float_precision="round_trip")
    q_cache = (
        saved_scores[saved_scores.cohort.eq("q_only_dutch")],
        saved_donors[saved_donors.cohort.eq("q_only_dutch")],
    )
    result.append(analyse_analogues(sample, arms, "p99_q_only", labels, meta, saved=q_cache))
    rain = pd.read_csv(X.OUT / "rainfall_event_coverage.csv").set_index("event_id")
    rain_sample = sample.copy()
    rain_sample[B.FEATURE_COLUMNS] = rain.loc[rain_sample.event_id, B.FEATURE_COLUMNS].to_numpy()
    rain_sample["complete_scoring_sample"] = rain.loc[
        rain_sample.event_id, "complete_scoring_sample"
    ].to_numpy()
    cache_scores = pd.read_csv(X.OUT / "event_assessments.csv", float_precision="round_trip")
    cache_donors = pd.read_csv(X.OUT / "selected_donors.csv", float_precision="round_trip")
    for cohort_name, subset in [("rain_matched", rain_sample), ("context", None)]:
        if cohort_name == "context":
            subset = X.join_context(sample, years)
            subset = subset[subset.context_available & subset.common_representation_sample].copy()
            settings = X.context_settings(subset, ordered, state, years)
        else:
            settings = {"r0": {}, **{a: v for a, v in arms.items() if a != "r1"}}
        scores_cache = cache_scores[
            cache_scores.cohort.eq(cohort_name)
            & cache_scores.policy.eq("domestic")
            & cache_scores.query_country.eq("NL")
        ]
        donor_cache = cache_donors[
            cache_donors.cohort.eq(cohort_name)
            & cache_donors.policy.eq("domestic")
            & cache_donors.query_event_id.map(meta.country).eq("NL")
        ]
        result.append(
            analyse_analogues(
                subset,
                settings,
                "p99_" + cohort_name,
                labels,
                meta,
                saved=(scores_cache, donor_cache),
            )
        )
    for path in [
        E.OUT / "event_assessments.csv",
        E.OUT / "selected_donors.csv",
        X.OUT / "event_assessments.csv",
        X.OUT / "selected_donors.csv",
        ROOT / "data/interim/radolan_catchment_hourly.csv",
        E.S.TTM.MODEL_DIR / "model.safetensors",
        E.S.TTM.MODEL_DIR / "config.json",
    ]:
        hashes[str(path.relative_to(ROOT))] = E.S.TTM.sha256(path)
    rows = pd.concat([x[0] for x in result], ignore_index=True)
    donors = pd.concat([x[1] for x in result], ignore_index=True)
    model_coverage = pd.concat([x[2] for x in result], ignore_index=True)
    rows.to_csv(out / "analogue_event_results.csv", index=False)
    donors.to_csv(out / "phase_conditioned_donors.csv", index=False)
    model_coverage.to_csv(out / "analogue_coverage.csv", index=False)
    summary = summarise(rows)
    summary.to_csv(out / "analogue_summary.csv", index=False)
    print("Computing paired escalation-evidence intervals", flush=True)
    paired_intervals(rows).to_csv(out / "paired_intervals.csv", index=False)
    rows.groupby(["cohort", "level", "scenario", "analysis", "arm", "target_k", "gauge"])[
        ["observed_reach", "share_squared_error", "archive_squared_error"]
    ].agg(["count", "mean"]).to_csv(out / "analogue_by_gauge.csv")
    # Explicit aggregation and risk checks; no sampled event validation.
    assert len(labels) == int(meta.country.eq("NL").sum()) and set(core) == set(
        summary_g for summary_g in labels.gauge.unique()
    )
    all_meta = pd.concat([meta, h1_meta])
    assert donors.analogue_event_id.map(all_meta.country).eq("NL").all()
    manifest = {
        "analysis": "full retrospective current-threshold census",
        "input_sha256": hashes,
        "source_sha256": {
            str(p.relative_to(ROOT)): E.S.TTM.sha256(p)
            for p in [
                Path(__file__),
                ROOT / "scripts/35_audit_waterschap_delivery.py",
                ROOT / "scripts/45_build_event_study_discharge.py",
                ROOT / "scripts/65_hydrological_analogue_baseline.py",
                ROOT / "scripts/84_complete_cross_border_analogues.py",
            ]
        },
        "code_version": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "bootstrap_draws": 9999,
        "seed": 20261013,
        "all_p99_episodes": len(labels),
        "all_H1_assessments": len(h1_labels),
        "primary_H1_episodes": len(primary),
        "all_source_series": len(coverage),
        "sampled_events": 0,
        "flood_impact_labels_inferred": 0,
        "outputs_sha256": {
            str(p.relative_to(out)): E.S.TTM.sha256(p)
            for p in out.rglob("*")
            if p.suffix in [".csv", ".png", ".html", ".parquet", ".json"]
            and p.name != "manifest.json"
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in [
                    "all_p99_episodes",
                    "primary_H1_episodes",
                    "all_source_series",
                    "sampled_events",
                ]
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
