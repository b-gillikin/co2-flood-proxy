# August Readiness

Date: 2026-06-21

> Historical planning snapshot. This document is superseded by
> `docs/chapter-readiness-plan.md`, which makes transfer secondary, sets the
> September 8 / October 6 data-freeze gates, and records the direct-state
> analysis required for chapter completion.

Source plan: `chapter-prework/August 2026 - How-To.docx`.

## Current Position

August is a transfer-stress-test and first-writing month. The repo now has an
August v1 transfer dry run and writing scaffold, but it is still not ready for
final transfer interpretation.

The main constraint is now data continuity rather than basic window length:
July models run on the merged IoT frame and the official 30-day train / 7-day
evaluation windows are available, but the IoT record remains gappy and not yet
a continuous annual cycle. KNMI historical backfill is running in Azure and
should improve the reference-meteorology lane over time as local syncs are
pulled back into the repo.

## Prerequisite Status

| August prerequisite | Status | Notes |
| --- | --- | --- |
| Three Kerkrade detectors fitted | Done, provisional | SARIMAX-family, Kalman, and Isolation Forest scripts exist and write anomaly flags. |
| Four-part Kerkrade evaluation run | Done, provisional | `scripts/10_evaluation.py` runs and the official 30-day train / 7-day evaluation scheme is now ready on the merged IoT frame. |
| SMAP and API baselines computed | Partial | API is computed in `data/processed/api.csv`; SMAP live acquisition is deferred. |
| Transfer sites ingested | Partial | RIVM/Luchtmeetnet starter lane exists; currently not enough for the planned "at least 3" transfer-site set. |
| Transfer experiment preregistered | Done | `docs/transfer-experiment-preregistration.md` exists. Commit it before interpreting transfer outputs. |
| KNMI reference meteorology | In progress | The curated Dutch Meuse/Maas station set is backfilling in Azure from current UTC backward toward 2020. Use `python scripts/04_sync_knmi_azure.py` to refresh local `knmi_hourly` CSV/Parquet outputs. |
| August v1 dry-run script | Done, provisional | `scripts/11_transfer_stress_test.py` trains Kerkrade transfer surrogates and scores the cached RIVM lane when at least 24 aligned hours exist. |
| Methods/results writing scaffolds | Done, draft | `docs/methods-outline.md`, `docs/results-outline.md`, and `results/figures/figure_manifest.csv` exist. |

## August Work We Can Start Now

1. **Methods drafting skeleton**
   - Safe to start because the June/July implementation details are stable.
   - Include data provenance, pressure decomposition, Eryilmaz replication, July detector specifications, evaluation protocol, and transfer preregistration.

2. **Figure inventory**
   - Safe to start from existing outputs.
   - Candidate current figures: EDA plots, barometric fit/residual plot, Eryilmaz ROC, signal-characterization plots, detector diagnostics, ensemble agreement, and synthetic-injection plots.

3. **Transfer dry-run maintenance**
   - `scripts/11_transfer_stress_test.py` is runnable now.
   - Treat outputs as a smoke test of feature alignment and scoring mechanics.
   - Rerun after additional KNMI backfill or new transfer lanes arrive.

4. **Transfer-site acquisition plan**
   - Safe to continue data discovery.
   - RIVM is the first lane. IRCEL-CELINE and LANUV NRW should remain discovery-first tasks using official APIs/docs at implementation time.

5. **KNMI backfill monitoring**
   - Safe and already underway.
   - Azure keeps compact station-slim monthly blobs and discards raw all-station
     NetCDF files by default. Sync locally before rerunning KNMI-dependent
     models.

## August Work To Wait On

- Do not treat transfer outcomes as evidence until at least three transfer-site lanes are in hand or the scope is explicitly narrowed.
- Do not claim final July evaluation results until the gappy IoT record is
  extended or the scope is explicitly limited; the official 30-day train /
  7-day windows are runnable now, but interpretation is still provisional.
- Do not write the discussion as if the hydrological mechanism is confirmed; draft methods/results first.
- Do not integrate groundwater unless the requested data arrive and are documented in `docs/data-requests.md`.

## Immediate Next Steps

1. Commit the current June/July/KNMI scheduler and August v1 dry-run state.
2. Let KNMI continue backfilling in Azure.
3. Periodically run `python scripts/04_sync_knmi_azure.py`, then rerun
   `python scripts/11_transfer_stress_test.py` as KNMI coverage expands.
4. Continue discovery for IRCEL-CELINE and LANUV NRW before interpreting transfer evidence.
