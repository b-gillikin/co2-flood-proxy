# Chapter Review — Second Pass

Follows `docs/chapter-review-2026-08-06.md`. Re-read all of `docs/`, `README.md`,
`src/`, `scripts/`, `tests/` and the regenerated artifacts in `results/`. Test
suite run (79 passed). Recomputations below are against
`results/regionalisation/similarity_pairs.csv` as regenerated.

Date: 2026-08-07

---

## Verdict

Substantially better, and better in the way that matters: the fixes are
*structural*, not cosmetic. Three changes stand out.

**The multi-draw null was the right diagnosis and it settles §1 of the last
review.** I was wrong to treat −0.143 as an estimate; it was an attenuated lower
bound, exactly as `docs/scope-decisions.md` now says. Averaging ~24 valid draws
per pair moves the calibrated result to −0.249, p = 0.001, and — the part that
matters most — it makes the raw and calibrated metrics agree (−0.264 against
−0.249). The gulf between them was noise in the subtrahend. The distance-decay
finding is now robust and the correction is documented in a way that will read
well to a committee.

**`src/substitution.py` is the best thing in the repository.** One harness, one
inherited threshold, a paired bootstrap on the gap, three rungs in one currency.
It converts "the CO2 work connects to the regionalisation work" from an assertion
into a design. §2.4's headline — *the distance at which the substitution gap
exceeds 0.05 AUROC* — is falsifiable, inherits its threshold rather than choosing
one, and is a better headline than a decay coefficient.

**The Eryilmaz result got stronger by being made more honest.** Gap +0.012 with a
paired CI of [−0.005, +0.027] is a stronger claim than "within 0.05," and it was
available only because the inference was fixed.

What remains is mostly bookkeeping, one real methodological problem (§2), and the
same three structural gaps as before: no figures, no committed git state, no
literature.

---

## 1. Fix status against the first review

| # | Item | Status |
| --- | --- | --- |
| 1 | Mantel on the raw metric | **Partial** — calibrated metric computed and stored as `response_excess`, but `response_matrix` still holds raw `r` and the Mantel still runs on it. `similarity_summary.txt` reports −0.264, not −0.249 |
| 2 | One null draw per pair | **Fixed** — `--null-draws` default 50, ~24 valid; null now resolves for 644 of 703 pairs (92%) |
| 3 | Hard-coded episode indices | **Fixed** — derived by rule (`NO_PRESSURE_DROP_HPA = 2.0`), with the failure mode explained in the comment |
| 4 | `signatures()` differencing across gaps | **Fixed** — differences taken on the grid; flashiness denominator now restricted to contributing hours; guarded by `test_differences_do_not_span_coverage_gaps` |
| 5 | Bootstrap blocks spanning the outage | **Not fixed**, and now propagated into `src/substitution.py` (§2) |
| 6 | `MATCH_TOLERANCE_KM` | **Fixed** — 1.0 |
| 7 | Signed `scale_log_ratio` | **Fixed** — `abs()`, with the reason in a comment |
| 8 | `baseflow_index` misnamed | **Fixed** — `low_flow_ratio`, with a note on why it is not a BFI |
| 9 | Arbitrary recession bound (0.5, 1.0) | **Not addressed** |
| 10 | `signature_distance` skipna | **Not addressed** (still latent, still harmless) |
| 11 | `same_river` string heuristic | **Not addressed** |
| 12 | Mask selected at zero lag | **Not addressed** |
| — | Coverage floor | **Fixed and exceeded** — 80% floor, 4 gauges excluded and *named with their coverage* in the output. Exactly right |
| — | README withdrawn centrality claim | **Fixed** — now states 18th of 42 and why, plus a provisional-numbers banner |
| — | Manual map pass on structures | **Not done** |
| — | Every-gauge-as-donor check | **Not done** — but see §4, I ran it |
| — | Figures | **Not started** — `results/figures/` still holds only a manifest |
| — | Bibliography | **Not started** — still 101 entries, still no regionalisation or network-design literature |
| — | Git commit | **Not done** — working tree still carries the entire reframe |

Nine of twelve code defects closed, plus the coverage floor. The three left
(9, 10, 11) are low-severity and can be handled in a single pass.

---

## 2. The one new methodological problem

**`src/substitution.py` is scored on random-fold predictions, and a block
bootstrap does not repair that.**

`scripts/03_eryilmaz_replication.py` feeds `substitution_test` the
cross-validated probabilities from stratified random 5-fold CV — the evaluation
the same file's docstring calls invalid for an autocorrelated series. The
bootstrap fixes the *interval*; it cannot fix the *point estimate*. AUROC 0.885
and 0.874 still carry fold leakage, because neighbouring hours sit on both sides
of every fold boundary.

The file then says this is "the number that belongs beside the CO2 and donor
results, because it was produced the same way they are." It was not. The
precursor rung uses raw rolling predictors with no fitting and therefore no
leakage; the donor rung will use fitted models under leave-one-storm-out. Only
the Eryilmaz rung is a random-CV number, and putting it in the same table
launders it.

Two ways out, both cheap:

- **Preferred.** Refit both models under blocked or forward-chaining CV and pass
  *those* out-of-sample probabilities to `substitution_test`. Report the random-
  fold AUROCs beside them as the faithfulness check. The gap is probably robust —
  leakage inflates both models similarly — but that is a claim to demonstrate,
  not assume.
- **Minimum.** Label the block explicitly: "same folds, honest interval; point
  estimates retain random-fold leakage and are not comparable to the donor rung."

**Related, and unfixed from last time.** Both `substitution_test` and
`18_precursor_skill.block_bootstrap_auroc` draw *positional* blocks after
dropping non-finite rows, so a "72-hour block" can span the 87.7-day outage. The
module's docstring correctly argues that blocks preserve autocorrelation; over a
gappy positional index they do not. Fix: carry the timestamp index into the
harness, split into contiguous runs, and sample blocks within runs.

**One inferential point worth arguing explicitly.** For the precursor rung the
effective unit is the *episode*, not the hour: 432 pre-event hours come from 20
episodes. A 168-hour block is roughly one episode, so the current interval is
about right by construction — but say so, or cluster-bootstrap on episodes. A
committee member who counts 20 episodes and sees n = 3,521 will ask.

**Smaller.** `SubstitutionResult.substitutes` tests `gap <= threshold` (one-
sided), while the docstring says "within 0.05 AUROC of A" (two-sided). One-sided
is defensible — B beating A certainly substitutes — but align the words with the
code.

---

## 3. The numbers now disagree across three documents

This is the highest-priority remaining item, because the stale version lives in
the document the README calls canonical.

| Source | corr(distance, similarity) | Variance | Pairs / gauges |
| --- | ---: | ---: | --- |
| `results/.../similarity_summary.txt` (script output) | −0.264 raw | 7.0% | 703 / 38 |
| `docs/scope-decisions.md` (correct, calibrated) | **−0.249**, p = 0.001 | **6.2%** | 644 / 38 |
| `docs/chapter-synthesis.md` "Established, and standing" | −0.305 | 9% | 42 gauges, 861 pairs |

`chapter-synthesis.md` is the canonical document per the README, and its summary
table is the pre-fix version — the exact table a reader copies into a seminar
slide. Its "Machinery" bullets carry the same drift: "42 gauges give 861 pairs
with each gauge in 41 of them" (now 38, 703, 37), and "measured floor +0.062
against a real +0.242" (now +0.016 against +0.257).

Make the script print the calibrated metric as the headline. It already computes
`response_excess` for every pair; it is a two-line change to build a second
matrix and run the Mantel on it. Then regenerate and propagate. As long as the
script's own output says −0.264, the documents will keep drifting back.

**Other stale values found:**

- `chapter-direction.md` §"First result" has the corrected −0.249 / 6.2% but the
  surrounding prose still says "on 42 filtered gauges and 861 pairs," "each gauge
  appears in 41 of them," "Mantel p < 0.0002" (the calibrated p is 0.001), and
  "distance accounts for about a tenth of the variation" — 6.2% is nearer a
  sixteenth. The numbers were updated; the sentences around them were not.
- `chapter-direction.md` still asserts "Coverage does not discriminate: every
  candidate runs 91-100%," seven lines below its own table reporting 89-100%
  after an 80% floor and four gauges excluded at 53-74%.
- `scope-decisions.md` §3 still says "41 natural gauges ... 91-100% coverage" and
  §"EStreams" still says "44 natural gauges" and "18-19 of 41."
- Elevation is "17 of 42" in `chapter-direction.md`; the artifact says 16 of 38.
- Scale range is "0.02 to 195 m3/s" in `chapter-direction.md` and "0.02 to 240"
  in `scope-decisions.md`; the artifact says 240.15.
- `README.md` data table still says "59 gauges available (17 pulled)."
- `decisions.md` (2026-08-06, precursor) is still the pre-rerun entry: 19
  episodes, 3,492 hours, rain 0.835, CO2 0.409 — against 20 / 3,521 / 0.872 /
  0.453 in the artifact. It also still carries the caveat that intervals were
  computed "by resampling hours, which are autocorrelated," which the 168-hour
  block bootstrap fixed. Left in place it reads as an open defect.

**One substantive consequence of the rerun that the docs have not absorbed.**
The barometrically-clean episode set changed from 3 hand-picked episodes to 9
selected by rule, and the new set is *mixed in sign*: z from −1.12 to +0.90, with
three positive. `decisions.md` still says "The three episodes with no pre-onset
pressure fall show no positive residual excursion." That sentence is now false,
and the true version is better for you — nine episodes scattering either side of
zero is much stronger evidence of no signal than three that happened to be
negative. Rewrite it; do not just delete it.

---

## 4. The every-gauge-as-donor check, run

`chapter-synthesis.md` lists this as robustness that "will be asked" and has not
run it. I ran it on the calibrated metric — corr(distance, `response_excess`)
computed separately with each gauge as donor, 36 donors with ≥16 pairs:

| | |
| --- | --- |
| Range across donors | **−0.58 to +0.21** |
| Median donor | −0.276 |
| Quartiles | −0.412 / −0.276 / −0.165 |
| Donors showing no decay (corr ≥ 0) | **2 of 36** |
| **Worm at Rimburg** | **−0.379** |

Two findings, and the second needs saying in the chapter before someone else
says it.

**Distance decay is not a universal property of this network.** It ranges from
strong to absent depending on which gauge you stand on. That is a more
interesting result than the pooled −0.249 and it belongs in the chapter — it says
the reach of a donor is a property of the donor, which is precisely the
monitoring-network-design question.

**Rimburg is in the favourable tail.** It ranks 11th of 36 on decay strength
(69% of donors show weaker decay) and 12th of 36 on median co-response. Not an
outlier, but not mid-pack either — and mid-pack is what
`chapter-direction.md` claims when it justifies the donor as "mid-range on every
response characteristic." That claim is true of the *signatures* (mean Q, CV,
flashiness) and not of the *transfer behaviour*. Report both. "Our donor sits at
the 69th percentile of transferability, so the pooled estimate is mildly
optimistic" is a sentence that wins trust; having it discovered in the viva is
not.

**Robustness of the pooled calibrated result** — all healthy, worth reporting:

| Check | corr(distance, excess) |
| --- | ---: |
| Headline | −0.249 |
| Spearman | −0.246 |
| Excluding same-river pairs | −0.232 |
| Excluding pairs with a >50 m³/s gauge | −0.281 |
| Partial on log joint high-flow hours | −0.256 |

---

## 5. Structural gaps, unchanged since the last review

**Fase thresholds are still not implemented.** `chapter-synthesis.md` §"Machinery"
specifies events as Fase 1/2/3 exceedances and explicitly rejects percentiles as
"self-referential and here largely set by January 2025." `03_build_event_catalogue.py`
still builds p90/p95/p99, and the precursor result — now promoted to a rung of
the ladder — rests on them. Worse, §2.2 defines the *spatial* rung's target as
"onset of a Fase 1 exceedance at the receiver," so the unbuilt work depends on
the unbuilt threshold. This is now on the critical path, not a documentation
mismatch.

**The +4 h Geul routing time still has no script.** It is cited in
`chapter-direction.md` as "measured ... verified by symmetric cross-correlation."
Nothing in `scripts/` or `src/` computes it. The pair table already carries
`response_lag_h` for every pair — this is a five-line script that reads the Geul
rows out of it.

**No figures.** `docs/figure-inventory.md` still lists 20 figures from the
retired anomaly-detection programme; `results/figures/` holds a manifest and
nothing else. The minimum set has not changed: study-area map with the 38 gauges,
the donor and the Geul chain; similarity-versus-distance with the null band; the
per-donor decay distribution from §4; per-storm skill once Q1 exists; the
precursor ROC.

**No literature.** 101 entries, unchanged. Still nothing on regionalisation
(Blöschl, Oudin, Parajka beyond the single hit), donor transfer, hydrometric
network design, or value of information — and still ~20 dead anomaly-detection
entries. The chapter's own framing document says it sits in the network-design
literature; the bibliography says it sits in the anomaly-detection literature.

**Nothing is committed.** `git status` still shows the entire reframe as
modified-or-untracked, and the last commit still reads "Reframe chapter around
early-warning precursor question." Three review cycles of work now exist only on
one machine.

**Three superseded planning documents still read as current** to anyone who opens
them without checking the banner: `figure-inventory.md`, `results-outline.md`,
`methods-outline.md`. And `chapter/chapter-draft.md` is still on disk telling
readers not to build on it.

---

## 6. One question about the new headline

§2.4 now defines the headline as *the distance at which the substitution gap
exceeds 0.05 AUROC*. It is the right target. Two things to settle before
building it:

**Is it estimable on this network?** Pair distances run 0.7 to 109 km with a
median of 30, distance explains ~6% of similarity, and there are 37 receivers.
A crossing point estimated from a weak trend over that span will carry a very
wide interval. Decide now — before seeing the answer — that you will report the
confidence interval on the crossing distance, and that **"no crossing within the
span of this network"** is a publishable answer. It is arguably the *better*
answer for a network-design chapter: it says a donor gauge is either useful
everywhere in the region or nowhere, and proximity is not the design variable.

**The per-donor spread in §4 says the crossing distance is donor-specific.** With
decay ranging −0.58 to +0.21, a single pooled crossing distance may not exist as
a meaningful quantity. Consider making the deliverable a *distribution* of
crossing distances across donors, with Rimburg located in it. That is more
honest, more useful to someone siting a gauge, and it turns the sample-size
problem into the finding.

---

## 7. Do next, in order

1. **Commit.** Everything. Today.
2. Make `23_catchment_similarity.py` run the Mantel on `response_excess` and
   report it as the headline; add the test that guards it. Regenerate.
3. Propagate −0.249 / 6.2% / 38 / 703 / p = 0.001 into `chapter-synthesis.md`
   (the "Established" table and the Machinery bullets), `chapter-direction.md`
   (the prose around the table, the 91-100% claim, elevation, scale range) and
   `scope-decisions.md` §3.
4. Rewrite the `decisions.md` precursor entry against the current artifact,
   including the nine mixed-sign clean episodes and the removal of the obsolete
   bootstrap caveat.
5. Fix the substitution harness: time-aware folds for the Eryilmaz scores (or an
   explicit label), and contiguous-run blocks in both bootstraps.
6. Add the per-donor decay distribution as a script and a figure. It is the
   robustness check that will be asked and it is already interesting.
7. Implement Fase thresholds. The spatial rung depends on them.
8. Manual map pass on the 15 excluded structures.
9. Bibliography: ~30 in, ~20 out.
10. Take the "monitoring network design" framing to the supervisor. Still open,
    still gating.

---

## What improved that should be said out loud

- Diagnosing the −0.143 collapse as single-draw attenuation rather than accepting
  it, then documenting both the review's finding and its own refutation in
  `scope-decisions.md`. That section is now a model of how to handle external
  criticism: the reviewer's mechanism was right, the reviewer's number was wrong,
  and both are on the record.
- The coverage floor implementation, which names the four excluded gauges *with
  their coverage* in the output rather than silently dropping them.
- Replacing hard-coded episode positions with a derived criterion, and writing
  the drift failure mode into the comment so it cannot come back.
- The unified substitution harness, and specifically the insistence on a *paired*
  interval on the gap. Most theses difference two independent intervals and get
  the uncertainty wrong in the direction that hides real effects.
- The Eryilmaz block reporting the inherited procedure *and* the chapter's
  inference side by side, with an explicit sentence on why omitting either would
  be wrong.
