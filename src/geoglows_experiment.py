"""Paired observed/modelled discharge preparation; no encoder training.

Hydrological hour-end alignment is distinct from real publication availability.
GEOGLOWS reanalysis histories here are a hypothetical information-content replay.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".partial")
    temp.write_text(json.dumps(value, indent=2, default=str) + "\n")
    temp.replace(path)


def disk_check(root, reserve_gib=50, pending_bytes=0):
    free = shutil.disk_usage(root).free
    if free - pending_bytes < reserve_gib * 2**30:
        raise RuntimeError(
            "Projected write would breach the free-space reserve; no deletion attempted"
        )
    return free / 2**30


def download(url, path, root, reserve_gib=50):
    """Stream to an atomic local file; retain source identity and resume by file."""
    path = Path(path)
    receipt = path.with_suffix(path.suffix + ".source.json")
    if path.exists() and receipt.exists():
        old = json.loads(receipt.read_text())
        if old["url"] != url or old["sha256"] != sha(path):
            raise ValueError(f"Retained source changed: {path}")
        return old
    if path.exists():
        raise ValueError(f"Unreceipted file requires inspection, not overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        disk_check(root, reserve_gib, int(response.headers.get("Content-Length", 0)))
        partial = path.with_suffix(path.suffix + ".partial")
        with partial.open("wb") as stream:
            for block in response.iter_content(1024**2):
                disk_check(root, reserve_gib, len(block))
                stream.write(block)
        partial.replace(path)
        record = dict(
            url=url,
            sha256=sha(path),
            bytes=path.stat().st_size,
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
            acquired_utc=datetime.now(timezone.utc).isoformat(),
        )
    write_json(receipt, record)
    return record


def hour_end(series):
    """Convert documented left-labelled hourly model averages; never interpolate."""
    result = series.copy()
    result.index = pd.to_datetime(result.index, utc=True) + pd.Timedelta(hours=1)
    if not result.index.is_unique or not result.index.is_monotonic_increasing:
        raise ValueError("Duplicate or unsorted GEOGLOWS timestamps")
    if (result.index != result.index.floor("h")).any():
        raise ValueError("Non-hourly GEOGLOWS timestamps")
    return result.where(np.isfinite(result) & (result >= 0))


def replace_histories(bank, hourly, epochs, offsets):
    """Replace query/donor histories and all Q normalization, preserve outcomes.

    No nearest-time match, backward fill, observed fallback or future Q allowed.
    Missing model coverage stays missing. The held donor-only causal forward
    hold convention is retained and is not a measured GEOGLOWS value.
    """
    from src.scarcity import coordinate_moments, forward_hold

    values = hourly.reindex(pd.to_datetime(epochs, unit="h", utc=True)).to_numpy(float)
    if values.shape[1] != 10:
        raise ValueError("All ten Q channels, including Meuse, must be explicit")
    result = dict(bank)
    for offset in offsets:
        pos = bank[f"positions_{offset}"]
        if pos.min() < 0 or pos.max() >= len(values):
            raise ValueError("History outside model source axis")
        q = values[pos].transpose(0, 2, 1)
        result[f"q_{offset}"] = q
        result[f"donor_q_{offset}"] = forward_hold(q)
        result[f"input_quality_{offset}"] = np.isfinite(q)
        key = f"{offset}_0"
        mean, variance = coordinate_moments(bank[f"prior_{key}"], result[f"donor_q_{offset}"])
        result[f"q_mean_{key}"] = mean
        result[f"q_pairvar_{key}"] = 2 * variance
    return result


def qm_fit(simulated, observed, months, boundary, minimum=20):
    """Training-only monthly empirical flow-duration mapping, no target-year data.

    At most 201 quantile knots; ties are averaged. Above the training maximum,
    preserve the model/observed ratio at that maximum instead of flat clipping.
    """
    sim, obs = simulated.align(observed, join="inner", axis=0)
    if not sim.columns.equals(obs.columns):
        raise ValueError("Calibration channels differ")
    prior = sim.index < pd.Timestamp(boundary)
    result = {}
    for column in sim:
        valid = prior & np.isfinite(sim[column]) & np.isfinite(obs[column])
        valid &= (sim[column] >= 0) & (obs[column] >= 0)
        for month in months:
            use = valid & (sim.index.month == month)
            fallback = int(use.sum()) < minimum
            if fallback:
                use = valid
            if not use.any():
                result[(column, month)] = None
                continue
            probabilities = np.linspace(0, 1, min(201, int(use.sum())))
            x = np.quantile(sim.loc[use, column], probabilities)
            y = np.quantile(obs.loc[use, column], probabilities)
            unique, inverse = np.unique(x, return_inverse=True)
            y = np.bincount(inverse, weights=y) / np.bincount(inverse)
            result[(column, month)] = dict(
                x=unique,
                y=y,
                pairs=int(use.sum()),
                annual_fallback=fallback,
                last_training_time=sim.index[use].max().isoformat(),
            )
    return result


def qm_apply(values, month, curve):
    """Map finite values only; absent calibration remains unknown."""
    del month  # selected by caller; retained for explicit monthly call sites
    out = np.full(np.shape(values), np.nan, dtype=float)
    if curve is None:
        return out
    a = np.asarray(values, float)
    good = np.isfinite(a) & (a >= 0)
    x, y = curve["x"], curve["y"]
    mapped = np.interp(a[good], x, y)
    if x[-1] > 0:
        mapped = np.where(a[good] > x[-1], a[good] * y[-1] / x[-1], mapped)
    out[good] = np.maximum(mapped, 0)
    return out


def closed_before(rows, year):
    boundary = pd.Timestamp(f"{year}-01-01", tz="UTC")
    return (
        (rows.end_utc + pd.Timedelta(hours=12) <= boundary) & (rows.response_end_utc <= boundary)
    ).to_numpy()


def paired_summary_table(cases, predictions, years, draws):
    """Encoder, raw-data, hydrology and source contrasts use identical support."""
    from src.eo_individual_review import paired_summary

    y = predictions["observed"]
    scores = {}
    for name, p in predictions.items():
        if name == "observed":
            continue
        use = np.isfinite(p).all(1) & np.isfinite(y).all(1) & cases.outcome_valid.to_numpy(bool)
        scores[name] = np.where(use, np.abs(p - y).mean(1), np.nan)
    contrasts = [
        ("encoder_correction", "raw_correction"),
        ("raw_correction", "hydro_correction"),
        ("hydro_correction", "conventional_mean"),
        ("encoder_correction", "conventional_mean"),
        ("encoder_correction", "monthly_qm_analogue"),
        ("encoder_correction", "monthly_qm_persistence"),
        ("encoder_correction", "input_persistence"),
    ]
    records = []
    for candidate, reference in contrasts:
        for subset, mask in [
            ("all", np.ones(len(cases), bool)),
            ("high_water", cases.future_p99.eq(1).to_numpy()),
            ("verification_clean", cases.verification_clean.eq(True).to_numpy()),
            ("documented_flood", cases.documented_flood_overlap.to_numpy(bool)),
            ("NL", cases.country.eq("NL").to_numpy()),
            ("DE", cases.country.eq("DE").to_numpy()),
            (
                "mapped_targets",
                cases.local_model_reach_mapped.to_numpy(bool)
                if "local_model_reach_mapped" in cases
                else np.ones(len(cases), bool),
            ),
            (
                "encoder_supported",
                cases.encoder_available.to_numpy(bool)
                if "encoder_available" in cases
                else np.ones(len(cases), bool),
            ),
        ]:
            difference = np.where(mask, scores[candidate] - scores[reference], np.nan)
            records.append(
                dict(
                    candidate=candidate,
                    reference=reference,
                    subset=subset,
                    **paired_summary(cases, difference, years, draws),
                )
            )
    return pd.DataFrame(records)
