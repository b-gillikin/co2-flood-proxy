# Resources for the proposed GEOGLOWS comparison

## Setup update — 14 November 2026

Stages 1–2 are now prepared, not fitted. Nine selected hourly series for
2010–2025 downloaded in about 48 seconds. Complete regional stream/catchment
geometry was also acquired to validate identities; the raw package totals about
521 MiB. Active preparation is about 56 MiB and the isolated dependency overlay
about 59 MiB. An earlier never-fitted setup revision is retained separately.
Free space is approximately 79 GiB, comfortably above the 50-GiB reserve.

The full input audit covers 15,392 opportunities per stage. Its timed baseline
check projects about two minutes for both uncalibrated source passes, excluding
calibration overhead. With previous minute-scale correction fits, allow 1–2
hours for first full execution and checks; a measured end-to-end ETA still
requires the actual run. No new extraction or sustained GPU work is needed.

Seven tributary gauges have usable independent model reaches. Eys does not:
retain its missing local input as a coverage case and use the seven mapped
targets for direct product comparisons. See the
[execution protocol](../limburg-geoglows-stages12-protocol-2026-11-14.md).

The original pre-acquisition estimate below is retained as a dated planning
record; the completed acquisition and setup update above supersede its status.

---

14 November 2026. Internal planning estimate for the three-stage research design discussed with Brian. No new analysis, download, cleanup or cloud job launched. Stage 3 is not included in these estimates.

## Measured local position

- Approximately 80.7 GiB free; 30.7 GiB available above the existing 50-GiB free-space reserve.
- Mac15,7, 36 GiB unified memory, 12 logical CPU cores.
- Presto and AnySat completed context feature tables are present: approximately 79 and 142 MiB respectively. Their SHA-256 hashes match their completed manifests. This verifies these compact tables, not every historical source image or their fitness for a changed context definition.
- Prior individual-experiment preparation occupies about 26 MiB; all ten models' retained score outputs together occupy about 968 MiB. These are existing allocations, not additional requirements.
- Recorded comparable correction jobs: AnySat approximately 70 seconds per scenario; Presto approximately 135–165 seconds. These reused existing baseline predictions; they do not measure the new GEOGLOWS pipeline end to end.

Evidence: `results/limburg_individual_experiments_v1/queue/progress.json`, `features/{presto,anysat}/manifest.json`, filesystem measurements on this date.

## Additional storage estimate for Stages 1–2

| Component | Planning allowance | Basis / limitation |
| --- | --- | --- |
| Selected GEOGLOWS discharge series and reach metadata | 0.1–1 GiB retained | Eight hourly series over sixteen years are about 17 MiB as separate float64 value/int64 timestamp pairs, before file/schema overhead. Reach count and period remain to be selected; this is an illustrative scale calculation, not a measured download size. |
| Retrieval staging, metadata and temporary source chunks | Up to 5 GiB | Actual source-chunk amplification and client caching are unmeasured. Subset the selected reaches/time range and inspect transfer/cache size before extending retrieval. Do not mirror the global archive. |
| Matched inputs, predictions, calibration fits, uncertainty summaries and review outputs | 1–3 GiB | Reuse compact EO features and existing observations; no duplicated imagery, checkpoint collection or large per-patch cache is needed for this comparison. |
| Overall working allowance | 10 GiB | Conservative allowance including staging; expected retained outputs are smaller. Leaves about 70 GiB free at present, about 20 GiB above the reserve. This is a planning allowance, not a scientific data cap. |

Current space is sufficient for this proposed scope. No deletion, Azure offload or other-chapter data change is needed now. Recheck actual free space and projected peak staging before retrieval and fitting; avoid simultaneous redundant caches. If retrieval exceeds the allowance, assess chunk layout and stream/subset or offload verified data rather than silently restricting scientific coverage.

GEOGLOWS documents per-reach retrospective queries through AWS and hourly/daily/monthly/yearly resolutions: https://geoglows.readthedocs.io/en/latest/api-documentation/data.html . Query support does not guarantee small network transfers for every storage layout.

## Runtime estimate

For the proposed same-catchment Stages 1–2 with existing AnySat/Presto features and small correction heads:

- Selected-series acquisition: provisionally 15 minutes–2 hours after reach identification, depending on service response and source chunks. Not a measured transfer benchmark.
- Temporal alignment, paired input preparation and conventional analogue recalculation: provisionally 30 minutes–2 hours.
- Small-head calibration, matched comparisons, bootstrap summaries and automated event diagnostics: provisionally 30 minutes–2 hours. The older minute-scale fits support the expectation that fitting is inexpensive; new source-specific preprocessing and calibration still need implementation.
- Working machine-time estimate: approximately 2–6 hours, with a full working day allowed for retrieval/retries and checks. This is a planning estimate, not a queued-job ETA. Reach validation, scientific implementation and Brian's interpretation are additional human/agent work, not included in machine time.

Two CPU workers are a reasonable initial allocation on this 36-GiB machine, with numerical-library thread counts controlled to avoid oversubscription. No sustained GPU lane is required for reusing the held EO features. Benchmark the first complete new data/preparation/fit unit and update the estimate before full execution. Optional TTM re-encoding is not priced as though it were already specified; estimate it separately if selected.

A changed EO time window, new imagery, encoder fine-tuning, external-river extraction or historical as-issued forecast archive would require a separate estimate. The current estimate does not assume any of those expansions.
