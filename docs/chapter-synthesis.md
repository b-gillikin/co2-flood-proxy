# Chapter Synthesis — Idea, Methods, Data

Status date: 2026-08-07. Consolidates and supersedes `docs/methods-outline.md`.
Framing detail in `docs/chapter-direction.md`, live decisions in
`docs/scope-decisions.md`, acquisition status in `docs/data-requests.md`.

The test applied throughout: does this serve the substitution ladder in §2? If
not, it is out of scope.

---

## 1. The core idea

Viefhues (2022) established that a deeply instrumented site carries hydrological
signal. Every study since has asked the same question about what can stand in
for that instrumentation, at widening scope. **This chapter is the third rung of
one ladder, not a new question.**

> **What can substitute for local instrumentation, and at what cost in skill?**

| Scope | A — the local instrument | B — the substitute | Gap in AUROC |
| --- | --- | --- | --- |
| Across **data source** — Eryilmaz (2025) | indoor IoT sensing | public weather | **−0.088**, CI [−0.195, +0.004] — the substitute is, if anything, better |
| Across **variable** — this chapter, §2.1 | the CO2 sensor | rainfall | **−0.41** — the substitute wins outright |
| Across **space** — this chapter, main | **the receiver's own gauge** | **a donor gauge** | *the chapter's result* |

Viefhues is the premise the ladder rests on, not a rung: it shows the instrument
has signal, without asking what could replace it.

### Why this is one question and not three

The design is identical at every rung. Score two predictors on one binary
target, compare AUROC, and decide whether B is close enough to A to stand in.
**Eryilmaz set the decision rule — B substitutes if within 0.05 AUROC of A —
and the chapter inherits it**, so the spatial result is reported in the same
currency as the study it extends and the threshold cannot be accused of having
been chosen to suit the answer.

The spatial rung works because **Model A is the receiver's own gauge**. That is
what you would have if you instrumented locally, so the ceiling is *measured*,
not assumed — and a gauge is held for all 38 retained catchments. The chapter's number is
therefore the **substitution gap**: how much skill is lost by using a
neighbour's gauge instead of your own.

### Why the spatial rung is hydrological, not administrative

The obvious objection is that neighbouring catchments co-vary because the same
rain falls on both, making "substitution" a restatement of proximity.
Measurement says the two are separable:

| | median co-response of pairs | median % of network simultaneously high |
| --- | ---: | ---: |
| Winter (Nov-Mar) | +0.233 | **14.3%** (p90 71.4%) |
| Summer (May-Sep) | +0.308 | **2.4%** (p90 11.9%) |

Winter events are frontal and near-network-wide; summer events convective and
local. But *conditional on both catchments responding*, they co-respond just as
strongly in summer. **Whether** two catchments are both hit is a property of the
storm; **how alike they behave once hit** is a property of the catchments. Only
the second is transferable, and separating them is what the rainfall arm in §2.3
is for.

### Contribution

Not prediction in ungauged basins — substantially answered at global scale by
FloodHub and the LSTM streamflow work. This asks what a *deeply instrumented*
catchment tells you about its neighbours, and answers it in an inherited
currency. Three gaps that literature leaves:

- **Scale.** Global models work on basins typically above 100 km2. These run
  from 27 km2, with mean flows down to 0.02 m3/s.
- **Grain.** That literature is overwhelmingly daily. This is hourly, in small
  flashy catchments.
- **Instrumentation depth.** The donor carries a CO2 sensor, groundwater wells
  and a barometric characterisation. No global dataset has that.

### Motivation, and one validation case

Gauges fail during the events they exist to record. Six NRW records terminate
around July 2021 — Herzogenrath 1 (06-30), Randerath, Welz and Luchem (07-01),
Reifferscheid (07-14 13:00, mid-peak), Kirchberg 1. Deltares independently
reports Geul observations missing "due to damage to the stations during the peak
of this extreme event."

**Motivation and a validation case, not the subject.** The stronger claim — that
outage scales with event magnitude, censoring flood records systematically — was
tested against the NRW archive and **is not supported**: only 3 of 42 gauges have
>85% hourly density in 2010-2025, and among those outage *falls* with flow (3.6%
against 10.0%). Earlier passes suggested otherwise; both were artifacts of
sampling density rising from 21% in the 1950s to 56% today. Six clustered
terminations are a hazard, not a law.

The useful residue is a **hold-out nobody had to manufacture**. Randerath sits on
the Worm downstream of the donor and died mid-flood; Herzogenrath 2 and Honsdorf
survived. Fit the donor model on the survivors, reconstruct what Randerath would
have recorded through July 2021, compare against the independently modelled peak.
One figure in the discussion, demonstrating what substitution is *for*.

### Scope caveat

For the **Dutch tributaries** the record holds no 2021-class event, so the honest
object there is **high-flow response**, not floods. The German gauges and the
Maas main stem reach through 2021 and can carry flood claims.

---

## 2. Methodology and methods

One harness, `src/substitution.py`, runs every rung: two score sets, one binary
target, AUROC each, a **paired** moving-block bootstrap on the gap, and
Eryilmaz's threshold. Before 2026-08-06 each rung re-implemented this and they
disagreed on inference. One harness means one standard, and the ladder becomes
structural rather than asserted.

### 2.1 Rungs already run

**Across data source.** `scripts/03_eryilmaz_replication.py` reports the same
comparison twice: under the inherited random 5-fold procedure, for faithfulness,
and under forward-chaining folds, which is the number comparable to the other
rungs because no future hour trains the model.

| | indoor IoT | public weather | gap |
| --- | ---: | ---: | --- |
| Random folds (inherited, leaky) | 0.885 | 0.874 | +0.012 [−0.005, +0.027] |
| **Forward chaining (comparable)** | **0.744** | **0.833** | **−0.088 [−0.195, +0.004]** |

**The gap changes sign.** Leakage inflated the indoor model by 0.141 and the
outdoor model by only 0.041 — as expected, since indoor CO2 is strongly
autocorrelated through occupancy and ventilation, so adjacent-hour leakage lets
the model memorise rather than predict. Out of sample, public weather is no worse
than indoor instrumentation and the point estimate favours it. The interval spans
zero, so "outperforms" is not established; "substitutes" is, more robustly than
the original design could show.

Part of the drop is the smaller training set forward chaining permits (3,300
against 3,964 scored hours), which is why both are reported rather than one
replacing the other. A bootstrap widens an interval; it cannot repair a leaky
point estimate, and putting random-fold numbers beside the donor rung would
launder them.

**Across variable.** `scripts/18_precursor_skill.py`. CO2 0.46 against rainfall
0.872 for high-flow onset. The substitute does not merely stand in, it wins
outright. This is the limiting case that motivates using discharge.

### 2.2 The spatial rung — Q1, not yet built

Fit a transfer model at **Worm/Rimburg**, apply at each receiver, and compare
against the receiver's own gauge.

- *Target:* onset of a Fase 1 exceedance at the receiver within the next *h*
  hours, for *h* in 1, 3, 6, 12, 24. Binary, so the metric matches every other
  rung. Continuous skill (KGE on discharge) is reported as secondary.
- *Model A:* the receiver's own gauge — persistence plus its own recent history.
- *Model B:* the donor's discharge, first differences, and lags to the pair's
  measured best lag. Nothing else; the point is to measure what **one gauge**
  buys.
- *Validation:* leave-one-storm-out over the ~10 network alarm episodes. Holding
  out storms rather than catchments keeps shared forcing out of the training set.

### 2.3 The control — Q2

A third arm: **rainfall alone**. If the donor adds nothing over knowing the
weather, donor gauges are redundant wherever rainfall is observed. That is a
real, publishable, negative result and the chapter must be willing to report it.

This is why radar rainfall is the blocking data need — and why it blocks only
this arm, not the headline gap.

### 2.4 The decay — Q3

Regress the substitution gap across receivers on **distance, signature distance,
scale ratio**, with the winter/summer regime as a covariate.

> **The headline number is the distance at which the substitution gap exceeds
> 0.05 AUROC** — the point at which a neighbour's gauge stops standing in for
> your own, by Eryilmaz's own rule.

### Machinery, stated once

- **Events** are Fase 1/2/3 exceedances, the water authority's published alarm
  thresholds — externally defined and comparable across gauges, where a
  percentile is self-referential and here largely set by January 2025.
- **Inference** is permutation over gauge labels for pairwise statistics, and the
  paired block bootstrap for substitution gaps. 38 gauges give 703 pairs with
  each gauge in 37 of them; pairs are not independent observations.
- **Nulls are mandatory**, and averaged over many draws. Best-lag selection and
  tail-conditioning manufacture correlation from nothing — measured floor +0.016
  against a real +0.257. With a single draw per pair the floor is so noisy that
  it attenuates the calibrated metric by a factor of two.
- **Model complexity is bounded by sample size, deliberately.** Ten storms and 42
  gauges make an LSTM unjustifiable and would put the chapter against FloodHub on
  its own terrain with a thousandth of the data. Linear and transfer-function
  models, or strictly depth-limited boosting.
- **Robustness:** repeat §2.4 with every gauge as donor. Rimburg is 18th of 42 on
  centrality, so "is Rimburg special?" will be asked.

### Power, honestly

Ten network alarm episodes, two of them large and both in January 2025 — 4% of
the record supplying 58% of all extreme hours. Leave-one-storm-out gives ten
folds of very unequal weight: report per-fold skill, never only the mean.

### 2.5 The unifying axis: spatial correlation length

`scripts/28_correlation_length.py`. One question asked of every variable the
chapter touches: **how far can you move from a place before this variable stops
telling you about it?**

    c(d) = c_inf + (c0 - c_inf) * exp(-d / L)

| Variable | c0 | L (km) | 95% CI | half-distance |
| --- | ---: | ---: | --- | ---: |
| Pressure, hourly | 1.00 | ≫ domain | [8, 3000], 5 stations | — |
| **Rainfall, hourly** | **0.87** | **30.2** | **[23, 40]** | 21 km |
| Rainfall, daily | 0.94 | 110.6 | [63, 205] | 77 km |
| **High-flow response, hourly** | **0.42** | 30.0 | **[9, 631]** | 21 km |
| High-flow response, null-calibrated | 0.39 | 29.6 | [8, 606] | 20 km |

**This is what makes the inherited progression physical rather than rhetorical.**
Eryilmaz's substitution works *because* pressure is spatially uniform over a
domain this size: a station 22 km away is, barometrically, the same place. His
result is a spatial finding that was never labelled as one, and it sits at the
top of the same axis the chapter measures discharge on.

Two things the data supports, and one it does not:

- **Supported.** `c0` separates the variables far more than `L` does — 0.87 for
  rainfall against 0.42 for discharge. Two co-located rain gauges agree; two
  co-located catchments only half-agree. Catchment individuality shows up as an
  amplitude reduction.
- **Supported.** Grain is not incidental: daily rainfall decorrelates over
  ~110 km and hourly over ~30 km, so any comparison must be at matched grain or
  it manufactures a difference out of aggregation.
- **NOT supported.** That rainfall and discharge share a correlation length. The
  point estimates coincide at 30 km, but bootstrapping over *gauges* rather than
  pairs puts the discharge interval at [9, 631]. **The coincidence is not
  established and must not be claimed.**

**Why the discharge length is unconstrained, and why that is itself a finding.**
Median pair spacing is 32 km against L ≈ 30 km, so only **28% of pairs sit inside
one correlation length** and most of the network is already on the flat tail. A
gauge network whose typical spacing exceeds the correlation length of the process
it measures cannot determine that correlation length. For a chapter about where
to put gauges, that is an argument for denser short-range gauging, and it is
testable — the 42-gauge LANUK network may resolve it, once
`scripts/25_ingest_lanuk_nrw.py` captures station coordinates, which it currently
does not.

This also reconciles the weak variance explained. Distance accounts for 6.2% not
because decay is absent but because a *linear* Mantel coefficient under-reads an
*exponential* decay when most pairs are beyond L. The correlation length is the
better parameterisation; the Mantel coefficient answers a different question.

### Established, and standing

| Finding | Value |
| --- | --- |
| **Weather substitutes for indoor sensing, and may beat it** | **gap −0.088, CI [−0.195, +0.004]** under forward-chaining folds |
| — the same comparison under the inherited random folds | gap +0.012, CI [−0.005, +0.027] |
| Rainfall beats CO2 for high-flow onset | 0.872 against 0.46 |
| Response similarity decays with distance | **−0.249**, Mantel p = 0.0012 |
| Variance explained by distance | **6.2%** |
| Co-response net of the procedural null | **+0.243**, Wilcoxon p = 1e-74 |
| Rainfall correlation length, hourly | 30 km [23, 40] |
| High-flow response correlation length | 30 km, but [9, 631] — unconstrained |

**On the first row.** Refitting Eryilmaz under forward chaining moves indoor
sensing from 0.885 to 0.744 and outdoor weather from 0.874 to only 0.833, so the
gap changes sign. Random folds inflated the indoor model three times as much,
which is what one would expect: indoor CO2 is strongly autocorrelated through
occupancy and ventilation, so adjacent-hour leakage lets the model memorise
rather than predict.

Out of sample, public weather is **no worse** than indoor instrumentation at
predicting indoor CO2, and the point estimate favours it. The interval spans
zero, so "outperforms" is not established — but "substitutes" is now established
more robustly than the original design could show. Part of the drop is the
smaller training set forward chaining allows (3,300 against 3,964 scored hours),
which is why both are reported side by side rather than one replacing the other.

---

## 3. Data

### Held

| Source | Coverage | Grain | Span |
| --- | --- | --- | --- |
| **Waterschap Limburg** | 57 → 42 natural → **38 after an 80% coverage floor** | hourly | 2024-08 → 2026-08 |
| **LANUK NRW** | **42 German gauges** | 15-min native | **1950 → 2026** |
| **RWS Maas** | 5 main-stem + Geul/Cottessen | 10-min | 2000 → 2026 |
| **DWD precipitation** | 34 stations | hourly | 1995 → 2026 |
| **KNMI meteorology** | 7 synoptic stations | hourly | 2020 → 2026 |
| **EStreams** | 18-19 matched catchments | static | — |
| **BRO groundwater** | 3 wells | 6-hourly | 2021 → 2025-08 |
| **Kerkrade IoT** | one house | hourly | 2025 → 2026 |

Cross-validated rather than assumed: LANUK against Waterschap on four shared
gauges gives r = 0.9994-1.0000; RWS against Waterschap at Borgharen gives
r = 0.9975 after the zero-sentinel fix.

**Caveat on the NRW archive:** it is not uniformly 15-minute. Hourly density runs
21% in the 1950s to 56% today, so any analysis spanning decades must account for
this or it will measure instrument history.

### Needed, by which rung it unblocks

| Need | Blocks | Route |
| --- | --- | --- |
| **Radar rainfall** — DWD RADOLAN (1 km hourly, 2005-, open), KNMI RAD_NL25_RAC (key held) | **§2.3 only** | No permission needed; needs catchment polygons |
| **Catchment polygons + `geopandas`** | §2.3 | EStreams ships boundaries; ranged access works |
| **Dutch tributary long records** | Widens the spatial rung from high flow to floods | Waterschap request; **JCAR ATRACE** as collaborator; HESS 2024 authors hold 1970-2021 15-min Meerssen |

**§2.2 and §2.4 need nothing that is not already on disk.** Model A and Model B
are both discharge; rainfall enters only as the §2.3 control. This is the single
biggest consequence of the substitution framing — the headline gap and its decay
are computable now.

Station rainfall alone does not unblock §2.3. Combining DWD and KNMI halves the
median gauge-to-station distance from 14.7 km to 8.0 km and cuts the worst
degenerate cluster from 21 gauges to 10 — enough to make meteorological
similarity a usable covariate — but 8 km against catchments 5-9 km across cannot
distinguish the rain falling on two neighbours.

**Wanted, not blocking:** KNMI dense precipitation network (the Azure backfill
function can be repointed; KDP dataset id needs confirming); Viefhues 2020-21 IoT
record; provincial groundwater and pumping schedules (sent 2026-08-06); Geul at
Cottessen history.

**Ruled out, so they are not re-chased:** ERA5-Land (needs a personal CDS key,
and ~9 km cells cannot resolve 27-77 km2 catchments); CAMELS-NL and a Dutch
Caravan extension (neither exists); CAMELS-DE (daily, ends 2020); GRDC (main stem
only); DWD REGNIE (retired); deeper Waterschap history (hard-capped).

### What the chapter can claim at each state

| State | Defensible claim |
| --- | --- |
| **Now** | Two rungs complete. The spatial gap and its decay, on high-flow response |
| **+ radar rainfall** | The gap separated from shared forcing — the ladder finished |
| **+ Dutch long records** | The same for floods, plus the Randerath reconstruction |
