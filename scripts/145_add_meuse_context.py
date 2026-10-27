"""Include held Meuse context in every tributary query and saved flood-case donor.

No retrieval, EO extraction, model fitting or causal confluence attribution.
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
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.eo_inputs import sha256
from src.eo_integrity import fresh_output
from src.meuse_context import hourly_context, source_rows, state_at_cutoff

OUT = ROOT / "results/meuse_context_2026_10_27"
INVENTORY = ROOT / "results/basin_ai_event_interpretation_ready/event_inventory.csv"
FLOOD = ROOT / "results/flood_case_review_2026_10_27"
SITES = {"sint_pieter": "maastricht.sintpieter", "venlo": "venlo"}


def main():
    inputs = {}

    def record(path):
        inputs[str(path.relative_to(ROOT))] = sha256(path)
        return path

    inventory = pd.read_csv(record(INVENTORY), low_memory=False)
    assert inventory.event_id.is_unique
    inventory["onset_utc"] = pd.to_datetime(inventory.onset_utc, utc=True)
    register = pd.read_parquet(record(FLOOD / "register.parquet"))
    donors = pd.read_parquet(record(FLOOD / "continuous_selected_donors.parquet"))
    events = inventory[
        [
            "event_id",
            "onset_utc",
            "gauge",
            "watercourse",
            "country",
            "storm_id",
            "q_only_input_sample",
            "q_only_scoring_sample",
        ]
    ].copy()
    # Include saved donors missing from this inventory, if any; never silently lose a join.
    additional = donors[["analogue_event_id", "analogue_onset_utc"]].drop_duplicates()
    for row in additional.itertuples():
        if row.analogue_event_id not in set(events.event_id):
            raise ValueError(f"Saved donor missing inventory: {row.analogue_event_id}")
    start_year = int(events.onset_utc.dt.year.min())
    end_year = int(events.onset_utc.dt.year.max())
    with fresh_output(OUT) as work:
        series, audits, coverage = {}, [], []
        for site, filename in SITES.items():
            frames = []
            for year in range(2000, end_year + 1):
                path = ROOT / f"data/raw/discharge/rws/{filename}_{year}.json"
                if not path.exists():
                    audits.append(dict(site=site, year=year, missing_file=True))
                    continue
                frame, blocks = source_rows(json.loads(record(path).read_text()))
                frames.append(frame)
                audits.append(dict(site=site, year=year, blocks=blocks, missing_file=False))
            f = hourly_context(
                pd.concat(frames, ignore_index=True), "2000-01-01", f"{end_year + 1}-01-01"
            )
            series[site] = f
            f.to_parquet(work / f"{site}_hourly.parquet")
            for year, subset in f.groupby(f.index.year):
                if year > end_year:
                    continue
                coverage.append(
                    dict(
                        site=site,
                        year=int(year),
                        hours=len(subset),
                        strict_hours=int(subset.q_strict.notna().sum()),
                        display_hours=int(subset.q_display.notna().sum()),
                        interpolated_readings=int(subset.n_interpolated.sum()),
                    )
                )
            print(
                f"{site}: source parsed; {f.q_strict.notna().sum()} strict hourly values",
                flush=True,
            )
        contexts = []
        for row in events.itertuples():
            state = {}
            for site, f in series.items():
                state.update(
                    {
                        f"{site}_{key}": value
                        for key, value in state_at_cutoff(f, row.onset_utc).items()
                    }
                )
            contexts.append(state)
        events = pd.concat([events.reset_index(drop=True), pd.DataFrame(contexts)], axis=1)
        events.to_parquet(work / "event_context.parquet", index=False)
        pd.DataFrame(coverage).to_csv(work / "coverage_by_year.csv", index=False)
        (work / "source_blocks.json").write_text(json.dumps(audits, indent=2))
        # Inspect actual saved choices; do not select or rerank with these contexts.
        pairs = donors[["query_event_id", "analogue_event_id"]].drop_duplicates()
        lookup = events.set_index("event_id")
        for site in SITES:
            col = f"{site}_prior_year_rank"
            pairs[f"{site}_query_rank"] = pairs.query_event_id.map(lookup[col])
            pairs[f"{site}_donor_rank"] = pairs.analogue_event_id.map(lookup[col])
            pairs[f"{site}_absolute_rank_difference"] = (
                pairs[f"{site}_query_rank"] - pairs[f"{site}_donor_rank"]
            ).abs()
        pairs.to_parquet(work / "saved_flood_donor_context.parquet", index=False)
        # Case summaries retain native register precision; year-only evidence is not an onset.
        case_rows = []
        for row in register.itertuples():
            precise = row.date_precision not in {
                "year_only",
                "early_month_statement_month_review_window",
            }
            for site, f in series.items():
                window = f.loc[row.start : row.end]
                case_rows.append(
                    dict(
                        case_id=row.case_id,
                        site=site,
                        date_precision=row.date_precision,
                        hours=len(window),
                        strict_hours=int(window.q_strict.notna().sum()),
                        display_hours=int(window.q_display.notna().sum()),
                        interpolated_readings=int(window.n_interpolated.sum()),
                        observed_strict_max_m3s=window.q_strict.max(),
                        observed_display_max_m3s=window.q_display.max(),
                        strict_window_complete=bool(len(window) and window.q_strict.notna().all()),
                        date_resolved_review_window=precise,
                    )
                )
        cases = pd.DataFrame(case_rows)
        cases.to_csv(work / "case_context.csv", index=False)
        # Four resolved regional episodes, including 2014 where quality may be poor.
        plots = []
        for label, first, last in [
            ("2014-07", "2014-07-06", "2014-07-15"),
            ("2018-04", "2018-04-27", "2018-05-06"),
            ("2021-07", "2021-07-10", "2021-07-22"),
            ("2024-05", "2024-05-14", "2024-05-25"),
        ]:
            fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
            for ax, (site, f) in zip(axes, series.items(), strict=True):
                window = f.loc[first:last]
                ax.plot(
                    window.index,
                    window.q_display,
                    color="orange",
                    linestyle="--",
                    label="Broader controlled codes: may include interpolation",
                )
                ax.plot(window.index, window.q_strict, color="navy", label="Controlled code 00")
                for case in register.itertuples():
                    if (
                        pd.notna(case.first_H3_utc)
                        and window.index.min() <= case.first_H3_utc <= window.index.max()
                    ):
                        ax.axvline(case.first_H3_utc, color="grey", alpha=0.35)
                if window.q_display.isna().all() and window.q_strict.isna().all():
                    ax.text(
                        0.5,
                        0.5,
                        "No eligible high-frequency discharge in held files",
                        transform=ax.transAxes,
                        ha="center",
                        fontsize=10,
                    )
                ax.set_ylabel(f"{site}: Q m³/s")
                ax.legend(fontsize=7, loc="upper left")
                ax.grid(alpha=0.2)
            axes[0].set_title(
                "Meuse context; grey lines = recorded tributary H3 reaches (not Meuse thresholds)"
            )
            axes[1].set_xlabel(
                "UTC; centred F103 support ends before hourly label; gaps remain missing"
            )
            fig.tight_layout()
            name = f"meuse_{label}.png"
            fig.savefig(work / name, dpi=140)
            plt.close(fig)
            plots.append(name)
        missing = {}
        for site in SITES:
            missing[site] = dict(
                total_events=len(events),
                strict_cutoff_available=int(events[f"{site}_q_strict_m3s"].notna().sum()),
                prior_rank_available=int(events[f"{site}_prior_year_rank"].notna().sum()),
                display_cutoff_available=int(events[f"{site}_q_display_m3s"].notna().sum()),
            )
        summary = dict(
            events=len(events),
            census_years=[start_year, end_year],
            event_support=missing,
            saved_unique_query_donor_pairs=len(pairs),
            register_cases=len(register),
            results_role="observational context; no changed model scores",
        )
        (work / "summary.json").write_text(json.dumps(summary, indent=2))
        body = (
            "<h1>Meuse context for tributary analogues</h1><p>Retrospective source-quality review. "
        )
        body += (
            "No reranking or new predictive result. Missing strict discharge is unknown, not zero. "
        )
        body += "Prior-year empirical ranks are descriptive, not flood stages. No causal backwater inference.</p>"
        body += "<pre>" + html.escape(json.dumps(summary, indent=2)) + "</pre>"
        body += "<h2>All source-bounded flood cases</h2>" + cases.to_html(index=False)
        body += "".join(
            f'<h2>{name}</h2><img style="max-width:100%" src="{name}">' for name in plots
        )
        body += "<p>Detailed data: event_context.parquet; saved_flood_donor_context.parquet; "
        body += "coverage_by_year.csv; source_blocks.json. "
        body += '<a href="../flood_case_review_2026_10_27/index.html">Original tributary case review</a></p>'
        (work / "index.html").write_text(
            '<!doctype html><html><head><meta charset="utf-8">'
            "<title>Meuse context</title></head><body>" + body + "</body></html>"
        )
        manifest = dict(
            status="completed",
            created_utc=datetime.now(timezone.utc).isoformat(),
            inputs_sha256=inputs,
            source_sha256={
                str(p.relative_to(ROOT)): sha256(p)
                for p in [
                    Path(__file__).resolve(),
                    ROOT / "src/meuse_context.py",
                    ROOT / "tests/test_meuse_context.py",
                ]
            },
            hourly_rule="F103 support-end ceil to hour; at least 4 distinct readings; no fill",
            strict_codes=["00"],
            display_codes=["00", "10", "20", "25", "30", "40"],
            rank_rule="strict hourly empirical CDF using earlier calendar years only",
            runtime_assertions=[
                "unique inventory",
                "every saved donor has an inventory row",
                "no conflicting source timestamps",
            ],
            outputs_sha256={
                str(p.relative_to(work)): sha256(p) for p in work.rglob("*") if p.is_file()
            },
        )
        (work / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
