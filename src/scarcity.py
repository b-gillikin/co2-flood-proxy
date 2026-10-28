"""Transparent source masks, partial-history distances and finite ensembles.

Historical donor observations are projected to the query's retained coordinates.
No hidden query value, verification label or full-record quantile sets distances.
"""

from __future__ import annotations

import itertools

import numpy as np


def forward_hold(values):
    """Causal hold on the last axis; no backward fill of an unknown beginning."""
    x = np.asarray(values, float)
    index = np.arange(x.shape[-1])
    last = np.maximum.accumulate(np.where(np.isfinite(x), index, -1), axis=-1)
    result = np.take_along_axis(x, np.maximum(last, 0), axis=-1)
    return np.where(last >= 0, result, np.nan)


def mask_series(length, replicas, channels, fractions, *, seed, mean_run=None):
    """Continuous nested masks, sampled independently of source values.

    One shared uniform variate gives nested severities. The two-state chain has
    stationary missing probability p and mean missing-run length L. Inputs in
    this study satisfy attractiveness (p/L/(1-p) + 1/L <= 1).
    """
    p = np.asarray(fractions, float)
    if np.any((p <= 0) | (p >= 1)):
        raise ValueError("0/100% are explicit endpoints, not stochastic transitions")
    rng = np.random.default_rng(seed)
    shape = (len(p), replicas, channels, length)
    result = np.empty(shape, bool)
    if mean_run is None:
        # Chunked draws bound memory while retaining a coherent source timeline.
        for start in range(0, length, 2048):
            u = rng.random((replicas, channels, min(2048, length - start)))
            result[..., start : start + u.shape[-1]] = u[None] < p[:, None, None, None]
        return result
    up = 1.0 / mean_run
    down = p / ((1 - p) * mean_run)
    if np.any(down + up > 1 + 1e-12):
        raise ValueError("Fraction/run-length combination cannot use this nested coupling")
    state = rng.random((replicas, channels))[None] < p[:, None, None]
    for start in range(0, length, 2048):
        u = rng.random((min(2048, length - start), replicas, channels))
        for j in range(len(u)):
            probability = np.where(state, 1 - up, down[:, None, None])
            state = u[j][None] < probability
            result[..., start + j] = state
    return result


def unpack_at(packed, channel, positions):
    """Read selected source-time mask bits without unpacking a full timeline."""
    p = np.asarray(positions, int)
    if (p < 0).any() or (p // 8 >= packed.shape[-1]).any():
        raise ValueError("Requested source mask outside its recorded time axis")
    return ((packed[:, channel, p // 8] >> (7 - p % 8)) & 1).astype(bool)


def scenario_groups(config):
    """One-axis groups; replications never mean a smaller event sample."""
    groups = [dict(name="rich_basin", family="reference", replicas=1)]
    groups += [dict(name="rich_local", family="local", replicas=1)]
    groups += [
        dict(name=f"maas_{label}", family="maas", maas=mask, replicas=1)
        for label, mask in [("none", 0), ("sint_pieter", 1), ("venlo", 2)]
    ]
    for hours in config["sampling_hours"][1:]:
        groups.append(dict(name=f"density_{hours}h", family="density", hours=hours, replicas=1))
        groups.append(
            dict(name=f"schedule_{hours}h", family="schedule", hours=hours, replicas=hours)
        )
        groups.append(dict(name=f"rain_{hours}h", family="rain", hours=hours, replicas=hours))
    for pattern in ["scattered", *[f"block_{h}h" for h in config["block_mean_hours"]]]:
        for fraction in config["missing_fractions"][1:-1]:
            groups.append(
                dict(
                    name=f"{pattern}_{int(100 * fraction)}pct",
                    family="missing",
                    pattern=pattern,
                    fraction=fraction,
                    replicas=config["mask_replicas"],
                )
            )
    groups.append(dict(name="local_q_absent", family="local_absent", replicas=1))
    for count in config["network_retained"][1:]:
        sets = list(itertools.combinations(range(8), count))
        groups.append(
            dict(
                name=f"network_{count}",
                family="network",
                retained=count,
                subsets=sets,
                replicas=len(sets),
            )
        )
    groups += [
        dict(name="all_q_absent", family="all_absent", replicas=1),
        dict(name="rain_absent", family="rain_absent", replicas=1),
    ]
    groups += [
        dict(name=f"history_{years}y", family="history", years=years, replicas=1)
        for years in config["historical_caps_years"]
    ]
    if config.get("combined_profiles"):
        networks = list(itertools.combinations(range(8), 4))
        rng = np.random.default_rng(config["seed"] + 771)
        groups += [
            dict(
                name="network4_schedule6_no_maas",
                family="combined_schedule",
                replicas=len(networks) * 6,
                subsets=[s for s in networks for _ in range(6)],
                phases=list(range(6)) * len(networks),
                hours=6,
            ),
            dict(
                name="network4_block12_50pct_no_maas",
                family="combined_missing",
                replicas=config["mask_replicas"],
                subsets=[
                    networks[i] for i in rng.integers(len(networks), size=config["mask_replicas"])
                ],
                mask_name="block_12h_50pct",
            ),
        ]
    for name in config.get("donor_support_sensitivity", {}).get("groups", []):
        source = next(g for g in groups if g["name"] == name)
        groups.append(
            dict(
                source,
                name=name + "_measured",
                paired_with=name,
                mask_name=source.get("mask_name", name),
                measured_support=True,
            )
        )
    return groups


def partial_history_distances(query, donors, mean, pair_variance, keep, *, held=False):
    """R x donor x station squared distances and R x station support.

    Source donor gaps are causally held first; remaining unknown donor values
    use the earlier-archive coordinate mean. Query gaps remain absent unless
    the explicitly named forward-hold treatment is requested.
    """
    q = np.asarray(query, float)
    d = np.where(np.isfinite(donors), donors, mean[None])
    mask = np.asarray(keep, bool) & np.isfinite(q)[None]
    result = np.zeros((len(mask), len(d), q.shape[0]))
    support = np.zeros((len(mask), q.shape[0]), bool)
    for s in range(q.shape[0]):
        # Reuse unaltered peer channels across 100 local-mask realizations.
        unique, inverse = np.unique(mask[:, s], axis=0, return_inverse=True)
        if held:
            x = forward_hold(np.where(unique, q[s][None], np.nan))
            w = np.isfinite(x).astype(float)
            xx = np.nan_to_num(x)
            donor = d[:, s]
            numerator = (
                w @ (donor * donor).T - 2 * (xx * w) @ donor.T + (xx * xx * w).sum(axis=1)[:, None]
            )
        else:
            w = unique.astype(float)
            numerator = w @ ((d[:, s] - np.nan_to_num(q[s])[None]) ** 2).T
        denominator = w @ pair_variance[s]
        value = np.divide(
            numerator,
            denominator[:, None],
            out=np.zeros_like(numerator),
            where=denominator[:, None] > 1e-14,
        )
        result[:, :, s] = value[inverse]
        support[:, s] = (denominator > 1e-14)[inverse]
    return np.maximum(result, 0), support


def standard_distances(query, donors, mean, variance):
    """R x donor distances from available standardized rainfall/season fields."""
    q = np.atleast_2d(np.asarray(query, float))
    d = np.where(np.isfinite(donors), donors, mean)
    valid = np.isfinite(q) & (variance[None] > 1e-14)
    scale = np.where(variance > 1e-14, variance, 1)
    error = (np.nan_to_num(q)[:, None, :] - d[None]) ** 2 / scale[None, None]
    count = valid.sum(axis=1)
    result = (error * valid[:, None]).sum(axis=-1)
    return np.divide(
        result, 2 * count[:, None], out=np.zeros_like(result), where=count[:, None] > 0
    )


def coordinate_moments(prior, values):
    """Earlier-input means and unbiased variances, never query/outcome fitted."""
    x = np.asarray(values, float)
    shape = x.shape[1:]
    flat = x.reshape(len(x), -1)
    available = np.isfinite(flat)
    p = np.asarray(prior, float)
    count = p @ available.astype(float)
    finite = np.where(available, flat, 0)
    mean = np.divide(p @ finite, count, out=np.zeros_like(count), where=count > 0)
    second = np.divide(p @ (finite * finite), count, out=np.zeros_like(count), where=count > 0)
    variance = np.maximum(second - mean * mean, 0)
    variance = np.divide(variance * count, count - 1, out=np.zeros_like(variance), where=count > 1)
    return mean.reshape((len(prior), *shape)), variance.reshape((len(prior), *shape))


def rain_histories(raw, hours, positions, period=1, phase=0):
    """168h prefixes from completed reporting blocks; causal hold of current tail.

    Block means can be assigned to earlier hours within a completed block,
    because its endpoint is already observed at issue. Never access a later one.
    """
    import pandas as pd

    values = np.asarray(raw, float)
    rates = pd.DataFrame(values).rolling(period, min_periods=period).mean().to_numpy()
    positions = np.asarray(positions, int)
    index = positions[:, None] - 167 + np.arange(168)
    safe = np.clip(index, 0, len(values) - 1)
    endpoints = safe + ((phase - np.asarray(hours)[safe]) % period)
    latest = positions - ((np.asarray(hours)[positions] - phase) % period)
    endpoints = np.minimum(endpoints, latest[:, None])
    valid = (index >= 0) & (endpoints >= 0) & (endpoints <= positions[:, None])
    reconstructed = rates[np.clip(endpoints, 0, len(values) - 1)]
    reconstructed[~valid] = np.nan
    result = []
    for window in [6, 24, 72, 168]:
        x = reconstructed[:, -window:]
        result.append(np.where(np.isfinite(x).all(axis=1), np.nansum(x, axis=1), np.nan))
    x = reconstructed[:, -24:]
    result.append(np.where(np.isfinite(x).all(axis=1), np.max(np.nan_to_num(x), axis=1), np.nan))
    return np.stack(result, axis=-1), positions - latest


def scenario_keep(spec, positions, epoch_hours, packed, target, history=72):
    """Retained input coordinates at one issue, before natural missingness."""
    r = spec["replicas"]
    keep = np.ones((r, 10, history), bool)
    family = spec["family"]
    if family == "local":
        keep[:] = False
        keep[:, target] = True
    elif family == "maas":
        keep[:, 8] = bool(spec["maas"] & 1)
        keep[:, 9] = bool(spec["maas"] & 2)
    elif family == "density":
        keep[:, target] = (np.arange(history - 1, -1, -1) % spec["hours"]) == 0
    elif family == "schedule":
        keep[:, target] = epoch_hours[None] % spec["hours"] == np.arange(r)[:, None]
    elif family == "missing":
        keep[:, target] = ~unpack_at(packed, target, positions)
    elif family == "local_absent":
        keep[:, target] = False
    elif family == "network":
        keep[:, :8] = False
        for i, subset in enumerate(spec["subsets"]):
            keep[i, list(subset)] = True
    elif family == "all_absent":
        keep[:] = False
    elif family in ["combined_schedule", "combined_missing"]:
        keep[:] = False
        retained = (
            None
            if family == "combined_schedule"
            else [~unpack_at(packed, channel, positions) for channel in range(8)]
        )
        for i, subset in enumerate(spec["subsets"]):
            if family == "combined_schedule":
                mask = epoch_hours % spec["hours"] == spec["phases"][i]
                keep[i, list(subset)] = mask
            else:
                for channel in subset:
                    keep[i, channel] = retained[channel][i]
    return keep


def measured_donor_support(query, raw_donors, keep, rain_query, rain_donors, fraction=0.8):
    """Shared sensitivity pool: adequate measured support in every active channel.

    Query-hidden coordinates do not determine eligibility. Rain descriptors used
    by the query must be observed in donors. Outcomes are handled separately.
    """
    active = keep & np.isfinite(query)[None]
    eligible = np.ones((len(keep), len(raw_donors)), bool)
    for channel in range(query.shape[0]):
        needed = active[:, channel].sum(axis=1)
        observed = active[:, channel].astype(float) @ np.isfinite(raw_donors[:, channel]).T
        eligible &= (needed[:, None] == 0) | (observed >= fraction * needed[:, None])
    used = np.isfinite(rain_query)
    missing = used.astype(float) @ (~np.isfinite(rain_donors)).T
    return eligible & (missing == 0)


def combine_ground(qdist, support, rain, target):
    """Equal available groups: rain/season, local, peer mean, Maas mean."""
    result = np.array(rain, copy=True)
    weights = np.ones(len(result))
    for channels in [[target], [i for i in range(8) if i != target], [8, 9]]:
        available = support[:, channels]
        count = available.sum(axis=1)
        block = (qdist[:, :, channels] * available[:, None]).sum(axis=-1)
        result += np.divide(
            block, count[:, None], out=np.zeros_like(block), where=count[:, None] > 0
        )
        weights += count > 0
    return result / weights[:, None]


def stable_members(distance, allowed, limit=10):
    """Stable event-index ties; one candidate per distinct regional donor storm."""
    d = np.where(allowed if allowed.ndim == 2 else allowed[None], distance, np.inf)
    k = min(limit, d.shape[1])
    ids = np.argpartition(d, k - 1, axis=1)[:, :k]
    values = np.take_along_axis(d, ids, axis=1)
    order = np.lexsort((ids, values), axis=1)
    ids = np.take_along_axis(ids, order, axis=1)
    cutoff = np.take_along_axis(d, ids[:, -1:], axis=1)[:, 0]
    boundary_ties = np.isfinite(cutoff) & (
        (d == cutoff[:, None]).sum(axis=1) > (values == cutoff[:, None]).sum(axis=1)
    )
    if boundary_ties.any():
        ids[boundary_ties] = np.argsort(d[boundary_ties], axis=1, kind="stable")[:, :k]
    finite = np.isfinite(np.take_along_axis(d, ids, axis=1))
    return np.where(finite, ids, -1)


def batch_scores(observed, outcomes, ids):
    """Exact equal-member empirical CRPS; padded -1 denotes no member."""
    y = np.asarray(observed, float)
    ids = np.asarray(ids, int)
    valid = ids >= 0
    n = valid.sum(axis=1)
    safe_n = np.maximum(n, 1)
    members = outcomes[np.maximum(ids, 0)]
    members = np.where(valid[..., None], members, 0)
    ordered = np.sort(np.where(valid[..., None], members, np.inf), axis=1)
    rank = np.arange(ids.shape[1])[None, :, None]
    coefficients = np.where(rank < n[:, None, None], 2 * rank + 1 - n[:, None, None], 0)
    finite_ordered = np.where(np.isfinite(ordered), ordered, 0)
    pair = (coefficients * finite_ordered).sum(axis=1) / safe_n[:, None] ** 2
    absolute = (np.abs(members - y) * valid[..., None]).sum(axis=1) / safe_n[:, None]
    crps = np.maximum(absolute - pair, 0)
    mean = members.sum(axis=1) / safe_n[:, None]
    lower = finite_ordered[np.arange(len(ids)), np.maximum(np.ceil(0.1 * n).astype(int) - 1, 0)]
    upper = finite_ordered[np.arange(len(ids)), np.maximum(np.ceil(0.9 * n).astype(int) - 1, 0)]
    timing = np.full(len(ids), np.nan)
    if np.ptp(y) > 0:
        yp = np.flatnonzero(y == y.max())
        for i in np.flatnonzero((np.ptp(mean, axis=1) > 0) & (n > 0)):
            mp = np.flatnonzero(mean[i] == mean[i].max())
            timing[i] = np.abs(yp[:, None] - mp).min()
    out = np.column_stack(
        [
            crps.mean(axis=1),
            crps[:, 5],
            crps[:, 11],
            crps[:, 23],
            np.sqrt(np.mean((mean - y) ** 2, axis=1)),
            np.abs(mean.max(axis=1) - y.max()),
            timing,
            ((y >= lower) & (y <= upper)).mean(axis=1),
            (upper - lower).mean(axis=1),
        ]
    )
    out[n == 0] = np.nan
    return out, n


def persistence_scores(observed, last):
    """Point-mass forecast from a genuinely retained local observation."""
    y = np.asarray(observed, float)
    last = np.asarray(last, float)
    error = np.abs(last[:, None] - y[None])
    out = np.column_stack(
        [
            error.mean(axis=1),
            error[:, 5],
            error[:, 11],
            error[:, 23],
            np.sqrt(np.mean(error**2, axis=1)),
            np.abs(last - y.max()),
            np.full(len(last), np.nan),
            (error == 0).mean(axis=1),
            np.zeros(len(last)),
        ]
    )
    out[~np.isfinite(last)] = np.nan
    return out


SCORE_FIELDS = [
    "crps",
    "crps_h6",
    "crps_h12",
    "crps_h24",
    "rmse",
    "peak_error",
    "peak_time_error_h",
    "coverage80",
    "width80",
]
