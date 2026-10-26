"""Check exclusive model assignment and source configurations in parallel queue."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "parallel_expansion", ROOT / "scripts/132_parallel_eo_expansion.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_one_gpu_lane_and_one_cpu_extraction_lane():
    gpu, cpu = module.lanes(module.PLAN.VARIANTS)
    assert [v[0] for v in gpu] == ["satmae_toa_qa60", "croma_ascending_15", "croma_ascending_161"]
    assert [v[0] for v in cpu] == ["copernicus_fm_toa_qa60"]
    assert all(v[4] == "mps" for v in gpu)
    assert all(v[4] == "cpu" for v in cpu)


def test_duplicate_or_missing_configuration_rejected():
    with pytest.raises(ValueError):
        module.lanes(module.PLAN.VARIANTS + [module.PLAN.VARIANTS[0]])
    with pytest.raises(ValueError):
        module.lanes(module.PLAN.VARIANTS[:-1])


def test_engineering_context_uses_observed_source_window_not_fixed_months():
    contexts = [
        {
            "context_id": "old",
            "kind": "monthly_snapshot",
            "windows": [{"id": "aug2018", "start": "2018-08-01"}],
        },
        {
            "context_id": "available",
            "kind": "monthly_snapshot",
            "windows": [{"id": "jan2020", "start": "2020-01-01"}],
        },
    ]
    jobs = [{"window": {"id": "jan2020"}, "relative_path": "observed.tif"}]
    assert module.engineering_context(contexts, jobs, {"observed.tif"}) == "available"
    with pytest.raises(ValueError):
        module.engineering_context(contexts, jobs, set())
