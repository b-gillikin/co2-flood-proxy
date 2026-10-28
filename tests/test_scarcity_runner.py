"""Small synthetic census through every scorer/control, not research sampling."""

import json
import sys

import numpy as np
import pandas as pd

from src.eo_comparison import load_script
from src.monitoring_analogues import ensemble_metrics
from src.scarcity import batch_scores, coordinate_moments, forward_hold, mask_series, scenario_keep


def test_full_runner_keeps_census_fallbacks_and_exact_trace_scores(tmp_path, monkeypatch):
    run = load_script("160_run_scarcity.py", "scarcity_runner_fixture")
    out = tmp_path / "synthetic_fixture"
    (out / "preparation").mkdir(parents=True)
    monkeypatch.setattr(run, "OUT", out)
    rng = np.random.default_rng(7)
    n = 8
    h = 72
    q = rng.random((n, 10, h))
    y = rng.random((n, 8, 24))
    prior = np.tri(n, k=-1, dtype=bool)
    donor = forward_hold(q)
    mean, var = coordinate_moments(prior, donor)
    rain = np.ones((n, 8, 7))
    rain[:, :, -2:] = rng.random((n, 8, 2))
    rm, rv = coordinate_moments(prior, rain)
    generic = np.full((n, 8, 9), np.nan)
    gc = np.zeros((n, 8), int)
    for qi in range(1, n):
        for gi in range(8):
            generic[qi, gi] = batch_scores(y[qi, gi], y[:, gi], np.arange(qi)[None])[0][0]
            gc[qi, gi] = qi
    positions = np.arange(200, 200 + n * 100, 100)[:, None] - 71 + np.arange(72)
    bank = {
        "q_0": q,
        "donor_q_0": donor,
        "prior_0_0": prior,
        "q_mean_0_0": mean,
        "q_pairvar_0_0": 2 * var,
        "rain_0_1_0": rain,
        "rain_mean_0_0": rm,
        "rain_var_0_0": rv,
        "outcome_0": y,
        "outcome_valid_0": np.ones((n, 8), bool),
        "outcome_quality_0": np.ones((n, 8), bool),
        "input_quality_0": np.ones((n, 10, h), bool),
        "generic_0_0": generic,
        "generic_count_0_0": gc,
        "positions_0": positions,
        "eo_valid": np.ones((1, n, 8), bool),
        "eo_pair_0_0": np.ones((1, 8, n)),
    }
    meta = pd.DataFrame(
        {
            "gauge": list("abcdefgh") * n,
            "country": (["NL"] * 6 + ["DE"] * 2) * n,
            "storm_id": np.repeat(np.arange(n).astype(str), 8),
            "area_km2": [50.0] * n * 8,
            "boundary_known": [True] * n * 8,
            "cutoff_utc": pd.date_range("2020-01-02", periods=n, freq="10D", tz="UTC").repeat(8),
            "physical_river": list("abcdefgh") * n,
        }
    )
    groups = [
        dict(name="rich_basin", family="reference", replicas=1),
        dict(name="rich_local", family="local", replicas=1),
        dict(
            name="scattered_50pct", family="missing", fraction=0.5, pattern="scattered", replicas=3
        ),
        dict(name="network_0", family="network", replicas=1, subsets=[[]]),
        dict(name="all_q_absent", family="all_absent", replicas=1),
        dict(
            name="combined_schedule",
            family="combined_schedule",
            replicas=2,
            subsets=[[0, 2, 4, 6]] * 2,
            phases=[0, 3],
            hours=6,
        ),
        dict(
            name="combined_missing",
            family="combined_missing",
            replicas=3,
            subsets=[[0, 2, 4, 6]] * 3,
            mask_name="scattered_50pct",
        ),
        dict(name="rich_basin_measured", family="reference", replicas=1, measured_support=True),
    ]
    hidden = mask_series(2000, 3, 8, [0.5], seed=9)[0]
    packed = np.packbits(hidden, axis=-1)
    np.save(out / "preparation/scattered_50pct.npy", packed)
    run.STATE.clear()
    run.STATE.update(
        bank=bank,
        meta=meta,
        storms=pd.DataFrame({"cutoff_utc": meta.cutoff_utc.iloc[::8].reset_index(drop=True)}),
        groups={g["name"]: g for g in groups},
        epochs=np.arange(2000),
        source_rain=pd.DataFrame(np.ones((2000, 8))),
        representations=[dict(model="fixture", kind="recent")],
        sources={"fixture": "synthetic_only"},
        config={"donor_support_sensitivity": {"minimum_measured_fraction_per_active_channel": 0.8}},
        eo=rng.random((1, 8, n, n)),
    )
    for spec in groups:
        name, status = run.run_job((spec["name"], 0))
        assert status == "completed"
        frame = pd.read_parquet(out / "scores" / name / "scores.parquet")
        assert frame["case"].nunique() == 8 * n
        z = dict(np.load(out / "scores" / name / "paired_replicates.npz"))
        np.testing.assert_allclose(
            z["paired"][..., 0],
            z["paired"][..., 1] + z["paired"][..., 2],
            atol=1e-6,
            equal_nan=True,
        )
        for row in frame.iloc[::11].itertuples():
            qi, gi = divmod(row.case, 8)
            ids = row.trace_members
            if row.trace_kind == "generic":
                ids = np.flatnonzero(prior[qi])
            if row.trace_kind == "persistence":
                keep = scenario_keep(
                    spec,
                    positions[qi],
                    positions[qi],
                    packed if spec["family"] in ["missing", "combined_missing"] else None,
                    gi,
                )
                local = np.where(keep[0, gi], q[qi, gi], np.nan)
                last = forward_hold(local)[-1]
                expected = ensemble_metrics(y[qi, gi], np.full((1, 24), last))["crps"]
            elif len(ids):
                expected = ensemble_metrics(y[qi, gi], y[ids, gi])["crps"]
            else:
                continue
            np.testing.assert_allclose(row.trace_crps, expected, atol=1e-12)
        assert run.run_job((spec["name"], 0))[1] == "reused"
    # Exercise the complete review/bridge publication against synthetic sources.
    review = load_script("162_review_scarcity.py", "scarcity_review_fixture")
    monkeypatch.setattr(review, "ROOT", tmp_path)
    monkeypatch.setattr(review, "OUT", out)
    script = tmp_path / "scripts/162_review_scarcity.py"
    script.parent.mkdir()
    script.symlink_to(review.__file__)
    monkeypatch.setattr(review, "__file__", str(script))
    helper = tmp_path / "src/scarcity_review.py"
    helper.parent.mkdir()
    helper.symlink_to(run.ROOT / "src/scarcity_review.py")
    prep = out / "preparation"
    meta.to_parquet(prep / "cases.parquet", index=False)
    run.STATE["storms"].to_parquet(prep / "storms.parquet", index=False)
    np.savez(prep / "bank.npz", **bank)
    (prep / "config.json").write_text(json.dumps({"issue_offsets_h": [0]}))
    (prep / "groups.json").write_text(json.dumps(groups))
    (prep / "manifest.json").write_text(
        json.dumps({"jobs": len(groups), "representations": run.STATE["representations"]})
    )
    old_path = (
        tmp_path
        / "results/limburg_monitoring_2026_10_28/scores/baseline__none__same_gauge/scores.parquet"
    )
    old_path.parent.mkdir(parents=True)
    baseline = pd.read_parquet(out / "scores/rich_basin__u0/scores.parquet")
    baseline = baseline[baseline.method.eq("conventional")].assign(
        role="natural_conventional", cap_h=0
    )
    baseline.to_parquet(old_path, index=False)
    normalizer_path = tmp_path / "results/storm_response/hourly_normalizer.parquet"
    normalizer_path.parent.mkdir(parents=True)
    pd.DataFrame(
        0.8,
        index=pd.date_range("2020-01-01", periods=2000, freq="h", tz="UTC"),
        columns=list("abcdefgh"),
    ).to_parquet(normalizer_path)
    register_path = tmp_path / "results/flood_case_review_2026_10_27/register.parquet"
    register_path.parent.mkdir(parents=True)
    pd.DataFrame(
        {
            "gauge": ["a"],
            "start": [meta.cutoff_utc.iloc[0]],
            "end": [meta.cutoff_utc.iloc[0] + pd.Timedelta(hours=24)],
        }
    ).to_parquet(register_path)
    monkeypatch.setattr(sys, "argv", ["review", "--benchmark"])
    review.main()
    ledger = pd.read_parquet(out / "benchmark_review/coverage-ledger.parquet")
    assert len(ledger) == n * 8 * len(groups)
    assert ledger.verification_available.all()
    effects = pd.read_parquet(out / "benchmark_review/paired-effects.parquet")
    assert {"eo_supported", "common_eo_support", "future_p99", "equal_age"} <= set(
        effects.population
    )
    assert (out / "benchmark_review/prior-method-bridge.csv").exists()
    assert (out / "benchmark_review/network-placement-inventory.csv").exists()
