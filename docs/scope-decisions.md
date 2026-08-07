# Scope Decisions

Status date: 2026-08-07

Live decisions governing the regionalisation analysis. Settled ones move to
`docs/decisions.md`; this file holds what is decided-but-not-yet-implemented and
what is still open. See `docs/chapter-direction.md` for the framing these serve.

---

## 1. Gauge filter — DECIDED

**Decision.** Exclude managed structures by name. Canals, dikes and weirs are all
out; a weir gauge measures a controlled release, not a catchment response, and
that is a different physical object regardless of how good the record is.

Exclusion pattern: `stuw` (weir), `duiker` (culvert), `inlaat` (inlet),
`verdeelwerk` (distribution works), `kanaal` (canal), `sloot` (ditch), `gemaal`
(pumping station), `dijk` (dike). Plus any gauge with sustained negative flow,
which indicates reversing or controlled discharge.

**Effect.** Implemented in `scripts/23_catchment_similarity.py` on 2026-08-06.
57 fetched → 15 excluded as structures → 42 natural → **38 after an 80%
coverage floor**, 703 pairs.

**Evidence this was needed**, confirmed on the run that applied it:

| | with structures | filtered | filtered + zeros blanked |
| --- | ---: | ---: | ---: |
| baseflow index, minimum | **-0.364** (impossible for a percentile ratio) | 0.000 | **0.093** |
| flashiness, maximum | **0.780** | 0.224 | 0.224 |
| winter/summer ratio, maximum | — | 14.54 | **12.12** |

The third column is the zero-sentinel correction below, applied 2026-08-06.

---

## 1b. Zero-sentinel contamination — FIXED 2026-08-06

**The Waterschap feed uses exact `0.0` as a missing-data marker, and the ingest
was averaging those zeros into the hourly mean.**

Found by cross-checking against Rijkswaterstaat, which publishes the same
Borgharen gauge (the Waterschap record is labelled *"bron Rijkswaterstaat"*).
The two disagreed on 20% of hours despite being the same instrument.

Raw ten-minute values at Borgharen, 2024-10-10 15:00:

    [0.0, 0.0, 1336.0, 0.0, 0.0, 0.0]  ->  hourly mean 222.7

RWS reports a steady ~1336 m3/s across that hour. The hourly mean was a sixth of
the true flow.

**Extent.** 26 of 57 gauges, 96,534 of 4.2 M readings (2.28%). Worst: Borgharen
7.9%, itterbeek 19.4%, leukerbeek 9.9%, uffelsebeek 9.2%, vlootbeek 7.4%.

**Why it mattered more than 2.3% suggests.** Every response statistic is
computed on *first differences*. An isolated zero inserts two spurious step
changes of the full flow magnitude, so the contamination lands directly in
flashiness, CV and the response correlations.

**Fix.** `scripts/22_ingest_waterschap_gauges.py` blanks exact zeros to NA.
Gauges more than 50% zero are flagged and left alone, since those may genuinely
be dry rather than broken — `selzerbeek_molentak` at 47% sits just under that
line and should be checked by eye.

**Verification.** Borgharen against RWS improved from r = 0.9805 to **r = 0.9975**,
and the corrupted hour now reads 1336.0 against RWS 1333.5.

**Effect on conclusions: none adverse — every result strengthened**, because the
zeros were adding noise rather than signal.

| | before | after |
| --- | ---: | ---: |
| corr(distance, response) | -0.299 | **-0.249** (null-calibrated, 38 gauges) |
| paired co-response excess | +0.187 | **+0.243** |
| Wilcoxon p | 3e-25 | **1e-74** |

**Open sub-item.** The name filter is a heuristic. Before anything reaches the
chapter it needs a manual pass against the map, because "how did you decide what
counts as a catchment" is a question that will be asked and "regex on the station
name" is not the answer to give. The 15 excluded station names are listed at the
foot of `results/regionalisation/similarity_summary.txt` for exactly that pass.

---

## 2. Temporal grain — DECIDED: hourly, event-conditioned

**Decision.** Keep the hourly grid. The chapter is about events *and* about
prediction, so what happens before and after an event is part of the subject and
must not be averaged away.

**The apparent problem.** Median cross-river correlation of hourly first
differences was +0.025. Near zero, and it got worse when more gauges were added.
That looked like an argument for daily or event aggregation.

**It was an artifact of how the correlation was computed, not of the grain.**
Two things were wrong: averaging over long quiet periods where nothing is
happening, and forcing zero lag between catchments with different response times.

| Condition | pairs | median r | p90 |
| --- | ---: | ---: | ---: |
| zero-lag, all hours | 804 | +0.025 | +0.186 |
| zero-lag, both gauges above own p90 | 722 | +0.113 | +0.392 |
| best-lag ±12 h, all hours | 804 | +0.060 | +0.261 |
| best-lag, both gauges above own p90 | 722 | +0.243 | +0.477 |

**So both hold together.** Hourly is the grain; events define *which* hours enter
a comparison; lag alignment handles differing catchment response times. Daily
aggregation is not needed and would discard the lead-and-recession structure the
prediction question depends on.

### Correction, 2026-08-06: about a third of +0.243 was procedural

The conclusion above stands. The number does not, and it must not be quoted raw.

Selecting the maximum |r| across 25 candidate lags inflates correlation on its
own, and conditioning on *both* series exceeding their own p90 selects for
co-movement by construction. Both biases are present whether or not the two
catchments have anything to do with each other.

`scripts/23_catchment_similarity.py` now calibrates this against a time-shifted
null — the identical procedure applied after rolling one series by a large
random offset, which destroys shared weather while preserving every source of
procedural bias, at matched sample size.

| | median r |
| --- | ---: |
| real pairs | +0.257 |
| time-shifted null, **averaged over ~24 draws per pair** | +0.016 |
| **paired difference** | **+0.243** |

Real exceeds null in 86% of the 644 pairs holding both estimates; Wilcoxon
signed-rank p = 1e-74.

### Correction, 2026-08-06 (second): the null needs many draws, not one

An external review (`docs/chapter-review-2026-08-06.md` §1) found that the
Mantel test was run on the **raw** metric, not the null-calibrated one this
section mandates, and that recomputing on the calibrated metric collapsed the
headline from −0.305 (p < 0.0002) to −0.143 (p = 0.14 on our seed). Verified and
correct.

The cause was **one null draw per pair**. That makes the null a very noisy
estimate of the procedural floor, and because the calibrated metric is
`response_corr − response_corr_null`, the noise sits in the subtrahend and
attenuates the excess toward zero. Averaging ~24 valid draws per pair fixes all
three symptoms the review identified:

| | one draw | ~24 draws |
| --- | ---: | ---: |
| Mantel on the calibrated metric | −0.143, p = 0.14 | **−0.249, p = 0.001** |
| Mantel on the raw metric | −0.305 | −0.264 |
| Pairs where the null resolves | 350 of 861 (41%) | **644 of 703 (92%)** |
| corr(distance, the null itself) | −0.097 | **−0.052, p = 0.24** |

**The raw and calibrated metrics now agree** (−0.264 against −0.249). The gulf
between them was single-draw noise, not a real disagreement about the answer.

The review's point (b) — that the surviving pairs were a closer-than-average
subset — dissolves at 92% coverage. Point (c) — that the null itself carried a
distance signal, implying surviving seasonality — also dissolves: −0.052 is not
distinguishable from zero, so the earlier −0.097 was noise rather than leakage.

**Headline, on the metric this document mandates: −0.249, Mantel p = 0.001,
6.2% of variance, on 38 gauges and 644 pairs.**

**Report the paired difference, not the raw median.**

**Implementation note.** Response similarity must be computed on event-window
hours at best lag, never on the full series at zero lag, and always against the
null. Both the full-series figure and the uncalibrated +0.243 are wrong numbers.

---

## 3. Gauged versus ungauged — PROVISIONAL: gauged only

**Provisional decision.** Restrict to gauged catchments. The ungauged-basin
question has a large literature and has been substantially answered at global
scale by Google FloodHub and the LSTM streamflow work already in the
bibliography (`Kratzert2019PUB`, `Nearing2024`, `Gauch2021`, `Frame2021NWMLSTM`).

### Correction, 2026-08-07: the "network design" answer below is WITHDRAWN

Stated by the author: **this is not a chapter about where to put a gauge.** The
framing below was a provisional answer to the novelty question and it leaked into
`chapter-direction.md` and the HANDOFF. It is withdrawn, and the block is kept
only as a record of a direction not taken.

The chapter is **descriptive, not prescriptive**: given that the Worm at Rimburg
is deeply instrumented, how much does its signal tell you about other Maas
tributaries around high-water events, and how does that fall off? A measurement
of donor reach is an *input* somebody else could use for siting; reporting it as
siting advice overclaims and drags in a value-of-information literature the
chapter does not engage. See `docs/analysis-inventory.md`.

**Still to strip:** `chapter-direction.md` ~175 and ~216.

---

**The novelty question this raises, and an honest answer.**

Restricting to gauged catchments means this is no longer prediction in ungauged
basins. That is a real cost: it removes the most-cited framing. What it becomes
instead is arguably a better fit for the available data and for the institute:

> **Monitoring network design.** Given that you can instrument one catchment
> deeply, how much does that tell you about its neighbours, and what governs the
> reach? That is a question about where to put a gauge, not about whether a model
> can predict without one.

That question is not answered by FloodHub, which addresses prediction accuracy
given existing global training data. It is a different literature — value of
information, hydrometric network design — and it is policy-relevant in a way that
suits a socio-economic research institute.

Three further gaps in the global-model literature that this data speaks to:

- **Scale.** Global streamflow models work on basins typically well above 100
  km2. Gauges here run down to 0.02 m3/s mean flow, which is far below that.
- **Grain.** That literature is overwhelmingly daily. This is hourly, in small
  flashy catchments, which is a different response regime.
- **Instrumentation depth.** The donor here carries a CO2 sensor, groundwater
  wells and a barometric characterisation. No global dataset has that.

**Coverage this gives.** 38 retained gauges across the Limburg tributary system in the
Limburg Maas tributary system, spanning four orders of magnitude in mean flow
(0.02 to 240 m3/s), two years, 89-100% coverage after an 80% floor. Cross-border German Lanuv gauges
on the Roer and Worm are included, as are Rijkswaterstaat Maas main-stem gauges
for scale contrast.

**Still open.** Whether "monitoring network design" is the framing the supervisor
wants, and whether it satisfies a committee expecting hydrological novelty. This
is the question to put to him before building further, because everything
downstream depends on it.

### EStreams static attributes — ACQUIRED

Fetched regardless of how 3 resolves, because they are cheap and useful either
way. `scripts/24_fetch_estreams_attributes.py`.

EStreams (Nascimento et al., *Scientific Data*, 2024) covers 17,130 European
catchments with terrain, soil, geology, hydrology, vegetation and land-cover
attributes, plus delineated boundaries.

The archive is a single 10 GB zip, dominated by per-catchment meteorology files
the chapter does not need. Zenodo honours HTTP range requests, so the script
reads the zip central directory from the tail and pulls only the attribute
tables — **a few MB instead of 10 GB.**

**Match quality is bimodal, and only the near half is real:**

| Tolerance | matched of 42 natural gauges |
| --- | ---: |
| 1 km | **18** |
| 2 km | 19 |
| 5 km | 21 |
| 10 km | 35 |
| 20 km | 44 |

Eighteen match at essentially zero distance, several at exactly 0.00 km, meaning
EStreams contains those same gauges. Beyond about 2 km the matches are spurious
nearest-neighbours to unrelated catchments. **Use a 1 km tolerance**; the wider
numbers are an artifact of nearest-neighbour matching with no cutoff.

So roughly **18-19 of 41 natural gauges have full static attributes** (366
columns) from a peer-reviewed source. That is enough to test whether static
descriptors proxy the behavioural signatures, which is the bridge needed if the
chapter ever wants to speak to ungauged catchments.

---

## 4. Catchment rainfall — DEFERRED

Deferred until 3 is settled, at the user's direction.

**The problem.** Seven KNMI stations, only 06380 Maastricht regionally relevant
at 22 km; the rest sit 50-100 km north. Every southern gauge snaps to the same
station, so `met_similarity` collapses to two distinct values (1.0 and 0.751). It
is a binary flag, not an axis.

**Options, to revisit:**

| Source | Resolution | Cost |
| --- | --- | --- |
| KNMI radar RAD_NL25_RAC | 1 km, 5 min | API key held; large volume; needs catchment polygons |
| KNMI precipitation network (~320 stations) | point, daily | easy; daily only |
| ERA5-Land | ~9 km, hourly | free via CDS; coarse for small catchments |
| Visual Crossing (held) | 4 points | already have it; too sparse |

**Coupling worth remembering.** Catchment rainfall means averaging over a
catchment polygon. EStreams ships delineated boundaries, so if those 18 matched
catchments are the analysis set, radar rainfall becomes tractable without
delineating anything — but reading the shapefiles does need a geospatial stack.

---

## Smaller open items

- **Geul at Cottessen** returned no records on every attempt. Check whether it is
  level-only despite the `Drainage` type. Determines whether the Geul validation
  chain is two gauges or three.
- **Longer discharge history** by direct request to Waterschap Limburg, WVER or
  GRDC. Two winters is workable for a first pass; deferred.
- **Nothing is committed** since the reframe. Four new scripts, the docs rewrite,
  57 gauges and the EStreams attributes. The push remains blocked on an expired
  github.com token.
