# Chapter Review — Sixth Pass, with Literature Review

Date: 2026-08-26. Follows `archive/docs/reviews/chapter-review-2026-08-08-fifth-pass.md`.

**Method.** Read `README.md`, every document in `docs/`, `src/event_study.py`,
all five live scripts, both test modules, the delivered Waterschap QC artifacts
and the LANUK feasibility artifacts. Ran the test suite, the gate audit, and
independent geometry calculations from the gauge coordinates on disk. Then ran a
literature review against the current published record and re-read the design
against what that literature says. Prior reviews were read as claims to check.

**What was executed.** `pytest -q` → 26 passed.
`31_event_study_gates.py --report-only` → FAIL, none of the six contracted files
present, as documented. All distance and grid-cell numbers below were computed
from `data/interim/waterschap_locations.csv` and
`results/feasibility/lanuk_gauge_metadata.csv`.

**Blinding.** No discharge threshold, episode count or signal contrast was
calculated. Only coordinates, record endpoints and the availability artifacts
already committed were used.

---

## Verdict

The document discipline is excellent and I am not going to spend space
re-praising it. The protocol is coherent, the gates are real, the code is small
and honest, and the repository refuses to run the analysis it wants to run. That
is all correct.

The problem is upstream of all of it. **The chapter asks a question that the
Limburg cohort cannot answer, and the reason is geometric rather than
statistical.** The available network spans 1.5–31 km. The published flood
synchrony scale for this part of Europe is 100–250 km. Every signal in the fixed
hierarchy except catchment rainfall decorrelates at scales far larger than the
whole study area, so the prespecified distance slope is pinned near zero before a
single observation is read. That is not a null result waiting to be discovered;
it is a property of where the gauges are.

The chapter is recoverable, and the recovery is already half-built in this
repository. It requires the NRW extension the protocol already permits and the
supervisor already approved — and that extension is blocked on **one unanswered
metadata email**, not on a data failure. §3 and §7 below.

Second finding: the design is a **case-crossover study** and does not know it.
Naming it connects the chapter to forty years of methodological literature on
referent selection, gives the protocol a real methods spine, and identifies one
concrete bias in the current control rule. §5.2.

Third finding: the closest published work — Tsiokanos et al. (2024, HESS), same
catchment, near-identical POT definition, five times the record length — already
answers a large part of what the local-recurrence stage would report. §5.1.

---

## 1. What pass one found sound

These are checked and I am not raising them again:

- The six-file gate contract is genuine and the audit exits nonzero. There is no
  quiet path from "data absent" to "result reported."
- `episode_table` requires adjacent timestamps to be exactly one hour apart, so a
  crossing cannot be manufactured across an omitted hour. The regression test for
  this is the right kind of test.
- `robust_standardize` has an explicit MAD-zero fallback and a not-estimable
  branch. `pressure_residuals` refuses to fit on fewer than 100 calibration hours
  and requires observed spans for every lagged difference.
- The Waterschap audit measures availability without touching thresholds, and
  reports "complete" as *four quarter-hours present*, explicitly not *valid*.
  That distinction is correct and rare.
- The literature corpus is 42 sources with structured, attributed, limitation-
  bearing notes and a 96-row evidence matrix. It is better than most published
  review sections.
- Retired work is genuinely retired: no live script fits SARIMAX, a Kalman
  filter, a classifier or a held-out fold.

## 2. The cohort is eight watercourses, and cannot become ten

From the delivered availability audit, the series passing the provisional
80%/70% rule resolve to eight *named watercourse labels*, and two of those carry
unresolved structural problems (Vloedgraaf is a split channel receiving diverted
Geleenbeek plus Rode Beek flow; Selzerbeek/Molentak is 91.6% observed zeros).
The honest count of clean, natural, distinct watercourses is **six**:

    Eyserbeek · Geleenbeek · Geul · Gulp · Voer · Worm

The provisional floor is ten. `student-next-actions.md` §2 correctly forbids
counting branches or duplicate columns to reach the number. But the document set
still frames this as "cohort unresolved pending metadata." It is not pending.
Waterschap Limburg does not operate ten discharge gauges on ten distinct natural
South Limburg tributaries. No metadata reply changes that.

**The floor is not the thing that is wrong here.** Dropping to eight would not
rescue the chapter, for the reason in §3.

## 3. The geometry finding

Coordinates for every candidate gauge are already on disk in
`data/interim/waterschap_locations.csv`. Computed great-circle distances for the
eight-label cohort:

| statistic | value |
| --- | ---: |
| watercourses | 8 |
| ordered pairs | 56 |
| minimum distance | 1.5 km |
| 25th / 50th / 75th percentile | 10.2 / 14.4 / 20.3 km |
| maximum distance | 31.0 km |

`log(1 + distance_km)` spans 0.90 to 3.47 across the entire design.

Three consequences, each fatal to a different part of the signal hierarchy:

**(a) Donor flow.** Kemter et al. (2020) define the flood synchrony scale as the
maximum radius within which at least half of stations flood at the same time. It
averages 140 km across Europe and is *lowest* — under 100 km — in exactly the
band running from northern Spain through the Alps into central Europe that
contains this study area. The entire Limburg network sits at roughly a fifth of
the smallest published synchrony scale for its own region. Donor-flow pair
contrasts will be near-uniformly high across all 56 pairs. The distance slope is
not weakly identified; it is measuring inside the plateau.

**(b) The atmospheric block.** ERA5-Land is a 0.1° product. Assigning each of the
eight gauge sites to its nearest cell gives **five unique cells, with four of the
eight sites sharing the single cell at 50.8 N, 5.9 E**:

| site | nearest ERA5-Land cell |
| --- | --- |
| Eyserbeek / Eys | 50.8 N, 5.9 E |
| Geul / Cottessen | 50.8 N, 5.9 E |
| Gulp / Azijnfabriek | 50.8 N, 5.9 E |
| Selzerbeek / Molentak | 50.8 N, 5.9 E |
| Geleenbeek / Brommelen | 50.9 N, 5.9 E |
| Voer / Mesch | 50.8 N, 5.7 E |
| Worm / Rimburg | 50.9 N, 6.1 E |
| Vloedgraaf / Nieuwstadt | 51.0 N, 5.9 E |

Twelve of the 56 ordered pairs therefore have receiver and donor drawing
**identical** temperature, humidity and pressure values. For those pairs the
donor contrast is not similar to the local contrast — it *is* the local contrast,
by construction. Those twelve points sit at the short-distance end and pin the
regression intercept with zero within-group variance. Catchment centroids will
shift assignments slightly but will not change the structure. §6 of the protocol
says to "record shared cells as shared exposures"; recording is not enough, since
a shared cell makes the pair contrast a mechanical identity rather than an
observation.

Independently, surface pressure decorrelates at synoptic scale. A pressure
distance slope over 31 km is a tautology whatever the grid.

**(c) Catchment rainfall is the one signal at the right scale.** Published radar
climatology for Germany reports that short-duration convective rainfall affects
"a few tens of km or less" while frontal systems act over 100 km or more. A
1.5–31 km range is genuinely informative for hourly convective catchment
rainfall — and only for that. So the design's distance axis is correctly scaled
for one of its six fixed signals and structurally uninformative for the other
five.

**(d) The units are nested.** Gulp, Eyserbeek and Selzerbeek all drain into the
Geul, and the location table even contains a gauge named *"Geul bij samenvloeiing
Geul Gulp Selzerbeek Eyserbeek."* Geul/Cottessen sits above that confluence, so
it is not downstream of them, but four of the eight units are sub-catchments of
one 344 km² basin lying within 7 km of each other. Short distance and
same-basin are almost perfectly confounded. The prespecified continuous slope
is, in substance, a two-level same-basin/different-basin contrast with eight
units — presented as a continuous distance relationship.

## 4. Literature review

Twelve searches; the findings that bear on the design.

**4.1 Spatial synchrony scale.** Kemter et al. (2020, *GRL*) — flood synchrony
scale averages 140 km in Europe, under 100 km in the central-European band
containing Limburg, exceeding 250 km in the northeast; scales grew ~50% over
1960–2010. Already cited in the corpus as `KemterEtAl2020` under Q12, but the
note records the *method* and not the *magnitude*, so the number never reached
the design. This is the single most consequential omission in the review.

**4.2 Rainfall spatial extent.** German radar climatology (16 years, 1 km):
convective short-duration rainfall over a few tens of km; frontal over 100 km+.
Supports §3(c). The corpus covers RADOLAN product characteristics (Q20,
`WinterrathEtAl2018`, `BartelsEtAl2004`) but has no evidence question for
*rainfall spatial correlation length*, which is the quantity the chapter's
rainfall distance slope actually estimates.

**4.3 The nearest published comparator.** Tsiokanos et al. (2024, *HESS* 28:
3327–3345), already in the corpus, is closer to this chapter than the corpus
note conveys:

| | Tsiokanos et al. 2024 | this chapter, local stage |
| --- | --- | --- |
| catchment | Geul, 344 km² | Geul + 7 neighbours |
| record | Meerssen 15-min, **1970–Aug 2021** | 2010–2025 |
| outcome | POT at **Q99**, ≥5-day separation | p99 upward crossing, 72 h merge |
| precursors | multi-day rainfall, API antecedent wetness, compound | 24/72 h rainfall, T, RH, pressure |
| finding | daily extremes insufficient; **compound heavy-rain-on-wet dominant**; 75% of annual peaks preceded by multi-day rain; **78% of peaks Nov–Apr against 75% of rainfall extremes in summer** | — |

The chapter's stage-one deliverable ("which public signals recur before high
water in these catchments") substantially overlaps a two-year-old HESS paper on
the same water, using a longer record and an almost identical event definition.
The chapter's genuine additions over it are the multi-watercourse replication and
the matched-control design. Those need to be stated as the contribution; "which
signals recur" on its own is largely answered.

Two operational facts fall out of the same paper: the recorded July 2021 Geul
peak of ~55 m³/s is reconstructed at >80 m³/s, so the delivered July 2021 cells
are known to be biased low by roughly a third — which converts
`data-requests.md` §5's censoring warning from a caution into a measured number.
And **Waterschap Limburg supplied that team 15-minute Meerssen discharge from
1970**, while the delivery here starts in 2010. Forty additional years exist.

**4.4 The design has a name.** The estimator — compare exposure in a hazard
window before each event against exposure in matched referent windows for the
same unit — is a **case-crossover design** (Maclure, 1991), the standard tool in
environmental epidemiology for short-term exposure and rare events. The protocol
reinvents it without naming it and therefore inherits none of its literature.
That literature is directly binding; see §5.2.

**4.5 The CO2 mechanism is well supported, and the chapter regresses it away.**
Barometric pumping as the control on gas emission from abandoned mine workings is
established (Forde et al. 2019 is already in the corpus under Q04); pressure
drops are the primary driver of gas outflow from closed mines, and emissions lag
pressure change. The Dutch official *Na-ijlende gevolgen steenkolenwinning
Zuid-Limburg* programme documents elevated CO2 and depressed O2 where workings
are incompletely flooded, and recommends additional monitoring. Meanwhile a
search for indoor air-quality sensors used as hydrological or subsurface proxies
returns nothing. That combination — established mechanism, official regional
hazard concern, no published sensing literature — is the one genuinely open niche
in this dissertation's territory, and the current design treats it as a
conditional appendix whose central variable is a nuisance to be regressed out.

## 5. Pass two: what the literature exposes in the design

### 5.1 The estimand and the geometry disagree

Covered in §3. Restated as a design statement: the protocol's own §9 disclaimer
("a descriptive network association rather than a causal effect of distance") is
honest but insufficient. The problem is not that the slope might be
misinterpreted causally; it is that at this geometry the slope for five of six
signals has no room to vary.

### 5.2 Referent selection is the known-biased variant

`quiet_control_times` ranks candidates "by absolute time from the event, then by
timestamp; take the first five." This is a nearest-neighbour referent scheme, and
it is *non-localizable* in the case-crossover sense: the referent set is a
function of the observed event time. That class of scheme is exactly what the
overlap-bias literature (Janes/Sheppard/Lumley 2005; Whitaker et al. 2007) shows
produces biased estimating equations, and the recommended remedy — **time-
stratified referent selection**, where referents are fixed a priori by calendar
stratum independently of when the event occurred — is a drop-in replacement here.
The protocol already matches on calendar month and UTC hour, so it is most of the
way there; the fix is to take *all* eligible same-month-same-hour times in a
predeclared stratum rather than the five nearest.

This matters more than usual because every signal in the hierarchy is strongly
seasonal *and* strongly trended within season, which is precisely the condition
under which nearest-referent selection is biased.

There is also a second, larger problem in the same function. Controls must be
more than seven days from **any receiver p95 exceedance** and **any regional
storm onset**. A p95 threshold on an hourly series is exceeded ~438 hours per
year, clustered in the wet season, and each such hour blackballs a 15-day window.
In a winter month, plausibly all candidate hours in most years are excluded, and
events with fewer than three controls are dropped. Tsiokanos et al. report 78% of
Geul annual peaks occur November–April. **The control rule may therefore
preferentially delete the majority of the event population, leaving a
summer-weighted sample, and nothing in the current audit would reveal it.** This
is measurable today and is the highest-value blinded check available.

### 5.3 The estimand is spatial; the uncertainty is temporal

Uncertainty comes from resampling complete regional storms. That handles temporal
dependence. It does nothing about the dependence among the 56 (or 506) ordered
pairs, which are generated by only 8 (or 23) underlying watercourses — each gauge
appearing in 2(n−1) pairs. An OLS interval over 56 rows backed by 8 units, with
intervals from a time-axis bootstrap only, will read as far more precise than the
network supports. Leave-one-watercourse-out is an influence diagnostic, not an
uncertainty estimate, and the protocol correctly says so — which leaves the
spatial axis with no uncertainty treatment at all. A cluster bootstrap over
watercourses, alongside the storm bootstrap, closes this.

### 5.4 Smaller items

- `data-requests.md:151` attributes the HESS 2024 Meerssen precedent to
  "Tsakiris et al."; the paper is **Tsiokanos et al.**, correctly cited
  everywhere else. It appears in the text used to justify a data request to a
  provider, so it should be right.
- `scope-decisions.md` §19 states flatly that the LANUK archive "is not a
  qualifying cohort." `lanuk-feasibility.md` is more careful and says the density
  result cannot be interpreted "before LANUK clarification." The definitive
  wording in the live decision list is not supported by the audit it summarises.
  See §7.
- `data/processed/` still holds `sarimax-anomalies.csv`, `kalman-innovations.csv`,
  `iforest-scores.csv`, `hourly_soft_labels.csv` and a `transfer-anomalies/`
  tree, and `results/eryilmaz/` still holds `fold_auroc.png` and `fold_metrics.csv`
  — outputs of designs the inventory lists as removed. The code is gone; the
  artifacts that could be mistaken for chapter results are not. They are
  gitignored, so this is local hygiene, but a reader with the working tree sees
  them.
- There is **no live chapter text**. `archive/chapter/chapter-draft.md` is
  explicitly superseded. Five prior reviews and three framings in, the manuscript
  is at zero words, and roughly 2,000 lines of `docs/` restate one design across
  six documents with substantial overlap between `README`, `chapter-synthesis`,
  `scope-decisions`, `HANDOFF` and `supervisor-decision-memo`.

## 6. Would we do this chapter from scratch?

Not this one, not at this cohort. Two of the three things that make it publishable
are missing at the current geometry, and the third is partly pre-empted:

- the distance-decay estimand is unidentifiable inside 31 km for donor flow and
  the atmospheric block;
- the local-recurrence estimand overlaps Tsiokanos et al. 2024 on the same water
  with a fifth of the record;
- the distinctive asset — indoor CO2 at a post-mining site, which nobody has
  published on — is a conditional appendix that currently does not clear its gate.

Three ways forward, in the order I would rank them.

**Option A — same question, correct network.** Extend to NRW, which the protocol
already permits and the supervisor already approved (memo item 3). This is the
recommendation. Detail in §7.

**Option B — same data, honest estimand.** Drop the distance slope. Reframe as
cross-watercourse *replication* of the case-crossover contrast: do the same
public precursors recur across eight neighbouring small tributaries, and does the
answer hold across seasons? Report the watercourse forest plots, drop the
regression, and add the season stratification that Tsiokanos identifies as the
dominant structure and that the current design only matches on and never reports.
Deliverable with data in hand; a smaller but defensible chapter; and the
case-crossover framing plus the seasonal contrast is a real methodological
contribution to small-catchment hydrology. This is the fallback if §7 fails.

**Option C — the chapter the literature is actually missing.** Post-mining indoor
CO2 in South Limburg housing and its meteorological and hydrological controls:
established mechanism (barometric pumping, mine-water rebound), an official Dutch
hazard programme calling for exactly this monitoring, and no competing sensing
literature. It is the best chapter of the three and the only genuinely novel one.
It is also not deliverable on the current record — one house, one undocumented
sensor, unresolved ABC lineage. It would need either a small deployed sensor
array or access to the provincial mine-gas monitoring network, and a year. Worth
raising with the supervisor as a *later* chapter rather than discarding, because
the Viefhues → Eryilmaz → CO2 sequence points at it and this chapter currently
inherits that framing without being able to deliver on it.

## 7. The unblocking move

The German extension is not a failed route. It is an unanswered email.

From `results/feasibility/lanuk_gauge_metadata.csv`, the held archive contains
**16 verified named tributary watercourses** after excluding the Rur and Niers
main stems and the Nierskanal. Ten of them carry records that start before 2010
and run to mid-2024 or later. Combined with the eight Limburg labels:

| cohort | watercourses | ordered pairs | distance range | median | pairs >50 km |
| --- | ---: | ---: | ---: | ---: | ---: |
| Limburg only | 8 | 56 | 1.5–31.0 km | 14.4 km | 0% |
| Limburg + NRW (records through 2024-06) | 18 | 306 | 1.5–106.2 km | 29.8 km | 22% |
| Limburg + all verified NRW tributaries | 23 | 506 | 1.1–121.0 km | 38.3 km | 35% |

The middle row clears the 10-watercourse floor, keeps 15 common years including
July 2021, and — decisively — **reaches the 100 km synchrony scale**, so the
distance slope has somewhere to go. It also spreads across many ERA5-Land cells,
removing the shared-exposure identity in §3(b).

What stands between here and that row is one thing. The LANUK verified-discharge
CSVs carry irregular timestamps, and the audit therefore counts an hour observed
only when a value falls inside it. Under that rule most gauges show 55–75%
coverage and fail the density gate. If the archive omits unchanged values or
implies a hold-forward interval — which the HYGON data-model note neither
confirms nor denies — true coverage is near complete and the density failure
disappears. The feasibility document says exactly this. `scope-decisions.md` §19
does not.

So: **the viability of this chapter's headline estimand currently rests on a
single unanswered question about timestamp semantics.** That should be the top
line of the next supervisor conversation, not the watercourse floor.

## 8. Gaps, ranked

1. **Distance range does not reach the scale of the phenomenon.** §3. Blocks the
   primary estimand.
2. **LANUK timestamp semantics unresolved**, and the live decision list records
   the route as failed rather than pending. §7. This is the unblock.
3. **Control availability by season never measured.** §5.2. Could be silently
   deleting the majority of events. Measurable now.
4. **Referent selection is the biased variant.** §5.2. Cheap fix, real bias.
5. **Shared ERA5-Land cells make 12 of 56 pair contrasts identities.** §3(b).
6. **No spatial-axis uncertainty.** §5.3.
7. **Novelty overlap with Tsiokanos et al. 2024** unaddressed in the synthesis.
   §4.3.
8. **Waterschap archive extends to 1970**, delivery starts 2010. §4.3.
9. **Cohort caps at eight and the docs still call it unresolved.** §2.
10. **No chapter text, six overlapping design documents, three framings.** §5.4.

## 9. Next steps, in order

**Now, no new data needed**

1. Send LANUK the timestamp-semantics question as a single, narrow, answerable
   request: *do the verified-discharge exports omit unchanged values, and is an
   absent timestamp a gap or a hold-forward interval?* Everything else waits on
   this.
2. Run the blinded control-availability audit: for each candidate receiver, by
   calendar month, how many events retain ≥3 controls under the current p95 ±7-day
   and storm-onset exclusions. Report the retained-event count by season. Use
   event counts and timestamps only — the supervisor memo §5 explicitly authorises
   this content, and it does not touch signal contrasts. **The repository has been
   blocking itself on an audit it is permitted to run.**
3. Commit the geometry table in §3 and §7 to the repo. It is blinded input
   evidence and it is the substance of the next supervisor decision.
4. Fix `data-requests.md:151` (Tsakiris → Tsiokanos). Soften `scope-decisions.md`
   §19 to match `lanuk-feasibility.md`.

**Next supervisor conversation — reframe the agenda**

5. Lead with §3, not with the watercourse floor. The question is not "may we drop
   from 10 to 8"; it is "the Limburg network is 31 km wide and the phenomenon has
   a 100 km scale — do we extend to NRW, or do we change the estimand?" Bring
   Option A and Option B and ask for a choice.
6. Report the retirement of the held-out fold, still outstanding from the last
   round.
7. Raise Option C as a candidate *later* chapter, so the CO2 thread has a home
   and stops distorting this one.

**Once the route is chosen**

8. If NRW is in: build the joint NL+NRW cohort, re-run the gate against the real
   combined geometry, and only then commission catchment polygons and RADOLAN —
   they are the most expensive remaining inputs and their scope depends entirely
   on the cohort.
9. Switch referent selection to a time-stratified scheme and add a watercourse
   cluster bootstrap alongside the storm bootstrap. Both are small edits to
   `src/event_study.py` and both should land before lock.
10. Add the case-crossover literature to the corpus as a new evidence question
    (design, referent selection, overlap bias, shared exposures) and add a second
    for rainfall spatial correlation length. Then rewrite the synthesis'
    contribution paragraph to position against Tsiokanos et al. 2024 explicitly.
11. Ask Waterschap for pre-2010 Meerssen and any other tributary history; cite the
    Tsiokanos precedent, correctly attributed.
12. Start the manuscript's methods and study-area sections. They do not depend on
    outcomes, and three framings in, the absence of prose is now itself a risk.

---

## Sources consulted in the literature review

- Kemter, Blöschl, Marwan, Plavcová, Hall, Merz — flood synchrony scale, Europe:
  <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020GL087464>
- Brunner et al., spatial dependence of floods shaped by meteorological and
  land-surface processes: <https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2020GL088000>
- Tsiokanos, Rutten, van der Ent, Uijlenhoet, Geul flood drivers and trends,
  HESS 28:3327: <https://hess.copernicus.org/articles/28/3327/2024/>
- Characteristic spatial extent of hourly and daily precipitation in Germany from
  16 years of radar data: <https://www.schweizerbart.de/papers/metz/detail/28/91763/Characteristic_spatial_extent_of_hourly_and_daily_precipitation_events_in_Germany_derived_from_16_years_of_radar_data>
- Janes, Sheppard, Lumley, overlap bias in the case-crossover design:
  <https://pubmed.ncbi.nlm.nih.gov/15546133/>
- Whitaker et al., case-crossover methods for environmental time series:
  <https://onlinelibrary.wiley.com/doi/10.1002/env.809>
- Insight into bias in time-stratified case-crossover studies:
  <https://arxiv.org/pdf/2001.06606>
- Optimising the case-crossover design for shared exposure settings:
  <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7374809/>
- Forde et al., barometric pumping controls fugitive gas emissions:
  <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6773692/>
- Meteorological factors influencing gas emissions from an abandoned coal mine
  shaft: <https://www.mdpi.com/2071-1050/17/9/3875>
- Na-ijlende gevolgen steenkolenwinning Zuid-Limburg:
  <https://zoek.officielebekendmakingen.nl/blg-795996.pdf>
- JCAR ATRACE rapid assessment, Geul river basin:
  <https://www.jcar-atrace.eu/publications/4-rapid-assessment-geul-river-basin-2022.pdf>
