#!/usr/bin/env python3
"""Validate the held AlphaEarth table and join prior-year catchment context."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alphaearth_export", ROOT / "scripts/67_export_alphaearth_embeddings.py"
)
EXPORT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(EXPORT)
BANDS = list(EXPORT.BANDS)
YEARS = list(EXPORT.YEARS)
DEFAULT_EXPORT = (
    ROOT / "data/raw/foundation_assets/alphaearth/limburg_alphaearth_catchment_year_v1.csv"
)
DEFAULT_CATCHMENTS = ROOT / "data/interim/foundation_model_catchments.gpkg"
DEFAULT_EVENTS = ROOT / "results/basin_ai_event_library/event_index.csv"
GEOMETRY_RECEIPT = ROOT / "config/alphaearth_geometry_receipt.json"
ASSETS = ROOT / "config/limburg_foundation_assets.json"
DEFAULT_OUT = ROOT / "results/basin_ai_alphaearth"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_export(
    embeddings: pd.DataFrame, catchments: pd.DataFrame, geometry_receipt: dict
) -> pd.DataFrame:
    missing = set(EXPORT.expected_output_columns()).difference(embeddings.columns)
    if missing:
        raise ValueError(f"Missing export columns: {sorted(missing)}")
    if catchments.gauge.duplicated().any():
        raise ValueError("Duplicate catchment gauge identifiers")
    table = embeddings.copy()
    table["embedding_year"] = pd.to_numeric(table.embedding_year, errors="raise")
    if table.duplicated(["gauge", "embedding_year"]).any():
        raise ValueError("Duplicate catchment-year embeddings")
    expected = {(gauge, year) for gauge in catchments.gauge for year in YEARS}
    if set(zip(table.gauge, table.embedding_year, strict=True)) != expected:
        raise ValueError("Export does not contain the fixed catchment-by-year grid")
    for column in [*BANDS, "valid_pixel_count"]:
        table[column] = pd.to_numeric(table[column], errors="raise")
    if not np.isfinite(table[[*BANDS, "valid_pixel_count"]].to_numpy()).all():
        raise ValueError("Non-finite embedding or valid-pixel values")
    if not table.valid_pixel_count.gt(0).all():
        raise ValueError("A catchment-year has no valid embedding pixels")

    source = catchments.set_index("gauge")
    receipt = pd.DataFrame(geometry_receipt["catchments"]).set_index("gauge")
    if set(receipt.index) != set(source.index):
        raise ValueError("Geometry receipt and catchment identifiers disagree")
    if not source.native_geometry_sha256.eq(receipt.native_geometry_sha256).all():
        raise ValueError("Native catchment geometry changed since the verified export")
    for column in ["gauge_name", "watercourse", "jurisdiction", "experiment_role"]:
        if not table[column].eq(table.gauge.map(source[column])).all():
            raise ValueError(f"Catchment identity mismatch in {column}")
    if not table.geometry_sha256.eq(table.gauge.map(receipt.export_geometry_sha256)).all():
        raise ValueError("Export geometry hashes disagree with the verified geometry receipt")
    table["embedding_year"] = table.embedding_year.astype("Int64")
    table["catchment_area_km2"] = table.gauge.map(source.area_km2)
    return table.sort_values(["gauge", "embedding_year"]).reset_index(drop=True)


def join_events(events: pd.DataFrame, embeddings: pd.DataFrame) -> pd.DataFrame:
    frame = events.copy()
    if frame.event_id.duplicated().any():
        raise ValueError("Duplicate event identifiers")
    frame["onset_utc"] = pd.to_datetime(frame.onset_utc, utc=True, errors="raise")
    frame["event_year"] = frame.onset_utc.dt.year
    frame["embedding_year"] = frame.event_year.map(EXPORT.alphaearth_year).astype("Int64")
    metadata = embeddings.rename(
        columns={
            "watercourse": "embedding_watercourse",
            "gauge_name": "embedding_gauge_name",
            "jurisdiction": "embedding_jurisdiction",
            "experiment_role": "embedding_experiment_role",
        }
    )
    joined = frame.merge(
        metadata, on=["gauge", "embedding_year"], how="left", validate="many_to_one"
    )
    supported = joined.embedding_year.notna()
    if joined.loc[supported, BANDS].isna().any().any():
        raise ValueError("A supported event lacks its required prior-year embedding")
    if (
        not joined.loc[supported, "watercourse"]
        .eq(joined.loc[supported, "embedding_watercourse"])
        .all()
    ):
        raise ValueError("Event and embedding watercourse identifiers disagree")
    joined["embedding_status"] = np.where(supported, "joined", "outside_embedding_period")
    joined["common_representation_sample"] = (
        joined.primary_usable
        & joined.history_discharge_fraction.eq(1)
        & joined.history_rainfall_fraction.eq(1)
        & joined.history_weather_fraction.eq(1)
    )
    joined["alphaearth_input_sample"] = supported & joined.common_representation_sample
    joined["alphaearth_scoring_sample"] = (
        joined.alphaearth_input_sample & joined.outcome_discharge_fraction.eq(1)
    )
    return joined.sort_values(["onset_utc", "gauge"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--catchments", type=Path, default=DEFAULT_CATCHMENTS)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    assets = json.loads(ASSETS.read_text())
    if sha256(args.export) != assets["alphaearth"]["delivery"]["sha256"]:
        raise ValueError("Export bytes differ from the validated delivery receipt")
    catchments = gpd.read_file(args.catchments)
    receipt = json.loads(GEOMETRY_RECEIPT.read_text())
    if str(catchments.crs) != receipt["source_crs"]:
        raise ValueError("Catchment CRS differs from the geometry receipt")
    catchments["native_geometry_sha256"] = catchments.geometry.map(EXPORT.geometry_hash)
    embeddings = validate_export(pd.read_csv(args.export), catchments, receipt)
    joined = join_events(pd.read_csv(args.events), embeddings)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    embeddings.to_parquet(args.output_dir / "catchment_year_embeddings.parquet", index=False)
    joined.to_parquet(args.output_dir / "event_embeddings.parquet", index=False)
    counts = joined.groupby(["gauge", "watercourse", "event_year"], as_index=False).agg(
        event_count=("event_id", "size"),
        joined_count=("embedding_year", "count"),
        input_sample_count=("alphaearth_input_sample", "sum"),
        scoring_sample_count=("alphaearth_scoring_sample", "sum"),
    )
    counts.to_csv(args.output_dir / "event_join_counts.csv", index=False)
    manifest = {
        "status": "prior-year AlphaEarth context joined; no context-effect model evaluated",
        "time_rule": assets["alphaearth"]["primary_time_rule"],
        "export_rows": len(embeddings),
        "catchment_count": embeddings.gauge.nunique(),
        "embedding_dimensions": len(BANDS),
        "event_count": len(joined),
        "embedding_status_counts": joined.embedding_status.value_counts().to_dict(),
        "complete_input_events": int(joined.alphaearth_input_sample.sum()),
        "complete_outcome_events": int(joined.alphaearth_scoring_sample.sum()),
        "sample_watercourses": sorted(
            joined.loc[joined.alphaearth_input_sample, "watercourse"].unique()
        ),
        "geometry_check": "native geometry and original-export WGS84 hashes match the verified receipt",
        "original_export_projection_version": receipt["projection_version"],
        "input_sha256": {
            "export": sha256(args.export),
            "catchments": sha256(args.catchments),
            "events": sha256(args.events),
            "geometry_receipt": sha256(GEOMETRY_RECEIPT),
            "assets_contract": sha256(ASSETS),
            "importer_code": sha256(Path(__file__)),
            "exporter_code": sha256(ROOT / "scripts/67_export_alphaearth_embeddings.py"),
        },
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
