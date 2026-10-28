"""Evidence synthesis, paired archive decomposition, and declared Meuse test.

Uses completed observations/embeddings; no encoder inference or model training.
Stages publish atomically and carry input/source hashes. --benchmark runs a
small computation only; --stage all executes the complete eligible census.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analogue_assessment import add_context, baseline_distance, scores, selected_rows
from src.analogue_distributions import group_weights
from src.eo_comparison import load_script
from src.eo_followup import METRICS, cluster_intervals_multi, eligible_archive
from src.eo_inputs import ROUTES, sha256
from src.eo_integrity import fresh_output

OUT = ROOT / "results/limburg_assessment_2026_10_27"
CONFIG = ROOT / "config/limburg_meuse_comparison.json"
KINDS = ["monthly_snapshot", "monthly", "recent"]
SETTINGS = {
    "main": ("all_rivers", False),
    "other_rivers": ("other_rivers", False),
    "quality": ("all_rivers", True),
}
SCORE_FIELDS = METRICS + [
    f"{v}_{h}"
    for v in ["crps", "coverage80", "width80", "above80", "below80"]
    for h in ["mean_24h", "h6", "h12", "h24"]
]
FOLLOW = load_script("137_eo_archive_and_route_followup.py", "assessment_followup")


class Run:
    def __init__(self):
        self.inputs = {}
        self.config = json.loads(self.bind(CONFIG).read_text())
        (
            self.sample,
            self.meta,
            self.raw,
            self.ttm,
            self.state,
            self.base,
            self.oldrain,
            self.rain,
            self.alpha,
        ) = FOLLOW.inputs()
        self.sample["onset_utc"] = pd.to_datetime(self.sample.onset_utc, utc=True)
        self.sample = self.sample.sort_values(["onset_utc", "event_id"]).reset_index(drop=True)
        self.meta["onset_utc"] = pd.to_datetime(self.meta.onset_utc, utc=True)
        self.response = pd.read_parquet(
            self.bind(
                ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet"
            )
        )
        self.context = pd.read_parquet(
            self.bind(ROOT / "results/meuse_context_2026_10_27/event_context.parquet")
        ).set_index("event_id")
        self.phase = pd.read_csv(
            self.bind(
                ROOT / "results/warning_threshold_progression/all_p99_event_phase_outcomes.csv"
            )
        ).set_index("event_id")
        for name in [
            "event_inventory.csv",
            "q_only_signatures.csv",
            "q_only_standardized_histories.parquet",
            "q_only_ttm_ordered.parquet",
            "q_only_discharge_state.parquet",
        ]:
            self.bind(ROOT / "results/basin_ai_event_interpretation_ready" / name)
        self.bind(ROOT / "results/basin_ai_cross_border_completion/rainfall_event_coverage.csv")
        self.bind(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
        for name in ["manifest.json", "summary.json"]:
            self.bind(ROOT / "results/meuse_context_2026_10_27" / name)
        self.sources = {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [
                Path(__file__).resolve(),
                ROOT / "src/analogue_assessment.py",
                ROOT / "src/analogue_distributions.py",
                ROOT / "src/eo_followup.py",
                ROOT / "scripts/65_hydrological_analogue_baseline.py",
                ROOT / "src/eo_comparison.py",
                ROOT / "scripts/137_eo_archive_and_route_followup.py",
            ]
        }
        self.full = {
            family: self.sample[self.sample.event_id.isin(ids)].copy()
            for family, ids in [("q", set(self.sample.event_id)), ("rain", self.rain)]
        }

    def bind(self, path):
        path = Path(path)
        self.inputs[str(path.relative_to(ROOT))] = sha256(path)
        return path

    def valid(self, path):
        m = path / "manifest.json"
        if not m.exists():
            return False
        saved = json.loads(m.read_text())
        for section, root in [
            ("inputs_sha256", ROOT),
            ("source_sha256", ROOT),
            ("outputs_sha256", path),
        ]:
            for name, digest in saved[section].items():
                if sha256(root / name) != digest:
                    raise ValueError("Changed stage dependency: " + name)
        return True

    def finish(self, work):
        m = dict(
            status="completed",
            created_utc=datetime.now(timezone.utc).isoformat(),
            inputs_sha256=self.inputs.copy(),
            source_sha256=self.sources,
            outputs_sha256={
                str(p.relative_to(work)): sha256(p) for p in work.rglob("*") if p.is_file()
            },
        )
        (work / "manifest.json").write_text(json.dumps(m, indent=2))

    def candidates(self, pool, query, setting):
        scenario, quality = SETTINGS[setting]
        return eligible_archive(pool, query, scenario, "pooled", quality)

    def distance(self, candidates, eid, method):
        return baseline_distance(
            candidates.event_id.tolist(),
            eid,
            conventional=self.sample.set_index("event_id")[self.base.FEATURE_COLUMNS]
            if method == "conventional"
            else None,
            temporal=self.ttm,
            state=self.state,
        )

    def score(self, eid, ids, weights=None):
        return scores(
            self.response.loc[eid].to_numpy(), self.response.loc[list(ids)].to_numpy(), weights
        )

    def support(self, c, query):
        labels = c.event_id.map(self.phase.H3_native)
        positive = c.loc[labels.eq(1), "event_id"].tolist()
        return dict(
            candidate_events=len(c),
            candidate_storms=c.storm_id.nunique(),
            earliest=c.onset_utc.min(),
            latest=c.onset_utc.max(),
            median_age_days=float(
                (query.onset_utc - c.onset_utc).dt.total_seconds().median() / 86400
            )
            if len(c)
            else np.nan,
            observed_H3_positive=len(positive),
            positive_event_ids=json.dumps(positive),
            H3_label_unknown=int(labels.isna().sum()),
            measured_concern_events=int(c.measurement_concern.sum()),
            candidate_ids_sha256=hashlib.sha256("\n".join(sorted(c.event_id)).encode()).hexdigest(),
        )

    def benchmark(self):
        pool = self.full["rain"]
        qlist = list(pool.itertuples())[100:112]
        elapsed = time.perf_counter()
        n = 0
        for q in qlist:
            c = self.candidates(pool, q, "main")
            for method in self.config["baselines"]:
                d, _ = self.distance(c, q.event_id, method)
                selected = selected_rows(c, d)
                for k in [5, 10]:
                    self.score(q.event_id, selected.head(k).event_id)
                n += 1
        seconds = time.perf_counter() - elapsed
        report = dict(
            queries=len(qlist),
            retrievals=n,
            seconds=seconds,
            seconds_per_retrieval=seconds / n,
            estimated_new_meuse_retrievals_upper=len(pool) * 2 * 2 * 3,
            rough_meuse_minutes_upper=seconds / n * len(pool) * 2 * 2 * 3 / 60,
            note="Control/EO bookkeeping and bootstrap add CPU time; no GPU or EO inference.",
        )
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "benchmark.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2), flush=True)

    def full_baselines(self):
        for family, pool in self.full.items():
            for setting in SETTINGS:
                dest = OUT / "baselines" / f"{family}_{setting}"
                if self.valid(dest):
                    continue
                eventrows, donors, support = [], [], []
                for q in pool.itertuples():
                    if setting == "quality" and q.measurement_concern:
                        continue
                    c = self.candidates(pool, q, setting)
                    support.append(
                        dict(
                            family=family,
                            setting=setting,
                            event_id=q.event_id,
                            **self.support(c, q),
                        )
                    )
                    if c.empty:
                        continue
                    for method in self.config["baselines"]:
                        if family == "q" and method == "conventional":
                            continue
                        d, _ = self.distance(c, q.event_id, method)
                        selected = selected_rows(c, d)
                        for rank, s in enumerate(selected.itertuples(), 1):
                            donors.append(
                                dict(
                                    query_event_id=q.event_id,
                                    analogue_event_id=s.event_id,
                                    method=method,
                                    rank=rank,
                                    distance=s.distance,
                                )
                            )
                        for k in [5, 10]:
                            eventrows.append(
                                dict(
                                    query_event_id=q.event_id,
                                    method=method,
                                    target_k=k,
                                    actual_donors=min(k, len(selected)),
                                    query_country=q.country,
                                    query_storm_id=q.storm_id,
                                    query_onset_utc=q.onset_utc,
                                    **self.score(q.event_id, selected.head(k).event_id),
                                )
                            )
                with fresh_output(dest) as work:
                    pd.DataFrame(eventrows).to_parquet(work / "scores.parquet", index=False)
                    pd.DataFrame(donors).to_parquet(work / "donors.parquet", index=False)
                    pd.DataFrame(support).to_parquet(work / "support.parquet", index=False)
                    self.finish(work)
                print("full baseline", family, setting, len(eventrows), flush=True)

    def archive(self):
        prep = ROOT / "results/eo_comparison_preparation"
        obs = pd.read_parquet(self.bind(prep / "observations.parquet"))
        links = pd.read_parquet(self.bind(prep / "observation_windows.parquet"))
        comparison = ROOT / "results/eo_analogue_comparison_coherent_v1"
        self.bind(comparison / "manifest.json")
        # Retain source contract for all ten vector indexes even though only availability is used here.
        m = json.loads((comparison / "manifest.json").read_text())
        for p in m["input_sha256"]:
            if any(p.endswith("/" + model + ".parquet") for model in ROUTES):
                self.bind(ROOT / p)
        for family, source, prefix in [
            ("q", comparison, "q_only_"),
            ("rain", ROOT / "results/eo_analogue_comparison_rain168_v1", "rain_"),
        ]:
            self.bind(source / "manifest.json")
            scorepath = self.bind(source / "event_assessments.parquet")
            # Arrow filters avoid loading millions of irrelevant foreign/domestic rows.
            saved = pq.read_table(
                scorepath,
                filters=[
                    ("policy", "=", "pooled"),
                    ("analysis", "in", ["main", "quality_sensitivity"]),
                    ("scenario", "in", ["all_rivers", "other_rivers"]),
                ],
                columns=[
                    "query_event_id",
                    "query_storm_id",
                    "query_onset_utc",
                    "query_country",
                    "candidate_count",
                    "candidate_storm_count",
                    "kind",
                    "cohort",
                    "scenario",
                    "analysis",
                    "arm",
                    "target_k",
                ]
                + METRICS,
            ).to_pandas()
            for kind in KINDS:
                dest = OUT / "archive" / f"{family}_{kind}"
                if self.valid(dest):
                    continue
                vectors = FOLLOW.vectors_for(comparison, kind, obs, links)
                allids = set(self.full[family].event_id)
                for v in vectors.values():
                    allids &= set(v.index)
                ledger = []
                decomp = []
                members = []
                groups = [("all_ten", allids)] + [
                    (model, set(v.index)) for model, v in sorted(vectors.items())
                ]
                fullpool = self.full[family]
                for model, ids in groups:
                    ids = set(fullpool.event_id) & ids
                    pop = fullpool[fullpool.event_id.isin(ids)].copy()
                    cohort = (
                        (prefix + "all_ten_matched")
                        if model == "all_ten"
                        else (
                            ("q_only_available_" if family == "q" else "rain_matched_available_")
                            + model
                        )
                    )
                    models = sorted(ROUTES) if model == "all_ten" else [model]
                    for eid in sorted(ids):
                        members.append(dict(model=model, event_id=eid))
                    for setting, (scenario, quality) in SETTINGS.items():
                        analysis = "quality_sensitivity" if quality else "main"
                        g = saved[
                            saved.kind.eq(kind)
                            & saved.cohort.eq(cohort)
                            & saved.scenario.eq(scenario)
                            & saved.analysis.eq(analysis)
                        ]
                        full = pd.read_parquet(
                            OUT / "baselines" / f"{family}_{setting}" / "scores.parquet"
                        )
                        full = full.set_index(["query_event_id", "method", "target_k"])
                        lookup = {(r.query_event_id, r.arm, r.target_k): r for r in g.itertuples()}
                        for q in pop.itertuples():
                            if quality and q.measurement_concern:
                                continue
                            c = self.candidates(pop, q, setting)
                            ledger.append(
                                dict(
                                    family=family,
                                    kind=kind,
                                    model=model,
                                    setting=setting,
                                    query_event_id=q.event_id,
                                    query_country=q.country,
                                    query_storm_id=q.storm_id,
                                    query_onset_utc=q.onset_utc,
                                    **self.support(c, q),
                                )
                            )
                            if c.empty:
                                continue
                            for baseline in (
                                ["ttm_state"] if family == "q" else ["conventional", "ttm_state"]
                            ):
                                for k in [5, 10]:
                                    key = (q.event_id, baseline, k)
                                    if key not in lookup:
                                        raise ValueError("Missing restricted reference " + str(key))
                                    r = lookup[key]
                                    b = full.loc[key]
                                    if (
                                        r.candidate_count != len(c)
                                        or r.candidate_storm_count != c.storm_id.nunique()
                                    ):
                                        raise ValueError("Reconstructed EO archive mismatch")
                                    for encoder in models:
                                        a = lookup[(q.event_id, encoder + "_ttm_state", k)]
                                        for metric in METRICS:
                                            fval, rval, aval = (
                                                float(b[metric]),
                                                float(getattr(r, metric)),
                                                float(getattr(a, metric)),
                                            )
                                            decomp.append(
                                                dict(
                                                    family=family,
                                                    kind=kind,
                                                    model=encoder,
                                                    population=model,
                                                    setting=setting,
                                                    baseline=baseline,
                                                    target_k=k,
                                                    metric=metric,
                                                    query_event_id=q.event_id,
                                                    query_storm_id=q.storm_id,
                                                    query_onset_utc=q.onset_utc,
                                                    query_country=q.country,
                                                    full_loss=fval,
                                                    restricted_loss=rval,
                                                    augmented_loss=aval,
                                                    archive_difference=rval - fval,
                                                    representation_difference=aval - rval,
                                                    total_difference=aval - fval,
                                                )
                                            )
                with fresh_output(dest) as work:
                    pd.DataFrame(ledger).to_parquet(work / "support.parquet", index=False)
                    pd.DataFrame(members).to_parquet(work / "population.parquet", index=False)
                    pd.DataFrame(decomp).to_parquet(work / "decomposition.parquet", index=False)
                    self.finish(work)
                print("archive decomposition", family, kind, len(decomp), flush=True)

    def meuse(self):
        for context, features in self.config["context_features"].items():
            vectors = self.context[features].dropna()
            pool = self.full["rain"][self.full["rain"].event_id.isin(vectors.index)].copy()
            for setting in SETTINGS:
                dest = OUT / "meuse" / f"{context}_{setting}"
                if self.valid(dest):
                    continue
                rows, donors, support = [], [], []
                for q in pool.itertuples():
                    if setting == "quality" and q.measurement_concern:
                        continue
                    c = self.candidates(pool, q, setting)
                    support.append(dict(query_event_id=q.event_id, **self.support(c, q)))
                    if c.empty:
                        continue
                    # Generic distribution is common to all methods/counts in this pool.
                    generic = self.score(q.event_id, c.event_id, group_weights(c.storm_id))
                    for k in [5, 10]:
                        rows.append(
                            dict(
                                query_event_id=q.event_id,
                                method="generic_archive",
                                target_k=k,
                                actual_donors=len(c),
                                query_country=q.country,
                                query_storm_id=q.storm_id,
                                query_onset_utc=q.onset_utc,
                                **generic,
                            )
                        )
                    for method in self.config["baselines"]:
                        d, base_scale = self.distance(c, q.event_id, method)
                        augmented, md, ms = add_context(
                            d, base_scale, vectors.loc[c.event_id], vectors.loc[q.event_id]
                        )
                        for arm, dist in [(method, d), (method + "_meuse", augmented)]:
                            cand = c.assign(
                                base_distance=d,
                                base_scale=base_scale,
                                meuse_distance=md,
                                meuse_scale=ms,
                            )
                            selected = selected_rows(cand, dist)
                            for rank, s in enumerate(selected.itertuples(), 1):
                                donors.append(
                                    dict(
                                        query_event_id=q.event_id,
                                        analogue_event_id=s.event_id,
                                        method=arm,
                                        rank=rank,
                                        distance=s.distance,
                                        base_distance=s.base_distance,
                                        base_scale=s.base_scale,
                                        meuse_distance=s.meuse_distance,
                                        meuse_scale=s.meuse_scale,
                                    )
                                )
                            for k in [5, 10]:
                                rows.append(
                                    dict(
                                        query_event_id=q.event_id,
                                        method=arm,
                                        target_k=k,
                                        actual_donors=min(k, len(selected)),
                                        query_country=q.country,
                                        query_storm_id=q.storm_id,
                                        query_onset_utc=q.onset_utc,
                                        **self.score(q.event_id, selected.head(k).event_id),
                                    )
                                )
                with fresh_output(dest) as work:
                    pd.DataFrame(rows).to_parquet(work / "scores.parquet", index=False)
                    pd.DataFrame(donors).to_parquet(work / "donors.parquet", index=False)
                    pd.DataFrame(support).to_parquet(work / "support.parquet", index=False)
                    self.finish(work)
                print("Meuse", context, setting, len(rows), flush=True)

    def intervals(self):
        """Resample all declared paired loss components, no selection on intervals."""
        dest = OUT / "intervals"
        if self.valid(dest):
            return
        outputs = []
        for p in sorted((OUT / "archive").glob("*/decomposition.parquet")):
            f = pd.read_parquet(self.bind(p))
            keys = [
                "family",
                "kind",
                "model",
                "population",
                "setting",
                "baseline",
                "target_k",
                "metric",
            ]
            for key, g in f.groupby(keys, observed=True):
                for country in ["all", "NL", "DE"]:
                    h = g if country == "all" else g[g.query_country.eq(country)]
                    outputs += self.ci(
                        h,
                        dict(zip(keys, key, strict=True))
                        | {"query_country": country, "module": "archive"},
                        ["archive_difference", "representation_difference", "total_difference"],
                    )
        meuse_pairs = []
        for folder in sorted((OUT / "meuse").iterdir()):
            f = pd.read_parquet(self.bind(folder / "scores.parquet"))
            context, setting = folder.name.rsplit("_", 1)
            if setting == "rivers":
                context, setting = folder.name.removesuffix("_other_rivers"), "other_rivers"
            full = pd.read_parquet(
                self.bind(OUT / "baselines" / f"rain_{setting}" / "scores.parquet")
            )
            allkeys = ["query_event_id", "target_k"]
            for baseline in self.config["baselines"]:
                a = f[f.method.eq(baseline + "_meuse")]
                r = f[f.method.eq(baseline)]
                b = full[full.method.eq(baseline)]
                x = a.merge(r, on=allkeys, suffixes=("_aug", "_restricted"), validate="one_to_one")
                x = x.merge(b, on=allkeys, validate="one_to_one")
                for row in x.itertuples():
                    for metric in SCORE_FIELDS:
                        fval = getattr(row, metric)
                        rval = getattr(row, metric + "_restricted")
                        aval = getattr(row, metric + "_aug")
                        meuse_pairs.append(
                            dict(
                                context=context,
                                setting=setting,
                                baseline=baseline,
                                target_k=row.target_k,
                                query_event_id=row.query_event_id,
                                query_country=row.query_country,
                                query_storm_id=row.query_storm_id,
                                query_onset_utc=row.query_onset_utc,
                                metric=metric,
                                full_loss=fval,
                                restricted_loss=rval,
                                augmented_loss=aval,
                                archive_difference=rval - fval,
                                representation_difference=aval - rval,
                                total_difference=aval - fval,
                            )
                        )
        pairs = pd.DataFrame(meuse_pairs)
        for key, g in pairs.groupby(
            ["context", "setting", "baseline", "target_k", "metric"], observed=True
        ):
            tags = dict(
                zip(["context", "setting", "baseline", "target_k", "metric"], key, strict=True)
            )
            for country in ["all", "NL", "DE"]:
                h = g if country == "all" else g[g.query_country.eq(country)]
                outputs += self.ci(
                    h,
                    tags | {"module": "meuse", "query_country": country},
                    ["archive_difference", "representation_difference", "total_difference"],
                )
        with fresh_output(dest) as work:
            pd.DataFrame(outputs).to_parquet(work / "paired_intervals.parquet", index=False)
            pairs.to_parquet(work / "meuse_pairs.parquet", index=False)
            self.finish(work)
        print("intervals", len(outputs), "rows", flush=True)

    def ci(self, g, tags, columns):
        if g.empty:
            return []
        g = g.rename(columns={"query_storm_id": "storm_id"}).copy()
        earliest = self.meta.groupby("storm_id").onset_utc.min().dt.year
        g["storm_year"] = g.storm_id.map(earliest)
        out = []
        for unit in ["storm_id", "storm_year"]:
            values = cluster_intervals_multi(
                g,
                unit,
                columns,
                draws=self.config["bootstrap_draws"],
                seed=self.config["bootstrap_seed"],
            )
            for component, v in values.items():
                out.append(tags | {"component": component, "resampling_unit": unit} | v)
        return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["benchmark", "baselines", "archive", "meuse", "intervals", "all"],
        default="benchmark",
    )
    args = parser.parse_args()
    run = Run()
    if args.stage == "benchmark":
        run.benchmark()
        return
    if args.stage in ["all", "baselines"]:
        run.full_baselines()
    if args.stage in ["all", "archive"]:
        run.archive()
    if args.stage in ["all", "meuse"]:
        run.meuse()
    if args.stage in ["all", "intervals"]:
        run.intervals()


if __name__ == "__main__":
    main()
