"""Resolve the sole search-boundary case using geometry, never Q performance.

Preserve all original registers and acquired inputs. New inputs live in a
separate one-gauge supplement, joined only through the resolved mapping overlay.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))
sys.path.insert(0, str(ROOT))

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

from src.dise_acquisition import HTTPRangeFile
from src.geoglows_experiment import sha, write_json

OUT = ROOT / "results/limburg_dise_v2/spatial_review_v1"


def load_script(number, name):
    path = next((ROOT / "scripts").glob(f"{number}_*.py"))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    source = ROOT / "results/limburg_dise_v2/regional_mapping_ledger.csv"
    ledger = pd.read_csv(source)
    before = sha(source)
    pending = ledger.loc[ledger.resolved_role.eq("unmapped_source_coverage")]
    if pending.gauge_id.tolist() != ["DEA13500"]:
        raise ValueError("Extension is scoped to the documented single boundary case")
    base = ROOT / "data/raw/limburg_geoglows_stages12_v1"
    camels = ROOT / "data/raw/limburg_dise_v1/camels"
    streams = gpd.read_file(base / "streams_209.gpkg").to_crs(3035).set_index("LINKNO")
    polys = gpd.read_parquet(base / "catchments_209.parquet").to_crs(3035).set_index("LINKNO")
    reference = (
        gpd.read_file(camels / "CAMELS_DE_1h_catchments.gpkg")
        .to_crs(3035)
        .set_index("gauge_id")
        .loc["DEA13500"]
        .geometry
    )
    point = (
        gpd.read_file(camels / "CAMELS_DE_1h_gauging_stations.gpkg")
        .to_crs(3035)
        .set_index("gauge_id")
        .loc["DEA13500"]
        .geometry
    )
    incoming = defaultdict(list)
    for n, d in streams.DSLINKNO.items():
        incoming[int(d)].append(int(n))
    distance = streams.geometry.distance(point)
    candidates = []
    for node, dist in distance.loc[distance.le(5000)].items():
        seen = set()
        todo = [node]
        while todo:
            n = todo.pop()
            if n in seen:
                continue
            seen.add(n)
            todo.extend(incoming[n])
        g = unary_union(polys.loc[sorted(seen)].geometry)
        overlap = reference.intersection(g).area
        candidates.append(
            dict(
                gauge_id="DEA13500",
                river_id=int(node),
                distance_m=float(dist),
                dice=2 * overlap / (g.area + reference.area),
                reference_covered=overlap / reference.area,
                model_purity=overlap / g.area,
                model_outlet_area_km2=streams.loc[node].DSContArea / 1e6,
                geometry_area_km2=reference.area / 1e6,
                model_polygon_area_km2=g.area / 1e6,
            )
        )
    tested = pd.DataFrame(candidates).sort_values(["dice", "distance_m"], ascending=[False, True])
    tested.to_csv(OUT / "expanded_search_candidates.csv", index=False)
    best = tested.iloc[0].to_dict()
    # Retain the same highest-overlap, then distance selection used previously;
    # make the bounded radius change explicit, before opening any observations.
    matches = ledger.loc[ledger.best_river_id.eq(best["river_id"])]
    if len(matches) == 0 or not matches.resolved_role.eq("regional_donor").all():
        raise ValueError("Selected extended reach requires a fresh role/topology review")
    group = matches.topology_group.unique()
    if len(group) != 1:
        raise ValueError("Shared model reach must share one topology group")
    index = ledger.index[ledger.gauge_id.eq("DEA13500")][0]
    for key, value in best.items():
        if key in ledger:
            ledger.loc[index, key] = value
    ledger.loc[index, "best_river_id"] = int(best["river_id"])
    ledger.loc[index, "reported_area_km2"] = ledger.loc[index, "reference_area_km2"]
    ledger.loc[index, "geometry_review_flag"] = best["dice"] < 0.8
    ledger.loc[index, "resolved_role"] = "regional_donor"
    ledger.loc[index, "topology_group"] = group[0]
    ledger.loc[index, "mapping_status"] = (
        "bounded_search_extension_high_overlap_proxy_not_exact_site_validation"
    )
    ledger.loc[index, "selection"] = (
        "highest upstream-polygon Dice among every segment within 5 km, tie by distance; no Q read"
    )
    ledger.to_csv(OUT / "resolved_mapping_ledger.csv", index=False)
    ledger.loc[[index]].to_csv(OUT / "one_gauge_supplement_mapping.csv", index=False)
    decision = dict(
        status="physical_proxy_resolved_from_search_boundary",
        gauge="DEA13500",
        original_search_radius_m=2000,
        expanded_search_radius_m=5000,
        candidates_tested=len(tested),
        selected=best,
        role="regional_donor",
        topology_group=group[0],
        shared_reach_with=matches.gauge_id.tolist(),
        station_reference_distance_m=reference.distance(point),
        remaining="Moderate station/reference offset; a high-overlap proxy is not independent verification of exact gauge identity.",
        observed_Q_or_prediction_errors_used=False,
        original_mapping_sha256=before,
        executed_source_sha256=sha(Path(__file__)),
    )
    write_json(OUT / "search_boundary_resolution.json", decision)
    plan = json.loads((ROOT / "config/limburg_dise_regional_inputs_v1.json").read_text())
    plan.update(
        experiment="limburg_dise_one_gauge_spatial_supplement_v1",
        mapping="results/limburg_dise_v2/spatial_review_v1/one_gauge_supplement_mapping.csv",
        raw="data/raw/limburg_dise_v2/spatial_supplement_v1/inputs",
        output="results/limburg_dise_v2/spatial_supplement_v1/inputs",
    )
    config = ROOT / "config/limburg_dise_spatial_supplement_v1.json"
    if config.exists() and json.loads(config.read_text()) != plan:
        raise ValueError("Supplement plan changed")
    write_json(config, plan)
    # Archive-member download and clock handling reuse the already-tested source
    # reader, but retain a separate receipt instead of rewriting the 386-record audit.
    reader = load_script(266, "observations_supplement")
    reader.RAW = ROOT / "data/raw/limburg_dise_v2/spatial_supplement_v1/observations"
    reader.DAILY = ROOT / "results/limburg_dise_v2/spatial_supplement_v1/observations"
    reader.RAW.mkdir(parents=True, exist_ok=True)
    reader.DAILY.mkdir(parents=True, exist_ok=True)
    row = next(ledger.loc[[index]].itertuples(index=False))
    with HTTPRangeFile(reader.PLAN["camels_archive"]) as remote:
        with zipfile.ZipFile(remote) as archive:
            report = reader.one(archive, row, remote.etag)
    write_json(OUT / "search_boundary_observation_receipt.json", report)
    if sha(source) != before:
        raise ValueError("Original mapping changed")
    print(json.dumps(decision), flush=True)
    print("Supplement observation source acquired:", report["complete_days_2018_2024"], flush=True)


if __name__ == "__main__":
    main()
