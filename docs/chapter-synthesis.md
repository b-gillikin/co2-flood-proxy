# Chapter Synthesis — Idea, Methods, Data

Status date: 2026-08-07. **Canonical** for the idea, the design and the data.
Live decisions in `docs/scope-decisions.md`; what is in and out of the chapter in
`docs/analysis-inventory.md`; session state in `docs/HANDOFF.md`.

Rewritten in full on 2026-08-07 rather than patched. The previous version carried
two withdrawn headline results and numbers from three code generations back, and
a canonical document that needs a second document to correct it is not canonical.

Every number here is quoted from an artifact in `results/` produced by the code
currently in the working tree. Where a number is not yet computed, it says so.

---

## 1. The question

> **Given that one Maas tributary is instrumented and gauged, how much does its
> record tell you about high-water events on the others, and how does that fall
> off with distance?**

The object is the Dutch tributaries of the Maas in Limburg. The events are
**crossings of the water authority's published Fase thresholds**. The donor is
the **Worm at Rimburg**.

### What this chapter is not

**It is not a monitoring-network-design or optimal-gauge-placement chapter.**
That framing was withdrawn by the author on 2026-08-07. The distinction is not
cosmetic: network design is prescriptive and has a mature optimisation literature
with its own objective functions; this chapter is descriptive and measures a
quantity. A measurement of how far donor information reaches is an *input*
someone else could use for siting. Reporting it *as* siting advice overclaims and
drags in a literature the chapter does not engage.

**It is not prediction in ungauged basins.** That is substantially answered at
global scale by FloodHub and the LSTM streamflow work. Every catchment here is
gauged, and Model A in the central test *is* the receiver's own gauge.

### The progression it sits in

Supervisor-required, and it is the reason rungs 1 and 2 exist at all:

| | Question | Substitution across |
| --- | --- | --- |
| Viefhues (2022), MSc | Does a deeply instrumented site carry hydrological signal? | — |
| Eryilmaz (2025) | Can public weather substitute for that local instrumentation? | data source |
| **This chapter** | Can a neighbour's gauge substitute for your own? | **space** |

Eryilmaz set the decision rule — **B substitutes if it is within 0.05 AUROC of
A** — and the chapter inherits it, so the spatial result is reported in the same
currency as the study it extends and the threshold cannot be accused of having
been chosen to suit the answer. `src/substitution.py` is the shared harness.

**Do not present the three as an arc.** Rung 3 is the chapter. Rungs 1 and 2 are
a replication and a negative, reported because the progression requires them and
because they set the currency. The ladder was assembled after the fact over lanes
that already existed; asking it to carry the contribution invites the question of
why three of its four legs are about a house in Kerkrade.

---

## 2. Events: the published Fase thresholds

Waterschap Limburg publishes per-gauge discharge triggers, defined in the
[Rampbestrijdingsplan Hoogwater Limburg 2023-2026](https://lokaleregelgeving.overheid.nl/CVDR719417/1):
**Fase 1 = Geel** (heightened vigilance), **Fase 2 = Oranje** (impending
flooding), **Fase 3 = Rood** (active flooding).

Verified against the plan rather than assumed: Maas St. Pieter **1250 / 2000 /
2600** matches its warning / GRIP-2 / GRIP-4 milestones; Geul Hommerich **10 / 20
/ 50** matches its worked tributary example. `scripts/29_fase_events.py`.

**Two thresholds, two jobs, and they must not be conflated.**

| | question it answers | requirement | use |
| --- | --- | --- | --- |
| **Target** | did something happen the authority cares about? | externally defined | **Fase** |
| **Conditioning mask** | which hours are active enough that a correlation between two catchments means anything? | enough hours to estimate a correlation | **own p90** |

The mask is a statistical device that is never interpreted, so self-reference
costs it nothing. Fase as a mask would leave **69% of gauge pairs with zero joint
hours**; own-p90 gives a median of 824.

### Power, honestly — this is the binding constraint

Over the two-year record, on the **37** analysis gauges carrying a usable Fase 1
(the 38 less Niers, excluded below):

| | gauges reaching it | events | median per gauge |
| --- | ---: | ---: | ---: |
| Fase 1 | **26 of 37** | **115** | **3** |
| Fase 2 | 13 of 37 | 21 | 0 |
| Fase 3 | **4 of 37** | 4 | 0 |

Fase 1 sits at a median **p99.96** of a gauge's own record. The 115 events cluster
into **24 network storms**, ten involving ≥3 gauges and six involving ≥5, spread
2024-10 → 2026-02. **42% of onsets fall in January 2025.**

Fase is *rarer* than a percentile, not more evenly spread — an earlier hypothesis
to the contrary was measured and refuted (p99 gives 452 events and a 27% January
share). Report per storm, never a mean, and treat any leave-one-storm-out scheme
as having that many unequal folds.

**Niers at Kessel is excluded by rule** — above Fase 1 for 25.2% of its record,
which is a mis-set threshold rather than a hazard. It is the only offender and it
should be raised with Waterschap.

---

## 3. What is measured, and what stands

### 3.1 Rung 1 — across data source (Eryilmaz replication)

`scripts/03_eryilmaz_replication.py`. Scored **within CV fold** and averaged, with
a paired cluster bootstrap over folds.

| | gap (A − B), within fold |
| --- | ---: |
| Random folds, inherited procedure | **+0.012** [+0.009, +0.015] |
| Forward chaining, no future hour trains | **−0.012** [−0.059, +0.017] |

The two agree and both sit far inside Eryilmaz's 0.05, so **public weather
substitutes for indoor sensing and the conclusion does not depend on the
evaluation scheme.** Model A scores 0.886 within fold under random folds against
0.900 under forward chaining, so there is **no measurable leakage penalty**.

> **Withdrawn 2026-08-07.** An earlier version of this document reported a gap of
> −0.088 with a sign flip, and attributed a 0.141 inflation to random-fold
> leakage. Both were an artifact of **pooling AUROC across folds fitted on
> different data**. AUROC is rank-based; probabilities from separate fits are not
> one ranking. Guarded by `tests/test_substitution.py::GroupedScoringTests`.

**The mechanism is barometric, not occupancy.** Pressure alone scores 0.872 (A)
and 0.864 (B); strip pressure and they fall to 0.587 and 0.681; hour-of-day alone
scores 0.554. An earlier claim in this document that indoor CO2 is "autocorrelated
through occupancy and ventilation" is **refuted by that decomposition**. The
autocorrelation is synoptic. *This is computed but not yet scripted — see
`analysis-inventory.md` item 5.*

### 3.2 Rung 2 — across variable (the negative that closes the CO2 lane)

`scripts/18_precursor_skill.py`. For high-flow onset within 24 h:

| predictor | AUROC | 95% CI |
| --- | ---: | --- |
| 72-hour rainfall | **0.872** | [0.783, 0.933] |
| 24-hour rainfall | 0.816 | [0.719, 0.893] |
| pressure level (inverted skill) | 0.316 | [0.165, 0.460] |
| **CO2 residual, 24 h** | **0.453** | [0.296, 0.587] |
| pressure change, 24 h | 0.506 | [0.414, 0.604] |

The substitute does not merely stand in, it wins outright. **One paragraph in the
chapter.** A well-bounded negative is worth reporting; it is not worth a section.

*Caveat to state in the methods:* the nine "barometrically clean" episodes are all
July–October, because episode selection requires IoT coverage and the record is
31% complete and summer-weighted. So the test isolating non-barometric CO2 signal
runs in the season when barometric forcing is weakest (r = −0.268 JJA against
−0.505 MAM). The negative stands; the reason usually given for it is not the
operative one.

### 3.3 The pairwise measurement — what a neighbour's record resembles

`scripts/23_catchment_similarity.py`. 38 gauges after a structure filter and an
80% coverage floor, 703 pairs, 644 with a usable response. Event-conditioned
(both above own p90), lag-aligned within ±12 h, against a time-shifted null
averaged over ~24 valid draws per pair.

| | value |
| --- | ---: |
| median raw response correlation | +0.259 |
| median time-shifted null — **the procedural floor** | **+0.152** |
| **co-response net of the null** | **+0.106** (Wilcoxon p = 7e-67, real exceeds null in 78% of pairs) |
| **decay with distance, null-calibrated** | **−0.311**, Mantel p < 0.0001 |
| variance explained by distance | **9.7%** |
| same-river pairs, n = 17, *on the raw metric* | −0.469 |
| different-river pairs, n = 627, *on the raw metric* | −0.324 |

The last two rows are quoted on the raw correlation, not the calibrated excess,
because that is what the artifact reports for those subsets. No p-value is quoted
for them: they are subsets of the same dependent pair structure the Mantel test
exists to handle.

**59% of the raw co-response is procedural.** That is the answer to the first
question a hydrology referee asks — *you searched 25 lags and conditioned on both
tails, so you manufactured this* — and it is now a measured answer rather than an
assertion.

> **Corrected 2026-08-07.** Until this date the lag maximum was taken on `|r|` and
> the signed value returned. Under the null that picks the largest *magnitude*
> noise excursion with near-symmetric sign, so the null averaged +0.016 while the
> median |null| was +0.036 — the correction was converging to no correction, and
> for 37% of pairs it made the statistic *larger*. Selecting on signed `r` is also
> physically right: two catchments driven by the same weather should be positively
> correlated at the lag aligning their response times. Previously reported as
> co-response **+0.243** and decay **−0.249 / 6.2%**; both are superseded.

### 3.4 Rung 3 — the chapter, and it is not built

Fit a transfer model at Worm/Rimburg, apply at each receiver, compare against the
receiver's own gauge, through `substitution_test` with `groups` = held-out storm.

- *Target:* the receiver crossing its published **Fase 1** within the next *h*
  hours. Binary, so the metric matches every other rung.
- *Model A:* the receiver's own gauge — persistence plus its own recent history.
- *Model B:* the donor's discharge, first differences, and lags to the pair's
  measured best lag. Nothing else; the point is to measure what **one gauge** buys.
- *Validation:* leave-one-storm-out over the 24 network storms.

**Two things must be settled before it is run, not after.**

**(a) Pre-register the horizon.** The target is a threshold on Model A's own
series, so at short *h* Model A is a near-oracle by construction and the gap is
large at every distance; at long *h* it decays toward climatology and the gap
collapses for reasons unrelated to the donor. **The headline is therefore a
function of *h*.** Choosing *h* after seeing which value gives an interpretable
answer is the same error this repository has already caught three times. Fix the
horizon set in `docs/transfer-experiment-preregistration.md` first.

**(b) Pre-commit to the interval.** A cluster bootstrap over 24 wildly unequal
storms is not a precision instrument. Report per-storm skill as the primary
evidence and label whatever interval accompanies it for what it is.

**Pre-commit also to the answer being null.** *No crossing within the span of this
network* is a publishable result — it says a donor gauge is either useful
everywhere in this region or nowhere, and that proximity is not the design
variable. Decide that now.

### 3.5 The open question about the donor

Rimburg is the donor because it holds the CO2 sensor and the groundwater wells.
**The chapter's own finding is that the CO2 sensor has no hydrological value**
(§3.2), and the groundwater lane was cut on 2026-08-07. So the "deep
instrumentation" justification no longer stands on anything, and what remains is a
discharge gauge that 37 other catchments also have — at the **69th percentile of
transferability**, 11th of 36 donors, not mid-pack.

**Recommended resolution, not yet adopted:** make the deliverable the
*distribution* of donor reach across all candidate donors, with the Worm located
in it as the worked case. Decay ranges **−0.58 to +0.21** across donors and only 2
of 36 show none, so the spread is the result. This keeps the Worm central without
resting the finding on it being special, and it answers "why Rimburg?" before it
is asked. **Decision required.**

---

## 4. Data

### Held

| Source | Coverage | Grain | Span |
| --- | --- | --- | --- |
| **Waterschap Limburg discharge** | 59 exist, 57 fetched → 42 natural → **38 after an 80% coverage floor** | hourly | 2024-08 → 2026-08 |
| **Waterschap Limburg water level** | 390 with a Fase 1 → **272 natural**, 125 water bodies | 10-min to hourly | 2024-08 → 2026-08 |
| **LANUK NRW** | 42 German gauges | 15-min from ~2000; **irregular before** | 1950 → 2026 |
| **RWS Maas** | 5 main-stem + Geul | 10-min | 2000 → 2026 |
| **DWD precipitation** | 34 stations | hourly | 1995 → 2026 |
| **KNMI meteorology** | 7 synoptic stations | hourly | 2020 → 2026 |
| **Kerkrade IoT** | one house, **31% complete, 46% JJA** | hourly | 2025 → 2026 |

Cross-validated rather than assumed: LANUK against Waterschap on four shared
gauges gives r = 0.9994–1.0000; RWS against Waterschap at Borgharen gives
r = 0.9975 after the zero-sentinel fix.

**The NRW archive is not uniformly 15-minute.** Measured from the raw zips: 2020s
median inter-record gap 15.0 min (84.5% at ≤15 min); 1950s median **216 min**
(7.9%). The sampling design changed. Anything using the long record must say which
era it uses.

### The water-level network — probed 2026-08-07, and it does not do what was hoped

Three checks, all answered:

1. **Historical series are served** — 12 of 12 probed returned records.
2. **Coverage is better than discharge** — median 100% against 89–100%.
3. **Event scarcity is *worse*, not better** — median **1** Fase-1 event per
   station against 3 for discharge; 5 of 12 never reach it.

**And the record is the same rolling two-year window, 2024-08 → 2026-08.** Going
wide on level extends the record by nothing.

So the trade is **spatial coverage, not temporal power**: 272 natural level
stations against 44 discharge gauges, and **124 of them on 92 water bodies with no
discharge gauge at all**. That is worth having for a distance-decay question —
more receivers, more short-range pairs, which is exactly the constraint that left
the discharge correlation length unidentified — and worth nothing for events per
catchment. Level is a stage, not a flux: fine for a binary threshold crossing,
wrong for anything requiring a rate. Sampling rates vary and need a common grid.

### The binding data need

**Longer Dutch tributary records.** Three Fase-1 events per gauge in two years is
the ceiling on everything in §3.4, and no method repairs it. Request tracked in
`docs/data-requests.md`; **JCAR ATRACE** as collaborator; HESS 2024 authors hold
1970–2021 15-min Meerssen.

**Ruled out, so they are not re-chased:** ERA5-Land (personal CDS key, ~9 km cells
cannot resolve 27–77 km² catchments); CAMELS-NL and a Dutch Caravan extension
(neither exists); CAMELS-DE (daily, ends 2020); GRDC (main stem only); DWD REGNIE
(retired); deeper Waterschap history (hard-capped).

---

## 5. Machinery, stated once

- **Inference** is Mantel permutation over gauge labels for pairwise statistics,
  and a paired cluster bootstrap over groups for substitution gaps. 38 gauges give
  703 pairs with each gauge in 37 of them; pairs are not independent observations
  and a Pearson p-value on the pair list is wrong by orders of magnitude.
- **Never pool a score across groups.** Probabilities from separately fitted
  models are not one ranking. This produced a withdrawn headline (§3.1).
- **Nulls are mandatory, averaged over many draws, and must be able to measure
  the bias they target.** A single draw attenuates by regression dilution; an
  `abs()` maximum makes the null mean-zero and inert (§3.3).
- **Model complexity is bounded by sample size, deliberately.** Twenty-four storms
  and 38 gauges make an LSTM unjustifiable and would put the chapter against
  FloodHub on its own terrain with a thousandth of the data. Linear and
  transfer-function models, or strictly depth-limited boosting.
- **Coverage gaps are never interpolated.** A row on the hourly grid is not an
  observation; a lagged difference is never computed across a gap.

---

## 6. What the chapter can claim, by state

| State | Defensible claim |
| --- | --- |
| **Now** | Public weather substitutes for indoor sensing (rung 1). Indoor CO2 has no precursor skill over rainfall (rung 2). Response similarity decays with distance, −0.311, 9.7% of variance, net of a measured procedural floor. Donor reach varies from −0.58 to +0.21 across donors. |
| **+ rung 3** | What a neighbour's gauge buys against your own, in AUROC, on the authority's own event definition |
| **+ level network** | The same across 92 additional tributaries |
| **+ long records** | The same for floods rather than high-flow response, and enough events to validate it |

**Stated plainly, because no other document does: the chapter has no positive
result about Maas tributaries yet.** What stands is inherited, negative, or
descriptive. If rung 3 returns *the donor substitutes everywhere* or *nowhere*,
the chapter is a well-executed negative-results chapter with one descriptive
figure. That is survivable and honest, and it should be planned for now rather
than discovered.

---

## 7. Open decisions

1. **Framing, with the supervisor** — is a hydrological-methods chapter with a
   valorisation-level policy hook what he wants, and who is likely to examine it?
   The answer does not depend on rung 3's sign, and asking after it is built costs
   a rebuild.
2. **Donor reach as a distribution** (§3.5) — recommended, not adopted.
3. **Horizon set for rung 3** (§3.4a) — must be fixed before the run.
4. **Whether to ingest the level network** (§4) — spatial coverage only.
5. **Bibliography.** 101 entries, nothing on regionalisation, donor transfer or
   spatial-dependence methodology, and ~20 dead anomaly-detection entries. Flagged
   in three review passes. Being unsituated is close to as serious as being
   unfinished, and unlike rung 3 it depends on nothing.
