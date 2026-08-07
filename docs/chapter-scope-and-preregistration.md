# Chapter Scope and Pre-Registration

Date: 2026-08-07. Written to be taken to the supervisor.

**Two documents in one.** Part I is a scoping proposal — what the chapter is,
why the lineage supports it, and what gets built. Part II is a **binding
pre-registration**: the design fixed in advance, before the analysis runs.

Part II is binding in the ordinary sense. Anything in it may be changed, but a
change made *after* seeing a result must be recorded here with its date and its
reason. That record is the point. This project's named failure mode is comparing
numbers produced different ways and settling specifications after seeing which
one reads better; a pre-registration is the standing defence against it.

Supersedes `docs/transfer-experiment-preregistration.md` (withdrawn 2026-08-06,
about the retired anomaly-detection lane; archived 2026-08-07).

---

# PART I — SCOPE

## 1. The two constraints

1. The sequence must be **Viefhues (2022) MSc → Eryilmaz (2025) → this chapter.**
2. The chapter must have a **transferability component.**

Everything below is the narrowest design satisfying both.

## 2. The lineage, and the bridge this chapter uses

Viefhues and Eryilmaz are both about **a house in Kerkrade and indoor CO2**.
Neither is about Maas tributaries. Any chapter on tributary transfer has to build
a bridge, and the bridge determines whether the chapter reads as one argument or
as three studies stapled together.

**The bridge previously used** — "substitution at widening scope: data source,
then variable, then space" — is elegant, but `docs/analysis-inventory.md` records
that it was invented after the fact to retro-fit a spine onto lanes that already
existed. A reader can reach that conclusion unaided, and three of its rungs are
about a house.

**The bridge this document proposes** is the same lineage read as a *progressive
devaluation of the exotic instrument*:

| | Claim | What it establishes |
| --- | --- | --- |
| **Viefhues (2022)** | A deeply instrumented site carries hydrological signal | The premise: deep instrumentation is worth something |
| **Eryilmaz (2025)** | Free public weather substitutes for that instrumentation, within 0.05 AUROC | The cheap substitute matches the expensive instrument, *in place* |
| **This chapter** | Does the instrumented site carry signal about *other* places — and if so, carried by what? | Substitution **across space**, and the answer is the ordinary gauge, not the exotic sensor |

Three properties recommend it.

**Nothing is retro-fitted.** Each step is the natural next question given the one
before. Viefhues asks whether the instrument works; Eryilmaz asks whether it is
necessary; this chapter asks whether it reaches.

**The CO2 negative result becomes load-bearing.** Indoor CO2 scores AUROC 0.46
for high-flow onset against rainfall's 0.872. Under the ladder framing that is an
embarrassment reported in one paragraph. Under this framing it is the pivot: the
lineage's own instrument does not transfer, which is precisely what motivates
asking what does.

**What is inherited is a method, not a result.** Eryilmaz supplies a falsifiable
substitution criterion with a threshold this chapter did not choose. That is a
real inheritance, and it does not require a reader to accept that indoor air
quality and catchment hydrology are one question.

## 3. What the chapter is

> Given a gauged tributary catchment, how much of what you would learn from
> instrumenting it can you get instead from a neighbouring gauge — and how far
> does that reach?

Measured as a **substitution gap in AUROC** against Eryilmaz's inherited 0.05
threshold, on the water authority's own published alarm thresholds, over the
Limburg Maas tributary network.

## 4. What the chapter is not

- **Not a monitoring-network-design chapter.** Withdrawn by the author on
  2026-08-07 and it stays withdrawn. A measurement of donor reach is an *input*
  someone else could use for siting. It appears as siting advice nowhere in the
  results. See §11 for where it does appear.
- **Not prediction in ungauged basins.** Every receiver has a gauge — that is
  what makes the ceiling *measured* rather than assumed.
- **Not a CO2 chapter.** Two pages: the inherited method, and the negative that
  motivates the pivot.
- **Not a mechanism chapter.** Viefhues established the instrumentation story.
  This chapter cites him rather than re-establishing it with three more
  instruments.

## 5. The one design decision that matters most

**All pairs as the estimate; the Worm at Rimburg as the worked case.**

The Worm is the donor because it holds the CO2 sensor and the groundwater wells.
The chapter's own finding is that the sensor carries no hydrological signal. So
the stated justification for the donor choice is instrumentation the chapter has
measured and found irrelevant, and what actually makes Rimburg a donor is a
discharge gauge that 37 other catchments also have. It sits at the **69th
percentile of transferability** (11th of 36), not mid-pack.

Running the substitution test over **all ordered (donor, receiver) pairs** fixes
this. It:

- removes a "why the Worm?" question that currently has no good answer;
- turns the per-donor spread — decay ranging **−0.58 to +0.21** across donors —
  from a robustness check into the finding;
- multiplies the inferential sample;
- and lets Rimburg be *located in a distribution* rather than asserted to be
  typical.

The Worm keeps its own section. It is the one catchment where the chapter can say
what the instrumentation actually is, and it carries the lineage. But it is the
worked example, not the design.

## 6. Sequencing

| | Step | Why here |
| --- | --- | --- |
| 0 | **Supervisor conversation** (§12) | The answer does not depend on any result below, and asking afterwards costs a rebuild |
| 1 | **Water-level feasibility check** (§7) | Determines the size of the analysis set, and therefore the power of everything after it |
| 2 | **Finalise Part II** against the resulting set | Pre-registration must be fixed before the first substitution run |
| 3 | Build the substitution harness run | The chapter |
| 4 | Reach model | The transferability component |
| 5 | Worked case, figures, limits | Writing |

## 7. The water-level check — RUN 2026-08-07

This was step 1 and it is complete. **The answer changes what it was expected to
change, in the opposite direction.**

`data/interim/waterschap_locations.csv` holds **390 WaterLevel locations**
carrying published Fase 1/2/3 thresholds in metres NAP. Applying the same
structure-name filter used for discharge leaves **272 natural stations across 125
water bodies**, of which **124 sit on 92 water bodies with no discharge gauge at
all**. Discharge gives 59 locations, 38 surviving filtering.

Because the target is **binary**, level's usual problem disappears: each location
has its own datum and channel geometry, but nothing is ever compared except *is
this location above its own published threshold*.

Twelve stations probed against the same endpoint:

| | check | result |
| --- | --- | --- |
| 1 | historical series served? | **Yes** — 12 of 12 returned records |
| 2 | coverage comparable to discharge? | **Better** — median **100%** against 89–100% |
| 3 | Fase-1 exceedance as sparse as discharge? | **Worse** — median **1** event per station against 3; **5 of 12 never reach it** |

**And the finding that was not one of the three questions: every probed station
spans 2024-08 → 2026-08.** The level network sits behind the same rolling
two-year window. Going wide on level extends the record by nothing.

**Consequence, replacing what this section previously predicted.** The expectation
was that the analysis set would exceed 100 and the power problem would ease
materially. It does not. The trade is **spatial coverage, not temporal power**:
roughly six times the receivers, about a third as many events each, and 92
tributaries currently invisible to the chapter.

That is worth having for §II.7 — more receivers means more pairs and more
short-range distance bins, which is the constraint that leaves the reach model
weakest — and worth nothing for events per catchment. **§8 stands unchanged and
is still the binding constraint.**

Two implementation caveats. Sampling rates vary across level stations (10-min,
15-min and hourly all appear in a sample of twelve), so a common grid is needed.
And level is a stage, not a flux: sound for a binary threshold crossing, wrong for
anything requiring a rate.

**Decision this now forces (§12, new question 4):** ingest the level network for
spatial coverage, or stay on 38 discharge gauges and accept a thinner reach model?
The power argument for level has gone; the coverage argument has not.

## 8. The binding constraint, stated once

On the **37** analysis gauges carrying a usable Fase 1 — the 38 less Niers,
excluded by §II.1 clause 5 — Fase 1 fires a **median of 3 times per gauge** over
the two-year record. **11 of 37 never reach it.** **42% of all Fase-1 events fall
in January 2025.** Fase 2 is reached by **13 of 37**, Fase 3 by **4 of 37**,
giving 21 and 4 events respectively across the whole network.

(Counts quoted elsewhere as "14 gauges" for Fase 2 come from the wider 56-gauge
probe in `results/events/fase_summary.txt`, which includes managed structures and
sub-floor gauges. Use the 37-gauge figures for anything inferential.)

No method repairs this. It has two consequences that shape the whole design:

- **The chapter is cross-sectional, not time-series.** The inferential unit is
  the *pair*, not the catchment. The claim is about the population of tributary
  pairs, not about forecasting any single catchment. Weaker, and it is what the
  data supports.
- **The long-record request is the chapter's most valuable open item** — not
  because more data would change a method finding, but because the target the
  authority actually uses fires three times in the window.

## 9. What never gets built

Explicitly, so it cannot return: barometric response function, tidal/earth-tide
response, groundwater characterisation (three wells), the catchment signature
space (`flashiness`, `low_flow_ratio`, `recession_constant`, `winter_summer_ratio`,
`signature_distance`), EStreams static attributes, spatial correlation length,
and the entire retired anomaly-detection programme.

That is roughly 2,000 lines and the six lanes `analysis-inventory.md` identifies
as the drift mechanism. Each produced a defensible result about *what an
instrument is doing*. None answers whether the Worm transfers.

## 10. Chapter shape

1. Lineage and the question
2. The inherited method, and the CO2 negative that motivates the pivot — **two
   pages, both**
3. Data, and why the event definition must be external
4. The substitution test across all pairs — **the chapter**
5. What governs reach
6. The Worm at Rimburg as the worked case, located in the distribution
7. Limits: two years, three events, and what a longer record would change

## 11. Where the institutional relevance goes

Maastricht requires a **valorisation addendum**. That is where the siting
implication belongs, and it is the only place it belongs.

The results measure *the information value of one gauge to its neighbours*,
expressed in skill. The addendum may say that someone allocating a monitoring
budget could use this as an input. It may not say where to put a gauge, and the
results section may not gesture at it. Designed in this way it costs a paragraph
in the introduction and a section at the end; bolted on afterwards it is the
overreach that was withdrawn on 2026-08-07.

## 12. Three questions for the supervisor

1. **Is the Kerkrade lane two pages, or a third of the chapter?** This design
   treats it as method-provenance plus a motivating negative. If a substantive
   CO2 contribution is expected, that is a conflict — the CO2 signal has now been
   measured and it does not carry (AUROC 0.46 against rainfall 0.872).
2. **Is the all-pairs design acceptable, with the Worm as worked case?** It is
   more defensible and more robust, but it changes the chapter's title framing
   from *the Worm's reach* to *donor reach, measured here*.
3. **Who is likely to sit on the assessment committee?** If it is staffed from
   UNU-MERIT's own disciplines, the hydrological content is difficult to assess
   and the socio-economic contribution is thin. Better known now than at
   submission.
4. **Ingest the water-level network, or stay on 38 discharge gauges?** Raised by
   the §7 probe. Level adds ~272 natural stations across 125 water bodies, 124 of
   them on tributaries with no discharge gauge — but events per station are ~3×
   scarcer and the record is the same two years. It buys a better reach model and
   no additional power. It is a week of ingest and QC, and it is optional.

---

# PART II — PRE-REGISTRATION (BINDING)

Fixed **before** the analysis runs. Any change after a result is seen must be
appended to §II.11 with date and reason.

## II.1 Analysis set

**Inclusion rule**, applied in this order:

1. Location type serves a discharge or water-level series over 2024-08 → 2026-08.
2. Not a managed structure — excluded by name (`stuw`, `duiker`, `inlaat`,
   `verdeelwerk`, `kanaal`, `sloot`, `gemaal`, `dijk`) or by sustained negative
   flow (>1% of observations). **The name filter requires a manual map pass
   before use**; it is a heuristic and is recorded as one.
3. Observes ≥ **80%** of the hourly grid.
4. Carries a published `Fase1Value`.
5. **Excluded** if above Fase 1 for more than **5%** of its record. This is a
   mis-thresholding rule, not a hazard rule. Niers at Kessel (25.2%) is the only
   known offender and is named in the output.

Final n is set by §7 and recorded here before the first run.

**Pair counting, stated explicitly because §5 and this clause disagreed.** The
design in §5 is over **ordered** (donor, receiver) pairs: substitution is
directional — what the Worm buys a receiver is not what that receiver buys the
Worm — and Model B contains only the donor. On 38 discharge gauges that is
**1,406 ordered pairs**, not the 703 unordered pairs used by the *symmetric*
pairwise statistics in §II.7 (distance, response correlation, scale ratio).

Both numbers are correct for their own object and neither substitutes for the
other. The substitution gap is estimated on 1,406 ordered pairs; the reach model
regresses a symmetric pair statistic on 703.

## II.2 Target

**Primary.** The receiver crosses its **published Fase 1** within *h* hours.

- Binary, one row per (receiver, hour).
- Scored only on hours where the receiver is **below** Fase 1 — a crossing, never
  a continuation.
- **Secondary, pre-specified:** the same target restricted to hours where the
  receiver is also below its **own p90**. This is the early-warning case as
  opposed to the nowcasting case, and it is the arm that matters operationally.
  Both are reported regardless of whether they agree.

**Power check.** The entire analysis is repeated with the target set at the
receiver's **own p99** (452 events against 115). Agreement across the two shows
the headline is not an artifact of a thin target; disagreement is itself the
finding. **Both are reported regardless of outcome.**

## II.3 Horizons

**h ∈ {6, 12, 24} hours. Headline h = 12.**

Fixed now, and here is the reason, so that it cannot be re-chosen later. The
target is a threshold on Model A's own series, so at h = 1–3 Model A is a
near-oracle by construction and the gap is large at every distance for reasons
that have nothing to do with transfer. Beyond ~24 h the horizon exceeds the
response time of 27–77 km² flashy catchments; median best lag between gauge pairs
is 5 h. All three horizons are reported.

## II.4 Models

| | Contents |
| --- | --- |
| **A — local instrument** | The receiver's own series: current value as a fraction of its Fase 1, and first differences at 1, 3 and 6 h |
| **B — the substitute** | The **donor's** series only, same four features, shifted by the pair's measured best lag. **Contains nothing from the receiver** |
| **C — the control** | Rainfall alone: nearest station 24 h and 72 h totals. Pre-specified as an arm, not an addition |

Estimator: `StandardScaler` + `LogisticRegression`, as inherited. Model
complexity is bounded by sample size deliberately — 24 storms does not justify
anything larger, and it would put the chapter against FloodHub on its own terrain
with a thousandth of the data.

## II.5 Validation

**Leave-one-storm-out.** A network storm is a cluster of Fase-1 onsets with
starts within 48 h. On the current 38-gauge set that is **24 storms**, of which
10 involve ≥3 gauges and 6 involve ≥5.

Storms, not catchments, are held out — holding out catchments leaves shared
forcing in the training set.

`groups` = storm is passed to `substitution_test` in every call. **Scores are
never pooled across storms.**

## II.6 Estimand and inference

**Estimand.** g = AUROC_A − AUROC_B, computed within storm and averaged.
Reported as a function of donor–receiver distance.

**Reporting, fixed now:**

- **Every** per-storm gap is reported, never only the mean. Two of the largest
  storms are both in January 2025; the folds are of very unequal weight.
- The **sign count** ("A better in k of n storms") is primary evidence.
- The interval is a **t-interval on the storm-level gaps at df = n − 1**, labelled
  as such. **Not** a percentile cluster bootstrap. With fewer than ~30 clusters a
  percentile bootstrap has severe undercoverage, and the artifact currently
  reports `[+0.009, +0.015]` from 5 folds, which reads as precision and is the
  spread of a mean of five numbers.

  **This is a code change, not just a reporting convention.**
  `src.substitution.substitution_test` currently returns a percentile cluster
  bootstrap over groups (`_interval` on resampled group means). Implementing this
  clause means returning the t-interval on `group_gaps` when `groups` is
  supplied, and it must be done **before** the first rung-3 run rather than
  applied to its output afterwards.

**Decision rule.** Inherited from Eryilmaz: **B substitutes for A if g ≤ 0.05.**
One-sided — a substitute that beats the instrument has plainly substituted.

## II.7 The reach model — the transferability component

Pair-level gap regressed on **distance**, plus exactly two further covariates,
**fixed now and not extendable**:

1. `same_river` — an upstream/downstream relation on one watercourse
2. `|log10(scale ratio)|` — magnitude only

No signature space. No static attributes. `analysis-inventory.md` names a
multi-covariate regression on signature distance as "item 17 coming back through
the window," and this clause exists to keep it out.

Inference on pairwise statistics is by **Mantel permutation over gauge labels**,
5,000 permutations. Pairs are not independent — each gauge appears in n − 1 of
them and a Pearson p-value on the pair list is wrong by orders of magnitude.

## II.8 Lag selection — IMPLEMENTED AND RUN 2026-08-07

The lag between a pair is selected on **signed** correlation, not absolute
correlation, and the **identical rule** is applied to the real and null arms.

This corrected a defect in `23_catchment_similarity.py`, which selected on
`abs(r)` and returned signed `r`. Under a time-shifted null that yields a signed
expectation of ≈ 0 (median +0.016 against a median |null| of +0.036, with 249 of
703 pairs negative), so the null subtracted almost nothing — and for 37% of pairs
the "correction" made the statistic *larger* than the raw value. See
`chapter-review-2026-08-07-third-pass.md` §1.

**Outcome, measured. The clause predicted the calibrated decay would weaken. It
strengthened.**

| | before | after |
| --- | ---: | ---: |
| median time-shifted null — the procedural floor | +0.016 | **+0.152** |
| co-response net of the null | +0.243 | **+0.106** |
| decay with distance, calibrated | −0.249 | **−0.311** |
| variance explained | 6.2% | **9.7%** |

The correction now bites as intended — **59% of the raw co-response is
procedural**, and the chapter has a measured answer to *"you searched 25 lags and
conditioned on both tails."* The decay moved the other way because the **raw**
metric changed too: under `abs()` selection a distant, unrelated pair could be
assigned a large *negative* correlation, meaningless as a similarity and diluting
the distance relationship.

**The pre-acceptance stands and was not needed.** Recording that a pre-registered
expectation was wrong, rather than quietly restating it, is the point of Part II.
Logged in §II.11.

## II.9 Pre-committed readings

Written before the answer is known, so that no outcome can be presented as more
than it is.

| Outcome | What the chapter says |
| --- | --- |
| g ≤ 0.05 at **all** distances in the network | A donor gauge substitutes for a receiver's own gauge throughout this region. Proximity is not the design variable. **Publishable** |
| g > 0.05 at **all** distances | A donor gauge does not substitute anywhere at this grain. Local gauging is not replaceable here. **Publishable** |
| g crosses 0.05 within the network span | Report the crossing distance **with its interval** |
| The interval on the crossing distance exceeds the network span | **"Not identified by this network."** Report it as such, and do not rest on a point estimate |
| Fewer than 10 storms yield scoreable folds for the median pair | The design is underpowered. Report that, not a gap |
| Model C ≈ Model B | The donor adds nothing over knowing the weather. **A real result, and the chapter reports it** |

## II.10 No-search commitments

1. Horizons are §II.3. They are not re-chosen after seeing which is
   interpretable.
2. Reach covariates are §II.7. Not extended, not swapped.
3. **One currency: the AUROC gap.** No correlation length, no KGE, no signature
   distance, no second Mantel coefficient on a different statistic. An analysis
   requiring a new currency to express its result is out of scope by definition.
4. Both target definitions (§II.2) are run and both reported, whatever they show.
5. No post-hoc subsetting of pairs, gauges or storms. Exclusions are §II.1 and
   are applied before any score is computed.
6. Every artifact states the coverage of every axis it uses **inside the
   artifact**, not in prose elsewhere. Three defects in this repository survived
   because coverage was recorded somewhere and never in the number.
7. No interpretive sentence containing a numeric value is written into a
   generated artifact as a string literal. Values are interpolated from the
   result object or the sentence lives in the docs.

## II.11 Amendments

Any deviation from Part II, with date and reason.

| Date | Clause | Change | Reason |
| --- | --- | --- | --- |
| 2026-08-07 | §II.8 | **Prediction falsified, rule unchanged.** The clause predicted the calibrated decay would weaken under signed lag selection. It strengthened: −0.249 → −0.311, variance 6.2% → 9.7%. The co-response did fall as intended, +0.243 → +0.106. | The raw metric changed as well as the null. Under `abs()` selection an unrelated distant pair could be assigned a large negative correlation, which diluted the distance relationship. The rule stands; only the expectation was wrong. Logged rather than restated. |
| 2026-08-07 | §7 | **Conclusion replaced.** The section predicted the level network would take the analysis set past 100 and ease the power problem. Probe result: history is served and coverage is better, but events are ~3× scarcer per station and the record is the same rolling two-year window. | Measured, 12 stations. Level buys spatial coverage, not temporal power. §8 remains the binding constraint. Adds a new supervisor question (§12.4). |
| 2026-08-07 | §II.1 | **Clarified, not changed.** Ordered vs unordered pair counts made explicit: 1,406 ordered pairs for the substitution gap, 703 unordered for the symmetric reach statistics. | §5 specified ordered pairs while §II.1 recorded 703 unordered. Neither number was wrong; the document did not say which applied where. |
| 2026-08-07 | §II.6 | **Flagged as unimplemented.** The t-interval requires changing `substitution_test`, which currently returns a percentile cluster bootstrap. | Recorded so the clause is not mistaken for current behaviour. Must land before the first rung-3 run. |

**Nothing in Part II has been changed after seeing a result it governs.** The
§II.8 entry records a wrong prediction, not a revised rule; the §7 entry records a
completed feasibility check, which Part I explicitly sequenced *before* Part II
was to be finalised.
