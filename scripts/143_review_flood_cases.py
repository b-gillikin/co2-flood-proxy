"""Complete source-bounded flood-case review of held results; no fitting or retrieval.

Current H3 crossings, documentary impacts and uncertain dates remain distinct.
Post-outcome oracle diagnostics are never used to choose operational donors.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_comparison import load_script
from src.eo_followup import eligible_archive
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.flood_case_review import archive_stage, build_register, curve_diagnostics, link_inventory

OUT = ROOT / "results/flood_case_review_2026_10_27"
PHASE = ROOT / "results/warning_threshold_progression"
READY = ROOT / "results/basin_ai_event_interpretation_ready"
FOLLOW = load_script("137_eo_archive_and_route_followup.py", "flood_frozen_followup")
WARN = load_script("86_analyse_warning_threshold_progression.py", "flood_frozen_warning")
REVIEW = load_script("135_review_eo_followup.py", "flood_frozen_browser")
PROVENANCE = {}


def record(path):
    path = Path(path)
    PROVENANCE[str(path.relative_to(ROOT))] = sha256(path)
    return path


def csv(path, dates=()):
    return pd.read_csv(record(path), parse_dates=list(dates), low_memory=False)


def parquet(path):
    return pd.read_parquet(record(path))


def h1_links(register, episodes, inventory):
    out = []
    for case in register.itertuples():
        if case.date_precision in {"year_only", "early_month_statement_month_review_window"}:
            continue
        e = episodes[episodes.gauge.eq(case.gauge) & episodes.primary]
        if pd.notna(case.episode_id):
            e = e[e.episode_id.eq(case.episode_id)]
        else:
            e = e[
                (pd.to_datetime(e.onset_utc, utc=True) < case.end)
                & (pd.to_datetime(e.review_end_utc, utc=True) >= case.start)
            ]
        for i in inventory[inventory.episode_id.isin(e.episode_id)].itertuples():
            out.append(
                {
                    "case_id": case.case_id,
                    "event_id": i.event_id,
                    "episode_id": i.episode_id,
                    "onset_utc": i.onset_utc,
                    "q_only_input_sample": i.q_only_input_sample,
                    "phase_base_available": i.phase_base_available,
                    "unrepaired_history_complete": i.unrepaired_history_complete,
                    "history_repaired_hours": i.history_repaired_hours,
                }
            )
    return pd.DataFrame(out)


def phase_review(links, inventory):
    meta = inventory.set_index("event_id", drop=False)
    labels = csv(PHASE / "H1_assessment_phase_outcomes.csv").set_index("event_id")
    sample = csv(PHASE / "H1_assessment_signatures.csv", ["onset_utc"])
    years = parquet(ROOT / "results/basin_ai_alphaearth/catchment_year_embeddings.parquet")
    settings = {}
    settings["h1_q_only"] = sample.copy()
    r = sample.copy()
    r["complete_scoring_sample"] &= r.event_id.map(meta.history_rainfall_fraction).eq(1)
    settings["h1_rain_matched"] = r
    r = sample.copy()
    r["complete_scoring_sample"] = (
        r[WARN.B.FEATURE_COLUMNS].notna().all(axis=1)
        & r.event_id.map(meta.native_observed_peak_72h).notna()
    )
    settings["h1_r0_maximal"] = r
    r = WARN.X.join_context(sample, years)
    settings["h1_context"] = r[r.context_available & r.common_representation_sample].copy()
    scores = csv(PHASE / "analogue_event_results.csv")
    scores = scores[
        scores.cohort.str.startswith("h1_")
        & scores.level.eq("H3")
        & scores.query_event_id.isin(links.event_id)
    ].copy()
    donors = csv(PHASE / "phase_conditioned_donors.csv")
    donors = donors[
        donors.cohort.str.startswith("h1_")
        & donors.level.eq("H3")
        & donors.query_event_id.isin(links.event_id)
    ].copy()
    # The phase file stores one ranked ten-donor list, not duplicate k5/k10 rows.
    missing_k = donors[donors.target_k.isna()].copy()
    donors = pd.concat(
        [
            donors[donors.target_k.notna()],
            missing_k[missing_k["rank"].le(5)].assign(target_k=5),
            missing_k.assign(target_k=10),
        ],
        ignore_index=True,
    )
    keys = ["cohort", "scenario", "analysis", "arm", "target_k", "query_event_id"]
    groups = {key: g for key, g in donors.groupby(keys, observed=True)}
    cache, diagnostics = {}, []
    for r in scores.itertuples():
        key = (r.cohort, r.scenario, r.analysis, r.query_event_id)
        if key not in cache:
            pop = WARN.phase_sample(settings[r.cohort], labels, "H3")
            if r.analysis == "complete_followup":
                pop["complete_scoring_sample"] &= pop.event_id.map(
                    labels.response_observed_quarters
                ).eq(288)
            if r.analysis == "observed_history_only":
                pop["complete_scoring_sample"] &= pop.event_id.map(meta.unrepaired_history_complete)
            query = pop.set_index("event_id", drop=False).loc[r.query_event_id]
            c = eligible_archive(
                pop, query, r.scenario, "pooled", r.analysis == "quality_sensitivity"
            )
            if len(c) != r.candidate_events or c.storm_id.nunique() != r.candidate_groups:
                raise ValueError("H1 candidate universe mismatch")
            cache[key] = c.event_id.tolist()
        ids = cache[key]
        selected = groups[(r.cohort, r.scenario, r.analysis, r.arm, r.target_k, r.query_event_id)]
        positive = int(labels.loc[ids, "H3_native"].eq(1).sum())
        selected_positive = int(selected.donor_native_reach.eq(1).sum())
        if selected_positive != r.positive_donors:
            raise ValueError("Saved H1 positive-donor count differs")
        diagnostics.append(
            {
                **dict(
                    zip(
                        keys,
                        (r.cohort, r.scenario, r.analysis, r.arm, r.target_k, r.query_event_id),
                        strict=True,
                    )
                ),
                "positive_candidates": positive,
                "positive_candidate_groups": int(
                    meta.loc[
                        [i for i in ids if labels.loc[i, "H3_native"] == 1], "storm_id"
                    ].nunique()
                ),
                "archive_stage": archive_stage(positive, 0, selected_positive),
                "positive_selected": selected_positive,
                "candidate_event_ids": json.dumps(ids),
            }
        )
    return scores, donors, pd.DataFrame(diagnostics), labels


def saved_comparisons(query_ids):
    specs = [
        (
            "main",
            ROOT / "results/eo_analogue_comparison_coherent_v1",
            ROOT / "results/eo_review_provenance_v2/main",
            False,
        )
    ]
    specs += [
        (
            v,
            ROOT / "results/eo_expansion_comparisons" / v,
            ROOT / "results/eo_review_provenance_v2" / v,
            False,
        )
        for v in FOLLOW.VARIANTS
    ]
    specs += [
        (
            "rain168",
            ROOT / "results/eo_analogue_comparison_rain168_v1",
            ROOT / "results/eo_review_provenance_v2/rain168",
            True,
        )
    ]
    scores, donors, browser = [], [], []
    for name, comparison, review, _is_new in specs:
        record(comparison / "manifest.json")
        for file, dest in [
            ("event_assessments.parquet", scores),
            ("selected_donors.parquet", donors),
        ]:
            p = record(comparison / file)
            f = pq.read_table(p, filters=[("query_event_id", "in", sorted(query_ids))]).to_pandas()
            dest.append(f.assign(source=name))
        f = parquet(review / "browser_case_index.parquet")
        f = f[f.query_event_id.isin(query_ids)].copy()
        f["cohort"] = name + " | " + f.cohort.astype(str)
        browser.append(f)
        print("read", name, "saved comparisons", flush=True)
    # The broad Q-history comparison is retained separately from EO availability.
    base = ROOT / "results/basin_ai_cross_border_completion"
    for file, dest in [("event_assessments.csv", scores), ("selected_donors.csv", donors)]:
        f = csv(base / file)
        f = f[
            f.query_event_id.isin(query_ids)
            & f.cohort.eq("q_only")
            & f.arm.isin(["raw_state", "ttm_ordered_state"])
        ].copy()
        f["kind"] = "512h_q_history"
        dest.append(f.assign(source="full_q"))
    combined_scores = pd.concat(scores, ignore_index=True)
    combined_donors = pd.concat(donors, ignore_index=True)
    for f in [combined_scores, combined_donors]:
        for column in ["query_onset_utc", "analogue_onset_utc"]:
            if column in f:
                f[column] = pd.to_datetime(f[column], utc=True, format="mixed")
    return specs, combined_scores, combined_donors, pd.concat(browser, ignore_index=True)


def response_review(specs, scores, donors, phase_labels, response):
    for name in [
        "q_only_signatures.csv",
        "q_only_standardized_histories.parquet",
        "q_only_ttm_ordered.parquet",
        "q_only_discharge_state.parquet",
    ]:
        record(READY / name)
    record(ROOT / "results/basin_ai_cross_border_completion/rainfall_event_coverage.csv")
    sample, meta, raw, ttm, state, base, old_rain, new_rain, alpha = FOLLOW.inputs()
    obs = parquet(ROOT / "results/eo_comparison_preparation/observations.parquet")
    windows = parquet(ROOT / "results/eo_comparison_preparation/observation_windows.parquet")
    sources = {name: (directory, new) for name, directory, _, new in specs}
    vectors, pools, archives, output = {}, {}, {}, []
    keys = [
        "source",
        "kind",
        "cohort",
        "scenario",
        "analysis",
        "policy",
        "target_k",
        "arm",
        "query_event_id",
    ]
    # Some legacy broad-Q tables store only the ten-donor list, so derive k by rank.
    if donors.source.eq("full_q").any():
        old = donors[donors.source.eq("full_q")].copy()
        if old.target_k.isna().all() or not old.target_k.eq(5).any():
            donors = donors[~donors.source.eq("full_q")]
            donors = pd.concat(
                [donors, old.loc[old["rank"].le(5)].assign(target_k=5), old.assign(target_k=10)],
                ignore_index=True,
            )
    groups = {key: g for key, g in donors.groupby(keys, observed=True)}
    for r in scores.itertuples():
        poolkey = (r.source, r.kind, r.cohort)
        if poolkey not in pools:
            if r.source == "full_q":
                pools[poolkey] = sample
            else:
                directory, new = sources[r.source]
                vkey = (r.source, r.kind)
                if vkey not in vectors:
                    vectors[vkey] = FOLLOW.vectors_for(directory, r.kind, obs, windows)
                pools[poolkey] = FOLLOW.cohort_population(
                    r.cohort, sample, vectors[vkey], new_rain if new else old_rain, alpha
                )
        akey = (poolkey, r.scenario, r.analysis, r.policy, r.query_event_id)
        if akey not in archives:
            pop = pools[poolkey]
            query = pop.set_index("event_id", drop=False).loc[r.query_event_id]
            c = eligible_archive(
                pop, query, r.scenario, r.policy, r.analysis == "quality_sensitivity"
            )
            labels = c.event_id.map(phase_labels.H3_native)
            archives[akey] = (
                c.event_id.tolist(),
                int(labels.eq(1).sum()),
                int(labels.isna().sum()),
            )
        ids, positive, unknown = archives[akey]
        if len(ids) != int(r.candidate_count):
            raise ValueError("Continuous-response candidate universe differs")
        key = tuple(getattr(r, k) for k in keys)
        selected = groups[key]
        if len(selected) != int(r.actual_donor_count):
            raise ValueError("Selected donor count mismatch")
        selected_ids = selected.analogue_event_id.tolist()
        positive_selected = int(pd.Series(selected_ids).map(phase_labels.H3_native).eq(1).sum())
        metrics = curve_diagnostics(
            response.loc[r.query_event_id], response.loc[ids], response.loc[selected_ids]
        )
        best = metrics.pop("oracle_best_candidate_position")
        if not np.isclose(
            metrics["selected_mean_curve_rmse_recomputed"],
            r.ensemble_curve_level_rmse,
            atol=1e-10,
            rtol=1e-10,
        ):
            raise ValueError("Stored trajectory error differs from donor curves")
        output.append(
            {
                **dict(zip(keys, key, strict=True)),
                **metrics,
                "positive_candidates": positive,
                "unlabelled_candidates": unknown,
                "positive_selected": positive_selected,
                "query_native_H3_label": phase_labels.H3_native.get(r.query_event_id, np.nan),
                "archive_stage": archive_stage(positive, unknown, positive_selected),
                "oracle_best_single_event_id": ids[best],
                "oracle_is_selected": ids[best] in selected_ids,
                "oracle_label": "withheld_outcome_diagnostic_not_a_forecast_or_equal_k_comparison",
            }
        )
    return pd.DataFrame(output), donors, vectors, obs, windows


def response_atlas(scores, donors, response, thresholds, meta):
    """All ten encoders, own matched rainfall cohorts; unavailable panels stay explicit."""
    models = sorted(FOLLOW.ROUTES)
    chosen = scores[
        scores.source.eq("rain168")
        & scores.scenario.eq("all_rivers")
        & scores.analysis.eq("main")
        & scores.policy.eq("pooled")
        & scores.target_k.eq(5)
    ]
    d = donors[
        donors.source.eq("rain168")
        & donors.scenario.eq("all_rivers")
        & donors.analysis.eq("main")
        & donors.policy.eq("pooled")
        & donors.target_k.eq(5)
    ]
    paths = []
    for (eid, kind), f in chosen.groupby(["query_event_id", "kind"], observed=True):
        available = f[f.arm.isin([m + "_ttm_state" for m in models])]
        if available.empty:
            continue
        fig, axes = plt.subplots(5, 2, figsize=(14, 15), sharex=True)
        query = response.loc[eid].to_numpy(float)
        hours = np.arange(1, 73)
        for ax, model in zip(axes.flat, models, strict=True):
            cohort = "rain_matched_available_" + model
            own = f[f.cohort.eq(cohort)]
            ax.plot(hours, query, color="black", linewidth=1.7, label="observed query")
            if model + "_ttm_state" not in set(own.arm):
                ax.set_title(model + ": no held matched assessment", fontsize=9)
            else:
                for arm, color, label in [
                    ("conventional", "tab:green", "conventional mean"),
                    ("ttm_state", "tab:orange", "TTM/state mean"),
                    (model + "_ttm_state", "tab:blue", model + "/TTM/state mean"),
                ]:
                    rows = d[
                        d.query_event_id.eq(eid)
                        & d.kind.eq(kind)
                        & d.cohort.eq(cohort)
                        & d.arm.eq(arm)
                    ]
                    if rows.empty:
                        continue
                    curves = response.loc[rows.analogue_event_id].to_numpy(float)
                    if arm == model + "_ttm_state":
                        ax.plot(hours, curves.T, color="0.65", linewidth=0.6, alpha=0.7)
                    ax.plot(hours, curves.mean(axis=0), color=color, linewidth=1, label=label)
                ax.set_title(model + ": model-available matched archive", fontsize=9)
            gauge = meta.loc[eid, "gauge"]
            if gauge in thresholds.index:
                ax.axhline(
                    thresholds.loc[gauge, "H3"] / meta.loc[eid, "p99_m3s"],
                    color="red",
                    linestyle=":",
                    linewidth=0.8,
                )
            ax.set_ylabel("Q / local-era p99")
            ax.grid(alpha=0.12)
            ax.legend(fontsize=6, loc="upper right")
        for ax in axes[-1]:
            ax.set_xlabel("Hours after p99 cutoff")
        fig.suptitle(
            eid
            + " | "
            + kind
            + "\nSaved main/pooled/k5 selections. Each panel has its own model-available archive; no cross-panel ranking.",
            fontsize=11,
        )
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        name = (
            "response_"
            + eid.replace("|", "_").replace(":", "").replace("+", "_")
            + "_"
            + kind
            + ".png"
        )
        fig.savefig(OUT / name, dpi=130)
        plt.close(fig)
        paths.append({"query_event_id": eid, "kind": kind, "path": name})
    return paths


def representation_coverage(specs, vectors, obs, windows, links, inventory, scores):
    rows = []
    indexed = inventory.set_index("event_id")
    for source, directory, _, _ in specs:
        for kind in ["monthly_snapshot", "monthly", "recent"]:
            key = (source, kind)
            if key not in vectors:
                vectors[key] = FOLLOW.vectors_for(directory, kind, obs, windows)
            for model, values in vectors[key].items():
                scored = set(
                    scores.loc[
                        scores.source.eq(source)
                        & scores.kind.eq(kind)
                        & scores.arm.isin([model + "_only", model + "_ttm_state"]),
                        "query_event_id",
                    ]
                )
                for e in links.itertuples():
                    rows.append(
                        {
                            "case_id": e.case_id,
                            "event_id": e.event_id,
                            "match_status": e.match_status,
                            "source": source,
                            "kind": kind,
                            "model": model,
                            "past_representation_available": e.event_id in values.index,
                            "exact_future_Q_score_admissible": bool(
                                indexed.loc[e.event_id, "q_only_scoring_sample"]
                            ),
                            "saved_model_assessment_available": e.event_id in scored,
                        }
                    )
    return pd.DataFrame(rows)


def observations():
    native, audit, ingest = WARN.read_native()
    record(audit.SOURCE)
    hourly = csv(
        ROOT / "data/interim/event_study_discharge_hourly.csv", ["timestamp_utc"]
    ).set_index("timestamp_utc")
    stage = {}
    # Reuse the source parser's verified units/timezone; do not reconstruct German Q.
    german = load_script("72_german_wurm_analogue_extension.py", "flood_native_german")
    for station, (gauge, name) in german.STATIONS.items():
        for parameter, pattern in [
            ("Abfluss", "*abfluss_mit_m_s_csv_export_mittelwerte_15minuten*.csv"),
            ("Wasserstand", "*wasserstand_mit_cm_csv_export_mittelwerte_15minuten*.csv"),
        ]:
            (p,) = (german.SOURCE / station).glob(pattern)
            q = german.read_quarters(record(p), gauge, name, parameter)
            if parameter == "Abfluss":
                native[gauge] = q.reindex(native.index)
                hourly[gauge] = german.complete_hourly(q).reindex(hourly.index)
            else:
                stage[gauge] = q
    return native, hourly, stage


def timeline(case, native, stage, thresholds, links, path):
    axes_count = 2 if case.gauge in stage else 1
    fig, axes = plt.subplots(
        axes_count, 1, figsize=(12, 4.8 if axes_count == 1 else 7), squeeze=False
    )
    ax = axes[0, 0]
    local = links[links.case_id.eq(case.case_id)]
    start = case.start
    if (
        not local.empty
        and not local.match_status.eq("coarse_documentary_candidate_not_flood_label").all()
    ):
        start = min(start, local.onset_utc.min())
    q = native[case.series_key].loc[start - pd.Timedelta(hours=24) : case.end]
    coarse = case.date_precision in {"year_only", "early_month_statement_month_review_window"}
    if case.date_precision == "year_only":
        q = q.resample("D").max()
    ax.plot(
        q.index,
        q,
        color="black",
        linewidth=0.9,
        label="reported Q (not necessarily exact at high flow)",
    )
    if case.gauge in thresholds.index:
        for level, color in [("H1", "goldenrod"), ("H2", "darkorange"), ("H3", "red")]:
            ax.axhline(
                thresholds.loc[case.gauge, level],
                color=color,
                linestyle="--",
                linewidth=0.8,
                label="current " + level,
            )
    for e in links[links.case_id.eq(case.case_id)].itertuples():
        if not coarse:
            ax.axvline(e.onset_utc, color="tab:blue", linewidth=0.7, alpha=0.7)
            ax.axvline(
                e.onset_utc + pd.Timedelta(hours=72), color="tab:blue", linestyle=":", linewidth=0.7
            )
    if pd.notna(case.first_H3_utc):
        ax.axvline(case.first_H3_utc, color="red", linewidth=1.3, label="first recorded H3")
    ax.set_ylabel("Reported discharge (m³/s)")
    ax.set_title(
        case.case_id + " | " + case.evidence_type + "\n" + case.date_precision, fontsize=10
    )
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(alpha=0.15)
    if axes_count == 2:
        s = stage[case.gauge].loc[start - pd.Timedelta(hours=24) : case.end]
        if case.date_precision == "year_only":
            s = s.resample("D").max()
        axes[1, 0].plot(s.index, s, color="tab:purple", linewidth=0.9)
        axes[1, 0].set_ylabel("Local stage (cm; not harmonized)")
        axes[1, 0].grid(alpha=0.15)
    axes[-1, 0].set_xlabel(
        "UTC; blue lines: p99 cutoff / dotted: its fixed 72-hour endpoint. Gaps remain missing."
    )
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def pages(
    register,
    links,
    hlinks,
    phase_scores,
    phase_diag,
    response_scores,
    response_diag,
    browser,
    native,
    stage,
    thresholds,
    meta,
    response,
    coverage,
    atlas,
):
    (OUT / "cases").mkdir()
    for kind in ["monthly_snapshot", "monthly", "recent"]:
        f = browser[browser.kind.eq(kind)]
        if f.empty:
            continue
        page = REVIEW.browser_page(
            f,
            meta,
            response,
            "Held analogues for date-resolved flood-review queries: " + kind,
            provenance_note="Source names prefix displayed cohort IDs. Frozen results filtered to review queries; no model rerun. Dutch provider_status is July 2021 gauge context. H3 is not an independent inundation map.",
        )
        page = page.replace(
            "Every scored main, pooled, five-donor case in the available-model cohorts is selectable.",
            "Every held main/pooled/five-donor available-model record for the date-resolved review queries is selectable.",
        )
        (OUT / ("analogues_" + kind + ".html")).write_text(page)
    index = [
        "<!doctype html><meta charset='utf-8'><title>Flood case census</title><h1>Source-bounded flood case review</h1><p>Current H3, documented impacts and uncertain documentary dates remain distinct. No physical-flood completeness claim or new model ranking.</p><ul>"
    ]
    for case in register.itertuples():
        name = case.case_id.replace(".", "_")
        timeline(case, native, stage, thresholds, links, OUT / "cases" / (name + ".png"))
        x = links[links.case_id.eq(case.case_id)]
        h = hlinks[hlinks.case_id.eq(case.case_id)]
        ps = phase_scores[
            phase_scores.query_event_id.isin(h.event_id)
            & phase_scores.analysis.eq("main")
            & phase_scores.scenario.eq("all_rivers")
            & phase_scores.target_k.eq(5)
        ]
        phase_keys = ["cohort", "scenario", "analysis", "arm", "target_k", "query_event_id"]
        ps = ps.merge(
            phase_diag[phase_keys + ["positive_candidates", "archive_stage"]],
            on=phase_keys,
            how="left",
            validate="one_to_one",
        )
        cs = response_diag[
            response_diag.query_event_id.isin(
                x.loc[x.match_status.eq("date_resolved_episode_overlap"), "event_id"]
            )
            & response_diag.analysis.eq("main")
            & response_diag.scenario.eq("all_rivers")
            & response_diag.policy.eq("pooled")
            & response_diag.target_k.eq(5)
        ]
        parts = [
            "<!doctype html><meta charset='utf-8'><style>body{font:15px system-ui;margin:25px}table{border-collapse:collapse;font-size:12px}td,th{border:1px solid #bbb;padding:4px}img{max-width:100%}</style>",
            "<h1>" + html.escape(case.case_id) + "</h1><p>" + html.escape(case.note) + "</p>",
            "<p>Evidence: "
            + html.escape(
                case.evidence_type
                + "; "
                + case.impact_confirmation
                + "; sources "
                + case.source_ids
            )
            + "</p>",
            "<img src='" + name + ".png'><h2>Every linked p99 inventory event / candidate</h2>",
            x.to_html(index=False, escape=True),
            "<h2>H1 assessment linkage</h2>",
            h.to_html(index=False, escape=True),
            "<details><summary>Past representation versus exact-future-score support (main archive)</summary>",
            coverage[coverage.case_id.eq(case.case_id) & coverage.source.eq("main")].to_html(
                index=False, escape=True
            ),
            "</details>",
            "<h2>Saved H1-to-H3 estimates: main/all-river/k5</h2><p>Different cohorts have different archives; donor shares are not calibrated probabilities.</p>",
            ps[
                [
                    c
                    for c in [
                        "cohort",
                        "arm",
                        "query_event_id",
                        "observed_reach",
                        "actual_donors",
                        "positive_donors",
                        "positive_candidates",
                        "archive_stage",
                        "donor_reach_share",
                        "generic_archive_share",
                        "share_squared_error",
                    ]
                    if c in ps
                ]
            ].to_html(index=False, escape=True),
            "<h2>Continuous-response availability, retrieval and estimation diagnostics</h2><p>Oracle uses withheld outcomes after the fact and cannot be used for forecast selection. Single-trajectory versus ensemble differences are diagnostic, not equal-k performance tests. Coarse-date candidates receive no flood-specific performance verdict.</p>",
            cs[
                [
                    c
                    for c in [
                        "source",
                        "kind",
                        "cohort",
                        "arm",
                        "query_event_id",
                        "query_native_H3_label",
                        "positive_candidates",
                        "unlabelled_candidates",
                        "positive_selected",
                        "archive_stage",
                        "selected_mean_curve_rmse_recomputed",
                        "oracle_best_single_curve_rmse",
                        "peak_estimate_pattern",
                    ]
                    if c in cs
                ]
            ].to_html(index=False, escape=True),
            "<p>Full settings, donor IDs, quality sensitivities and candidate universes are retained in the parent parquet tables. <a href='../index.html'>Register</a></p>",
        ]
        parts.append(
            "<h2>Actual selected-donor response atlas</h2><p>Grey: individual EO-selected donor responses; coloured lines: saved method means. Recovery assessments are not new flood-onset predictions.</p>"
        )
        parts += [
            "<p>"
            + html.escape(a["query_event_id"] + " | " + a["kind"])
            + "</p><img src='../"
            + a["path"]
            + "'>"
            for a in atlas
            if a["query_event_id"] in set(x.event_id)
        ]
        (OUT / "cases" / (name + ".html")).write_text("\n".join(parts))
        index.append(
            "<li><a href='cases/"
            + name
            + ".html'>"
            + html.escape(case.case_id)
            + "</a> — "
            + html.escape(case.evidence_type)
            + "</li>"
        )
    index += [
        "</ul><p>Actual selected-analogue browsers: "
        + " ".join(
            "<a href='analogues_" + k + ".html'>" + k + "</a>"
            for k in ["monthly_snapshot", "monthly", "recent"]
            if (OUT / ("analogues_" + k + ".html")).exists()
        )
        + "</p>"
    ]
    (OUT / "index.html").write_text("\n".join(index))


def main():
    global OUT
    evidence = json.loads(record(ROOT / "config/limburg_flood_review_evidence.json").read_text())
    for source in evidence["sources"]:
        p = record(ROOT / source["path"])
        receipt = p.with_suffix(p.suffix + ".receipt.json")
        if receipt.exists() and sha256(p) != json.loads(record(receipt).read_text())["sha256"]:
            raise ValueError("Documentary snapshot changed")
    episodes = csv(PHASE / "episodes.csv")
    record(PHASE / "manifest.json")
    entry_status = csv(PHASE / "episode_phase_progression.csv")
    entry_status = entry_status[entry_status.level.eq("H3")].set_index("episode_id")
    episodes["H3_entry_status"] = episodes.episode_id.map(entry_status.entry_status)
    inventory = csv(
        ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/event_inventory.csv",
        ["onset_utc", "last_crossing_utc"],
    )
    meta = csv(READY / "event_inventory.csv", ["onset_utc"]).set_index("event_id", drop=False)
    register = build_register(episodes, evidence, set(inventory.gauge))
    links = link_inventory(register, inventory)
    hmeta = csv(PHASE / "H1_assessment_inventory.csv", ["onset_utc"])
    hlinks = h1_links(register, episodes, hmeta)
    hscore, hdonors, hdiag, hlabels = phase_review(hlinks, hmeta)
    for column in ["H3_native", "H3_below_cutoff", "response_observed_quarters"]:
        hlinks[column] = hlinks.event_id.map(hlabels[column])
    resolved = links[links.match_status.eq("date_resolved_episode_overlap")]
    query_ids = set(resolved.loc[resolved.q_only_scoring_sample, "event_id"])
    specs, scores, donors, browser = saved_comparisons(query_ids)
    response = parquet(
        ROOT / "results/basin_ai_event_definition_sensitivity/p99_72/response_p99.parquet"
    )
    p99labels = csv(PHASE / "all_p99_event_phase_outcomes.csv").set_index("event_id")
    diag, donors, vectors, obs, windows = response_review(
        specs, scores, donors, p99labels, response
    )
    coverage = representation_coverage(specs, vectors, obs, windows, links, inventory, scores)
    native, hourly, stage = observations()
    thresholds = csv(PHASE / "current_thresholds.csv").set_index("gauge")
    destination = OUT
    with fresh_output(destination) as temp:
        OUT = temp
        for name, frame in [
            ("register", register),
            ("event_links", links),
            ("H1_links", hlinks),
            ("H1_scores", hscore),
            ("H1_selected_donors", hdonors),
            ("H1_diagnostics", hdiag),
            ("representation_coverage", coverage),
            ("continuous_scores", scores),
            ("continuous_selected_donors", donors),
            ("continuous_diagnostics", diag),
        ]:
            frame.to_parquet(OUT / (name + ".parquet"), index=False)
        donor_audit = REVIEW.audit_donors(donors, meta)
        for (scenario, analysis, _cohort, _arm, _k), group in hdonors.groupby(
            ["scenario", "analysis", "cohort", "arm", "target_k"], observed=True
        ):
            WARN.validate_phase_donors(
                group,
                hmeta.set_index("event_id"),
                hlabels,
                "H3",
                scenario,
                analysis == "quality_sensitivity",
            )
        (OUT / "donor-audit.json").write_text(
            json.dumps(
                {"continuous_violations": donor_audit, "H1_donor_rows_checked": len(hdonors)},
                indent=2,
            )
            + "\n"
        )
        atlas = response_atlas(scores, donors, response, thresholds, meta)
        pages(
            register,
            links,
            hlinks,
            hscore,
            hdiag,
            scores,
            diag,
            browser,
            native,
            stage,
            thresholds,
            meta,
            response,
            coverage,
            atlas,
        )
        summary = {
            "register_rows": len(register),
            "native_H3_rows": int(register.evidence_type.eq("current_H3_recorded_reach").sum()),
            "core_native_H3_rows": int(
                (register.primary & register.evidence_type.eq("current_H3_recorded_reach")).sum()
            ),
            "date_resolved_scored_p99_queries": len(query_ids),
            "scored_preflood_p99_queries": int(
                resolved.loc[
                    resolved.q_only_scoring_sample & resolved.timing_role.eq("H3_within_72h"),
                    "event_id",
                ].nunique()
            ),
            "scored_recovery_queries": int(
                resolved.loc[
                    resolved.q_only_scoring_sample & resolved.timing_role.eq("after_first_H3"),
                    "event_id",
                ].nunique()
            ),
            "response_atlas_figures": len(atlas),
            "source_bound_scope": evidence["scope"],
            "oracle_role": "Post-outcome error diagnostic only; never used for retrieval or tuning",
            "unknown_labels": "Unlabelled German/non-complete flood outcomes are not negatives",
        }
        (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        manifest = {
            "status": "completed",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "input_sha256": PROVENANCE,
            "source_sha256": {
                str(p.relative_to(ROOT)): sha256(p)
                for p in [
                    Path(__file__),
                    ROOT / "src/flood_case_review.py",
                    ROOT / "src/eo_followup.py",
                    ROOT / "src/eo_comparison.py",
                    ROOT / "scripts/137_eo_archive_and_route_followup.py",
                    ROOT / "scripts/135_review_eo_followup.py",
                    *ROOT.glob("scripts/[678][0-9]_*.py"),
                ]
            },
            "outputs_sha256": {
                str(p.relative_to(OUT)): sha256(p) for p in OUT.rglob("*") if p.is_file()
            },
        }
        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
