# Same rivers, different discharge information: Stages 1–2

14 November 2026. Internal research design and execution guide. Brian approved
the three-stage direction and requested setup of the first two stages. These
are research aids; Brian writes the dissertation. No formal preregistration or
new empirical performance result is claimed.

## Research argument

**RQ:** When gauge observations are replaced by global modelled discharge, how
well can we assess developing high water, and can AI improve that assessment?

The practical problem is the information an agency can use when its current
local discharge feed is unavailable but historical observations exist. Evaluate
the information content of a global substitute, conventional assessment, local
calibration and learned corrections. Better monitoring remains a competing
investment; an encoder gain over a weak comparator would not justify deployment.

Stage 1 uses held observed discharge inputs. Stage 2 replaces every discharge
input channel with the corresponding GEOGLOWS retrospective series or explicit
missingness. The outcome remains the next 24 hourly **observed** discharge
values. Rainfall, event clock, target gauges and verification rules are unchanged.
The paired design isolates the input-product change as far as these observations
and model-reach representations permit; it is not a causal study of river flow.

The deployment interpretation is historically gauged/local calibration, not an
ungauged river: historical observed outcomes remain available for training and
for earlier analogue responses. The two sources are not assumed to have a fixed
quality ranking. Measure bias, timing and error rather than calling GEOGLOWS
universally inferior.

## Population and clocks

- Full held 481 regional rainfall episodes, eight tributary response gauges,
  four issue offsets (0, 6, 12, 24 hours): **15,392 opportunities per stage**.
  Availability and outcome validity are recorded; no final event sample is used.
- Ten input channels: the eight tributary gauges plus Sint Pieter and Venlo on
  the Meuse. Those mainstem sites are context, not response targets or generic
  upstream controls for every tributary.
- Gauge/hourly observations use the existing checked UTC hour-end convention.
  GEOGLOWS hourly averages are documented at interval start and shifted +1 hour.
  No nearest-time interpolation or future hour enters a query history.
- Histories end at issue; future 24-hour observations are labels only. All
  transformations, analogue response availability and tuning respect chronology.
- GEOGLOWS retrospective is reanalysis-based and released with a 5–12-day delay.
  This study supplies its past hydrological state under an explicit hypothetical
  information clock. It is **not an as-issued forecast or live-feed replay**.
  Future operational claims require the forecast/reforecast product and its
  actual issue/arrival times. Historical completed EO windows similarly retain
  the existing nominal availability convention, not proof of as-issued delivery.
- The RADOLAN-derived common rainfall clock conditions the evaluated population;
  it does not demonstrate autonomous event detection by GEOGLOWS.

## Reach identity and an important coverage result from setup

The complete RFS V2 VPU 209 stream network and incremental catchment polygons
were acquired. Candidate matches were checked using coordinates, topology,
downstream-end drainage area and overlap with our independently held catchments.
TDX-Hydro USContArea and DSContArea are square metres at the upstream/downstream
segment ends respectively; the two fields must not be interchanged.

Seven tributary reaches and both Meuse context reaches are selected in the
[reach register](../config/limburg_geoglows_reaches_v1.json). Seven selected
tributary catchments cover approximately 97–99% of our corresponding held
catchment polygons, but model outlets and gauge sections are not identical.
Additional downstream area is material at some sites and remains a source of
representativeness error rather than being silently area-scaled away.

**Eys/Eyserbeek has no independent reach in this network.** The nearest segment,
230111456, overlaps only 0.56% of its held catchment and belongs to a different
tributary. Approximately 98.17% of the Eyserbeek polygon lies in the incremental
catchment of Geul reach 230375839, whose outlet drainage is 191.04 km2 versus
28.31 km2 at Eys. Do not substitute that larger river's discharge for Eyserbeek.
Stage 2 channel 0 remains missing in both query and donor histories.

The **primary direct product comparison uses the seven mapped target gauges**.
The complete eight-gauge pipeline census is retained, and Eys is reported as a
separate structural-coverage case. This is a geography-based distinction made
before the new fits, not an outcome-selected exclusion. At Herzogenrath, the
Wurm reach is distinguished from nearby Broicher Bach and the combined reach.

## Methods and comparators

1. **Conventional analogue mean and median:** same-gauge earlier regional storms,
   five donors, existing rainfall/network-history matching. Use a fixed annual
   donor archive and normalization for all arms; historical responses and entire
   storm closure must precede the annual boundary. This differs from older
   rolling-archive headline scores; Stage 1 is recalculated for fair pairing.
2. **Input persistence:** latest hour repeated over 24 hours; missing latest Q
   remains missing. This is a deliberately simple reference, not the only one.
3. **Simple calibration:** training-only monthly empirical quantile mapping of
   GEOGLOWS to valid observed hourly pairs. Use up to 201 knots, annual fallback
   if a month has fewer than 20 pairs, averaged tied knots, and multiplicative
   extrapolation above the training maximum. No past calibration means unknown,
   not an identity mapping. Report both calibrated persistence and calibrated
   analogue matching; the latter retains observed historical donor responses.
   Stage 1 calibration is identity. Save all fitted knots/counts/fallbacks.
4. **Hydrology-only correction:** small multi-output ridge residual correction
   of the conventional trajectory, using permitted discharge/rainfall context.
5. **Raw-EO correction:** the same design with each candidate's matched raw
   satellite descriptors, coverage and context age.
6. **Encoder correction:** corresponding frozen encoder features added to the
   raw-EO correction. Retain the existing validated earlier-year tuning scheme,
   zero correction and zero encoder influence. Report chosen prediction modes;
   a zero-encoder policy improvement is not evidence of encoded information.

Core encoder candidates are **AnySat** (four completed weekly optical contexts,
spatial summaries) and **Presto** (twelve completed monthly pixel-series
contexts). Reuse their completed, hash-verified compact tables and their matched
raw descriptors. Their proposed mechanism is antecedent/landscape context, not
hourly rainfall recovery. Historical support differs: present full-census
pipeline-with-fallback and encoder-supported comparisons separately. Do not rank
models by unmatched cohorts. TTM remains a possible separate temporal
representation comparison; no TTM re-encoding, AlphaEarth sweep, fine-tuning or
new imagery extraction is included in this setup.

## Evaluation and interpretation

Primary loss is site-balanced 24-hour trajectory MAE in mm/h; retain per-site
m3/s results. Average offsets within storm/site before balancing sites. Report
whole-census and evaluation-only high-water strata, supported-EO effects,
documented-flood overlap, verification-clean cases and NL/DE/site diagnostics.
RMSE, +6/+12/+24h errors, peak magnitude and timing are secondary. Undefined
timing remains undefined, and incomplete outcomes are unscored, never dry or
zero error. Rating-domain/provisional-flow qualifications remain in force;
uncertain peaks are not automatically invalid onsets.

Separate hydrology learning, raw satellite information, encoder-specific
increment, net performance versus the strong conventional and simple-calibrated
references, and performance change between information sources. Explicitly
compare encoder increments across stages on four-arm paired support; separate
significance labels do not establish an interaction.

Use the same 999 whole-year bootstrap multiplicities across methods/stages,
assigning each complete regional storm to its initial-landmark year. These are
exploratory, pointwise intervals conditional on fitted procedures and the held
network, not full model-training uncertainty or a random country sample. Both
German targets are on the Wurm; a country contrast is not a national-system
effect. The archive has already informed earlier studies: chronological held-out
years protect fitting but are not a previously unseen confirmatory discovery set.

Review actual analogue selections and helped/harmed events after full scoring.
Null/adverse outcomes remain informative. Stage 3 would replicate a specific
finding or failure condition in Europe; it is not part of this queue.

## Data, resources and execution

Design: [machine-readable plan](../config/limburg_geoglows_stages12_v1.json).
Raw selected series/GIS: `data/raw/limburg_geoglows_stages12_v1/`.
Prepared banks/census and future results: `results/limburg_geoglows_stages12_v1/`.
Earlier outputs stay intact; only this chapter is changed.

The selected series cover 2010–2025 continuously at all nine mapped input sites.
Download/preparation are complete; no new fits have started. See
`results/limburg_geoglows_stages12_v1/readiness.json` and `setup_audit.json` for
the current machine-verified state. Raw GIS/series are about 521 MiB, prepared
tables/banks about 56 MiB, and the isolated dependency overlay about 59 MiB.
Approximately 79 GiB free remains. Preserve the 50-GiB reserve and recheck before
each write phase. No Azure offload or cleanup is necessary for this scope.

The baseline engineering check projected roughly two minutes for both raw-source
baseline passes, excluding calibration overhead. Prior complete correction jobs
took about 1–3 minutes per model/scenario. Allow **1–2 hours machine time** for
the first full comparison/review with debugging and checks; this is not a measured
end-to-end ETA. Two single-threaded CPU workers, no sustained GPU requirement.

```sh
# Already performed during setup; idempotent verification on repetition:
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py inventory
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py mapping-audit
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py download
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py prepare
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py audit
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py readiness

# Full fitting and review are explicit subsequent commands, not started by setup:
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py run
.venv-geoglows/bin/python scripts/260_setup_geoglows_comparison.py review
```

Each completed job has input/code/output hashes. Changed scientific inputs or
code require a versioned experiment rather than overwriting completed results.
Interrupted downloads resume at verified site files; fits resume at completed
stage/model jobs. Failures propagate to the controller and logs, not silent
successful partial completion. No alert emails are activated or sent.

## Literature foundation and contribution

- [Mbuvha et al. (2023)](https://doi.org/10.1017/eds.2023.11): GEOGLOWS plus local
  observations, learned correction and forecasting under missing gauge data is
  direct precedent. This chapter cannot claim that basic workflow is new.
- [GEOGLOWS correction guidance](https://training.geoglows.org/rfs/bias-correction/bias-correction/):
  flow-duration-based correction supplies the simple-calibration comparator.
- [Presto](https://arxiv.org/abs/2304.14065) and
  [AnySat](https://openaccess.thecvf.com/content/CVPR2025/html/Astruc_AnySat_One_Earth_Observation_Model_for_Many_Resolutions_Scales_and_CVPR_2025_paper.html):
  foundations for task-specific frozen representations, not proof of discharge benefit.
- [GEOGLOWS hydrography](https://training.geoglows.org/rfs/datasets/hydrography/) and
  [retrospective conventions](https://training.geoglows.org/rfs/datasets/retrospective/):
  reach/area semantics, temporal support and release limitations.

The proposed contribution is a paired high-water assessment of actual source
substitution and the incremental value/limitations of satellite representations
beyond strong hydrological and calibration controls. It is a testable proposed
contribution, not a verified first-in-literature claim or guaranteed AI advantage.
