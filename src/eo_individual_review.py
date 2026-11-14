"""Paired point-trajectory summaries with shared whole-storm/year resampling."""

from __future__ import annotations

import numpy as np
import pandas as pd


def paired_summary(
    rows, differences, years, multiplicities, transfer=False, fixed_population=False
):
    """Equal sites, then storms, then available issue offsets on PAIRED support.

    Whole storms belong to their INITIAL landmark year. The same matrix of
    year multiplicities is used across all methods/scenarios/strata. Missing
    draws are retained/countable; no retry or favourable-draw selection.
    """
    frame = rows[["gauge", "physical_river", "storm_id", "cutoff_utc"]].copy()
    required_sites = frame[["gauge", "physical_river"]].drop_duplicates().sort_values("gauge")
    frame["difference"] = differences
    frame = frame[np.isfinite(frame.difference)]
    empty = dict(
        estimate=np.nan,
        lower=np.nan,
        upper=np.nan,
        assessments=0,
        storms=0,
        sites=len(required_sites) if fixed_population else 0,
        years=0,
        bootstrap_nonfinite=len(multiplicities),
        bootstrap_partial_sites=0,
        point_missing_sites=len(required_sites) if fixed_population else 0,
    )
    if frame.empty:
        return empty
    frame["year"] = pd.to_datetime(frame.cutoff_utc, utc=True).dt.year
    storms = (
        frame.groupby(["gauge", "physical_river", "storm_id", "year"], sort=True)
        .difference.mean()
        .reset_index()
    )
    sites = (
        required_sites
        if fixed_population
        else storms[["gauge", "physical_river"]].drop_duplicates().sort_values("gauge")
    )
    numerator, denominator = [], []
    for site in sites.gauge:
        local = storms[storms.gauge.eq(site)]
        totals = local.groupby("year").difference.agg(["sum", "count"]).reindex(years, fill_value=0)
        numerator.append(totals["sum"].to_numpy())
        denominator.append(totals["count"].to_numpy())
    num, den = np.array(numerator), np.array(denominator)
    counts = np.vstack([np.ones(len(years)), multiplicities])
    den = counts @ den.T
    values = np.divide(
        counts @ num.T, den, out=np.full_like(den, np.nan, dtype=float), where=den > 0
    )
    complete = (den > 0).all(1)
    partial = (den > 0).any(1) & ~complete
    if transfer:
        grouped = []
        for river in sites.physical_river.unique():
            block = values[:, sites.physical_river.eq(river)]
            count = np.isfinite(block).sum(1)
            grouped.append(
                np.divide(
                    np.nansum(block, axis=1),
                    count,
                    out=np.full(len(values), np.nan),
                    where=count > 0,
                )
            )
        values = np.column_stack(grouped)
    count = np.isfinite(values).sum(1)
    combined = np.divide(
        np.nansum(values, axis=1), count, out=np.full(len(values), np.nan), where=count > 0
    )
    if fixed_population:
        combined[~complete] = np.nan
    valid = combined[1:][np.isfinite(combined[1:])]
    interval = np.quantile(valid, [0.025, 0.975]) if len(valid) else [np.nan, np.nan]
    return dict(
        estimate=float(combined[0]),
        lower=float(interval[0]),
        upper=float(interval[1]),
        assessments=len(frame),
        storms=storms.storm_id.nunique(),
        sites=len(sites),
        years=storms.year.nunique(),
        bootstrap_nonfinite=int((~np.isfinite(combined[1:])).sum()),
        bootstrap_partial_sites=int(partial[1:].sum()),
        point_missing_sites=int((den[0] == 0).sum()),
    )


def verify_losses(cases, predictions, saved_scores):
    """Independent point-loss recomputation, complete census and method alignment."""
    assert cases.assessment_id.is_unique
    assert len(cases) == 481 * 8 * 4, "Expected the complete primary scenario census"
    observed = predictions["observed"]
    assert observed.shape == (len(cases), 24)
    checked = 0
    for method in predictions:
        if method == "observed":
            continue
        p = predictions[method]
        assert p.shape == observed.shape
        assert (p[np.isfinite(p)] >= 0).all(), "Negative discharge prediction"
        expected = np.where(
            np.isfinite(p).all(1) & np.isfinite(observed).all(1),
            np.abs(p - observed).mean(1),
            np.nan,
        )
        frame = (
            saved_scores[saved_scores.method.eq(method)]
            .set_index("assessment_id")
            .reindex(cases.assessment_id)
        )
        assert len(frame) == len(cases)
        np.testing.assert_allclose(
            expected, frame.mae.to_numpy(), rtol=1e-11, atol=1e-12, equal_nan=True
        )
        checked += int(np.isfinite(expected).sum())
    return checked
