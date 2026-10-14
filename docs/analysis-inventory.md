# Limburg analysis inventory

**Evidence status updated 2026-10-14:** scripts 81–84 are the main current
readout; 75–78 retain specified supporting controls/sensitivities; 70–74 are
development/reproduction stages and 80 is preparation. Detailed roles and
interpretation limits are in the
[evidence index](limburg-analogue-evidence-index-2026-10-14.md). All dependency
code remains in place and tested. The inventory below includes historical
execution counts, not a list of equally current chapter findings.

Status: 2026-10-13. The historical-analogue representation comparison is the
active chapter direction. Earlier empirical branches remain reproducible in
the archive.

## Live evidence preparation

| code | output or role |
| --- | --- |
| `scripts/25_ingest_lanuk_nrw.py` | held German station-package ingest support |
| `scripts/31_event_study_gates.py` | historical input-contract audit; supporting QA only |
| `scripts/32_lanuk_feasibility.py` | German source semantics and coverage audit |
| `scripts/34_fetch_era5_land.py` | fallback acquisition for the completed weather archive |
| `scripts/35_audit_waterschap_delivery.py` | Dutch provider-delivery audit |
| `scripts/37_fetch_radar.py` | RADOLAN/RADKLIM acquisition and crop |
| `scripts/39_delineate_catchments.py` | Dutch and German catchment geometry |
| `scripts/40_build_event_study_weather.py` | hourly catchment weather |
| `scripts/41_radar_catchment_rainfall.py` | hourly catchment rainfall |
| `scripts/42_check_rating_transcription.py` | rating-document transcription QA |
| `scripts/43_build_rating_eras.py` | dated rating domains |
| `scripts/44_build_event_study_gauges.py` | gauge identity and provider metadata |
| `scripts/45_build_event_study_discharge.py` | verified hourly Dutch discharge |
| `scripts/46_review_events.py` | checked Dutch high-water onsets and concerns |
| `src/event_study.py` | shared event, rating-era and continuity functions |

Historical `event_study_*` names remain in derived files to preserve
provenance. They do not make the archived case-crossover model active.

## Live historical-analogue experiment

| code or contract | purpose | state |
| --- | --- | --- |
| `docs/ai-eval/representation-arms.json` | representation comparison R0–R4 | bounded exploratory R4 and matched raw fusion executed |
| `scripts/64_build_basin_ai_event_library.py` | 512-hour histories and 72 withheld hours | complete |
| `scripts/65_hydrological_analogue_baseline.py` | conventional prior-event retrieval; one selected event per prior storm | complete; tied historical median |
| `scripts/66_download_limburg_foundation_assets.py` | pinned asset acquisition and receipts | complete |
| `scripts/67_export_alphaearth_embeddings.py` | Earth Engine catchment-year export | delivered |
| `scripts/68_import_alphaearth_embeddings.py` | validated prior-year event join; fixed geometry receipt | complete; 304 input and 296 outcome events |
| `scripts/69_raw_hydrograph_analogue_baseline.py` | R1 raw 512-hour control on the same R0 query/donor pools | executed; 534 paired queries |
| `scripts/70_ttm_analogue_comparison.py` | pinned frozen backbone representation on identical histories | executed; 534 paired queries |
| `scripts/71_alphaearth_analogue_increment.py` | fixed TTM + prior-year context, with area control | executed; 276 common-subset queries |
| `scripts/72_german_wurm_analogue_extension.py` | delivered Wurm stage/Q conversion and pooled Q-only R1/R2 | executed; 338 German episodes, 774 pooled queries |
| `scripts/73_analogue_uncertainty_review.py` | paired sampling intervals, river-removal refits, provenance and visual review packet | executed; 14 AI-inspected illustrations; human verdicts pending |
| `scripts/74_review_analogue_census.py` | every selected pair/set, whole response and complete prior-pool reference; chronological atlas | executed; 38,540 selected slots, 774 distinct queries; explicitly exploratory |
| `scripts/75_strengthen_foundation_representations.py` | ordered patch/state comparisons, common-frame rainfall control, identity/static/metric-grid context controls | executed; 102,645 selected slots / 20,529 sets; original controls replayed |
| `scripts/76_check_alphaearth_metric_grid.py` | separate 10-m EPSG:3035 catchment aggregation and projection QA | complete; 72-row table; no donor set changes |
| `scripts/77_plot_representation_checks.py` | main and quality comparison figures from tidy summaries | complete |
| `scripts/78_cross_river_analogue_checks.py` | cross-physical-river donors, fixed 3/5/10 neighborhoods, disagreement census, donor-spread checks and matched conventional/TTM fusion | user-authorized exploratory extension; separate outputs |
| `scripts/79_audit_analogue_consistency.py` | independent input/window, representation, identity, candidate-pool and metric audit | consistency checks pass; no new empirical model |
| `scripts/80_prepare_event_interpretation.py` | full Q-only inventory/vectors, persistence and group-balanced references, archive availability and editable review fields | prepared; 964 inputs / 851 scorable responses; expanded execution follows in script 81 |
| `scripts/81_run_expanded_event_analogues.py` | expanded Q-only retrieval, available short archives, phase evidence and own-history references | executed; see `limburg-expanded-event-pass-2026-10-13.md`; existing rain/Q and AlphaEarth comparisons preserved |
| `scripts/82_review_analogue_information.py` | specificity versus the group-balanced eligible archive, outcome-independent case selection and separately attributed AI interpretation | executed; 19,764 pooled score sets; 24 sentinels; see `limburg-analogue-information-review-2026-10-14.md` |
| `scripts/83_review_alphaearth_event_information.py` | matched geographic donor changes, original/strengthened temporal families, area/identity/static/annual controls and case review | executed; 296 context responses / 290 main queries; no training or new download |
| `scripts/84_complete_cross_border_analogues.py` | pooled/domestic/foreign archive effects, German geographic context and held-radar rain/Q benchmark | country-specific main/quality results and explicit unavailable archives; see cross-border completion note |
| `scripts/85_audit_cross_border_results.py` | independent pair-metric and country-summary reconstruction with input/output/source fingerprints | 780,312 pair slots and 528 summary rows verified |
| `scripts/86_analyse_warning_threshold_progression.py` | all native threshold episodes, H1-started frozen analogue analysis and p99 bridge; quality/history/follow-up sensitivities | full run; see warning-threshold results note |
| `scripts/87_audit_warning_threshold_results.py` | independent native labels, donor-share and summary reconstruction, input/output hashes and whole-record low-flow masking check | separate audit receipt |
| `config/lanuk_rating_periods.csv` | hashed provider curve-validity transcription | complete; literal boundaries and provisional regime explicit |

Execution choices, results and reproduction commands are in
`limburg-analogue-steps-3-5-2026-10-13.md` and
`limburg-analogue-step6-2026-10-13.md`. The original computational uncertainty
checks and AI-assisted illustration review are complete; event-level added
understanding remains to be evaluated. Independent human verdicts remain
unfilled. In that original mean-readout/five-donor run, no learned arm has a
lower point MAE than its historical-median benchmark; later donor-count
results are reported separately in the cross-river checks note.
Brian then authorized the richer full-response census in
`limburg-analogue-census-2026-10-13.md`. Shape matching improves modestly with
TTM versus raw and with AlphaEarth versus TTM/area, despite peak and timing
limitations; conventional rain/Q remains stronger in the Dutch comparison.
The census adds no model arm or data requirement.
The subsequent user-authorized checks are in
`limburg-representation-strengthening-2026-10-13.md`: better-supported TTM
readout/state usage, and a more limited AlphaEarth increment beyond locality.
These are variations/controls of the same two foundation models, not a model
leaderboard. No hyperparameter winner or training regimen was selected.
`limburg-consistency-audit-2026-10-13.md` records the independent numerical
checks, stronger replay provenance, metric definitions and remaining
event-interpretation questions. Script 80 now embeds the 58 additional Q
histories and prepares the 56 additional complete responses, explicit
references and all-event availability. Their expanded analogue retrieval
and event-level interpretation remain pending.

R0 is the practical conventional signature baseline; R1 versus R2 compares
raw-hydrograph similarity with frozen TTM on identical discharge inputs; R3
adds prior-year AlphaEarth context only on the common 2018+ subset. Brian
authorized a bounded exploratory R4 check in script 78: equal conventional
and temporal blocks, with matched raw-history fusion. It is not a dissertation
requirement or a new trained model.

## Retained evidence QA, outside the core experiment

`docs/ai-eval/source-inventory.json`, `basin-graph.json`,
`benchmark-draft.json`, `system-arms.json` and
`scripts/63_build_basin_ai_pilot.py` preserve the earlier four-arm feasibility
pilot. They may support factual and source-link checks. Running or scoring the
RAG arms, selecting a generator, and human-reviewing all 30 cases are not
chapter requirements.

## Archived directions

The case-crossover fit, observed-rainfall follow-up, cross-tributary footprint,
retrospective prediction, atmospheric increment, Wurm CO2/pressure diagnostic,
Maas increment and early AI brainstorming are under
`archive/retired-directions/2026-retrospective-high-water/`.
