# Chapter Review — Third Pass, Independent

Date: 2026-08-07. Follows `chapter-review-2026-08-06.md`, `chapter-review-2026-08-07.md`
and the second-pass findings in `HANDOFF.md`.

**Method.** Prior review documents were read as *claims to be checked*, not as
findings to summarise. Every number below was re-derived from code or from the
artifact on disk, and the derivation is given so it can be disputed.

**What could not be done.** The test suite was not run this pass — the sandbox
used for execution lost its disk partway through and did not recover. Every
claim below therefore rests on reading code and artifacts, never on execution.
Where a claim would need a run to settle, it is marked **[unverified]**. The
reported 85-passing suite is taken on trust.

---

## Verdict

The self-review culture here is unusually good and the last three cycles caught
real errors. This pass does not overturn that. It finds **one substantive
methodological problem that all three prior reviews missed**, and it disagrees
with the project on one question of scope.

The methodological problem is §1. It matters because it is the answer to the
objection a referee is most likely to raise, and the answer does not work.

The scope disagreement is §5. `analysis-inventory.md` is right that the chapter
is overburdened and right about most of what to cut. It does not go far enough,
and one of its recommendations adds work to the lane it is closing.

---

## 1. The null calibration does not remove the bias it was built to remove

**This is the finding of this pass.** It is new; it is not in either prior review
or in the HANDOFF.

### The claim under examination

`scope-decisions.md` §2 states the problem correctly: selecting the maximum
correlation across 25 candidate lags inflates correlation on its own, and
conditioning on both series exceeding their own p90 selects for co-movement by
construction. It mandates a time-shifted null to remove both, and forbids quoting
the raw figure:

> Both the full-series figure and the uncalibrated +0.243 are wrong numbers.

### Why the correction is inert

`scripts/23_catchment_similarity.py:225` selects the lag on **absolute**
correlation:

```python
if np.isnan(best_r) or abs(r) > abs(best_r):
    best_r, best_lag = r, lag
```

and then returns the **signed** `r`. Under the time-shifted null the true
correlation at every lag is approximately zero, so the search returns the largest
*magnitude* noise excursion with a roughly symmetric sign. The expected value of
the null is therefore near zero **in signed terms**, while the bias it exists to
measure lives entirely in the magnitude.

Three independent measurements on `results/regionalisation/similarity_pairs.csv`
confirm this:

| Measurement | Value | What it means |
| --- | ---: | --- |
| Median `response_corr_null` | **+0.016** | the "procedural floor" is ≈ 0 |
| Pairs with a **negative** null | **249 of 703 (35%)** | the null's sign is near-symmetric |
| Mantel, raw − Mantel, calibrated | **−0.264 vs −0.249** | the correction moves the headline by 0.015 |

And the consequence for the co-response headline:

> `scope-decisions.md` forbids quoting the raw median **+0.257** and mandates the
> calibrated **+0.243**. The two differ by **0.014**.

### Two things follow

**(a) The "raw and calibrated now agree" result is being read backwards.**
`scope-decisions.md` and the 08-07 review both treat the convergence of −0.264
and −0.249 under many draws as evidence that the correction is now reliable. The
more parsimonious reading is that **the correction converges to no correction**.
With one draw the null was a single max-|r| pick — a high-variance, mean-zero
quantity — entering as noise in the subtrahend, which attenuated the
distance correlation to −0.143 by ordinary regression dilution. Averaging 50
draws shrinks that noise toward its own mean of ≈ 0, so the calibrated metric
converges to the raw metric. The 08-07 review's diagnosis of *why* −0.143 was
wrong is correct; the inference that the multi-draw number is therefore a
bias-corrected estimate does not follow.

**(b) For a third of pairs the correction runs the wrong way.** Row 4 of
`similarity_pairs.csv`: `roer_julich` × `rode_beek_susteren`, raw r = **+0.383**,
null = **−0.288**, excess = **+0.671**. A bias correction that makes the
statistic *larger* than the uncorrected value, for 35% of the sample, is not a
bias correction.

### What survives, and what does not

**Survives.** The distance-decay finding itself. The Mantel on the raw metric is
−0.264, p = 0.0008, on 644 pairs, and the gauge-label permutation correctly
handles pair dependence. That is a real, defensible, weak effect.

**Does not survive.** The claim that the decay is measured *net of procedural
bias*, and the instruction to prefer +0.243 over +0.257 as though they were
materially different numbers. The chapter currently has no working defence
against "you searched 25 lags and conditioned on both tails, so you manufactured
this." That is the first question a hydrology referee asks about a best-lag
event-conditioned correlation.

### Fix

Apply one rule to both arms. Either:

- select the lag on **signed** `r` in the real and null arms (physically right —
  two catchments co-responding should be positively correlated), or
- compare **|r|** against **|r_null|** throughout.

Under either, the null becomes strongly positive, the correction bites, and
`+0.243` becomes a number that differs from `+0.257` enough to be worth the
sentence defending it. Expect the calibrated decay to weaken. **[unverified —
needs a rerun]** That is the honest outcome and it is still publishable: a weak
decay, correctly bounded, beats a moderate one that a referee dismantles.

---

## 2. Interpretive prose is hard-coded into generated artifacts

`scripts/03_eryilmaz_replication.py:307-312` writes these as **string literals**
into `results/eryilmaz/auroc.txt`:

> "The two agree at +0.012 and -0.012 ... forward chaining scores HIGHER within
> fold (A 0.900 vs 0.886) ... an earlier reading of 0.141 was the pooling
> artifact above."

and at lines 290-294, "on (b) it reads -0.088 against a within-fold -0.012."

None of these are computed. They currently happen to match the block printed
directly above them. **On the next data refresh they will not, and the artifact
will contradict itself in the same file.**

This repository has correctly named its recurring failure mode as *comparing a
number against another number produced a different way*. This is the limiting
case of it: a number compared against a number that is not produced at all. It
is also the cheapest thing in this review to fix — interpolate the values from
`result`, or move the sentences to the docs where a human owns them.

**Related, same file.** The headline at the top of `auroc.txt` — `AUROC gap
(A - B): 0.011716` and the `Replication check` — is the **pooled** cross-fold
AUROC from `fit_cv_predictions`, the operation the bottom half of the same file
declares an artifact. The defence (all five random folds cover the same period)
is sound, but the file states one rule and then opens by breaking it. Either
print the within-fold figure at the top or add the one-line reason there.

---

## 3. The reported confidence intervals are not intervals

`substitution_test` with `groups` runs a percentile cluster bootstrap over the
groups. In `auroc.txt` that is **n = 5 folds**.

A percentile bootstrap over 5 clusters has at most 126 distinct resamples and
severe undercoverage. The random-fold line reads:

```
gap (A - B)   +0.012   95% CI [+0.009, +0.015]
```

That interval looks like high precision. It is the spread of a mean over five
numbers ranging +0.007 to +0.017. It measures **fold-to-fold consistency**, not
sampling uncertainty about a population gap — and it is the version the documents
quote.

The artifact already prints the honest evidence on the next line: *per-group gap:
min +0.007, median +0.013, max +0.017; A better in 5/5*. That sentence is the
result. Recommendation: promote it, and either drop the CI or replace it with a
t-interval on the fold gaps at df = n − 1 and label it as such.

**This gets worse, not better, at rung 3.** Leave-one-storm-out over 24 Fase-1
storms with 42% of events in January 2025 gives a cluster bootstrap over 24 wildly
unequal units. `chapter-synthesis.md` §"Power, honestly" already says report per
fold, never the mean. Make that binding on the *interval* too, not just the point
estimate.

**A related gap in the tests.** `tests/test_substitution.py` is good, but nothing
in it can catch the known positional-block defect, because the harness takes no
timestamp index — the defect is currently untestable by construction. That is
worth saying out loud when the fix is scheduled.

---

## 4. Rung 3 has a degeneracy that should be settled before it is built

The design in `chapter-synthesis.md` §2.2:

- **Model A** = the receiver's own gauge (persistence plus its own recent history)
- **Target** = the receiver crossing its own published Fase 1 within *h* hours

The target is a threshold on Model A's own series. At short *h*, A is a
near-oracle **by construction** — a gauge two hours below its Fase 1 threshold
predicts crossing it almost perfectly. So:

- at small *h*, the gap is large at every distance, and §2.4's headline (*the
  distance at which the gap exceeds 0.05*) is **0 km everywhere**;
- at large *h*, A degrades toward climatology and the gap collapses toward zero
  for reasons that have nothing to do with the donor.

The headline is therefore a function of *h*, and there is an intermediate range
where it is informative. **Fix the horizon, or the reported set of horizons,
before running.** Selecting *h* after seeing which value gives an interpretable
crossing distance is the same species of error as the three this repo has already
caught, and it is the one a committee is best equipped to spot.

The 08-07 review's §6 asks the right question ("is it estimable on this
network?") and pre-commits to *no crossing within the span of this network* as a
publishable answer. Extend that pre-commitment to the horizon.

---

## 5. Scope — where this disagrees with `analysis-inventory.md`

`analysis-inventory.md` is the best document in the repository. Its diagnosis
(every phase ended by characterising an instrument; the chapter keeps changing
currency) is correct and its cut list is right. Three places it does not go far
enough.

### 5a. The mechanism decomposition should not be built

The minimal chapter's item 5 — the ~20-line pressure-vs-occupancy decomposition —
adds a **new analysis to the Kerkrade lane at the same moment the inventory
closes that lane**. It is also unnecessary. The chapter's finding is that indoor
CO2 carries no precursor skill. The chapter does not need to establish *why* CO2
moves; it needs one sentence establishing that it moves for a non-hydrological
reason, and the numbers for that sentence already exist (pressure-only 0.872/0.864
against hour-of-day 0.554, `HANDOFF.md` §(c)).

Report the numbers. Do not build the script. Building it re-opens the lane and
invites the "so what does drive it?" question that the chapter has no reason to
answer.

The one thing that **must** change is the prose: "indoor CO2 is autocorrelated
through occupancy and ventilation" is refuted by the repo's own decomposition and
appears twice in `chapter-synthesis.md` (lines 129, 271). That is a rewrite, not
an analysis.

### 5b. Three of nine analyses are still about a house

The inventory's own sentence — *"three of its rungs are about a house in Kerkrade
and only one is about Maas tributaries"* — is the diagnosis. Its remedy keeps
items 3, 4 and 5, all Kerkrade. With 5a cut that becomes two, which is the right
number: rung 1 is required by the supervisor's progression, rung 2 is the negative
that closes the lane. Neither needs more than a paragraph.

### 5c. Do not let the ladder become the contribution

The substitution ladder is a genuine design and the 08-07 review is right to
praise the harness. But the inventory states plainly that the ladder was
*"invented after the fact to retro-fit a spine onto lanes that already existed."*
Both can be true, and a committee may reach the second reading on its own.

The safe framing: rung 3 is the chapter. Rungs 1 and 2 are a replication and a
negative, reported because the progression requires them and because they set the
currency. Presenting the three as an *arc* asks the ladder to carry weight it was
not built to carry, and invites exactly the question the inventory is worried
about.

### 5d. Where the chapter actually stands

Worth stating plainly, because no document does:

**The chapter has no positive result about Maas tributaries yet.** What stands is
inherited (Eryilmaz), negative (CO2), or descriptive (distance decay, 6.2% of
variance, donor-dependent from −0.58 to +0.21). Rung 3 is unbuilt.

If rung 3 returns *the donor substitutes everywhere* or *nowhere*, the chapter is
a well-executed negative-results chapter with one descriptive figure. That is
survivable and honest. **It should be planned for now.** The consequence:
`HANDOFF.md`'s next-action 4 — take "is regional scope transfer plus a
negative-results battery enough for Chapter 1?" to the supervisor — should be
**action 1, before rung 3 is built**. The answer to that question does not depend
on rung 3's sign, and the cost of asking after is a rebuild.

---

## 6. Confirmed defects, with severity revised

| # | Defect | Status this pass |
| --- | --- | --- |
| 1 | Positional bootstrap blocks span coverage gaps | **Confirmed, live in two places.** `substitution._block_indices` and `18_precursor_skill.block_bootstrap_auroc`. Worse than described: `_clean` compresses out non-finite rows *first*, so block contiguity is in the compressed index, not the calendar. The precursor CIs (rain_72h [0.783, 0.933]) are not what they claim, and "about 20 independent blocks" overstates the effective sample on a 31%-complete record |
| 2 | `fetch_elevations` cache short-circuit | **Confirmed** (`23_:141-144` returns the whole cache if *any* label resolves). Artifact shows elevation for 16 of 38. Correctly **downgraded** — elevation only served the cut signature space. Leave it; do not spend the API call |
| 3 | `pytest` at repo root fails on `archive/tests/` | **Confirmed** — `pyproject.toml` has no `[tool.pytest.ini_options]`. One line, named in the HANDOFF, still unapplied |
| 4 | `knmi_pressure_pairs` silently uses 5 of 7 stations | Not re-checked; `28_` is cut, so this dies with it |

### New, lower severity

- **`18_precursor_skill.episodes()` selects on IoT coverage** (≥ 60 of 72
  pre-onset hours). The nine surviving "barometrically clean" episodes are **all
  July–October**. So the test designed to isolate non-barometric CO2 signal runs
  entirely in the season when barometric forcing is weakest — which the repo's own
  seasonal result confirms (r = −0.268 JJA against −0.505 MAM). The negative result
  is still correct; the reason given for it is not the operative one. One sentence
  in the methods.
- **`precursor_skill.txt`'s reading note points at the weaker pressure
  predictor.** It says CO2 must beat `pressure_change_24h` (0.506, no skill), but
  `pressure_level` scores 0.316 — a strong inverted signal, and the real barometric
  comparator. The note understates its own confound.
- **`18_`: "barometrically clean" is defined as `first value − minimum`**, not
  `max − min`, over the 24 h window. If pressure rises then falls, the fall is
  understated. Defensible, but it is the rule that defines the episode set and it
  is not the obvious definition.
- **`features.antecedent_precipitation_index` fills missing rain with 0**, which
  reads an outage as a dry hour and violates the repo's own "coverage gaps are
  never interpolated" convention. Only reached by the archived distributed-lag
  work and by `test_io_data.py`. Note it or delete the function.
- **`src/io_groundwater.py` has zero importers** after the groundwater lane was
  cut. It should follow the lane into `archive/`.

---

## 7. Provenance: the regionalisation artifact predates the code that made it

`results/regionalisation/similarity_pairs.csv` contains a **`signature_distance`**
column, and `similarity_summary.txt` reports **`recession_constant`** and
**`winter_summer_ratio`** ranges. The current `23_catchment_similarity.py`
computes none of the three.

So the artifact carrying the chapter's headline regionalisation numbers was
produced by a version of the script that no longer exists in the working tree,
and nothing on disk records which one.

**Reading the diff carefully, the numbers should be unaffected**: the cut
statistics fed `signature_distance` only; gauge selection still turns on
`signatures() is None`, which depends on `MIN_HOURS` and `flow.sum() > 0`, both
unchanged. The distance, response and excess matrices are computed from
untouched code paths. **[unverified — needs a rerun to confirm]**

But this is the exact hazard the repo's own convention ("every input is
re-fetchable by script") exists to prevent, and `results/run_manifest.json` is
from 21 July with its writer archived. Rerun `23_` once and let the artifact match
the code. Then the −0.249 has a provenance a reader can check.

---

## 8. Documentation

The 08-07 review's §3 identified this and it has been **partly actioned** —
`chapter-direction.md` now carries −0.249 / 6.2% / 38 / 703 and "a sixteenth".
Credit where due. The rest has not landed, and the situation is now worse in one
specific way.

**`chapter-synthesis.md` is canonical per the README and carries both withdrawn
headline results in full:**

| Location | Content | Status per `HANDOFF.md` |
| --- | --- | --- |
| §1 table, line 23 | Eryilmaz gap **−0.088** [−0.195, +0.004] | Withdrawn 08-07 |
| §2.1 table, line 125 | Same, plus 0.744 / 0.833 | Withdrawn |
| §2.1, lines 127-128 | "Leakage inflated the indoor model by 0.141 and the outdoor by only 0.041" | Withdrawn — "no measurable leakage penalty at all" |
| §2.1 line 129, §"Established" line 271 | "autocorrelated through occupancy and ventilation" | **Refuted** by the repo's own decomposition |
| §"Established" line 258 | −0.088 again | Withdrawn |
| §2.5 whole section | Correlation length, presented as "the unifying axis" | The analysis is **cut**; the estimator mismatch is withdrawn |
| §2.5 line 240 | "28% of pairs sit inside one correlation length" | True share within 30 km is **46.4%** |
| §2.4 line 172 | Decay regressed on distance, **signature distance**, scale ratio | Signature space is **cut**; the inventory names this exact item as "cutting coming back through the window" |
| §"Power" line 199 | "Ten network alarm episodes" | **24** network storms on published Fase 1 |
| Random-fold CI, lines 124 / 259 | [−0.005, +0.027] | Artifact says **[+0.009, +0.015]** |

**The specific risk.** Every correction above lives only in `docs/HANDOFF.md`,
which `git status` shows as **untracked**. The canonical document is wrong, the
corrections are one `git clean` from gone, and nothing is committed.

Also still stale: `scripts/README.md:66` ("42 gauges give 861 pairs" — now 38 and
703), and `chapter-direction.md:~175` still argues from "monitoring network
design", the framing withdrawn by the author.

**Recommendation.** Do not propagate corrections into `chapter-synthesis.md`
line by line. Rewrite §2.1, §2.4 and §2.5 against the artifacts, delete §2.5's
table outright, and fold the HANDOFF's withdrawal record in as a dated section so
it is tracked. A canonical document that needs a second document to correct it is
not canonical.

---

## 9. Do next, in order

1. **Commit.** Everything, today, including `HANDOFF.md`. Three review cycles and
   ~50 dirty paths exist on one machine. This is the largest risk in the project
   and it has been item 1 on two prior reviews.
2. **Supervisor**, before building rung 3. §5d. The question does not depend on
   rung 3's answer, and asking after it is built costs a rebuild.
3. **Fix the lag-selection rule in `23_`** (§1), rerun, and let the artifact match
   the code (§7). Expect the calibrated decay to weaken; report it.
4. **Delete the hard-coded prose** from `03_eryilmaz_replication.py` (§2). Ten
   minutes.
5. **Pre-register rung 3's horizon** *h* and its interval reporting (§3, §4)
   before running it. Write it into `transfer-experiment-preregistration.md`.
6. **Rewrite `chapter-synthesis.md`** §2.1 / §2.4 / §2.5 (§8).
7. Add `[tool.pytest.ini_options] testpaths = ["tests"]`.
8. Contiguous-run blocks in both bootstraps, with the timestamp index carried in
   — and a test that can fail if it regresses.
9. Then build rung 3.

Figures, bibliography and the manual structure pass remain open from the prior
reviews and are unchanged by this one.

---

## What is genuinely good, and should not be traded away

Said plainly because a review this long can read as a verdict on the whole.

- **`analysis-inventory.md`.** Few projects can name their own drift mechanism
  and cut ten live analyses on the strength of it. The two mechanisms it
  identifies — characterising instruments instead of answering questions, and
  changing currency — are correct and generalisable.
- **The paired gap interval** in `substitution_test`. Most theses difference two
  independent intervals and get the uncertainty wrong in the direction that hides
  real effects. This one does not, and `PairedIntervalTests` guards it.
- **Comments that name a specific past bug** — `NO_PRESSURE_DROP_HPA`, the
  station-id coordinate join, the zero-sentinel discovery, the coverage floor
  naming its four excluded gauges *with their coverage*. That pattern is worth
  more than the essays around it.
- **Novelty claims tested and allowed to die.** Three of four failed and were
  recorded as failures. That is rarer than any of the positive results here.
- **The `29_fase_events.py` hand-verification** against Geul Hommerich. Checking a
  new target against a manual count before using it is the right instinct and it
  is not common.
