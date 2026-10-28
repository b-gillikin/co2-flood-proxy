# Scarcity design: implemented audit corrections

28 October 2026. Research-aid/code update authorized by Brian. The [audit](limburg-scarcity-research-design-audit-2026-10-28.md) remains the dated assessment before correction. This record describes implementation, not new empirical findings or dissertation prose.

| Audit issue | Implementation |
| --- | --- |
| One-axis loss misses simultaneous scarcity | Two combined profiles: all 70 four-gauge networks × six UTC reporting phases; and 100 joint four-gauge/clustered-gap realizations. Both remove current Maas context. Shared views across target sites; no event sample. |
| Rain episodes versus high water | Full opportunity ledger, existing p99 evaluation labels, undefined labels, net rising/falling response strata and overlap with the reviewed flood register. Labels do not enter matching. |
| EO coverage and restricted donors | Whole-census fallback effects, EO-used and common-weekly-support strata, matched representation and archive-restriction decomposition; site diagnostics retain coverage and donor counts. |
| Meaning of scarcity | Protocol and interpretation guide explicitly retain finalized local archives, nominal release assumptions and the reference rain clock. No ungauged-basin, as-issued or government-FEWS equivalence claim. |
| Filled donor histories | Selected-donor measured/held/mean-filled and clean fractions; repeat rich/local-absence/both combined profiles with a shared 80%-measured-support donor sensitivity. Report restriction/fallback rather than impose a chapter gate. |
| Changed reference algorithm | A paired case-level bridge to the prior full-information local method. Preserve original results and separate versioned artifacts. |
| Ambiguous inference | Equal target-site mass at each separately reported issue; valid paired case-mask observations equal within site. Resample complete years and R coherent random-mask IDs, then average. Exact phases/networks are averaged without resampling. Direct scarcity interactions; undefined bootstrap draws disclosed. Measured-support conditions use their own measured-support rich reference. |
| Many comparisons | Recent/K5/CRPS primary; intervals for declared principal contrasts/populations are exploratory pointwise intervals. Monthly/K10/archive/country/secondary endpoints are diagnostic. No favorable-cell or family-controlled winner claim. |
| Age and placement | Equal-age diagnostics, target-retained/removed strata, channel names in opportunity traces, network-placement inventory with NL/DE/Wurm counts and Maas retention. |
| Physical/operational interpretation | Antecedent EO context, donor-date/season traces, actual-member diagnostics and an interpretation guide; no instantaneous flood imagery, warning skill or physical-mechanism claim inferred solely from predictive improvement. |

## Execution and provenance

- Configuration: `config/limburg_scarcity_v1.json` (legacy filename, **schema 2**).
- Protocol: `docs/limburg-scarcity-executable-protocol-2026-10-28.md`.
- Corrected output: `results/limburg_scarcity_v2_2026_10_28/`.
- **45 groups × four issue offsets = 180 jobs**, using all 481 declared storms and eight target gauges wherever verification is held. Repeated masks/placements are not new independent storms.
- Entry point: `scripts/163_finish_scarcity.py`; two CPU scoring workers, then complete output audit and evidence review. No download or embedding extraction is required by this correction.
- Live state: `pipeline.json`, `execution.json`, and per-job `progress/*.json` within that output. Log: `logs/scarcity-v2-2026-10-28.log`.
- Earlier v1 preparation/benchmark remain untouched, with the original config/protocol/code/tests in `results/limburg_scarcity_v1_2026_10_28/source_snapshot/` and SHA256 receipt. An initial v2 benchmark is retained under `development-benchmarks/initial-quality-diagnostics/`, with its runner source; the corrected queue reruns that job. This corrected only the interpretation of clean donor inputs when there are no active Q channels, not the benchmark's predicted distributions.

## Verification

Nineteen scarcity tests pass, including hidden-value poisoning, coherent combined masks, donor support, scalar CRPS replay, explicit joint-bootstrap examples, exact-design replication invariance, undefined draws, and a full synthetic scoring-to-review/coverage/bridge publication fixture. The real-data preparation and first reference benchmark also passed independent source/chronology/scalar-score audits, and the reporting smoke run completed. Final audit/reporting repeats against the completed corrected matrix.

The broader suite covered 411 tests: 402 passed on the initial invocation; nine geospatial tests failed because that invocation omitted the environment's PROJ data path. All nine passed when rerun with `PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj`. No production geospatial code was changed. Scoped scarcity tests were rerun after the final reporting corrections. Repository lint and formatting checks pass.

At this update, the full corrected queue is running. Numerical conclusions await its review; the previous completed age/outage findings remain evidence. All changes are confined to Chapter 1 code and research aids. No other chapter data was touched, no raw provider records are committed, and no email was sent. Brian retains all dissertation writing and email dispatch.
