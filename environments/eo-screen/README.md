# Local EO model preparation

This is acquisition and checkpoint-loading preparation for the existing bounded
EO screen. It is not a model ranking, an eleven-arm analysis commitment, a new
research question or an inference result. TTM and annual AlphaEarth were already
held and are not downloaded again. Event-specific EO embeddings will be computed
from our imagery after input adaptation, not downloaded as a global product.

## Assets and reproducibility

The explicit source/weight lock is
[`config/limburg_eo_model_assets.json`](../../config/limburg_eo_model_assets.json).
It records official repositories, immutable revisions, exact selected files,
publisher hashes/byte counts, licences and input contracts. The earlier planning
note's count of "nine" did not reconcile its later additions. All eleven named
EO families are now accounted for: ten selected public checkpoints and SkySense.
Brian excluded SkySense from the usable screen after its official checkpoint
page did not expose accessible weights. Its official code and research-use
terms are retained for provenance; no further retrieval work is planned.

Files live in `data/raw/limburg_dynamic_model_weights/`, outside Git:

- `models/`: one checkpoint per accessible family, plus essential cards/configs.
- `code/`: pinned official code and TerraTorch architecture support for TerraMind.
- `load_checks/`: actual model-loading checks, separate from download receipts.
- `acquisition-status.json`: per-family download outcomes, not model performance.

Selected weights and support files total **4,082,384,244 bytes** (~4.1 GB).
All ten selected checkpoints are now downloaded and publisher-checksum verified;
the final verification summary is recorded in the tracked manifest. SatMAE's
interrupted transfer was completed with bounded ranges and its publisher MD5
matched before the temporary range copies were removed.
Code and Python environments are additional. Training datasets, optimizers as
separate downloads, duplicate model sizes, demo datasets and large global
embedding grids are not requested. The official SatMAE checkpoint itself includes
training state, so its 1.34 GB file is larger than encoder-only weights. The small
Copernicus-FM variable-name embeddings are included as loader support; these are
not event or catchment embeddings.

```sh
.venv-foundation/bin/python scripts/97_download_limburg_eo_models.py
.venv-foundation/bin/python scripts/97_download_limburg_eo_models.py --download
```

The first command prints the plan. Acquisition verifies every byte count and
publisher SHA-256, Git-blob SHA-1 or Zenodo MD5 before publishing the final file.
Each accepted asset also receives a local SHA-256 receipt. A rerun verifies and
reuses complete files; partial downloads remain resumable. Requests uses the
OpenSSL Python runtime for the Zenodo endpoint that failed with macOS curl's
LibreSSL. No model code or pickle is executed by the downloader. The source
repositories contain their licences; code and weight licences are recorded
separately rather than assumed identical.

## Environments

Six isolated runtimes are installed under `.venvs-eo/` (Git-ignored). Existing
`.venv-foundation` and the Azure acquisition runtime are unchanged. Requirements
and macOS ARM64 resolved package locks are stored here.

| Runtime | Python | Purpose |
| --- | --- | --- |
| `modern` | 3.12 | OlmoEarth, Prithvi Tiny, AnySat, CROMA; Torch 2.9.1/timm 1.0.22. |
| `galileo` | 3.11 | Galileo single-file loader; Torch 2.2.1/NumPy 1.26.4. |
| `legacy` | 3.11 | DOFA and Copernicus-FM; Torch 2.2.1/timm 0.9.2. |
| `terramind` | 3.12 | Pinned TerraTorch source; NumPy 2.2.6, independent geospatial stack. |
| `presto` | 3.11 | Official source; openmapflow 0.2.4/Pandas 1.5.3 resolve legacy import dependencies. |
| `satmae` | 3.11 | Original timm API/NumPy 1.23.5 for published np.float use; no upstream code patch. |

All six pass `pip check`. These are inference runtimes, not claimed paper training
reproductions. TerraTorch is installed from the pinned downloaded repository;
its source dependency constraints differ from the same-version PyPI release.
No inference requires new Earth Engine authentication or a training dataset.

Example recreation (substitute your Python 3.12/3.11 executables):

```sh
python3.12 -m venv .venvs-eo/modern
.venvs-eo/modern/bin/python -m pip install -r environments/eo-screen/modern-macos-arm64.lock.txt
python3.11 -m venv .venvs-eo/galileo
.venvs-eo/galileo/bin/python -m pip install -r environments/eo-screen/galileo-macos-arm64.lock.txt
python3.11 -m venv .venvs-eo/legacy
.venvs-eo/legacy/bin/python -m pip install -r environments/eo-screen/legacy-macos-arm64.lock.txt
```

## Actual loading checks and remaining adaptation

`check_load.py` binds local publisher weights to the pinned architecture, sets
evaluation/frozen mode and records versions. Its optional Copernicus `--probe`
runs a synthetic normalization check. It produces loading diagnostics; the separate real-input runner produces patch embeddings. Run it in the corresponding runtime:

```sh
.venvs-eo/modern/bin/python environments/eo-screen/check_load.py --model olmoearth
.venvs-eo/galileo/bin/python environments/eo-screen/check_load.py --model galileo
.venvs-eo/legacy/bin/python environments/eo-screen/check_load.py --model dofa
.venvs-eo/legacy/bin/python environments/eo-screen/check_load.py --model copernicus_fm --probe
```

All ten accessible families now have real-input adapters. See the
[input-readiness note](../../docs/reviews/limburg-eo-input-readiness-2026-10-16.md)
for routes, normalization sources, masks, dates, limitations and actual checks.
SkySense remains excluded by Brian because official weights were inaccessible.

Recreate the extra runtimes using their matching Python versions and lock files.
For TerraMind, install the pinned architecture source after the lock:

```sh
.venvs-eo/terramind/bin/python -m pip install --no-deps data/raw/limburg_dynamic_model_weights/code/terratorch
```

## Real-input checks and resumable extraction

```sh
# Print all ten isolated check commands without executing models.
.venvs-eo/legacy/bin/python environments/eo-screen/check_real_inputs.py
# Engineering fixture, repeatability, then verified cache resume for all ten.
.venvs-eo/legacy/bin/python environments/eo-screen/check_real_inputs.py --run
# Inventory only, then one model's full locally available patch census.
.venvs-eo/galileo/bin/python scripts/98_extract_limburg_eo_embeddings.py --model galileo
.venvs-eo/galileo/bin/python scripts/98_extract_limburg_eo_embeddings.py --model galileo --run
```

Use the runtime listed above for each model. Full extraction is resumable but is
not automatically launched by preparation. Files still arriving in Azure do not
need to finish for these engineering checks. The runner processes locally staged
TIFFs and receipts, not an automatic full cloud mirror. It reports pending jobs.
Embeddings/masks/date surfaces and JSON provenance stay outside Git under
`data/processed/limburg_eo_embeddings/`. No flood-event performance comparison has
yet used these new embeddings. Sequence/event assembly remains separate work.

## Event-level comparison preparation

Scripts 99–102 now link both event censuses, assemble native temporal inputs,
aggregate exact observed catchment areas and connect to the existing analogue
evaluation. See [the preparation readout](../../docs/reviews/limburg-eo-comparison-preparation-2026-10-16.md)
for commands, coverage, input choices and limitations.

```sh
.venvs-eo/legacy/bin/python environments/eo-screen/check_temporal_inputs.py --run
```

This checks ten two-frame inputs and five native twelve-frame inputs, each with
repeatability and resume. Galileo's current route is 32 spatial pixels with an
8-pixel projection patch, matching a released twelve-frame training layout.
Full extraction/evaluation is explicit; engineering checks do not launch it.

## Full local census execution — 17 October 2026

The full archive pixel/date audit is complete. Script 105 now queues all ten
models sequentially using their pinned runtimes and scripts 100–101. It performs
frozen feature extraction and exact observed-area catchment pooling, not fitting
or analogue scoring. All 742 prepared contexts are visited per model; missing
slots and pixel sequences remain explicit. There is no event sample or new
coverage threshold.

```sh
.venvs-eo/terramind/bin/python -u scripts/105_run_limburg_eo_census.py
```

Only one queue may run (filesystem lock). Do not launch another while it is
active. The queue is local: keep the laptop awake. No Azure VM is started.
Rerunning resumes checksum-/identity-verified patches; it rechecks model queues
rather than trusting a prior completed label. Script 100 pauses with exit 75
below the existing 60 GiB free-space reserve; the queue then stops. Source data
and existing outputs are not deleted. Models are frozen and their fixed inputs,
patch sizes, normalization and temporal readouts are unchanged.

- Queue: `logs/eo-census/progress.json`; per-model logs beside it.
- Live model: `data/processed/limburg_eo_sequences/<model>/<run>/status.json`.
- Per-model aggregates: `results/eo_catchment_representations/per_model/<model>/census/`.
- Merged model tables and provenance: `results/eo_catchment_representations/census/`,
  published after the queue. Errors remain explicit; incomplete outputs are not
  reported as a successful ten-model census. Unexpected stale model tables or
  differing catchment geometries stop the merge.

Inference/repeatability and verified resume were rechecked for the Prithvi
engineering fixture after adding progress/storage controls. Two merge checks
cover model/provenance retention, corruption and differing geometries. Actual
census completion and counts belong in the live status, not this launch note.

### Three-job local scheduler and bounded cloud preparation

The [17 October queue update](../../infrastructure/eo_census/README.md) supersedes
the sequential launch instructions above: three total local jobs, one proposed
GPU cloud job, and a $30 cloud-task budget including its pilot. The local queue
is running. GPU quota is zero, so cloud preparation is not a completed deployment.

### Cloud inference cancelled — 17 October

Brian cancelled the cloud inference plan. All models remain local, with three
concurrent jobs. The live plan sets Azure workers and budget to zero and disables
cloud launch/payload entry points. Existing imagery in Azure is retained.

### Apple GPU test — 17 October

[Actual-input MPS benchmarks](../../docs/reviews/limburg-mps-benchmark-2026-10-17.md)
are complete: seven models executed on GPU, with device/precision limitations
recorded for the others. This was an isolated engineering test. The production
CPU adapters and three-job census have not changed; DOFA resumed after testing.
No Azure work was restarted.
