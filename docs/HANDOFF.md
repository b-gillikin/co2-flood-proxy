# Limburg handoff — 10 November 2026

## Active scope

Brian accepted the [chapter-sized flood-mapping study](limburg-chapter-sized-study-2026-11-10.md).
The [canonical pointer](../config/limburg_current_study.json) selects its scope,
acquisition manifest and compute policy. The former three-prong programme is
[archived as future ideas](../archive/future-ideas/2026-11-10-broad-spatial-programme/README.md).
Do not resume a queue from an older dated plan.

Compare Copernicus-FM native paired-SAR change (frozen encoder, trained spatial
head), a same-input standard U-Net and a physical SAR change/water method. Test
delivered versus label-blind updated compatible pre-flood reference, with the
same event image and source-trained states. No target adaptation or label-budget
study is required. Source-only selection and three training seeds remain.

## Next work

1. Verify the selected pipeline's intended inputs, normalizers, paired-date head,
   class/ignore semantics and reference-aware physical comparator. Match these
   to existing source-fit records; reuse exact compatible completed fits.
2. Assign evaluation roles after source/event/geographic and label checks for
   all 1,301 released external tiles/nine activations. Inventory all assessable
   local radar cases; July 2021 remains one physical event, not many AOI floods.
3. Retrieve the pinned core external package when acquisition begins. Inventory
   P1 pre-event SAR using a source-fixed orbit/radiometry/coverage/chronology
   rule. Record unavailable updates and preserve P0 coverage. P1 may equal P0.
4. Enumerate only necessary source fits, full-grid inference and scoring;
   profile complete workloads before giving a runtime estimate. Use at most
   one MPS and two CPU workers within memory pressure and the 50-GiB reserve.
5. Execute the paired comparisons, then review event-level differences,
   permanent/flood confusion, false/missed mapped area, support and actual
   preparation/compute burden. Use event dependence and reference provenance
   in uncertainty and interpretation.

## Status and evidence

This scope decision started no download or training job. The acquisition package
is pinned at 9.068 GiB; P1 imagery volume and selected-state reuse are unresolved.
No new agency request, interview or local target-label campaign is introduced.
Preparation checks resolve implementation details; they do not create another
research programme or pass a scientific gate.

[Completed findings](limburg-consolidated-findings-2026-11-10.md) and the
[recovery audit](reviews/limburg-completion-recovery-audit-2026-11-10.md) remain
unchanged. Earlier discharge, TTM, AlphaEarth and other spatial-model work is
historical/supporting evidence, not part of the new queue. Preserve data, weights,
results and provenance. Any later disk cleanup needs its own verified-recovery
process; this scope archive deletes no research data and touches no other chapter.
Brian writes all dissertation prose and sends all emails.

## Most recent audit

[Accepted-scope scientific/data/compute audit](reviews/limburg-chapter-scope-audit-2026-11-10.md)
retains the agreed scope. Particular next checks: P0/P1 processing parity and fixed
labels; actual label-image timing;26source-overlapping target tiles; a named
competent physical comparator; final-source versus existing CV states;1024px
native-grid inference and bounded probability/cache preservation. Existing30full-
label CV states are reusable development evidence, not30all-source deployment
models. Do not infer new accuracy, complete compatibility or a calendar ETA from
the metadata audit. Useful new citations are in
[the scope-audit bibliography](limburg-chapter-scope-literature-2026-11-10.bib).

## Interrupted/unattended runtime requirement

Brian will close the laptop intermittently and may leave it running while away.
[Runtime requirements](limburg-unattended-runtime-2026-11-10.md) cover full-state
training checkpoints, chunk-resumable inference, automatic verified Azure offload,
an independent heartbeat monitor and bounded same-configuration retries. Existing
best-weight recovery is not full training resume. The
[execution plan](limburg-execution-plan-2026-11-10.md) gives the work order.
An Azure email action group, telemetry resource and two disabled production
alerts are prepared; a temporary real alert fired and Brian received its email.
The scientific runner, full-state recovery and automatic offload remain
unimplemented. FileVault is enabled, so reboot/login recovery
cannot be promised without human unlock. Brian chose email alerts to
`btgillikin@gmail.com`.
