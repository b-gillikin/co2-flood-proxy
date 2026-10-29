"""Lossless final assembly of compact tile moments; shared by smoke and census."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.eo_individual_features import Moments


def assemble_features(dest, contexts, gauges, model, dimension, cached_data=None):
    records = []
    input_hashes = {}
    for context in contexts:
        cid = context["context_id"]
        groups = {}
        for path in sorted((dest / "tiles" / cid).glob("*.npz")):
            receipt = json.loads(path.with_suffix(".json").read_text())
            input_hashes.update(receipt["input_hashes"])
            with np.load(path) as data:
                for key in data.files:
                    moment = Moments.from_arrays(data[key])
                    if key not in groups:
                        groups[key] = moment
                    else:
                        groups[key].merge(moment)
        for gauge in gauges:
            gauge = str(gauge)
            record = {"context_id": cid, "catchment_gauge": gauge, "kind": context["kind"]}
            for key, moment in sorted(groups.items()):
                owner, label, ti, region = key.split("|")
                if owner != gauge:
                    continue
                values = moment.output()
                if label in ["primary", "ablation", "paired_primary"] and model != "presto":
                    values = values[: len(moment.mean)]
                for j, value in enumerate(values):
                    record[f"{label}_t{int(ti):02d}_r{region}_{j:04d}"] = value
                record[f"{label}_area_t{int(ti):02d}_r{region}"] = float(
                    moment.weight.max(initial=0)
                )
                if model == "presto" and label == "primary":
                    for j, value in enumerate(values[: len(moment.mean)]):
                        record[f"ablation_t{int(ti):02d}_r{region}_{j:04d}"] = value
            if model == "terramind":
                for region in range(4):
                    for j in range(dimension):
                        values = np.array(
                            [
                                record.get(f"primary_t{t:02d}_r{region}_{j:04d}", np.nan)
                                for t in range(4)
                            ]
                        )
                        record[f"ablation_t00_r{region}_{j:04d}"] = (
                            float(np.nanmean(values)) if np.isfinite(values).any() else np.nan
                        )
            if cached_data is not None and (cid, gauge) in cached_data.index:
                row = cached_data.loc[(cid, gauge)]
                for j, key in enumerate(
                    k for k in cached_data if k.startswith("e") and k[1:].isdigit()
                ):
                    record[f"primary_t00_r0_{j:04d}"] = row[key]
            records.append(record)
    return pd.DataFrame(records), input_hashes
