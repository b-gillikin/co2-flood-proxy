# Frozen EO input preparation, 16 October 2026

This implements the four preparation tasks while the compact Azure archive is
being acquired: isolated runtimes, explicit input adapters, real-input engineering
checks and resumable patch extraction. It creates no flood-event result, model
ranking, new research question or required acquisition.

## Inputs and encoders

| Encoder | Held route | Patch | Adaptation and output |
| --- | --- | --- | --- |
| OlmoEarth Tiny | Ascending S1 VV/VH dB | 64×64 at 10 m | Published computed normalization; missing-pixel masks; mean of seen tokens. No invented missing S2 channels. |
| Galileo Nano | Ten S2 SR bands | 64×64 at 10 m | Published mean ±2 SD scaling; S2 groups seen, unused modalities/NDVI masked; official token average. |
| AnySat base | Ten S2 SR bands | 64×64 at 10 m | Published demo's fixed S2 statistics; day-of-year; tile output, 20 m attention patch. Demo statistics are a transfer choice, not a universal sensor calibration. |
| Prithvi Tiny TL | Six HLS reflectance bands | 224×224 at 30 m, edge padding recorded | Physical reflectance ×10000 once, released DN statistics; year/day-of-year and coordinates; final normalized patch-token mean. |
| CROMA SAR | Ascending S1 VV/VH dB | 120×120 at 10 m | Official example's per-image mean ±2 SD eight-bit contrast stretch, computed on observed pixels; SAR_GAP. Constant-channel stretch is explicitly undefined. |
| DOFA v1 | S2 B5/B6/B7/B8/B11/B12 | 224×224 at 10 m | Published Satlas non-TCI DN//32 clipped to eight-bit, then DOFA's matching six PNG-band statistics; wavelength-conditioned CLS vector. |
| Copernicus-FM | Ten S2 SR bands | 224×224 at 10 m | Reviewed DN statistics/wavelengths/bandwidths; publisher's unknown-metadata encoding; normalized mean-patch vector. Actual spatial/date metadata retained separately. |
| TerraMind Tiny | Selected ten S2L2A bands | 224×224 at 10 m | Released raw-DN statistics, official band selection; final token mean. Every selected backbone tensor must exist in checkpoint; no random fill for missing trained weights. |
| Presto | All observed S2 pixels | 64×64 at 10 m | Official batch helper, masks for absent modalities, pixel coordinates, month; mean of all observed pixel encodings, batches of 128 for RAM. |
| SatMAE multispectral | Ten S2 SR bands | 96×96 at 10 m | Published multispectral DN statistics, channel-group encoder CLS. Only extra classifier channel-CLS embedding may be absent, and must be zero, matching pretraining's CLS construction. |

Normalization/architecture sources are the pinned repositories in
`config/limburg_eo_model_assets.json`: OlmoEarth `data/normalize.py`, Galileo
`src/data/dataset.py` and `config/normalization.json`, AnySat `demo.ipynb`, Prithvi
released inference/config, CROMA README/use script, DOFA
`pretraining/datasets/ofall_dataset.py`/`waves.json`, TerraMind
`terramind_register.py`, Presto's input helper, and SatMAE `util/datasets.py`.
DOFA's non-TCI conversion follows the [official Satlas normalization example](https://github.com/allenai/satlas/blob/main/Normalization.md).
Its absent TCI RGB is not approximated. The six-band route is an explicit transfer
adaptation; it is not an exact nine-band pretraining reproduction. SatMAE,
Copernicus and DOFA use held SR products where source pretraining products differ;
finite inference does not establish robustness to that domain shift.

## Shared contracts

Source TIFF checksums must match their receipts, the receipt job must match the
ledger, and band count, declared names when present, CRS and bounds must agree.
Earth Engine exports can omit TIFF band descriptions: in that case the
checksum-bound receipt's band order is authoritative. Packed validity bits and
finite values determine observation status; physical zero remains valid.

S2 20 m bands/masks/dates use explicit nearest-neighbour alignment to the held
10 m grid, matching acquisition's resampling rule. Each patch retains its full
mask, acquisition-day surface, source products/checksums, candidate scene dates,
source date ranges, bounds, valid fraction and padding. The common optical mask
requires all selected bands; less restrictive model-specific coverage is not
silently mixed into the engineering test.

Inputs are completed-window composites, not instantaneous scenes. Single-frame
encoders receive a declared representative date (median of latest per-pixel
band dates); original date ranges remain available. **Event/as-of joins must use
the completed window's end and account for product publication latency, not the
representative date.** This pass does not construct those joins or claim that
current pretrained weights existed at historical event dates.

All-empty patches produce `no_observation`, never embeddings. Encoders without
native masks use normalized mean imputation for missing/padded pixels (CROMA
uses its eight-bit midpoint). Their pooling can still be affected by missing
coverage. Coverage must accompany subsequent comparisons; this engineering pass
does not validate missingness invariance or establish a coverage cutoff. Native
masks are used where supported. Presto averages observed pixels only.

## Checks and extraction

The engineering fixture is the already-held September 2018 composite, tile
`297600_5625600`. Within each model's deterministic native-size patch grid, the
most observed patch is selected without event outcomes. This is a loader test,
not a sample for scientific inference. The machine-readable check record lists
actual forward and resume outcomes. Forward checks require finite vectors and
exact repeated-input equality. Unit checks cover valid zeros, mask bits, padding,
receipt corruption, job mismatch, out-of-window dates, all-missing input,
HLS scaling and cache invalidation.

`98_extract_limburg_eo_embeddings.py` defaults to inventory only. `--smoke` runs
the fixture; `--run` visits every patch of every locally complete primary tile
(with its required companion), with no random subsample or coverage gate. Pending
files remain pending. Failures are recorded per tile and retried on rerun;
verified completed patches within that tile can resume. Atomic NPZ/JSON outputs
contain embeddings, masks and dates. A fingerprint binds actual publisher-verified
weights, source Python files, input hashes, adapter code, resolved environment,
installed package versions and the fixed seed. Modified/corrupt outputs are
recomputed rather than accepted on filename alone.

Outputs are local, ignored by Git, under `data/processed/limburg_eo_embeddings`.
This script consumes the existing local archive; it does not mirror the Azure
archive, change the downloader or start a cloud compute bill. Extraction from
additional Azure tiles can use an explicitly staged subset with the same ledger
and receipts. The 200 GB acquisition limit is unchanged.

Full temporal sequence assembly, catchment-area weighting, matched event cohorts
and scientific comparisons remain the next analysis work. Native patches cover
different ground extents, so these fixture vectors cannot rank models fairly.
There is no need for another data request or model family to finish this pass.

Validation completed: all ten real-input/repeatability checks and all ten cache
resume checks passed. All six runtimes pass `pip check`. Twenty-one focused unit
checks passed (12 input/normalization checks in the isolated legacy runtime;
9 existing acquisition checks in the foundation runtime). Ruff and whitespace
checks pass. The existing acquisition-time seven-loader summary remains a dated
historical snapshot; the asset manifest's engineering summary records this pass.
