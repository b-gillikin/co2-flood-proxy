# Limburg analogue study: Steps 3–5 execution

Internal results and implementation aid, 2026-10-13. Brian writes dissertation
text. This follows the active analogue design; it adds no RAG experiment,
fine-tuning, forecast target, data request or empirical chapter.

Subsequent uncertainty and relevance checks are now complete as documented in
`limburg-analogue-step6-2026-10-13.md`. The descriptive results below preserve
the state at completion of Steps 3–5.

## What ran

| Step | Runner | Local outputs |
| --- | --- | --- |
| 3 | `scripts/70_ttm_analogue_comparison.py` | `results/basin_ai_ttm/` |
| 4 | `scripts/71_alphaearth_analogue_increment.py` | `results/basin_ai_alphaearth_increment/` |
| 5 | `scripts/72_german_wurm_analogue_extension.py` | `results/basin_ai_german_extension/` |

Each runner saves predictions, selected prior analogues, paired comparisons,
sample counts and a hash-based manifest. The data and detailed results remain
local under the repository's existing ignore rules. No raw provider files are
published. The interpretation below is descriptive: uncertainty, dependence,
leave-one-watercourse-out behavior and hydrological relevance remain Step 6.

## Frozen temporal representation

R2 uses the pinned IBM TTM-R2 `512-96-r2` snapshot, 805,280 loaded parameters,
zero trainable parameters, CPU evaluation mode and seed 20261013. All weights
load without missing, unexpected or mismatched keys. The runner verifies the
weight/configuration receipts, pinned code archive and the imported model and
configuration source against that archive.

It takes exactly the same 570 standardized histories saved by R1. Only the
backbone is called: last hidden state `[1 channel, 8 patches, 192 dimensions]`,
patch mean, then L2 normalization. The checkpoint's standard scaler is retained;
no decoder, forecast head, future values, zero padding or model training is used.

The outcome is the maximum discharge/p99 ratio in hours 1–72. Lower mean
absolute error (MAE) is better. Both p99 labels and normalization remain
retrospective; these errors are not operational forecast scores.

| Dutch comparison | Queries / storms | R0 signatures | R1 raw Q | R2 TTM | Historical median |
| --- | ---: | ---: | ---: | ---: | ---: |
| Main | 534 / 186 | 0.6423 | 0.7492 | 0.7489 | 0.6424 |
| Measurement-concern sensitivity | 497 / 182 | 0.5555 | 0.6282 | 0.6352 | 0.5444 |

R2 does not show a useful average error improvement over raw Q here, and neither
temporal representation beats the practical rain/discharge comparator. R0 has
rainfall, whereas R1/R2 have identical Q-only inputs; this is not a causal test
of pretraining or of rainfall's contribution. No new model is selected from
these outcomes.

## Bounded geospatial increment

Fix TTM as the event representation, as recorded before the context comparison.
Use only the common prior-year AlphaEarth subset: 304 complete inputs, 296
complete outcomes, six catchments and 45 represented catchment-year pairs.
The resulting eligible query sample is smaller because donors must come from
that same subset and satisfy the unchanged 20-candidate/five-distinct-storm rule.

Compare TTM alone, TTM plus log catchment area, and TTM plus the L2-normalized
64-dimensional catchment-year mean. Every distance block is divided by the
RMS pair distance among its unique prior candidate vectors. For `n` unique
vectors this scale is `sqrt(2*n/(n-1) * sum(population variances))`. Constant
prior blocks use unit scale. Combine scaled blocks by equal-weight RMS; no
outcomes or query vectors determine the scales and no weight search is run.
Selected-neighbor files retain component distances and prior scales.

| Common 2018+ comparison | Queries / storms | TTM | TTM + area | TTM + AlphaEarth | Historical median |
| --- | ---: | ---: | ---: | ---: | ---: |
| Main | 276 / 99 | 0.6955 | 0.6946 | 0.6641 | 0.6103 |
| Measurement-concern sensitivity | 257 / 96 | 0.6220 | 0.6255 | 0.6022 | 0.5448 |

AlphaEarth lowers average error relative to TTM and the area control in both
runs. It still does not beat the historical median. This is a modest descriptive
increment, not established usefulness or independent evidence from 276
catchments. Its support is six catchments and their repeated years. Comparing
these numbers with the full Dutch table is invalid because the query/donor
cohorts differ.

## German Wurm extension

Use the delivered Herzogenrath 1 and Randerath stage/Q exports through 2025,
not the older archive ending in 2021. Source headers, units, identifiers and
quarter-hour grids are checked. Fixed UTC+1 applies in winter and summer.
Each hour-ending mean requires all four trailing quarter-hours; no gaps are
filled by the runner.

`config/lanuk_rating_periods.csv` transcribes literal validity periods and
stage/Q domains from the provider's two curve-validity PDFs, with source
hashes. Repeated verified curve versions share a threshold group, while
literal period boundaries still censor onset transitions. The provisional
group starts at source-clock 2021-07-01, the first affected rating period;
this is a conservative scoring boundary, not an asserted flood onset.

| German station / status | Inventory episodes | Complete known-onset Q histories | Exact-Q score eligible |
| --- | ---: | ---: | ---: |
| Herzogenrath 1, pre-provisional | 143 | 142 | 141 |
| Herzogenrath 1, provisional | 57 | 57 | 0 |
| Randerath, pre-provisional | 97 | 96 | 96 |
| Randerath, provisional | 41 | 41 | 0 |
| Total | 338 | 336 | 237 |

Preserve all 338 event objects, stage windows, rating identities and quality
flags. Exact-Q scoring additionally requires complete stage/Q at onset and
through the 72-hour response, one literal period and values inside both stage
and Q curve domains. Post-boundary German high-water Q stays outside that
exact score because the provider reports provisional high-flow ratings.
Measured stage is retained for later evidence review. Current gauge datum is
not assumed to guarantee historical datum continuity. Redundant local sensor
substitution is documented but not fabricated into row-level flags.

German rainfall/weather have not been aligned in this pass. Run the supported
common Q-only comparison R1 versus R2; do not present German R0 or AlphaEarth
results. Keep the fixed Dutch input cohort, and recompute 72-hour regional
storm linkage over the full NL/DE inventory before donor selection. Two German
Wurm gauges and Dutch Worm are one physical river group, not three tributaries.

| Pooled temporal comparison | Queries / storms | R1 | R2 | Historical median |
| --- | ---: | ---: | ---: | ---: |
| Main | 774 / 236 | 0.6751 | 0.6969 | 0.5874 |
| Measurement-concern sensitivity | 734 / 232 | 0.5826 | 0.6123 | 0.5195 |

Among the 229 scored German queries, main R1/R2 MAE is 0.5768/0.5929, versus
0.4577 for the historical median. On the same German queries after removing
flagged Dutch donors, it is 0.5395/0.5739 versus 0.4562. Country/watercourse
tables are saved separately. R2 selects 1,683 cross-country donor slots among
3,870 main slots, which demonstrates executed cross-border retrieval, not its
added value. The pooled result cannot be compared directly with the Dutch-only
result: candidate pools and storm identities change.

## Reproduce

The held model and source archives are sufficient. No further downloads are
needed. `environment-foundation.yml` pins the inference dependencies; use
Python 3.11, not the older Python 3.9 shell environment. After creating and
activating that environment, unpack and install the held source:

```bash
mkdir -p data/raw/foundation_assets/code/unpacked
tar -xzf data/raw/foundation_assets/code/granite-tsfm-fe7a356.tar.gz \
  -C data/raw/foundation_assets/code/unpacked
SETUPTOOLS_SCM_PRETEND_VERSION_FOR_GRANITE_TSFM=0.0.0+fe7a356 \
  python -m pip install --no-deps --no-build-isolation -e \
  data/raw/foundation_assets/code/unpacked/granite-tsfm-fe7a35697723e2a2f5246ae979474bfc554e26c0

python scripts/70_ttm_analogue_comparison.py
python scripts/71_alphaearth_analogue_increment.py
python scripts/72_german_wurm_analogue_extension.py
python -m pytest -q
ruff check .
```

Editable installation is required because the pinned upstream wheel omits
its model subpackages; the runner verifies the actual imported source.
The local execution used `.venv-foundation` over the existing scientific
Conda environment. For tests that use PROJ in such an overlay, set `PROJ_DATA`
to the base Conda environment's `share/proj` directory; a standalone Conda
environment finds its own directory normally.

Validation: all 97 scientific tests passed, repository Ruff lint passed, and
all five changed/new Python files passed formatting checks. Fresh runs into
a separate temporary directory reproduced all 54 output files byte for byte,
including representations, event objects, paired scores and manifests. The
original R1 predictions remain identical. Every selected donor has a finished
response before query onset, differs in storm identity, and occupies one of
five distinct prior storms. No provisional German response entered an exact-Q
query or donor score. The local check receipt is
`results/basin_ai_german_extension/reproduction.json`.

The checks follow `dissertation-research-and-code-guidelines.md`: direct
dataframe scripts, source-format ingest from held deliveries, fixed comparisons,
explicit measurement limits, no outcome-driven model/weight search, and tidy
hash-traceable results. Inference beyond descriptive error comparisons remains
pending. Execution preceded the implementation commit; manifests' source hashes
identify the evaluated working-tree code, rather than relying on Git HEAD alone.

## Next work

Step 6 remains: storm-aware paired uncertainty, watercourse/catchment dependence
checks, and review of retrieved analogues' hydrological relevance and provenance.
These runs establish that the comparison is executable. They do not yet establish
that learned representations offer useful high-water analogues beyond simple
benchmarks. Retain null and mixed results; no model expansion is implied.
