"""Independent numerical/provenance audit of the completed assessment pass."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import load_script
from src.eo_inputs import sha256
from src.meuse_context import state_at_cutoff

OUT = ROOT / "results/limburg_assessment_2026_10_27"


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ["href", "src"] and value and not urlsplit(value).scheme:
                self.paths.append(unquote(urlsplit(value).path))


def main():
    module = load_script("146_run_limburg_assessment.py", "assessment_independent_audit")
    run = module.Run()
    meta = run.meta
    counts = dict(
        manifests=0,
        output_hashes=0,
        selected_sets=0,
        selected_donor_rows=0,
        paired_decompositions=0,
        independent_crps_scores=0,
        legacy_distance_checks=0,
    )
    for path in OUT.rglob("manifest.json"):
        saved = json.loads(path.read_text())
        for field, root in [
            ("inputs_sha256", ROOT),
            ("source_sha256", ROOT),
            ("outputs_sha256", path.parent),
        ]:
            for name, digest in saved[field].items():
                assert sha256(root / name) == digest, (path, name)
        counts["manifests"] += 1
        counts["output_hashes"] += len(saved["outputs_sha256"])
    # Full query inventory remains an inventory rather than a hidden complete-case sample.
    ledger = pd.read_parquet(OUT / "review/eligibility_ledger.parquet")
    assert not ledger.duplicated(["module", "context", "event_id"]).any()
    assert ledger.groupby(["module", "context"]).size().eq(len(meta)).all()
    counts["inventory_rows"] = len(meta)
    counts["eligibility_rows"] = len(ledger)
    for path in OUT.glob("archive/*/decomposition.parquet"):
        f = pd.read_parquet(path)
        np.testing.assert_allclose(
            f.archive_difference + f.representation_difference,
            f.total_difference,
            rtol=0,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            f.restricted_loss - f.full_loss, f.archive_difference, rtol=0, atol=1e-12
        )
        counts["paired_decompositions"] += len(f)
    for folder in list((OUT / "baselines").iterdir()) + list((OUT / "meuse").iterdir()):
        d = pd.read_parquet(folder / "donors.parquet")
        assert not d.duplicated(["query_event_id", "method", "rank"]).any()
        assert not d.duplicated(["query_event_id", "method", "analogue_event_id"]).any()
        for row in d.itertuples():
            q = meta.loc[row.query_event_id]
            a = meta.loc[row.analogue_event_id]
            assert a.onset_utc + pd.Timedelta(hours=72) <= q.onset_utc
            assert a.storm_id != q.storm_id
            if folder.name.endswith("other_rivers"):
                assert a.physical_river_group != q.physical_river_group
            if folder.name.endswith("quality"):
                assert not (a.measurement_concern or q.measurement_concern)
        for _, g in d.groupby(["query_event_id", "method"]):
            assert meta.loc[g.analogue_event_id].storm_id.is_unique
        counts["selected_donor_rows"] += len(d)
        sets = {
            (eid, m): g.sort_values("rank")
            for (eid, m), g in d.groupby(["query_event_id", "method"])
        }
        f = pd.read_parquet(folder / "scores.parquet")
        for row in f[f.method.ne("generic_archive")].itertuples():
            g = sets[row.query_event_id, row.method].head(row.target_k)
            a = run.response.loc[g.analogue_event_id].to_numpy()[:, :24]
            y = run.response.loc[row.query_event_id].to_numpy()[:24]
            # Direct double sum is independent of sorted-CDF scoring implementation.
            crps = np.abs(a - y).mean(0) - 0.5 * np.abs(a[:, None, :] - a[None, :, :]).mean((0, 1))
            np.testing.assert_allclose(crps.mean(), row.crps_mean_24h, atol=1e-12, rtol=0)
            assert len(g) == row.actual_donors
            counts["independent_crps_scores"] += 1
        counts["selected_sets"] += len(sets)
        if folder.parent.name == "meuse":
            context, setting = tags(folder.name)
            features = run.config["context_features"][context]
            v = run.context[features].dropna()
            assert set(d.query_event_id) | set(d.analogue_event_id) <= set(v.index)
            pool = run.full["rain"][run.full["rain"].event_id.isin(v.index)]
        else:
            family, setting = folder.name.split("_", 1)
            pool = run.full[family]
        # Directly verify original baseline formulas and augmented block distances at
        # fixed first/middle/last assessment times, without choosing good outcomes.
        eids = sorted(d.query_event_id.unique())
        for eid in [eids[0], eids[len(eids) // 2], eids[-1]]:
            query = pool.set_index("event_id", drop=False).loc[eid]
            c = run.candidates(pool, query, setting)
            for method in run.config["baselines"]:
                if (eid, method) not in sets:
                    continue
                if method == "conventional":
                    p = c[run.base.FEATURE_COLUMNS]
                    q = query[run.base.FEATURE_COLUMNS].astype(float)
                    iqr = (p.quantile(0.75) - p.quantile(0.25)).replace(0, 1)
                    distance = np.sqrt((((p - q) / iqr) ** 2).sum(axis=1))
                else:
                    distance, _ = run.base.block_distances(
                        c, query, {"temporal": run.ttm, "state": run.state}, ("state",)
                    )
                expected = (
                    c.assign(distance=distance)
                    .sort_values(["distance", "onset_utc", "event_id"])
                    .drop_duplicates("storm_id")
                    .head(10)
                )
                assert expected.event_id.tolist() == sets[eid, method].analogue_event_id.tolist()
                np.testing.assert_allclose(
                    expected.distance, sets[eid, method].distance, atol=1e-12, rtol=0
                )
                counts["legacy_distance_checks"] += 1
            if folder.parent.name == "meuse":
                for method in run.config["baselines"]:
                    g = sets.get((eid, method + "_meuse"))
                    if g is None:
                        continue
                    expected = np.sqrt(
                        0.5 * (g.base_distance / g.base_scale) ** 2
                        + 0.5 * (g.meuse_distance / g.meuse_scale) ** 2
                    )
                    np.testing.assert_allclose(expected, g.distance, atol=1e-12, rtol=0)
    p = pd.read_parquet(OUT / "intervals/meuse_pairs.parquet")
    np.testing.assert_allclose(
        p.archive_difference + p.representation_difference, p.total_difference, atol=1e-12, rtol=0
    )
    f = pd.read_parquet(OUT / "review/fallback_policy.parquet")
    for column in [c for c in f if c.endswith("_difference")]:
        assert f.loc[~f.used_meuse, column].eq(0).all()
    counts["fallback_policy_rows"] = len(f)
    # Cutoff and annual-reference timing are invariant to post-cutoff changes.
    for site in ["sint_pieter", "venlo"]:
        frame = pd.read_parquet(ROOT / f"results/meuse_context_2026_10_27/{site}_hourly.parquet")
        t = pd.Timestamp("2024-05-17T07:00:00Z")
        old = state_at_cutoff(frame, t)
        frame.loc[frame.index > t, ["q_strict", "q_display"]] = 9999999
        pd.testing.assert_series_equal(pd.Series(old), pd.Series(state_at_cutoff(frame, t)))
    links = 0
    for path in (OUT / "review").glob("*.html"):
        parser = LocalLinks()
        parser.feed(path.read_text())
        for name in parser.paths:
            assert (path.parent / name).exists(), (path, name)
            links += 1
    browser_text = (OUT / "review/analogues.html").read_text()
    match = re.search(r"const D=(.*?);const el", browser_text, re.S)
    assert match is not None
    payload = json.loads(match.group(1))
    assert set(payload["curves"]) == set(payload["facts"])
    assert len(payload["sets"]) == 830
    for eid, curve in payload["curves"].items():
        np.testing.assert_allclose(curve, run.response.loc[eid], rtol=0, atol=1e-12)
    for eid, arms in payload["sets"].items():
        assert eid in payload["curves"]
        for donor_ids in arms.values():
            assert len(donor_ids) <= 10
            assert set(donor_ids) <= set(payload["curves"])
    counts["browser_queries"] = len(payload["sets"])
    counts["browser_curves_checked"] = len(payload["curves"])
    original = OUT / "bootstrap_original_reference/paired_intervals.parquet"
    if original.exists():
        left = pd.read_parquet(original)
        right = pd.read_parquet(OUT / "intervals/paired_intervals.parquet")
        numeric = [
            "difference",
            "lower",
            "upper",
            "query_count",
            "cluster_count",
            "draws",
            "finite_draws",
        ]
        keys = [c for c in left if c not in numeric]
        compare = left.merge(
            right, on=keys, suffixes=("_original", "_joint"), validate="one_to_one"
        )
        assert len(compare) == len(left) == len(right)
        for c in numeric:
            np.testing.assert_allclose(
                compare[c + "_original"], compare[c + "_joint"], atol=1e-12, rtol=0, equal_nan=True
            )
        counts["equivalent_bootstrap_rows"] = len(compare)
    # Independently check a reported bootstrap at the primary endpoint, with the same
    # deterministic cluster draws generated as a full matrix rather than chunked.
    h = p[
        (p.context == "both_sites")
        & (p.setting == "main")
        & (p.baseline == "conventional")
        & (p.target_k == 5)
        & (p.metric == "crps_mean_24h")
    ]
    values = h.groupby("query_storm_id").representation_difference.sum().sort_index()
    sizes = h.groupby("query_storm_id").size().sort_index()
    rng = np.random.default_rng(run.config["bootstrap_seed"])
    picks = rng.integers(0, len(values), size=(run.config["bootstrap_draws"], len(values)))
    samples = values.to_numpy()[picks].sum(1) / sizes.to_numpy()[picks].sum(1)
    bounds = np.quantile(samples, [0.025, 0.975])
    intervals = pd.read_parquet(OUT / "intervals/paired_intervals.parquet")
    reported = intervals[
        (intervals.module == "meuse")
        & (intervals.context == "both_sites")
        & (intervals.setting == "main")
        & (intervals.baseline == "conventional")
        & (intervals.target_k == 5)
        & (intervals.metric == "crps_mean_24h")
        & (intervals.query_country == "all")
        & (intervals.component == "representation_difference")
        & (intervals.resampling_unit == "storm_id")
    ].iloc[0]
    np.testing.assert_allclose(bounds, [reported.lower, reported.upper], atol=1e-12, rtol=0)
    counts.update(
        status="passed",
        internal_links=links,
        independent_bootstrap_draws=len(samples),
        after_cutoff_poison_checks=2,
    )
    (OUT / "audit.json").write_text(json.dumps(counts, indent=2))
    print(json.dumps(counts, indent=2))


def tags(name):
    for s in ["other_rivers", "quality", "main"]:
        if name.endswith("_" + s):
            return name[: -(len(s) + 1)], s
    raise ValueError(name)


if __name__ == "__main__":
    main()
