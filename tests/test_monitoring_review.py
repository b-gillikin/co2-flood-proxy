"""Independent weighting, shared resampling and baseline-fallback checks."""

import numpy as np
import pandas as pd
import pytest

from src.eo_comparison import load_script
from src.monitoring_review import mean_estimate, paired_interval


def test_equal_gauge_issue_weight_does_not_reward_many_available_cases():
    f = pd.DataFrame(
        {
            "gauge": ["a"] * 3 + ["b"],
            "offset_h": [0] * 4,
            "case": [0, 1, 2, 3],
            "effect": [0.0, 0.0, 0.0, 4.0],
        }
    )
    assert mean_estimate(f, "effect") == pytest.approx(2.0)


def test_paired_constant_effect_interval_and_shared_universe():
    f = pd.DataFrame(
        {
            "gauge": ["a"] * 4,
            "offset_h": [0, 6, 0, 6],
            "case": [0, 0, 1, 1],
            "storm": ["a", "a", "b", "b"],
            "effect": [2.0] * 4,
        }
    )
    out = paired_interval(f, "effect", "storm", draws=99, block_universe=["a", "b"])
    assert out["lower"] == out["upper"] == 2.0
    assert out["blocks"] == 2 and out["finite_draws"] == 99
    assert paired_interval(f, "effect", "storm", draws=99) == out
    with pytest.raises(ValueError):
        paired_interval(f, "effect", "storm", block_universe=["a"])


def test_undefined_bootstrap_draws_are_recorded_not_dropped():
    f = pd.DataFrame(
        {
            "gauge": ["a", "a"],
            "offset_h": [0, 0],
            "case": [0, 1],
            "storm": ["a", "b"],
            "effect": [1.0, 2.0],
        }
    )
    out = paired_interval(f, "effect", "storm", draws=999, block_universe=list("abcdefghij"))
    assert out["finite_draws"] < 999 and np.isnan(out["lower"])
    one = paired_interval(f.iloc[:1], "effect", "storm", block_universe=list("abcdefghij"))
    assert one["blocks"] == 1 and one["universe_blocks"] == 10 and one["draws"] == 0


def test_fallback_preserves_observed_zero_and_natural_comparison_priority():
    review = load_script("155_review_monitoring_analogues.py", "monitoring_fallback_test")
    rows = []
    for role, k, value in [
        ("persistence", 0, 0.0),
        ("generic", 0, 7.0),
        ("natural_conventional", 5, 2.0),
        ("natural_conventional", 10, 3.0),
        ("fixed_conventional", 5, 4.0),
        ("fixed_conventional", 10, 5.0),
    ]:
        rows.append(
            dict(
                case=0,
                offset_h=0,
                cap_h=0,
                target_k=k,
                role=role,
                actual_k=max(k, 1),
                query_clean=True,
                donors_clean=True,
                member_ids=[0],
                **{field: value for field in review.FIELDS},
            )
        )
    _, _, _, ref = review.references(pd.DataFrame(rows), None, None, None)
    assert ref.reference_crps_specific.tolist() == [2.0, 3.0]
    only_fallback = pd.DataFrame(rows)
    only_fallback = only_fallback[only_fallback.role.isin(["persistence", "generic"])]
    _, _, _, ref = review.references(only_fallback, None, None, None)
    assert ref.reference_crps_specific.tolist() == [0.0, 0.0]


def test_opportunity_ledger_keeps_missing_states_and_deduplicates_aliases():
    review = load_script("155_review_monitoring_analogues.py", "monitoring_ledger_test")
    meta = pd.DataFrame(
        {
            "case_id": ["a", "b", "c"],
            "gauge": ["g"] * 3,
            "country": ["NL"] * 3,
            "storm_id": ["a", "b", "c"],
        }
    )
    aliases = pd.DataFrame({"offset_h": [0, 0], "cap_h": [0, 0], "scenario": ["delay_0", "outage"]})
    q = np.zeros((3, 6))
    q[2, 1] = np.nan
    arrays = {
        "outcome_valid_0": np.array([True, False, True]),
        "q_0_0": q,
        "rain_0": np.zeros((3, 5)),
        "fixed_valid_0": np.array([True, False, False]),
    }
    base = pd.DataFrame(
        [
            dict(case=0, offset_h=0, cap_h=0, role="natural_conventional", target_k=5, actual_k=5),
            dict(case=2, offset_h=0, cap_h=0, role="persistence", target_k=0, actual_k=1),
        ]
    )
    ledger = review.opportunity_ledger(meta, aliases, arrays, base)
    assert len(ledger) == 3
    assert ledger.conventional_status.tolist() == [
        "full_five_members",
        "unscored_missing_verification",
        "unavailable_input_history",
    ]
    assert ledger.any_reference.tolist() == [True, False, True]
