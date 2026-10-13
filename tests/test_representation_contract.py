import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_temporal_pretraining_contrast_has_identical_inputs():
    arms = {
        arm["arm_id"]: arm
        for arm in json.loads((ROOT / "docs/ai-eval/representation-arms.json").read_text())
    }
    raw = arms["R1_RAW_Q_512"]
    ttm = arms["R2_TTM_R2_Q_512"]
    for field in (
        "input_channels",
        "history_observations",
        "relative_hour_start",
        "relative_hour_end",
        "history_standardization",
        "support_unit",
    ):
        assert raw[field] == ttm[field]
    assert raw["history_observations"] == 512
    assert raw["relative_hour_end"] - raw["relative_hour_start"] + 1 == 512


def test_alphaearth_contract_uses_prior_year_supported_period_and_unit():
    arms = {
        arm["arm_id"]: arm
        for arm in json.loads((ROOT / "docs/ai-eval/representation-arms.json").read_text())
    }
    alphaearth = arms["R3_ALPHAEARTH_CONTEXT"]
    assert alphaearth["first_event_year"] == 2018
    assert alphaearth["support_unit"] == "catchment_year"
