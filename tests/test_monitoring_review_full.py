"""Small synthetic integration fixture; never mixed with scientific scores."""

import json
import sys

import numpy as np
import pandas as pd

from src.eo_comparison import load_script
from src.monitoring_analogues import information_states


def test_complete_review_publishes_coverage_pairs_and_shared_cohorts(tmp_path, monkeypatch):
    review = load_script("155_review_monitoring_analogues.py", "monitoring_full_review_fixture")
    original_root = review.ROOT
    monkeypatch.setattr(review, "ROOT", tmp_path)
    monkeypatch.setattr(review, "OUT", tmp_path / "results/synthetic_monitoring_review")
    monkeypatch.setattr(sys, "argv", ["review-fixture"])
    review.BLOCK_UNIVERSES.clear()
    review.VERIFICATION_LABELS.clear()
    out = review.OUT
    prep = out / "preparation"
    prep.mkdir(parents=True)
    for path in ["scripts/155_review_monitoring_analogues.py", "src/monitoring_review.py"]:
        target = tmp_path / path
        target.parent.mkdir(exist_ok=True)
        target.symlink_to(original_root / path)
    dates = pd.date_range("2020-01-02", periods=4, freq="D", tz="UTC")
    n = 8
    meta = pd.DataFrame(
        {
            "case_id": [f"fixture-{i}" for i in range(n)],
            "gauge": ["n", "d"] * 4,
            "country": ["NL", "DE"] * 4,
            "storm_id": np.repeat(["a", "b", "c", "d"], 2),
            "cutoff_utc": dates.repeat(2),
            "boundary_known": [True] * n,
        }
    )
    meta.to_parquet(prep / "cases.parquet", index=False)
    aliases, states, arrays = [], [], {}
    for u in [0, 6, 12, 24]:
        arrays[f"fixed_valid_{u}"] = np.ones(n, bool)
        arrays[f"outcome_valid_{u}"] = np.ones(n, bool)
        arrays[f"outcome_{u}"] = np.ones((n, 24))
        arrays[f"rain_{u}"] = np.ones((n, 5))
        for cap, labels in information_states(u).items():
            arrays[f"q_{u}_{cap}"] = np.ones((n, 6))
            states.append((u, cap))
            aliases.extend(dict(offset_h=u, cap_h=cap, scenario=label) for label in labels)
    pd.DataFrame(aliases).to_parquet(prep / "scenario_aliases.parquet", index=False)
    np.savez_compressed(prep / "inputs.npz", **arrays)
    (prep / "manifest.json").write_text(json.dumps({"kind": "synthetic test fixture"}))
    normalizer = tmp_path / "results/storm_response/hourly_normalizer.parquet"
    normalizer.parent.mkdir(parents=True)
    pd.DataFrame(
        2.0, index=pd.date_range("2020-01-01", periods=168, freq="h", tz="UTC"), columns=["n", "d"]
    ).to_parquet(normalizer)

    def scores(baseline):
        rows = []
        roles = (
            [
                "natural_conventional",
                "fixed_conventional",
                "natural_no_season",
                "persistence",
                "generic",
            ]
            if baseline
            else ["matched_conventional", "eo_augmented"]
        )
        for case in range(n):
            for u, cap in states:
                for role in roles:
                    for k in [0] if role in ["persistence", "generic"] else [5, 10]:
                        value = 0.8 if role == "eo_augmented" else 1.0
                        rows.append(
                            dict(
                                case=case,
                                offset_h=u,
                                cap_h=cap,
                                role=role,
                                target_k=k,
                                actual_k=max(k, 1),
                                query_clean=True,
                                donors_clean=True,
                                member_ids=[0] * max(k, 1),
                                **{field: value for field in review.FIELDS},
                            )
                        )
        return pd.DataFrame(rows)

    base, eo = scores(True), scores(False)
    models = [
        "dofa",
        "croma",
        "satmae",
        "copernicus_fm",
        "terramind",
        "presto",
        "anysat",
        "galileo",
        "prithvi",
        "olmoearth",
    ]
    for pool in ["same_gauge", "other_rivers"]:
        for model, kind in [("baseline", "none")] + [
            (m, k) for m in models for k in ["recent", "monthly_snapshot"]
        ]:
            target = out / "scores" / f"{model}__{kind}__{pool}"
            target.mkdir(parents=True)
            (base if model == "baseline" else eo).to_parquet(target / "scores.parquet", index=False)
            (target / "manifest.json").write_text(
                json.dumps(
                    dict(
                        model=model,
                        kind=kind,
                        pool=pool,
                        kind_of_data="synthetic fixture, not scientific scores",
                    )
                )
            )
    (out / "execution.json").write_text(json.dumps(dict(status="completed", completed_jobs=42)))
    review.main()
    table = pd.read_parquet(out / "review/contrasts.parquet")
    assert set(table[table.population.eq("all_ten_intersection")].model) == set(models)
    assert set(table[table.population.eq("full_members_horizons")].effect) == {
        "total_h6",
        "total_h12",
        "total_h24",
    }
    assert np.allclose(table[table.effect.eq("total_vs_natural")].difference, -0.2)
    assert len(pd.read_parquet(out / "review/opportunity-ledger-same_gauge.parquet")) == 26 * n
    assert (out / "review/manifest.json").exists()
