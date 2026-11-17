"""Versioned audit corrections and physical regional screening; no full fitting."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.dise_corrected import add_climate
from src.geoglows_experiment import disk_check, sha, write_json

CONFIG = ROOT / "config/limburg_dise_v2.json"
PLAN = json.loads(CONFIG.read_text())
OUT = ROOT / PLAN["output"]
RAW = ROOT / PLAN["raw"]
OLD = ROOT / "results/limburg_dise_v1"


def features():
    source = ROOT / PLAN["input_features"]
    frame = pd.read_parquet(source)
    sites = json.loads((ROOT / PLAN["source_config"]).read_text())["sites"]
    coordinates = {s["gauge"]: s for s in sites}
    pieces, paths = [], []
    for year in PLAN["weather_years"]:
        p = RAW / "weather" / f"local_daily_{year}.parquet"
        paths.append(p)
        pieces.append(
            pd.read_parquet(p)[
                ["day", "gauge", "temperature_2m", "total_precipitation_sum"]
            ].rename(
                columns={"temperature_2m": "h_temp_k", "total_precipitation_sum": "h_precip_m"}
            )
        )
    history = pd.concat(pieces, ignore_index=True)
    history.h_precip_m = history.h_precip_m.where(history.h_precip_m.ge(0))
    result = add_climate(frame, max(PLAN["test_years"]), coordinates, history)
    # Derived quantities use only the same day's reconstruction inputs.
    result["h_wind_speed"] = np.hypot(result.h_u10, result.h_v10)
    tc, dc = result.h_temp_k - 273.15, result.h_dewpoint_k - 273.15
    result["h_relative_humidity"] = 100 * np.exp(
        17.625 * dc / (243.04 + dc) - 17.625 * tc / (243.04 + tc)
    )
    for col in ["h_wind_speed", "h_relative_humidity"]:
        block = {f"{col}_lag{k}": result.groupby("gauge")[col].shift(k) for k in range(1, 8)}
        result = pd.concat([result, pd.DataFrame(block, index=result.index)], axis=1)
    # Already-held raw-component lags provide exact first-week derived histories.
    for k in range(1, 8):
        result[f"h_wind_speed_lag{k}"] = np.hypot(result[f"h_u10_lag{k}"], result[f"h_v10_lag{k}"])
        t, d = result[f"h_temp_k_lag{k}"] - 273.15, result[f"h_dewpoint_k_lag{k}"] - 273.15
        result[f"h_relative_humidity_lag{k}"] = 100 * np.exp(
            17.625 * d / (243.04 + d) - 17.625 * t / (243.04 + t)
        )
    OUT.mkdir(parents=True, exist_ok=True)
    result.to_parquet(OUT / "local_features.parquet", index=False)
    # Regulation provenance is explicit; missing inventory is not 'no regulation'.
    topo = pd.read_csv(
        RAW / "camels/CAMELS_DE_1h_topographic_attributes.csv", dtype={"provider_id": str}
    )
    human = pd.read_csv(RAW / "camels/CAMELS_DE_1h_humaninfluence_attributes.csv")
    regulation = []
    for s in sites:
        if s["gauge"] not in set(frame.gauge):
            continue
        matches = topo.loc[topo.provider_id.eq(s["gauge"])]
        rec = dict(
            gauge=s["gauge"], status="inventory_unmatched_unknown", observed_regulation_absent=False
        )
        if len(matches) == 1:
            g = matches.iloc[0].gauge_id
            row = human.loc[human.gauge_id.eq(g)].iloc[0]
            rec.update(
                status="exact_provider_id_match_current_inventory",
                camels_id=g,
                dams_num=int(row.dams_num),
                dams_names=row.dams_names,
                first_year=row.dams_year_first,
                last_year=row.dams_year_last,
            )
        rec = {
            k: None if v is None or (isinstance(v, float) and not np.isfinite(v)) else v
            for k, v in rec.items()
        }
        regulation.append(rec)
    write_json(
        OUT / "regulation_register.json",
        dict(
            records=regulation,
            predictor_policy="Diagnostic only: database zero is not no weirs/management; historic structure dates insufficient for common predictive feature.",
        ),
    )
    write_json(
        OUT / "preparation_receipt.json",
        dict(
            status="corrected_local_features_ready",
            source_hashes={
                str(p.relative_to(ROOT)): sha(p)
                for p in [source, CONFIG, Path(__file__), ROOT / "src/dise_corrected.py", *paths]
            },
            output_sha256=sha(OUT / "local_features.parquet"),
            rows=len(result),
            climate_clock="Each row's climate context uses forcing dates strictly before Jan 1 of that row's year, including 2017 warm-up; no Q labels.",
        ),
    )
    print("Corrected features", result.shape, flush=True)


def regional_map():
    import geopandas as gpd
    from shapely.ops import unary_union

    base = ROOT / "data/raw/limburg_geoglows_stages12_v1"
    streams = gpd.read_file(base / "streams_209.gpkg").to_crs(3035).set_index("LINKNO", drop=False)
    polygons = gpd.read_parquet(base / "catchments_209.parquet").to_crs(3035).set_index("LINKNO")
    references = (
        gpd.read_file(RAW / "camels/CAMELS_DE_1h_catchments.gpkg")
        .to_crs(3035)
        .set_index("gauge_id")
    )
    stations = (
        gpd.read_file(RAW / "camels/CAMELS_DE_1h_gauging_stations.gpkg")
        .to_crs(3035)
        .set_index("gauge_id")
    )
    topo = pd.read_csv(RAW / "camels/CAMELS_DE_1h_topographic_attributes.csv").set_index("gauge_id")
    ledger = pd.read_csv(OLD / "regional_candidate_ledger.csv").set_index("gauge_id")
    ids = set(ledger.index[ledger.role.ne("outside_declared_domain")])
    named = topo.index[
        topo.water_body_name.fillna("")
        .str.casefold()
        .isin([n.casefold() for n in PLAN["external_rivers"]])
    ]
    ids.update(named)
    downstream = streams.DSLINKNO.astype(int).to_dict()
    incoming = defaultdict(list)
    for node, parent in downstream.items():
        incoming[parent].append(int(node))
    upstream_cache, geom_cache = {}, {}

    def upstream(node):
        if node not in upstream_cache:
            visited, queue = set(), [int(node)]
            while queue:
                n = queue.pop()
                if n not in visited:
                    visited.add(n)
                    queue.extend(incoming[n])
            upstream_cache[node] = visited
        return upstream_cache[node]

    def geometry(node):
        if node not in geom_cache:
            nodes = list(upstream(node) & set(polygons.index))
            geom_cache[node] = unary_union(polygons.loc[nodes].geometry)
        return geom_cache[node]

    candidates, selected = [], {}
    for count, gauge in enumerate(sorted(ids)):
        point = stations.loc[gauge].geometry
        positions = streams.sindex.query(point.buffer(2000), predicate="intersects")
        near = streams.iloc[positions]
        if near.empty:
            selected[gauge] = dict(
                gauge_id=gauge, mapping_status="no_network_within_2km", best_river_id=None
            )
            continue
        near = near.loc[near.geometry.distance(point).nsmallest(8).index]
        reference = references.loc[gauge].geometry
        entries = []
        for node, row in near.iterrows():
            geom = geometry(int(node))
            intersection = geom.intersection(reference).area
            dice = 2 * intersection / (geom.area + reference.area)
            distance = row.geometry.distance(point)
            entry = dict(
                gauge_id=gauge,
                river_id=int(node),
                distance_m=float(distance),
                dice=float(dice),
                reference_covered=float(intersection / reference.area),
                model_purity=float(intersection / geom.area),
                model_outlet_area_km2=float(row.DSContArea / 1e6),
                reported_area_km2=float(
                    ledger.loc[gauge, "reference_area_km2"]
                    if gauge in ledger.index
                    else topo.loc[gauge, "area_metadata"]
                ),
                geometry_area_km2=float(reference.area / 1e6),
            )
            entries.append(entry)
        entries.sort(key=lambda r: (-r["dice"], r["distance_m"]))
        candidates.extend(entries)
        best = entries[0]
        selected[gauge] = dict(
            best,
            best_river_id=best["river_id"],
            mapping_status="best_physical_proxy_reviewable",
            geometry_review_flag=best["dice"] < 0.8,
            selection="maximum full-upstream polygon Dice among up to 8 segments within 2 km; no Q outcomes",
        )
        if count % 40 == 0:
            print("Mapped physical candidates", count, "/", len(ids), flush=True)
    reserved = {}
    for river in PLAN["external_rivers"]:
        matches = [
            r
            for g, r in selected.items()
            if str(topo.loc[g, "water_body_name"]).casefold() == river.casefold()
            and r.get("best_river_id")
        ]
        if not matches:
            reserved[river] = dict(status="unresolved_no_mainstem_mapping")
            continue
        last = max(matches, key=lambda x: x["reported_area_km2"])
        node = last["best_river_id"]
        trace = [node]
        # Detect an obvious confluence area jump; mark its provisional character.
        while downstream.get(node) in streams.index and len(trace) < 500:
            nxt = downstream[node]
            if float(streams.loc[nxt, "DSContArea"]) > 3 * float(streams.loc[node, "DSContArea"]):
                break
            node = nxt
            trace.append(node)
        reserved[river] = dict(
            status="provisional_outlet_before_large_area_jump_reviewable",
            outlet=node,
            anchor_gauge=last["gauge_id"],
            trace=trace,
            upstream_reaches=len(upstream(node)),
        )
    local_nodes = [
        r["river_id"]
        for r in json.loads((ROOT / "config/limburg_geoglows_reaches_v1.json").read_text())
        if r["mapped"] and r["channel"] in range(1, 8)
    ]
    rows = []
    for gauge in ledger.index[ledger.role.ne("outside_declared_domain")]:
        row = {**ledger.loc[gauge].to_dict(), **selected[gauge]}
        node = row.get("best_river_id")
        row["metadata_role"] = row["role"]
        if not node:
            row["resolved_role"] = "unmapped_source_coverage"
        elif any(node in upstream(n) or n in upstream(node) for n in local_nodes):
            row["resolved_role"] = "local_connected_section_excluded"
        else:
            external = [
                name
                for name, r in reserved.items()
                if "outlet" in r
                and (node in upstream(r["outlet"]) or r["outlet"] in upstream(node))
            ]
            row["resolved_role"] = "reserved_external" if external else "regional_donor"
            row["external_group"] = "|".join(external)
        rows.append(row)
    table = pd.DataFrame(rows)
    # Group only directly overlapping upstream/downstream sections, not all
    # tributaries that eventually share a distant ocean outlet.
    parent = {g: g for g in table.gauge_id}

    def root(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    mapped = [
        (g, int(n))
        for g, n in table[["gauge_id", "best_river_id"]].itertuples(index=False, name=None)
        if pd.notna(n)
    ]
    for i, (g, n) in enumerate(mapped):
        for h, m in mapped[i + 1 :]:
            if n in upstream(m) or m in upstream(n):
                parent[root(h)] = root(g)
    table["topology_group"] = table.gauge_id.map(lambda g: root(g))
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "regional_mapping_ledger.csv", index=False)
    pd.DataFrame(candidates).to_parquet(OUT / "regional_mapping_candidates.parquet", index=False)
    write_json(
        OUT / "regional_mapping_receipt.json",
        dict(
            counts=table.resolved_role.value_counts().to_dict(),
            groups=table.groupby("resolved_role").topology_group.nunique().to_dict(),
            geometry_review_flags=int(table.geometry_review_flag.fillna(True).sum()),
            reserved=reserved,
            status="physical_proxy_register_with_explicit_review_flags_not_an_outcome_selected_cohort",
            screen_thresholds_are_flags_not_automatic_rejections=True,
            source_hashes={
                str(p.relative_to(ROOT)): sha(p)
                for p in [
                    CONFIG,
                    Path(__file__),
                    base / "streams_209.gpkg",
                    base / "catchments_209.parquet",
                    RAW / "camels/CAMELS_DE_1h_catchments.gpkg",
                ]
            },
        ),
    )
    print(table.resolved_role.value_counts().to_dict(), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["features", "regional"])
    args = parser.parse_args()
    disk_check(ROOT, PLAN["reserve_gib"])
    (features if args.phase == "features" else regional_map)()


if __name__ == "__main__":
    main()
