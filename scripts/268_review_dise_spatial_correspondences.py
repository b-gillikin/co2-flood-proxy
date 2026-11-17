"""Stratify spatial correspondence using held geometry/metadata only; no Q inputs."""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PROJ_DATA", str(Path(sys.base_prefix) / "share/proj"))
sys.path.insert(0, str(ROOT))

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

from src.dise_spatial import analysis_memberships, location_stratum, overlap_stratum, review_status
from src.geoglows_experiment import sha, write_json

CONFIG = ROOT / "config/limburg_dise_spatial_review_v1.json"
PLAN = json.loads(CONFIG.read_text())
OUT = ROOT / PLAN["output"]
BASE = ROOT / "data/raw/limburg_geoglows_stages12_v1"
CAMELS = ROOT / "data/raw/limburg_dise_v1/camels"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = [
        CONFIG,
        Path(__file__),
        ROOT / "src/dise_spatial.py",
        ROOT / PLAN["mapping"],
        ROOT / PLAN["candidates"],
        BASE / "streams_209.gpkg",
        BASE / "catchments_209.parquet",
        CAMELS / "CAMELS_DE_1h_catchments.gpkg",
        CAMELS / "CAMELS_DE_1h_gauging_stations.gpkg",
    ]
    pinned = {str(p.relative_to(ROOT)): sha(p) for p in files}
    ledger = pd.read_csv(ROOT / PLAN["mapping"])
    candidates = pd.read_parquet(ROOT / PLAN["candidates"])
    streams = gpd.read_file(BASE / "streams_209.gpkg").to_crs(3035).set_index("LINKNO")
    polys = (
        gpd.read_parquet(BASE / "catchments_209.parquet")
        .to_crs(3035)
        .set_index("LINKNO", drop=False)
    )
    ref = gpd.read_file(CAMELS / "CAMELS_DE_1h_catchments.gpkg").to_crs(3035).set_index("gauge_id")
    points = (
        gpd.read_file(CAMELS / "CAMELS_DE_1h_gauging_stations.gpkg")
        .to_crs(3035)
        .set_index("gauge_id")
    )
    if not polys.index.is_unique or set(polys.index) != set(streams.index):
        raise ValueError("LINKNO must join polygons and network one-to-one")
    incoming = defaultdict(list)
    for n, d in streams.DSLINKNO.items():
        incoming[int(d)].append(int(n))
    geom_cache = {}

    def upstream_geometry(node):
        if node not in geom_cache:
            seen = set()
            stack = [node]
            while stack:
                n = stack.pop()
                if n in seen:
                    continue
                seen.add(n)
                stack.extend(incoming[n])
            geom_cache[node] = unary_union(polys.loc[sorted(seen)].geometry)
        return geom_cache[node]

    records = []
    map_records = []
    for row in ledger.itertuples(index=False):
        gauge = row.gauge_id
        reference = ref.loc[gauge].geometry
        point = points.loc[gauge].geometry
        mapped = pd.notna(row.best_river_id)
        distance = float(reference.distance(point))
        overlap = overlap_stratum(
            mapped, row.dice, row.reference_covered, row.model_purity, PLAN["bands"]
        )
        location = location_stratum(distance, PLAN["bands"])
        record = dict(
            gauge_id=gauge,
            selected_river_id=int(row.best_river_id) if mapped else None,
            original_geometry_flag=bool(row.geometry_review_flag)
            if pd.notna(row.geometry_review_flag)
            else True,
            station_reference_distance_m=distance,
            reference_polygon_area_km2=reference.area / 1e6,
            reference_metadata_area_ratio=(reference.area / 1e6) / row.reference_area_km2,
            overlap_stratum=overlap,
            location_stratum=location,
            review_status=review_status(overlap, location),
        )
        record.update(analysis_memberships(mapped, row.resolved_role, overlap, location))
        possible = candidates.loc[candidates.gauge_id.eq(gauge)]
        if mapped:
            node = int(row.best_river_id)
            s = streams.loc[node]
            cell = polys.loc[node].geometry
            record["selected_incremental_cell_to_stream_distance_m"] = float(
                cell.distance(s.geometry)
            )
            record["polygon_tdx_original_id"] = int(polys.loc[node].TDXHydroLinkNo)
            # The crosswalk retains original component IDs. LINKNO, not the
            # original TDX field, joins the routed network used by this product.
            area = (
                (reference.area / 1e6) * row.reference_covered / row.model_purity
                if row.model_purity > 0
                else np.nan
            )
            record["model_polygon_area_km2"] = area
            record["model_polygon_to_reported_outlet_area_ratio"] = area / row.model_outlet_area_km2
            near = possible.loc[possible.distance_m.idxmin()] if len(possible) else None
            record["nearest_candidate_river_id"] = int(near.river_id) if near is not None else None
            record["nearest_candidate_dice"] = float(near.dice) if near is not None else None
            record["candidate_count_within_original_search"] = len(possible)
            ranked = possible.sort_values(["dice", "distance_m"], ascending=[False, True])
            record["dice_margin_to_second_candidate"] = (
                float(ranked.dice.iloc[0] - ranked.dice.iloc[1]) if len(ranked) > 1 else np.nan
            )
            if (
                record["original_geometry_flag"]
                or location == "large_station_reference_disagreement"
            ):
                model = upstream_geometry(node)
                intersection = reference.intersection(model).area
                actual = 2 * intersection / (model.area + reference.area)
                if not np.isclose(actual, row.dice, atol=1e-8):
                    raise ValueError("Reconstructed geometry changed")
                record["model_polygon_area_km2"] = model.area / 1e6
                record["model_polygon_to_reported_outlet_area_ratio"] = (
                    model.area / 1e6
                ) / row.model_outlet_area_km2
                map_records.append((row, reference, model, point, possible))
        else:
            nearest = streams.geometry.distance(point).nsmallest(1)
            record["nearest_network_river_id"] = int(nearest.index[0])
            record["nearest_network_distance_m"] = float(nearest.iloc[0])
            map_records.append((row, reference, None, point, possible))
        records.append(record)
    decisions = pd.DataFrame(records)
    joined = ledger.merge(decisions, on="gauge_id", validate="one_to_one")
    joined.to_csv(OUT / "spatial_correspondence_register.csv", index=False)
    joined.to_parquet(OUT / "spatial_correspondence_register.parquet", index=False)
    flagged = joined.loc[joined.original_geometry_flag]
    flagged.to_csv(OUT / "flagged_case_decisions.csv", index=False)
    # Reporting bands do not silently remove anyone from the acquired census.
    assert joined.include_all_mapped_census.sum() == 386
    render_maps(map_records, streams)
    views = {
        name: joined.loc[joined[col], "gauge_id"].tolist()
        for name, col in [
            ("all_mapped_census", "include_all_mapped_census"),
            ("high_overlap_sensitivity", "include_high_overlap_sensitivity"),
            (
                "high_overlap_location_consistent_sensitivity",
                "include_high_overlap_location_consistent_sensitivity",
            ),
            ("mapping_stress_stratum", "evaluate_mapping_stress_stratum"),
        ]
    }
    write_json(
        OUT / "analysis_views.json",
        dict(
            views=views,
            thresholds_are_descriptive_not_exclusion_rules=True,
            original_roles_unchanged=True,
            model_ids_unchanged=True,
        ),
    )
    receipt = dict(
        status="all_flagged_cases_reviewed_or_explicitly_stratified",
        source_hashes=pinned,
        records=len(joined),
        original_flagged_records=len(flagged),
        flagged_status_counts=flagged.review_status.value_counts().to_dict(),
        acquired_overlap_strata=joined.loc[joined.include_all_mapped_census]
        .overlap_stratum.value_counts()
        .to_dict(),
        acquired_location_strata=joined.loc[joined.include_all_mapped_census]
        .location_stratum.value_counts()
        .to_dict(),
        analysis_view_counts={n: len(v) for n, v in views.items()},
        polygon_join=dict(
            key="LINKNO",
            one_to_one=True,
            original_tdx_component_ids_differ=int(polys.LINKNO.ne(polys.TDXHydroLinkNo).sum()),
            why_not_tdx_original="Original component IDs are not routed model IDs; 17262 are absent from the routed network.",
        ),
        q_observations_or_model_performance_read=False,
        source_inputs_changed=False,
        new_model_downloads_or_fits=False,
        unresolved_cases_retained=True,
    )
    if {str(p.relative_to(ROOT)): sha(p) for p in files} != pinned:
        raise ValueError("Review source changed")
    receipt["output_hashes"] = {
        p.name: sha(p) for p in OUT.glob("*") if p.is_file() and p.name != "receipt.json"
    }
    write_json(OUT / "receipt.json", receipt)
    print(json.dumps(receipt, indent=2), flush=True)


def render_maps(records, streams):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    panels = []
    for page in range(0, len(records), 8):
        fig, axes = plt.subplots(4, 2, figsize=(16, 20))
        axes = np.asarray(axes).ravel()
        for ax, info in zip(axes, records[page : page + 8], strict=False):
            row, reference, model, point, candidates = info
            gpd.GeoSeries([reference], crs=3035).plot(
                ax=ax, facecolor="#55aa6638", edgecolor="#26713b", linewidth=1
            )
            if model is not None:
                gpd.GeoSeries([model], crs=3035).boundary.plot(ax=ax, color="#3869ba", linewidth=1)
            if len(candidates):
                streams.loc[candidates.river_id.astype(int)].plot(
                    ax=ax, color="#999999", linewidth=0.7
                )
            if pd.notna(row.best_river_id):
                gpd.GeoSeries([streams.loc[int(row.best_river_id)].geometry], crs=3035).plot(
                    ax=ax, color="#2454b4", linewidth=2
                )
            ax.scatter([point.x], [point.y], c="#b51b30", marker="*", s=65, zorder=5)
            ax.set_title(
                f"{row.gauge_id} {row.gauge_name} / {row.water_body_name}\nDice {row.dice:.3f} | station–reference {reference.distance(point):.0f} m",
                fontsize=10,
            )
            ax.set_aspect("equal")
            ax.tick_params(labelsize=6)
            ax.ticklabel_format(style="plain", useOffset=False)
        for ax in axes[len(records[page : page + 8]) :]:
            ax.axis("off")
        fig.legend(
            handles=[
                Line2D([0], [0], color="#26713b", label="Reference catchment"),
                Line2D([0], [0], color="#3869ba", label="Model upstream footprint"),
                Line2D(
                    [0],
                    [0],
                    marker="*",
                    color="#b51b30",
                    label="Provided station point",
                    linestyle="",
                ),
            ],
            loc="lower center",
            ncol=3,
        )
        fig.suptitle(
            "Spatial evidence only — original matched reaches retained; no Q outcomes inspected",
            fontsize=13,
        )
        fig.tight_layout(rect=[0, 0.025, 1, 0.97])
        p = OUT / f"flagged_atlas_{page // 8 + 1:02d}.png"
        fig.savefig(p, dpi=125)
        plt.close(fig)
        panels.append(p.name)
    write_json(
        OUT / "atlas_index.json",
        dict(
            pages=panels,
            flags=len(records),
            crs="EPSG:3035",
            no_basemap_or_river_name_validation_implied=True,
        ),
    )


if __name__ == "__main__":
    main()
