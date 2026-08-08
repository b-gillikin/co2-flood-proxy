# Chapter Review — Fourth Pass

Date: 2026-08-07. Reviews the event-study rewrite that replaced the substitution
design. Follows `chapter-review-2026-08-07-third-pass.md`.

**Method.** Read the new protocol, `src/event_study.py`, `scripts/31_event_study_gates.py`,
`tests/test_event_study.py`, and every document in `docs/`, against each other and
against the data actually on disk.

**What could not be done.** The execution sandbox is still down from the previous
pass, so the test suite was not run and `git` state was not inspected. Claims
needing execution are marked **[unverified]**.

---

## Verdict

The rewrite is a large net improvement in method and in document discipline. The
worst problem in the last review — a canonical document carrying two withdrawn
results, with the corrections living only in an untracked file — is **fully
fixed**. README, synthesis, protocol, data-requests and HANDOFF now tell one
consistent story.

It has also introduced one strategic problem that outweighs most of the technical
gains: **the chapter is now unexecutable, and the document set has not noticed
that a qualifying discharge cohort is probably already on disk.**

That is §1. Everything else is smaller.

---

## 1. The long-record cohort may already be held

`docs/data-requests.md` §2 lists LANUK NRW as **alternative route 3**, behind two
requests that have not been sent. On the evidence of `data/interim/lanuk_stations.csv`
it should be route 1.

**What is on disk.** 42 German gauges on the Rur, Wurm, Inde, Niers and Schwalm,
hourly, in `lanuk_discharge_hourly.csv`. Counting from the station table, roughly
**29 gauges have 18+ years overlapping RADOLAN's 2005 start and run to 2024–2026**
— Monschau (1953→2025-11), Stah (1960→2026-01), Eschweiler (1965→2025-05),
Jülich Stadion, Linnich, Selhausen, Altenburg, Goch, Weeze, Kornelimünster,
Boisheim, Molzmühle and others.

**The Kerkrade pair is in it.** `herzogenrath_2` and `honsdorf` both sit on the
Wurm, both carry 48.7-year records, and **both run to 2026-06-30**. The Wurm
crosses the border at Rimburg, where the donor instrumentation is. The protocol's
Worm/Wurm gate is satisfiable without a request.

**July 2021 is in it, and so is the censoring.** Most gauges carry 300–360
observed hours in July 2021 with a recorded peak. The six terminations — Randerath
(07-01), Welz, Luchem, Herzogenrath 1 (06-30), Kirchberg 1, Reifferscheid
(07-14 13:00, mid-peak) — are exactly the interval-censored anchor the protocol
requires, and they are *documented failures*, not missing-at-random.

**The other two long inputs line up on the same footprint.** RADOLAN is DWD
gauge-adjusted German radar from 2005 — native to this area, not an extension to
it. DWD precipitation (1995–2026) is already held. A 2005–2026 window gives 21
common years against a 10-year gate, and it sidesteps the NRW sampling-density
change the repo documented (2020s median inter-record gap 15 min; 1950s 216 min).

**Why this matters more than convenience.** `data-requests.md` §2 records that the
Dutch tributary archive lies beyond the public endpoint and needs Waterschap, the
HESS 2024 authors or JCAR ATRACE to answer. Meanwhile the protocol makes July
2021 a *required* anchor — and the Dutch public record starts 2024-08. **The
German cohort is not a fallback for the discharge population; it is the only
route on the list that reaches the anchor the protocol requires.**

**What it costs.** The question says "Across Limburg tributaries." A Rur–Wurm
cohort is North Rhine-Westphalia. Same Maas basin, same transboundary system, the
Wurm running through both — but the framing changes and that is a supervisor
decision, not a technical one. It is also a *better* July 2021 story than the
Dutch side can tell.

**What is still needed.** A watercourse assignment (one representative gauge per
natural watercourse — the station table carries names, not watercourses), gauge
coordinates, and polygons. The NRW metadata product identified in earlier sessions
(`OpenHygon_meta.zip`, 66 KB, public, no key) carries coordinates for 196 gauges
and would close the first two.

**[unverified]** — this reads the station table, not the series. Per-gauge
observation density over 2005–2026, the distinct-watercourse count and the
p99-episode counts all need checking before the claim is load-bearing. That check
needs no external request and should take under a day.

---

## 2. Real improvements, named so they survive the next rewrite

- **`pressure_residuals` differences are gap-aware.** Each lagged change requires
  both `lag + 1` observed values *and* an index span of exactly `lag` hours. This
  replaces a bare positional `.diff(lag)` and is now the best code in the
  repository. `test_pressure_change_does_not_bridge_an_omitted_timestamp` guards it.
- **`episode_onsets` requires both adjacent hours observed.** The exact bug class
  that produced three withdrawn results in this project, closed at the definition.
- **Thresholds are estimated per fold.** p99/p95 come from outside the held block,
  so the *event definition* no longer leaks. The old design had this leak and
  nobody had named it.
- **Storm-level resampling** is the right unit and is specified, not left to a
  caller.
- **July 2021 is interval-censored and never imputed**, with a gate requiring
  explicit lower/upper onset bounds.
- **"A nonrecurring residual is a planned substantive conclusion, not grounds to
  alter the pressure baseline"** (§10). That single clause closes the most likely
  route to a laundered result in the whole design.
- **The gate concept itself.** An executable audit that exits nonzero, plus a
  written refusal to rename the rolling files into the contracts, is a stronger
  discipline than anything in the previous design.
- **`testpaths = ["tests"]`** added — third-pass §6 item 3 actioned.
- **Documentation is coherent.** This was the worst finding of the last review and
  it is resolved.

---

## 3. Gate-script defects

| # | Defect | Severity |
| --- | --- | --- |
| 1 | **No observation-density gate.** `common_span` takes the latest `first_valid_index` and earliest `last_valid_index` per column, so a gauge observed in 2006 and 2025 with nothing between passes a 19-year span. The backstop — ≥20 p99 episodes — is computed against the gauge's *own* p99 over whatever it observed, so one dense year can clear both. The retired design had an 80% coverage floor and it caught real problems. **Add a minimum observed fraction over the joint span.** | **High** |
| 2 | **The polygon contract is checked by filename only.** `event_study_catchments.gpkg` is never opened: no CRS check, no geometry count, no match against the watercourse list. It is the input the entire rainfall exposure rests on, and §11 requires visual verification. | **High** |
| 3 | **Nothing gates that the joint span contains July 2021**, though the protocol calls it a required anchor. A 2005–2015 cohort passes every gate and contains none of it. | Medium |
| 4 | `common_span` divides by 365 days, so "10 years" is 3,650 days. Consistent with the documented definition; ignores leap days. | Cosmetic |
| 5 | `add(rows, "Primary discharge series", ..., len(gauge_names))` passes an int into a column that is otherwise text. | Cosmetic |

---

## 4. Protocol gaps

**4a. The binding document has no decision rule.** §9 says "Do not impose a
success proportion or magnitude threshold." Declining an arbitrary threshold is
statistically defensible — but the pre-committed readings then live in
`chapter-synthesis.md` §7, which is *not* the document that gets locked. As
written, the artifact that freezes before outcome inspection contains no
interpretive commitment at all. **Move synthesis §7 into the protocol.** It is
good content in the wrong file.

**4b. No minimum fold occupancy.** The crossed design is watercourses × 5
**equal-duration** blocks. Over a decade with winter-clustered events, many folds
will hold zero events for a given signal, and `heldout_signal_transfer` silently
`continue`s past them. It reports `n_heldout_events`, so the information survives
— but there is no rule and no gate, and the transfer conclusion could rest on a
handful of folds with nothing flagging it. Pre-specify a minimum, and report the
occupancy distribution.

**4c. The most leakage-prone rule is unimplemented and untestable.** §5 requires
that controls for a held-out event lie inside the held block and controls for a
reference event lie outside it. `quiet_control_times` has no block parameter, so
this is delegated to the caller via the `available` mask — and the caller does not
exist. §11 lists "control contamination" among the required pre-execution tests.
**Make the holdout a parameter of the function, not a caller responsibility.**

**4d. Episode merging is unbounded single-linkage and the protocol does not say
so.** `episode_onsets` compares each crossing against the *previous crossing*, not
the last kept onset, so crossings 71 hours apart chain indefinitely — a wet
fortnight with a crossing every two days becomes one episode.
`test_episode_onsets_merge_consecutive_recrossings_through_72_hours` shows three
crossings spanning 144 hours collapsing to one, so the behaviour is deliberate and
tested. But it is undeclared, and it feeds the **≥20 episodes per watercourse hard
gate** directly. The protocol declares the single-linkage rule for *regional
storms* and commits to reporting chain length; make the same declaration and the
same commitment for episodes.

**4e. The primary target reverted to a within-record percentile.** Fase is now "a
sparse sensitivity" and own-p99 is primary. The stated reason — inventory Fase
values at non-designated points may not be the statutory thresholds — is a good
catch and probably right. But `scope-decisions.md` had a documented decision the
other way, and the chapter loses "the receiver crosses the province's own yellow
threshold," which `analysis-inventory.md` called the far stronger sentence. A
defensible trade, but record it as a reversal rather than a silent replacement.

**4f. `environment.yml` has no geospatial stack.** No geopandas, fiona, shapely,
pyproj or rasterio — while one of nine hard gates is a `.gpkg` and the primary
rainfall exposure is an area-weighted polygon mean.

---

## 5. What the redesign gave up, measured against the two supervisor constraints

Stated plainly, because the documents do not.

**Constraint 2 — a transferability component — is now much weaker.** §6 uses the
**nearest** other-watercourse gauge and distance never varies. So *how far donor
information reaches* is no longer asked. "Transfer" now means sign concordance of
a contrast across held-out folds — a real and defensible thing to measure, but it
is out-of-sample validation of a descriptive contrast, not a measurement of reach.
The per-donor decay distribution (−0.58 to +0.21 across 36 donors), which the
previous inventory called the answer to the first question anyone would ask, is
gone with the scripts.

**Constraint 1 — the sequence — is now narrative rather than structural.**
Eryilmaz's inherited 0.05 threshold is gone; `chapter-synthesis.md` §8 calls the
Eryilmaz work "same-site predecessor context only." The lineage is now told in
prose rather than carried by a shared decision rule.

Both may be the right calls. A contrast study on ten years is more honest than a
substitution ladder on two. But these are **losses against the two stated
constraints**, and they should go to the supervisor as deliberate choices rather
than be discovered by him.

---

## 6. The strategic problem

The project has moved from *computable now, with methodological problems* to
*methodologically tight, computable only after three external deliveries*. Eight
of nine contracted inputs are absent. The protocol says stop and return to the
supervisor if any gate fails, and forbids substituting the rolling record.

That discipline is correct in spirit and I would not soften it. But there is **no
fallback design**, and the blocking request is the one this repository already
documents as lying beyond a hard-capped public endpoint. One non-reply from
Waterschap and there is nothing.

**Pre-specify a reduced-scope fallback now, before any outcome is seen**, so that
it is a planned branch rather than a post-hoc concession. Two candidates:

1. **The German cohort in §1.** May need no gate lowered at all, and reaches the
   July 2021 anchor that the Dutch route cannot.
2. A shorter-span version with specific gates lowered — **with the lowering
   written into the protocol before lock**, not after a gate fails.

Option 1 is much better and should be tested first because it costs a day and no
correspondence.

---

## 7. Do next

1. **Test the German cohort** (§1). Per-gauge density over 2005–2026, distinct
   watercourse count, p99 episode counts, and whether the NRW metadata product
   closes coordinates and watercourse names. No external request needed.
2. **Move `chapter-synthesis.md` §7 into the protocol** (§4a). The readings must
   live in the document that locks.
3. **Give `quiet_control_times` a holdout-block parameter** and write the
   contamination test (§4c).
4. **Add the observation-density gate and a July-2021-in-span gate; open the
   `.gpkg`** (§3, items 1–3).
5. **Declare the episode chaining rule** and commit to reporting chain length
   (§4d).
6. **Supervisor:** the two constraint losses (§5), the cohort question (§1), the
   public-weather assignment rule, and the pre-committed readings.
7. **Commit.** Outstanding since the 08-06 review; state not verifiable this pass.

---

## On the rewrite as a whole

Worth saying directly, since three of my seven sections are criticisms.

Deleting seventeen scripts, eleven documents and every computable result in favour
of a design that cannot yet run is a hard thing to do and it was, on the merits,
mostly right. The old chapter's problem was never that it lacked analyses; it was
that the analyses answered questions nobody had asked, in currencies that could
not be compared. This design has one estimand, one contrast, applied identically
everywhere, with the gap-honest handling that the old code kept failing to get
right.

The risk it carries is the opposite of the old one. The old repository would
produce a number for anything. This one will produce nothing at all until four
deliveries land, and it has no plan for their not landing. §1 and §6 are the fix
for that, and neither requires giving up any of the discipline that makes the
rewrite better.
