"""Paired, storm-aware review helpers for monitoring-loss comparisons."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analogue_bootstrap import draw_counts


def design_weights(frame):
    """Equal original gauge/issue-cell mass, equal cases within each cell."""
    sizes = frame.groupby(["gauge", "offset_h"])["case"].transform("size")
    return 1 / sizes.to_numpy(float)


def mean_estimate(frame, column):
    keep = frame[column].notna()
    f = frame.loc[keep]
    if f.empty:
        return np.nan
    return float(np.average(f[column], weights=design_weights(f)))


def paired_interval(frame, column, cluster, draws=999, seed=20261028, block_universe=None):
    """Intact paired block resampling; fixed original design weights.

    Same draw counts are shared by all endpoints with the same named blocks.
    Uncertainty is conditional on the held archive; masks are not independent N.
    """
    f = frame.loc[frame[column].notna()].copy()
    if f.empty:
        return dict(lower=np.nan, upper=np.nan, blocks=0, draws=0, finite_draws=0)
    w = design_weights(f)
    grouped = (
        pd.DataFrame(
            {"cluster": f[cluster].to_numpy(), "sum": f[column].to_numpy() * w, "weight": w}
        )
        .groupby("cluster", sort=True)
        .sum()
    )
    observed_blocks = len(grouped)
    if block_universe is not None:
        universe = pd.Index(block_universe)
        if not universe.is_unique or not grouped.index.isin(universe).all():
            raise ValueError("Unique shared blocks must include all observed blocks")
        grouped = grouped.reindex(universe, fill_value=0)
    n = len(grouped)
    if observed_blocks < 2:
        return dict(
            lower=np.nan,
            upper=np.nan,
            blocks=observed_blocks,
            universe_blocks=n,
            draws=0,
            finite_draws=0,
        )
    counts = draw_counts(n, draws, seed)
    denominator = counts @ grouped.weight.to_numpy()
    values = np.divide(
        counts @ grouped["sum"].to_numpy(),
        denominator,
        out=np.full(draws, np.nan),
        where=denominator > 0,
    )
    finite = np.isfinite(values)
    if not finite.all():
        return dict(
            lower=np.nan,
            upper=np.nan,
            blocks=observed_blocks,
            universe_blocks=n,
            draws=draws,
            finite_draws=int(finite.sum()),
        )
    lo, hi = np.quantile(values, [0.025, 0.975])
    return dict(
        lower=float(lo),
        upper=float(hi),
        blocks=observed_blocks,
        universe_blocks=n,
        draws=draws,
        finite_draws=draws,
    )


def keyed_pairs(frame, full):
    """Same cases/issues for a change in EO increment relative to zero delay."""
    return frame.merge(
        full, on=["case", "offset_h", "target_k"], how="inner", validate="one_to_one"
    )
