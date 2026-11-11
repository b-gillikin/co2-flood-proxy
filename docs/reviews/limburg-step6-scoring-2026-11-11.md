# External scoring and comparison audit — 11 November 2026

Internal evidence workflow. Brian writes dissertation/article text.

## Completed before external scoring

- Six final source states verify against model/manifest hashes. Both learned
  pipelines completed 2,214 tile jobs and 3,127 reference-tile evaluations each,
  with three seeds: 18,762 maps in total. All maps are accounted for in 46
  Azure archives previously verified by complete download/readback hashes.
- Conventional source-calibrated radar mapping completed 3,127 evaluations.
- The full 1,301-tile support census was reconstructed from checked outputs and
  original targets. The 913 triplets supply the paired reference comparison.
- Overlaps include 28 cross-UTM tile pairs in EMSR861 and 17 in EMSR866.
  Use prediction-blind ownership: smallest absolute listed radar–label timing
  discrepancy, then tile key. Earlier eligible coverage owns pixel centers;
  nearest-neighbor coverage reprojection handles different UTM grids. Holes and
  each support bit remain distinct. No model result enters ownership.

## Fixed scoring conventions

`config/limburg_chapter_evaluation_v1.json` records the conventions before the
first external scores were calculated. This is an internal run record, not
formal preregistration. Delivered P0 is assessed as its own cohort/processing
chain. P1−P0 and interactions use only harmonized imagery on identical known
support. Actual output validity must equal independently checked radar validity.

The primary target remains the released composed label. Additional summaries
use original flood/permanent-water mask composition (unknown retained), the
released validity mask, and a one-pixel class-boundary interior. Timing and
source-footprint flags are descriptive strata of owned coverage. Do not silently
relabel all unmarked land as independently observed dry terrain.

For each activation/method/reference/seed, sum native confusion counts and then
calculate flood IoU. Do not average tile IoUs or make empty-union IoU equal one.
Average training seeds within activation, activations within conservative
episode blocks, then equally weight blocks. Keep all nine activation results,
training-seed variation and pixel-weighted descriptive totals available.

EMSR861 and EMSR864 form one conservative Iberian dependence block; this is
not an assertion that they are exactly one meteorological storm. The other
activation IDs form separate blocks. Their different geographical dates are
recorded in the held catalogue; incomplete storm lineage remains a limitation.
Report 9,999 paired block-bootstrap draws and leave-one-block-out summaries.
With eight blocks, uncertainty remains coarse; millions of pixels do not enlarge
the independent event sample. No universal model-superiority/equivalence claim
follows from a small average contrast.

## Execution and recovery

`241_prepare_chapter_evaluation.py` verifies the census and freezes support.
`243_score_chapter_physical.py` scores the existing conventional outputs.
`245_continue_chapter_evaluation.py` runs two bounded restoration/scoring workers
(`242`), then consolidated paired comparisons (`244`) and the systematic map
atlas (`246`). Each archive is downloaded into a bounded workspace, checked
against its original full SHA256 and membership, scored, and removed from the
local workspace only after durable score and compact-class-map output exists.
Full original probabilities remain in Azure. The 50-GiB reserve remains in force.

The first complete restored archive passed the full path: 84 predictions and
420 score rows, with no external parameter adjustment. Targeted ownership,
known-support, undefined-IoU and paired-bootstrap tests pass. No source weights,
labels, acquisition selection or thresholds were changed after scoring began.

The atlas selects the largest absolute native P1−P0 tile-IoU change within each
assessable activation using all-seed means. It deliberately examines informative
differences and is not a representative accuracy sample. Figures show seed 42,
while numerical summaries retain all three seeds. Local July 2021 cases have
their own outstanding assessability/provenance work; the external queue does
not declare those complete. Production email alerts remain disabled.

## Local receiving cases and final checks

The local inventory contains 167 held radar scene/grid records across Venlo,
Eschweiler and Wassenberg. All have a compatible held P0. A label-blind catalogue
search finds 35 newer same-platform/orbit/pass references covering the relevant
footprint before 13 July 2021 00:00 UTC; 132 retain P1=P0. This is a conservative
pre-event cutoff, not an assertion of exact onset at every site. P0 is the held
archive baseline from an earlier collection ending before 10 July, not a
documented Dutch/German operational reference policy. These cases cannot show
that agencies actually chose outdated references.

All three dates are exported through the same linear-intensity Earth Engine
chain. The first actual triplet has median intensity ratios of 1.0 in VV/VH
against held P0 and post images converted from dB. This is a checked example,
not assumed cohort-wide equality. Targets retain the existing source-aware
mapped proxy, hydrography/trace exclusions and unknown pixels. Models share
paired known support. Adjacent slices are deduplicated within each AOI/date/orbit
case; different dates are not pooled as independent flood events. The original
six learned source states and physical calibration remain fixed.

The local acquisition controller (`249`) starts the resumable local runner
(`248`) after verified acquisition. This uses the otherwise available MPS worker
alongside the archive scoring workers. Local outputs have their own receipts;
they are not inserted into the independent external cohort.

All 74 relevant frozen encoder/vendor assets match the hashes used to construct
source features. Import and scientific checks cover the pending summary/map
code; the full native-grid check now includes both external 1024px and local
512px grids. A synthetic end-to-end summary recovers the known paired interaction
while retaining all training seeds. Completed-worker/queued-code formatting was
cleaned separately; active worker versions remain intact until completion.
