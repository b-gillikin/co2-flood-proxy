"""Prevent incomplete experiment designs and presence-only checks becoming launch approval."""

import copy
import json
from pathlib import Path

import pytest

from src.eo_experiment_readiness import inspect_readiness, validate_plan

ROOT = Path(__file__).resolve().parents[1]


def plan():
    return json.loads((ROOT / "config/limburg_individual_encoder_experiments_v1.json").read_text())


def test_ten_complete_designs():
    validate_plan(plan())


@pytest.mark.parametrize(
    "mutation", ["duplicate", "missing_question", "encoding_unknown", "launched"]
)
def test_bad_design_is_rejected(mutation):
    p = copy.deepcopy(plan())
    if mutation == "duplicate":
        p["experiments"][0]["model"] = p["experiments"][1]["model"]
    elif mutation == "missing_question":
        p["experiments"][0]["matched_comparator"] = ""
    elif mutation == "encoding_unknown":
        p["experiments"][0]["requires_encoding"] = None
    else:
        p["status"] = "running"
    with pytest.raises(ValueError):
        validate_plan(p)


def test_receipt_presence_does_not_claim_execution(tmp_path):
    import shutil

    config = tmp_path / "config"
    config.mkdir()
    for name in ("limburg_eo_coherent_selected_runs.json", "limburg_eo_model_assets.json"):
        shutil.copy(ROOT / "config" / name, config / name)
    supplemental = config / "limburg_eo_supplemental_selected_runs"
    supplemental.mkdir()
    shutil.copy(
        ROOT / "config/limburg_eo_supplemental_selected_runs/satmae_toa_qa60.json", supplemental
    )
    future = tmp_path / "results/limburg_individual_experiments_v1/readiness"
    future.mkdir(parents=True)
    (future / "shared_backbone_validated.json").write_text("{}")
    for experiment in plan()["experiments"]:
        (future / (experiment["model"] + "_contract_and_benchmark.json")).write_text("{}")
    receipt = inspect_readiness(tmp_path, plan())
    assert receipt["launched"] is False
    assert receipt["runnable_dispatcher_implemented"] is False
    assert all(e["status"] == "preparation_needed" for e in receipt["experiments"])
    assert all(e["checks"]["new_shared_backbone_receipt_present"] for e in receipt["experiments"])
    satmae = next(e for e in receipt["experiments"] if e["model"] == "satmae")
    assert "satmae_toa_qa60" in satmae["selected_run"]


def test_support_join_does_not_count_future_or_zero_vectors(tmp_path):
    import numpy as np
    import pandas as pd

    from src.eo_event_inputs import completed_windows, context_id
    from src.eo_experiment_readiness import inspect_context_support

    cutoff = pd.Timestamp("2020-06-15T12:00:00Z")
    context = context_id("monthly", completed_windows(cutoff, "monthly"))
    cases = pd.DataFrame(
        {"cutoff_utc": [cutoff, cutoff], "catchment_gauge": ["a", "b"], "gauge": ["a", "b"]}
    )
    prep = tmp_path / "source/preparation"
    prep.mkdir(parents=True)
    cases.to_parquet(prep / "cases.parquet")
    outputs = tmp_path / "results/eo_catchment_representations/coherent_v1/selected/census"
    outputs.mkdir(parents=True)
    pd.DataFrame(
        {
            "kind": ["monthly"] * 3,
            "context_id": [context, context, "future"],
            "catchment_gauge": ["a", "b", "b"],
            "e0000": [1.0, 0.0, 9.0],
            "e0001": [2.0, 0.0, np.nan],
        }
    ).to_parquet(outputs / "presto.parquet")
    small = {"shared": {"source": "source"}, "experiments": [{"model": "presto"}]}
    out = inspect_context_support(tmp_path, small)["presto"]
    assert out["finite_nonzero_existing_vector_cases"] == 1
    assert out["unsupported_cases"] == 1
    assert out["per_site"]["b"]["supported"] == 0


@pytest.mark.parametrize(
    "defect", ["forced_eo", "hidden_outcome", "native_pooled_units", "transfer_residual"]
)
def test_audited_scientific_contract_cannot_be_removed(defect):
    p = copy.deepcopy(plan())
    if defect == "forced_eo":
        p["readout_contract"]["eo_weights"] = [0.1, 1]
    elif defect == "hidden_outcome":
        p["readout_contract"]["target_outcomes_are_predictors"] = True
    elif defect == "native_pooled_units":
        p["readout_contract"]["pooled_error_units"] = "m3/s"
    else:
        next(e for e in p["experiments"] if e["model"] == "dofa")["evaluation_overrides"].pop(
            "residual_crossfit"
        )
    with pytest.raises(ValueError):
        validate_plan(p)
