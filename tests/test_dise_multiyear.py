"""Chronology, whole-river exclusion, test census and unchanged benchmark folds."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dise_multiyear import (
    annotate,
    assert_census,
    calibration,
    coverage,
    evaluation,
    extended_assignment,
    jobs_for,
    masks,
    split_weight_table,
)


def fixture():
    rows = []
    for gauge, group, role in [
        ("w1", "Wurm", "local"),
        ("w2", "Wurm", "local"),
        ("g", "Geul", "local"),
        ("d1", "D1", "regional_donor"),
        ("d2", "D2", "regional_donor"),
        ("e", "external:Ahr", "reserved_external"),
    ]:
        for year in range(2018, 2026):
            rows.append(
                dict(
                    gauge=gauge,
                    river_group=group,
                    source_role=role,
                    day=pd.Timestamp(f"{year}-01-01", tz="UTC"),
                    q_observed=float(year - 2017),
                    q_model=2.0,
                    clean_verification=True,
                )
            )
    return pd.DataFrame(rows)


def test_spatial_withholds_whole_river_and_all_external_labels_in_every_year():
    f = fixture()
    job = dict(id="held_Wurm_2024", year=2024, held="Wurm")
    tr, va, te, target = masks(f, job, [2021, 2022, 2023, 2024])
    assert f.loc[tr, "day"].dt.year.max() == 2022 and set(f.loc[va, "day"].dt.year) == {2023}
    assert set(f.loc[te, "gauge"]) == {"w1", "w2"}
    assert not f.loc[tr | va, "river_group"].isin(["Wurm", "external:Ahr"]).any()
    assert coverage(f, te, target, job).eligible_days.sum() == 2


def test_temporal_keeps_historical_local_labels_and_scores_external_only_through_2024():
    f = fixture()
    for year in [2024, 2025]:
        tr, va, te, _ = masks(
            f, dict(id=f"temporal_{year}", year=year, held=None), [2021, 2022, 2023, 2024]
        )
        assert "w1" in set(f.loc[tr, "gauge"]) and "e" not in set(f.loc[tr | va, "gauge"])
        assert ("e" in set(f.loc[te, "gauge"])) == (year == 2024)


def test_missing_outcomes_never_filled_and_no_verification_gauge_is_retained_in_ledger():
    f = fixture()
    f.loc[f.gauge.eq("w2") & f.day.dt.year.eq(2021), "q_observed"] = np.nan
    j = dict(id="held_Wurm_2021", year=2021, held="Wurm")
    _, _, te, targets = masks(f, j, [2021])
    ledger = coverage(f, te, targets, j).set_index("gauge")
    assert (
        ledger.loc["w2", "eligible_days"] == 0
        and ledger.loc["w2", "status"] == "no_complete_verification_pairs"
    )


def test_extension_does_not_reassign_any_original_group():
    f = fixture()
    old = {"Geul": 0, "D1": 1, "D2": 0}
    new = extended_assignment(f, old, 2, "fixed")
    assert all(new[g] == v for g, v in old.items()) and "Wurm" in new and "external:Ahr" not in new
    assert new == extended_assignment(f.sample(frac=1), old, 2, "fixed")


def test_row_weights_preserve_whole_inner_groups_and_normalization():
    f = fixture()
    j = dict(id="temporal_2021", year=2021, held=None)
    tr, va, te, _ = masks(f, j, [2021])
    assignment = {"Wurm": 0, "Geul": 1, "D1": 0, "D2": 1}
    table = split_weight_table(f, tr, va, te, assignment, 2).set_index("row_id")
    for k in range(2):
        a = table[f"inner_training_weight_{k}"].dropna()
        b = table[f"inner_validation_weight_{k}"].dropna()
        assert np.isclose(a.sum(), len(a)) and np.isclose(b.sum(), len(b))
        assert not set(f.loc[a.index, "river_group"]) & set(f.loc[b.index, "river_group"])


def test_thresholds_use_only_prior_year_observations_and_unknown_is_not_false():
    f = fixture()
    j = dict(id="held_Wurm_2024", year=2024, held="Wurm")
    _, _, te, _ = masks(f, j, [2024])
    p, a = annotate(f, f.loc[te], j)
    f.loc[f.day.dt.year.ge(2024), "q_observed"] = 1e9
    _, b = annotate(f, f.loc[te], j)
    pd.testing.assert_series_equal(a, b)
    assert p.high_water.all() and set(p.regime) == {"spatial"}


def test_fixed_population_nonfinite_prediction_is_undefined():
    f = fixture()
    p = f.loc[f.day.dt.year.eq(2021) & f.source_role.eq("local")].copy()
    p["high_water"] = True
    p["one"] = 1.0
    p["two"] = 1.0
    p["local_fdc"] = 1.0
    p.loc[p.gauge.eq("w1"), "two"] = np.nan
    records, _ = evaluation(p, ["one", "two"])
    result = {
        r["arm"]: r for r in records if r["scope"] == "local_all" and r["stratum"] == "all_days"
    }
    assert result["one"]["status"] == "defined" and result["two"]["status"] == "undefined"
    assert result["one"]["expected_gauges"] == result["two"]["expected_gauges"]


def test_queue_has_30_jobs_and_census_rejects_duplicate_predictions():
    jobs = jobs_for(
        dict(
            test_years=list(range(2021, 2026)),
            local_groups=["Wurm", "Geul", "Gulp", "Voer", "Geleenbeek"],
        )
    )
    assert len(jobs) == 30 and jobs[0]["id"] == "held_Wurm_2021"
    f = fixture().loc[lambda x: x.source_role.eq("local")].assign(regime="spatial")
    assert_census(f, len(f))
    with pytest.raises(ValueError):
        assert_census(pd.concat([f, f.iloc[:1]]), len(f) + 1)


def test_temporal_donor_cannot_select_target_or_read_its_river_labels():
    f = fixture()
    f["a_log_area"] = f.gauge.map({"w1": 1.0, "w2": 1.1, "g": 2.0, "d1": 3.0, "d2": 4.0, "e": 5.0})
    f["source_quality"] = "unknown"
    j = dict(id="temporal_2021", year=2021, held=None)
    tr, va, te, _ = masks(f, j, [2021])
    a, records = calibration(f, tr, va, te, 2021)
    for r in records:
        donor_group = f.loc[f.gauge.eq(r["donor"]), "river_group"].iloc[0]
        assert donor_group != r["excluded_target_river"]
    f.loc[f.river_group.eq("Wurm"), "q_observed"] = 1e6
    b, _ = calibration(f, tr, va, te, 2021)
    target = f.loc[te, "river_group"].eq("Wurm")
    np.testing.assert_array_equal(a.loc[target, "donor_fdc"], b.loc[target, "donor_fdc"])
