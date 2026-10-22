# EO retirement and corrected restart — 22 October 2026

Brian authorized scrapping the eight superseded first-run patch caches and
restarting. This replaces the previous plan to finish their held-archive scoring
or maintain two full copies of their extraction directories.

## Retirement completed

- Stopped the current script-102 scoring process and its script-121 queued review.
  The full held-archive comparison did not publish completed scientific results.
  Its workflow state explicitly records cancellation for superseded inputs.
- Retired patch vectors, masks, acquisition arrays and per-patch receipts for
  CROMA, SatMAE, AnySat, Galileo, Presto, DOFA, Copernicus-FM and TerraMind,
  including their superseded partial/smoke runs: 36 run directories in total.
  Cleared the derivable retrieval cache from the cancelled comparison.
- Preserved original run manifests/statuses and complete catchment-level
  aggregates/coverage/area summaries in
  `data/processed/limburg_eo_retired_2026-10-22`. The combined old selection was
  also moved there and its former directory explicitly marked retired. These
  summaries are historical material, not current model-performance evidence.
- Held raw imagery, checkpoints, publisher source and input-population ledgers
  remain available to regenerate historical patch outputs if ever needed.
  Prithvi and repaired OlmoEarth were retained and independently revalidated;
  their protected manifest/status/aggregate hashes did not change.

Free space was about 70 GiB before cancellation. The retirement receipt measured
82.9 GiB free at cleanup start and 476.8 GiB at completion, an increase of about
393.9 GiB during cleanup. The compact retired archive occupies about 0.89 GiB,
including the old combined selection. These are observed free-space/allocation
figures, not an exact attribution of every APFS block under other system activity.

This provides room for the corrected census using the existing compressed NPZ
writer and its 60 GiB reserve. A storage-format redesign is not needed for this
restart. New working outputs continue retaining masks, acquisition days and full
per-patch provenance; only the retired versions were deliberately discarded.

## Corrected execution

The versioned entry point now installs `src/eo_encoder_corrections.py`, while
keeping the historical encoder source unchanged for reproducibility and reuse.
It applies:

1. Same-UTC-day S2 band validity for the seven optical routes.
2. CROMA's sample-SD/eight-bit stretch followed by the missing division by 255.
3. SatMAE's publisher stretch/quantization/0–1 scaling, including neutral fill.
4. AnySat's one-based day-of-year convention from the executable demo/dated
   loaders, with the README disagreement retained in the review.
5. Presto's actual acquisition month per pixel and timestep, with absent slots
   masked and unknown observed dates rejected rather than fabricated.

Future identities directly bind the correction module and Galileo normalization
JSON. Aggregation receipts bind their code/helper hashes, and area-cache paths
include the area-algorithm source hash. Geometry, area calculations, model
weights, input population, readouts and donor/response evaluation design are
otherwise the existing declared comparison. No event subsample or new data
requirement was introduced. The same 742 context definitions remain in the ledger.

All four independent corrected-input captures match their recorded reference
conventions. All eight models passed small real held-input checks for 1-, 4- and
12-frame readouts, finite/repeatable vectors and lossless storage round trips.
The checks include naturally sparse weekly support, not only completely observed
tiles. Each model also has an isolated production-writer smoke run.

The first full-launch attempt exposed an argument-parser issue before any census
embedding was written: the wrapper consumed `--run` as an abbreviation of
`--runtime-profile`. Disabling abbreviations fixes that boundary. Regression
tests now feed the actual eight-model queue commands through the wrapper parser
for both census and smoke modes. This did not change the numerical corrections
or invalidate an already-started full extraction. Failure receipts/logs remain
available alongside the corrected launch record.

The maintained suite passes **307 tests**. The restart controller uses the
existing resource split:

| Lane | Sequential ownership |
| --- | --- |
| CPU 1 | DOFA → Copernicus-FM → TerraMind |
| CPU 2 | Presto, validated Torch 2.9.1 / four-thread profile |
| MPS | CROMA → SatMAE → AnySat → Galileo |

The controller completes all engineering checks before full extraction, then
aggregates, verifies/merges the eight replacements with the two reusable models,
and runs corrected scoring and actual-analogue review. It has no dependency on
finishing the cancelled old scoring and cannot silently substitute retired arms.
The full census is a long-running job; passing its input checks is not a completed
scientific comparison or a claim of improved performance.

Read `logs/eo-coherent-correction-v1/progress.json` for live phase/model states;
the new census is under `data/processed/limburg_eo_coherent_census_v1`. Final
comparison/review outputs remain separate as `results/eo_analogue_comparison_coherent_v1`
and `results/eo_analogue_review_coherent_v1`. The companion check receipt preserves
the retirement measurements and verification evidence in Git.

At restart verification, controller PID 12646 was extracting with DOFA/Presto on
CPU and CROMA on MPS. All three had written new census embeddings with zero
recorded errors; the remaining five models had passed engineering checks and
were queued in their assigned lanes. This is an initial execution observation,
not a completion estimate. All eight current readout receipts match the frozen
entry/correction source hashes.
