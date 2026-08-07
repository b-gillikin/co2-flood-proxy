# Chapter Review — Defensibility Pass

Reviewer read: all of `docs/`, `chapter/chapter-draft.md`, `README.md`, `src/`,
`scripts/`, `tests/`, and the artifacts in `results/`. Recomputations below were
run against `results/regionalisation/similarity_pairs.csv` as committed.

Date: 2026-08-06

---

## Verdict

The self-correction discipline here is better than most submitted dissertations.
Six data bugs found and documented, two prespecified criteria withdrawn as
defective, a headline centrality claim retracted by the same document that made
it — a committee that reads `docs/decisions.md` will trust the author.

The chapter is not yet defensible, and the reason is not honesty. It is that
**the argument is three weeks old and the evidence is three months old.** Every
finished result belongs to a question the chapter no longer asks; the one result
that belongs to the current question has a problem described below. There is no
prose, no figure set, and no committed git state.

The gap is bridgeable, but the order of work matters. Fix §1 before writing
anything, because §1 changes what the chapter's first sentence can claim.

---

## 1. The headline result is computed on the metric the repo forbids

`docs/scope-decisions.md` §2 is unambiguous:

> **Report the paired difference, not the raw median.** ... Both the full-series
> figure and the uncalibrated +0.243 are wrong numbers.

`scripts/23_catchment_similarity.py` then builds `response_matrix` from the raw
`response_corr` and runs the Mantel test on it. The distance-decay headline —
r = −0.305, p < 0.0002, 9% of variance — is the uncalibrated number.

Recomputed on the null-calibrated excess (`response_corr − response_corr_null`),
same Mantel procedure, 5,000 permutations:

| Metric | corr(distance, similarity) | Mantel p | Pairs | R² |
| --- | ---: | ---: | ---: | ---: |
| Raw best-lag correlation (as reported) | **−0.305** | < 0.0002 | 794 | 9.3% |
| Null-calibrated excess (as mandated) | **−0.143** | **0.038** | 350 | **2.1%** |

The result survives, but it goes from "clearly distinguishable from chance,
9% of variance" to "marginal at p = 0.04, 2% of variance." That is a different
sentence in the abstract, and a referee who reads §2 of your own scope document
and then reruns the script will find this in twenty minutes. Find it first.

Three things to do before quoting either number:

**(a) The null is one draw per pair.** Each pair gets a single random circular
offset. That makes `response_corr_null` extremely noisy, and noise in the
subtrahend attenuates the excess correlation toward zero. Average 50–200 offsets
per pair; −0.143 is a lower bound until you do. This is cheap and it is the
single highest-value code change in the repository.

**(b) The null resolves for only 350 of 861 pairs (59% missing).** Time-shifting
destroys the high-flow co-occurrence the mask requires, so pairs drop out
non-randomly — the surviving 350 have median distance 29.7 km against 37.2 km
for the dropouts. The null-calibrated estimate is computed on a closer-than-
average subset, which is exactly the subset where distance decay is hardest to
see. Either report a selection diagnostic or replace the circular shift with a
year-swap / phase-randomisation null that preserves the marginal tail structure.

**(c) The null itself correlates with distance at −0.097.** A pure procedural
null should be distance-independent. It is not, which means the time shift is not
destroying all shared structure — seasonality survives a circular shift. Say so,
or use a null that removes it.

**Robustness checks that came out well** and are worth reporting, since they
answer objections a committee will raise anyway:

- Spearman −0.327 (not driven by the distance distribution's right tail).
- Partial correlation controlling log joint high-flow hours: **−0.280**. Good —
  the decay is not just "distant pairs share fewer event hours."
- Dropping all pairs involving a >50 m³/s gauge (the Maas main stem): **−0.350**.
  The effect strengthens, so it is not a main-stem artifact.
- Dropping same-river pairs: −0.295. Not routing.

---

## 2. What a committee will attack, in the order they will attack it

**"Which chapter is this?"** Three framings died this year, and the surviving one
was chosen on 2026-08-06. The CO2 material is now "donor characterisation," but
`docs/chapter-synthesis.md` §1 concedes it "sits outside the spine" and that
"forcing it into the arc will read as two studies stapled together." Both
statements are in the repository, one paragraph apart in different files. Pick
one and delete the other. My read: the synthesis is right and the direction
document is rationalising. The honest structure is a short, clearly-labelled
methods-and-negative-result section on donor instrumentation (§6 below), not a
claim that CO2 is load-bearing for regionalisation.

**"Two winters."** The archive is a rolling window; earliest record 2024-08-06.
Every signature that has a seasonal term — `winter_summer_ratio` above all — has
n = 2. There is no sampling distribution. Either drop seasonal signatures from
the similarity space or state explicitly that they are descriptive only and
cannot enter an inferential axis. `docs/chapter-synthesis.md` already makes the
right admission about January 2025 supplying 58% of extreme hours; make the same
admission about the seasonal signatures.

**"How did you decide what counts as a catchment?"** `docs/scope-decisions.md`
already flags that "regex on the station name" is not the answer to give, and the
manual map pass has not happened. Do it. It is an afternoon with the 15 excluded
names and a map, and it converts a known vulnerability into a defensible
appendix table.

**"Is Rimburg special?"** Anticipated in the synthesis (repeat Q3 with every
gauge as donor) but not implemented. Rimburg is 18th of 42 on centrality, so this
is the first question after the seminar. It is also cheap — the pair table
already exists.

**"Q2 doesn't exist yet."** The synthesis says the chapter "lives or dies" on
separating donor skill from shared weather, and that radar rainfall blocks it.
Right now Q1 and Q3 are unbuilt and Q2 is unbuildable. See §7.

---

## 3. Code defects that reached results

| # | Where | What | Severity |
| --- | --- | --- | --- |
| 1 | `23_catchment_similarity.py`, Mantel input | Raw metric, not null-calibrated (§1) | **High** |
| 2 | `23_catchment_similarity.py`, null draw | One offset per pair; attenuates the excess | **High** |
| 3 | `18_precursor_skill.py:52` | `NO_PRESSURE_DROP_EPISODES = (7, 17, 18)` — hard-coded *positional* indices into a catalogue that is regenerated on every data refresh. The catalogue already grew 19 → 20 episodes; these indices now silently point at different storms than when they were chosen | **High** |
| 4 | `23_catchment_similarity.py`, `signatures()` | `flow = series.dropna()` then `flow.diff()` — differences and recession ratios are computed *across* coverage gaps. This directly violates the repo's own stated policy ("Never compute a lagged difference across a coverage gap") and it lands in flashiness and the recession constant, the same statistics the zero-sentinel bug corrupted. `best_lag_corr` does it correctly on the reindexed grid; `signatures()` does not | **Medium** |
| 5 | `18_precursor_skill.py`, block bootstrap | Blocks are drawn from the *positional* index of the dropna'd frame, so a "168-hour block" can span the 87.7-day outage | **Medium** |
| 6 | `24_fetch_estreams_attributes.py:59` | `MATCH_TOLERANCE_KM = 5.0`; `docs/scope-decisions.md` says 1.0 is correct and wider values are "an artifact of unbounded nearest-neighbour matching." Already flagged in HANDOFF, still not changed | **Medium** |
| 7 | `23_catchment_similarity.py`, `scale_log_ratio` | Signed, and the sign depends on which gauge happens to sort first. Meaningless as a symmetric pair axis; use `abs()` for the pair table and keep the signed version only for directional donor→receiver analysis | **Medium** |
| 8 | `23_catchment_similarity.py`, `baseflow_index` | It is q10/q50, a flow-duration ratio, not a baseflow index (BFI is a filtered baseflow *volume* fraction — Lyne–Hollick, UKIH). Any hydrologist on the committee will object to the name. Rename to `low_flow_ratio`, or implement a real BFI | **Medium** |
| 9 | `23_catchment_similarity.py`, `recession_constant` | Median of Q(t+1)/Q(t) truncated to (0.5, 1.0). The 0.5 floor is arbitrary and censors fast recessions — which is precisely the behaviour that distinguishes flashy tributaries. Justify the bound or fit a master recession curve | **Medium** |
| 10 | `23_catchment_similarity.py`, `signature_distance` | `sum(skipna=True)` means pairs with missing components get a systematically *smaller* distance. Currently harmless (all five components are complete for all 42 gauges) but it is a latent trap the moment a gauge fails a signature | **Low** |
| 11 | `23_catchment_similarity.py`, `same_river` | `a.split("_")[0] == b.split("_")[0]` on labels like `keutelbeek_beek_keutelbeek_beek_keutelbeek`. Works today; will not survive a refetch | **Low** |
| 12 | `best_lag_corr` mask | The mask is selected at zero lag, then `b` is shifted. So the compared hours are "both high simultaneously," but the correlation is a[t] vs b[t−lag]. Defensible, but state the choice — it is not the same as "both high at their respective lags" | **Low** |

---

## 4. Numbers that disagree with each other

These are the ones a careful reader finds, and each one costs credibility
disproportionately to its size.

**`README.md` still asserts a withdrawn claim.** The opening paragraph justifies
the donor because Rimburg "ranks second on centrality among 17 candidate gauges."
`docs/chapter-direction.md` withdrew exactly that sentence the same day (18th of
42, not 2nd of 17). The README is the first thing anyone reads.

**"91–100% coverage" is false for the current gauge set.** True for the old
17-gauge set. In the 42-gauge signature table, five gauges are below 90% and
`selzerbeek_molentak` is at **53%** (9,358 of ~17,521 hours) with mean flow
0.04 m³/s. `docs/scope-decisions.md` even notes molentak sits just under the
50%-zeros threshold and "should be checked by eye." It is still in the analysis
set. Either exclude it on a stated coverage floor or report the real range.

**The gauge count is 41, 42, and 44 in different places.** `scope-decisions.md`
alone uses "42 natural stream gauges," "41 natural gauges across 30 distinct
rivers," and "44 natural gauges" (EStreams matching) — all on the same day. The
artifact says 42. Pick one and propagate.

**`decisions.md` precursor entry is stale against its own artifact.**

| | `decisions.md` (2026-08-06) | `results/precursor/precursor_skill.txt` |
| --- | --- | --- |
| Episodes | 19 | 20 |
| Scored hours | 3,492 | 3,521 |
| rain_72h AUROC | 0.835 | 0.872 |
| CO2 residual AUROC | 0.409 | 0.453 |

The same entry carries a caveat that the bootstrap "resampled hours, which are
autocorrelated, so the stated intervals are too narrow." The code now uses a
168-hour moving-block bootstrap. The caveat is obsolete and, left in place, reads
as an unfixed defect.

**Events are percentile-based, but the methods say they are not.**
`docs/chapter-synthesis.md` specifies events as **Fase 1/2/3 exceedances** —
the water authority's published alarm thresholds — and explicitly criticises
percentiles as "self-referential and in this record largely set by January 2025."
`scripts/03_build_event_catalogue.py` builds p90/p95/p99 events, and the
precursor result rests on them. Either implement Fase thresholds or amend the
methods document.

**The +4 h Geul routing time is not in any script.** It appears in `README.md`
and `chapter-direction.md` as a measured, verified result; HANDOFF says "verified
in-session." Nothing in `scripts/` or `src/` computes it. Any number in the
chapter needs a script that regenerates it.

---

## 5. Reproducibility

**Nothing is committed.** `git status` shows the entire reframe — four new
scripts, the archive move, `chapter-synthesis.md`, `scope-decisions.md`,
`HANDOFF.md` — untracked or modified, and the last commit still says "Reframe
chapter around early-warning precursor question." `scope-decisions.md` attributes
this to an expired GitHub token. Fix the token today. A dissertation whose
provenance story is "every input is re-fetchable by script" cannot have its
scripts living only on one laptop.

**`environment.yml` has no lockfile.** `conda env create -f environment.yml`
today and in 2027 give different `statsmodels`. Export `conda env export
--no-builds` alongside it.

**The run manifest belongs to the retired programme.** `results/run_manifest.json`
was built for the frozen-snapshot machinery in `archive/`. Nothing in the current
pipeline writes provenance. Whatever survives of the freeze discipline, it needs
to cover `22`–`27` and `23` in particular.

**The test suite is the strongest part of the repo.** `tests/test_similarity.py`
is exemplary — each test names the bug it guards, including the selection-bias
test that justifies the null. Two gaps: nothing tests `signatures()` for
gap-crossing differences (defect 4), and nothing tests that the Mantel input is
the calibrated metric (defect 1). Add both; they are the two defects that reached
published numbers.

---

## 6. What the CO2 work should be in the chapter

It is a clean, quantified negative — AUROC 0.453 against 0.872 for 72-hour
rainfall, with a comparator, a false-alarm rate, and a block bootstrap. Negatives
this well-bounded are rare and it should be reported. But it answers a different
question from the rest of the chapter, and the "donor characterisation" bridge is
thin.

The defensible framing is the one `chapter-synthesis.md` already reaches for and
then abandons: **this is the substitution argument's limiting case, and it is a
methods section, not a spine.** Viefhues shows a deeply instrumented site carries
signal; Eryilmaz shows public weather substitutes for that instrumentation;
this chapter shows one instrument in that stack has no marginal value at all
over rainfall the forecaster already has, and then asks how far the substitution
extends in space. Framed that way it is a paragraph of motivation plus a short
results subsection, and nobody accuses you of stapling.

Two presentational notes:

- `pressure_level` scores AUROC 0.316 (skill, inverted) while
  `pressure_change_24h` scores 0.506 (none). That is worth a sentence — the
  *level* separates storm-season hours, the *tendency* does not. As written the
  table invites the question and does not answer it.
- The forward gain bound (`21_forward_gain_model.py`) plus its same-day
  self-correction is the most impressive reasoning in the repository: a physical
  bound, an error in the noise-floor comparison, and a corrected position that
  concedes ground. Put the corrected version in the chapter. It converts "we
  found nothing" into "we established what a capable study would need," which is
  a genuine contribution.

---

## 7. The decision that is actually blocking

`docs/HANDOFF.md` names it: **is "monitoring network design" acceptable to the
supervisor and to a committee?** Everything downstream depends on it, including
whether radar rainfall — the Q2 blocker — needs solving at all.

That question has been open since the reframe and no analysis should proceed
before it is answered. The framing is genuinely well-suited to UNU-MERIT: value
of information and hydrometric network design are policy questions, and a
socio-economic institute is a better home for them than for a hydrological
prediction contest against FloodHub. But it is a change of claim, and only the
supervisor can accept it.

One thing to bring to that conversation that the docs do not currently make:
**the weakness of the distance effect is the result.** If distance explains 2–9%
of response similarity, then siting a gauge by proximity is close to worthless
and the network-design literature has a concrete finding to absorb. That is a
better chapter than a clean decay law, and it is the one the data supports.

**Bibliography gap.** 101 entries, strong on anomaly detection, state-space
methods and the PUB/LSTM literature — and essentially empty on the literature the
chapter now sits in. No Blöschl regionalisation, no Oudin/Parajka donor-transfer
work, no Razavi & Coulibaly, no hydrometric network design or value-of-information
strand, no Mantel/spatial-dependence methodology. The retired anomaly-detection
citations (Isolation Forest, CutAddPaste, tsadams, Schmidl, Wenig) are now dead
weight. Roughly 30 entries in and 20 out.

---

## 8. Prioritised sequence

**Before writing a sentence**

1. Rerun the Mantel on the null-calibrated metric with 100+ null draws per pair.
   Report whichever number survives, with the selection diagnostic for the 350.
2. Take the "monitoring network design" question to the supervisor.
3. Commit everything. Fix the token.

**Before the analysis is defensible**

4. Manual map pass on the 15 excluded structures; publish the table.
5. Coverage floor on the gauge set; decide molentak explicitly.
6. Fix defects 3, 4, 5, 6, 7 in the table above. Add the two missing tests.
7. Every-gauge-as-donor robustness check — it will be asked.
8. Reconcile the number disagreements in §4; retire `README.md`'s withdrawn
   centrality sentence today.

**Before it is a chapter**

9. Build Q1. It is unbuilt and it gates Q2 and Q3.
10. Radar rainfall, or an explicit written decision that the chapter is Q1+Q3 on
    high-flow response and says so in the abstract.
11. Figure set from scratch. `docs/figure-inventory.md` lists 20 figures, all of
    them from the retired programme, and `results/figures/` contains only a
    manifest. Minimum: study-area map with the 42 gauges, the donor and the Geul
    chain; the similarity-vs-distance scatter with the null band; per-storm skill
    (never the mean — January 2025 is 58% of extreme hours); the precursor ROC.
12. Rewrite `docs/figure-inventory.md`, `docs/results-outline.md` and
    `docs/methods-outline.md`, or delete them. They are three superseded planning
    documents that a reader will mistake for current.
13. Delete `chapter/chapter-draft.md`. Its own header says do not build on it.
    Its value as a record is in git history; on disk it is a trap.

---

## What is already strong, and should be said out loud in the defence

- The zero-sentinel discovery, found by cross-validating one gauge against an
  independent publisher of the same instrument. That is exactly the check most
  theses skip, and the r = 0.9805 → 0.9975 verification is a clean story.
- Withdrawing the centrality-based donor justification as circular, in the same
  document that made the claim.
- Retiring two prespecified criteria after discovering they were
  scaffolding-generated rather than author decisions — and saying so.
- Bounding the gain-modulation mechanism physically instead of reporting a null,
  then correcting the bound the same day when the noise-floor argument was wrong.
- `docs/decisions.md` as an audit trail. Keep it; it is the reason a committee
  will believe the corrected numbers.
