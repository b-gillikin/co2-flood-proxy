"""Event definitions for the time-stratified case-crossover study.

These helpers implement protocol draft 0.9 §3-§5: rating-era thresholds,
adjacent-hour crossings, onset-only censoring, 72-hour single linkage, at-risk
hours and time strata. They read timestamps, flags and discharge ranks only.
Nothing here reads a signal or estimates an association.

Admissibility is decided at ingest and passed in as a mask. An inadmissible
hour cannot contribute to an exact crossing or be at risk, but its value still
counts as above or below the threshold, so a record that resumes above p99
after a gap starts a censored episode rather than vanishing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

WARM_MONTHS = frozenset(range(5, 11))
HOUR = pd.Timedelta(hours=1)


def hourly_presence(source_mask):
    """All four trailing quarter-hours; the source clock is deliberately not called UTC."""
    if source_mask.index.has_duplicates or not source_mask.index.is_monotonic_increasing:
        raise ValueError("Source timestamps must be sorted and unique")
    expected = pd.date_range(source_mask.index[0], source_mask.index[-1], freq="15min")
    if not source_mask.index.equals(expected):
        raise ValueError("Presence masks require a complete quarter-hour grid")
    complete = source_mask.rolling(4, min_periods=4).sum().eq(4)
    return complete.loc[complete.index.minute == 0]


def assign_eras(index, eras):
    """Label each hour with the rating era whose [valid_from, valid_to) interval holds it.

    `eras` needs `era_id`, `valid_from_utc` and `valid_to_utc`; an empty
    `valid_to_utc` means the era is still current. Hours outside every era get
    no label, and overlapping eras are rejected.
    """
    index = pd.DatetimeIndex(index)
    start = pd.to_datetime(eras.valid_from_utc, utc=True)
    end = pd.to_datetime(eras.valid_to_utc, utc=True).fillna(pd.Timestamp.max.tz_localize("UTC"))
    order = np.argsort(start.to_numpy())
    if (start.iloc[order].to_numpy()[1:] < end.iloc[order].to_numpy()[:-1]).any():
        raise ValueError("Rating eras overlap")
    labels = pd.Series(pd.NA, index=index, dtype="string")
    for era_id, lower, upper in zip(eras.era_id.astype(str), start, end, strict=True):
        labels[(index >= lower) & (index < upper)] = era_id
    return labels


def rating_domain_admissible(series, eras, era_table):
    """True where an observed value lies inside its era's valid rating domain.

    `era_table` gives `domain_min_m3s` and `domain_max_m3s` per `era_id`; an
    empty bound is unbounded. Hours without an era are inadmissible. This is
    the single place where protocol §3's rating-domain rule is applied.
    """
    table = era_table.set_index(era_table.era_id.astype(str))
    labels = pd.Series(eras, index=series.index).astype("string")
    lower = labels.map(table.domain_min_m3s).astype(float).fillna(-np.inf)
    upper = labels.map(table.domain_max_m3s).astype(float).fillna(np.inf)
    return series.notna() & labels.notna() & series.ge(lower) & series.le(upper)


def era_thresholds(series, eras=None, quantile=0.99):
    """Return each era's p99 and the hourly threshold series it implies.

    Every observed value in the era is ranked, including values outside the
    rating domain: their magnitude is uncertain but their rank is not, so the
    quantile needs them. Documented failures must already be missing.
    """
    if eras is None:
        eras = pd.Series("all", index=series.index, dtype="string")
    per_era = series.groupby(eras.astype("string"), dropna=True).quantile(quantile)
    hourly = eras.astype("string").map(per_era).astype(float)
    return per_era, hourly


def _aligned(series, threshold, admissible, eras):
    """Shared classification of every hour relative to its own era threshold."""
    index = series.index
    threshold = (
        threshold.reindex(index).astype(float)
        if isinstance(threshold, pd.Series)
        else pd.Series(float(threshold), index=index)
    )
    known = series.notna() & threshold.notna()
    admissible = (
        known
        if admissible is None
        else known & pd.Series(admissible, index=index).fillna(False).astype(bool)
    )
    eras = (
        pd.Series("all", index=index, dtype="string")
        if eras is None
        else pd.Series(eras, index=index).astype("string")
    )
    above = known & series.gt(threshold)
    elapsed = index.to_series().diff()
    adjacent = (
        elapsed.eq(HOUR).to_numpy()
        & eras.eq(eras.shift(1)).fillna(False).to_numpy()
        & known.shift(1, fill_value=False).to_numpy()
    )
    adjacent = pd.Series(adjacent, index=index)
    return known, admissible, above, adjacent


def crossing_flags(series, threshold, admissible=None, eras=None):
    """Classify hours as exact upward crossings or unobserved entries above threshold.

    An exact crossing moves from at or below to above the threshold between
    adjacent, admissible hours of the same rating era. An unobserved entry is
    any other hour that is above the threshold while its predecessor is not
    known to be above it in the same era: after a gap, at an era boundary, or
    where either hour is inadmissible. Such an entry starts a censored episode.
    """
    known, admissible, above, adjacent = _aligned(series, threshold, admissible, eras)
    previous_above = above.shift(1, fill_value=False)
    previous_admissible = admissible.shift(1, fill_value=False)
    exact = above & ~previous_above & adjacent & admissible & previous_admissible
    continuing = above & previous_above & adjacent
    entry = above & ~exact & ~continuing
    return pd.DataFrame({"exact": exact, "entry": entry})


def episode_table(series, threshold, merge_hours=72, admissible=None, eras=None):
    """Join crossings by unbounded single linkage and mark censored onsets.

    Consecutive crossings at most `merge_hours` apart belong to one episode.
    The episode onset is its first crossing; the onset is censored when that
    crossing is an unobserved entry rather than an exact crossing.
    """
    flags = crossing_flags(series, threshold, admissible, eras)
    crossings = flags.loc[flags.exact | flags.entry]
    columns = [
        "onset_utc",
        "last_crossing_utc",
        "n_crossings",
        "chain_span_hours",
        "onset_censored",
    ]
    if crossings.empty:
        return pd.DataFrame(columns=columns)

    times = crossings.index.to_series()
    new_episode = times.diff().gt(pd.Timedelta(hours=merge_hours))
    new_episode.iloc[0] = True
    episode = new_episode.cumsum()
    grouped = times.groupby(episode.to_numpy())
    first = grouped.min()
    last = grouped.max()
    table = pd.DataFrame(
        {
            "onset_utc": first.to_numpy(),
            "last_crossing_utc": last.to_numpy(),
            "n_crossings": grouped.size().to_numpy(),
            "chain_span_hours": ((last - first) / HOUR).to_numpy(),
            "onset_censored": crossings.entry.loc[first.to_numpy()].to_numpy(),
        }
    )
    return table[columns]


def episode_onsets(series, threshold, merge_hours=72, admissible=None, eras=None):
    """Return uncensored episode onsets: the onsets eligible for estimation."""
    episodes = episode_table(series, threshold, merge_hours, admissible, eras)
    return pd.DatetimeIndex(episodes.onset_utc[~episodes.onset_censored.astype(bool)])


def at_risk_hours(series, threshold, admissible=None, eras=None, window_hours=72):
    """Return the at-risk indicator and onset outcome for every hour (protocol §5).

    Hour t is at risk when t and t-1 are adjacent, admissible hours of one
    rating era, flow at t-1 is at or below the threshold, and no crossing,
    exact or unobserved, occurred in the preceding `window_hours` hours. This
    is the exact complement of the merge rule in `episode_table`, so an
    at-risk hour with an exact crossing is always an uncensored episode onset.
    """
    index = series.index
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError("At-risk hours need a sorted, unique index")
    if len(index) > 1 and not index.to_series().diff().iloc[1:].eq(HOUR).all():
        raise ValueError("At-risk hours need a complete hourly grid")
    known, admissible, above, adjacent = _aligned(series, threshold, admissible, eras)
    flags = crossing_flags(series, threshold, admissible, eras)
    crossed = (flags.exact | flags.entry).astype(int)
    recent = crossed.shift(1, fill_value=0).rolling(window_hours, min_periods=1).sum().gt(0)
    previous_below = known.shift(1, fill_value=False) & ~above.shift(1, fill_value=False)
    at_risk = (
        adjacent & admissible & admissible.shift(1, fill_value=False) & previous_below & ~recent
    )
    onset = at_risk & flags.exact
    return pd.DataFrame({"at_risk": at_risk, "onset": onset})


def warm_season(index):
    """True for May-October, the protocol's warm season."""
    return pd.Series(pd.DatetimeIndex(index).month.isin(WARM_MONTHS), index=index)


def stratum_labels(index, watercourse):
    """Watercourse x calendar year x calendar month x hour-of-day strata (UTC)."""
    index = pd.DatetimeIndex(index)
    labels = (
        f"{watercourse}|"
        + index.strftime("%Y-%m").astype(str)
        + "|"
        + index.strftime("%H").astype(str)
    )
    return pd.Series(labels, index=index, dtype="string")


def cluster_regional_storms(events, onset_col="onset_utc", max_gap_hours=72):
    """Assign chronologically adjacent watercourse events to regional storms."""
    if events.empty:
        return events.assign(storm_id=pd.Series(dtype="string"))
    out = events.sort_values(onset_col).reset_index(drop=True).copy()
    gap = out[onset_col].diff().gt(pd.Timedelta(hours=max_gap_hours))
    gap.iloc[0] = True
    number = gap.cumsum().astype(int)
    out["storm_id"] = number.map(lambda value: f"storm_{value:04d}")
    return out


def storm_table(storms, onset_col="onset_utc", censored_col="onset_censored"):
    """One row per regional storm: first onset, season and estimable onsets.

    A storm's season is the season of its first onset. A storm counts toward
    the information floors only if at least one of its onsets is uncensored.
    """
    columns = ["storm_id", "first_onset_utc", "warm_season", "n_onsets", "n_uncensored"]
    if storms.empty:
        return pd.DataFrame(columns=columns)
    censored = (
        storms[censored_col].fillna(True).astype(bool)
        if censored_col in storms
        else pd.Series(False, index=storms.index)
    )
    grouped = storms.assign(uncensored=~censored).groupby("storm_id", sort=True)
    table = grouped.agg(
        first_onset_utc=(onset_col, "min"),
        n_onsets=(onset_col, "size"),
        n_uncensored=("uncensored", "sum"),
    ).reset_index()
    table["warm_season"] = table.first_onset_utc.dt.month.isin(WARM_MONTHS)
    return table[columns]


def stage_onsets(stage, eras, thresholds, merge_hours=72):
    """Candidate stage onsets within verified datum or sensor eras (conditional, §3).

    Thresholds are supplied from the valid rating curve, never optimised here.
    Unknown eras, missing hours and era transitions cannot create exact onsets.
    """
    if not stage.index.equals(eras.index) or stage.index.has_duplicates:
        raise ValueError("Stage and era indices must be aligned and unique")
    if not stage.index.is_monotonic_increasing:
        raise ValueError("Stage must be sorted")
    if stage.index.tz is None:
        raise ValueError("Stage onset analysis requires a resolved timezone")
    if not all(np.isfinite(value) for value in thresholds.values()):
        raise ValueError("Finite stage threshold required")
    hourly = eras.astype("string").map(thresholds).astype(float)
    episodes = episode_table(stage, hourly, merge_hours, eras=eras)
    return episodes.loc[~episodes.onset_censored.astype(bool)].reset_index(drop=True)
