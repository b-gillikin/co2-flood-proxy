# Chapter Direction

Status date: 2026-08-07

Supersedes the research question and claim structure in
`docs/chapter-readiness-plan.md` and `chapter/chapter-draft.md`. It also
supersedes the early-warning framing this document carried earlier the same day.

## The question

> If one tributary catchment is instrumented deeply, how far does that knowledge
> transfer to others, and what governs the decay?

This is regionalisation, or donor-catchment transfer: characterise one gauged
catchment thoroughly, then transfer to ungauged ones weighted by similarity. It
sits in the Prediction in Ungauged Basins literature the chapter already cites
(`Kratzert2019PUB`, `Kratzert2024Single`, `Gauch2021`, `Nearing2024`,
`Frame2021NWMLSTM`, `Klotz2022`).

The chapter is quantitative and tributary-scale. It is **not** an early-warning
system: the Dutch operational system is advanced and well resourced, and
competing with it was never the useful contribution.

## Why this framing

It completes the supervisor's progression as a genuine intellectual arc rather
than an asserted one, because each step is the same question at a wider scope:

| | Question | Scope of substitution |
| --- | --- | --- |
| Viefhues (2022) | Does a deeply instrumented site carry hydrological signal? | — |
| Eryilmaz (2025) | Can public weather substitute for that local instrumentation? | across data source |
| This chapter | Can knowledge from one instrumented catchment substitute for instrumentation elsewhere? | **across space** |

The indoor CO2 sensor becomes the limiting case of a local instrument that turns
out to be substitutable. That is why the Kerkrade characterisation is
load-bearing rather than a sidebar: it is the donor's deep instrumentation, and
establishing what each instrument is worth is part of defining the donor.

## Why tributaries

The site sits in the Worm catchment, and the gauges are tributary gauges. The
Worm reaches the Maas via the Roer; the Geul joins directly. Tributaries receive
less attention than the main stem and are usually absorbed into basin-scale
treatments, yet they are where small flashy catchments generate local flooding,
and they are mostly ungauged, which is what makes transfer worth measuring.

## Data

Waterschap Limburg publishes 634 locations through a public OData endpoint with
no key: 390 water level, 185 groundwater, **59 discharge**. The chapter
previously used three, which was a configuration choice.

**Not limited to the Netherlands.** The inventory republishes German Lanuv gauges
on the Roer and Worm and Rijkswaterstaat gauges on the Maas, so cross-border and
main-stem comparison come from the same source.

Held as of 2026-08-06, via `scripts/22_ingest_waterschap_gauges.py`:

| | |
| --- | --- |
| Discharge, 42 fetched → 38 retained | 2024-08-06 to 2026-08-06, hourly, 89-100% coverage after an 80% floor |
| Multi-gauge tributaries | Geul (3), Geleenbeek (4), Roer (3), Worm (2), Selzerbeek (2) |
| Scale range | 0.02 to 240 m3/s, four orders of magnitude |
| KNMI meteorology, 7 stations | 2020-2026, precipitation corrected 2026-08-06 |
| Groundwater, 3 BRO wells | 2021-2025, 6-hourly, barometrically correctable |
| Kerkrade IoT CO2 | 2025-2026, one house |

**Archive limit.** The endpoint is a rolling window; earliest record 2024-08-06.
Two years, two winters. Longer history needs a direct request to Waterschap
Limburg, WVER, or GRDC.

## Donor selection

Evidence rather than convenience. Coverage discriminates a little: after the 80%
floor the retained set runs 89-100%, and four gauges were excluded at 53-74%.

| Gauge | mean Q | CV | flashiness | centrality |
| --- | ---: | ---: | ---: | ---: |
| geleenbeek_munstergeleen | 1.77 | 0.56 | 0.034 | **0.222** |
| **worm_rimburg** | **2.42** | **0.80** | **0.048** | **0.203** |
| worm_randerath | 2.62 | 0.95 | 0.050 | 0.200 |
| geul_hommerich | 1.47 | 0.79 | 0.023 | 0.191 |
| roer_stah | 16.20 | 0.75 | 0.011 | 0.127 |
| maas_borgharen | 195.46 | 1.31 | 0.129 | 0.024 |
| geleenbeek_millen | 0.89 | 0.18 | 0.019 | 0.017 |

Centrality is the mean absolute correlation of differenced hourly discharge
against all other gauges. Values are low in absolute terms because hourly
differences are noisy; the ranking is what matters.

> **The centrality column above is withdrawn (2026-08-06).** It was computed on
> full-series zero-lag correlation — the metric retired in
> `docs/scope-decisions.md` section 2 — over a 17-gauge candidate set that still
> contained managed structures. Recomputed on the event-conditioned, lag-aligned
> metric across the filtered 42-gauge set, **Worm at Rimburg ranks 18th of 42,
> not 2nd of 17.** Roggelsebeek, Uffelsebeek and Worm at Randerath lead;
> Rimburg's centrality is 0.248 against a leader at 0.372.
>
> Keeping a donor chosen by a metric the same document retires would be
> circular, so the justification is restated below without it.

**Donor: Worm at Rimburg**, justified on grounds that survive the correction:

- It is the catchment holding the CO2 sensor and the BRO wells. This is the
  decisive reason and the only one no other gauge can satisfy — the donor
  framing exists *because* one catchment is instrumented deeply.
- Mid-range on every response characteristic (mean Q 2.43, CV 0.80,
  flashiness 0.048), so it is not an outlier being asked to represent a
  population.
- Complete coverage over the full record.
- A downstream partner at Randerath for within-catchment validation. Randerath
  independently ranks 3rd on the corrected centrality, so the Worm is a
  well-connected river even though Rimburg itself is mid-pack.

**Centrality is not a donor criterion here, and should not be reintroduced as
one.** A high-centrality gauge is one that co-varies with many others, which
mostly measures how typical its weather exposure is. The chapter's question is
what a *deeply instrumented* catchment tells you about its neighbours, so
instrumentation is the selection criterion and centrality is a property to
report, not to select on. Rimburg ranking mid-pack is worth stating plainly: it
makes the transfer test harder, not easier.

**Validation catchment: Geul.** Three gauges in an upstream-to-downstream chain
(Cottessen, Hommerich, Meerssen), so routing can be validated inside a catchment
before any transfer between catchments is claimed. Measured routing time
Hommerich to Meerssen is **+4 h**, verified by symmetric cross-correlation and
consistent with mean discharge rising 1.47 to 2.50 m3/s downstream.

**Excluded as donors, retained as receivers.** Maas Borgharen (main stem,
centrality 0.024, different dynamics), Geleenbeek Millen (CV 0.18, evidently
regulated), Selzerbeek molentak (0.02 m3/s, a mill channel).

## Similarity axes

All derivable from data held or freely available:

| Axis | Source | Status |
| --- | --- | --- |
| Distance | lat/lon in the station inventory, joined on station id | held |
| Response similarity | event-conditioned, lag-aligned discharge correlation | held |
| Catchment scale | mean discharge as proxy | held |
| Signature distance | flashiness, CV, baseflow, recession, seasonality | held |
| Elevation | EU-DEM via OpenTopoData | **held for 16 of 38 gauges only** |
| Meteorological similarity | nearest-KNMI rainfall correlation | **degenerate — see below** |
| Land use, geology, area | CORINE, Copernicus EU-DEM, EStreams | partly pulled |

Two axes are not currently usable and should not be presented as if they were.
`met_similarity` collapses to two distinct values because the KNMI synoptic
network is too sparse in South Limburg (`docs/scope-decisions.md` section 4); it
has been dropped from the pair table rather than reported as an axis. Elevation
resolves for 16 of 38 gauges because the public DEM endpoint fails on the rest;
the script now reports the shortfall instead of silently returning nulls.

## First result: response similarity decays with distance

From `results/regionalisation/similarity_summary.txt`, on 38 filtered gauges and
703 pairs (644 with a usable response):

| | |
| --- | --- |
| corr(distance, response similarity) | **-0.249** (null-calibrated) |
| Mantel permutation p (5,000 gauge-label permutations) | 0.0012 |
| variance in pair similarity explained by distance | 6.2% |
| median co-response, net of the procedural null | **+0.243** |

Inference is by Mantel permutation because 703 pairs come from 38 gauges and are
not independent: each gauge appears in 37 of them. A Pearson p-value on the pair
list would be wrong by many orders of magnitude, and quoting one is the fastest
way to lose a referee.

The effect is real and clearly distinguishable from chance, and it is **weak**:
distance accounts for about a sixteenth of the variation in how alike two
catchments respond. That is itself informative for the question the chapter asks — if
proximity were most of the story, monitoring network design would be trivial —
but it must be presented as a weak effect, not as a decay law.

## The design risk to build around

Catchments within one region share storms. Cross-catchment transfer will look
good partly because the same weather hit both, which is shared forcing rather
than a model generalising.

Under the donor framing this is a variable rather than a confound -- similarity
is what the chapter measures -- but the design must still separate near from far
transfer, or hold out storms rather than catchments. Decide before building.

## Kerkrade findings, retained as donor characterisation

These now describe what the donor's instrumentation is worth. Full detail in
`docs/decisions.md` (2026-08-06).

- **No precursor skill in indoor CO2.** 20 episodes, 3,521 scored hours. Rainfall
  over 72 h reaches AUROC 0.872; every CO2 predictor spans 0.5. The sensor
  detects approaching weather, not approaching water.
- **Eryilmaz replicates on an independent period**: indoor 0.885 against public
  weather 0.874, a gap of 0.012.
- **Groundwater is itself barometric**, efficiency 0.20-0.34. Uncorrected it
  produces spurious hydrological findings; in February 2025 corrected level and
  pressure correlate at -0.74.
- **Occupancy dominates the non-barometric variance.** The 12-hour band is four
  to eight times larger than pressure allows and survives pressure removal.
- **Groundwater follows the river** rather than leading it, 1-3 cm around events.
- **The gain-modulation mechanism was at or below detection** given 0.20 m of
  water movement, and the limit is exposure range rather than sample size.

The barometric response function is **not** in this list. The deconvolution used
49 correlated lags under plain OLS and rings; the "instantaneous response" claim
was an artifact and is withdrawn pending regularisation.

## Directions not taken

**Symmetric transfer matrix.** Fit at every gauge, test at every other, and
report the full matrix. Rejected in favour of the donor framing because it treats
all catchments as equally known, which wastes the deep Kerkrade instrumentation
and makes shared forcing a confound rather than a variable. Worth revisiting if
the donor result proves sensitive to donor choice -- the symmetric version is the
natural robustness check.

**Flood early warning.** The original framing. Dropped: the Dutch operational
system is advanced and well resourced, and the question was too broad.

**Gaussian-process varying coefficient and interaction distributed lag.** Both
test whether barometric gain varies with water level, which the forward bound
answers more directly.

## The design in three questions

`docs/chapter-synthesis.md` states the chapter as three questions — can a donor
predict a receiver (Q1), is that skill transfer or shared weather (Q2), and what
governs the decay (Q3) — with one test each. Read it before building anything;
it is the document that says what is *not* in scope.

## Live scope decisions

`docs/scope-decisions.md` holds the four decisions governing the
regionalisation analysis: the gauge filter (decided), temporal grain
(decided: hourly, event-conditioned), gauged versus ungauged (provisional:
gauged only), and catchment rainfall (deferred). Read it before building.

## Open

1. Whether to pull the remaining 42 discharge gauges. They are receivers, not
   donor candidates, and would widen the transfer set cheaply.
2. Catchment descriptors from CORINE and EU-DEM for the similarity axes.
3. Longer discharge history by direct request, if two winters proves too thin.
4. Geul at Cottessen failed with a gateway timeout on the first pull; retry.
