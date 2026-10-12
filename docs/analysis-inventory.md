# Limburg analysis inventory

Status: 2026-10-12. The basin-aware AI design is the only active chapter
direction. Earlier empirical branches remain reproducible in the archive.

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

## Live basin-aware AI experiment

| code or contract | purpose | state |
| --- | --- | --- |
| `docs/ai-eval/source-inventory.json` | source and provenance inventory | pilot-ready |
| `docs/ai-eval/basin-graph.json` | verified basin and agency relations | pilot-ready |
| `docs/ai-eval/benchmark-draft.json` | answerable and unanswerable cases | human gold review pending |
| `docs/ai-eval/system-arms.json` | evidence-access ablation A0–A3 | fixed |
| `docs/ai-eval/representation-arms.json` | representation comparison R0–R4 | R4 conditional |
| `scripts/63_build_basin_ai_pilot.py` | validates evidence and builds prompt packets | complete |
| `scripts/64_build_basin_ai_event_library.py` | 512-hour histories and 72 withheld hours | complete |
| `scripts/65_hydrological_analogue_baseline.py` | conventional prior-event retrieval | complete |
| `scripts/66_download_limburg_foundation_assets.py` | pinned asset acquisition and receipts | complete |
| `scripts/67_export_alphaearth_embeddings.py` | Earth Engine catchment-year export | delivered |

The A and R labels describe different experiments. A0–A3 isolate access to
documents, checked tools and basin structure. R0–R3 compare historical-event
representations after basin/provenance grounding is fixed. R4 runs only if the
conventional and pretrained representations are individually useful and
complementary.

## Archived directions

The case-crossover fit, observed-rainfall follow-up, cross-tributary footprint,
retrospective prediction, atmospheric increment, Wurm CO2/pressure diagnostic,
Maas increment and early AI brainstorming are under
`archive/retired-directions/2026-retrospective-high-water/`.
