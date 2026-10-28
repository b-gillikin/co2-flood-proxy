"""Prepare held histories, prior-only calibration and coherent scarcity masks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import load_script
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.scarcity import (
    SCORE_FIELDS,
    batch_scores,
    coordinate_moments,
    forward_hold,
    mask_series,
    rain_histories,
    scenario_groups,
)

CONFIG = ROOT / "config/limburg_scarcity_v1.json"


def main():
    config = json.loads(CONFIG.read_text())
    output = ROOT / config["output"] / "preparation"
    source = ROOT / config["source_preparation"]
    inputs = {}

    def bind(path):
        p = ROOT / path
        inputs[str(p.relative_to(ROOT))] = sha256(p)
        return p

    meta = pd.read_parquet(bind(source.relative_to(ROOT) / "cases.parquet"))
    old = dict(np.load(bind(source.relative_to(ROOT) / "inputs.npz")))
    raw_q = pd.read_parquet(bind("results/storm_response/hourly_discharge.parquet"))
    rain = pd.read_parquet(bind("results/storm_response/hourly_rainfall.parquet"))
    strict = pd.read_parquet(bind("results/storm_response/hourly_strict.parquet")).fillna(False)
    domain = pd.read_parquet(bind("results/storm_response/hourly_domain.parquet")).fillna(False)
    if not raw_q.index.equals(rain.index):
        raise ValueError("Shared UTC hour-end source axis required")
    gauges = list(raw_q.columns)
    n = len(meta) // 8
    if len(gauges) != 8 or len(meta) != 8 * n:
        raise ValueError("Expected eight fixed response targets, not a sampled subset")
    if not np.array_equal(meta.gauge.to_numpy().reshape(n, 8), np.tile(gauges, (n, 1))):
        raise ValueError("Case order must retain all target gauges for each storm")
    storms = meta.iloc[::8].reset_index(drop=True)
    cutoff = storms.cutoff_utc.dt.as_unit("ns").astype("int64").to_numpy()
    end = storms.end_utc.dt.as_unit("ns").astype("int64").to_numpy()
    hour = pd.Timedelta(hours=1).value
    epochs = raw_q.index.as_unit("ns").asi8 // hour
    positions = raw_q.index.get_indexer(storms.cutoff_utc)
    combined = raw_q.copy()
    quality = strict & domain
    for site in config["maas_sources"]:
        frame = pd.read_parquet(bind(f"results/meuse_context_2026_10_27/{site}_hourly.parquet"))
        combined[site] = frame.q_strict.reindex(raw_q.index)
        quality[site] = combined[site].notna()
    sources = [
        CONFIG,
        Path(__file__),
        ROOT / "src/scarcity.py",
        ROOT / "scripts/154_run_monitoring_analogues.py",
        ROOT / "docs/limburg-scarcity-executable-protocol-2026-10-28.md",
    ]
    for p in sources:
        bind(p.relative_to(ROOT))
    runner = load_script("154_run_monitoring_analogues.py", "scarcity_held_eo")
    representations = []
    vectors = []
    for model in config["eo_models"]:
        for kind in config["eo_readouts"]:
            x, valid, path = runner.eo_features(meta, model, kind)
            bind(path.relative_to(ROOT))
            representations.append(dict(model=model, kind=kind))
            vectors.append((x.reshape(n, 8, -1), valid.reshape(n, 8)))
    if output.exists():
        saved = json.loads((output / "manifest.json").read_text())
        if saved["sources_sha256"] != inputs:
            raise ValueError(
                "Existing preparation differs: version a new output instead of overwriting"
            )
        for name, digest in saved["outputs_sha256"].items():
            if sha256(output / name) != digest:
                raise ValueError("Prepared input hash changed")
        print("Reusing identical prepared scarcity inputs", flush=True)
        return
    with fresh_output(output) as work:
        groups = scenario_groups(config)
        (work / "groups.json").write_text(json.dumps(groups, indent=2) + "\n")
        (work / "config.json").write_text(json.dumps(config, indent=2) + "\n")
        meta.to_parquet(work / "cases.parquet", index=False)
        storms.to_parquet(work / "storms.parquet", index=False)
        np.save(work / "source_epoch_hours.npy", epochs)
        arrays = {}
        h = config["q_history_h"]
        raw = combined.to_numpy(float)
        good = quality.to_numpy(bool)
        rain_raw = rain.to_numpy(float)
        similarity = np.lib.format.open_memmap(
            work / "eo_distance.npy", mode="w+", dtype="float64", shape=(len(vectors), 8, n, n)
        )
        arrays["eo_valid"] = np.stack([valid for _, valid in vectors])
        for j, (x, _) in enumerate(vectors):
            for gi in range(8):
                xx = np.nan_to_num(x[:, gi])
                similarity[j, gi] = np.maximum(2 - 2 * (xx @ xx.T), 0)
        similarity.flush()
        del similarity
        for u in config["issue_offsets_h"]:
            pos = positions + u
            if (pos >= len(raw)).any() or (pos - h + 1 < 0).any():
                raise ValueError("Issue/history outside held source time axis")
            history_positions = pos[:, None] - h + 1 + np.arange(h)
            observed = raw[history_positions].transpose(0, 2, 1)
            donor = forward_hold(observed)
            arrays[f"q_{u}"] = observed
            arrays[f"donor_q_{u}"] = donor
            arrays[f"input_quality_{u}"] = good[history_positions].transpose(0, 2, 1)
            arrays[f"positions_{u}"] = history_positions
            arrays[f"outcome_{u}"] = old[f"outcome_{u}"].reshape(n, 8, 24)
            arrays[f"outcome_quality_{u}"] = old[f"quality_{u}"].reshape(n, 8)
            arrays[f"outcome_valid_{u}"] = old[f"outcome_valid_{u}"].reshape(n, 8)
            day = (storms.cutoff_utc + pd.Timedelta(hours=u)).dt.dayofyear.to_numpy()
            season = np.stack(
                [np.sin(2 * np.pi * day / 365.25), np.cos(2 * np.pi * day / 365.25)], axis=-1
            )
            for period in config["sampling_hours"]:
                for phase in range(period):
                    values, ages = rain_histories(rain_raw, epochs, pos, period, phase)
                    values = np.concatenate(
                        [values, np.broadcast_to(season[:, None], (n, 8, 2))], axis=-1
                    )
                    arrays[f"rain_{u}_{period}_{phase}"] = values
                    arrays[f"rain_age_{u}_{period}_{phase}"] = ages
            full_rain = arrays[f"rain_{u}_1_0"]
            for years in [0, *config["historical_caps_years"]]:
                prior = cutoff[:, None] >= cutoff[None] + 24 * hour
                prior &= end[None] + 12 * hour <= cutoff[:, None] + u * hour
                prior &= storms.storm_id.to_numpy()[:, None] != storms.storm_id.to_numpy()[None]
                if years:
                    earliest = storms.cutoff_utc.map(lambda t, y=years: t - pd.DateOffset(years=y))
                    earliest = earliest.dt.as_unit("ns").astype("int64").to_numpy()
                    prior &= cutoff[None] >= earliest[:, None]
                key = f"{u}_{years}"
                arrays[f"prior_{key}"] = prior
                mean, var = coordinate_moments(prior, donor)
                arrays[f"q_mean_{key}"] = mean
                arrays[f"q_pairvar_{key}"] = 2 * var
                mean, var = coordinate_moments(prior, full_rain)
                arrays[f"rain_mean_{key}"] = mean
                arrays[f"rain_var_{key}"] = var
                pair = np.ones((len(vectors), 8, n))
                for j, (x, valid) in enumerate(vectors):
                    for gi in range(8):
                        p = prior & valid[:, gi][None]
                        count = p.sum(axis=1)
                        means = np.divide(
                            p.astype(float) @ np.nan_to_num(x[:, gi]),
                            count[:, None],
                            out=np.zeros((n, x.shape[-1])),
                            where=count[:, None] > 0,
                        )
                        variance = np.maximum(1 - (means * means).sum(axis=1), 0)
                        v = np.divide(
                            2 * count * variance, count - 1, out=np.ones(n), where=count > 1
                        )
                        pair[j, gi] = np.where(v > 1e-14, v, 1)
                arrays[f"eo_pair_{key}"] = pair
                generic = np.full((n, 8, len(SCORE_FIELDS)), np.nan)
                generic_count = np.zeros((n, 8), int)
                for qi in range(n):
                    for gi in range(8):
                        if not arrays[f"outcome_valid_{u}"][qi, gi]:
                            continue
                        ids = np.flatnonzero(prior[qi] & arrays[f"outcome_valid_{u}"][:, gi])
                        generic_count[qi, gi] = len(ids)
                        if len(ids):
                            generic[qi, gi] = batch_scores(
                                arrays[f"outcome_{u}"][qi, gi],
                                arrays[f"outcome_{u}"][:, gi],
                                ids[None],
                            )[0][0]
                arrays[f"generic_{key}"] = generic
                arrays[f"generic_count_{key}"] = generic_count
            print(f"prepared issue +{u}h", flush=True)
        np.savez_compressed(work / "bank.npz", **arrays)
        fractions = config["missing_fractions"][1:-1]
        for code, mean_run in enumerate([None, *config["block_mean_hours"]]):
            pattern = "scattered" if mean_run is None else f"block_{mean_run}h"
            hidden = mask_series(
                len(raw_q),
                config["mask_replicas"],
                8,
                fractions,
                seed=config["seed"] + code * 100003,
                mean_run=mean_run,
            )
            for j, fraction in enumerate(fractions):
                name = f"{pattern}_{int(fraction * 100)}pct"
                np.save(work / (name + ".npy"), np.packbits(hidden[j], axis=-1))
            del hidden
            print("prepared coherent masks", pattern, flush=True)
        report = dict(
            status="prepared",
            storms=n,
            gauges=8,
            cases=len(meta),
            groups=len(groups),
            jobs=4 * len(groups),
            representations=representations,
            sources_sha256=inputs,
            outputs_sha256={
                str(p.relative_to(work)): sha256(p) for p in work.iterdir() if p.is_file()
            },
            note="No performance result. Original verification is separate from all masks; finalized earlier donor inputs retained, projected onto current query coordinates.",
        )
        (work / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({k: report[k] for k in ["status", "storms", "cases", "groups", "jobs"]}),
        flush=True,
    )


if __name__ == "__main__":
    main()
