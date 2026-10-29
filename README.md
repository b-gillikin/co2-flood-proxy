Final ten-experiment design audit (29 October): [findings and corrected contracts](docs/reviews/limburg-ten-experiment-design-audit-2026-10-29.md). Explicit raw-only/zero-EO choice, same-scenario ground inputs, causal transfer residuals, paired fallback, mm/h scoring, donor-median reference and matched ablations replace ambiguous initial choices. No scientific run launched. Disk Cleanup completed: about 13.0 GiB recovered by retiring the superseded original-mask OlmoEarth cache after metadata verification; active downloads, selected corrected outputs, raw data, weights, completed results and other chapters remain protected.

Current work: [ten individual encoder experiments — implementation and execution](docs/limburg-individual-experiments-implementation-2026-10-29.md). The local queue prepares/extracts/scores each model according to its own design, using at most one MPS worker and two CPU workers. Live status: `results/limburg_individual_experiments_v1/queue/progress.json`. Prior numerical results remain intact; engineering checks do not establish new findings.

Ten individual experiments planned (29 October): [six-part designs](docs/limburg-ten-individual-experiments-plan-2026-10-29.md), [readiness sweep](docs/reviews/limburg-ten-experiment-readiness-2026-10-29.md). Model-specific hypotheses, inputs/readouts, equal-input raw comparators and strong conventional references are specified. Eight targeted extraction routes, two initial cache-reuse experiments. No new model/scoring run launched; shared residual/transfer and feature builders still need implementation. Existing results remain common-interface evidence.

Individual encoder-use review (29 October): [model-by-model documentation, literature and held-data assessment](docs/reviews/limburg-individual-encoder-use-review-2026-10-29.md). Separates each checkpoint's appropriate role, cached-output options and targeted re-encoding possibilities. Recommends model-specific antecedent-state use, starting with held Presto cadence and existing product-domain evidence; no new extraction/scoring launched. Earlier completed findings remain intact.

Model-specific signal diagnostics (29 October): Brian authorized real-versus-seasonal-placebo retrieval, earlier-year learned readouts and representation-variation checks. [Protocol](docs/limburg-eo-signal-diagnostic-2026-10-29.md) and [implementation](docs/reviews/limburg-eo-signal-implementation-2026-10-29.md). Scripts 164–166 run all ten models separately, both readouts and the full initial-landmark event census under three conditions; no new extraction. All 20 jobs and full audit/review are complete: [findings](docs/limburg-eo-signal-findings-2026-10-29.md). Learned readouts extract small model-dependent increments, notably recent Presto/AnySat, but do not reliably beat the original conventional mean trajectory. Preserve the completed negative fixed-retrieval findings below.

Completed scarcity findings (29 October): all 180 jobs, full audit and automated review finished. [First numerical interpretation](docs/limburg-scarcity-results-2026-10-29.md): EO augmentation does not beat conventional matching on average in any primary whole-census model/scenario/offset cell; high-water/model-supported populations, monthly snapshots and measured-support checks retain the negative overall direction. Thinning sometimes improves the matcher, requiring an algorithmic weighting interpretation rather than a sensor-removal recommendation. Earlier running snapshots below preserve their dated status.

Corrected scarcity implementation (28 October, following design audit): [docs/executable protocol](docs/limburg-scarcity-executable-protocol-2026-10-28.md) governs scripts 159–163. The separate v2 run adds combined sparse networks/feeds, donor-support sensitivity, high-water/EO-support coverage, explicit whole-year/shared-mask uncertainty and a bridge to the prior local method. No new acquisition or embeddings. Run/progress: `results/limburg_scarcity_v2_2026_10_28/`; the original v1 preparation/benchmark and source snapshot remain preserved. Brian writes prose and sends emails. No new scarcity finding is adopted before the complete review. Earlier snapshots below retain their dated history.

Current direction (28 October, after completed scoring): [information-rich reference and graded monitoring scarcity](docs/limburg-data-scarcity-design-2026-10-28.md). The 42-job age/outage component and independent audit/reporting are complete. Brian clarified that scarcity also means fewer observations, intermittent gaps and reduced spatial/context information, not only late/stopped feeds. Those additional comparisons are planned, not run; use the [living one-pager](docs/chapter-one-pager.md) for current scope and findings. Earlier execution snapshots below are historical. No new jobs launched by this design amendment.

Core monitoring-loss analysis (later 28 October): [full eligible-census execution and corrections](docs/limburg-monitoring-first-analysis-2026-10-28.md) is running. It adopts the 481-episode shared NL/DE rainfall calendar, reuses the held encoders, and queues independent auditing, paired storm/year review and actual-analogue plots. Read `results/limburg_monitoring_2026_10_28/execution.json` and `postprocessing.json` for live status. [Provider drafts](docs/limburg-monitoring-provider-request-drafts-2026-10-28.md) are for Brian to send, not automatically dispatched. Soil/snow adds a later control against saved core results, without a full embedding/core rerun.

Code cleanup/restart (28 October): [review and verification](docs/reviews/limburg-code-cleanup-2026-10-28.md). 376 scientific and 2 infrastructure tests pass; saved-result audits pass. `make -j2 check PYTHON=.venv-foundation/bin/python` runs the current local checks.

Current data pulls (28 October): [acquisition record](docs/limburg-monitoring-acquisition-2026-10-28.md). Targeted EO additions are complete; local soil/snow retrieval has resumed with one CDS request at a time. No new embeddings are extracted by this core scoring pass; soil/snow acquisition is independent of it.

Latest completed assessment: [synthesis, archive decomposition and Meuse test](docs/limburg-assessment-synthesis-2026-10-27.md). All three October 27 workstreams are complete; the October 28 monitoring-loss design below is now being executed. The broader conventional archive substantially qualifies the earlier AnySat increment; the declared Meuse test does not establish a primary distributional benefit. Full suite: 359 tests.

# AI-Assisted High-Water Assessment Under Monitoring Loss

Completed findings: [consolidated evidence brief](docs/limburg-findings-consolidated-2026-10-27.md), with shared-population comparisons, broader-census checks, existing sensitivities and actual event cases. The earlier full-information analysis/consolidation is complete.

Current audit and execution: [completed-chapter audit, 27 October](docs/reviews/limburg-completed-chapter-audit-2026-10-27.md). All main and supplemental computational workflows are complete. The [authorized audit follow-up](docs/reviews/limburg-audit-followup-2026-10-27.md) is complete; see the [re-audit](docs/reviews/limburg-second-chapter-audit-2026-10-27.md); dated execution descriptions below retain their historical context.

Meuse inclusion (27 October): Sint Pieter and Venlo now provide mainstem context for the held tributary event census and saved flood-case analogues. See [context, source quality and interpretation](docs/limburg-meuse-context-2026-10-27.md). Existing model scores are preserved.

Current research question (28 October):

> **Can satellite AI help assess developing high water when a gauge's data are
> late or stop arriving?**

The [monitoring-resilience design](docs/limburg-monitoring-resilience-design-2026-10-28.md),
[scenario specification](config/limburg_monitoring_scenarios.json) and
[literature refresh](docs/reviews/limburg-monitoring-literature-2026-10-28.md)
and the [six-step implementation plan](docs/limburg-monitoring-implementation-plan-2026-10-28.md)
now govern the next analysis. They specify repeated rainfall-clock assessments,
fixed observation delays and a stopped station feed, comparing conventional
analogues and ten frozen EO representations with explicit timing, seasonal and
archive controls. **Core implemented and scoring; no adopted scarcity finding yet.** Held inputs
support this test; changed/new contexts receive targeted coverage checks before any additional extraction. Earlier full-information
TTM, AlphaEarth, EO, cross-border and Meuse results remain preserved reference
evidence. This is a retrospective availability study; operator benefit and
as-issued warning skill are not established.

The [22 October restart](docs/reviews/limburg-eo-retirement-and-restart-2026-10-22.md)
extracted eight corrected EO routes and reused verified Prithvi/repaired
OlmoEarth outputs. Earlier scoring was cancelled before completed scientific
results were published; superseded patch caches were retired with compact
provenance and catchment summaries preserved. Its corrected selection was subsequently
aggregated, compared and reviewed; use the completed assessment above for status. The accompanying
[paper/appendix review](docs/reviews/limburg-eo-model-literature-and-runtime-2026-10-22.md)
documents configuration and runtime evidence without changing the running setup.

The latest [storm-response analysis](docs/limburg-storm-response-results-2026-10-15.md)
examines individual-event divergence, conditional information from other gauges
and repeated rainfall/recovery using a rainfall-defined census with nonresponses.
It includes actual event curves, quality checks and a storm-separation sensitivity.

The repository name `chapter1-co2` is historical. CO2, case-crossover,
cross-tributary prediction and pressure diagnostics are preserved under
`archive/retired-directions/2026-retrospective-high-water/`; they are not the
active chapter design.

## Historical EO execution contract — October 22

| Work | Current entry point and contract |
| --- | --- |
| Corrected extraction | `scripts/122_run_coherent_eo_correction.py`: two CPU lanes and one MPS lane; replaces eight routes and reuses Prithvi/repaired OlmoEarth. Live state: `logs/eo-coherent-correction-v1/progress.json`. |
| Date-coherence census | `scripts/116_audit_s2_band_day_census.py`: all 8,538 held S2 tile/window pairs; exact observed catchment areas, no model scoring. |
| Selected handoff | The controller creates `config/limburg_eo_coherent_selected_runs.json` after corrected aggregation, verifies all ten, and merges under `results/eo_catchment_representations/coherent_v1/selected/census`. |
| Versioned writer | `scripts/118_extract_versioned_eo_sequences.py`: same-day S2 bands, corrected publisher transforms/dates, bound population, masks and source hashes. Output: `data/processed/limburg_eo_coherent_census_v1`. |
| Final comparison | The controller runs script 102 against the corrected merge, followed by script 120's actual-analogue review. Outputs are separate from the cancelled held-input comparison. |
| Performance check | `scripts/119_profile_eo_retrieval.py`: full eligible TTM/state cohort, exact cold/cached equivalence; no new scientific score. |

The original `config/limburg_eo_selected_runs.json` is a historical map: eight
referenced runs are explicitly retired. Do not pass it to scientific scoring.
Use the restart controller's corrected map/output paths after completion. The
restart note records the preceding code checks and deliberately preserved history.

Comparison planning now writes under `<out>/planning/`; executed result sets
publish together with `manifest.json` and retain their preceding version. A
zero-score run is explicit and carries no stale score tables. [Second-audit
fixes](docs/reviews/limburg-eo-second-audit-fixes-2026-10-21.md) document portable
input locations, reviewed source compatibility and validation.

## Read first

| document | role |
| --- | --- |
| [Evidence index](docs/limburg-analogue-evidence-index-2026-10-14.md) | main evidence, useful controls and superseded development stages |
| [Active monitoring-resilience design](docs/limburg-monitoring-resilience-design-2026-10-28.md) | current RQs, situations, simulation and evaluation specification; not yet run |
| [Analogue design history](docs/limburg-historical-analogue-active-design-2026-10-13.md) | active pointer followed by dated development sections |
| [Storm-response explanation](docs/limburg-storm-response-results-2026-10-15.md) | three linked event/relationship/escalation analyses, all-case browser, retrospective forcing controls and 12h/24h separation |
| [Expanded event pass](docs/limburg-expanded-event-pass-2026-10-13.md) | main temporal census and short/no-archive coverage |
| [Analogue distributions](docs/limburg-analogue-distribution-results-2026-10-15.md) | 24h distribution accuracy and uncertainty coverage; fixed five/ten donors, conventional and AlphaEarth controls |
| [Event-definition robustness](docs/limburg-event-definition-results-2026-10-14.md) | p95 selection and five-day local linkage, one factor at a time; fixed p99 response scale |
| [Warning-threshold progression](docs/limburg-warning-threshold-results-2026-10-14.md) | full native-record census and H1-started escalation evidence; current thresholds applied retrospectively |
| [Cross-border completion](docs/limburg-cross-border-completion-2026-10-14.md) | country/archive effects, German rainfall benchmark and pooled geographic context |
| [Information review](docs/limburg-analogue-information-review-2026-10-14.md) | generic-archive references and event interpretation |
| [AlphaEarth review](docs/limburg-alphaearth-detailed-review-2026-10-14.md) | main matched spatial-context evidence |
| [Literature bridge](docs/limburg-analogue-literature-bridge-2026-10-13.md) | event-similarity and cross-border foundation |
| [October literature update](docs/limburg-weekly-literature-2026-10-16.md) | global event-to-event response variability as interpretation context; German pooling correction |
| [EO literature/runtime review](docs/reviews/limburg-eo-model-literature-and-runtime-2026-10-22.md) | ten exact checkpoint routes, primary papers/appendices, compute evidence and optional adaptations |
| [EO error/correction ledger](docs/reviews/limburg-eo-error-and-correction-ledger-2026-10-22.md) | defects, fixes, validation evidence, retired runs and remaining execution |
| [Inventory](docs/analysis-inventory.md) | code, dependencies and supporting work |
| [Handoff](docs/HANDOFF.md) | current state followed by historical execution ledger |
| [Current ideas](docs/limburg-ideas-2026-10-15.md) | saved Idea 1: past-only event-divergence prediction; not implemented |
| `docs/data-requests.md`, `docs/decisions.md` | provider status and append-only design history |

Earlier execution notes and controls are indexed separately rather than
presented as equally current main findings. Numerical outputs remain local;
no raw provider data is published.

## Reproduction chain

The commands below preserve the upstream dependency chain. They are not a
list of separate active experiments. For analysis and interpretation, use the
evidence index to start with scripts 81–84 and 90–91 and their existing held inputs;
rerun upstream stages only when rebuilding or checking provenance.

```bash
conda env create -f environment.yml
conda activate chapter1-co2

python scripts/39_delineate_catchments.py
python scripts/46_review_events.py
python scripts/64_build_basin_ai_event_library.py
python scripts/65_hydrological_analogue_baseline.py
python scripts/66_download_limburg_foundation_assets.py
python scripts/68_import_alphaearth_embeddings.py
python scripts/69_raw_hydrograph_analogue_baseline.py
```

With the pinned foundation environment/source installed as described in the
Steps 3–5 execution note:

```bash
python scripts/70_ttm_analogue_comparison.py
python scripts/71_alphaearth_analogue_increment.py
python scripts/72_german_wurm_analogue_extension.py
python scripts/73_analogue_uncertainty_review.py
python scripts/74_review_analogue_census.py
python scripts/75_strengthen_foundation_representations.py
python scripts/77_plot_representation_checks.py
python scripts/78_cross_river_analogue_checks.py
python scripts/79_audit_analogue_consistency.py
python scripts/80_prepare_event_interpretation.py
python scripts/81_run_expanded_event_analogues.py
python scripts/82_review_analogue_information.py
python scripts/83_review_alphaearth_event_information.py
python scripts/84_complete_cross_border_analogues.py
python scripts/85_audit_cross_border_results.py
python scripts/86_analyse_warning_threshold_progression.py
python scripts/87_audit_warning_threshold_results.py
python scripts/88_event_definition_sensitivity.py
python scripts/89_audit_event_definition_sensitivity.py
python scripts/90_evaluate_analogue_distributions.py
python scripts/91_audit_analogue_distributions.py
python scripts/92_build_storm_response_catalogue.py
python scripts/93_analyse_storm_responses.py
python scripts/94_audit_storm_response_analysis.py
```

The event-library default is the fixed 512-hour assessment history required by
TTM-R2, followed by 72 withheld hours. AlphaEarth export is an authenticated
Earth Engine step documented in the download-readiness note.
The separate metric-grid QA table is retrieved with
`python scripts/76_check_alphaearth_metric_grid.py --download`; the original
export remains preserved. The latest checks note documents the tested
representation variations and keeps them separate from the original run.
The cross-river checks use other physical rivers as donors, compare fixed
3/5/10-storm neighborhoods, and test matched conventional/raw and
conventional/TTM fusion. See
`docs/limburg-cross-river-checks-2026-10-13.md` for interpretation boundaries.
The pre-interpretation audit is in
`docs/limburg-consistency-audit-2026-10-13.md`; it independently checks event
windows, representations, identities, candidate pools and response metrics.
`docs/limburg-event-interpretation-readiness-2026-10-13.md` documents the
broader Q-only inputs, explicit reference measures and blank event-review
packet. Script 81 runs the expanded Q-only census and writes a local event
browser, phase evidence, paired intervals and explicit unavailable-archive rows.
See `docs/limburg-expanded-event-pass-2026-10-13.md` for the resulting evidence.

The information and policy interpretation is in
`docs/limburg-analogue-information-review-2026-10-14.md`: generic-archive
reference checks, actual benefit/failure cases and separately attributed AI
notes. Independent human review fields remain untouched.

AlphaEarth’s detailed matched review is in
`docs/limburg-alphaearth-detailed-review-2026-10-14.md`: donor replacements,
area/identity/static controls and geographic context alongside strengthened TTM.

## Verify

```bash
python -m pytest -q
ruff check .
ruff format --check .
```

Historical code is retained for reproducibility but excluded from live lint
and tests.
