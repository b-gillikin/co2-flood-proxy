# Limburg chapter and code audit — 2026-10-21

The retrospective analogue design remains coherent. The audit found three high-priority problems in the new EO input/handoff workflow, plus reproducibility, performance and documentation weaknesses. These need resolving before interpreting the final EO model rankings. They do not establish that earlier hydrological/TTM/AlphaEarth results are wrong, or that the chapter needs a different question or more datasets.

This is an audit, not an implementation pass: no active worker source, extraction job, original data or prior result was changed. Brian retains all dissertation writing. There is no new scientific stop rule, preregistration requirement or gate pass.

## Scope and checks

Reviewed the active question/design, evidence index and analysis inventory; conventional/raw/TTM/AlphaEarth retrieval, donor chronology and uncertainty paths; EO acquisition, inputs, adapters, extraction, aggregation, schedulers and comparison runner; runtime consistency and current documentation. This is not a line-by-line certification of every historical file or an independent rerun of every empirical analysis.

- Maintained test suite: **243 passed**, 47.50 seconds. Command: `PROJ_DATA="$PWD/.venvs-eo/terramind/lib/python3.12/site-packages/pyproj/proj_dir/share/proj" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-foundation/bin/python -m pytest -q`.
- Ruff lint: passed. Formatting: one existing file, `tools/disaster_recovery.py`, would be reformatted; 137 already formatted.
- `pip check`: passed in all seven EO environments (legacy, modern, satmae, terramind, galileo, presto and presto-torch291). Cache-permission warnings do not indicate broken dependencies.
- Two isolated integration reproductions used temporary fixtures, without modifying production outputs.
- Actual S2 acquisition dates were compared in eight diagnostic tile/window pairs. This is a targeted engineering diagnosis, not a sample-based scientific analysis or an estimate of archive-wide prevalence.
- [Compact evidence receipt](limburg-chapter-code-audit-checks-2026-10-21.json) preserves source hashes, check outcomes and all eight tile measurements. Detailed local logs are under `logs/chapter-audit-2026-10-21/` and `logs/chapter-audit-*-2026-10-21.log`.

## Findings

### F1 — High: default final merge does not select the repaired model outputs

**Location:** [script 105, merge_aggregates](../../scripts/105_run_limburg_eo_census.py), lines 44–91; [script 111, separate recovery aggregation](../../scripts/111_run_token_mask_recovery.py), lines 57–63.

The original scheduler hardcodes `per_model/<model>/census`. Repaired OlmoEarth and Galileo aggregates are written to `per_model/<model>/token_consistent/census`. Finishing recovery therefore does not make those corrected outputs the defaults of the final merge. The original queue can retain the old OlmoEarth aggregate and omit the independently recovered Galileo output.

**Consequence:** an analyst following the default chain could compare superseded mask policies, miss a repaired model, or obtain an empty all-ten intersection. No completed new EO ranking was shown to be corrupted; the risk concerns the pending final comparison.

**Correction:** create one explicit model-to-selected-run/aggregate map, including mask policy and extraction scope; have merge and comparison consume it. Use the corrected paths deliberately and preserve superseded runs as historical evidence. Add a regression test with both old and recovered outputs present.

### F2 — High: aggregation/completion checks can certify stale or incomplete output

**Location:** [script 101](../../scripts/101_aggregate_limburg_eo_catchments.py), lines 58–70 and 198–216; [script 105](../../scripts/105_run_limburg_eo_census.py), lines 94–120 and 312–317; [script 102](../../scripts/102_connect_limburg_eo_experiments.py), lines 153–159.

Script 101 skips stale source manifests but does not remove or reject prior model parquet files in its destination. If no current run contributes rows, it can still return success and hash those old model files into its new manifest. Separately, script 105's completion check verifies hashes/code/device but not extraction status or error counts. Its queue adds models to the merge when aggregation succeeds even if extraction failed. Script 102 checks output hashes and the engineering flag, but not the selected extraction contract/status.

**Reproduced:** a temporary errored extraction was accepted by `completed_aggregate`; a temporary stale aggregate survived a no-accepted-input aggregation, exit code 0, with empty `contexts_by_model`, and appeared in the new output hashes. These are distinct from ordinary scientifically useful partial coverage.

**Correction:** write aggregates to a fresh/atomic destination; reject unexplained pre-existing outputs; validate the selected run, expected scope and completion/error state. Intentionally partial results can remain available, explicitly labelled with their actual coverage. Test stale, empty, errored and partial cases rather than treating every zero exit as complete.

### F3 — High input-compatibility risk: S2 spectral bands can represent different acquisition days

**Location:** [script 96, composite](../../scripts/96_acquire_limburg_compact_eo.py), lines 243–287; [eo_inputs.read_tile](../../src/eo_inputs.py), lines 118–155.

The 10 m and 20 m products are composited separately. The loader upsamples the 20 m bands, intersects masks, concatenates reflectance and assigns the latest of the two acquisition dates. It does not require the two sets of bands to come from the same day. Using the latest date is conservative for the age bound, but does not make a mixed spectrum a same-time observation. Ordinary spatial mosaicking is not the issue; within-pixel cross-band temporal coherence is.

Confirmed examples, using the union of actual catchments within each tile and common-valid observed area as denominator:

| Window | Two diagnostic tiles: mixed-date share of observed catchment area | Largest day difference over valid tile pixels |
| --- | --- | --- |
| July 2018 monthly | 0.069%, 0.103% | 25 days |
| July 2021 monthly | 4.946%, 4.669% | 10 days |
| 5–12 July 2021 weekly | 2.333%, 1.003% | 2 days |
| 12–19 July 2021 weekly | 0%, 0% | 2 days outside the catchment union |

This establishes an undocumented input difference, not its effect on downstream scores. It potentially affects the seven S2-based adapters: DOFA, Copernicus-FM, TerraMind, SatMAE, AnySat, Galileo and Presto. It does not implicate radar-only CROMA/OlmoEarth or HLS Prithvi through this particular defect.

**Correction:** first count same-day agreement over the held census; then compare source-consistent compositing or an explicit same-day mask, with versioned inputs and a coverage/sensitivity account. Check compatibility with each model's documented input assumptions. Do not silently alter active worker code or assume every embedding needs rerunning. The eight examples cannot establish archive prevalence or the size/direction of any score change. Additional downloads alone do not solve the joining rule.

### F4 — Medium: extraction identity omits the intended input population

**Location:** [script 100](../../scripts/100_extract_limburg_eo_sequences.py), lines 35–69 and 110–139.

The run fingerprint binds model weights, source, packages, purpose and readout, but not the `jobs.json`/`contexts.json` hashes or the `--context` selection. A one-context invocation and a full census can therefore share a run directory and status file. A changed input calendar can also retain prior patches under that identity. Per-patch provenance is useful but does not specify the complete intended population; aggregation scans saved patches rather than verifying that population.

**Correction:** include input-ledger hashes, selection scope and expected context IDs in the identity. Give a context-only run a distinct destination. Record actual availability separately from intended census coverage. This is a reproducibility correction, not a requirement to discard events or preregister.

### F5 — Medium: the final comparison repeats substantial work

**Location:** [script 102](../../scripts/102_connect_limburg_eo_experiments.py), lines 185–248.

With all matched populations nonempty, the configured grid can issue **8,964 retrieval calls** before bootstrap contrast work: 249 arm evaluations × 3 readouts × 2 river scenarios × 2 quality settings × 3 archive policies. Several conventional/raw/state/identity calculations repeat across populations. This is a static upper-bound work count, not a runtime prediction. The current plumbing tests do not establish throughput for a realistic cohort.

**Correction:** profile a realistic cohort, then cache identical distance/retrieval computations by population, inputs and code. Preserve the full event census and authorized model comparisons. Partition/stream large outputs where useful. Compact duplicate patch metadata only after retaining equivalent provenance and validating recovery; do not delete active runtime dependencies or original provider deliveries.

### F6 — Low: front-door documentation trails the active EO execution

**Location:** [README](../../README.md), opening description and reproduction chain; [active design](../limburg-historical-analogue-active-design-2026-10-13.md); [representation arms](../ai-eval/representation-arms.json); [handoff](../HANDOFF.md).

The README mainly describes TTM/AlphaEarth and its reproduction chain predates scripts 99–115. The active design leads with the October 16 preparation state; the small representation-arm registry does not describe the ten-model expansion. Newer handoff entries contain the details, but older sections still labelled current can suggest obsolete commands or output selections.

**Correction:** provide one concise current execution table distinguishing prior results, running extraction, corrected runs, acquisition and pending comparisons. Preserve dated history. Link the selected-run map from the README/design. Formatting `tools/disaster_recovery.py` is routine cleanup and lower priority than the above.

## Scientific design: what is working and what the claims mean

The chapter remains an evaluation of whether basin-aware representations help retrieve useful historical high-water analogues across Dutch/German tributaries, including identifying weak evidence. Its core retrieval uses prior, completed donor outcomes, excludes the query storm, limits repeated storm contributions, and retains current-state controls. The frozen TTM backbone, conventional rainfall/discharge references, AlphaEarth/area/identity controls, cross-river/country restrictions and explicit coverage reporting are appropriate safeguards. Exact catchment-area weighting and separate native-temporal versus order-invariant readouts are strengths.

Retrospective full-era p99 labels/scales do not constitute a historical forecast replay. Current warning thresholds applied to old records are not reconstructed historical official warning decisions or observed inundation labels. Frozen pretrained models may postdate the events. These are already acknowledged interpretation limits, not reasons to abandon the retrospective question.

Keep all model/readout/control outcomes visible rather than selecting the most attractive slice. Storm/year bootstrap intervals remain conditional on the held donor archive; they do not cover model-selection uncertainty or establish country-level causality. Many events do not create many independent catchments. A missing representation under a native sequence contract is not evidence that no potentially useful observations exist.

The audit adds no empirical advantage claim for EO, AI or the new downloads. It found no basis for new interviews, data requests, model families or research questions.

## Smallest correction sequence

1. Establish the authoritative model/run map and repair stale/partial aggregate handling, with isolated tests. No need to interrupt active extraction.
2. Run the date-agreement census and decide/document the S2 input correction and sensitivity. Version changed inputs; assess affected work before rerunning anything.
3. Bind future extraction identities to the input population; leave existing immutable runs auditable.
4. Profile/cache the comparison workflow, then update the current execution documentation and run the matched comparison with explicitly selected inputs.

Do not interpret final EO rankings until their selected inputs and merge are correct. This is ordinary scientific/code validity, not a blanket restriction on concurrent data acquisition, model completion, or the chapter's other analyses.
