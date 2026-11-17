"""Audit-corrected selection, population accounting and calibration for DISE.

The original module/benchmark remain unchanged for historical reproducibility.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from src.dise import reconstruct, residual_target


def split_masks(frame, year, excluded_group=None):
    day = pd.to_datetime(frame.day, utc=True)
    allowed = (
        np.ones(len(frame), bool)
        if excluded_group is None
        else frame.river_group.ne(excluded_group).to_numpy()
    )
    good = np.isfinite(frame[["q_observed", "q_model"]]).all(axis=1).to_numpy()
    train = allowed & day.ge("2018-01-01").to_numpy() & day.lt(f"{year - 1}-01-01").to_numpy()
    validation = (
        allowed & day.ge(f"{year - 1}-01-01").to_numpy() & day.lt(f"{year}-01-01").to_numpy()
    )
    test = day.ge(f"{year}-01-01").to_numpy() & day.lt(f"{year + 1}-01-01").to_numpy()
    if excluded_group is not None:
        test &= ~allowed
    return train & good, validation & good, test & good


def weights(frame):
    counts = frame.groupby(["river_group", "gauge"])["gauge"].transform("size")
    gauges = frame[["river_group", "gauge"]].drop_duplicates().groupby("river_group").size()
    value = 1.0 / (counts.to_numpy() * frame.river_group.map(gauges).to_numpy())
    return value * len(value) / value.sum()


def population(frame):
    table = frame[["gauge", "river_group"]].drop_duplicates()
    if table.gauge.duplicated().any():
        raise ValueError("A gauge cannot belong to two river groups")
    return table.set_index("gauge").river_group.to_dict()


def score(frame, prediction, expected, multiplicity=None):
    """Return undefined plus explicit support when a fixed population is absent."""
    pred = np.asarray(prediction, float)
    if len(pred) != len(frame):
        raise ValueError("Prediction and reference row counts differ")
    mult = np.ones(len(frame)) if multiplicity is None else np.asarray(multiplicity, float)
    if len(mult) != len(frame) or (mult < 0).any() or not np.isfinite(mult).all():
        raise ValueError("Invalid resampling multiplicity")
    if set(frame.gauge) - set(expected):
        raise ValueError("Undeclared gauge in score frame")
    if any(
        expected[g] != r
        for g, r in frame[["gauge", "river_group"]].itertuples(index=False, name=None)
    ):
        raise ValueError("Gauge river identity differs from declared population")
    active = mult > 0
    missing = sorted(set(expected) - set(frame.loc[active, "gauge"]))
    bad = active & (~np.isfinite(pred) | ~np.isfinite(frame.q_observed.to_numpy()))
    reason = (
        "missing_population"
        if missing
        else "nonfinite_prediction_or_reference"
        if bad.any()
        else None
    )
    result = dict(
        rows=int(active.sum()),
        effective_rows=float(mult.sum()),
        expected_gauges=sorted(expected),
        missing_gauges=missing,
        nonfinite_rows=int(bad.sum()),
        status="undefined" if reason else "defined",
        reason=reason,
        mae=None,
        rmse=None,
        bias=None,
        per_gauge=[],
    )
    if not expected or not active.any():
        result.update(status="undefined", reason="no_verification_population")
        return result
    if reason:
        return result
    errors = pred - frame.q_observed.to_numpy()
    for gauge, group in expected.items():
        use = active & frame.gauge.eq(gauge).to_numpy()
        result["per_gauge"].append(
            dict(
                gauge=gauge,
                river_group=group,
                rows=int(use.sum()),
                mae=float(np.average(np.abs(errors[use]), weights=mult[use])),
                mse=float(np.average(errors[use] ** 2, weights=mult[use])),
                bias=float(np.average(errors[use], weights=mult[use])),
            )
        )
    table = (
        pd.DataFrame(result["per_gauge"])
        .groupby("river_group")[["mae", "mse", "bias"]]
        .mean()
        .mean()
    )
    result.update(mae=float(table.mae), rmse=float(np.sqrt(table.mse)), bias=float(table.bias))
    return result


def fit_candidate(
    train, validation, columns, candidate, policy="native_rmse", seed=101, tree_limit=1500
):
    from xgboost import XGBRegressor

    cols = [c for c in columns if np.isfinite(train[c]).any() and train[c].nunique() > 1]
    if not cols:
        raise ValueError("No varying training-supported features")
    w = weights(validation)
    base = validation.q_model.to_numpy()
    observed = validation.q_observed.to_numpy()

    def native_rmse(_truth, residual, sample_weight=None):
        pred, _ = reconstruct(base, residual)
        return float(np.sqrt(np.average((pred - observed) ** 2, weights=w)))

    extra = dict(eval_metric=native_rmse) if policy == "native_rmse" else {}
    if policy not in ("native_rmse", "article_faithful"):
        raise ValueError(policy)
    model = XGBRegressor(
        **candidate,
        n_estimators=tree_limit,
        n_jobs=2,
        tree_method="hist",
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=10,
        reg_alpha=0.1,
        objective="reg:squarederror",
        early_stopping_rounds=50,
        random_state=seed,
        **extra,
    )
    before = time.monotonic()
    model.fit(
        train[cols],
        residual_target(train.q_observed, train.q_model),
        sample_weight=weights(train),
        eval_set=[(validation[cols], residual_target(validation.q_observed, validation.q_model))],
        sample_weight_eval_set=[w],
        verbose=False,
    )
    pred, clipped = reconstruct(base, model.predict(validation[cols]))
    metrics = score(validation, pred, population(validation))
    record = dict(
        seconds=time.monotonic() - before,
        best_iteration=int(model.best_iteration),
        selection_score=metrics["rmse"] if policy == "native_rmse" else metrics["mae"],
        validation_mae=metrics["mae"],
        validation_rmse=metrics["rmse"],
        floored_validation=clipped,
        features=len(cols),
        policy=policy,
        parameters=candidate,
    )
    return model, cols, record


def add_climate(frame, year, coordinates, forcing_history=None):
    """Only earlier forcing data; no target discharge or supplied full-record signatures."""
    result = frame.copy()
    history = frame if forcing_history is None else forcing_history
    for current_year in sorted(result.day.dt.year.unique()):
        past = history.loc[history.day.lt(f"{current_year}-01-01")]
        stat = past.groupby("gauge").agg(
            a_past_precip_mean_m=("h_precip_m", "mean"),
            a_past_temp_mean_k=("h_temp_k", "mean"),
            a_past_temp_sd_k=("h_temp_k", "std"),
        )
        use = result.day.dt.year.eq(current_year)
        for name in stat:
            result.loc[use, name] = result.loc[use, "gauge"].map(stat[name])
    for name in ["latitude", "longitude"]:
        result[f"a_{name}"] = result.gauge.map({g: c[name] for g, c in coordinates.items()})
    return result


def fdc_fit(simulated, observed, months):
    """Daily empirical monthly FDC mapping, annual fallback, positive tail ratio."""
    curves = {}
    simulated, observed, months = map(np.asarray, [simulated, observed, months])
    good = np.isfinite(simulated) & np.isfinite(observed) & (simulated >= 0) & (observed >= 0)
    for month in [0, *range(1, 13)]:
        use = good & ((months == month) if month else True)
        if use.sum() < (20 if month else 2):
            continue
        p = np.linspace(0, 1, min(201, int(use.sum())))
        qx, qy = np.quantile(simulated[use], p), np.quantile(observed[use], p)
        ties = pd.DataFrame({"x": qx, "y": qy}).groupby("x").y.mean()
        curves[month] = dict(
            x=ties.index.to_numpy().tolist(), y=ties.to_numpy().tolist(), n=int(use.sum())
        )
    return curves


def fdc_apply(curves, simulated, months):
    out = np.full(len(simulated), np.nan)
    for i, (q, month) in enumerate(zip(simulated, months, strict=True)):
        curve = curves.get(int(month), curves.get(0))
        if curve is None or not np.isfinite(q):
            continue
        x, y = np.asarray(curve["x"]), np.asarray(curve["y"])
        out[i] = np.interp(q, x, y)
        if q > x[-1] and x[-1] > 0:
            out[i] = q * y[-1] / x[-1]
    return out


def choose_donor(frame, past_mask, target, descriptor_columns):
    """Training-only conventional-descriptor standardization; no target Q used."""
    train = frame.loc[past_mask]
    cutoff = pd.Timestamp(year=train.day.max().year + 1, month=1, day=1, tz="UTC")
    snapshots = frame.loc[frame.day.eq(cutoff)].set_index("gauge")[descriptor_columns]
    means = snapshots.reindex(sorted(train.gauge.unique()))
    target_row = snapshots.loc[target]
    valid = means.notna().all(axis=0) & target_row.notna() & means.std().gt(0)
    cols = means.columns[valid]
    if not len(cols):
        return None, {}
    scale = means[cols].std(ddof=0)
    distances = (((means[cols] - target_row[cols]) / scale) ** 2).mean(axis=1)
    donor = str(distances.sort_values(kind="stable").index[0])
    return donor, dict(features=cols.tolist(), distances=distances.to_dict())


def donor_fdc_fit(donor_sim, donor_obs, donor_months, target_sim, target_months):
    """Transfer donor correction ratios at target-model quantiles, without target Q labels."""
    ds, do, dm, ts, tm = map(
        np.asarray, [donor_sim, donor_obs, donor_months, target_sim, target_months]
    )
    curves = {}
    for month in [0, *range(1, 13)]:
        good_d = np.isfinite(ds) & np.isfinite(do) & (ds >= 0) & (do >= 0)
        good_t = np.isfinite(ts) & (ts >= 0)
        if month:
            good_d &= dm == month
            good_t &= tm == month
        minimum = 20 if month else 2
        if min(good_d.sum(), good_t.sum()) < minimum:
            continue
        p = np.linspace(0, 1, min(201, int(good_d.sum()), int(good_t.sum())))
        dx, dy, tx = (
            np.quantile(ds[good_d], p),
            np.quantile(do[good_d], p),
            np.quantile(ts[good_t], p),
        )
        usable = dx > 0
        if not usable.any():
            continue
        ratio = np.interp(p, p[usable], dy[usable] / dx[usable])
        # Positive-tail ratio is retained beyond the target training maximum.
        merged = pd.DataFrame(dict(x=tx, ratio=ratio)).groupby("x").ratio.mean()
        curves[month] = dict(
            x=merged.index.to_list(),
            ratio=merged.to_list(),
            donor_pairs=int(good_d.sum()),
            target_model_days=int(good_t.sum()),
            omitted_zero_donor_quantiles=int((~usable).sum()),
        )
    return curves


def donor_fdc_apply(curves, simulated, months):
    result = np.full(len(simulated), np.nan)
    for i, (q, month) in enumerate(zip(simulated, months, strict=True)):
        c = curves.get(int(month), curves.get(0))
        if c is not None and np.isfinite(q):
            result[i] = q * np.interp(q, c["x"], c["ratio"])
    return result


def year_bootstrap(frame, predictions, expected, draws=999, seed=20261116):
    """Joint year multiplicities, fixed population, no retry of undefined draws."""
    blocks = sorted(frame["block_year"].unique())
    if len(blocks) < 2:
        return (
            pd.DataFrame(np.nan, index=range(draws), columns=list(predictions)),
            np.ones((draws, len(blocks)), int),
            blocks,
        )
    rng = np.random.default_rng(seed)
    multiplicities = rng.multinomial(len(blocks), np.full(len(blocks), 1 / len(blocks)), size=draws)
    result = []
    arrays = {k: np.asarray(v) for k, v in predictions.items()}
    for row in multiplicities:
        count = frame.block_year.map(dict(zip(blocks, row, strict=True))).to_numpy()
        values = {}
        for name, pred in arrays.items():
            values[name] = score(frame, pred, expected, count)["mae"]
        result.append(values)
    return pd.DataFrame(result), multiplicities, blocks
