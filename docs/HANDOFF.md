# Session handoff

Updated 2026-10-13 after implementing and executing Steps 1–5.
Canonical design: `limburg-historical-analogue-active-design-2026-10-13.md`.
Execution/results: `limburg-analogue-steps-3-5-2026-10-13.md`.

## Active question

> Can basin-aware AI find useful past high-water events across Limburg's Dutch
> and German tributaries, and identify when the evidence is too uncertain to use?

One retrospective representation comparison: conventional rain/Q signatures,
raw 512-hour Q shape, frozen TTM-R2, and a bounded prior-year AlphaEarth
increment. River identity and measurement provenance determine applicability.
No RAG-arm experiment, model training or operational forecast claim.

## Executed state

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
- Validation: 97 tests passed; repository lint and changed-file formatting
  passed; all 54 outputs reproduced byte for byte in a separate directory.

## Next work: Step 6

Evaluate paired storm-aware uncertainty, watercourse/catchment dependence and
hydrological relevance of selected analogues. Review provenance failures and
uncertain measurements before making cross-border evidence recommendations.

Preserve null/mixed results. Do not select new models, tune distance weights,
expand outcomes, add fine-tuning or create a dashboard to improve the answer.
The rating-era p99 labels/scaling remain retrospective; neither these scores
nor a relevant analogue establish live warning skill or operator benefit.
