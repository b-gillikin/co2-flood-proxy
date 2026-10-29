"""Frozen conventional point references and source-watercourse donor exclusion."""

from __future__ import annotations

import numpy as np

from src.scarcity import (
    combine_ground,
    partial_history_distances,
    stable_members,
    standard_distances,
)


def keep_channels(target, scenario, river_groups=None, excluded=()):
    keep = np.ones((1, 10, 72), bool)
    if scenario == "local_q_absent":
        keep[:, target] = False
    elif scenario == "all_q_absent":
        keep[:] = False
    elif scenario != "rich_basin":
        raise ValueError("Unknown primary scenario")
    if river_groups is not None:
        for j, group in enumerate(river_groups):
            if group in excluded:
                keep[:, j] = False
    return keep


def same_gauge_reference(bank, qi, gi, offset, scenario, fixed_prior=None):
    key = f"{offset}_0"
    allowed = bank[f"prior_{key}"][qi] & bank[f"outcome_valid_{offset}"][:, gi]
    if fixed_prior is not None:
        allowed &= fixed_prior
    qmean = bank[f"q_mean_{key}"][qi]
    qvar = bank[f"q_pairvar_{key}"][qi]
    rmean = bank[f"rain_mean_{key}"][qi, gi]
    rvar = bank[f"rain_var_{key}"][qi, gi]
    donor = bank[f"donor_q_{offset}"]
    rain = bank[f"rain_{offset}_1_0"]
    # A fixed-year donor diagnostic also freezes the input normalization archive.
    if fixed_prior is not None:
        stats = bank[f"prior_{key}"][qi] & fixed_prior
        if stats.any():
            with np.errstate(invalid="ignore", divide="ignore"):
                qmean = finite_moments(donor[stats])[0]
                qvar = 2 * finite_moments(donor[stats])[1]
                rmean, rvar = finite_moments(rain[stats, gi])
        else:
            allowed[:] = False
    q = bank[f"q_{offset}"][qi]
    keep = keep_channels(gi, scenario)
    distance, support = partial_history_distances(q, donor, qmean, qvar, keep)
    rain_distance = standard_distances(rain[qi, gi], rain[:, gi], rmean, rvar)
    ranked = combine_ground(distance, support, rain_distance, gi)
    members = stable_members(ranked, allowed, limit=5)[0]
    members = members[members >= 0]
    outcome = bank[f"outcome_{offset}"][:, gi]
    if len(members):
        return outcome[members].mean(0), np.median(outcome[members], axis=0), members, "analogue"
    measured = np.where(keep[0, gi], q[gi], np.nan)
    if np.isfinite(measured).any():
        value = measured[np.flatnonzero(np.isfinite(measured))[-1]]
        return np.full(24, value), np.full(24, value), members, "persistence"
    if allowed.any():
        return outcome[allowed].mean(0), np.median(outcome[allowed], axis=0), members, "generic"
    return np.full(24, np.nan), np.full(24, np.nan), members, "unavailable"


def finite_moments(values):
    finite = np.isfinite(values)
    n = finite.sum(0)
    mean = np.divide(
        np.where(finite, values, 0).sum(0), n, out=np.zeros(values.shape[1:]), where=n > 0
    )
    variance = np.divide(
        np.where(finite, (values - mean) ** 2, 0).sum(0), n, out=np.zeros_like(mean), where=n > 0
    )
    return mean, variance


def transfer_reference(bank, qi, gi, offset, scenario, groups, areas, excluded, fixed_prior=None):
    """One member per regional storm; all held-watercourse labels excluded.

    Global source-channel histories compare storms; own-catchment rain compares
    query/donor sites. Discharge trajectories transfer in mm/h, never p99 units.
    """
    prior = bank[f"prior_{offset}_0"][qi].copy()
    if fixed_prior is not None:
        prior &= np.asarray(fixed_prior, dtype=bool)
    eligible_gauges = np.array([group not in excluded for group in groups[:8]])
    outcome_ok = bank[f"outcome_valid_{offset}"] & prior[:, None] & eligible_gauges[None, :]
    qmean = bank[f"q_mean_{offset}_0"][qi]
    qvar = bank[f"q_pairvar_{offset}_0"][qi]
    if fixed_prior is not None and prior.any():
        qmean, variance = finite_moments(bank[f"donor_q_{offset}"][prior])
        qvar = 2 * variance
    q = bank[f"q_{offset}"][qi]
    keep = keep_channels(gi, scenario, groups, excluded)
    qdist, support = partial_history_distances(q, bank[f"donor_q_{offset}"], qmean, qvar, keep)
    rains = bank[f"rain_{offset}_1_0"]
    own = rains.reshape(-1, 7)
    rain_stats = outcome_ok.reshape(-1)
    if not rain_stats.any():
        return np.full(24, np.nan), np.full(24, np.nan), []
    mean, var = finite_moments(own[rain_stats])
    rd = standard_distances(rains[qi, gi], own, mean, var).reshape(1, len(rains), 8)
    # Combine rain with identically masked network histories without weighting a
    # donor watercourse multiple times merely because it has several gauges.
    # combine_ground already includes one rain group. Recover its Q-group
    # sum and add one cross-site rain distance, never count rain twice.
    qonly = combine_ground(qdist, support, np.zeros((1, len(rains))), gi)[0]
    groups_present = 1 + sum(
        int(support[:, channels].any())
        for channels in [[gi], [j for j in range(8) if j != gi], [8, 9]]
    )
    score = rd[0] / groups_present + qonly[:, None]
    score = np.where(outcome_ok, score, np.inf)
    # Choose the closest eligible donor site per storm, then five distinct storms.
    dg = np.argmin(score, axis=1)
    dscore = score[np.arange(len(score)), dg]
    order = np.argsort(dscore, kind="stable")
    order = order[np.isfinite(dscore[order])][:5]
    members = [(int(i), int(dg[i])) for i in order]
    if not members:
        return np.full(24, np.nan), np.full(24, np.nan), []
    responses = np.stack([bank[f"outcome_{offset}"][i, j] * 3.6 / areas[j] for i, j in members])
    return responses.mean(0), np.median(responses, axis=0), members
