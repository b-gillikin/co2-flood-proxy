"""Independent review must reject leakage and preserve matched event comparisons."""

import json
import runpy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MODULE = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/120_review_eo_analogues.py")
)


def donor_fixture():
    meta = pd.DataFrame(
        {
            "event_id": ["query", "donor"],
            "onset_utc": pd.to_datetime(["2020-01-10", "2020-01-01"], utc=True),
            "storm_id": ["s2", "s1"],
            "country": ["NL", "DE"],
            "physical_river_group": ["Geul", "Wurm"],
            "measurement_concern": [False, False],
            "q_only_scoring_sample": [True, True],
        }
    ).set_index("event_id")
    frame = pd.DataFrame(
        {
            "query_event_id": ["query"],
            "analogue_event_id": ["donor"],
            "policy": ["foreign"],
            "scenario": ["other_rivers"],
            "analysis": ["quality_sensitivity"],
            "rank": [1],
            "target_k": [5],
        }
    )
    return frame, meta


@pytest.mark.parametrize(
    "field,value",
    [
        ("onset_utc", pd.Timestamp("2020-01-09", tz="UTC")),
        ("storm_id", "s2"),
        ("country", "NL"),
        ("physical_river_group", "Geul"),
        ("measurement_concern", True),
        ("q_only_scoring_sample", False),
    ],
)
def test_independent_audit_rejects_invalid_prior_evidence(field, value):
    frame, meta = donor_fixture()
    assert not any(MODULE["audit_donors"](frame, meta).values())
    meta.loc["donor", field] = value
    with pytest.raises(ValueError, match="violations"):
        MODULE["audit_donors"](frame, meta)


def test_actual_count_and_cohort_pairing_cannot_imply_a_model_gain():
    rows = []
    for cohort, arm, count, error in [
        ("same", "ttm_state", 5, 3),
        ("same", "eo", 4, 1),
        ("different", "eo", 5, 1),
        ("same", "raw_state", 5, 4),
    ]:
        row = dict.fromkeys(MODULE["KEYS"], "fixed")
        row.update(
            cohort=cohort,
            arm=arm,
            query_event_id="query",
            query_country="NL",
            query_river="Geul",
            actual_donor_count=count,
            query_measurement_concern=False,
        )
        row.update(dict.fromkeys(MODULE["METRICS"], error))
        rows.append(row)
    result = MODULE["paired_event_rows"](pd.DataFrame(rows))
    assert not result.arm.eq("eo").any()
    pair = result[result.reference.eq("ttm_state")]
    assert len(pair) == 1 and pair.iloc[0][MODULE["METRICS"][0] + "_difference"] == 1


def test_complete_review_writes_browser_tables_and_verifiable_receipt(tmp_path, monkeypatch):
    """Engineering fixture only: exercise full writer, joins, audit and HTML payload."""
    frame, meta = donor_fixture()
    meta["provider_status"] = "engineering fixture"
    ready = tmp_path / "results/basin_ai_event_interpretation_ready"
    ready.mkdir(parents=True)
    meta.to_csv(ready / "event_inventory.csv")
    response_dir = tmp_path / "results/basin_ai_event_definition_sensitivity/p99_72"
    response_dir.mkdir(parents=True)
    pd.DataFrame(np.ones((2, 72)), index=meta.index).to_parquet(
        response_dir / "response_p99.parquet"
    )
    source = tmp_path / "comparison"
    source.mkdir()
    scores, selected = [], []
    for arm in ["ttm_state", "raw_state", "prithvi_only", "prithvi_ttm_state"]:
        tags = dict(
            kind="monthly_snapshot",
            cohort="q_only_available_prithvi",
            scenario="other_rivers",
            analysis="main",
            policy="pooled",
            target_k=5,
            arm=arm,
        )
        score = dict(
            **tags,
            query_event_id="query",
            query_country="NL",
            query_river="Geul",
            query_storm_id="s2",
            actual_donor_count=1,
            query_measurement_concern=False,
        )
        score.update(dict.fromkeys(MODULE["METRICS"], 0.0))
        scores.append(score)
        selected.append(frame.assign(**tags))
    pd.DataFrame(scores).to_parquet(source / "event_assessments.parquet", index=False)
    pd.concat(selected).to_parquet(source / "selected_donors.parquet", index=False)
    digest = MODULE["sha256"]
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "input_sha256": {},
                "outputs_sha256": {p.name: digest(p) for p in source.glob("*.parquet")},
            }
        )
    )
    out = tmp_path / "review"
    monkeypatch.setitem(MODULE["main"].__globals__, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["review", "--input", str(source), "--out", str(out)])
    MODULE["main"]()
    receipt = json.loads((out / "manifest.json").read_text())
    assert receipt["assessment_rows"] == 4 and receipt["audited_donor_rows"] == 4
    assert not any(receipt["donor_violations"].values())
    for name, value in receipt["outputs_sha256"].items():
        assert digest(out / name) == value
    case = pd.read_parquet(out / "browser_case_index.parquet")
    assert case.donor_jaccard_with_ttm.eq(1).all()
    assert len(case) == 4 and all(list(v) == ["donor"] for v in case.donor_ids)
    page = (out / "monthly_snapshot.html").read_text()
    assert "engineering fixture" in page and '"donor_ids": ["donor"]' in page
