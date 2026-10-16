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

Three isolated runtimes are installed under `.venvs-eo/` (Git-ignored). Existing
`.venv-foundation` and the Azure acquisition runtime are unchanged. Requirements
and the actual macOS ARM64 resolved package locks are stored in this directory.

| Runtime | Python | Purpose |
| --- | --- | --- |
| `modern` | 3.12 | OlmoEarth inference-only, Prithvi Tiny, AnySat, CROMA; Torch 2.9.1/timm 1.0.22. |
| `galileo` | 3.11 | Minimal Galileo single-file loader; upstream Torch 2.2.1/NumPy 1.26.4/einops 0.7.0. |
| `legacy` | 3.11 | Older timm API for DOFA and Copernicus-FM checks; Torch 2.2.1/timm 0.9.2. |

All three pass `pip check`. These are inference preparation runtimes, not copies
of each paper's training environment. In particular, the legacy runtime is not
a claimed SatMAE reproduction environment. TerraMind's full TerraTorch stack
also needs its own resolved environment: the pinned current source requires
NumPy >=2.2, whereas the modern runtime deliberately retains NumPy 1.26.4.
Do not upgrade the common runtime in place to satisfy that one model.

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
runs a synthetic normalization check. It uses no event data and produces no
event embeddings. Run it in the corresponding runtime:

```sh
.venvs-eo/modern/bin/python environments/eo-screen/check_load.py --model olmoearth
.venvs-eo/galileo/bin/python environments/eo-screen/check_load.py --model galileo
.venvs-eo/legacy/bin/python environments/eo-screen/check_load.py --model dofa
.venvs-eo/legacy/bin/python environments/eo-screen/check_load.py --model copernicus_fm --probe
```

| Family / selected checkpoint | Preparation check | Input work before imagery inference |
| --- | --- | --- |
| OlmoEarth v1.2 Tiny | Strict checkpoint load passed. | Twelve S2 channels expected; held S2 lacks B01/B09. Check explicit missing-band treatment against v1.2's band-dropout training, or the supported SAR route. Training dropout is not by itself a validated missing-band inference adapter. |
| Galileo Nano encoder | Strict checkpoint load passed. | Ten held S2 bands match; combine grids, published normalization and masks for unused modalities. |
| AnySat base | Strict checkpoint load passed, flash attention disabled. | Band order, same spatial extent, normalization and day-of-year companions. Composite pixel dates require a documented temporal adapter. |
| Prithvi EO 2.0 Tiny TL | Strict checkpoint load passed, using publisher position-grid handling. | Six HLS bands match. Convert held physical reflectance to the released normalization units and preserve time/location coordinates. |
| CROMA base, SAR branch | Encoder load passed. | Source supports SAR-only. Check source per-image normalization and masks. The optical branch expects twelve S2 bands, two more than held. |
| DOFA v1 base | Complete backbone load passed with `global_pool=False`, no classifier. | Excluded only pretraining `mask_token` and projector tensors; no missing backbone keys. Verify wavelengths and sensor-specific preprocessing. v2 is a different architecture, not an automatic substitute. |
| Copernicus-FM base | Loading and synthetic normalization probe passed. | Official benchmark mean-patch pooling adds output LayerNorm with deterministic scale one/bias zero; its two absent keys are expected. All pretrained backbone keys must match. Input normalization and TOA-to-SR transfer are documented in the [review](../../docs/reviews/limburg-copernicus-normalization-2026-10-15.md). |
| TerraMind 1.0 Tiny | Weight/source preparation; load not attempted. | Model card explicitly supports S1GRD and S2L2A band subsets. Use that contract rather than requiring RTC or extra bands by default. Resolve TerraTorch runtime separately. |
| Presto default | Weight/source preparation; load not attempted. | Official input helper supports missing channels/modalities. Use its masks and normalization; do not make absent environmental inputs mandatory. Its legacy package imports also need an inference-dependency check. |
| SatMAE multispectral ViT base e199 | Weight/source preparation; load not attempted. | This is the multispectral S2 checkpoint, not temporal RGB SatMAE. Check legacy timm API, channel selection and TOA-to-SR transfer. |
| SkySense | Outside the usable screen per Brian. | Code retained as provenance; weights were not obtained and no further retrieval is planned. |

These differences affect adapter design and interpretation, not whether the
chapter proceeds. Use supported subsets where justified; request no additional
imagery merely because a pretraining dataset used it. No empirical screen has
yet compared these representations. Later extraction must retain past-only
windows, masks, acquisition age and the matched-event cohort, and distinguish
pretrained model exposure from a genuine historically available forecast.
