# Monitoring-loss data acquisition — 28 October 2026

Brian authorized acquiring the useful additions for the whole new analysis. Both pulls use local storage; no Azure VM, storage expansion or model inference was launched. All other chapters' data is untouched. This is source acquisition, not a simulation result.

## Soil and snow: running

`scripts/150_fetch_monitoring_land_state.py --download --workers 2` retrieves ERA5-Land hourly soil-water layers 1 and 2 and snow depth **water equivalent** for 2009–2025, including antecedent history. The 0.1-degree covering grid has 72 cells and covers all nine existing exported catchments. The estimated float32 value payload is 128,749,824 bytes (0.120GiB), excluding metadata; actual NetCDF compression is smaller.

CDS rejected a quarterly test on request-cost limits. The production pull uses 204 monthly requests, with two concurrent workers, saved remote request IDs, checksums and atomic source writes. The first real month passed timestamp, grid, units, finite-value and physical-range validation before the remaining requests were submitted. Snow is stored in metres water equivalent, not snow thickness; genuine zero is valid and small floating-point underflow is preserved.

- Sources and per-month receipts: `data/raw/limburg_monitoring_land_state/`.
- Live progress: `data/raw/limburg_monitoring_land_state/manifest.json`.
- Log: `logs/monitoring-acquisition-2026-10-28/land-state.log`.

At the subsequent status check, **57/204 months (27.94%)** were validated, totaling 14,254,661 bytes, with no recorded failures; the remaining worker was verified alive. This is a dated snapshot. Read the progress manifest for current status. Retrieval time includes CDS processing/queue time and is not determined by the small transfer volume. The same command resumes requests and verified local deliveries.

## Targeted EO windows: completed

`scripts/151_prepare_monitoring_eo_gaps.py` reconstructs causal rainfall timestamps and inventories their completed EO contexts using held catalogues. It leaves existing scientific results and their source archives unchanged. The eight-gauge regional preparation candidate contains 481 episodes versus the original 468; regrouping changes event identities, so this is **not** simply 13 independent additional storms or an adopted new scientific result. All original and regional-candidate context requirements were included in the acquisition inventory.

Of 876 required source windows, 872 were already indexed. Four missing completed weeks were acquired:

- 4–11 May 2020.
- 27 June–4 July 2022.
- 4–11 July 2022.
- 11–18 July 2022.

These cover 240 primary exports and 202 supplemental exports for the previously declared TOA/QA60 and separate ascending-orbit routes: **442/442 validated files, zero failures**. Actual compressed size is **643,309,684 bytes (0.599GiB)**, below the 3.034GiB raw tile estimate. Each export retains source identities, acquisition dates, grid and validity masks, with receipt hashes and pixel/date audit. Zero-valid-pixel tiles remain explicit; a completed download is not proof of finite model support.

- Sources/receipts: `data/raw/limburg_monitoring_eo/`.
- Completion and identity: `data/raw/limburg_monitoring_eo/progress.json`, `identity.json`.
- Pixel audit: `data/raw/limburg_monitoring_eo/pixel-audit.json`.
- Inventory/calendar candidate: `results/monitoring_acquisition_2026_10_28/`.
- Command: `scripts/152_download_monitoring_eo_gaps.py --download --workers 2`.

There are nine newly indexed sequence-context identities; most constituent windows were already held. Their embeddings have **not** been extracted. Future extraction must join the old and new archives by exact window/product/source identity and retain input-route distinctions. No full ten-model restart was launched.

## Storage, outstanding work and checks

Free disk was about 76GiB at launch and about 80GiB at the status check; both acquisitions fit locally. The soil/snow worker remains the outstanding download. Provider-only historical delivery/outage metadata is still an optional request, not acquired and not sent automatically. No new agency reply is required for the counterfactual study.

Next: let soil/snow finish and validate its complete-period inventory; build source-audited catchment land-state summaries; attach the revised event clocks and legal EO contexts; then implement the simulation plan. Existing raw provider records, earlier results, model weights and other chapters remain intact.

Twenty-one targeted acquisition/source-contract tests pass, including the new rainfall-prefix and soil/snow source checks. Ruff checks/formatting pass for the new scripts/tests. The initial broad test invocation omitted this machine's required `PROJ_DATA`; rerunning with the configured projection directory passed all 21 tests. No empirical result or scientific gate pass is claimed.
