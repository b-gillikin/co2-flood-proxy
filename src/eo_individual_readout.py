"""Chronological, conditional residual probes for individual encoder experiments.

No encoder import, outcome-derived normalization, or distributional forecast.
All fitted transformations see training rows only. Zero EO means the exact
selected raw pipeline, including its independently causal validation fallbacks.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import eigh

ALPHAS = (0.001, 0.01, 0.1, 1.0, 10.0)


def normalized_weights(weights):
    w = np.asarray(weights, float)
    if w.ndim != 1 or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError("Strictly positive finite training weights required")
    return w / w.sum()


def transform(train, test, weights):
    """Weighted train-only imputation/scaling; constant or unseen columns drop."""
    train, test = np.asarray(train, float), np.asarray(test, float)
    w = normalized_weights(weights)
    finite = np.isfinite(train)
    count = (finite * w[:, None]).sum(0)
    mean = np.divide(
        (np.where(finite, train, 0) * w[:, None]).sum(0),
        count,
        out=np.zeros(train.shape[1]),
        where=count > 0,
    )
    a = np.where(finite, train, mean)
    b = np.where(np.isfinite(test), test, mean)
    sd = np.sqrt(((a - mean) ** 2 * w[:, None]).sum(0))
    keep = (count > 0) & (sd > 1e-10)
    a, b = (a[:, keep] - mean[keep]) / sd[keep], (b[:, keep] - mean[keep]) / sd[keep]
    missing = (~finite).astype(float)
    mu = (missing * w[:, None]).sum(0)
    sigma = np.sqrt(((missing - mu) ** 2 * w[:, None]).sum(0))
    variable = sigma > 1e-10
    if variable.any():
        a = np.column_stack((a, (missing[:, variable] - mu[variable]) / sigma[variable]))
        b = np.column_stack(
            (b, ((~np.isfinite(test[:, variable])).astype(float) - mu[variable]) / sigma[variable])
        )
    scale = np.sqrt(max(a.shape[1], 1))
    return a / scale, b / scale


def conditional_design(common, raw, eo, conditioners, train, test, weights):
    """Linear kernels for main effects and two fixed causal interactions."""
    ca, cb = transform(conditioners[train], conditioners[test], weights)
    # Conditioners have no missingness in lawful rows and both columns can be
    # constant. Do not assume transform retained exactly two columns.
    ra, rb = transform(raw[train], raw[test], weights)
    ea, eb = transform(eo[train], eo[test], weights)
    ga, gb = transform(common[train], common[test], weights)
    raw_train, raw_test = [ga, ra], [gb, rb]
    eo_train, eo_test = [ea], [eb]
    for j in range(ca.shape[1]):
        a, b = transform(ra * ca[:, j, None], rb * cb[:, j, None], weights)
        raw_train.append(a)
        raw_test.append(b)
        a, b = transform(ea * ca[:, j, None], eb * cb[:, j, None], weights)
        eo_train.append(a)
        eo_test.append(b)
    r, t = np.column_stack(raw_train), np.column_stack(raw_test)
    e, f = np.column_stack(eo_train), np.column_stack(eo_test)
    return r, t, e, f


def conditional_parts(common, raw, eo, conditioners, train, test, weights):
    r, t, e, f = conditional_design(common, raw, eo, conditioners, train, test, weights)
    return r @ r.T, t @ r.T, e @ e.T, f @ e.T


def primal_predictions(design, residual, weights, alpha_grid, eo_grid, tolerance=1e-8, maximum=500):
    """Same ridge objective using bounded-memory, multi-output preconditioned CG."""
    ra, rb, ea, eb = design
    w = normalized_weights(weights)
    mean = (residual * w[:, None]).sum(0)
    result = {}
    diagnostics = []
    for influence in eo_grid:
        x = np.column_stack((ra, ea * np.sqrt(influence))) if influence else ra
        test = np.column_stack((rb, eb * np.sqrt(influence))) if influence else rb
        rhs = x.T @ ((residual - mean) * w[:, None])
        coefficient = np.zeros_like(rhs)
        for alpha in sorted(alpha_grid, reverse=True):

            def operation(value, x=x, alpha=alpha):
                return x.T @ ((x @ value) * w[:, None]) + alpha * value

            diagonal = (x * x * w[:, None]).sum(0) + alpha
            r = rhs - operation(coefficient)
            z = r / diagonal[:, None]
            direction = z.copy()
            rz = (r * z).sum(0)
            reference = np.maximum(np.linalg.norm(rhs, axis=0), 1e-30)
            for iteration in range(maximum + 1):
                active = np.linalg.norm(r, axis=0) > tolerance * reference
                if not active.any():
                    break
                if iteration == maximum:
                    raise RuntimeError(
                        "Ridge CG did not converge; preserve fold and repair, never discard silently"
                    )
                direction[:, ~active] = 0
                ap = operation(direction)
                denominator = (direction * ap).sum(0)
                step = np.divide(
                    rz, denominator, out=np.zeros_like(rz), where=active & (denominator > 0)
                )
                coefficient += direction * step
                r -= ap * step
                z = r / diagonal[:, None]
                new_rz = (r * z).sum(0)
                beta = np.divide(new_rz, rz, out=np.zeros_like(rz), where=active & (rz > 0))
                direction = z + direction * beta
                rz = new_rz
            result[(float(influence), float(alpha))] = test @ coefficient + mean
            diagnostics.append(
                dict(
                    eo_weight=float(influence),
                    alpha=float(alpha),
                    iterations=iteration,
                    maximum_relative_residual=float(
                        (np.linalg.norm(r, axis=0) / reference).max(initial=0)
                    ),
                )
            )
    primal_predictions.last_diagnostics = diagnostics
    return result


def residual_predictions(parts, residual, weights, alpha_grid, eo_grid):
    """Weighted kernel ridge; returned values are UNCLIPPED residuals."""
    kr, tr, ke, te = parts
    w = normalized_weights(weights)
    sw = np.sqrt(w)
    mean = (residual * w[:, None]).sum(0)
    centered = (residual - mean) * sw[:, None]
    result = {}
    for influence in eo_grid:
        kernel = kr + influence * ke
        eigen, vectors = eigh(kernel * sw[:, None] * sw[None, :], check_finite=True)
        eigen = np.maximum(eigen, 0)
        projected = vectors.T @ centered
        cross = (tr + influence * te) * sw[None, :]
        for alpha in alpha_grid:
            coef = vectors @ (projected / (eigen[:, None] + alpha))
            result[(float(influence), float(alpha))] = cross @ coef + mean
    return result


def fit_grid(
    common,
    raw,
    eo,
    conditioners,
    outcome,
    baseline,
    train,
    test,
    weights,
    alphas=ALPHAS,
    eo_weights=(0.0,),
):
    if not len(train) or not len(test):
        return {}
    if not np.isfinite(outcome[train]).all() or not np.isfinite(baseline[train]).all():
        raise ValueError("Only closed finite training labels/baselines are allowed")
    if len(train) > 2048:
        design = conditional_design(common, raw, eo, conditioners, train, test, weights)
        corrections = primal_predictions(
            design, outcome[train] - baseline[train], weights, alphas, eo_weights
        )
        fit_grid.last_solver = {
            "solver": "primal_CG",
            "details": primal_predictions.last_diagnostics,
        }
    else:
        parts = conditional_parts(common, raw, eo, conditioners, train, test, weights)
        corrections = residual_predictions(
            parts, outcome[train] - baseline[train], weights, alphas, eo_weights
        )
        fit_grid.last_solver = {"solver": "dual_eigendecomposition", "training_rows": len(train)}
    return {
        key: np.maximum(baseline[test] + correction, 0) for key, correction in corrections.items()
    }


def weighted_error(observed, prediction, weights):
    ok = np.isfinite(observed).all(1) & np.isfinite(prediction).all(1)
    if not ok.any():
        return 0.0, 0.0
    error = np.abs(observed[ok] - prediction[ok]).mean(1)
    return float(error @ weights[ok]), float(weights[ok].sum())


def choose(candidates):
    """Ties prefer zero correction, then zero EO, then stronger shrinkage."""
    valid = [
        (num / den, weight, -alpha, key)
        for key, (num, den, weight, alpha) in candidates.items()
        if den > 0
    ]
    return min(valid)[-1] if valid else "baseline"


def raw_fold(
    common,
    raw,
    conditioners,
    y,
    baseline,
    train,
    test,
    validation,
    weights,
    available,
    alphas=ALPHAS,
):
    """Select raw head using earlier-year validation only; never test labels."""
    totals = {"baseline": [0.0, 0.0, -1.0, float("inf")]}
    for a in alphas:
        totals[float(a)] = [0.0, 0.0, 0.0, float(a)]
    empty = np.zeros((len(y), 0))
    for inner, held in validation:
        inner = inner[available[inner]]
        if not len(inner):
            continue
        pred = fit_grid(
            common, raw, empty, conditioners, y, baseline, inner, held, weights[inner], alphas
        )
        for key in totals:
            candidate = baseline[held].copy() if key == "baseline" else pred[(0.0, key)]
            candidate[~available[held]] = baseline[held][~available[held]]
            num, den = weighted_error(y[held], candidate, weights[held])
            totals[key][0] += num
            totals[key][1] += den
    selected = choose(totals)
    result = baseline[test].copy()
    fit = train[available[train]]
    held = test[available[test]]
    if selected != "baseline" and len(fit) and len(held):
        result[available[test]] = fit_grid(
            common, raw, empty, conditioners, y, baseline, fit, held, weights[fit], [selected]
        )[(0.0, selected)]
    return result, {"alpha": selected, "validation": totals}


def encoded_fold(
    common,
    raw,
    eo,
    conditioners,
    y,
    baseline,
    raw_oof,
    train,
    test,
    validation,
    weights,
    raw_available,
    eo_available,
    alphas=ALPHAS,
    eo_weights=(0.1, 1.0),
):
    """EO=0 retains the exact causal raw OOF policy, not a retuned raw head.

    Earlier raw OOF predictions are constructed before this function; therefore
    unsupported validation queries use predictions whose own tuning predates
    their validation year. Outer test outcomes never enter tuning or fitting.
    """
    totals = {"raw_only": [0.0, 0.0, 0.0, float("inf")]}
    for w in eo_weights:
        for a in alphas:
            totals[(float(w), float(a))] = [0.0, 0.0, float(w), float(a)]
    for inner, held in validation:
        inner = inner[raw_available[inner]]
        if not len(inner):
            continue
        preds = fit_grid(
            common,
            raw,
            eo,
            conditioners,
            y,
            baseline,
            inner,
            held,
            weights[inner],
            alphas,
            eo_weights,
        )
        for key in totals:
            candidate = raw_oof[held].copy()
            if key != "raw_only":
                use = eo_available[held] & raw_available[held]
                candidate[use] = preds[key][use]
            num, den = weighted_error(y[held], candidate, weights[held])
            totals[key][0] += num
            totals[key][1] += den
    selected = choose(totals)
    if selected == "baseline":
        selected = "raw_only"
    result = raw_oof[test].copy()
    fit = train[raw_available[train]]
    use = raw_available[test] & eo_available[test]
    if selected != "raw_only" and len(fit) and use.any():
        w, a = selected
        result[use] = fit_grid(
            common, raw, eo, conditioners, y, baseline, fit, test[use], weights[fit], [a], [w]
        )[selected]
    return result, {"parameters": selected, "validation": {str(k): v for k, v in totals.items()}}


def balanced_weights(storms, sites=None, rivers=None):
    """Balance only the supplied rows; future case counts cannot change fitting."""
    storms = np.asarray(storms)
    sites = np.zeros(len(storms), int) if sites is None else np.asarray(sites)
    rivers = np.zeros(len(storms), int) if rivers is None else np.asarray(rivers)
    w = np.zeros(len(storms))
    for river in np.unique(rivers):
        river_mask = rivers == river
        local_sites = np.unique(sites[river_mask])
        for site in local_sites:
            mask = river_mask & (sites == site)
            local_storms = np.unique(storms[mask])
            for storm in local_storms:
                take = mask & (storms == storm)
                w[take] = (
                    1 / len(np.unique(rivers)) / len(local_sites) / len(local_storms) / take.sum()
                )
    return w


def prequential_heads(
    common,
    raw,
    eo,
    conditioners,
    y,
    baseline,
    years,
    label_ready,
    train_before,
    storm_ids,
    raw_available,
    eo_available,
    sites=None,
    rivers=None,
    alphas=ALPHAS,
    eo_weights=(0.1, 1.0),
    progress=None,
):
    """Each annual grid is fitted once and reused in earlier-year validation.

    Raw and encoded hyperparameter policies see only earlier closed validation
    outcomes. Encoded unsupported rows use the previously computed causal raw
    policy, not a raw model tuned on that validation year's labels. This avoids
    expensive refitting of identical inner-year grids without changing chronology.
    """
    raw_oof = baseline.copy()
    encoded = baseline.copy()
    grid = {}
    records = []
    years = np.asarray(years)
    raw_available = np.asarray(raw_available, bool)
    eo_available = np.asarray(eo_available, bool)

    def weights(ids):
        return balanced_weights(
            storm_ids[ids],
            sites[ids] if sites is not None else None,
            rivers[ids] if rivers is not None else None,
        )

    for year in sorted(np.unique(years)):
        closed = np.array(train_before(int(year)), dtype=bool, copy=True)
        held_storms = np.unique(storm_ids[years == year])
        closed &= ~np.isin(storm_ids, held_storms)
        train = np.flatnonzero(closed & label_ready & raw_available & np.isfinite(baseline).all(1))
        test = np.flatnonzero(years == year)
        if not len(train):
            records.append(
                dict(
                    year=int(year),
                    training=0,
                    status="no_closed_training",
                    raw_parameters="baseline",
                    eo_parameters="raw_only",
                )
            )
            continue
        fit = fit_grid(
            common,
            raw,
            eo,
            conditioners,
            y,
            baseline,
            train,
            test,
            weights(train),
            alphas,
            (0.0, *eo_weights),
        )
        grid[int(year)] = {k: np.array(v, copy=True) for k, v in fit.items()}
        solver = fit_grid.last_solver
        validation = []
        for previous in sorted(np.unique(years[train]), reverse=True):
            if int(previous) in grid and previous < year:
                ids = np.flatnonzero(
                    (years == previous)
                    & closed
                    & label_ready
                    & raw_available
                    & np.isfinite(baseline).all(1)
                )
                if len(ids):
                    validation.append((int(previous), ids))
            if len(validation) == 2:
                break
        totals = {"baseline": [0.0, 0.0, -1.0, float("inf")]}
        for alpha in alphas:
            totals[float(alpha)] = [0.0, 0.0, 0.0, float(alpha)]
        for previous, ids in validation:
            full = np.flatnonzero(years == previous)
            positions = np.searchsorted(full, ids)
            w = weights(ids)
            for key in totals:
                pred = (
                    baseline[ids]
                    if key == "baseline"
                    else grid[previous][(0.0, float(key))][positions]
                )
                num, den = weighted_error(y[ids], pred, w)
                totals[key][0] += num
                totals[key][1] += den
        raw_parameter = choose(totals)
        use = raw_available[test]
        if raw_parameter != "baseline":
            raw_oof[test[use]] = fit[(0.0, raw_parameter)][use]
        # EO can preserve the exact tuned raw policy OR reject the entire head.
        candidates = {
            "raw_only": [0.0, 0.0, -1.0, float("inf")],
            "baseline": [0.0, 0.0, 0.0, float("inf")],
        }
        for weight in eo_weights:
            for alpha in alphas:
                candidates[(float(weight), float(alpha))] = [0.0, 0.0, float(weight), float(alpha)]
        for alpha in alphas:
            candidates[(0.0, float(alpha))] = [0.0, 0.0, 0.0, float(alpha)]
        for previous, ids in validation:
            full = np.flatnonzero(years == previous)
            positions = np.searchsorted(full, ids)
            w = weights(ids)
            for key in candidates:
                pred = raw_oof[ids].copy()
                if key == "baseline":
                    pred = baseline[ids]
                elif key != "raw_only":
                    active = raw_available[ids] & (eo_available[ids] if key[0] else True)
                    pred[active] = grid[previous][key][positions[active]]
                num, den = weighted_error(y[ids], pred, w)
                candidates[key][0] += num
                candidates[key][1] += den
        parameter = choose(candidates) if validation else "raw_only"
        encoded[test] = raw_oof[test]
        if parameter == "baseline":
            encoded[test] = baseline[test]
        elif parameter != "raw_only":
            active = raw_available[test] & (eo_available[test] if parameter[0] else True)
            encoded[test[active]] = fit[parameter][active]
        records.append(
            dict(
                year=int(year),
                training=len(train),
                training_rows=train.tolist(),
                solver=solver,
                validation_years=[x[0] for x in validation],
                raw_parameters=raw_parameter,
                eo_parameters=parameter,
                raw_validation={str(k): v for k, v in totals.items()},
                eo_validation={str(k): v for k, v in candidates.items()},
            )
        )
        if progress is not None:
            progress(records[-1])
    return raw_oof, encoded, records
