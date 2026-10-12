import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/67_export_alphaearth_embeddings.py"
SPEC = importlib.util.spec_from_file_location("alphaearth_export", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_prior_year_rule_prevents_same_year_information():
    assert MODULE.alphaearth_year(2017) is None
    assert MODULE.alphaearth_year(2018) == 2017
    assert MODULE.alphaearth_year(2024) == 2023
    assert MODULE.alphaearth_year(2025) == 2024
    assert MODULE.alphaearth_year(2030) == 2024


def test_export_schema_has_all_embedding_dimensions_and_provenance():
    columns = MODULE.expected_output_columns()
    assert len([column for column in columns if column.startswith("A")]) == 64
    assert "embedding_year" in columns
    assert "valid_pixel_count" in columns
    assert "geometry_sha256" in columns
