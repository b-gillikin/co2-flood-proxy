# EO signal diagnostics: implementation and verification

29 October 2026. Brian authorized the three diagnostic checks after the completed scarcity analysis. This is research-workflow documentation, not dissertation prose.

## What is tested

Scripts 164–166 use the full 481-storm/eight-gauge census at the initial landmark for three declared information conditions. All ten models are evaluated separately, with recent and monthly-snapshot representations: 20 model/readout jobs, each covering every condition and target. Twenty seasonal negative-control replicates accompany both retrieval and learned probes. No encoder, weights, source imagery or previous scores are changed.

The model inventory preserves selected checkpoint, modality, patch dimensions, output dimension, native temporal versus independent-frame-mean handling, norms and effective rank. Five routes already have native temporal encoding; the claim that all ten simply average frame vectors would be incorrect. Spatial catchment pooling remains a limitation in both groups. Raw stored vectors are standardized within each learned fold; the legacy retrieval probe retains its old geometry for attribution.

Separate same-gauge kernel-ridge readouts learn from earlier calendar years, using earlier-year validation to select shrinkage and EO influence, including zero. Ground-only and augmented arms share coverage/date metadata; same-gauge fitting removes between-gauge identity as a direct source of predictive gains. The quarter-preserving null keeps whole coordinates together, shuffles training associations, and sources test vectors only from the earlier training archive. Retrieval placebos use earlier same-quarter sources with a different context. Coarse-quarter nulls do not establish control of every seasonal or sensor effect.

The head evaluation uses point MAE/RMSE. The old conventional ensemble mean is scored as a point trajectory too, so gains against a trained control can be checked against the original method without confusing point error with empirical CRPS. The retrieval diagnostic continues to use CRPS. This benchmark comparison is diagnostic: the legacy library updates within a year, while the learned heads are fitted at fixed year boundaries.

## Checks and corrections

- Nine diagnostic tests pass: train-only scaling/zero handling, explicit UTC-unit chronology, seasonal null sources, planted-signal recovery, exact zero-EO control, poisoned future outcomes, unsupported EO handling, inner-year separation and read-only Arrow loading.
- The first preflight stopped before producing predictions because pandas returned a read-only array. The raw-model reader now explicitly copies before marking unavailable vectors; a regression test covers that case. No invalid scientific output was published by that failed preflight.
- A real CROMA/recent full-census job completed; independent review checked every fold/source, zero-weight equivalence, and exact reproduction of existing matched/augmented retrieval scores. The complete queue repeats those checks for every model/readout.
- Negative controls and tuning choices are retained, alongside all hourly predictions, supported/active EO flags, source IDs, full outer-fold membership, source/output hashes and environment versions. Null replications are not additional independent storms. Paired intervals retain whole-year dependence and average the null-replication uncertainty.
- Historical finalized records, checkpoint pretraining overlap and unknown actual release times still limit operational replay claims. A successful learned probe would demonstrate conditional predictive information for this interface, not prove a physical mechanism. A failed probe would concern the held pooled representation/task, not all possible fine-tuning or spatial readouts.

## Live artifacts

Configuration: `config/limburg_eo_signal_diagnostic_v1.json`; [protocol](../limburg-eo-signal-diagnostic-2026-10-29.md).

Run: `results/limburg_eo_signal_diagnostic_2026_10_29/`. `execution.json`, `pipeline.json` and `progress/*.json` record live state. The completed review will contain paired effects, model inventories, representation associations, learned-weight use, coverage/case scores and a memo. The initial partial review is explicitly labelled `benchmark_only`.

Two CPU workers run this pass. No GPU job, new acquisition, new email or change to another chapter's data is part of it. Numerical interpretation follows the complete audit; no diagnostic performance was used to choose a favorable setting or encoder.

## Completed execution

All 20 model/readout jobs and the final audit/review completed on 29 October. The audit replayed the original retrieval scores, checked every outer training/source fold and zero-weight equivalence, and retained the full case census. The combined diagnostic/scarcity regression checks pass: 28 tests. [Numerical interpretation](../limburg-eo-signal-findings-2026-10-29.md) distinguishes small learned increments from the absence of a reliable gain over the stronger legacy point-mean benchmark. The diagnostic pipeline used about 15 minutes of two-worker local computation after preflight, without re-extraction. No additional experiment was launched after inspecting these results.
