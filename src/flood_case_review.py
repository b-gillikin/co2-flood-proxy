"""Flood-case linkage and post-outcome diagnostics; no model fitting or reranking."""

import json

import numpy as np
import pandas as pd


def build_register(episodes, evidence, core_gauges):
    rows = []
    for e in episodes[episodes.H3_observed.eq(1)].itertuples():
        first = pd.Timestamp(e.first_H3_utc)
        region = (
            "regional_2021_07"
            if first.year == 2021 and first.month == 7
            else "regional_" + first.strftime("%Y_%m_%d")
        )
        rows.append(
            {
                "case_id": "H3_" + e.series_key + "_" + first.strftime("%Y%m%d"),
                "gauge": e.gauge,
                "series_key": e.series_key,
                "country": "NL",
                "primary": bool(e.primary),
                "start": pd.Timestamp(e.onset_utc),
                "end": pd.Timestamp(e.review_end_utc),
                "first_H3_utc": first,
                "date_precision": "native_recorded_threshold_episode",
                "regional_event": region,
                "evidence_type": "current_H3_recorded_reach",
                "impact_confirmation": "not_independent_inundation_observation",
                "source_ids": json.dumps(["supplied_thresholds_and_native_records"]),
                "episode_id": e.episode_id,
                "native_H1_entry_status": getattr(e, "onset_status", "not_supplied"),
                "native_H3_entry_status": getattr(e, "H3_entry_status", "not_supplied"),
                "source_series_warning": "composite_or_duplicate_not_direct_high_flow_evidence"
                if e.gauge == "6.Q.27"
                else "",
                "range26_H3": e.H3_range26,
                "range27_5_H3": e.H3_range27_5,
                "note": "Current threshold applied retrospectively; not a reconstructed historical warning."
                + (
                    " Ancillary supplied series, outside the eight-gauge model cohort."
                    if not e.primary
                    else ""
                ),
            }
        )
    for item in evidence["documentary_cases"]:
        r = dict(item)
        r.update(
            start=pd.Timestamp(r["start"]),
            end=pd.Timestamp(r["end"]),
            primary=r["gauge"] in core_gauges,
            series_key=r["gauge"],
            first_H3_utc=pd.NaT,
            episode_id=None,
            source_ids=json.dumps(r["source_ids"]),
            range26_H3=np.nan,
            range27_5_H3=np.nan,
        )
        rows.append(r)
    return pd.DataFrame(rows).sort_values(["start", "case_id"]).reset_index(drop=True)


def link_inventory(register, inventory):
    """Link overlapping onset chains/recovery, retaining coarse matches as candidates only."""
    rows = []
    for case in register.itertuples():
        g = inventory[inventory.gauge.eq(case.gauge)]
        end = pd.to_datetime(g.last_crossing_utc, utc=True) + pd.Timedelta(hours=72)
        selected = g[g.onset_utc.lt(case.end) & end.ge(case.start)]
        coarse = case.date_precision in {"year_only", "early_month_statement_month_review_window"}
        for _, e in selected.iterrows():
            onset = e.onset_utc
            first = case.first_H3_utc
            timing = "documentary_window_no_exact_flood_onset"
            if pd.notna(first):
                timing = (
                    "after_first_H3"
                    if onset >= first
                    else "H3_within_72h"
                    if first <= onset + pd.Timedelta(hours=72)
                    else "H3_after_72h"
                )
            reasons = []
            if not bool(e.q_only_input_sample):
                reasons.append("insufficient_or_inadmissible_history")
            if bool(e.onset_censored):
                reasons.append("onset_censored")
            if float(e.outcome_discharge_fraction) < 1:
                reasons.append("incomplete_72h_discharge")
            for flag in [
                "provisional_high_flow",
                "response_out_of_rating_domain",
                "response_crosses_rating_period",
            ]:
                if pd.notna(e.get(flag)) and bool(e[flag]):
                    reasons.append(flag)
            if not bool(e.outcome_score_admissible) and not reasons:
                reasons.append("exact_response_not_admissible")
            rows.append(
                {
                    "case_id": case.case_id,
                    "event_id": e.event_id,
                    "match_status": "coarse_documentary_candidate_not_flood_label"
                    if coarse
                    else "date_resolved_episode_overlap",
                    "timing_role": timing,
                    "q_only_input_sample": bool(e.q_only_input_sample),
                    "q_only_scoring_sample": bool(e.q_only_scoring_sample),
                    "onset_utc": onset,
                    "measurement_concern": bool(e.measurement_concern),
                    "exclusion_reasons": ";".join(reasons),
                    "history_discharge_fraction": e.history_discharge_fraction,
                    "outcome_discharge_fraction": e.outcome_discharge_fraction,
                }
            )
    return pd.DataFrame(rows)


def archive_stage(positive_candidates, unknown_candidates, positive_selected):
    """A missing documented positive is not evidence that all candidates were non-floods."""
    if positive_candidates == 0:
        return (
            "no_confirmed_positive_with_incomplete_labelling"
            if unknown_candidates
            else "no_positive_in_observed_label_archive"
        )
    if positive_selected == 0:
        return "confirmed_positive_available_not_selected"
    return "confirmed_positive_selected_examine_estimate"


def curve_diagnostics(query, candidates, selected):
    """Post-outcome oracle and averaging diagnostics, never operational donor selection.

    Candidate single-trajectory error is not a fair equal-k ensemble comparator.
    It only checks whether a closer observed trajectory existed in this archive.
    """
    q, a, d = (np.asarray(x, float) for x in [query, candidates, selected])
    if q.shape != (72,) or a.ndim != 2 or d.ndim != 2 or a.shape[1] != 72 or d.shape[1] != 72:
        raise ValueError("Complete 72-hour arrays required")
    if not all(np.isfinite(x).all() for x in [q, a, d]) or not len(a) or not len(d):
        raise ValueError("Finite nonempty arrays required")
    errors = np.sqrt(((a - q) ** 2).mean(axis=1))
    mean = d.mean(axis=0)
    peaks = d.max(axis=1)
    mechanism = "ensemble_peak_not_below_query"
    if peaks.max() < q.max():
        mechanism = "all_selected_peaks_below_query"
    elif mean.max() < q.max():
        mechanism = "extreme_member_diluted_or_time_smeared"
    return {
        "oracle_best_single_curve_rmse": float(errors.min()),
        "oracle_best_candidate_position": int(errors.argmin()),
        "selected_mean_curve_rmse_recomputed": float(np.sqrt(((mean - q) ** 2).mean())),
        "query_peak_over_p99": float(q.max()),
        "max_selected_peak_over_p99": float(peaks.max()),
        "mean_selected_peak_over_p99": float(peaks.mean()),
        "peak_of_mean_curve_over_p99": float(mean.max()),
        "peak_loss_from_time_averaging": float(peaks.mean() - mean.max()),
        "peak_estimate_pattern": mechanism,
    }
