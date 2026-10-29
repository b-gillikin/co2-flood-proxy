"""Feature joins, masked common context and point-score accounting."""

from __future__ import annotations

import re

import numpy as np


def vector_columns(frame, prefix):
    pattern = re.compile(r"^" + re.escape(prefix) + r"_t\d+_r\d+_\d+$")
    return sorted(c for c in frame if pattern.match(c))


def feature_matrix(frame, prefixes, landscape=False):
    columns = [c for p in prefixes for c in vector_columns(frame, p)]
    if not columns:
        return np.empty((len(frame), 0))
    x = frame[columns].to_numpy(float, copy=True)
    grouped = {}
    for j, c in enumerate(columns):
        match = re.match(r"(.+)_t(\d+)_r(\d+)_(\d+)$", c)
        key = (match[1], match[3], match[4])
        grouped.setdefault(key, []).append((int(match[2]), j))
    additional = []
    for group in grouped.values():
        indexes = [j for _, j in sorted(group)]
        if len(indexes) > 1:
            values = x[:, indexes]
            if landscape:
                count = np.isfinite(values).sum(1)
                mean = np.divide(
                    np.nansum(values, axis=1),
                    count,
                    out=np.full(len(values), np.nan),
                    where=count > 0,
                )
                var = np.divide(
                    np.nansum((values - mean[:, None]) ** 2, axis=1),
                    count,
                    out=np.full(len(values), np.nan),
                    where=count > 0,
                )
                additional.extend([mean[:, None], np.sqrt(var)[:, None]])
            else:
                additional.append(np.diff(values, axis=1))
        elif landscape:
            additional.append(x[:, indexes])
    return np.column_stack(additional) if landscape else np.column_stack([x, *additional])


def common_context(
    bank,
    rows,
    scenario,
    area,
    raw_available,
    eo_available,
    source_coverage=None,
    excluded_channels=(),
):
    parts = []
    conditions = []
    for row in rows.itertuples():
        qi, gi, u = int(row.query), int(row.site), int(row.offset_h)
        q = np.array(bank[f"q_{u}"][qi], float, copy=True)
        if scenario == "local_q_absent":
            q[gi] = np.nan
        elif scenario == "all_q_absent":
            q[:] = np.nan
        q[list(excluded_channels)] = np.nan
        available = np.isfinite(q)
        counts = available.sum(1)
        age = np.full(10, np.nan)
        for j in range(10):
            if counts[j]:
                age[j] = 71 - np.flatnonzero(available[j])[-1]
        rain = bank[f"rain_{u}_1_0"][qi, gi]
        parts.append(
            np.r_[
                q.ravel(),
                rain,
                counts / 72,
                age,
                float(row.issue_utc.year),
                u,
                getattr(row, "eo_context_age_days", np.nan),
            ]
        )
        conditions.append(rain[1])
    common = np.column_stack(
        [np.asarray(parts), raw_available.astype(float), eo_available.astype(float)]
    )
    if source_coverage is not None:
        common = np.column_stack([common, source_coverage])
    return common, np.asarray(conditions)


def assessment_scores(observed, predicted):
    ok = np.isfinite(observed).all(1) & np.isfinite(predicted).all(1)
    error = predicted - observed
    result = {
        "mae": np.where(ok, np.abs(error).mean(1), np.nan),
        "rmse": np.where(ok, np.sqrt((error**2).mean(1)), np.nan),
    }
    for h in (6, 12, 24):
        result[f"absolute_error_h{h}"] = np.where(ok, np.abs(error[:, h - 1]), np.nan)
    result["peak_error"] = np.where(ok, np.abs(predicted.max(1) - observed.max(1)), np.nan)
    timing = np.full(len(observed), np.nan)
    for i in np.flatnonzero(ok):
        if np.ptp(observed[i]) > 0 and np.ptp(predicted[i]) > 0:
            a = np.flatnonzero(observed[i] == observed[i].max())
            b = np.flatnonzero(predicted[i] == predicted[i].max())
            timing[i] = np.abs(a[:, None] - b).min()
    result["peak_time_error_h"] = timing
    return result


def prediction_status(records, years, raw_available, eo_available):
    """Case-level training/fallback ledger; no observed outcomes are inspected."""
    n = len(years)
    train_n = np.zeros(n, int)
    raw_mode = np.full(n, "conventional", object)
    eo_mode = raw_mode.copy()
    for record in records:
        take = np.asarray(years) == record["year"]
        train_n[take] = record["training"]
        if not record["training"]:
            continue
        raw_parameter = record.get("raw_parameters", "baseline")
        parameter = record.get("eo_parameters", "raw_only")
        active = take & raw_available
        if raw_parameter != "baseline":
            raw_mode[active] = "raw_correction"
        eo_mode[take] = raw_mode[take]
        if isinstance(parameter, str):
            if parameter == "baseline":
                eo_mode[take] = "conventional"
        else:
            if float(parameter[0]) == 0:
                eo_mode[active] = "raw_grid_correction"
            else:
                eo_mode[active & eo_available] = "encoder_correction"
    return dict(
        training_count=train_n, raw_prediction_mode=raw_mode, encoder_prediction_mode=eo_mode
    )
