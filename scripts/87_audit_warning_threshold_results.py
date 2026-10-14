#!/usr/bin/env python3
"""Independently recompute native threshold outcomes and published aggregates."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "threshold_run", ROOT / "scripts/86_analyse_warning_threshold_progression.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def native_outcome(series, cutoff, threshold):
    values = series.reindex(
        pd.date_range(cutoff + pd.Timedelta(minutes=15), periods=288, freq="15min")
    )
    positions = np.flatnonzero(values.to_numpy() >= threshold)
    if len(positions):
        j = int(positions[0])
        return (
            1.0,
            (j + 1) / 4,
            bool(
                values.iloc[:j].notna().all()
                and pd.notna(series.get(cutoff))
                and series.get(cutoff) < threshold
            ),
        )
    return (0.0 if values.notna().all() else np.nan), np.nan, False


def main():
    out = M.OUT
    manifest = json.loads((out / "manifest.json").read_text())
    for name, digest in manifest["outputs_sha256"].items():
        assert M.E.S.TTM.sha256(out / name) == digest, name
    for name, digest in manifest["input_sha256"].items():
        assert M.E.S.TTM.sha256(ROOT / name) == digest, name
    native, _, _ = M.read_native()
    thresholds = M.read_thresholds(M.THRESHOLDS)
    verified = 0
    for name in ["all_p99_event_phase_outcomes.csv", "H1_assessment_phase_outcomes.csv"]:
        frame = pd.read_csv(out / name)
        for row in frame.itertuples():
            cutoff = pd.Timestamp(row.onset_utc)
            for level in M.LEVELS:
                y, first, certain = native_outcome(
                    native[row.gauge], cutoff, thresholds.loc[row.gauge, level]
                )
                assert np.isclose(y, getattr(row, level + "_native"), equal_nan=True), row.event_id
                assert np.isclose(
                    first, getattr(row, level + "_first_response_h"), equal_nan=True
                ), row.event_id
                assert certain == getattr(row, level + "_first_response_time_certain"), row.event_id
                verified += 1
    episodes = pd.read_csv(out / "episodes.csv")
    for source in pd.read_csv(out / "source_coverage.csv").itertuples():
        q = native[source.series_key]
        positions = np.flatnonzero(q.to_numpy() >= thresholds.loc[source.gauge, "H1"])
        groups = np.cumsum(np.r_[True, np.diff(positions) > 288]) if len(positions) else []
        assert len(np.unique(groups)) == episodes.series_key.eq(source.series_key).sum(), (
            source.series_key
        )
    rows = pd.read_csv(out / "analogue_event_results.csv")
    np.testing.assert_allclose(
        rows.share_squared_error, (rows.donor_reach_share - rows.observed_reach) ** 2
    )
    np.testing.assert_allclose(
        rows.archive_squared_error, (rows.generic_archive_share - rows.observed_reach) ** 2
    )
    keys = ["cohort", "level", "scenario", "analysis", "arm", "target_k"]
    donors = pd.read_csv(out / "phase_conditioned_donors.csv", low_memory=False)
    donor_keys = ["cohort", "level", "scenario", "analysis", "arm", "query_event_id"]
    for k in [5, 10]:
        means = donors[donors["rank"].le(k)].groupby(donor_keys).donor_native_reach.mean()
        actual = rows[rows.target_k.eq(k)].set_index(donor_keys).donor_reach_share
        np.testing.assert_allclose(means.sort_index(), actual.sort_index(), atol=1e-14)
    metadata = pd.concat(
        [
            pd.read_csv(out / "all_p99_event_phase_outcomes.csv"),
            pd.read_csv(out / "H1_assessment_phase_outcomes.csv"),
        ]
    ).set_index("event_id")
    for level, pairs in donors.groupby("level"):
        expected_labels = pairs.analogue_event_id.map(metadata[level + "_native"])
        np.testing.assert_allclose(pairs.donor_native_reach, expected_labels)
        assert pairs.analogue_event_id.map(metadata[level + "_below_cutoff"]).all()
    assert (
        pd.to_datetime(donors.analogue_onset_utc, utc=True) + pd.Timedelta(hours=72)
        <= pd.to_datetime(donors.query_onset_utc, utc=True)
    ).all()
    assert donors.analogue_storm_id.ne(donors.query_storm_id).all()
    expected = rows.groupby(keys).share_squared_error.mean()
    reported = pd.read_csv(out / "analogue_summary.csv").set_index(keys).mean_squared_error
    np.testing.assert_allclose(expected.sort_index(), reported.sort_index(), atol=1e-14)
    # Whole eligible low-flow record masking check (no sampled centers): how
    # much error does replacing an observed hour by its neighbor average cause?
    ingest = M.load_module("45", "audit_threshold_hourly")
    validation = []
    repairs = pd.read_csv(out / "H1_history_repairs.csv")
    for gauge in episodes.loc[episodes.primary, "gauge"].unique():
        q = native[gauge]
        h = ingest.four_quarter_hour_mean(q, pd.Series(q.index))
        for repair in repairs[repairs.gauge.eq(gauge)].itertuples():
            t = pd.Timestamp(repair.timestamp_utc)
            cutoff = pd.Timestamp(repair.assessment_utc)
            assert t < cutoff - pd.Timedelta(hours=24)
            assert pd.isna(h.get(t))
            left, right = h.get(t - pd.Timedelta(hours=1)), h.get(t + pd.Timedelta(hours=1))
            assert max(left, right) < thresholds.loc[gauge, "H1"]
            assert np.isclose((left + right) / 2, repair.replacement_hourly_m3s)
            quarters = q.reindex(
                pd.date_range(t - pd.Timedelta(minutes=45), t, freq="15min")
            ).dropna()
            assert len(quarters) == repair.observed_native_quarters
            assert len(quarters) and quarters.lt(thresholds.loc[gauge, "H1"]).all()
        low = h.lt(thresholds.loc[gauge, "H1"])
        valid = low & low.shift(1, fill_value=False) & low.shift(-1, fill_value=False)
        error = ((h.shift(1) + h.shift(-1)) / 2 - h).loc[valid].abs()
        validation.append(
            {
                "gauge": gauge,
                "masked_observed_hours": len(error),
                "absolute_error_mean_m3s": error.mean(),
                "absolute_error_p99_m3s": error.quantile(0.99),
                "absolute_error_max_m3s": error.max(),
            }
        )
    pd.DataFrame(validation).to_csv(out / "history_repair_masking_validation.csv", index=False)
    receipt = {
        "verified_native_phase_outcomes": verified,
        "verified_analogue_rows": len(rows),
        "verified_selected_donor_rows": len(donors),
        "verified_census_episodes": len(episodes),
        "verified_historical_input_repairs": len(repairs),
        "max_summary_error": float((expected - reported).abs().max()),
        "all_manifest_hashes_match": True,
        "analysis_manifest_sha256": M.E.S.TTM.sha256(out / "manifest.json"),
        "audit_source_sha256": M.E.S.TTM.sha256(Path(__file__)),
        "mask_validation_is_not_proof_of_missing_peak_absence": True,
    }
    (out / "independent_audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
