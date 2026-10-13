import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alphaearth_import", ROOT / "scripts/68_import_alphaearth_embeddings.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def export_fixture():
    catchments = pd.DataFrame(
        [
            {
                "gauge": "g1",
                "gauge_name": "Gauge 1",
                "watercourse": "river",
                "jurisdiction": "NL",
                "experiment_role": "core_dutch",
                "native_geometry_sha256": "native",
                "area_km2": 10.0,
            }
        ]
    )
    receipt = {
        "catchments": [
            {
                "gauge": "g1",
                "native_geometry_sha256": "native",
                "export_geometry_sha256": "exported",
            }
        ]
    }
    rows = []
    for year in MODULE.YEARS:
        rows.append(
            {
                "gauge": "g1",
                "gauge_name": "Gauge 1",
                "watercourse": "river",
                "jurisdiction": "NL",
                "experiment_role": "core_dutch",
                "embedding_year": year,
                "valid_pixel_count": 10,
                "geometry_sha256": "exported",
                **dict.fromkeys(MODULE.BANDS, float(year)),
            }
        )
    return pd.DataFrame(rows), catchments, receipt


def test_join_uses_prior_year_and_retains_unsupported_events():
    export, catchments, receipt = export_fixture()
    embeddings = MODULE.validate_export(export, catchments, receipt)
    events = pd.DataFrame(
        [
            {
                "event_id": str(year),
                "gauge": "g1",
                "watercourse": "river",
                "onset_utc": f"{year}-06-01T00:00:00Z",
                "primary_usable": True,
                "history_discharge_fraction": 1.0,
                "history_rainfall_fraction": 1.0,
                "history_weather_fraction": 1.0,
                "outcome_discharge_fraction": 1.0,
            }
            for year in [2017, 2018, 2024, 2025]
        ]
    )
    joined = MODULE.join_events(events, embeddings).set_index("event_id")
    assert joined.loc["2017", "embedding_status"] == "outside_embedding_period"
    assert not joined.loc["2017", "alphaearth_input_sample"]
    assert pd.isna(joined.loc["2017", "A00"])
    for year, prior in [(2018, 2017), (2024, 2023), (2025, 2024)]:
        assert joined.loc[str(year), "embedding_year"] == prior
        assert joined.loc[str(year), "A00"] == prior
        assert joined.loc[str(year), "alphaearth_scoring_sample"]


@pytest.mark.parametrize(
    "corruption", ["geometry", "identity", "native_geometry", "duplicate", "missing_band"]
)
def test_export_rejects_inapplicable_geometry_identity_or_incomplete_context(corruption):
    export, catchments, receipt = export_fixture()
    if corruption == "geometry":
        export.loc[0, "geometry_sha256"] = "other"
    elif corruption == "identity":
        export.loc[0, "watercourse"] = "other river"
    elif corruption == "native_geometry":
        catchments.loc[0, "native_geometry_sha256"] = "changed"
    elif corruption == "duplicate":
        export = pd.concat([export, export.iloc[[0]]], ignore_index=True)
    else:
        export.loc[0, "A63"] = np.nan
    with pytest.raises(ValueError):
        MODULE.validate_export(export, catchments, receipt)
