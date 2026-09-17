"""Blinded design experiments: source masks and synthetic contrasts only."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd


def distances_km(latitude, longitude):
    lat, lon = np.radians(latitude), np.radians(longitude)
    a = np.sin((lat[:, None] - lat) / 2) ** 2
    a += np.cos(lat[:, None]) * np.cos(lat) * np.sin((lon[:, None] - lon) / 2) ** 2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def spatial_subset(distance, n):
    """Deterministic geometry-only farthest-point subset, never chosen on effects."""
    if not 2 <= n <= len(distance):
        raise ValueError("Subset must contain 2..N existing sites")
    first, second = np.unravel_index(np.argmax(distance), distance.shape)
    chosen = [int(first), int(second)]
    while len(chosen) < n:
        nearest = distance[:, chosen].min(axis=1)
        nearest[chosen] = -1
        chosen.append(int(np.argmax(nearest)))
    return np.array(chosen)


def hourly_presence(source_mask):
    """All four trailing quarter-hours; source clock is deliberately not called UTC."""
    if source_mask.index.has_duplicates or not source_mask.index.is_monotonic_increasing:
        raise ValueError("Source timestamps must be sorted and unique")
    expected = pd.date_range(source_mask.index[0], source_mask.index[-1], freq="15min")
    if not source_mask.index.equals(expected):
        raise ValueError("Presence masks require a complete quarter-hour grid")
    complete = source_mask.rolling(4, min_periods=4).sum().eq(4)
    return complete.loc[complete.index.minute == 0]


def availability_for_synthetic_storms(hourly, anchors, rng, participation=0.65):
    """Apply real flow presence to fictitious storms and matched control windows.

    This is an upper bound: no rainfall/weather masks, source QA or real quiet
    thresholds are available. All anchors are simulated, not detected floods.
    """
    preceding = hourly.shift(1).rolling(13, min_periods=13).sum().eq(13)
    receiver = hourly & hourly.shift(1, fill_value=False)
    event_available = receiver.loc[anchors].to_numpy() & (
        rng.random((len(anchors), hourly.shape[1])) < participation
    )
    donor_available = preceding.loc[anchors].to_numpy()
    control_available = np.zeros_like(donor_available)
    # Every hypothetical regional storm excludes controls for all pairs.
    anchor_ns = anchors.as_unit("ns").asi8
    for i, anchor in enumerate(anchors):
        candidates = preceding.loc[
            (preceding.index.month == anchor.month) & (preceding.index.hour == anchor.hour)
        ]
        ns = candidates.index.as_unit("ns").asi8
        far = np.abs(ns[:, None] - anchor_ns).min(axis=1) > pd.Timedelta(days=7).value
        candidates = candidates.loc[far]
        order = np.argsort(
            np.abs(candidates.index.as_unit("ns").asi8 - anchor.value), kind="stable"
        )
        # Up to five available controls per donor, minimum three. Actual
        # receiver quietness requires a future, locked empirical analysis.
        control_available[i] = candidates.iloc[order].sum(axis=0).to_numpy() >= 3
    return event_available[:, :, None] & (donor_available & control_available)[:, None, :]


def median_estimates(values, x, minimum_pairs=5):
    """Fixed network estimands; never silently drop a poorly observed pair."""
    n = values.shape[-1]
    off = ~np.eye(n, dtype=bool)
    count = np.isfinite(values).sum(axis=-3)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(values, axis=-3)
    xx = x[off]
    xx = xx - xx.mean()
    slope = (
        (med[..., off] @ xx) / np.dot(xx, xx)
        if np.dot(xx, xx) > 0
        else np.full(med.shape[:-2], np.nan)
    )
    slope = np.where((count[..., off] >= minimum_pairs).all(axis=-1), slope, np.nan)
    local = med.diagonal(axis1=-2, axis2=-1).mean(axis=-1)
    local = np.where(
        (count.diagonal(axis1=-2, axis2=-1) >= minimum_pairs).all(axis=-1), local, np.nan
    )
    return np.stack([local, slope], axis=-1)


def simulate_once(
    distance, available, slope, rho, rng, bootstrap=199, minimum_pairs=5, extreme_failure=False
):
    """Storm bootstrap preserves receiver, donor and pair dependence jointly."""
    if not 0 <= rho < 1 or bootstrap < 20:
        raise ValueError("Invalid dependence or bootstrap setting")
    storms, n, _ = available.shape
    x = np.log1p(distance)
    truth = 0.5 + slope * x
    common = rng.normal(size=(storms, 1, 1))
    receiver = rng.normal(size=(storms, n, 1))
    donor = rng.normal(size=(storms, 1, n))
    noise = np.sqrt(rho) * common + np.sqrt((1 - rho) / 3) * (
        receiver + donor + rng.normal(size=(storms, n, n))
    )
    mask = available.copy()
    if extreme_failure:
        # A declared MNAR stress test, not an estimate of real flood failures.
        mask &= ~((common > 1) & (rng.random(mask.shape) < 0.65))
    observed = np.where(mask, truth[None, :, :] + noise, np.nan)
    estimate = median_estimates(observed, x, minimum_pairs)
    if not np.isfinite(estimate).any():
        return estimate, np.full((2, 2), np.nan), np.zeros(2)
    indices = rng.integers(0, storms, size=(bootstrap, storms))
    draws = median_estimates(observed[indices], x, minimum_pairs)
    valid = np.isfinite(draws)
    # Missing bootstrap samples are reported, not silently accepted as a CI.
    ci = np.full((2, 2), np.nan)
    for k in range(2):
        if np.isfinite(estimate[k]) and valid[:, k].mean() >= 0.95:
            ci[:, k] = np.quantile(draws[valid[:, k], k], [0.025, 0.975])
    return estimate, ci, valid.mean(axis=0)


def stage_onsets(stage, eras, thresholds, merge_hours=72):
    """Candidate stage target: crossings within one verified datum/sensor era.

    Thresholds are provided, not optimized here. Unknown eras, missing hours,
    and era transitions never create exact onsets. This helper reads no files.
    """
    from src.event_study import episode_table

    if not stage.index.equals(eras.index) or stage.index.has_duplicates:
        raise ValueError("Stage and era indices must be aligned and unique")
    if not stage.index.is_monotonic_increasing:
        raise ValueError("Stage must be sorted")
    if stage.index.tz is None:
        raise ValueError("Stage onset analysis requires a resolved timezone")
    rows = []
    for era, threshold in thresholds.items():
        if not np.isfinite(threshold):
            raise ValueError("Finite stage threshold required")
        masked = stage.where(eras.eq(era))
        found = episode_table(masked, threshold, merge_hours=merge_hours)
        found["era"] = era
        rows.append(found)
    if not rows:
        return pd.DataFrame(
            columns=["onset_utc", "last_crossing_utc", "n_crossings", "chain_span_hours", "era"]
        )
    return pd.concat(rows, ignore_index=True).sort_values("onset_utc").reset_index(drop=True)
