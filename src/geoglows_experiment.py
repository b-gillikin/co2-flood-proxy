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


def align_channels(frame, slots=10):
    """Channel labels are identities, not arbitrary parquet column positions."""
    if frame.columns.duplicated().any():
        raise ValueError("Duplicate discharge channel labels")
    expected = [str(i) for i in range(slots)]
    labels = [str(c) for c in frame.columns]
    if len(set(labels)) != slots or set(labels) != set(expected):
        raise ValueError("Discharge channel labels do not match the registered slots")
    result = frame.copy()
    result.columns = labels
    result = result.reindex(columns=expected)
    result.columns = range(slots)
    return result


def validate_acquisition(root, plan):
    """Verify the frozen acquisition independently of the new analysis config."""
    root = Path(root)
    raw = root / plan["raw"]
    receipt = json.loads((raw / "download_manifest.json").read_text())
    if receipt["config_sha256"] != sha(root / plan["acquisition_config"]):
        raise ValueError("Stale acquisition configuration")
    mapping_path = root / "config/limburg_geoglows_reaches_v1.json"
    if receipt["mapping_sha256"] != sha(mapping_path):
        raise ValueError("Stale acquisition reach mapping")
    if any(sha(raw / name) != digest for name, digest in receipt["outputs"].items()):
        raise ValueError("Acquisition output checksum mismatch")
    mapping = json.loads(mapping_path.read_text())
    if sorted(r["channel"] for r in mapping) != list(range(plan["legacy_input_slots"])):
        raise ValueError("Acquisition channel registry is incomplete or duplicated")
    by_channel = {r["channel"]: r for r in mapping}
    for site in plan["sites"]:
        registered = by_channel[site["channel"]]
        if not registered["mapped"] or registered["gauge"] != site["gauge"]:
            raise ValueError("Active gauge differs from the reviewed reach registry")
    hourly = align_channels(
        pd.read_parquet(raw / "hourly_discharge.parquet"), plan["legacy_input_slots"]
    )
    if (
        not hourly.index.is_unique
        or not hourly.index.is_monotonic_increasing
        or hourly.index.tz is None
        or (hourly.index != hourly.index.floor("h")).any()
    ):
        raise ValueError("Expected unique, sorted, aware UTC hourly discharge index")
    for channel, row in by_channel.items():
        if not row["mapped"]:
            if hourly[channel].notna().any():
                raise ValueError("Unmapped channel has fabricated discharge")
            continue
        path = raw / f"q_{channel:02d}_{row['river_id']}.parquet"
        site_receipt = json.loads(path.with_suffix(".json").read_text())
        if (
            site_receipt["river_id"] != row["river_id"]
            or site_receipt["sha256"] != sha(path)
            or site_receipt["timestamp_shift_hours"] != 1
        ):
            raise ValueError("Series identity or interval alignment differs from its reach receipt")
        piece = pd.read_parquet(path)
        if list(piece.columns) != [str(channel)]:
            raise ValueError("Per-reach file has the wrong channel label")
        pd.testing.assert_series_equal(
            hourly[channel],
            piece.iloc[:, 0].reindex(hourly.index),
            check_names=False,
            check_freq=False,
        )
    return hourly


def exclude_channels(bank, offsets, excluded):
    """Keep legacy slot identities, removing all information from excluded feeds."""
    result = dict(bank)
    for u in offsets:
        for prefix in ["q", "donor_q", "input_quality"]:
            key = f"{prefix}_{u}"
            value = np.array(bank[key], copy=True)
            value[:, excluded, :] = False if prefix == "input_quality" else np.nan
            result[key] = value
        for prefix in ["q_mean", "q_pairvar"]:
            key = f"{prefix}_{u}_0"
            value = np.array(bank[key], copy=True)
            value[:, excluded, :] = 0
            result[key] = value
    return result


def declared_subsets(cases):
    """Joint high-water/EO support is explicit; seven mapped targets only."""
    mapped = cases.get("local_model_reach_mapped", pd.Series(True, index=cases.index)).to_numpy(
        bool
    )
    high = cases.future_p99.eq(1).to_numpy()
    supported = cases.get("raw_available", pd.Series(True, index=cases.index)).to_numpy(
        bool
    ) & cases.get("encoder_available", pd.Series(True, index=cases.index)).to_numpy(bool)
    return {
        "all": np.ones(len(cases), bool),
        "mapped_targets": mapped,
        "high_water": high,
        "mapped_high_water": mapped & high,
        "mapped_high_water_encoder_supported": mapped & high & supported,
        "encoder_supported": supported,
        "verification_clean": cases.verification_clean.eq(True).to_numpy(),
        "documented_flood": cases.documented_flood_overlap.to_numpy(bool),
        "NL": cases.country.eq("NL").to_numpy(),
        "DE": cases.country.eq("DE").to_numpy(),
    }


def correction_modes(records, years, raw_available, eo_available):
    """Describe the exact nested hydrology -> raw -> encoder fallback policy."""
    years = np.asarray(years)
    raw_available, eo_available = np.asarray(raw_available, bool), np.asarray(eo_available, bool)
    raw = np.full(len(years), "hydro_fallback", object)
    encoded = raw.copy()
    count = np.zeros(len(years), int)
    for record in records:
        take = years == record["year"]
        count[take] = record["training"]
        use = take & raw_available
        parameter = record["raw_parameters"]
        if parameter == "baseline":
            raw[use] = "conventional"
        elif parameter != "hydro_fallback":
            raw[use] = "raw_correction"
        encoded[take] = raw[take]
        parameter = record["eo_parameters"]
        use &= eo_available
        if parameter == "baseline":
            encoded[use] = "conventional"
        elif parameter != "raw_only":
            encoded[use] = "encoder_correction" if parameter[0] > 0 else "raw_grid_correction"
    return dict(training_count=count, raw_prediction_mode=raw, encoder_prediction_mode=encoded)


def execution_status(out, plan):
    """Report actual execution separately from input-integrity readiness."""
    import fcntl

    out = Path(out)
    state_path = out / "run_state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    expected = [f"{s}__{m}" for s in plan["stages"] for m in plan["models"]]
    complete, active = [], []
    for job in expected:
        path = out / "scores" / job / "manifest.json"
        if path.exists() and json.loads(path.read_text()).get("status") == "completed":
            complete.append(job)
        stage, model = job.split("__")
        lock = out / f".{stage}_{model}.lock"
        if lock.exists():
            with lock.open("a") as stream:
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(stream, fcntl.LOCK_UN)
                except BlockingIOError:
                    active.append(job)
    controller_active = False
    lock = out / ".controller.lock"
    if lock.exists():
        with lock.open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(stream, fcntl.LOCK_UN)
            except BlockingIOError:
                controller_active = True
    launched = bool(
        state or complete or active or list((out / "baselines").glob("*/progress.json"))
    )
    review = out / "review/manifest.json"
    if active or (controller_active and state.get("status") == "running"):
        status = "running"
    elif len(complete) == len(expected):
        status = (
            "reviewed"
            if review.exists() and json.loads(review.read_text()).get("status") == "completed"
            else "completed"
        )
    elif state.get("status") in ["failed", "interrupted"]:
        status = state["status"]
    elif launched:
        status = "interrupted" if state.get("status") == "running" else "partial"
    else:
        status = "not_started"
    return dict(
        execution_status=status,
        full_analysis_launched=launched,
        completed_jobs=complete,
        expected_jobs=expected,
        active_jobs=active,
        last_error=state.get("error"),
        attempts=len(state.get("history", [])),
    )


def replace_histories(bank, hourly, epochs, offsets):
    """Replace query/donor histories and all Q normalization, preserve outcomes.

    No nearest-time match, backward fill, observed fallback or future Q allowed.
    Missing model coverage stays missing. The held donor-only causal forward
    hold convention is retained and is not a measured GEOGLOWS value.
    """
    from src.scarcity import coordinate_moments, forward_hold

    hourly = align_channels(hourly)
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
        ("encoder_correction", "conventional_median"),
        ("encoder_correction", "monthly_qm_analogue"),
        ("encoder_correction", "monthly_qm_persistence"),
        ("encoder_correction", "input_persistence"),
    ]
    records = []
    for candidate, reference in contrasts:
        for subset, mask in declared_subsets(cases).items():
            mask = mask & cases.outcome_valid.to_numpy(bool) & np.isfinite(y).all(1)
            difference = scores[candidate] - scores[reference]
            records.append(
                dict(
                    candidate=candidate,
                    reference=reference,
                    subset=subset,
                    **paired_summary(
                        cases.loc[mask], difference[mask], years, draws, fixed_population=True
                    ),
                )
            )
    return pd.DataFrame(records)
