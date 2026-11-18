"""Fixed-prediction, synchronized uncertainty for the DISE multiyear census."""

from __future__ import annotations

import numpy as np
import pandas as pd

CONTRASTS = {
    "alpha_added": ("native_rmse__H+A+E", "native_rmse__H+A"),
    "alpha_substitute": ("native_rmse__H+E", "native_rmse__H+A"),
    "combined_vs_raw": ("native_rmse__H+A+E", "q_model"),
    "conventional_vs_raw": ("native_rmse__H+A", "q_model"),
    "dynamic_vs_raw": ("native_rmse__H", "q_model"),
    "article_alpha_added": ("article_faithful__H+A+E", "article_faithful__H+A"),
    "donor_fdc_vs_raw": ("donor_fdc", "q_model"),
    "local_fdc_vs_raw": ("local_fdc", "q_model"),
}


def joint_multiplicities(calendar, draws, seed, block_days=None):
    """One multiplicity per date shared by all gauges and models, never row draws.

    None resamples entire years. Otherwise circular moving blocks are drawn
    within each fixed year, retaining its exact calendar length.
    """
    dates = pd.DatetimeIndex(calendar)
    if dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError("Unique ordered common calendar required")
    years = sorted(set(dates.year))
    rng = np.random.default_rng(seed)
    out = np.zeros((draws, len(dates)), dtype=np.int16)
    if block_days is None:
        if len(years) < 2:
            raise ValueError("Year uncertainty needs at least two years")
        counts = rng.multinomial(len(years), np.full(len(years), 1 / len(years)), size=draws)
        for k, year in enumerate(years):
            out[:, dates.year == year] = counts[:, k, None]
    else:
        if block_days < 1:
            raise ValueError("Positive block length required")
        for year in years:
            positions = np.flatnonzero(dates.year == year)
            n = len(positions)
            expected = pd.date_range(f"{year}-01-01", f"{year}-12-31", tz=dates.tz)
            if not dates[positions].equals(expected):
                raise ValueError("Moving blocks need the full calendar, including unobserved dates")
            for draw in range(draws):
                starts = rng.integers(0, n, size=int(np.ceil(n / block_days)))
                selected = ((starts[:, None] + np.arange(block_days)) % n).ravel()[:n]
                out[draw, positions] = np.bincount(selected, minlength=n)
    return out


def conditions(p):
    high = p.high_water.fillna(False).to_numpy(bool)
    return {
        "all_days": np.ones(len(p), bool),
        "high_water": high,
        "clean_high_water": high & p.clean_verification.fillna(False).to_numpy(bool),
    }


def gauge_resamples(frame, arms, calendar, multiplicities):
    """Exact sufficient sums; recompute each gauge denominator in every draw.

    Return counts and (MAE, MSE, signed bias) by draw/gauge/arm. Nonfinite
    predictions propagate as undefined only when their dates are sampled.
    """
    gauges = sorted(frame.gauge.unique())
    dates = pd.DatetimeIndex(calendar)
    gi = pd.Index(gauges).get_indexer(frame.gauge)
    di = dates.get_indexer(pd.to_datetime(frame.day))
    if (di < 0).any() or frame.duplicated(["gauge", "day"]).any():
        raise ValueError("Out-of-calendar or repeated verification rows")
    width = 1 + len(arms) * 4
    sums = np.zeros((len(dates), len(gauges), width), dtype=float)
    sums[di, gi, 0] = 1
    obs = frame.q_observed.to_numpy(float)
    for k, arm in enumerate(arms):
        err = frame[arm].to_numpy(float) - obs
        good = np.isfinite(err)
        safe = np.where(good, err, 0)
        sums[di, gi, 1 + 4 * k : 5 + 4 * k] = np.column_stack([np.abs(safe), safe**2, safe, ~good])
    totals = (np.asarray(multiplicities, float) @ sums.reshape(len(dates), -1)).reshape(
        len(multiplicities), len(gauges), width
    )
    counts = totals[:, :, 0]
    values = np.full((len(multiplicities), len(gauges), len(arms), 3), np.nan)
    for k in range(len(arms)):
        valid = (counts > 0) & (totals[:, :, 4 + 4 * k] == 0)
        np.divide(
            totals[:, :, 1 + 4 * k : 4 + 4 * k],
            counts[:, :, None],
            out=values[:, :, k],
            where=valid[:, :, None],
        )
    return gauges, counts, values


def balanced_resamples(gauges, counts, values, expected):
    """Fixed-population group/gauge balancing; no accidental population changes."""
    if not expected:
        return np.full((len(counts), values.shape[2], 3), np.nan), len(counts)
    positions = pd.Index(gauges).get_indexer(list(expected))
    if (positions < 0).any():
        return np.full((len(counts), values.shape[2], 3), np.nan), len(counts)
    missing = (counts[:, positions] == 0).any(axis=1)
    groups = sorted(set(expected.values()))
    means = []
    for group in groups:
        indices = [gauges.index(g) for g, river in expected.items() if river == group]
        means.append(values[:, indices].mean(axis=1))
    answer = np.stack(means).mean(axis=0)
    answer[missing] = np.nan
    answer[:, :, 1] = np.sqrt(answer[:, :, 1])
    return answer, int(missing.sum())


def contrast_record(candidate, reference):
    """Positive reduction means improvement; intervals use paired differences."""
    if candidate is None or reference is None or not np.isfinite([candidate, reference]).all():
        return dict(delta=None, reduction_pct=None)
    return dict(
        delta=float(candidate - reference),
        reduction_pct=float(100 * (1 - candidate / reference)) if reference > 0 else None,
    )


def regional_episodes(frame, gap_days):
    """Descriptive per-river episodes across calendar years, independent of model errors."""
    records = []
    for river, p in frame.groupby("river_group"):
        dates = pd.DatetimeIndex(sorted(p.loc[p.high_water.fillna(False), "day"].unique()))
        if not len(dates):
            continue
        groups = np.r_[0, np.cumsum((dates[1:] - dates[:-1]) > pd.Timedelta(days=gap_days))]
        for _, part in pd.Series(dates).groupby(groups):
            records.append(
                dict(
                    episode=f"{river}|{part.iloc[0].date()}",
                    river_group=river,
                    start=part.iloc[0],
                    end=part.iloc[-1],
                    high_water_dates=len(part),
                )
            )
    return records
