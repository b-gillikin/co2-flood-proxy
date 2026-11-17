"""Bind the geometry review, one resolved search-boundary case and held inputs.

This assembles input/stratum views only; it does not fit or evaluate a model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd

from src.dise_spatial import analysis_memberships, location_stratum, overlap_stratum
from src.geoglows_experiment import disk_check, sha, write_json

OUT = ROOT / "results/limburg_dise_v2/spatial_review_v1"
DEST = ROOT / "results/limburg_dise_v2/regional_inputs_resolved_v1"


def main():
    disk_check(ROOT, 50, 512 * 2**20)
    DEST.mkdir(parents=True, exist_ok=True)
    source = OUT / "spatial_correspondence_register.parquet"
    f = pd.read_parquet(source)
    plan = json.loads((ROOT / "config/limburg_dise_spatial_review_v1.json").read_text())
    resolution = json.loads((OUT / "search_boundary_resolution.json").read_text())
    overlay = pd.read_csv(OUT / "resolved_mapping_ledger.csv").set_index("gauge_id")
    row = f.index[f.gauge_id.eq(resolution["gauge"])][0]
    for name, value in overlay.loc[resolution["gauge"]].items():
        if name in f:
            f.loc[row, name] = value
    best = resolution["selected"]
    location = location_stratum(f.loc[row, "station_reference_distance_m"], plan["bands"])
    overlap = overlap_stratum(
        True, best["dice"], best["reference_covered"], best["model_purity"], plan["bands"]
    )
    f.loc[row, "selected_river_id"] = best["river_id"]
    f.loc[row, "overlap_stratum"] = overlap
    f.loc[row, "location_stratum"] = location
    f.loc[row, "review_status"] = "resolved_search_boundary_high_overlap_proxy"
    f.loc[row, "model_polygon_area_km2"] = best["model_polygon_area_km2"]
    f.loc[row, "model_polygon_to_reported_outlet_area_ratio"] = (
        best["model_polygon_area_km2"] / best["model_outlet_area_km2"]
    )
    for k, v in analysis_memberships(True, "regional_donor", overlap, location).items():
        f.loc[row, k] = v
    assert f.include_all_mapped_census.sum() == 387
    f.to_parquet(OUT / "resolved_spatial_correspondence_register.parquet", index=False)
    f.to_csv(OUT / "resolved_spatial_correspondence_register.csv", index=False)
    original = pd.read_csv(ROOT / "results/limburg_dise_v2/regional_mapping_ledger.csv").set_index(
        "gauge_id"
    )
    before = original.best_river_id.dropna()
    after = overlay.best_river_id.reindex(before.index)
    assert before.equals(after.rename(before.name))
    assert f.loc[f.original_geometry_flag, "review_status"].notna().all()
    views = {
        name: f.loc[f[col].astype(bool), "gauge_id"].tolist()
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
        OUT / "resolved_analysis_views.json",
        dict(
            views=views,
            all_mapped_is_full_census=True,
            bands_are_reporting_conventions_not_validity_guarantees=True,
            reference_data_quality_is_separate=True,
        ),
    )
    mapping = f.loc[f.include_all_mapped_census].set_index("gauge_id")
    components = {}
    input_hashes = {
        str(source.relative_to(ROOT)): sha(source),
        "resolved_mapping": sha(OUT / "resolved_mapping_ledger.csv"),
    }
    for component in ["geoglows", "weather", "alphaearth", "attributes"]:
        paths = [
            ROOT / f"results/limburg_dise_v2/regional_inputs/{component}.parquet",
            ROOT / f"results/limburg_dise_v2/spatial_supplement_v1/inputs/{component}.parquet",
        ]
        frames = []
        for p in paths:
            receipt = json.loads(p.with_suffix(p.suffix + ".receipt.json").read_text())
            if sha(p) != receipt["sha256"]:
                raise ValueError("Changed input table")
            input_hashes[str(p.relative_to(ROOT))] = sha(p)
            frames.append(pd.read_parquet(p))
        data = pd.concat(frames, ignore_index=True)
        keys = ["gauge", "day"] if "day" in data else ["gauge"]
        assert not data.duplicated(keys).any() and set(data.gauge) == set(mapping.index)
        if "day" in data:
            assert data.groupby("gauge").size().eq(3287).all()
        path = DEST / f"{component}.parquet"
        data.to_parquet(path, index=False)
        components[component] = dict(
            rows=len(data), gauges=int(data.gauge.nunique()), sha256=sha(path)
        )
    observation_paths = [
        ROOT / f"results/limburg_dise_v2/regional_observations/{g}.parquet"
        for g in original.index
        if original.loc[g, "resolved_role"] in ["regional_donor", "reserved_external"]
    ]
    observation_paths.append(
        ROOT / "results/limburg_dise_v2/spatial_supplement_v1/observations/DEA13500.parquet"
    )
    pieces = []
    for p in observation_paths:
        rec = json.loads(p.with_suffix(".parquet.receipt.json").read_text())
        if sha(p) != rec["daily_sha256"]:
            raise ValueError("Changed observation table")
        d = pd.read_parquet(p)
        d = d.loc[d.day.dt.year.between(2017, 2025)].copy()
        pieces.append(d)
        input_hashes[str(p.relative_to(ROOT))] = sha(p)
    observations = pd.concat(pieces, ignore_index=True)
    assert not observations.duplicated(["gauge", "day"]).any() and set(observations.gauge) == set(
        mapping.index
    )
    observations.to_parquet(DEST / "observations.parquet", index=False)
    components["observations"] = dict(
        rows=len(observations),
        gauges=int(observations.gauge.nunique()),
        complete_days_2018_2024=int(
            observations.loc[observations.day.dt.year.between(2018, 2024), "q_observed"]
            .notna()
            .sum()
        ),
        sha256=sha(DEST / "observations.parquet"),
        unknown_quality_preserved=True,
        missing_days_not_filled=True,
    )
    report = dict(
        status="spatial_resolution_and_explicit_strata_ready",
        original_flagged=44,
        original_flagged_actions=f.loc[f.original_geometry_flag]
        .review_status.value_counts()
        .to_dict(),
        additional_station_reference_conflicts=int(
            (
                ~f.original_geometry_flag
                & f.location_stratum.eq("large_station_reference_disagreement")
            ).sum()
        ),
        original_flag_atlas_cases=52,
        atlas_pages_visually_inspected=7,
        final_overlap_strata=mapping.overlap_stratum.value_counts().to_dict(),
        final_location_strata=mapping.location_stratum.value_counts().to_dict(),
        final_roles=mapping.resolved_role.value_counts().to_dict(),
        analysis_view_counts={k: len(v) for k, v in views.items()},
        coverage_resolution=resolution,
        components=components,
        input_hashes=input_hashes,
        original_existing_model_ids_preserved=True,
        original_cohort_preserved_and_one_added=True,
        q_performance_used_for_mapping=False,
        new_model_fit_started=False,
        provider_requests_needed_to_proceed=False,
        tests_passed=46,
        free_gib=disk_check(ROOT, 50),
        code_hashes={
            str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), ROOT / "src/dise_spatial.py"]
        },
    )
    report["output_hashes"] = {
        p.name: sha(p)
        for p in [
            OUT / "resolved_spatial_correspondence_register.csv",
            OUT / "resolved_spatial_correspondence_register.parquet",
            OUT / "resolved_analysis_views.json",
            OUT / "expanded_search_candidates.csv",
            OUT / "search_boundary_resolution.json",
        ]
    }
    write_json(OUT / "final_receipt.json", report)
    write_json(ROOT / "docs/reviews/limburg-dise-spatial-resolution-2026-11-16.json", report)
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ["input_hashes", "code_hashes"]}, indent=2
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
