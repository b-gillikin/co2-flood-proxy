# EO audit corrections — 2026-10-21

Implementation of the [chapter/code audit](limburg-chapter-code-audit-2026-10-21.md).
This changes engineering validity and reproducibility, not the research question,
event census, model list, comparisons or dissertation text.

## Changes and remaining execution

| Audit finding | Implemented correction | What execution remains |
| --- | --- | --- |
| F1: repaired outputs omitted | Authoritative `config/limburg_eo_selected_runs.json`; script 117 explicitly checks each selected run and merges the ten selected aggregates. Script 102 defaults to that selected merge. | Finish existing Galileo aggregation and Presto work, then run script 117 `--merge`. An in-memory old controller can still write its old merge; that folder is not the new comparison default. |
| F2: stale/incomplete output accepted | Script 101 preflights extraction status, rejects ambiguous runs, checks context identities/windows and publishes from a fresh staging directory. Previous destinations are preserved on replacement. Empty/error-bearing input cannot produce a complete result. `--allow-partial` explicitly labels useful partial research; complete-result validation excludes it. Final merge checks source selection, model/run rows, masks, geometry and output hashes; comparison checks the current selection and its source receipts. | The currently running Galileo aggregator loaded its original code before this change. It remains untouched; its completed output must pass the new independent finalizer. Future aggregators load the corrected implementation. |
| F3: mixed-date S2 bands | `src/eo_coherent_inputs.py` implements same-UTC-day joining as an explicit mask, preserving source arrays. Script 116 measures every held S2 tile/window pair with exact catchment and union areas. | The full 8,538-pair census completed with zero errors. Its coverage loss does not establish a change in model scores. Corrected embeddings require separate versioned extraction after the census; none were silently recomputed or relabelled. |
| F4: scope missing from run identity | Script 118 binds job/context file hashes and paths, expected IDs, full-versus-single-context selection, input policy, source, runtime/device and token-mask policy. New output root prevents reuse of old IDs. | Existing run IDs remain immutable and are identified as legacy scope records. Their status count and actual aggregate contexts are checked, without inventing prospective input hashes. Use script 118 for future extraction. |
| F5: repeated computation | A content-addressed retrieval cache binds sample rows/order, every representation block, policy/options and retrieval code; cached files have integrity receipts. Script 102 uses it without changing retrieval or scoring. | Profile completed on the full eligible TTM/state cohort; no total-ten-model runtime estimate is inferred. Final scoring remains pending selected inputs. |
| F6: documentation/formatting | README, active design, representation-arm registry and handoff now point to the current chain. Dated historical sections remain. Formatted the one previously flagged recovery utility. | Keep status updates in the current handoff/selection rather than treating old dated sections as current commands. |

A completed-model subset can proceed concurrently: script 117 `--merge
--available-only` writes a separate `available/census` directory. Script 102
`--run --allow-partial` can score that explicitly labelled subset and keeps
missing models visible; its all-ten intersection remains empty. It does not
silently relax the all-ten comparison or overwrite complete-result outputs.
Incomplete model extraction is distinct from a completed-model subset.

## Scientific handling of the S2 correction

Same-day masking excludes a pixel if its fine/coarse spectral bands represent
different UTC days. Held acquisition dates are day-quantized: this does not prove
exact scene identity. There is no reflectance interpolation, invented spectrum,
backfilled observation or arbitrary minimum-area cutoff. Native token masks are
applied before patch metadata is calculated, keeping valid counts, coordinates,
representative dates and encoder input support consistent.

The census has one record per tile/window/catchment plus a catchment-union record.
It measures lost observed area and reports the maximum day gap within the actual
catchment. Overlapping months/weeks and nested catchments are not independent
replicates. A same-day mask can reduce representation availability; retain that
coverage change as a result, rather than treating it as a silent cohort change.

This is the smallest held-data correction; source-consistent recompositing could
recover some lost support later, but is not required to implement or measure this
fix. Do not initiate seven expensive complete reruns until the affected coverage
is known. Future corrected outputs have distinct identities and must be selected
explicitly in a new selection-map version. The held map continues to describe
actual completed/running inputs, including their original multi-day S2 policy.

## Completed date-agreement census

All **8,538 held S2 tile/window pairs** were checked, with zero failures.
Using exact catchment-union area, after avoiding double-counting nested
catchments:

| Held window type | Windows with observed area | Windows with some mixed-day area | Area-window-weighted loss under same-day masking | Largest whole-union window loss |
| --- | --- | --- | --- | --- |
| Monthly | 121 | 107 | 1.169% | 4.177% |
| Weekly (`recent`) | 422 | 306 | 0.378% | 2.308% |

Four further weekly windows had no valid observed area; their mixed-day fraction
is undefined, not zero. These are full held-window counts, not sampled events.
The weighted ratio is total mixed-day area divided by total observed union area
across the held windows. Windows overlap in time; this is an exposure summary,
not independent replication, a significance test or a population probability.

Monthly median loss was 0.861% (95th percentile 3.158%); weekly median was
0.055% (95th percentile 1.312%). These quantify observed-area masking, not
encoder token support, catchment representation availability or score changes.
The same pixel change can affect a contextual patch beyond its exact catchment
intersection. Assess the corrected representation version separately rather
than inferring prediction/retrieval changes from these percentages.

Local artifacts: `results/eo_band_day_census/{manifest.json,
tile_catchment_areas.parquet,catchment_window_coverage.csv,summary.json}`.
The compact check receipt embeds the census summary and output hashes.

## Current commands

Run from the repository root, using the model-specific runtimes. The full date
census is complete; its output lock rejects duplicate concurrent workers.

```bash
# Full held-date census; no encoder or model score.
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venvs-eo/terramind/bin/python scripts/116_audit_s2_band_day_census.py

# Inspect exact selected-run readiness; then merge when all ten are ready.
.venvs-eo/terramind/bin/python scripts/117_finalize_selected_eo_runs.py
.venvs-eo/terramind/bin/python scripts/117_finalize_selected_eo_runs.py --merge

# Comparison planning, then scoring of the validated selected version.
.venv-foundation/bin/python scripts/102_connect_limburg_eo_experiments.py
.venv-foundation/bin/python scripts/102_connect_limburg_eo_experiments.py --run
```

Script 118 defaults to inventory. Examples of corrected extraction commands,
to be run after assessing the census (not launched by this implementation):

```bash
PYTORCH_ENABLE_MPS_FALLBACK=0 .venvs-eo/galileo/bin/python \
  scripts/118_extract_versioned_eo_sequences.py --model galileo --device mps --run

.venvs-eo/presto-torch291/bin/python \
  scripts/118_extract_versioned_eo_sequences.py --model presto \
  --runtime-profile presto-torch291-cpu4 --run
```

Other model runtimes are the routes in `src/eo_inputs.py`; the same versioned
entry point supports CPU/MPS and inventory/smoke/full/context modes. A context
run has a distinct fingerprint; it cannot certify a complete census. Legacy
scripts 100/107/109/110 remain unchanged because running jobs fingerprint them.
Script 105 is the legacy in-flight scheduler, not the future corrected extractor.

## Validation

The final maintained suite passes **261 tests**; Ruff lint and formatting pass.
Regression tests cover incomplete/errored status, stale files, fresh publication
and rollback, fixed-versus-old run selection, input population changes, context
scope, mixed-day masking and cache invalidation/corruption. A real-data engineering
profile used **all 851 eligible TTM/state event rows**, producing 845 queries and
8,305 donor rows. First call: **17.81 seconds**; identical cache hit: **0.0364
seconds**. Both returned exactly equal frames. These timings concern one repeated
retrieval, not all model calculations or bootstrap work, and add no empirical
finding. The existing scientific estimator remains unchanged.

No provider data, old embedding, running model source, or unrelated chapter was
removed. The date census uses one low-priority worker. An isolated two-frame
real-imagery Galileo smoke test verified deterministic corrected extraction;
no full corrected encoder census was launched. Results and logs remain local; the correction receipt records exact
validation outcomes and execution status.
