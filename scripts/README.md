# Live scripts

## Current entry points — 28 October 2026

The [monitoring-loss implementation plan](../docs/limburg-monitoring-implementation-plan-2026-10-28.md)
governs the next analysis. Its simulation/scoring runner is not implemented yet.
Acquisition is independent of the completed historical analyses below.

| Role | Entry points | Status/contract |
| --- | --- | --- |
| Soil/snow acquisition | `150_fetch_monitoring_land_state.py --download` | One CDS request at a time under the provider's current guidance; resumes verified sources/request IDs and stops on policy errors. |
| Causal-clock EO inventory | `151_prepare_monitoring_eo_gaps.py` | Versioned held/regional-candidate calendars and exact completed-window requirements; does not score events or replace old inputs. |
| Targeted EO additions | `152_download_monitoring_eo_gaps.py --download` | Completed 442-file local pull; reuse the held sources, do not start a full encoder extraction queue. |
| Latest completed scientific pass | `146_run_limburg_assessment.py`, `149_resample_limburg_assessment.py`, `147_review_limburg_assessment.py`, `148_audit_limburg_assessment.py` | Full-information synthesis, archive decomposition and Meuse comparison; preserve their source/input hashes. |
| Flood-case evidence | `143_review_flood_cases.py`, `144_audit_flood_case_review.py` | Retrospective source-bounded case review, not operational flood classification. |

Run the whole active-code checks from the chapter root with
`make -j2 check PYTHON=.venv-foundation/bin/python`. This overlaps local lint/tests;
it does not parallelize CDS submissions. The Makefile finds the existing runtime's
PROJ data unless explicitly supplied. No dataset, model or environment upgrade is
performed by these checks.

Completed-run source files are preserved when formatting affects their hash;
the compatibility registry and source snapshots record the exact old version and
AST-equivalence proof. Generated scientific outputs and original receipts are
not rewritten as a cleanup operation.

## Evidence and execution roles

Earlier analysis/interpretation runners: **81–84**. Supporting controls: **75–78**;
independent audit: **79**. Scripts **70–74** are original execution/development
and **80** prepares expanded inputs. Preserve them in place because later
runners depend on their code or artifacts; they are not independent chapter
experiments to present by default. See the
[evidence index](../docs/limburg-analogue-evidence-index-2026-10-14.md).

The active code prepares audited basin evidence and evaluates one bounded
basin-aware AI design. Number gaps identify scripts moved to the historical
archive; they are not missing dependencies.

Scripts 25, 31–35, 37 and 39–46 preserve the acquisition, source-semantics,
catchment, rainfall, weather, rating and event-review chain. See
`docs/analysis-inventory.md` for each file's role.

```bash
python scripts/64_build_basin_ai_event_library.py
python scripts/65_hydrological_analogue_baseline.py
python scripts/66_download_limburg_foundation_assets.py
python scripts/68_import_alphaearth_embeddings.py
python scripts/69_raw_hydrograph_analogue_baseline.py
```

Script 63 and its four-arm RAG pilot are archived under
`../archive/retired-basin-ai-pilot/`. Script 64 defaults to the
fixed 512-hour TTM-R2 history and 72 withheld hours. Script
65 retrieves strictly earlier events from different storms. Script 66 is a dry
run unless `--download` is supplied.

Script 68 validates the held AlphaEarth table against its delivery and native
catchment geometry receipts, then joins prior-year embeddings to events.
Script 69 standardizes each eligible 512-hour discharge history, runs R1
through the same prior-storm retrieval function as R0, and writes paired
comparisons plus the existing measurement-concern sensitivity.

```bash
python scripts/67_export_alphaearth_embeddings.py --project YOUR_EE_PROJECT
```

Raw data, weights and generated results remain outside Git; contracts,
manifests and receipts are versioned. Historical scripts and tests are under
`archive/retired-directions/2026-retrospective-high-water/` and excluded from
live lint/test discovery.

Script 84 completes the held-data country comparison in separate outputs:
pooled/domestic/foreign archives; matched country-specific temporal and context
controls; German rainfall derived from the held radar crop; coverage and paired
quality/donor-count sensitivities. Its default country policy in the shared
retriever preserves earlier runs. No training or download.

Script 85 independently audits script 84's saved six pair metrics and country
summary means. It verifies numerical input, source and output fingerprints
before reading; it does not rerank donors or assign human judgments.
