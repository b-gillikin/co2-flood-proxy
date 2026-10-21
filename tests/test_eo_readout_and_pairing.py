import runpy
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from src.eo_comparison import load_script
from src.eo_window_diagnostics import slot_reason, support_reason

ROOT = Path(__file__).resolve().parents[1]
PAIR = runpy.run_path(str(ROOT / "scripts/102_connect_limburg_eo_experiments.py"))[
    "paired_intervals"
]


def test_slot_absence_does_not_guess_cloud_or_invent_mission_dates():
    assert slot_reason(0, 0, 0, float("nan")) == "no_catalogued_source"
    assert slot_reason(2, 1, 0, 0) == "local_files_incomplete"
    assert slot_reason(2, 2, 0, 0) == "no_valid_catchment_pixels"
    assert slot_reason(2, 2, 0, 0.001) == "observed"
    assert support_reason(["observed"] * 4, False) == "encoder_sequence_support_loss"
    assert (
        support_reason(["observed", "no_valid_catchment_pixels"], False)
        == "no_valid_catchment_pixels"
    )


def test_encoded_context_cannot_hide_a_missing_source_slot():
    with pytest.raises(ValueError, match="contradicts"):
        support_reason(["observed", "no_catalogued_source"], True)


def test_direct_conventional_pairing_uses_actual_equal_counts_and_keeps_ttm():
    evaluator = load_script("84_complete_cross_border_analogues.py", "eo_pair_test")
    # Real pairing rules; one storm/year so the scientifically undefined interval
    # is recorded explicitly rather than manufacturing independent replicates.
    evaluator.METRICS = ["error"]
    rows = []
    for arm, values, counts in [
        ("ttm_state", [4, 8], [5, 5]),
        ("conventional", [3, 6], [5, 5]),
        ("eo_only", [1, 2], [5, 4]),
    ]:
        for event, value, count in zip(["a", "b"], values, counts, strict=True):
            rows.append(
                dict(
                    kind="recent",
                    cohort="rain_matched",
                    scenario="all_rivers",
                    analysis="main",
                    policy="foreign",
                    target_k=5,
                    query_country="NL",
                    arm=arm,
                    query_event_id=event,
                    query_storm_id="one_storm",
                    query_onset_utc="2020-01-01",
                    actual_donor_count=count,
                    error=value,
                )
            )
    x = PAIR(pd.DataFrame(rows), evaluator)
    direct = x[x.reference.eq("conventional") & x.challenger.eq("eo_only")]
    assert len(direct) == 2
    assert direct.query_count.eq(1).all() and direct.difference.eq(-2).all()
    assert direct.draws.eq(0).all() and direct.lower.isna().all()
    old = x[x.reference.eq("ttm_state") & x.challenger.eq("eo_only")]
    assert old.difference.eq(-3).all()
    without_rain = PAIR(pd.DataFrame(rows).query("arm != 'conventional'"), evaluator)
    assert set(without_rain.reference) == {"ttm_state"}


def test_both_references_use_storm_and_year_cluster_intervals():
    evaluator = load_script("84_complete_cross_border_analogues.py", "eo_cluster_test")
    calls = []

    def interval(pair, unit):
        calls.append(unit)
        return dict(
            difference=pair.difference.mean(),
            lower=-1,
            upper=1,
            draws=999,
            query_count=len(pair),
            cluster_count=pair[unit].nunique(),
        )

    mock = SimpleNamespace(
        METRICS=["error"],
        paired_differences=evaluator.paired_differences,
        C=SimpleNamespace(REVIEW=SimpleNamespace(cluster_interval=interval)),
    )
    rows = []
    for arm in ["ttm_state", "conventional", "eo_only"]:
        for i, year in enumerate([2019, 2020]):
            rows.append(
                dict(
                    kind="monthly",
                    cohort="rain_matched",
                    scenario="other_rivers",
                    analysis="main",
                    policy="pooled",
                    target_k=10,
                    query_country="DE",
                    arm=arm,
                    query_event_id=str(i),
                    query_storm_id=str(i),
                    query_onset_utc=f"{year}-01-01",
                    actual_donor_count=10,
                    error=i,
                )
            )
    x = PAIR(pd.DataFrame(rows), mock)
    assert set(x.reference) == {"ttm_state", "conventional"}
    assert set(calls) == {"query_storm_id", "storm_year"}
    assert len(calls) == 8 and x.draws.eq(999).all()
