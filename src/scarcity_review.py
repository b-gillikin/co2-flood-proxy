"""Paired scarcity estimands: fixed site mass, whole years, coherent mask means."""

from __future__ import annotations

import numpy as np

from src.analogue_bootstrap import draw_counts


def joint_summary(values, years, *, random_masks, draws=999, seed=20261028):
    """R x gauge x storm differences; equal sites, valid case-mask pairs per site.

    Resample years with all their storms/sites intact. For random designs also
    resample R entire mask IDs then average, preserving their dependence across
    sites and issues. Enumerated phases/network subsets are averaged exactly.
    No independent replication of masks is counted as additional storm evidence.
    """
    x = np.asarray(values, float)
    years = np.asarray(years)
    if x.ndim != 3 or x.shape[-1] != len(years):
        raise ValueError("Expected replication x gauge x shared storm calendar")
    valid = np.isfinite(x)
    num = np.where(valid, x, 0).sum(axis=(0, 2))
    den = valid.sum(axis=(0, 2))
    cells = den > 0
    estimate = float(np.mean(num[cells] / den[cells])) if cells.any() else np.nan
    universe = np.unique(years)
    observed_years = sum(valid[:, :, np.asarray(years) == year].any() for year in universe)
    result = dict(
        estimate=estimate,
        lower=np.nan,
        upper=np.nan,
        case_storms=int(valid.any(axis=(0, 1)).sum()),
        gauge_storms=int(valid.any(axis=0).sum()),
        valid_case_mask_pairs=int(valid.sum()),
        gauges=int(cells.sum()),
        years=int(observed_years),
        year_universe=len(universe),
        replicas=len(x),
        random_masks=bool(random_masks),
        bootstrap_draws=draws,
        finite_draws=0,
    )
    if not cells.any() or observed_years < 2 or not draws:
        return result
    yc = draw_counts(len(universe), draws, seed)
    mc = draw_counts(len(x), draws, seed + 91) / len(x) if random_masks else None
    boot = np.zeros((draws, cells.sum()))
    for index, gi in enumerate(np.flatnonzero(cells)):
        yn = np.stack(
            [
                np.where(valid[:, gi, years == y], x[:, gi, years == y], 0).sum(axis=1)
                for y in universe
            ],
            axis=1,
        )
        yd = np.stack([valid[:, gi, years == y].sum(axis=1) for y in universe], axis=1)
        if random_masks:
            bn = ((yc @ yn.T) * mc).sum(axis=1)
            bd = ((yc @ yd.T) * mc).sum(axis=1)
        else:
            bn = yc @ yn.mean(axis=0)
            bd = yc @ yd.mean(axis=0)
        boot[:, index] = np.divide(bn, bd, out=np.full(draws, np.nan), where=bd > 0)
    b = boot.mean(axis=1)
    result["finite_draws"] = int(np.isfinite(b).sum())
    if np.isfinite(b).all():
        result["lower"], result["upper"] = map(float, np.quantile(b, [0.025, 0.975]))
    return result


def severity_labels(outcomes, thresholds, current):
    """Hindsight evaluation only; -1 denotes undefined, never normal flow."""
    known = np.isfinite(outcomes).all(axis=-1) & np.isfinite(thresholds).all(axis=-1)
    high = np.where(known, (outcomes >= thresholds).any(axis=-1), -1).astype("int8")
    change = outcomes[..., -1] - current
    phase = np.full(high.shape, "undefined", dtype="U24")
    phase[(high == 0)] = "not_high_water"
    phase[(high == 1) & np.isfinite(change) & (change > 0)] = "rising_high_water"
    phase[(high == 1) & np.isfinite(change) & (change < 0)] = "falling_high_water"
    phase[(high == 1) & np.isfinite(change) & (change == 0)] = "level_high_water"
    return high, phase
