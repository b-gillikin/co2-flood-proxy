"""Task budgets include the pilot and preserve a noncompute reserve."""

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT / "infrastructure/eo_census/budget.py"))
PLAN = json.loads((ROOT / "infrastructure/eo_census/plan.json").read_text())


def test_budget_includes_pilot_and_prior_compute():
    assert PLAN["budget_usd"] == 30
    assert M["remaining_compute_usd"](PLAN) == 25
    paid = dict(PLAN, compute_spent_usd=5)
    assert M["remaining_compute_usd"](paid) == 20
    assert not M["can_start_model"](paid, None)
    assert not M["can_start_model"](paid, 40)
    assert M["can_start_model"](paid, 2)
    assert M["remaining_compute_usd"](paid, 100) == 0


def test_gpu_overlay_covers_explicit_numpy_and_keeps_live_cpu_code():
    m = runpy.run_path(str(ROOT / "infrastructure/eo_census/prepare_cloud.py"))
    original = (ROOT / "src/eo_encoders.py").read_text()
    patched = m["gpu_overlay"](original)
    compile(patched, "gpu-overlay", "exec")
    assert "torch.device(DEVICE)" in patched
    assert "loaders.build_model(name).to(DEVICE)" in patched
    assert "LIMBURG_EO_DEVICE" not in original


def test_pilot_does_not_reset_across_restarts():
    paid = dict(PLAN, compute_spent_usd=4)
    assert M["benchmark_seconds"](paid) == 1 / PLAN["azure_hourly_usd"] * 3600
    assert M["benchmark_seconds"](paid, 3) == 0
