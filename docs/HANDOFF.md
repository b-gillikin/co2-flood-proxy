# Session handoff

## 2026-10-22 EO paper/appendix review; extraction unchanged

The [literature/runtime review](reviews/limburg-eo-model-literature-and-runtime-2026-10-22.md)
records fifteen primary sources and all ten checkpoint routes. Frozen retrieval
and per-date pooling have precedent; published GPU throughput is not a Mac ETA.
No additional demonstrated input defect was found. Presto mean-plus-spread and
Copernicus-FM known metadata are documented options, not required reruns or
implemented changes. The corrected queue remains in charge; extraction code,
weights, runtimes and scoring rules were not changed by this review.

## 2026-10-22 superseded EO caches retired; corrected restart

Brian authorized discarding the eight superseded patch caches. Old scoring and
its queued review were cancelled. Retirement of 36 full/partial/smoke run
directories completed; free space is about 477 GiB. Original manifests and full
catchment summaries are in `data/processed/limburg_eo_retired_2026-10-22` (~0.89
GiB); old per-patch records were deliberately retired and can be regenerated.
Raw imagery/weights and the two reusable models remain held and verified.
The [restart record](reviews/limburg-eo-retirement-and-restart-2026-10-22.md)
supersedes the earlier held queue/storage-redesign plan. Four publisher/pixel-date
corrections are implemented in a versioned module; all eight real 1/4/12-frame
checks pass. The full-launch `--run`/`--runtime-profile` abbreviation issue was
caught before census writes and fixed with actual-command regression coverage.
The suite passes 307 tests. The queue again owns two CPU workers and one MPS
worker; it reuses Prithvi/repaired OlmoEarth and later scores only the corrected
selection. Consult its progress JSON for current execution; no completed new
scientific comparison is implied by this launch note. Restart verification
confirmed controller PID 12646 and three active census writers: DOFA/Presto on
CPU and CROMA on MPS, all with positive written counts and zero errors.

## 2026-10-22 ten-model documentation review — correction still held

The [documentation review](reviews/limburg-ten-model-documentation-review-2026-10-22.md)
and its hashed source inventory supersede the earlier assumption that CROMA
could be reused unchanged. Independent input captures show CROMA receives
0–255 instead of the publisher's 0–1; it joins the correction, bringing the
recommended rerun to **eight models**. AnySat's README says zero-based day of
year, but its executable demo and several dated training loaders use one-based
dates; the captured one-day mismatch should be resolved in the versioned adapter.
SatMAE scaling and Presto pixel-month issues remain as previously documented.
Copernicus-FM's known location/date/scale inputs are an optional underused
capability, not missing required data. Prithvi and repaired OlmoEarth remain
reusable on this review's evidence. Four no-weight input diagnostics completed;
no production numerical source or active scoring was changed. Script 122 still
contains the old seven-model list and must not simply be restarted unchanged.
Consolidate the fixes and compact storage before the authorized two-CPU/one-MPS
run. No additional imagery/checkpoint is required by this review.

## 2026-10-22 pre-correction audit — correction held

The [full audit](reviews/limburg-pre-correction-full-audit-2026-10-22.md) found a
SatMAE normalization mismatch, removable Presto pixel-month approximation,
missing direct Galileo normalization-JSON binding, and an output layout that
cannot be duplicated within local free space (285.7 GiB selected seven vs ~70
GiB free; vector payload alone 2.83 GiB). The correction controller was stopped
while waiting, before extraction; progress records `held_for_requested_audit`.
Current scoring/review still run. Bundle the numerical/provenance corrections,
compact storage and verified cleanup before restarting two CPU/one MPS workers.
284 tests and 28 publisher-asset checks pass, but do not establish input-transform
conformance: the independent SatMAE input capture demonstrates the gap. No source
imagery, selected result, provider delivery or other chapter's data was deleted.

## 2026-10-22 S2 correction authorized and queued — earlier authorization; now held

Brian authorized the seven-model same-day correction after current scoring,
again with two CPU workers plus one MPS worker. Script 122 waits for the current
workflow, then runs corrected extraction, aggregation, a separate merge,
comparison and case review. Three native-product models are reused; held
results and the Azure expansion remain separate. The [execution record](reviews/limburg-eo-current-archive-execution-2026-10-22.md#authorized-correction-queue--22-october)
lists lane ownership and paths. Read
`logs/eo-coherent-correction-v1/progress.json` for live status. This queue does
not mean corrected embeddings or results already exist.

## 2026-10-22 ten-model merge and current-archive execution — current

All ten selected aggregates verified and merged, including completed Presto and
the repaired Galileo/OlmoEarth runs. The full script-102 comparison is running;
script 121 waits on publication and then executes script 120's census-level
actual-donor review. The [execution record](reviews/limburg-eo-current-archive-execution-2026-10-22.md)
records coverage, readouts, controls, interpretation limits and output paths.
Read `logs/eo-current-archive-workflow-2026-10-22.json` for live completion state;
this launch note does not claim finished scores. No new imagery enters this
held-archive pass. Mixed-day S2 exposure and legacy provenance limitations stay
explicit; no full same-day corrected embedding census is implied.

## 2026-10-21 second-audit fixes implemented — current

[Correction record](reviews/limburg-eo-second-audit-fixes-2026-10-21.md).
Comparison planning is isolated under `<out>/planning`; executed outputs publish
from a fresh staging directory with a hash manifest and explicit empty-result
status. Legacy comparison entry rechecks the selected context ledger. Population
identities are portable; external/old absolute-path inputs have explicit root
resolvers. Partial output aliases normalize before destination separation.
Future extraction fingerprints a small population builder, not downstream
integrity code. Reviewed metadata-only snapshots preserve earlier valid run
receipts without accepting unknown numerical changes. A real Galileo smoke is
bit-identical to its earlier corrected embedding/masks/dates. No scientific
scores or full corrected census were run in this pass. Active model jobs remain
unchanged. All 273 maintained tests, lint and formatting pass; real-writer
integration and numerical-equivalence outcomes are in the linked check receipt.

## 2026-10-21 second audit — follow-up findings

[Second audit](reviews/limburg-eo-second-audit-2026-10-21.md) reproduced stale
comparison-score files surviving planning/zero-score runs, a missing legacy
context-ledger check at comparison entry, nonportable absolute ledger paths,
and a relative-path bypass of partial/full merge destinations. It also found
an unnecessarily broad extraction fingerprint dependency. These are pending
corrections; no production source or active job was changed in this audit.
261 tests, lint and formatting pass. Eight completed aggregates still verify;
Presto and Galileo are now both awaiting aggregation completion. The full S2
date census remains complete. No new scientific score or data requirement.

## 2026-10-21 audit fixes implemented — current execution

[Implementation record](reviews/limburg-eo-audit-fixes-2026-10-21.md) and
[check receipt](reviews/limburg-eo-audit-fix-checks-2026-10-21.json).
All six audit findings have code/documentation corrections. The original input
loader and active model-run fingerprints are unchanged; corrected extraction
is versioned separately in script 118. Its isolated real-imagery Galileo smoke
is deterministic and complete. The maintained suite passes 261 tests; lint and
format checks pass. Full-cohort retrieval caching exactly reproduces the
uncached result (17.81s first call / 0.0364s hit for that one repeated retrieval).
Script 117 verified/merged the eight completed models under `available/census`;
script 102 planning validated that partial selection without running scores.
Missing models remain visible; no full-model gate blocks completed-model work.

The full 8,538-pair S2 date-agreement census completed with zero errors.
Same-day masking removes 1.169% of observed union area across monthly windows
and 0.378% across weekly windows (area-window weighted; not score effects).
The check receipt preserves window counts and output hashes. Existing Galileo
aggregation and Presto extraction continue. Script 117 `--merge` will select
the corrected recovery paths when all ten are ready; an old in-memory
controller's legacy merge is not the new scoring default. Same-day masks have
not yet been applied to a full corrected embedding census, and no new EO
scientific scores were run. Keep old results labelled with their actual policy.

## 2026-10-21 chapter/code audit — current corrections

[Audit and prioritized findings](reviews/limburg-chapter-code-audit-2026-10-21.md):
243 maintained tests and all seven runtime dependency checks pass. The audit
reproduced stale/incomplete aggregate acceptance, identified the default merge's
failure to select token-consistent recovery outputs, and confirmed mixed-date
S2 bands in diagnostic held tiles. Quantify date agreement over the census and
select/version corrected inputs before interpreting final EO rankings. Running
jobs and fingerprinted source were not changed. Earlier results are not shown
invalid; no new dataset, RQ, preregistration rule or scientific gate was added.
See the audit for input-population fingerprints, comparison caching and current
documentation corrections. It supersedes blanket readiness inferences from hash
or finite-vector checks alone.

## 2026-10-21 supplemental download moved to Azure — current

[Cloud handoff](../infrastructure/eo_expansion/README.md) is live on the existing
small acquisition VM, service `limburg-eo-expansion.service`, private Blob prefix
`expansion-v1`. All 13 cloud product exports/readbacks passed; production has
committed new files with zero failures. The prior Azure acquisition service is
disabled. Local script-114 downloader and seed uploader are retired; 3,418 local
pairs are retained, 137 uploaded pairs will receive cloud readback, and Azure
fetches the remaining 3,281 local-only pairs directly so no laptop upload is needed.
Original archive/inference jobs are unchanged. Keep the existing October 29
shutdown timer; service also deallocates on completion/error. Supplemental storage
headroom is 300 decimal GB, separate from original `v1`. For live status use
Azure CLI Python with script 115 `--status` (writes `cloud-progress.json`); local
`progress.json` deliberately records `retired_to_azure`, not current acquisition.

## 2026-10-21 broader EO acquisition — running

Brian prefers more useful data over download economy. [Expanded acquisition](reviews/limburg-eo-acquisition-expansion-2026-10-21.md)
adds 66,913 separate files across the existing 930 windows: other SAR orbits,
Landsat 5/7/8/9 SR and S2 TOA/QA. Script 114 is running locally with three network
workers; check `data/raw/limburg_eo_expansion/progress.json` and `worker.json`
before starting another worker. Thirteen actual product exports passed. All jobs
passed date/orbit provenance checks. Do not edit its fingerprinted script while
running. Current encoder runs and original archive are unchanged. Additional
data are not automatically compatible encoder inputs or completed comparisons.

## 2026-10-21 readout coverage and conventional-reference contrasts

[Exact snapshot–weekly loss decomposition](reviews/limburg-eo-readout-diagnostics-2026-10-21.md)
is complete. Radar losses are all missing catalogue source weeks; optical losses
combine source absence, zero-valid-pixel weeks and sequence support. There are
no incomplete local-download losses. Script 113 retains every observation/slot,
country, gauge and year. It cannot attribute all masking specifically to clouds.
Script 102 now reports direct conventional-reference paired intervals wherever
the rainfall comparator exists, preserving TTM references and existing equal-count
storm/year resampling. This supersedes the preceding note that this runner change
is still needed. No scientific scores were run; active workers are unchanged.

## 2026-10-21 completed-model coverage and comparison review

[Eight-model audit and comparison choices](reviews/limburg-eo-comparability-2026-10-21.md)
are complete. Corrected OlmoEarth is explicitly selected; all eight aggregate
checks pass. Eight-model common populations are 479 snapshot / 357 monthly /
115 weekly events, diagnostic only while Galileo/Presto finish. Keep per-model
populations and matched query/donor archives; do not rank unmatched errors.
Script 102 needs a direct conventional-reference paired contrast before any
claim of EO improvement over rainfall/discharge. No model scoring or active
worker/source change in this pass. Script 112 reproduces the coverage review.

## 2026-10-20 token-mask recovery — current

OlmoEarth/Galileo errors were reproduced and traced to pixel masks violating
native token-block assumptions. [Diagnosis and recovery record](limburg-eo-token-mask-recovery-2026-10-20.md).
Script 111 runs a separate serial MPS recovery (OlmoEarth then Galileo) using
script 110. Check `logs/eo-token-recovery/progress.json` as well as the original
queue. Presto continues unchanged. Old Galileo worker was terminated; outputs
remain. Corrected aggregates are separate and not yet comparison inputs.
Do not edit fingerprinted source files during extraction. Both corrected GPU
smokes passed; the full repaired census is in progress, not complete.

## 2026-10-15 compact EO download — current

Brian approved the compact path. [Current acquisition record](limburg-compact-eo-acquisition-2026-10-15.md).
Script 96 is running with a 70 GB image ceiling / 100 GB new-work budget;
script 95's full-archive worker stays paused. Check compact progress/log before
starting any worker. All 468 events are mapped; usable satellite coverage and
model compatibility are not assumed. No new empirical result or model ranking.


## 2026-10-15 shared satellite acquisition

**PAUSED at Brian's storage concern.** The background worker was suspended
with SIGSTOP; do not resume or launch another full-archive worker. About
614 MiB is held, including inventories and imagery. Revise storage scope first.
The downloading status below records the earlier launch.

Brian chose acquisition before model-compatibility screening. The full dated
Sentinel-1, Sentinel-2 SR/TOA and Landsat optical archive is downloading in a
background worker; see [acquisition record](limburg-satellite-acquisition-2026-10-15.md).
Check the local progress/log before starting another worker. This is not a
completed archive or an empirical model comparison.


## Saved Idea 1 and dynamic foundation-model review — 2026-10-15

Brian requested saving the past-only event-divergence prediction extension as
[Idea 1](limburg-ideas-2026-10-15.md). It is proposed, not implemented. Its
numbering is distinct from the archived October 4 ideas. The [current model
shortlist](reviews/limburg-dynamic-foundation-model-shortlist-2026-10-15.md)
reviews dated EO, weather and hydrological representations. OlmoEarth Tiny,
Galileo and AnySat are plausible antecedent-state candidates, not validated
hourly wetness estimators. No weights/images were downloaded during that
review; the subsequently authorised imagery acquisition is recorded above.
No new model arm was added.

## Storm-response explanation — 2026-10-15

Brian authorized all three paths in the event-insight review. Scripts 92–94
execute the [storm-response census](limburg-storm-response-results-2026-10-15.md):
468 rainfall episodes, 3,744 eight-gauge rows, 3,491 exact numeric windows,
retaining nonresponses and uncertainties. The 24h sensitivity has 461 episodes.
Both independent audits pass; all 180 chapter tests pass. Outputs remain ignored.

Actual cases exposed regional-clock/local-rainfall phase mismatches. The
strengthened forcing comparator includes early and response-window rain;
the initial episode-only arm and development artifacts remain. This
outcome-informed refinement improves matching. TTM improves on raw history but
remains worse than forcing-only matching. Peer-state additions are generally
unhelpful after rainfall/local controls. Recovery-pulse evidence is segmentation-
sensitive and does not establish a mechanism. Do not oversell the negative
early-rise coefficient: its outcome shares landmark Q with that predictor.

Use the all-case curve browser and illustrative pairs for Brian's interpretation.
No new data request, RAG, neural training, scenario model, inundation label,
dissertation prose or independent human verdict. Earlier results remain intact.
Next work is assessing the event diagnoses and contribution, not automatically
adding another model family.

## Analogue distributions — 2026-10-15

The [24h distributional analysis](limburg-analogue-distribution-results-2026-10-15.md)
is implemented and executed on the saved script-84 pooled donor sets. Primary
available populations remain 845 discharge-history, 764 rainfall-matched and
365 context queries. All 1,062 held events, exclusions and short/no archives
remain visible. Scripts 90/91 add empirical CRPS and pointwise range diagnostics
with the existing five/ten donors and geographic controls.

Five-donor TTM has no clear distributional advantage over raw/state or the
generic archive. Ten-donor retrieval improves several archive comparisons;
its AI-specific increment remains modest and uncertain. Conventional rain/Q
is strong. Annual AlphaEarth has no clear incremental all-river advantage,
and worsens ten-donor cross-river CRPS versus temporal/state under group and
year intervals. Coverage is lead-, cohort- and donor-count-dependent, not
calibrated operational confidence. Full-era p99 and inherited 72h eligibility
remain retrospective. No training, new dataset, changed trajectory mapping,
future-rain input or human verdict. Brian writes dissertation text.

The independent audit verifies every score and all 3,840 intervals (maximum
discrepancy 1.46e-13). All 39 existing scientific data files reproduce byte for
byte. The chapter suite passes 173 tests; lint/format checks pass. Large local
outputs remain ignored; code, tests, internal results and receipts describe
the analysis without publishing source records.

## Event-definition robustness — 2026-10-14

[Both requested sensitivity analyses](limburg-event-definition-results-2026-10-14.md)
are complete: p95/72h and p99/120h against the held p99/72h baseline, with
fixed p99 state/response scaling and all available candidate cases. The small
TTM/state shape increment over raw/state remains favorable in direction in both
countries; Dutch five-day group uncertainty includes zero. Conventional rain/Q
beats TTM/state shape on the broader matched p95 cohorts. AlphaEarth timing
benefits vary with population, country and control, so no universal geographic
improvement is established. Generic archive duration/mean-trajectory limits
remain; this is case retrieval rather than demonstrated warning prediction.

Retain p99/72h as the main definition, with alternatives and common-onset/mapped
episode evidence visible. Earlier p95 assessment starts are not operational lead
time. Scripts 88/89 preserve prior results, replay the baseline and independently
audit all source catalogues and numerical results; 160 tests pass. No new model,
training, data request, dissertation prose or human verdict. The remaining work
is synthesis and Brian's case review/writing, not another required model run.


## Warning-threshold progression — 2026-10-14

The user-authorized [full analysis](limburg-warning-threshold-results-2026-10-14.md) adds a census of
all native Dutch threshold records and every held p99 event, plus an H1-started
analogue application. It preserves the existing research question, frozen
representations and earlier numerical runs. Current H1/H2/H3 threshold names
are provider categories, not verified inundation or historical warning labels.
German events remain in the broader analogue analysis; no equivalent German
thresholds are invented. Internal design, missing-history sensitivity and
reproduction details are in `limburg-warning-threshold-analysis-2026-10-14.md`.
Brian retains all dissertation prose and independent human-review fields.


## Cross-border completion — 2026-10-14

[The completed country readout](limburg-cross-border-completion-2026-10-14.md)
now tests pooled/domestic/foreign archives, derives German rainfall from held
radar crops and extends strengthened TTM/state geographic controls to German
catchments. Main pooled populations: Q-only 610 NL / 235 DE, rain-matched
554 NL / 210 DE, context 294 NL / 71 DE. Earlier stage statements about
unavailable German rainfall or an unexecuted geographic extension are historical.

Pooling improves German donor peak-time similarity but worsens peak magnitude;
Dutch primary archive effects are small/uncertain. TTM's main shape increment
over matched raw/state appears in both countries, with quality uncertainty
for the Dutch group interval. The new German conventional rain/Q benchmark
has lower main peak error than TTM; quality makes that difference uncertain.
Dutch AlphaEarth timing benefit is not clearly established at the German sites.
All quality/count sensitivities, provider flags and coverage losses are retained.
No national causal comparison, live forecast claim, training or new data request.

Scripts 84/85 and the evidence index document execution and numerical audit.
Independent human fields remain unchanged; Brian writes dissertation prose.

## Current readout — 2026-10-14

Start with [the evidence index](limburg-analogue-evidence-index-2026-10-14.md).
Main results are scripts 81–83; scripts 75–78 retain useful matched benchmarks,
ablations and sensitivity evidence. Original Steps 3–6 and the first census
are development history, not equally current headline results. Mean pooling
was not found invalid. Do not discard unfavorable comparisons or claim the
later outcome-informed refinements are confirmatory. The stage-by-stage
ledger below is retained for provenance, including dated test counts.

Updated 2026-10-14 after the detailed AlphaEarth review.
Canonical design: `limburg-historical-analogue-active-design-2026-10-13.md`.
Execution/results: `limburg-analogue-steps-3-5-2026-10-13.md`.
Uncertainty/review: `limburg-analogue-step6-2026-10-13.md`.
Census: `limburg-analogue-census-2026-10-13.md`.
Latest checks: `limburg-representation-strengthening-2026-10-13.md`.
Latest application/results: `limburg-cross-river-checks-2026-10-13.md`.
Consistency/next-pass definitions: `limburg-consistency-audit-2026-10-13.md`.
Current preparation: `limburg-event-interpretation-readiness-2026-10-13.md`.
Latest execution: `limburg-expanded-event-pass-2026-10-13.md`.
Latest interpretation: `limburg-analogue-information-review-2026-10-14.md`.
Latest spatial review: `limburg-alphaearth-detailed-review-2026-10-14.md`.

## Active question

> Can basin-aware AI find useful past high-water events across Limburg's Dutch
> and German tributaries, and identify when the evidence is too uncertain to use?

One retrospective representation comparison: conventional rain/Q signatures,
raw 512-hour Q shape, frozen TTM-R2, and a bounded prior-year AlphaEarth
increment. River identity and measurement provenance determine applicability.
No RAG-arm experiment, model training or operational forecast claim.

## Executed stages, original settings followed by extensions

- Dutch inventory: 724 events; 570 complete common inputs, 558 complete
  responses. R0/R1/R2 share 534 queries from 186 storms. Peak-ratio MAE:
  R0 0.6423, raw Q 0.7492, TTM 0.7489, historical median 0.6424.
- Existing measurement-concern sensitivity: 497 paired queries; R0 0.5555,
  raw Q 0.6282, TTM 0.6352. No temporal learned-representation advantage yet.
- AlphaEarth delivery and prior-year join are validated. The 2018+ comparison
  has 304 complete inputs, 296 outcomes, six catchments/45 catchment-years;
  276 queries from 99 storms. Fixed TTM 0.6955, +area 0.6946, +AlphaEarth
  0.6641, historical median 0.6103. Context increment is descriptive and
  still trails the median; event rows are not independent catchment evidence.
- German Herzogenrath 1/Randerath delivered stage/Q converted by script 72:
  338 episodes, 336 complete known-onset Q histories, 237 exact-Q scoring
  responses. All 98 provisional episodes remain in the inventory, outside
  exact-Q scoring. Provider literal curves/domains, fixed UTC+1, complete
  trailing-hour means and unflagged redundant-local-sensor continuity remain
  explicit. Current datum does not guarantee historical datum stability.
- Common Q-only NL/DE run: 774 paired queries/236 storms, raw Q 0.6751,
  TTM 0.6969, historical median 0.5874. Country/watercourse scores saved
  separately. Regional storms are reclustered over the whole inventory;
  German Wurm and Dutch Worm form one physical river group. German
  rainfall/weather are unavailable in this pass, so no German R0/R3 claim.
- Scripts 70–72 save tidy paired results, representations, selected donors,
  quality flags and input/code hashes under ignored `results/` directories.
  Raw provider files remain local. Pinned inference runtime is installed in
  ignored `.venv-foundation`; use Python 3.11, not the shell's Python 3.9.
- The earlier source-card/RAG pilot is optional evidence QA/history only.
- Step 6: 9,999 paired query-storm resamples, year-block sensitivity, and
  six physical-river removals per cohort/sensitivity. TTM-minus-raw Dutch
  difference -0.0003, 95% interval [-0.0582, 0.0583]; pooled difference
  +0.0218 [-0.0250, 0.0679]. No temporal representation advantage established.
- AlphaEarth-minus-TTM difference -0.0315 [-0.0836, 0.0204]. Main point
  improvements survive all six river removals, but same-gauge donor share
  rises from 27.1% to 83.6%. Catchment identity is not response suitability.
- Every selected pair was audited for provenance; fourteen illustrative
  cards were inspected with AI assistance. Human verdicts remain blank.
  Conditional sampling intervals do not cover donor/measurement uncertainty.
- Validation: 102 tests passed. The earlier 54 Step 3–5 outputs and all ten
  Step 6 scientific/review CSV tables reproduced exactly in separate runs.
- User-authorized exploratory extension: script 74 reviews every saved
  selected slot (38,540; 14,318 distinct query–donor pairs), all 774 distinct
  queries, and the full eligible reference pools without sampling. All 1,062
  held episodes remain in a coverage table. The complete main-run atlas has
  133 chronological pages, indexed by gauge/date in a local HTML document.
- Full-response shape differs from mean-peak prediction: TTM improves average
  peak-scaled shape mismatch by 2.7% Dutch / 3.4% pooled versus raw history,
  with favorable conditional storm/year intervals and mean directions on
  every river. AlphaEarth improves shape by 6.4% versus TTM and 2.9% versus
  the area control. These are exploratory, modest increments.
- Timing/duration do not consistently improve; Dutch TTM timing is worse.
  Conventional rain/Q remains better on Dutch shape and level. Census
  diagnostics distinguish individual donors from averages, rainfall context,
  and response segments that may start in recession or end before high water
  is over. No numerical metric becomes an automatic human relevance verdict.
- Census validation: 108 tests passed; ten scientific CSV tables reproduced
  exactly. All 55 input/code hashes and every atlas/query index entry checked.
- Scripts 75–77 now execute exploratory, fixed pooling/state and context
  controls. Ordered TTM preserves all eight patch states. A matched observed
  state block is supplied equally to raw/mean/ordered controls using only
  prior-pool scaling. No training, architecture change or weight sweep.
- Dutch ordered TTM + state: peak MAE 0.6389, shape RMSE 0.2008; rain/Q
  benchmark 0.6423/0.1997. Point proximity is not an equivalence result.
  Against matched raw + state, ordered TTM adds a shape increment -0.0064
  Dutch / -0.0057 pooled, with favorable storm/year intervals and quality
  sensitivity. Pooling alone improves timing; state accounts for much of
  the peak gain in both raw and learned representations.
- AlphaEarth's common-frame rain/Q benchmark now runs on identical 276-query
  pools. Gauge identity nearly matches its shape gain; the residual difference
  and annual-versus-static difference remain uncertain. Do not claim that
  the six-site result uniquely establishes learned hydrological attributes.
- Projection check complete: explicit 10-m EPSG:3035 table downloaded and
  compared with the original angular-grid export. Direction changes <0.000314;
  no main or quality donor set changes. Original CSV preserved.
- Latest validation: 112 tests passed; all 51 scientific CSV outputs reproduced
  exactly, 56 input/code hashes checked, 588 finite interval rows, and all donor
  sets verified as five distinct eligible prior storms. Repo lint/format passed.

## Latest application and interpretation

Independent consistency audit: every saved donor-slot response metric and
score-set aggregate agrees with direct event-window calculations; all actual
candidate pools, IDs and UTC offsets match. Replay now binds prepared data,
vectors and weights to input fingerprints before reading/rewriting results;
code updates remain allowed and recorded. Weather completeness is no longer
an eligibility condition for methods that do not use weather; current counts
are unchanged because all held Dutch weather windows are complete.

Before the event-level pass, distinguish what analogues add beyond the query's
own history. R0 is itself an analogue method, not a history-only reference.
The audit inventory identifies 58 extra usable Q histories, 56 with complete
responses, outside the shared rain/Q cohort. Script 80 has now extracted their
frozen mean/ordered vectors. The broader Q-only inputs total 964 histories
and 851 scorable responses; expanded retrieval is now executed by script 81. Keep the matched
rain/Q comparison separate. No additional data request or training needed. Metrics describe
72h response segments; donor timing is not a predicted peak-time error.

The preparation now gives every old scored set explicit cutoff-persistence
and group-balanced median references. Persistence is a strong magnitude
reference and a weak full-curve reference; no timing estimate is invented for
its flat curve. All scorable events appear in archive-availability tables,
including no/short archives. Review fields remain blank and editable. All
original vectors, state blocks, scores and result hashes are preserved;
twelve new scientific files reproduce exactly. This is preparation, not a
completed event-understanding analysis or an independent human validation.

Script 78 has executed the authorized cross-physical-river donor scenario,
complete disagreement census, fixed k=3/5/10 comparison, spread/error audit,
and equal-block conventional/TTM fusion with a matched raw fusion control.
Outputs: `results/basin_ai_cross_river_checks/`. Computational counts are
87,987 repeated query/configuration sets and 527,922 selected slots, not
independent event sample sizes. Main other-river queries: Dutch 530,
pooled 757, context 264. Original settings remain preserved.

Cross-river TTM + state improves shape over matched raw + state by 2.4%
Dutch / 1.8% pooled, supported by storm/year and quality sensitivity; it
does not clearly beat conventional rain/Q overall. AlphaEarth improves
donor peak timing versus mean-TTM on the context sample, but shape and
magnitude increments remain uncertain and conventional remains strong.
Ten donors often improve mean-response magnitude while exemplar shape
matching can worsen. Donor spread modestly tracks error, with river-specific
exceptions; this is an uncertainty diagnostic, not calibrated warning skill.

Fusion improves Dutch cross-river donor timing by approximately one hour
relative to conventional, but that advantage reverses with the smaller
context archive. The common-query archive audit exposes this limitation.
Report both archives and all fixed-k results; no automatic winner selected.
Twelve outcome-selected response cards have AI-assisted visual review;
companion input-history plots are available. No independent human labels.

Read the latest checks note before interpreting the original model scores.
All 102,645 new selected slots / 20,529 sets have census diagnostics; all
seven outcomes have paired intervals and river summaries. Sixteen original
control configurations replay their previous predictions. The new tables and
comparison figures are under `results/basin_ai_representation_checks/`.

The census corrects the earlier narrow relevance assessment. Open
`results/basin_ai_analogue_census/index.html` for all main-run actual analogue
sets; browser Find locates a date or gauge. Detailed tables also cover every
quality-sensitivity selection. The fourteen older case cards remain historical
illustrations, not the basis of the census. Brian writes the interpretation;
independent human validation has not been claimed or made a new requirement.
That atlas depicts the original settings; the latest donor identities are in
the new selected-pair tables.

Discuss the fixed mean-of-five aggregation versus a median benchmark under
MAE, the distinction between peak error and full-response relevance, and the
limited independent catchment support. No change of aggregator or model has
been made in response to these results.

The cross-river scenario retains observed query histories; it is not an
ungauged-flow prediction test. Its interpretation can now use actual donor
histories, outcomes, uncertainty and source concerns without extra data or
training. Earlier atlases remain illustrations of their original settings.

Preserve null/mixed results alongside the exploratory shape evidence. The
expanded relevance assessment was explicitly requested by Brian; earlier
peak-only conclusions must not be generalized to every meaning of usefulness.
Keep the existing retrievals and report all diagnostics, rather than choosing
a favorable metric or tuning weights after the census.
The rating-era p99 labels/scaling remain retrospective; neither these scores
nor a relevant analogue establish live warning skill or operator benefit.

## Expanded event-level execution

Script 81 scores 845 pooled / 610 Dutch Q-only queries with available earlier
completed groups; six pooled/four Dutch scorable queries have no eligible
archive and remain explicit. Short archives use available groups rather than
become a blanket exclusion. 33,888 score sets / 166,410 selected slots and
416 paired interval rows are independently verified. Full tests: 126 pass.

Five-donor pooled all-river TTM + state shape improves about 2.2% versus raw
+ state; cross-river about 1.5%. All-river final-24h level error also improves
modestly, with favorable group/year/quality checks. Peak and duration do not
show a reliable TTM advantage. Dutch cross-river shape is less certain in the
broader census than the narrower comparison. Ten-donor peak averaging improves
both learned and raw arms; no universal AI winner. Current cutoff discharge
remains a strong magnitude reference; flat persistence is weak for recession.

All-event browser and twelve explicitly outcome-selected benefit/failure
illustrations distinguish complete cutoff histories from observed verification
responses. Four illustrations received AI-assisted visual inspection; no human
verdicts have been entered. Existing rain/Q and AlphaEarth populations/results
remain preserved and separately labeled. Read `limburg-expanded-event-pass-2026-10-13.md`
for exact results, limitations and next interpretation work. Raw records stay
local; no additional model/data request or dissertation prose.

## Information and policy interpretation pass

Script 82 checks fixed selected responses against the generic group-balanced
eligible archive, with no reranking or training. For five-donor pooled main,
TTM selects individual shapes about 14.3% closer all-river / 13.6% closer
cross-river than the archive in general; raw + state already accounts for
most of this gain. Generic averaging has lower duration error and often lower
mean-curve error. TTM's modest unique shape increment survives, and all-river
late-level information improves; no overall continuation-prediction winner.

AI-assisted interpretation covers 24 outcome-independently selected sentinel
cases and the 12 earlier outcome-selected illustrations (35 distinct events).
It distinguishes useful elevated-background/recession comparisons, redundant
cutoff facts, false renewed-rise implications, averaging away peak timing,
low-spread failures and source/coverage constraints. No independent human
labels or operator effectiveness claim. Existing human fields are untouched.

The policy inference is an inspectable casebook for analyst training/post-event
review, with individual prior paths, a generic reference, controls and provenance.
Operational decisions and warning benefits remain unevaluated, not a new
chapter prerequisite. See `limburg-analogue-information-review-2026-10-14.md`
and `reviews/limburg-ai-case-notes-2026-10-14.json`. Brian writes chapter prose.

Validation of the information pass: 130 tests; all 3,294 group-balanced
reference curves independently checked; repeated scientific tables identical.
The one-row-per-event evidence census includes all 851 scorable episodes,
including six unavailable archives.

## Detailed AlphaEarth review

Script 83 explicitly reviews AlphaEarth on the existing context population:
304 inputs, 296 responses, 290 available main queries / 271 quality queries.
All controls share candidate pools and five/ten prefixes; short archives remain.
Original mean-TTM controls replay; geographic blocks are also tested alongside
the already-held ordered TTM/state readout with matched area/identity/static
controls. No training, weight search, new checkpoint or data request.

AlphaEarth changes about three of five donors and increases same-gauge routing.
With the stronger temporal readout, no clear broad shape/peak/duration increment.
Cross-river donor peak-time mismatch improves about 1.14h at five donors;
group/year/quality checks support it, with differing river directions. Fixed
2017 context supplies much of this. At ten donors an additional annual/static
timing increment is about 0.63h in the main run, but is weaker under quality/year
sensitivity. Keep these conditional results; no universal annual-context winner
or forecast lead-time interpretation.

All 26 selected case figures were AI-inspected (18 outcome-independent
selections, eight outcome-selected illustrations), with separately attributed
notes. 118,503 donor slots, 24,684 score sets and 1,120 interval rows independently
verified; 20 old cross-river configurations and static controls replayed.
Human fields remain untouched. Direct matched context conclusions cover six
Dutch catchments. German catchment embeddings are held, explicitly inventoried,
but not tested in this specific paired cohort; that extension needs no assumed
new satellite download. See `limburg-alphaearth-detailed-review-2026-10-14.md`.

AlphaEarth review validation: 133 tests pass; all current output hashes verify;
previous scientific tables and the separate human-review fields are unchanged.
