# Apple GPU / MPS benchmark — 17 October 2026

Internal engineering report, not dissertation prose, a predictive model ranking or a completed production migration.

## Method

MPS was built and available in the local PyTorch runtime; an actual MPS tensor operation passed. Script 106 tested all ten model adapters against held 2018 inputs from the existing engineering tile. One and twelve completed monthly frames were used, with the most-observed patch and a partial patch where distinct. Twelve-frame inputs retain each model’s existing native-temporal or frame-mean readout. No random event sample or hydrological outcome was involved.

CPU and MPS builds used the same fixed weights and preprocessing, float32 model inputs and their pinned environments. A separate adapter copy moved tensors/models to MPS; the live CPU source and its extraction hashes stayed unchanged. Automatic unsupported-operation CPU fallback was disabled. Three warmed repeats follow a cold call; times include sequence preprocessing and output transfer but exclude tile loading and catchment aggregation. CPU used the existing two-thread setting. Two CPU production jobs continued while DOFA was suspended, keeping no more than three model workloads active. DOFA was resumed and its running state verified afterward.

## Results

| Model | Warm inference speedup, MPS / CPU | Maximum relative vector L2 difference | Interpretation |
| --- | ---: | ---: | --- |
| terramind | 1.85–2.22× | 5.31e-07 | Close agreement in all tested cases |
| dofa | 4.10–5.21× | 2.05e-05 | Small norm difference; stricter coordinate-wise comparison fails |
| croma | 6.20–7.83× | 2.20e-07 | Close agreement in all tested cases |
| prithvi | — | — | CPU/MPS positional-embedding device mismatch |
| copernicus_fm | — | — | Upstream float64 operation unsupported on MPS |
| satmae | 6.05–6.63× | 7.85e-07 | Close agreement in all tested cases |
| olmoearth | 1.29–3.57× | 1.55e-07 | Close agreement in all tested cases |
| galileo | 0.13–2.65× | 4.00e-07 | Snapshots slower; twelve-frame inputs faster |
| anysat | 5.50–6.86× | 9.20e-07 | Close agreement in all tested cases |
| presto | — | — | MPS placeholder-storage/device error in channel embedding |

A value below 1 means MPS was slower. Galileo snapshots were 0.13–0.17× CPU speed; twelve-frame sequences were 2.32–2.65×. DOFA’s worst relative L2 difference was about 0.002%; coordinate-wise `allclose(rtol=1e-3, atol=1e-5)` did not pass. These are engineering diagnostics, not universal scientific tolerances or a reason to abandon a model. All seven successful models repeated their outputs exactly within each tested device. Cosine diagnostics computed in float32 can slightly exceed 1 by rounding.

## Practical interpretation

- Strong acceleration candidates: CROMA, SatMAE and AnySat. TerraMind and longer OlmoEarth inputs also benefit. Galileo needs a readout-aware performance decision; DOFA needs its numerical difference documented if used on MPS.
- Prithvi is already completed on CPU. Copernicus-FM and Presto remain on their working CPU route unless a separate device-compatibility adjustment is justified and checked. The errors concern these adapters/versions, not proof that the models can never run on Apple GPUs.
- A useful next production configuration is one MPS inference worker plus two CPU workers, with a three-job overall ceiling. This benchmark does not establish the best number of simultaneous GPU consumers.
- Preserve completed/partial CPU work. A production device policy needs an explicit fingerprint and provenance, rather than silently adding GPU outputs to a CPU run. No existing encoder source, production vector or model assignment was changed by this test.
- Warm per-patch speedup does not scale directly to end-to-end throughput: raster I/O, patch construction, output serialization and area aggregation remain. Production timing is needed to revise the full-census ETA.
- Local testing does not reactivate cancelled Azure work. No new data, cloud resource, model family or empirical research question was added.

## Reproduction and evidence

```sh
.venvs-eo/terramind/bin/python scripts/106_benchmark_limburg_mps.py --run --pause-pid IDENTIFIED_DOFA_WORKER_PID
```

The command verifies the named DOFA process before suspension and resumes it in a `finally` block. A timeout/resumption regression test passes. Do not reuse an old PID. Local detailed case timings and diagnostics are under `logs/eo-mps-benchmark/`; the compact tracked JSON alongside this report retains per-case metrics. The benchmark controller has a five-minute limit per model.
