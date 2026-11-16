"""Transparent daily reconstruction helpers, separate from the old 24h task."""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

ARMS = ("H", "H+A", "H+E", "H+A+E")
CANDIDATES = (
    {"max_depth": 2, "learning_rate": 0.03, "min_child_weight": 10},
    {"max_depth": 2, "learning_rate": 0.1, "min_child_weight": 30},
    {"max_depth": 4, "learning_rate": 0.03, "min_child_weight": 30},
    {"max_depth": 4, "learning_rate": 0.1, "min_child_weight": 10},
)


def daily_hour_end(frame):
    """UTC calendar-day average of exactly 24 hour-END means; no gap filling."""
    x = frame.copy()
    x.index = pd.to_datetime(x.index, utc=True)
    if not x.index.is_unique or not x.index.is_monotonic_increasing:
        raise ValueError("Hourly axis must be sorted and unique")
    if (x.index != x.index.floor("h")).any():
        raise ValueError("Hourly means must fall on integer hours")
    x = x.where(np.isfinite(x) & x.ge(0))
    x.index -= pd.Timedelta(hours=1)
    counts = x.resample("D").count()
    return x.resample("D").mean().where(counts.eq(24)), counts


def specific_q(q_m3s, area_km2):
    if not np.isfinite(area_km2) or area_km2 <= 0:
        raise ValueError("Discharge conversion requires positive reference area")
    return np.asarray(q_m3s) * 86.4 / area_km2


def residual_target(observed, model):
    if (np.asarray(observed) < 0).any() or (np.asarray(model) < 0).any():
        raise ValueError("Negative discharge cannot enter log residual")
    return np.log1p(observed) - np.log1p(model)


def reconstruct(model, residual):
    with np.errstate(over="raise", invalid="raise"):
        before_floor = np.expm1(np.log1p(model) + residual)
    return np.maximum(0, before_floor), int((before_floor < 0).sum())


def weights(frame):
    """Equal groups, equal gauges within group, equal valid days within gauge."""
    counts = frame.groupby(["river_group", "gauge"]).size()
    gauges = counts.groupby(level=0).size()
    w = np.array([1 / (counts.loc[(g, s)] * gauges[g]) for g, s in
                  frame[["river_group", "gauge"]].itertuples(index=False, name=None)])
    return w * len(w) / w.sum()


def balanced_mae(frame, prediction):
    f = frame[["river_group", "gauge", "q_observed"]].copy()
    f["error"] = np.abs(f.q_observed.to_numpy() - np.asarray(prediction))
    if not np.isfinite(f.error).all():
        raise ValueError("Nonfinite prediction cannot silently reduce the scored population")
    return float(f.groupby(["river_group", "gauge"]).error.mean().groupby(level=0).mean().mean())


def feature_columns(frame, arm):
    if arm not in ARMS:
        raise ValueError(arm)
    names = [x for x in frame if x.startswith("h_")]
    if "+A" in arm:
        names += [x for x in frame if x.startswith("a_")]
    if "+E" in arm:
        names += [x for x in frame if x.startswith("e_")]
    if not names:
        raise ValueError("No declared input features")
    return names


def split_masks(frame, year, excluded_group=None):
    """Past-only training/validation with one group excluded from both."""
    day = pd.to_datetime(frame.day, utc=True)
    allowed = np.ones(len(frame), bool) if excluded_group is None else frame.river_group.ne(excluded_group).to_numpy()
    train = allowed & day.ge("2018-01-01").to_numpy() & day.lt(f"{year-1}-01-01").to_numpy()
    val = allowed & day.ge(f"{year-1}-01-08").to_numpy() & day.lt(f"{year}-01-01").to_numpy()
    # Seven-day gap prevents a weather/model lag crossing the data partition.
    test = day.ge(f"{year}-01-08").to_numpy() & day.lt(f"{year+1}-01-01").to_numpy()
    if excluded_group is not None:
        test &= frame.river_group.eq(excluded_group).to_numpy()
    valid = np.isfinite(frame[["q_observed", "q_model"]]).all(axis=1).to_numpy()
    return train & valid, val & valid, test & valid


def fit_candidate(train, validation, columns, candidate, seed=101, tree_limit=1500):
    """One training-only missing-feature filter and past validation early stop."""
    from xgboost import XGBRegressor

    columns = [c for c in columns if np.isfinite(train[c]).any() and train[c].nunique() > 1]
    if not columns:
        raise ValueError("No varying training-supported features")
    # XGBoost learns missing-value routes from training data; no full-record fill.
    model = XGBRegressor(
        **candidate, n_estimators=tree_limit, n_jobs=2, tree_method="hist",
        subsample=0.8, colsample_bytree=0.8, reg_lambda=10, reg_alpha=0.1,
        objective="reg:squarederror", early_stopping_rounds=50, random_state=seed,
    )
    before = time.monotonic()
    model.fit(train[columns], residual_target(train.q_observed, train.q_model),
              sample_weight=weights(train),
              eval_set=[(validation[columns], residual_target(validation.q_observed, validation.q_model))],
              sample_weight_eval_set=[weights(validation)], verbose=False)
    predicted, floored = reconstruct(validation.q_model.to_numpy(), model.predict(validation[columns]))
    record = dict(seconds=time.monotonic()-before, best_iteration=int(model.best_iteration),
                  validation_mae=balanced_mae(validation, predicted), floored_validation=floored,
                  features=len(columns), seed=seed, parameters=candidate)
    return model, columns, record
