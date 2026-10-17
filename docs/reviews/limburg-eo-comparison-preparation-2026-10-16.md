# EO comparison preparation — 16 October 2026

Internal research workflow/readiness note, not dissertation prose or new empirical
findings. Implements the four preparation tasks authorized while Azure acquisition
continues. Brian also authorized expanding acquisition where needed for the science.

## 1. Event/window census and coverage

Script 99 links **all 1,062 high-water gauge events** and, separately, **3,744
gauge/rainfall-episode rows** (468 regional episodes × eight gauges). The existing
scoring flags admit 851 and 3,491 respectively; these flags are inherited, not new
EO exclusions. The two populations have different assessment times and storm IDs
and are never relabelled as one population.

The current map contains 742 unique contexts, 930 calendar windows, 81,702
observation/window links and 144,180 observation/model/context coverage rows.
Every completed window ends by its observation's assessment time. Product
publication latency and pretrained exposure remain separate limitations on any
future prospective claim.

Three explicit readouts reuse the acquired windows:

- **Monthly snapshot:** the most recent completed calendar month, a common
  low-history control requiring no additional acquisition.
- **Monthly sequence:** twelve completed months, oldest first.
- **Recent sequence:** four completed UTC Monday-to-Monday weeks, oldest first.

Twelve months are not a blanket entry requirement. Each readout has its own
coverage and comparisons. Absent frames, pre-mission years, catalogue-empty
windows, cloud-only/pending local files and partial observed areas stay visible.
No nearest-date replacement, fabricated image or random event sample is used.

The local pixel audit verified **2,700 primary tiles**: 626 paired S2 tiles,
881 S1 tiles and 1,193 HLS tiles, with **zero errors**. Actual masks, exact
catchment/pixel intersections and acquisition dates produce observed area and
age measures. Missing files locally do not imply failure of the cloud archive.
The local scan is a dated coverage inventory, not final archive coverage.

## Acquisition expansion

The original request calendar was built around rainfall episodes. The high-water
assessment calendar adds **862 files** to the original 35,442: **36,304 total**.
Held scene catalogues and the original spatial grid suffice to build those jobs.
Every original job remains unchanged. The source ledger, composite code,
normalization and spatial domain are preserved.

The extra compressed volume is estimated from local product-specific median
file sizes at **1,847,360,882 bytes** (~1.85 GB), not a guaranteed final size;
uncompressed pixel payload is ~8.17 GB. The existing 200 GB cap remains adequate
for this extension. Brian permits a higher cap if later evidence justifies it;
200 GB is not a scientific boundary.

The expansion was verified, deployed and the Azure service resumed with 36,304
planned files and no recorded failures. Original ledgers/plans are backed up on
both machines. The expanded ledger and extension provenance are also stored in
the private archive's `_control/` area. Completed downloads were retained.
The dated [extension receipt](limburg-eo-download-extension-2026-10-16.json)
records the original/expanded ledger hashes and the earlier preparation snapshot.

## 2. Temporal inputs and encoder use

Script 100 validates chronological, spatially aligned frames and preserves
per-frame masks/dates. OlmoEarth, Galileo, AnySat, Prithvi and Presto use native
temporal input. CROMA, DOFA, Copernicus-FM, TerraMind's selected single-frame
backbone and the selected multispectral SatMAE use an explicitly labelled,
order-invariant mean of frame embeddings. The latter is not temporal attention.

Each model has a fixed input route. Galileo now uses **32-pixel spatial patches
and an 8-pixel projection patch**: its released Nano config supports patch sizes
1–8 and specifies a 4×4 spatial-token layout for twelve-frame training. This
matches that layout, avoids the oversized full-attention token count of the
initial 64-pixel/4-pixel engineering fixture, and was chosen without outcome
inspection. The earlier single-frame check record remains historical. This
change needs no new imagery or learned weights.

All ten models passed two-real-frame inference, exact repeatability and verified
resume checks. All five native temporal models additionally passed **twelve real
monthly frames**, including time/location handling where supported. The
[machine-readable temporal record](limburg-eo-temporal-checks-2026-10-16.json)
is engineering evidence, not a model ranking.

## 3. Catchment representations

Script 101 uses exact polygon/pixel areas, including boundaries and holes.
Patch weights use the mean observed catchment area across the fixed slots;
per-frame, minimum and common-across-frame areas also remain available. The
full catchment is always the coverage denominator. Padding contributes no area;
duplicate/overlapping support is detected. No arbitrary observed-area cutoff is
introduced. A catchment with no observation in a required frame remains explicitly
incomplete for that fixed readout.

This is an **observed-area-weighted patch-feature proxy**. A patch overlapping a
catchment can also attend to pixels outside it; pooling does not turn the vector
into a pure pixel-level catchment measurement. Native patch footprints differ by
model. These facts, coverage and acquisition age must accompany interpretation.
Engineering aggregation succeeded for all ten models, with zero errors.

## 4. Existing experiment connection

Script 102 defaults to an experiment/coverage plan. Its explicit `--run` reuses
script 65 retrieval, script 84's scoring/validation and existing phase evidence:
completed earlier 72-hour donor outcomes, different storm groups, one donor per
group, all-/other-river scenarios, pooled/domestic/foreign archives, main/quality
sensitivity, and five/ten donors. It preserves full-era p99 as a retrospective
scale. No outcome ranks neighbours or fits the representation.

EO-only and EO plus TTM/state are compared with raw/state and TTM/state.
Catchment area and gauge identity controls test geographic specificity. Rainfall
and AlphaEarth use their own matched subsets rather than excluding earlier or
otherwise usable events from the primary Q-only comparison:

| Held baseline eligibility, before EO availability | Events |
| --- | ---: |
| Q-only with raw/state and TTM/state | 851 |
| Matched conventional rainfall/discharge | 770 |
| Matched preceding-year AlphaEarth | 373 |

Each model retains its available-event population. An explicitly separate
all-ten intersection uses exactly the same eligible queries and donor pool for
all arms; a missing model does not silently disappear from that intersection.
The all-ten population is an additional comparison, not a gate on pairwise work.
Country, river, actual donor count and measurement-quality distinctions persist.
Paired differences reuse equal-count pairing and intact storm/year bootstrap.

The complete adapter was exercised with explicitly labelled synthetic engineering
vectors and real held event/scoring records. Those outputs live under `logs/`,
not scientific results, and support no performance finding. Regression checks
verify exact five/ten-donor means/counts and no duplicate phase fields. Production
execution rejects engineering representations and changed output hashes.

The rainfall-episode rows are linked for reuse by the existing storm-response
analyses; script 102's implemented evaluator is the high-water analogue spine.
No new peer-regression or warning-threshold model is claimed in this pass.

## Run and outputs

Run from the chapter directory. Preparation/aggregation use the isolated TerraMind
runtime because it has a working modern geospatial stack; encoder extraction uses
each model's runtime in `src/eo_inputs.py`.

```sh
.venvs-eo/terramind/bin/python scripts/99_prepare_limburg_eo_comparison.py --scan-local
.venvs-eo/legacy/bin/python environments/eo-screen/check_temporal_inputs.py --run
# Explicit census extraction; this can be lengthy. No bulk extraction started here.
.venvs-eo/galileo/bin/python scripts/100_extract_limburg_eo_sequences.py --model galileo --run
.venvs-eo/terramind/bin/python scripts/101_aggregate_limburg_eo_catchments.py
.venvs-eo/terramind/bin/python scripts/102_connect_limburg_eo_experiments.py
# After coverage review, the same final command with --run executes comparisons.
```

Preparation files: `results/eo_comparison_preparation/`. Patch sequences:
`data/processed/limburg_eo_sequences/`. Aggregates:
`results/eo_catchment_representations/{engineering,census}/`. Experiment plan:
`results/eo_analogue_comparison/`. Data, private provider records and model outputs
stay outside Git. Raw sources and earlier scientific results are unchanged.
The runner processes locally staged inputs; it does not mirror the full Azure
archive onto the laptop or start new cloud inference. Chunked extraction/storage
can be arranged without changing the analytical design.

The [preparation check record](limburg-eo-preparation-checks-2026-10-16.json) records 35 passing pytest checks, two additional projection checks in the working geospatial runtime, exact expansion replay, all temporal checks and the isolated end-to-end scoring fixture.

Validation covers exact calendar/age bounds, mask/zero/padding treatment,
polygon area conservation, overlap detection, exact context joins, missing-model
intersections, chronological/storm/country/river exclusions, outcome-blind donor
ranking, exact donor-count scoring and real temporal repeatability/resume.
The foundation environment's PROJ database is incomplete; the two projection
checks were rerun successfully in the isolated geospatial runtime. No global
environment change was made. Final scientific comparisons remain unrun.

## Provider requests

No further NL/DE request is required for this comparison. Optional later work:
LANUK's official gauge-specific reporting-level stage thresholds, effective dates
and documented gauge-zero changes, if readily available. That would support
German threshold-progression interpretation, not prove inundation onset. Do not
re-request the historical Dutch thresholds or datum/sensor histories René said
he could not provide. Held measurement uncertainty remains explicit.

## Full archive follow-up — 17 October 2026

The [completed full-archive audit](limburg-eo-full-coverage-audit-2026-10-17.md)
supersedes the partial local pixel counts above for current coverage. All planned
files are local; 27,766 primary tiles passed the scan with zero errors. Context
availability and observed area remain distinct; no model-performance result or
new exclusion was introduced.
