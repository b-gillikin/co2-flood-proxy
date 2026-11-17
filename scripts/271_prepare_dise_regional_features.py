"""Assemble the full regional predictor census with the validated local recipe."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.dise import feature_columns
from src.dise_regional import WEATHER, fold_assignments, gauge_features, regional_masks
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_regional_benchmark_v1.json"
PLAN = json.loads(CONFIG.read_text())
OUT = ROOT / PLAN["output"] / "preparation"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    disk_check(ROOT, PLAN["reserve_gib"], 4 * 2**30)
    start = time.monotonic()
    base = ROOT / PLAN["regional_inputs"]
    local_path = ROOT / PLAN["local_features"]
    files = [
        CONFIG,
        Path(__file__),
        ROOT / "src/dise_regional.py",
        ROOT / PLAN["spatial_register"],
        local_path,
        *[
            base / f"{n}.parquet"
            for n in ["geoglows", "weather", "alphaearth", "attributes", "observations"]
        ],
    ]
    pinned = {str(p.relative_to(ROOT)): sha(p) for p in files}
    dest = OUT / "features.parquet"
    manifest = OUT / "manifest.json"
    if manifest.exists():
        previous = json.loads(manifest.read_text())
        if previous["input_hashes"] != pinned:
            raise ValueError("Preparation inputs changed; preserve/version existing output")
        if sha(dest) != previous["feature_sha256"]:
            raise ValueError("Feature table changed")
        print("Regional features already complete and verified")
        return
    metadata = pd.read_parquet(ROOT / PLAN["spatial_register"]).set_index("gauge_id")
    metadata = metadata.loc[metadata.include_all_mapped_census]
    q = pd.read_parquet(base / "geoglows.parquet")
    w = (
        pd.read_parquet(base / "weather.parquet")
        .drop(columns="sampled_area_m2")
        .rename(columns=WEATHER)
    )
    o = pd.read_parquet(base / "observations.parquet")[
        [
            "gauge",
            "day",
            "q_observed_m3s",
            "q_observed",
            "observed_hours",
            "clean_verification",
            "source_quality",
        ]
    ]
    merged = q.merge(w, on=["gauge", "day"], validate="one_to_one").merge(
        o, on=["gauge", "day"], how="left", validate="one_to_one"
    )
    attributes = pd.read_parquet(base / "attributes.parquet").set_index("gauge")
    alpha = pd.read_parquet(base / "alphaearth.parquet").set_index("gauge")
    local = pd.read_parquet(local_path)
    local["source_role"] = "local"
    local["source_quality"] = "provider-qualified; inherited clean flag retained"
    local["overlap_stratum"] = "local_previously_reviewed_proxy"
    local["location_stratum"] = "local_location_not_reaudited"
    local["spatial_view_high_overlap"] = False
    local["spatial_view_location_consistent"] = False
    local["spatial_view_stress"] = False
    local["station"] = local.station.astype(str)
    predictors = feature_columns(local, "H+A+E")
    common = [
        "day",
        "gauge",
        "station",
        "river_group",
        "source_role",
        "source_quality",
        "reference_area_km2",
        "q_observed_m3s",
        "q_model_m3s",
        "observed_hours",
        "model_hours",
        "clean_verification",
        "q_observed",
        "q_model",
        "overlap_stratum",
        "location_stratum",
        "spatial_view_high_overlap",
        "spatial_view_location_consistent",
        "spatial_view_stress",
        *predictors,
    ]
    # A common explicit schema prevents regional unknown-QA values from becoming
    # False and prevents first-batch type inference from dropping later metadata.
    schema = pa.Schema.from_pandas(local[common], preserve_index=False)
    schema = pa.schema(
        [pa.field(f.name, pa.bool_() if f.name == "clean_verification" else f.type) for f in schema]
    )
    temporary = dest.with_suffix(".parquet.partial")
    support = []
    writer = pq.ParquetWriter(temporary, schema, compression="zstd")

    def append(f):
        table = pa.Table.from_pandas(f[common], schema=schema, preserve_index=False, safe=True)
        writer.write_table(table)
        counts = (
            f.assign(year=f.day.dt.year, paired=f.q_observed.notna() & f.q_model.notna())
            .groupby(["gauge", "river_group", "source_role", "year"])
            .agg(rows=("day", "size"), paired=("paired", "sum"))
        )
        support.append(counts.reset_index())

    try:
        append(local)
        for done, (gauge, f) in enumerate(merged.groupby("gauge", sort=True), 1):
            m = metadata.loc[gauge]
            f = gauge_features(f, m, attributes.loc[gauge], alpha.loc[gauge])
            f["station"] = m.gauge_name
            f["source_role"] = m.resolved_role
            f["river_group"] = (
                ("regional:" + str(m.topology_group))
                if m.resolved_role == "regional_donor"
                else "external:" + str(m.external_group)
            )
            f["overlap_stratum"] = m.overlap_stratum
            f["location_stratum"] = m.location_stratum
            f["spatial_view_high_overlap"] = bool(m.include_high_overlap_sensitivity)
            f["spatial_view_location_consistent"] = bool(
                m.include_high_overlap_location_consistent_sensitivity
            )
            f["spatial_view_stress"] = bool(m.evaluate_mapping_stress_stratum)
            if set(predictors) - set(f):
                raise ValueError("Regional feature recipe differs from local columns")
            append(f)
            if done % 25 == 0:
                print(f"Assembled {done}/387 regional gauges", flush=True)
    finally:
        writer.close()
    temporary.replace(dest)
    support = pd.concat(support, ignore_index=True)
    support.to_csv(OUT / "support.csv", index=False)
    # Fold construction reads only role/group metadata, never discharge values.
    groups = set(local.loc[local.river_group.ne(PLAN["withheld_local_group"]), "river_group"])
    groups.update(
        "regional:" + str(x)
        for x in metadata.loc[
            metadata.resolved_role.eq("regional_donor"), "topology_group"
        ].unique()
    )
    assignment = fold_assignments(groups, PLAN["inner_folds"], PLAN["fold_seed"])
    write_json(OUT / "inner_folds.json", assignment)
    labels = pd.read_parquet(
        dest, columns=["gauge", "day", "river_group", "source_role", "q_observed", "q_model"]
    )
    tr, va, te = regional_masks(labels, PLAN["test_year"], PLAN["withheld_local_group"])
    sizes = dict(
        train_rows=int(tr.sum()),
        validation_rows=int(va.sum()),
        test_rows=int(te.sum()),
        train_gauges=int(labels.loc[tr, "gauge"].nunique()),
        validation_gauges=int(labels.loc[va, "gauge"].nunique()),
        test_gauges=int(labels.loc[te, "gauge"].nunique()),
        external_fit_rows=int(labels.loc[tr | va, "source_role"].eq("reserved_external").sum()),
    )
    if {str(p.relative_to(ROOT)): sha(p) for p in files} != pinned:
        raise ValueError("Preparation source changed")
    write_json(
        manifest,
        dict(
            status="completed",
            input_hashes=pinned,
            feature_sha256=sha(dest),
            rows=len(labels),
            columns=len(common),
            predictors=predictors,
            support_sha256=sha(OUT / "support.csv"),
            folds_sha256=sha(OUT / "inner_folds.json"),
            sizes=sizes,
            seconds=time.monotonic() - start,
            missingness_policy=PLAN["predictor_missingness"],
            unknown_quality_not_imputed=True,
            free_gib=disk_check(ROOT, PLAN["reserve_gib"]),
        ),
    )
    print(json.dumps(sizes), flush=True)
    print("Preparation seconds", time.monotonic() - start, flush=True)


if __name__ == "__main__":
    main()
