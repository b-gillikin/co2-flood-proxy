# Limburg step 4 — source-only final fit record

Internal methods and run audit, 10 November 2026. This records source
development and execution, not external flood-map performance.

## Frozen source-only choices

The five held event folds, seed 42 and full source labels selected the lowest
mean-IoU rate in the completed three-rate grids: 0.0002 for the frozen
Copernicus encoder/spatial head (mean fold IoU 0.6113), and 0.0001 for the
same-input standard U-Net (0.6336). The median fold-best epochs are 7 and 10.
Both full-source fits retain the original 50-epoch cosine schedule, stopping
at their selected epoch rather than compressing the schedule. These learning
rates sit at the tested grid boundary; they are **selected settings, not
globally optimized rates**. All 5,000 records and 20 source events enter each
final fit. No external labels, scores or image statistics set those choices.

The physical comparator uses the original un-clipped four-band source rasters,
not an inversion of clipped neural inputs. Across 30 declared VV/VH darkness
and change rules, equal-event source flood IoU selected VH, −21 dB dark-water
threshold, ≥3 dB drop, mean source event IoU 0.5123. Its per-event results
range widely, so this is a transparent source-calibrated comparator rather
than a production flood service. Neither physical rule nor learned settings
were selected on GEOID target labels.

## Fit/recovery state

The first U-Net all-source state (seed 42) completed 10 epochs and 3,130 total
updates with no skipped examples. Epoch 1 was intentionally interrupted after
its atomic full-state checkpoint; rerunning the same command recovered that
checkpoint and completed epochs 2–10. The final model SHA-256 is recorded in
`results/limburg_chapter_sized_v1/final_source/unet-42/complete.json`.

The native Copernicus seed-42 fit is running. A queue is prepared to produce
the other four states after it, checking the common MPS lock, per-state
manifest, disk reserve and final model hashes. The production email alerts
remain disabled until Brian wants the long-run alert window.

## Code/data/chapter audit

The fit runner reads only the pinned Flood-S1 source inventory, tensor cache,
and for the native route the previously verified frozen feature cache. Its
per-epoch checkpoints include model, optimizer, scheduler, random states and
completed epoch. The frozen encoder is identified by held code/weights; only
its trainable head is serialized. A corrupted latest checkpoint falls back to
the previous generation in a dedicated test. No older study state was
rebranded as an all-source final fit. Final artifacts live in a new result
tree; other chapters and historical results were untouched.
