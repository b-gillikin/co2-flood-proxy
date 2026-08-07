# Analysis Inventory — What Belongs in the Chapter

Status date: 2026-08-07. Every analysis this chapter has run, across all phases,
assessed against the spine below. Written at the author's request after the
observation that the chapter "gets close to the idea of what I want and then
drifts away when we get into the analysis."

---

## The spine, as the author states it

> Maas tributaries in the Netherlands. High-water level events. The
> supervisor-required progression **Viefhues (2022) MSc → Eryilmaz (2025) →
> this chapter**, doing something with the **Worm signal/noise that transfers to
> other tributaries around high-water events.**

Everything below passes or fails against that sentence. The test is not "is this
good work" — much of the failing work is good. The test is **"does a reader of
this chapter need it to believe the transfer result?"**

### What this chapter is NOT — stated 2026-08-07 by the author

**It is not a monitoring-network-design or optimal-gauge-placement chapter.**
That framing entered via `scope-decisions.md` §3 as a provisional answer to the
novelty question and has since leaked into several documents. It is withdrawn.

The difference is not cosmetic:

| | network design | **this chapter** |
| --- | --- | --- |
| mood | prescriptive — *where should a gauge go?* | descriptive — *given the Worm is instrumented, what does it tell you about the others?* |
| deliverable | a siting rule | a measured transfer skill and its falloff |
| literature | value of information, hydrometric network optimisation | donor transfer / regionalisation |

A measurement of how far donor information reaches is an *input* someone else
could use for siting. Reporting it as siting advice overclaims, invites a
literature the chapter does not engage, and is the same overreach that produced
the correlation-length and sign-flip withdrawals.

**Still to strip:** `scope-decisions.md` §3 (whole "Monitoring network design"
block), `chapter-direction.md` lines ~175 and ~216.

---

## Why it drifts: two mechanisms, both structural

**1. Every phase ended by characterising an instrument instead of answering a
question.** The CO2 sensor, the groundwater wells, the barometer, the earth tide,
the EStreams attributes, the catchment signature space — each arrived, each
generated its own lane, and each lane produced a defensible result about *what
that instrument is doing*. None of them answered whether the Worm transfers. The
substitution ladder was invented after the fact to retro-fit a spine onto lanes
that already existed, which is why three of its rungs are about a house in
Kerkrade and only one is about Maas tributaries.

**2. The chapter keeps changing currency.** AUROC gap (the ladder), Mantel r
(similarity), correlation length L (`28_`), signature distance, KGE (planned
secondary). Each currency invites its own analysis, its own inference machinery,
and its own robustness battery. **One currency. The rest are drift.**

The corollary: an analysis that needs a *new* currency to express its result is
almost certainly out of scope.

---

## Verdict summary

Counted as entries below, where one entry may bundle related scripts.

| | count |
| --- | ---: |
| **Live** — Lane A (Kerkrade) + Lane B (tributaries) | **22** |
| — keep | 11 |
| — keep but demote to a robustness arm | 1 |
| — **cut** | **10** |
| **Not yet built** — Lane C | 6 |
| — build (one of them *is* the chapter) | 5 |
| — drop | 1 |
| **Already retired** — Lane D, confirming they stay dead | 7 |
| **Total entries across the chapter's life** | **35** |

Of the 11 live keeps, 4 are pure ingest. **The chapter is 9 analyses**; see the
minimal chapter at the foot of this document.

---

## LANE A — Kerkrade CO2 (Viefhues → Eryilmaz)

The progression requires this lane to exist. It does **not** require it to be
large. Target size: motivation paragraph + one results subsection.

| # | Analysis | Verdict | Why |
| --- | --- | --- | --- |
| 1 | `01_ingest_iot.py` | **KEEP** | Infrastructure for rungs 1–2. |
| 2 | `02_ingest_weather.py`, `04_ingest_knmi.py`, `04_sync_knmi_azure.py` | **KEEP** | Supplies Eryilmaz's Model B and the rainfall comparator. |
| 3 | `01_eda.py` | **KEEP, thin** | The join and the coverage QC. Coverage QC is load-bearing given the IoT record is 31% complete. |
| 4 | `02_barometric_baseline.py` | **KEEP, demoted** | Produces the barometric residual that `18_` scores. Survives only as long as rung 2 does. |
| 5 | `03_eryilmaz_replication.py` | **KEEP — required** | This *is* E's paper. The progression is not optional. Needs the fold-wise scoring fix. |
| 6 | `04_signal_characterization.py` | **CUT** | The drift engine. PCA + random-forest importance + cross-correlation scanned over 336 lags against every available column, no hypothesis, no multiplicity correction. Its top hits are `iot_pm2_5` at lag 262 h (r = 0.22) and indoor RH at lag 28 h. That is noise mining. Nothing downstream reads it. |
| 7 | `18_precursor_skill.py` | **KEEP as one paragraph** | Rung 2, and the clean negative that *closes* the CO2 lane: CO2 0.46 against rainfall 0.872. A well-bounded negative is worth reporting; it is not worth a section. |
| 8 | `19_barometric_response.py` | **CUT** | The response shape is already withdrawn (rings under OLS). Only `cumsum[-1]` survives, and only `21_` consumes it. |
| 9 | `20_tidal_response.py` | **CUT** | Earth tide in an indoor CO2 record. Genuinely interesting, entirely outside the spine. The finding — the 12 h band is occupancy — is a sentence in the methods at most. |
| 10 | `21_forward_gain_model.py` | **CUT to one sentence** | A physical bound on a mechanism the chapter has already concluded is absent. The reasoning is the best in the repo; keep the *sentence* ("we established what a capable study would need"), drop the machinery. |
| 11 | `05_ingest_groundwater.py`, `05a_fetch_bro_groundwater.py` | **CUT** | Infrastructure for 12–13 below. |
| 12 | `05b_barometric_efficiency.py` | **CUT** | Characterises three wells. Does not touch transfer. |
| 13 | `05c_groundwater_event_lag.py` | **CUT** | A third instrument, a third detour. |

**Lane A verdict: 5 keep, 8 cut.** Items 8–13 are the "deep instrumentation"
story. That story is *premise*, not result — Viefhues already established it, and
this chapter cites him for it rather than re-establishing it with three more
instruments.

---

## LANE B — Tributaries and events (the actual chapter)

| # | Analysis | Verdict | Why |
| --- | --- | --- | --- |
| 14 | `22_ingest_waterschap_gauges.py` | **KEEP — core** | The only source covering Dutch Maas tributaries. Should go wide (see Scope). |
| 15 | `03_build_event_catalogue.py` | **KEEP, but rewrite** | Builds p90/p95/p99 while `Fase1Value`/`Fase2Value`/`Fase3Value` sit unread in `waterschap_locations.csv` for all 38 gauges. It should emit **both**: the Fase flags as the *target*, and own-p90 as the *conditioning mask*. See the Fase section — they are different jobs. |
| 16 | `23_catchment_similarity.py` — **pair table** | **KEEP — core** | Distance, event-conditioned lag-aligned response correlation, and the time-shifted null. This is the measurement the chapter is about. Keep the **p90 mask** here; Fase would leave 69% of pairs with zero joint hours. |
| 17 | `23_catchment_similarity.py` — **signature space** | **CUT** | `flashiness`, `low_flow_ratio`, `recession_constant`, `winter_summer_ratio` (n = 2 winters), `signature_distance`. A similarity space nothing in the ladder consumes, carrying a statistic with no sampling distribution into an inferential axis. Cutting it removes four of the twelve code defects the reviews raised. |
| 18 | `28_correlation_length.py` | **CUT** | Broken as built (two estimators compared as if one), and even repaired it introduces a **second currency** competing with the substitution gap. The one thing worth keeping — pressure is spatially uniform, which is *why* Eryilmaz's substitution works — is two sentences and a range, not a curve fit. |
| 19 | `24_fetch_estreams_attributes.py` | **CUT** | 18 of 38 catchments, 366 columns, already ruled unmodellable. Acquired cheaply and correctly; that is not a reason to use it. |
| 20 | `25_ingest_lanuk_nrw.py` | **DEMOTE** | 42 German gauges. Not Dutch Maas tributaries, so not the spine — but they carry July 2021 and short-range pairs. Keep as a **robustness arm**, explicitly labelled as such. |
| 21 | `26_ingest_rws_maas.py` | **KEEP, narrow** | Main stem. Its job is the Borgharen cross-validation that found the zero-sentinel bug, plus scale contrast. Not a tributary source. |
| 22 | `27_ingest_dwd_precipitation.py` | **KEEP, narrow** | The rainfall control for Q2. Note it is *German* stations; Dutch tributaries want KNMI. |

**Lane B verdict: 6 keep (2 narrowed, 1 demoted), 3 cut.**

---

## LANE C — Not yet built, and required

| # | Analysis | Verdict | Why |
| --- | --- | --- | --- |
| 23 | **Donor substitution (rung 3)** | **BUILD — this is the chapter** | Receiver's own gauge as A, Worm/Rimburg as B, target = receiver above its published Fase 1 within *h* hours. Needs nothing not already on disk. |
| 24 | **Rainfall control (Q2)** | **BUILD, simplest form** | Does the donor add anything over knowing the weather? A publishable negative either way. Station rainfall is enough for a first pass; radar is a refinement, not a gate. |
| 25 | **Decay of the gap with distance (Q3)** | **BUILD, one covariate** | Gap against distance. **Not** a multi-covariate regression on signature distance and scale ratio — that is item 17 coming back through the window. |
| 26 | **Per-donor decay distribution** | **BUILD — cheap** | Already run by the 08-07 reviewer: decay ranges −0.58 to +0.21 across donors. It answers "is Rimburg special?", which will be the first question after the seminar, and it locates the Worm result in a distribution instead of asserting it is typical. Report it as *how much the answer depends on which catchment you stand on* — **not** as advice on where to site a gauge. |
| 27 | **Geul routing time** | **BUILD — trivial** | Five lines reading `response_lag_h` out of the pair table. Currently cited in two documents with no script behind it. |
| 28 | **Randerath reconstruction** | **DROP** | German gauge, different source, a figure in the discussion. Attractive and out of scope. |

---

## LANE D — Already retired. Confirming they stay dead.

All correctly retired; listed so no future session revives them.

| # | Analysis | Why it stays dead |
| --- | --- | --- |
| 29 | SARIMAX + Kalman detectors, `src/detectors.py` (701 lines) | The anomaly-detection phase. Wrong target: detectors look for abrupt departures; the exposure is a slow seasonal ramp. |
| 30 | Isolation Forest, ensemble agreement, synthetic injection, rolling-origin evaluation | Same phase. Sound engineering aimed at a question the chapter no longer asks. |
| 31 | RIVM cross-site transfer + ingest | Transfer to air-quality stations. No role under any current framing. |
| 32 | Distributed-lag antecedent wetness | Returned `NOT SUPPORTED` against its own preregistered rule. The null is recorded; the machinery belongs to the retired CO2-as-hydrological-proxy framing. |
| 33 | Locked direct-state regression | Two prespecified criteria were defective scaffolding, correctly withdrawn. |
| — | Weekly readiness, chapter-draft checker, run manifest, pipeline runner | Project machinery, not analysis. |
| — | Duplicate discharge ingest | Two pipelines over one endpoint had drifted apart. |

---

## Fase: what it is, and the one distinction that matters

**Fase is not a threshold the chapter chooses. It is Waterschap Limburg's
statutory escalation ladder**, defined in the
[Rampbestrijdingsplan Hoogwater Limburg 2023-2026](https://lokaleregelgeving.overheid.nl/CVDR719417/1)
as a four-colour scheme with **discharge thresholds at designated measurement
points**:

| | colour | meaning |
| --- | --- | --- |
| baseline | Groen | normal discharge |
| **Fase 1** | **Geel** | heightened vigilance |
| **Fase 2** | **Oranje** | *dreigende wateroverlast* — impending flooding |
| **Fase 3** | **Rood** | active flooding |

**Mapping verified against the data, not assumed.** Two exact matches:

- Plan: Maas at Sint Pieter escalates at 1,250 (preliminary warning), 2,000
  (regional coordination, GRIP 2), 2,600 m³/s (GRIP 4 advisory).
  Inventory: **Maas, St. Pieter — 1250 / 2000 / 2600.**
- Plan's worked tributary example: the Geul at 10.0 / 20.0 / 50.0 m³/s.
  Inventory: **Geul, Hommerich — 10.0 / 20.0 / 50.0.**

**It is already on disk.** `data/interim/waterschap_locations.csv` carries
`Fase1Value`, `Fase2Value` **and `Fase3Value`** for all 634 locations, including
all 59 discharge gauges and all 38 in the analysis set. `03_build_event_catalogue.py`
has been building p90/p95/p99 next to it. This was listed as a blocking data
request; it is a column read.

### How often it fires — and why that forces one design decision

Over the 2-year record, 38 gauges, 17,522 hours:

| | gauges reaching it | total hours | median episodes per gauge |
| --- | ---: | ---: | ---: |
| Fase 1 | 27 of 38 | 8,291 | **3** |
| Fase 2 | 14 of 38 | 782 | **0** |
| Fase 3 | **4 of 38** | 50 | **0** |
| *own p90, for contrast* | *38 of 38* | — | *26* |

Fase 1 sits at a **median p99.7** of each gauge's own record. Eleven gauges never
reach it — their Fase 1 is above anything that happened in two years.

**The pair-table consequence is severe.** Joint hours with *both* gauges above
Fase 1: **median 0**. **485 of 703 pairs (69%) have zero**; only 7% clear 100
hours. The same pairs at own-p90 give a median of 824 joint hours and 92%
usability. Swapping the mask to Fase would collapse the pair analysis from 644
usable pairs to about 51.

### Two thresholds, two jobs. Do not conflate them.

| | question it answers | requirement | use |
| --- | --- | --- | --- |
| **Conditioning mask** | which hours are hydrologically active enough that a correlation between two catchments means anything? | enough hours to estimate a correlation | **own p90** |
| **Prediction target** | did something happen that the water authority cares about? | externally defined, operationally meaningful | **Fase** |

`scope-decisions.md` §2 criticises percentiles as "self-referential and here
largely set by January 2025." **That is right about the target and wrong about
the mask.** The mask is a statistical device that is never interpreted, so
self-reference costs nothing. The two got conflated, and the fix is to separate
them rather than to replace one with the other.

**What Fase buys.** The threshold encodes *local vulnerability*, not flow
statistics — it sits at p74.8 on the Niers and p100 on the Gulp. That spread is
the authority saying these gauges carry different risk, which no percentile can
express. "A donor substitutes for a receiver's own gauge at predicting the
receiver crossing the province's own yellow threshold" is a far stronger sentence
than one about a p90.

**What it costs.** Median 3 Fase-1 episodes per gauge. Leave-one-storm-out over 3
episodes is not a validation scheme, and Fase 2/3 are out of reach entirely at two
years. This is the honest limit of the record, and it is the sharpest argument yet
for the Waterschap long-record request: the target the authority actually uses
fires three times in our window.

**One anomaly, now handled.** Niers at Kessel spends **25.2% of the record above
Fase 1** — 4,280 hours, **52% of every Fase-1 hour in the network**. A gauge in
heightened vigilance a quarter of the time is mis-thresholded, not hazardous.
`29_fase_events.py` excludes any gauge above Fase 1 for more than 5% of its
record and names it in the output. Niers is the only one. It should still be
raised with Waterschap.

### BUILT 2026-08-07 — `scripts/29_fase_events.py`

Kept separate from `03_build_event_catalogue.py` rather than folded into it.
That script serves the 3-gauge CO2 lane through the tested `src/eval.py`
percentile path; rung 3 needs all gauges on published thresholds. Overloading one
function to serve both is the drift mechanism in miniature.

Outputs `data/processed/fase_events.csv` (one row per event) and
`results/events/fase_summary.{csv,txt}` (one row per gauge × level).

Verified: hand count of hours above 10 m³/s at Geul Hommerich = 60 = script's
count; the six events it resolves are Oct 2024, Nov 2024, Jan 2025 (×3), Feb 2026.

**Across all 56 gauges holding a Fase 1 and a record:**

| | gauges reaching it | events | hours |
| --- | ---: | ---: | ---: |
| Fase 1 | 33 of 56 | 164 | 4,319 |
| Fase 2 | 17 of 56 | 38 | 466 |
| Fase 3 | 7 of 56 | 11 | 64 |

**On the 38-gauge analysis set — the numbers rung 3 has to live with:**

**115 Fase-1 events across 26 gauges**, clustering into **24 network storms**
(onsets within 48 h), of which **10 involve ≥3 gauges and 6 involve ≥5**:

    2024-10-09 (12 gauges)   2024-11-19 (10)   2024-12-22 (6)
    2025-01-05 (26)          2025-01-23 (20)   2026-02-22 (9)

**This is a better position than the docs claim.** `chapter-synthesis.md` says
"ten network alarm episodes, two of them large and both in January 2025." On
published thresholds it is 24 storms with six substantial ones spread from
October 2024 to February 2026. Leave-one-storm-out has more than two useful folds.

### Correction: Fase does NOT fix the January-2025 concentration

An earlier hypothesis in this session — that an externally-set threshold would
spread events out, because a percentile is set *by* the biggest event in the
record — is **wrong, and backwards**. Measured on the same 38 gauges, same merge
and clustering rules:

| threshold | events | gauges | storms | ≥3 gauges | **Jan-2025 share** |
| --- | ---: | ---: | ---: | ---: | ---: |
| **published Fase 1** | 115 | 26 | 24 | 10 | **42%** |
| own p99 | 452 | 38 | 122 | 32 | 27% |
| own p95 | 1,085 | 38 | 118 | 62 | 13% |
| own p90 | 1,428 | 38 | 101 | 70 | 8% |

Fase 1 sits at a median p99.96, so it is a *rarer* bar than p99 and concentrates
harder on the largest storms. The self-reference objection to percentiles is about
**interpretation** — a p90 means something different at every gauge — not about
temporal concentration.

**Design consequence.** Run rung 3 on **Fase 1 as the headline** (the
operationally meaningful target) and **p99 as a power check**. If the substitution
gap agrees under both, the Fase result is not an artifact of 115 events; if it
does not, that disagreement is itself the finding. Both use the same harness, so
this costs one extra run.

---

## Scope: "all of them? why not?"

The inventory (`data/interim/waterschap_locations.csv`, 634 rows) resolves this.

| LocationType | count | water bodies | carry Fase 1/2/3 |
| --- | ---: | ---: | ---: |
| **Drainage** (discharge) | **59** | — | all |
| **WaterLevel** | **390** | **170** | all |
| GroundWater | 185 | — | — |

**On the discharge side you are near the ceiling already**: 59 exist, 57 fetched,
42 natural, 38 after the coverage floor. "All of them" buys at most a handful
more.

**On the level side you are using none of 390.** Of those, 143 sit on 26 of the
28 tributaries already analysed; the rest are tributaries with no representation
at all. Level locations carry their own Fase thresholds in metres NAP (Geul,
Cottessen: 120.78 / 121.28), so the same externally-defined binary is available
there.

Because the target is binary, water level's incomparability across gauges — each
has its own datum and channel geometry — **stops mattering**: nothing is compared
except "is this gauge above its own published threshold."

**But the level network does not escape the rarity problem**, and the same
mask/target split applies: a p90 on level is still needed for any pairwise
statistic. Going wide on level buys *coverage of more tributaries*, not more
events per tributary.

**Three checks before committing** (none run yet): that the OData endpoint serves
*historical* water-level series and not only `CurrentValue`; that level coverage
matches discharge coverage; and that level-based Fase exceedance is not as sparse
as the discharge case. Same endpoint and same ingest script, so all three are
quick.

---

## The minimal chapter

Nine analyses. Everything else is a cut or a robustness appendix.

1. **Ingest** — Waterschap (wide), KNMI/weather, IoT.
2. **Events** — above published Fase 1. One definition, externally set, identical
   everywhere.
3. **Rung 1** — Eryilmaz replication, fold-wise scored. *Required by the
   progression.*
4. **Rung 2** — CO2 against rainfall for high-water onset. One paragraph. The
   negative that closes the Kerkrade lane.
5. **Mechanism** — pressure-only vs occupancy decomposition, ~20 lines. Converts
   the chapter's causal claim from assertion to measurement.
6. **Rung 3** — Worm/Rimburg as donor against each receiver's own gauge. **The
   chapter.**
7. **Control** — rainfall alone. Does the donor add anything?
8. **Decay** — the gap against distance, plus the per-donor distribution.
9. **Coverage and power** — stated honestly, per fold and per storm, never only
   the mean.

One currency throughout: the substitution gap in AUROC, against Eryilmaz's
inherited 0.05.

---

## What cutting buys

- **Removes 9 live analyses** and the ~2,000 lines behind them.
- **Removes 4 of the 12 code defects** the reviews raised (all in the signature
  space) without fixing anything.
- **Removes both withdrawn headline results** — the correlation-length comparison
  goes with `28_`, and the Eryilmaz sign flip is a fold-scoring fix in a script
  that stays.
- **Removes the second and third currencies**, which is the structural cause of
  the drift.
- Leaves the progression intact: Viefhues is cited as premise, Eryilmaz is
  replicated as rung 1, and the chapter's own contribution is rung 3.
