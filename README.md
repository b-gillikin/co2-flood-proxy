# Basin-Aware AI for Historical High-Water Analogues

Research question:

> **Can basin-aware AI find useful past high-water events across Limburg's
> Dutch and German tributaries, and identify when the evidence is too
> uncertain to use?**

The chapter compares conventional hydrological summaries, raw hydrograph
similarity, a frozen time-series foundation-model representation and bounded
AlphaEarth catchment context, extended by ten frozen EO encoders with explicit
coverage and matched-population controls. It reviews whether river identity and measurement
provenance make retrieved analogues usable. It is a retrospective archive
study, not an automatic warning system or operational forecast evaluation.

The [22 October execution](docs/reviews/limburg-eo-current-archive-execution-2026-10-22.md)
has verified and merged all ten EO outputs and launched the full current-archive
comparison, followed automatically by an actual-analogue review. The machine
status file named in that record distinguishes running work from completed
results. Coverage differences and held-input limitations remain explicit.

The latest [storm-response analysis](docs/limburg-storm-response-results-2026-10-15.md)
examines individual-event divergence, conditional information from other gauges
and repeated rainfall/recovery using a rainfall-defined census with nonresponses.
It includes actual event curves, quality checks and a storm-separation sensitivity.

The repository name `chapter1-co2` is historical. CO2, case-crossover,
cross-tributary prediction and pressure diagnostics are preserved under
`archive/retired-directions/2026-retrospective-high-water/`; they are not the
active chapter design.

## Current EO execution — October 21

| Work | Current entry point and contract |
| --- | --- |
| Held extraction runs | Original jobs continue unchanged. Their immutable IDs and aggregate paths are selected in `config/limburg_eo_selected_runs.json`, including repaired OlmoEarth/Galileo and the separate Presto runtime. |
| Date-coherence census | `scripts/116_audit_s2_band_day_census.py`: all 8,538 held S2 tile/window pairs; exact observed catchment areas, no model scoring. |
| Selected handoff | `scripts/117_finalize_selected_eo_runs.py` checks readiness; `--merge` publishes a validated ten-model merge under `results/eo_catchment_representations/selected/census`. It never substitutes the old recovery paths. |
| Future corrected extraction | `scripts/118_extract_versioned_eo_sequences.py`: separate output root, same-UTC-day S2 masks, bound job/context population and native token masks. Previous embeddings are not silently relabelled corrected. |
| Final comparison | `scripts/102_connect_limburg_eo_experiments.py --run`: consumes the selected merge, verifies selection/provenance and caches identical retrievals. Planning without `--run` remains available. |
| Performance check | `scripts/119_profile_eo_retrieval.py`: full eligible TTM/state cohort, exact cold/cached equivalence; no new scientific score. |

[Correction record and commands](docs/reviews/limburg-eo-audit-fixes-2026-10-21.md)
distinguishes completed code changes from the running date census and any later
corrected embeddings. The default selection currently names the held runs, not
same-day reruns. The old script-105 controller already in memory may still write
its legacy `census` folder; final scoring no longer consumes that folder by default.

Comparison planning now writes under `<out>/planning/`; executed result sets
publish together with `manifest.json` and retain their preceding version. A
zero-score run is explicit and carries no stale score tables. [Second-audit
fixes](docs/reviews/limburg-eo-second-audit-fixes-2026-10-21.md) document portable
input locations, reviewed source compatibility and validation.

## Read first

| document | role |
| --- | --- |
| [Evidence index](docs/limburg-analogue-evidence-index-2026-10-14.md) | main evidence, useful controls and superseded development stages |
| [Active design](docs/limburg-historical-analogue-active-design-2026-10-13.md) | question, comparison and scope; dated development sections preserved |
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
