# Session Handoff

Written 2026-08-07 (second pass). Read this first, then `docs/chapter-synthesis.md`
(canonical for idea, design and data), `docs/scope-decisions.md` (live decisions),
and the reviews in `docs/chapter-review-2026-08-0{6,7}.md`.

Archived in the dissertation KB as DS-2026-030; predecessor DS-2026-029.

---

## The chapter in one paragraph

One question, asked at widening scope: **what can substitute for local
instrumentation, and at what cost in skill?** Eryilmaz set the decision rule — B
substitutes if within 0.05 AUROC of A — and the chapter inherits it, so every
rung is reported in one currency. Rung 1 (data source) and rung 2 (variable) are
run. Rung 3 (space: a donor gauge for the receiver's own gauge) is **not built**,
and it is the chapter.

`src/substitution.py` is the shared harness; it is what makes the progression
structural rather than asserted.

---

## Two headline results were withdrawn on 2026-08-07 (second pass)

Both failed the same check: **a number was compared against another number
produced a different way.** The verification code was written to a session
scratchpad and is **not in the repo** — if it is wanted as a standing check it
has to be promoted into `scripts/`. Everything below is cheap to re-derive
either way; the recipes are in the sections themselves.

### (a) The Eryilmaz "sign flip" is a cross-fold pooling artifact — WITHDRAWN AND FIXED

**Fixed in code 2026-08-07 and the artifact regenerated.**
`substitution_test` now takes `groups`; scores are compared within fold and
averaged, with a paired cluster bootstrap over folds. `results/eryilmaz/auroc.txt`
as regenerated:

| | within fold (the estimate) | pooled (contrast only) |
| --- | ---: | ---: |
| Random folds, inherited | **+0.012** [+0.009, +0.015] | +0.012 |
| Forward chaining | **−0.012** [−0.059, +0.017] | **−0.088** |

Per-fold gaps under forward chaining: min −0.105, median +0.010, max +0.019,
**A better in 4 of 5**. Random folds show no pooling gap because all five cover
the same period — which is exactly why the +0.012 and −0.088 were never
comparable.

**Two things follow, and both are better for the chapter than what they replace.**
The two evaluation schemes now **agree at ±0.012**, so the substitution
conclusion does not depend on the scheme — a stronger claim than either block
alone. And forward chaining scores *higher* within fold (A 0.900 against 0.886),
so **there is no measurable leakage penalty at all**; the "0.141" was the same
artifact.

Guarded by `tests/test_substitution.py::GroupedScoringTests`, which builds two
folds where A wins within each and loses pooled. 85 tests pass, ruff clean.

Original diagnosis follows.

`fit_blocked_predictions` writes every fold's `predict_proba` into one column and
`substitution_block` takes a single AUROC over the concatenation. AUROC is
rank-based, fold base rates here run **1.2% to 25.5%**, and fold calibration
drifts badly (fold 2 mean p = 0.250 against actual 0.012; fold 4 mean p = 0.059
against actual 0.255). Pooling asks a cross-period ranking question the
random-fold number never asks, because all five random folds cover one period.

| | pooled (as reported) | rank-normalised in fold | per-fold mean |
| --- | ---: | ---: | ---: |
| A indoor IoT | 0.744 | 0.810 | **0.900** |
| B outdoor weather | 0.833 | 0.838 | **0.912** |
| **gap** | **−0.088** | −0.028 | **−0.012** |

Fold-wise gaps `+0.018, +0.010, +0.019, +0.001, −0.105`: **four of five favour A**;
the whole effect is fold 4.

**Do not claim** the sign flip, or the leakage arithmetic that rests on it
("leakage inflated the indoor model by 0.141 and the outdoor by 0.041"). Per
fold, forward chaining gives 0.900 / 0.912, both *above* the random-fold
0.885 / 0.874 — there is no measured leakage penalty. That sentence is in
`chapter-synthesis.md` §2.1 and again in "Established, and standing"; strike both.

**What stands:** public weather substitutes for indoor sensing. Gap −0.012
fold-matched against +0.012 random-fold. Which is nominally better is not
determined.

**Fix:** `substitution_test` must take fold labels and score per fold, never
pool across them. Report the paired fold-wise gap.

### (b) §2.5 compares rainfall and discharge with two different estimators

`28_correlation_length.py` correlates rainfall and pressure as **raw levels, all
hours, zero lag**; discharge as **first differences, both gauges above p90, best
lag ±12 h**. It then compares rows of one table. Re-estimated under both:

| Variable | estimator | c0 | L (km) | c_inf | amplitude |
| --- | --- | ---: | ---: | ---: | ---: |
| rainfall | levels, all hours, 0 lag *(as reported)* | 0.87 | **30.2** | 0.18 | 0.69 |
| rainfall | diffs, both>p90, best lag *(discharge's)* | 0.91 | **16.5** | 0.08 | 0.83 |
| high-flow | diffs, both>p90, best lag *(as reported)* | 0.42 | **30.0** | 0.13 | 0.29 |
| high-flow | levels, all hours, 0 lag *(rainfall's)* | 0.59 | **19.6** | 0.48 | 0.11 |

**The ordering reverses with the estimator.** Matched on discharge's estimator
rainfall decays twice as fast; matched on rainfall's, discharge does. The
reported coincidence at 30 km is manufactured. The cross-variable L comparison is
**not identified** by this design — say so, rather than resting on the wide CI.

**What stands: the c0 contrast**, 0.87–0.91 rainfall against 0.42–0.59 discharge
under either estimator. "Two co-located rain gauges agree; two co-located
catchments only half-agree" is robust and is the claim to keep.

**Fix:** pick one estimator, state why, apply it to every variable, regenerate.
The discharge estimator is better conditioned (rainfall amplitude 0.83 over a
0.08 floor, against discharge-under-levels fitting 0.11 over a 0.48 floor).

### (c) The barometric mechanism is real — and the stated reason for it is wrong

Feature decomposition, random 5-fold as published:

| Model | AUROC |
| --- | ---: |
| A indoor full / **pressure only** / minus pressure | 0.885 / **0.872** / 0.587 |
| B outdoor full / **pressure only** / minus pressure | 0.874 / **0.864** / 0.681 |
| **hour-of-day only** (sin/cos, no weather) | **0.554** |
| daytime flag only | 0.517 |

Pressure carries all of it; `r(CO2, indoor pressure) = −0.298`; mean CO2 by hour
of day is flat at 546–679 ppm. The CO2 → pressure claim is correct and now
demonstrable in ~20 lines — **build that script**, it converts assertion to
measurement.

But "indoor CO2 is autocorrelated through **occupancy and ventilation**"
(`chapter-synthesis.md` §2.1, twice) is refuted by the same test. It is synoptic
barometric autocorrelation. Rewrite.

Seasonal split, a real physical result: `r(CO2, indoor pressure)` = −0.505 MAM,
−0.386 DJF, **−0.268 JJA**. Barometric pumping weakens when the house is
ventilated — and fold 4, the only fold where B beats A, is 2026-03 → 2026-07.

---

## Results that stand

| Finding | Value | Where |
| --- | --- | --- |
| Public weather substitutes for indoor sensing | gap **−0.012** fold-matched, +0.012 random-fold | `results/eryilmaz/` (needs regeneration) |
| Indoor CO2 is barometrically driven, not occupancy driven | pressure-only 0.872/0.864 vs hour-of-day 0.554 | not yet scripted |
| Rainfall beats CO2 for high-flow onset | 0.872 vs 0.46 | `results/precursor/` |
| Response similarity decays with distance | **−0.249**, Mantel p = 0.0012, 6.2% | `results/regionalisation/` |
| — partialling on log joint high-flow hours | **−0.256** (strengthens) | verified this session |
| Co-response net of the procedural null | **+0.243**, Wilcoxon p = 1e-74 | same |
| Co-located correlation, rainfall vs catchments | **0.87–0.91 vs 0.42–0.59**, estimator-robust | `results/correlation_length/` |
| Well barometric efficiency 0.20–0.34 | correction mandatory | `results/groundwater/` |
| Occupancy dominates non-barometric variance | 12 h band 4–8× too large | `results/barometric_response/tidal_response.txt` |

## Do NOT claim

- **The Eryilmaz sign flip, or any leakage arithmetic.** See (a).
- **That rainfall and high-flow response share a correlation length**, or any
  cross-variable L comparison. See (b). Two independent reasons now: the discharge
  interval is [9, 631], *and* the ordering is estimator-dependent.
- **Rimburg as "mid-range."** True of its signatures, false of its transfer
  behaviour — the second review puts it at the **69th percentile** of
  transferability (11th of 36). Say both.
- **Any EStreams static-attribute model.** 18 catchments, 366 columns.
- The raw best-lag correlation, or the uncalibrated +0.243.
- Anything from `chapter/chapter-draft.md`, `figure-inventory.md`,
  `results-outline.md`, `methods-outline.md` — all superseded.
- The BRF response **shape** (rings under OLS). The **sum** is sound and is what
  `21_forward_gain_model.py` consumes.

## Four novelty claims tested, three failed — do not re-run

| Claim | Outcome |
| --- | --- |
| Gauge outage scales with flood magnitude | Not supported. Two passes gave opposite answers; both were artifacts of NRW sampling density rising 21% → 56% across decades |
| Donor choice is objective-dependent | Not supported. Rankings agree at ρ = +0.70; only 6% of event skill forfeited |
| National border degrades transfer | No effect (p = 0.62), underpowered at 3 German gauges |
| Optimal donor count ≈ 5 | Replicates Oudin et al. (4–8). Established, not novel |

**Accepted novelty position:** regional scope transfer — hourly grain, 27–77 km²
flashy Maas tributaries — plus a negative-results battery. Not a new mechanism.

---

## Next actions, in order

**Read `docs/analysis-inventory.md` first.** The author cut 10 of 22 live
analyses on 2026-08-07. Several items below existed only to serve cut work; the
list is reconciled against the cuts.

**DONE 2026-08-07.**

- ~~**Fase thresholds**~~ — built as `scripts/29_fase_events.py`, lint clean,
  81 tests still pass. Verified against a hand count at Geul Hommerich.
  **The target now exists**: `data/processed/fase_events.csv`. On the 38-gauge
  analysis set, **115 Fase-1 events across 26 gauges in 24 network storms**, six
  of them involving ≥5 gauges and spread October 2024 → February 2026. Kept
  separate from `03_build_event_catalogue.py`, which serves the 3-gauge CO2 lane
  through the tested percentile path in `src/eval.py`.
- ~~**Resolve Niers at Kessel**~~ — excluded by rule (any gauge above Fase 1 for
  >5% of its record), named in the output. Only offender. Still worth raising
  with Waterschap.

- ~~**Fold-wise scoring in `substitution_test`**~~ — done, `groups` parameter,
  4 new guard tests, `results/eryilmaz/` regenerated. See §(a) above. This also
  retires the positional-block bug for any grouped call: the resampling unit is
  the group, so no block ever spans a coverage gap.

**Next.**

1. **Build rung 3.** Receiver's own gauge as A, Worm/Rimburg as B, target =
   receiver crossing its published Fase 1 within *h* hours, `groups` = held-out
   storm. **Target, harness and grouped inference all now exist**; nothing else
   is needed and nothing else in the chapter matters until it does. Run it on
   **Fase 1 as the headline and p99 as a power check** — 115 events against 452,
   so agreement across the two is what shows the headline is not an artifact of
   a thin target.
2. **Script the pressure-vs-occupancy decomposition.** ~20 lines, already comes
   out in the chapter's favour, and it is the chapter's only direct evidence for
   its own mechanism.
3. **Commit.** Nothing committed across three review cycles; ~50 paths dirty.
   Token expired: `gh auth login -h github.com`, then push.
4. **Supervisor.** The question is now "is regional scope transfer plus a
   negative-results battery enough for Chapter 1?" You have the evidence to ask.
5. Remaining review items: `decisions.md` precursor rewrite (19→20 episodes,
   0.835→0.872, nine mixed-sign clean episodes); **`18_precursor_skill.py` still
   uses its own positional block bootstrap** — move it onto `substitution_test`
   with `groups` = episode, which is the unit the 08-07 review argued for anyway;
   per-donor decay script and figure; bibliography (~30 in, ~20 out); figures.

**Dropped:** elevation cache invalidation — it only served the signature space,
which the inventory cuts.

### Withdrawn from this list on 2026-08-07, and why

| Was | Why it is gone |
| --- | --- |
| **NRW gauge metadata** (`OpenHygon_meta.zip`) | Justified by "unblocks §2.5's one open test". §2.5 / `28_correlation_length.py` is **cut**. Demoted to the German robustness arm; do it only if that arm survives. |
| **DWD hourly pressure** | Same — it existed to repair the correlation-length pressure fit. That fit is cut. The surviving claim (pressure is spatially uniform, which is *why* Eryilmaz substitutes) is two sentences and a range from the ten pairs already held. |
| **One estimator in `28_`** | The script is cut, so the estimator mismatch no longer needs repairing — only recording, as a withdrawn result. |
| **Manual map pass on 15 structures** | Still worth doing, but it defends the signature space, which is cut. Reduced to a one-line note on the exclusion rule. |
| **"Dutch Fase thresholds" as a blocking request** | Not blocking. Already on disk (item 1). What *is* still worth requesting is **longer record**, for the reason in the next section. |

---

## Framing correction, 2026-08-07: this is NOT a network-design chapter

Stated by the author. **It is not about where to put a gauge.** The
"monitoring network design" framing entered via `scope-decisions.md` §3 as a
provisional answer to the novelty question and leaked outward.

The chapter is **descriptive**: given that the Worm at Rimburg is deeply
instrumented, how much does its signal tell you about other Maas tributaries
around high-water events, and how does that fall off? A measurement of donor
reach is an *input* somebody else could use for siting. Reporting it *as* siting
advice overclaims, drags in a value-of-information literature the chapter does
not engage, and is the same species of overreach that produced the
correlation-length and sign-flip withdrawals.

**Still carrying the old framing and needing a strip:** `scope-decisions.md` §3
(the whole "Monitoring network design" block), `chapter-direction.md` ~175 and
~216.

---

## Is this a data problem? Mostly no — but the pattern is real

Asked directly on 2026-08-07. Honest classification:

**The findings that change what the chapter can claim are method, not data.** The
pooling artifact, the estimator mismatch, the undemonstrated mechanism and the
missing rung 3 would all survive infinite data. Two of them — the estimator
mismatch above all — are *choices*, and more data just yields two more precise
numbers that still are not comparable.

**But analysis has repeatedly run over known gaps and concluded anyway:**

| # | Gap | Status |
| --- | --- | --- |
| 1 | Elevation 16 of 38 | **A bug, not a gap.** `fetch_elevations` returns the cache if *any* label resolves; the cache holds 17 entries from the retired 17-gauge set, so 21 of 38 are never looked up. Free API. |
| 2 | `winter_summer_ratio` has n = 2 winters | Still in the standardised signature space feeding `signature_distance` → the decay regression. A statistic with no sampling distribution carrying an inferential axis. Flagged 08-06. |
| 3 | IoT 31% coverage, 46% JJA vs 644 DJF hours | The mechanism is synoptic pressure forcing, a winter phenomenon. No document says this. |
| 4 | Discharge correlation length [9, 631] | The data cannot answer it; "30.0" went into a table anyway with a narrative on the coincidence. |
| 5 | 10 alarm episodes, 2 large, both Jan 2025 | Hard limit of two years. Rung 3 gets ten folds of wildly unequal weight — report per-fold, never the mean. |
| 6 | EStreams 18 of 38 | Correctly capped at 1 km and correctly not modelled. Handled well. |

**Verified obtainable this session** (see Data). The rule that follows: before an
axis enters an analysis, state its coverage in the artifact. Items 1–3 all
survived because coverage was recorded in prose somewhere and never in the number.

---

## Data

**Held.** Waterschap Limburg 57 → 42 natural → **38 after an 80% coverage floor**
(hourly, 2024-08 → 2026-08); **LANUK NRW 42 German gauges, 15-min, 1950–2026**;
**RWS Maas 10-min, 2000–2026**; **DWD 34 rain stations, hourly, 1995–2026**;
EStreams attributes; BRO groundwater; Kerkrade IoT.

Cross-validated, not assumed: LANUK vs Waterschap r = 0.9994–1.0000; RWS vs
Waterschap at Borgharen r = 0.9975 after the zero fix.

**The Kerkrade IoT record is three disjoint, summer-weighted chunks, and no
document says so.** `data/processed/iot_coverage_gaps.csv`: gaps of **2,854 h,
3,823 h and 2,103 h**. The 2025-01-31 → 2026-07-21 window is ~12,700 hours;
**3,964 are observed (31%)**, of which 1,825 (46%) are JJA against 644 DJF. A
chapter whose mechanism is synoptic pressure forcing is evidencing it on a record
that largely excludes the synoptic season. This belongs in the methods.

**The NRW archive is NOT uniformly 15-minute, and the docs describe it wrongly.**
Measured from the raw zips: 2020s median inter-record gap **15.0 min** (84.5% at
≤15 min); 1950s median gap **216 min** (7.9% at ≤15 min). The sampling *design*
changed; this is not just the known density rise from 21% to 56%. Anything
touching the long record must state which era it uses.

### Fase thresholds — already on disk, not a data request

`data/interim/waterschap_locations.csv` carries **`Fase1Value`, `Fase2Value` and
`Fase3Value` for all 634 locations**, including all 59 discharge gauges and all
38 in the analysis set. (An earlier note here said only Fase 1/2 were present —
that read a truncated column list and was wrong.)

Verified against the
[Rampbestrijdingsplan Hoogwater Limburg 2023-2026](https://lokaleregelgeving.overheid.nl/CVDR719417/1):
Fase 1/2/3 are the **Geel / Oranje / Rood** discharge triggers of the province's
statutory flood plan — heightened vigilance, impending flooding, active flooding.
Two exact matches confirm the mapping: Maas St. Pieter **1250 / 2000 / 2600**
against the plan's warning / GRIP-2 / GRIP-4 milestones, and Geul Hommerich
**10 / 20 / 50** against its worked tributary example.

**But it is rare, and that forces the design.** Over the 2-year record: Fase 1 is
reached by 27 of 38 gauges, median **3 episodes** each, sitting at a median
**p99.7**; Fase 2 by 14 gauges; Fase 3 by **4**. Pairwise, **485 of 703 pairs
(69%) have zero hours with both gauges above Fase 1** against a median of 824
joint hours at own-p90.

**So: Fase is the target, p90 is the mask.** Different jobs. The mask is a
statistical device that is never interpreted, so self-reference costs it nothing;
the target must be externally defined. `scope-decisions.md` §2's attack on
percentiles is right about the target and wrong about the mask. Full working in
`docs/analysis-inventory.md`.

**This is now the strongest argument for the long-record request**: the target the
water authority actually uses fires three times in our window.

### Verified obtainable now — checked live 2026-08-07 (mostly superseded, see cuts)

**1. NRW gauge metadata — 66 KB, public, no key. Highest leverage in the repo.**

    https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/
      oberflaechengewaesser/hygon/OpenHygon_meta.zip

`OpenHygon_Pegel_EPSG25832_ASCII.txt` holds **196 NRW gauges, all with
coordinates** (EPSG:25832; the inverse-UTM conversion is ~15 lines, no geospatial
stack needed), plus MNW/MHW/Mittel and **`Informationsstufe 1/2/3` for 83** —
the German published alarm thresholds, i.e. the externally-defined event
definition the methods demand.

Match to the 42 gauges held: **22 exact + 10 on transliteration** (`Hs.
Langenfeld`→`Haus_Langenfeld`, `Pannenmühle`→`Pannenmuehle`) = **32 of 42**; 8 of
those carry an `Informationsstufe 1`. The 10 with no candidate include
Reifferscheid, Welz and Luchem — the July-2021 terminations, which a *current*
inventory would not list. Coherent, and a small finding in itself.

Effect on the geometry that identifies `L`:

| Network | gauges | pairs | **pairs < 20 km** | share < 20 km |
| --- | ---: | ---: | ---: | ---: |
| Waterschap only (current) | 38 | 703 | 196 | 27.9% |
| + locatable NRW | 60 | 1,770 | **340** | 19.2% |

**Quote the count, not the share** — the share falls because the German network is
sparser overall, but short-range pairs rise **73%**, and short-range pairs are
what identify `L`. This is the open test `chapter-synthesis.md` §2.5 names.

**2. DWD hourly pressure** — same server and zip layout `27_` already parses:
`.../climate/hourly/pressure/historical/`, inventory
`P0_Stundenwerte_Beschreibung_Stationen.txt`. Converts the pressure row from a
degenerate fit (5 of 7 stations, 10 pairs, all r > 0.99 over 114 km) into a real
measurement over ~600 km. "Pressure is spatially uniform here" is the premise the
whole ladder rests on and it currently rests on ten pairs.

**3. Elevation** — free API, blocked only by the cache short-circuit above.

**Blocking:** Dutch tributary long records (Waterschap Limburg request; **JCAR
ATRACE** as collaborator; HESS 2024 authors hold 1970–2021 15-min Meerssen).
Dutch Fase thresholds (same request). Radar rainfall + catchment polygons +
`geopandas`, which block only the shared-forcing control.

**Ruled out, do not re-chase:** ERA5-Land (personal CDS key, and ~9 km cells
cannot resolve 27–77 km² catchments — wrong instrument); CAMELS-NL and a Dutch
Caravan extension (neither exists); CAMELS-DE (daily, ends 2020); GRDC (main stem
only); DWD REGNIE (retired); deeper Waterschap history (hard-capped).

**Provenance correction:** EStreams attributes the Dutch tributaries to `NL_RWS`,
but none appear in the live RWS catalogue of 2,635 locations. **Waterschap
Limburg is the holder.**

---

## Environment gotchas

- **Use the project interpreter:**
  `/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python`. The shell
  default is 3.9; the repo needs 3.11+.
- **`pytest` at the repo root FAILS** — 6 collection errors from `archive/tests/`.
  `pytest tests/` gives **81 passed**. Fix: add
  `[tool.pytest.ini_options]` / `testpaths = ["tests"]` to `pyproject.toml`.
  Ruff is clean; `archive/` is excluded from lint.
- **`knmi_pressure_pairs()` silently uses 5 of the 7 stations in `KNMI_COORDS`** —
  two fail the `len(joined) < 2000` test. The pressure decay fit is degenerate:
  10 pairs, correlations 0.9915–0.9993 over 31–114 km, `L` pinned at the
  `max_length=3000` bound with a CI of [8, 3000]. Report the range, drop the fit.
- **`chapter-synthesis.md:241` says 28% of pairs sit inside one correlation
  length.** The true share within 30 km is **46.4%**; 28% is the share within
  20 km. The "network cannot resolve L" argument is weaker than stated.
- **Positional bootstrap blocks are still unfixed** and now live in the shared
  harness (`src/substitution.py:120`). A "72-hour block" can cross the 3,823-hour
  IoT outage. Carry the timestamp index in; sample within contiguous runs.
- The real repo is `~/Desktop/floods/chapter1-co2`. `~/Desktop/chapter1-co2` is a
  near-empty decoy; a `cd` that fails silently lands you there.
- `data/raw/discharge/rws/` is ~2.1 GB of cached JSON, gitignored. The parsed CSV
  is 24 MB; the raw can be deleted.
- No geospatial stack. EStreams tabular attributes work without it; polygons and
  radar do not.
- **`scripts/25_ingest_lanuk_nrw.py` does not capture station coordinates.** That
  blocks using the denser German network to constrain the discharge correlation
  length — the one open test that could settle §2.5.
- `update_data.py` now chains `22_ingest_waterschap_gauges.py --all-discharge`,
  which also writes `discharge_hourly.csv` as a three-column projection. The old
  `01_ingest_discharge.py` is archived; two pipelines over one endpoint had
  drifted apart.
- Grep for `spec_from_file_location` before moving scripts — `21_` loads `19_` by
  path, invisible to ruff and to the tests.

---

## Code style: this is engineered, not analysed

Measured 2026-08-07:

| File | total | docstring lines | report-string lines |
| --- | ---: | ---: | ---: |
| `23_catchment_similarity.py` | 540 | 74 | 44 |
| `src/substitution.py` | 226 | 65 | 3 |
| `28_correlation_length.py` | 301 | 52 | 10 |

- `substitution.py` is 226 lines around ~30 lines of analysis: a 43-line module
  docstring, a 12-field dataclass, two `@property` methods, `verdict()` rendering
  English, and `format_result()`. Return a one-row DataFrame; let the caller
  print. The prose duplicates `chapter-synthesis.md` almost verbatim and will
  drift.
- `23_` spends 44 lines building a text report inside `main()`, interleaved with
  the inference. Tables to CSV, short `print`, done.
- The flashiness expression at `23_catchment_similarity.py:191` is correct and
  unreadable. Two named lines.
- Script numbering no longer conveys order: two `01_`, two `02_`, two `03_`,
  three `04_`, four `05*`, then a jump to 18–28.
- The comments that work are the ones naming a specific past bug
  (`NO_PRESSURE_DROP_HPA`, the coordinate-join note, the coverage floor). Keep
  that pattern; cut the essays.

---

## How this session went, so it can be repeated or avoided

**The recurring failure mode is now named.** Three times this repo has compared a
number against another number produced a different way: the raw-vs-calibrated
Mantel (caught by review 1), the random-fold-vs-forward-chaining laundering
(caught by review 2), and now the cross-fold AUROC pooling and the cross-variable
estimator mismatch. **Before any two numbers go in one table, check that the same
estimator produced both.** This is the check to run first, every time.

**What worked.** Every claim was tested before being written down, and three of
four novelty claims died that way. Two external reviews were read as evidence
rather than accepted wholesale — one of them was refuted on a detail
(`scope-decisions.md` §2, second correction) while its mechanism was upheld.

**What the assistant got wrong in prior sessions, and how it was caught.**

- Claimed three `src` modules had no importers; the grep had omitted `src/`.
- Asserted Rijkswaterstaat holds the Dutch tributaries, retracting a correct
  earlier statement, then re-corrected against the live catalogue.
- Reported the outage-versus-magnitude relationship twice in opposite directions;
  both were artifacts.
- Archived `19_barometric_response.py` and silently broke `21_`.
- Over-read the correlation-length coincidence before computing intervals — and
  the coincidence turns out to be an estimator artifact as well.
- Wrote that random-fold and blocked scores were "produced the same way," which
  review 2 correctly called laundering. The fix addressed the training scheme but
  not the scoring, which is how (a) survived a whole review cycle.

**The user's corrections were the load-bearing ones**: rejecting the two-year
limit, stopping the gauge-failure story from becoming the chapter, naming the
methodology a muddle, and insisting the Eryilmaz CO2 → pressure claim be kept —
which is now the one mechanism claim that survives direct testing.
