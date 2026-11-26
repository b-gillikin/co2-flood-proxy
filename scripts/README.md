# Live scripts

## Current discharge reconstruction — 24 November 2026

| Work | Entry point |
| --- | --- |
| C1 and C2 preparation and fitting | `292_run_c1_multiyear.py` and `294_run_c2_multiyear.py` |
| C2 with 2017 AlphaEarth | `295_run_c2_alphaearth_2017.py` |
| High-water attribution and seasonality | `296_attribute_c2_high_water.py` and `300_review_dise_seasonality.py` |
| Rimburg and Meuse context | `297_meuse_peak_timing.py` (audit, then run), `298_compare_rimburg_discharge_products.py` and `299_check_meuse_grrr_context.py` |
| Geospatial verification | `301_audit_dise_geospatial.py` |

The [handoff](../docs/HANDOFF.md) gives the evidence status and input paths.
Launch each fitting runner in its own process with `.venv-dise/bin/python`.
Each runner configures its copy of the shared worker for its own output and
feature set. The review scripts accept `--output` for a separate
reproduction directory.

Run the focused discharge tests from the chapter root. Older EO tests use
the foundation environment and include imports from `src` on `PYTHONPATH`.

```bash
export PROJ_DATA="$(.venv-dise/bin/python -c 'import pathlib, sys; print(pathlib.Path(sys.base_prefix) / "share/proj")')"
.venv-dise/bin/python -m pytest -q tests/test_dise*.py tests/test_alphaearth*.py \
  tests/test_geoglows*.py tests/test_meuse_context.py tests/test_grrr_reanalysis.py
```

## Earlier DISE continuation — 18 November 2026

`277_assess_dise_repeatability.py` implements completed Step 3 using the frozen
`276_run_dise_multiyear.py` predictions. It checks paired uncertainty, year/river
influence and all available largest-flow windows without refitting. See
`docs/limburg-dise-repeatability-2026-11-18.md` and
`config/limburg_dise_repeatability_v1.json`. Step 4 remains pending.

## Historical entry points — 28 October 2026

The [monitoring-loss implementation plan](../docs/limburg-monitoring-implementation-plan-2026-10-28.md)
governed the next analysis at that date. The statuses below are historical;
the current discharge analysis is listed above.

| Role | Entry points | Status/contract |
| --- | --- | --- |
| Soil/snow acquisition | `150_fetch_monitoring_land_state.py --download` | One CDS request at a time under the provider's current guidance; resumes verified sources/request IDs and stops on policy errors. |
| Causal-clock EO inventory | `151_prepare_monitoring_eo_gaps.py` | Versioned held/regional-candidate calendars and exact completed-window requirements; does not score events or replace old inputs. |
| Targeted EO additions | `152_download_monitoring_eo_gaps.py --download` | Completed 442-file local pull; reuse the held sources, do not start a full encoder extraction queue. |
| Latest completed scientific pass | `146_run_limburg_assessment.py`, `149_resample_limburg_assessment.py`, `147_review_limburg_assessment.py`, `148_audit_limburg_assessment.py` | Full-information synthesis, archive decomposition and Meuse comparison; preserve their source/input hashes. |
| Flood-case evidence | `143_review_flood_cases.py`, `144_audit_flood_case_review.py` | Retrospective source-bounded case review, not operational flood classification. |

Completed-run source files are preserved when formatting affects their hash;
the compatibility registry and source snapshots record the exact old version and
AST-equivalence proof. Generated scientific outputs and original receipts are
not rewritten as a cleanup operation.

For earlier external flood-map reproductions, `238_archive_chapter_predictions.py`
checks each Azure readback against the upload and retains the small prediction
and radar-valid arrays used by `242_score_chapter_archives.py`. Keep the
`evaluation/compact` files until scoring finishes. Their hashes are recorded
in the archive ledger, so scoring can use them without downloading the large
tar again. If the compact inputs are absent or the ledger predates this
workflow, the scorer can still restore the archive.

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
