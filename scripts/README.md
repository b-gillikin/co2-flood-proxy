# Scripts

The live scripts are data acquisition, input QA or small transparent analyses.
New chapter code should read as:

`load -> check -> define events/controls -> estimate -> tidy tables -> figures`

There is no analysis framework or model registry.

| script/module | purpose | state |
| --- | --- | --- |
| `25_ingest_lanuk_nrw.py` | acquire the held German discharge source used by the feasibility audit | implemented; source does not pass |
| `31_event_study_gates.py` | audit the five binding primary input files and report S2 weather plus information benchmarks separately | implemented; 19/19 binding input contracts pass on 2026-09-29 |
| `32_lanuk_feasibility.py` | audit German metadata, gaps, density and episode counts without signal outcomes | implemented; relevant only to the conditional distance module |
| `34_fetch_era5_land.py` | local fallback for the fixed 2001–2025 weather grid | implemented; archive complete, fallback only |
| `35_audit_waterschap_delivery.py` | outcome-blind raw coverage audit plus provider-sourced station QA for the delivered 2010–2025 table | implemented; timezone and zero semantics confirmed by provider |
| `37_fetch_radar.py` | download DWD RADOLAN RW or RADKLIM-RW, crop to South Limburg, checksum | implemented; decoding matches DWD ASCII exactly |
| `38_validate_estimator.py` | synthetic validation: agreement with R, recovery, bootstrap coverage | implemented and run; see `results/estimator_validation/` |
| `39_delineate_catchments.py` | cross-border catchments from Copernicus GLO-30, checked against EStreams areas | implemented; provisional pour points |
| `40_build_event_study_weather.py` | ERA5-Land relative humidity, surface pressure and six-hour change per catchment | implemented and run |
| `41_radar_catchment_rainfall.py` | area-weighted hourly catchment rainfall and exposure-only QA | implemented and run (RADOLAN and RADKLIM) |
| `42_check_rating_transcription.py` | check the hand transcription of the 14 rating-curve PDFs (`config/rating_curves/`) against the PDF text and its own arithmetic | implemented and run |
| `43_build_rating_eras.py` | rating-era table under decision D8 (`config/rating_curves/event_study_eras.csv`), with domains and the level where merged versions agree; also the literal-era sensitivity table | implemented and run |
| `44_build_event_study_gauges.py` | core gauge-metadata table: D3 cohort, provisional D5 coordinates, source QA and July 2021 status, coordinate cross-check | implemented and run |
| `45_build_event_study_discharge.py` | hourly discharge outcome series: four trailing quarters per hour, verified timezone/zero choices, failure masking | core file built on 2026-09-29; rejects unverified choice combinations |
| `R/case_crossover_reference.R` | R reference fit (`dlnm` plus fixed-effects GLM), called by script 38 | implemented |
| `src/event_study.py` | rating-era thresholds, crossings, censoring, episodes, storms, at-risk hours, strata | implemented and unit-tested |
| `src/case_crossover.py` | lag basis, cross-basis, conditional Poisson fit, block bootstrap, primary summaries | implemented, unit-tested and validated against R |
| `46_review_events.py` | outcome-only review of every candidate onset, source concerns and discharge contact sheets | run; 724 exact onsets reviewed |
| `47_run_real_event_study.py` | primary, S1–S4, specified sensitivities, 999-draw joint-month bootstrap and tidy outputs | first real-data fit run 2026-09-29 |
| `48_render_real_event_study.py` | five protocol figures from fitted outputs and the fixed catchment GeoPackage | run |
| `49_diagnose_real_event_study.py` | fitted-onset diagnostics, July 2021 point-estimate influence and rainfall-contrast support | run; diagnostic only |

Safe input-only commands:

```bash
python scripts/31_event_study_gates.py --report-only
python scripts/32_lanuk_feasibility.py
python scripts/35_audit_waterschap_delivery.py
python scripts/37_fetch_radar.py --product radolan
python scripts/38_validate_estimator.py   # synthetic data only; needs R with dlnm
python scripts/39_delineate_catchments.py
python scripts/40_build_event_study_weather.py
python scripts/41_radar_catchment_rainfall.py
python scripts/42_check_rating_transcription.py
python scripts/43_build_rating_eras.py
python scripts/44_build_event_study_gauges.py
python scripts/45_build_event_study_discharge.py --timezone fixed_utc_plus_1 --zero true_zero --commit
```

First-fit workflow (project environment):

```bash
python scripts/46_review_events.py
python scripts/47_run_real_event_study.py --replicates 999
python scripts/48_render_real_event_study.py
python scripts/49_diagnose_real_event_study.py
```

The review is completed before the fit. `results/event_study/real_data_v1/`
holds ignored local analytical artifacts; `docs/limburg-first-fit-results-guide.md`
records the interpretation and the cumulative-contrast limitation.

The last command writes a labelled candidate under
`results/discharge_ingest_candidates/` and the core gate file. The core write
is limited to the provider-verified fixed-offset and true-zero choices and
requires matching verified flags in `event_study_gauges.csv`.

The ERA5-Land Azure backfill completed and its Function App is stopped. Do not
start `34_fetch_era5_land.py` without first confirming that no cloud request is
active; both paths use the same CDS account and fixed monthly request sequence.

The eventual outcome script should be one direct pandas/statsmodels-style
analysis, split only if the figures make it unreadable. Add helpers only for a
scientific definition reused in more than one place or requiring an isolated
check. Comment choices such as censoring and window completeness, not obvious
syntax.

## Retired from the live tree

The later-era Eryilmaz re-fit, Visual Crossing join, rolling two-year Dutch
gauge pull, Maas main-stem validation and DWD point-rain sensitivity were
removed. The Eryilmaz paper remains predecessor evidence; those extra pipelines
did not answer the prospective chapter question. Older prediction matrices,
classifiers, filters, anomaly detectors and generic substitution machinery were
already retired. `01_ingest_iot.py` and `33_ingest_viefhues_iot.py` moved to
`archive/` on 2026-09-18: draft 0.9 removed the conditional Kerkrade CO2 case
they served, and the chapter analyses no CO2. `src/io_iot.py` stays in `src/`,
still exercised by `infrastructure_tests/test_io_data.py` to protect the
deployed daily-summary Azure function. This does not touch the Azure
collection infrastructure in `kerkrade_data/`, which those scripts consumed
but did not operate. Git history and `docs/decisions.md` preserve the audit
trail.

## Verification boundary

`pytest -q` covers scientific definitions and input semantics. The older IoT
collection checks live in `infrastructure_tests/` and run only when that
collection machinery changes. New parsers should first be checked against the
delivered file and a tidy QC artifact; do not add fixture tests by default.
