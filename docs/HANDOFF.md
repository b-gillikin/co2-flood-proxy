# Session Handoff

Written 2026-08-07. **Read `docs/chapter-synthesis.md` first** — it is canonical
for the idea, design and data, and every figure in it is quoted from an artifact
produced by the code in the tree. Then `docs/chapter-scope-and-preregistration.md`
for what gets built and the binding design, and `docs/analysis-inventory.md` for
what was cut and why.

This file is session state only. It was 498 lines and is now 150; a handoff that
restates the canonical document is how the numbers drifted apart three times.

---

## Where the chapter stands

**It has no positive result about Maas tributaries yet.** What stands is
inherited (Eryilmaz), negative (CO2), or descriptive (distance decay). **Rung 3 —
what a donor gauge buys against a receiver's own — is unbuilt, and it is the
chapter.**

Everything it needs now exists: the target (published Fase thresholds), the
harness (`substitution_test` with `groups`), the storm structure (24 network
storms), and a binding pre-registration.

---

## This session, in one table

| | |
| --- | --- |
| Scripts | 26 → **16** |
| Docs | 27 → **16** |
| Tests | 84 pass, ruff clean |
| Commits | 3. Working tree clean. **Was 49 dirty paths across three review cycles** |

**The commit blocker was not the expired token.** A stale zero-byte
`.git/index.lock` dated 2026-08-06 23:46 had been failing every write since. The
token is real but separate and only affects `push`.

### Four things changed a number

1. **Cross-fold AUROC pooling** (`substitution_test`). Probabilities from
   separately fitted models are not one ranking. The Eryilmaz "sign flip" of
   −0.088 was this artifact; within fold the gap is **−0.012** and the two
   evaluation schemes agree. There is **no measurable leakage penalty** — the
   0.141 was the same artifact. Guarded by `GroupedScoringTests`.
2. **Inert null calibration** (`23_`). The lag maximum was taken on `|r|` and the
   signed value returned, so the null averaged +0.016 against a median |null| of
   +0.036 — it was converging to no correction. Now signed. Co-response
   **+0.243 → +0.106** (59% of the raw is procedural); decay **−0.249 → −0.311**,
   variance **6.2% → 9.7%**. The decay *strengthened*, which the third-pass review
   did not predict, because the raw metric changed too.
3. **The Fase target built** (`29_fase_events.py`). Waterschap Limburg's published
   Geel/Oranje/Rood triggers, verified against the statutory flood plan. They were
   on disk the whole time.
4. **Ten analyses cut**, ~2,000 lines, plus twelve stale documents archived.

---

## Do next, in order

1. **Supervisor**, before rung 3. Four questions in
   `chapter-scope-and-preregistration.md` §12. None depends on rung 3's answer and
   asking afterwards costs a rebuild. The live one is **§12.2**: all-pairs design
   with the Worm as worked case, which changes the framing from *the Worm's reach*
   to *donor reach, measured here*.
2. **Finalise Part II §II.1** — the analysis set. Blocked only on §12.4 (ingest
   the level network or stay on 38 gauges). The recommendation is to finalise on
   38 and treat level as a stated extension: it buys a better reach model and no
   additional events.
3. **t-interval in `substitution_test`** (§II.6). It currently returns a percentile
   cluster bootstrap, which undercovers badly below ~30 clusters. Must land
   *before* the first rung-3 run, not be applied to its output.
4. **Build rung 3.** Horizons pre-registered at h ∈ {6, 12, 24}, headline 12.
5. **Bibliography.** 101 entries, nothing on regionalisation or donor transfer,
   ~20 dead anomaly-detection entries. Flagged in three review passes, depends on
   nothing.
6. **Figures from scratch**, and the manual map pass on the 15 excluded structures.

**Not worth doing:** the mechanism decomposition is ~20 lines and the third-pass
review argues against building it at all (§5a) — but the repo's own standard is
that every number needs a regenerating script, and this is the chapter's only
direct evidence for its own mechanism. Unresolved; my read is build it.

---

## Open decisions, all yours

| | Decision |
| --- | --- |
| 1 | Framing and likely examiners, with the supervisor |
| 2 | **All-pairs with the Worm as worked case** — recommended, not adopted. The donor's justification (CO2 sensor, groundwater wells) no longer stands on anything: the sensor was measured worthless and the groundwater lane is archived |
| 3 | Ingest the level network, or stay on 38 gauges |
| 4 | Whether the chapter is planned as a negative-results chapter now rather than discovered as one |

---

## Do NOT claim

- **The Eryilmaz sign flip (−0.088), or any leakage arithmetic.** Pooling artifact.
- **Co-response +0.243, or decay −0.249 / 6.2%.** Superseded by the null fix.
- **Any cross-variable correlation-length comparison.** The analysis is cut; the
  point estimates were produced by two different estimators and the ordering
  reversed depending on which one you matched on.
- **Rimburg as "mid-range."** True of its signatures, false of its transfer
  behaviour — 69th percentile, 11th of 36.
- **That indoor CO2 is autocorrelated "through occupancy and ventilation."**
  Refuted: pressure-only scores 0.872, hour-of-day 0.554.
- **That the level network eases the power problem.** Measured; it does not.
- Anything from `archive/`.

---

## Environment

- **Interpreter:** `/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`.
  The shell default is 3.9; the repo needs 3.11+.
- **`pytest` at the repo root fails** on `archive/tests/`. Use `pytest tests/`
  (84 pass). One-line fix still unapplied: `[tool.pytest.ini_options]`,
  `testpaths = ["tests"]`.
- `23_catchment_similarity.py` takes **~12 minutes** (703 pairs × ~24 null draws).
  Background it.
- The real repo is `~/Desktop/floods/chapter1-co2`. `~/Desktop/chapter1-co2` is a
  near-empty decoy a failed `cd` lands you in.
- Grep for `spec_from_file_location` before moving scripts — path-based imports are
  invisible to ruff and to the tests, and broke `21_` once.
- `data/raw/discharge/rws/` is ~2.1 GB of cached JSON, gitignored and deletable.

---

## The failure mode, named — it has now recurred four times

**Comparing a number against another number produced a different way.**

1. Mantel on the raw metric while the docs mandated the calibrated one.
2. Random-fold point estimates placed beside blocked-fold ones.
3. AUROC pooled across folds fitted on different data.
4. Rainfall and discharge correlation lengths computed with different estimators.

Plus its limiting case, caught this session: **a number compared against a number
that is not computed at all** — interpretive sentences hard-coded into generated
artifacts. `chapter-scope-and-preregistration.md` §II.10.7 now forbids it, and
both `03_` and `23_` interpolate those figures from the result object.

**Before any two numbers go in one table, check the same estimator produced both.**

## What is worth keeping

- Every claim tested before being written down. Three of four novelty claims died
  that way and were recorded as failures.
- The zero-sentinel discovery, found by cross-validating one gauge against an
  independent publisher of the same instrument.
- Comments that name a specific past bug — `NO_PRESSURE_DROP_HPA`, the station-id
  coordinate join, the coverage floor naming its excluded gauges *with* their
  coverage. Worth more than the essays around them.
- Four external review passes read as evidence rather than accepted wholesale.
  The third pass found the inert null; its predicted direction was wrong and that
  is recorded in the pre-registration rather than quietly fixed.
