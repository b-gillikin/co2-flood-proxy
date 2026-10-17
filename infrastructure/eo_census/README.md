# Local model queue — 17 October 2026

**Cloud inference cancelled by Brian on 17 October.** Live cloud budget and workers
are zero; all models remain assigned locally. GPU worker/payload entry points
reject execution. Cloud sections below preserve the earlier preparation history,
not an active deployment plan. The research download VM was confirmed deallocated;
no new inference VM was provisioned. Existing Azure imagery/results are retained.

Internal engineering instructions; no model-performance claim or dissertation prose.

## Current execution

Three total local model jobs, each using its existing two-thread model runtime.
The scheduler adopted CROMA without restarting it; TerraMind and DOFA fill the
other slots. Prithvi's completed extraction and aggregate hashes were verified
and retained. The live model adapters and script 100 have not changed in this
update, so existing fingerprints remain valid. Per-model aggregation has its
own output directory; final merging checks geometry and hashes. No model is
selected by outcome or ranked here.

`logs/eo-census/progress.json` is current; the earlier sequential-controller
snapshot is `progress-before-parallel.json`. Logs and data are Git-ignored.
Do not launch another local queue. Rerun script 105 after interruption to verify
completed aggregates and resume patches; `--adopt model:PID` is only for a still
running, explicitly identified extraction child. Keep the laptop awake. Three
is a starting resource ceiling, not a measured universal optimum.

## Cloud ownership and budget

`plan.json` records **$30 total**, with **$25 compute and $5 noncompute reserve**.
The $5 pilot ceiling is INCLUDED within compute, not added to it. One Azure
model worker is allowed. On-demand East US NC4as T4 v3 retail rate was checked
17 October: $0.526/hour. No assumption of credits, Spot pricing or guaranteed
capacity is made. Actual subscription prices must be rechecked before launch.

All jobs currently remain assigned local: T4 quota was 0 in East US, East US 2
and West US 3 on the Azure for Students research subscription. The East US
regional vCPU quota is six. No inference VM was created, no GPU pilot executed,
and no subscription was upgraded. Other workplace subscriptions were not used.
Research GPU quota must be enabled before cloud execution can proceed.

Cloud candidates are Galileo, AnySat and Presto, but this is not an irrevocable
allocation. Before handoff, select pending models from the current queue and
update ownership; never move a running model or pay to repeat a completed one.
Use one owner for a whole model. A GPU run has its own device/platform/code
fingerprint; do not splice its patches into a CPU run without validation.

## Prepared cloud code (not yet a deployed Linux/CUDA environment)

- `prepare_cloud.py` copies an allowlist of code, contexts, catchment geometry
  and the job ledger into a credential-free payload. It does not copy raw gauge
  files, Earth Engine tokens or private SSH keys. Source weights can be acquired
  from pinned public sources by script 97; they are not in the code tarball.
- The device overlay lives only in that payload. It moves the frozen model and
  tensors to the selected device, retaining float32 and disabling TF32. Its
  Prithvi CPU smoke vector was bit-for-bit identical to the live CPU adapter.
  This does **not** establish CUDA compatibility or equivalence for other models.
- Linux candidate dependency lists retain source versions, replacing the local
  macOS-only Torch wheel reference. They must be resolved/tested and recorded
  on the target Linux image; they are not verified Linux lock files.
- `run_cloud.py` runs one model at a time. It requires CUDA, a provision-time
  watchdog, the VM allocation timestamp and managed identity with scoped Blob
  access and self-deallocation. The deadline includes VM setup/idle time and
  preserves a half-hour shutdown allowance. A durable Blob budget ledger
  carries compute estimates across sessions. A model needs a measured duration
  estimate before the production queue admits it. It publishes compact results
  and attempts deallocation on success, error or timeout.

Provisioning/watchdog installation, Linux environment checks and CPU-versus-GPU
numerical/throughput comparison remain **unexecuted** due to quota. A GPU pilot
is not interchangeable with the existing CPU smoke test. Do not mark the cloud
path ready or start a full cloud census based on payload preparation alone.
The watchdog must be armed at allocation before setup; a billing alert is not a
spending cap. Retail-rate timers plus reserve are conservative controls, not an
Azure-guaranteed dollar cap; reconcile actual charges before another session.

## Downloadable results

`package_results.py --model NAME` validates aggregate hashes and writes one
`results/eo_result_packages/NAME.tar.gz` plus SHA-256 sidecar. It contains the
catchment embeddings, coverage, patch-area table and provenance manifest. It
contains no raw provider gauge series. Source imagery/patch intermediates remain
separate; a compact result package suffices for the downstream comparison input.

A real completed example, Prithvi, is about 5 MB and has been uploaded privately:
`limburg-compact-eo/v1/results/prithvi-3d3cb9195255.tar.gz`.

```sh
az storage blob download --account-name stkerkradeprod01bg \
  --container-name limburg-compact-eo \
  --name v1/results/prithvi-3d3cb9195255.tar.gz \
  --file prithvi.tar.gz --auth-mode login
```

Expected SHA-256:
`3d3cb919525543712c80893a8d245b401fa0b7bd173283705be864208e3bc502`.
Download and check hashes before merging into the local analysis; do not publish
unsigned complete-census claims from a partial set of models.

## Active device policy — 17 October, supersedes three-CPU policy

Brian authorized **one MPS worker plus two CPU workers**, three jobs total.
`plan.json` records those lane limits and the per-model devices; the scheduler
checks lane capacity as well as total capacity. Current adoption retains
TerraMind/DOFA CPU processes unchanged. Prithvi's completed CPU aggregate is
verified and retained. CROMA's partial CPU run was interrupted only after the MPS
production smoke and aggregation check passed; its outputs remain on disk.

MPS lane: CROMA, SatMAE, OlmoEarth and AnySat. CPU lane: Prithvi, TerraMind,
DOFA, Copernicus-FM, Galileo and Presto. DOFA stays on its existing CPU run;
Galileo stays CPU because MPS performance depends strongly on input length.
The model/readout/event census itself is unchanged.

Script 107 injects the tested device overlay without changing script 100 or the
live CPU adapter. It adds device/platform and wrapper/overlay-helper source
hashes to the run identity. GPU outputs reside separately under
`data/processed/limburg_eo_mps_sequences/`; only that root is aggregated for
MPS-assigned models. CPU outputs are not silently used to fill a GPU run.
Production MPS fallback is disabled. The overlay uses the existing tested helper
function; it does not call the cancelled cloud launch or payload entry point.

Live status includes `device_limits` and `active_devices`. No more than one GPU
job is admitted. Existing free-space safeguards remain. Do not edit the frozen
MPS wrapper/helper while the run is active, because its source hashes define
resume validity. Handoff evidence is `logs/eo-census/mps-handoff.json` and the
previous CPU-only scheduler snapshot remains `progress-before-mps.json`.
Actual MPS extraction/area aggregation was checked on the real CROMA engineering
fixture with zero errors. A regression test rejects substituting a CPU aggregate
for an explicitly MPS-assigned model. Full-run throughput must be measured;
patch-level speedups are not an end-to-end ETA.
