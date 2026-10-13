# Limburg analysis inventory

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
| `docs/ai-eval/representation-arms.json` | representation comparison R0–R4 | R4 conditional |
| `scripts/64_build_basin_ai_event_library.py` | 512-hour histories and 72 withheld hours | complete |
| `scripts/65_hydrological_analogue_baseline.py` | conventional prior-event retrieval; one selected event per prior storm | complete; tied historical median |
| `scripts/66_download_limburg_foundation_assets.py` | pinned asset acquisition and receipts | complete |
| `scripts/67_export_alphaearth_embeddings.py` | Earth Engine catchment-year export | delivered |

R0 is the practical conventional signature baseline; R1 versus R2 compares
raw-hydrograph similarity with frozen TTM on identical discharge inputs; R3
adds prior-year AlphaEarth context only on the common 2018+ subset. R4 is
optional if conventional and pretrained representations are individually
useful and complementary.

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
