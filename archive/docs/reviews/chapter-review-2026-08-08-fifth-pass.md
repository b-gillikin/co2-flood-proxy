# Chapter Review — Fifth Pass, Independent

Date: 2026-08-08. Follows `chapter-review-2026-08-07-fourth-pass.md`.

**Method.** Read `README.md`, every document in `docs/`, `src/event_study.py`,
`scripts/31_event_study_gates.py`, `scripts/03_eryilmaz_replication.py`,
`scripts/01_eda.py`, `scripts/25_ingest_lanuk_nrw.py`, `scripts/update_data.py`,
both test modules, `archive/README.md`, the archived chapter draft and
`chapter-prework/Lit-scaffold - chapter draft.docx`. Prior reviews were read as
claims to check, not findings to repeat.

**What was executed.** Unlike the two previous passes, the sandbox worked. The
test suite, both ruff commands, the gate audit and every quantitative claim below
were run against the data actually on disk in
`/Users/briangillikin/miniforge3/envs/chapter1-co2`. Nothing here is marked
unverified. Numbers are given so they can be disputed.

- `python -m pytest -q` → **41 passed**
- `ruff check .` → passed; `ruff format --check .` → **60 files** already formatted
  (HANDOFF says 59)
- `python scripts/31_event_study_gates.py --report-only` → FAIL, one of nine
  contracted files present, as documented

---

## Verdict

The rewrite is sound and the document set is coherent. I agree with the fourth
pass on that, and on most of its technical findings.

I disagree with its central strategic claim. The fourth pass proposed the German
LANUK cohort as a fallback that "may need no gate lowered at all." I ran that
check. **The cohort is real for the discharge population and false for the
Kerkrade arm.** The two Wurm gauges it names both carry multi-year interior holes
that remove July 2021 and everything up to 2024, and the later-recurrence gate
resolves to **two events, not the three the protocol requires**. §1.

Two further problems are new. The transfer estimator's function signature
contradicts the protocol's own per-fold estimation rule (§3), and the one live
analysis in the repository builds validation folds that are contiguous in row
position but span a 159-day outage in calendar time (§4).

Sections 5 lists what I checked and found sound, including two things I expected
to be broken and which are not.

---

## 1. The German cohort: what is actually on disk

The fourth pass §1 reads `lanuk_stations.csv`, which reports each gauge's first
and last observation. It does not report what lies between them. On the series
themselves:

**The discharge population claim survives.** Of 42 gauges, 38 carry observations
in 2005–2026. Using the repo's own `episode_onsets` at each gauge's own p99 over
that window, **27 gauges clear the ≥20-episode gate** and the pooled set gives
**374 regional storms** against a gate of 40. Ten distinct watercourses is
plausible from this. That part of the fourth pass is correct and is the single
most useful thing in it.

**The Kerkrade pair claim does not survive.** `herzogenrath_2` and `honsdorf` do
end at 2026-06-30, but:

| gauge | last observation before the flood | first observation after | interior gap |
| --- | --- | --- | --- |
| `honsdorf` | 2021-07-09 19:00 | 2024-09-20 08:00 | **1,168 days** |
| `herzogenrath_2` | 2021-06-30 22:00 | 2024-01-28 05:00 | **941 days** |
| `herzogenrath_1` | 2021-06-30 22:00 | — (record ends) | — |
| `randerath` | 2021-07-01 01:00 | — (record ends) | — |

Neither pair candidate observed July 2021 at all, and neither observed 2021–2024.
The station table's `end` column shows 2026-06-30 for both, which is what the
fourth pass read.

**The later-recurrence gate fails on this pair.** Running the gate's own
`complete_precursor_events` logic against `iot_hourly.csv`:

| gauge | p99 onsets inside the IoT era | with all 72 pre-onset CO2 **and** pressure hours |
| --- | ---: | ---: |
| `herzogenrath_2` | 3 (2025-04-24, 2025-07-02, 2025-09-09) | **2** |
| `honsdorf` | 1 (2025-09-09) | **1** |

`honsdorf`'s single event is the same 2025-09-09 regional event as one of
`herzogenrath_2`'s. So the design's own minimum — three exact-onset Kerkrade-pair
events with complete windows — resolves to **two**, and `scope-decisions.md` §18
is explicit that fewer events are *absence of recurrence evidence, not a null*.

**The binding constraint is the IoT record, not the gauge.** `iot_hourly.csv` is
**31.7% observed** (4,088 of 12,885 hours carry both CO2 and pressure) and the
missingness is not scattered — it is six blocks, the longest 159 days:

```
2025-01 0.42  2025-02 0.95  2025-03 0.00  2025-04 0.00  2025-05 0.00
2025-06 0.15  2025-07 1.00  2025-08 1.00  2025-09 1.00  2025-10 0.24
2025-11 0.00  2025-12 0.00  2026-01 0.00  2026-02 0.00  2026-03 0.48
2026-04 0.40  2026-05 0.00  2026-06 0.00  2026-07 0.58
```

There are **four** contiguous observed runs of 72 hours or more in the entire
record. Any Kerkrade high-water event that does not land inside February 2025 or
July–September 2025 cannot produce a complete precursor window, whatever the
gauge does. Recovering the Viefhues 2020–2021 package does not fix this: that
package serves the censored anchor, not the later-recurrence arm.

**What this means.** The German cohort is worth pursuing for the discharge
population — it costs no correspondence and reaches ten watercourses. It does not
rescue the Kerkrade CO2 arm, and the fourth pass's "no gate lowered" reading
should not go to the supervisor unqualified. The honest statement is: *the
transfer study is executable on German data; the local recurrence question is not
yet estimable and its feasibility depends on sensor uptime through the coming
winter, not on any data request.*

**Framing cost, unchanged.** The question says "Across Limburg tributaries." A
Rur/Wurm cohort is North Rhine-Westphalia. `chapter-prework/Lit-scaffold` §1.2
already states the hydrological defence — Kerkrade drains to the Wurm, a Rur
tributary, and so to the Maas — but this is a supervisor decision, not a
technical one.

---

## 2. The "ten common years" gate is hollow, demonstrated

The fourth pass §3 item 1 identified that `common_span` takes endpoints and has
no density floor. Here is what it costs on a real candidate cohort. Ten German
gauges with ≥20 episodes each, 2005–2025:

- `common_span` reports **19.66 years** → **passes** the ≥10-year gate.
- Hours inside that span where **all ten** gauges are observed: **6,682 of
  172,239 = 3.9%**.
- Longest run with all ten observed: **37 hours**.
- Per-gauge observed fraction inside the "common" span ranges **38.9%**
  (`boisheim`) to **92.3%** (`eschweiler`).

The design does not need all ten gauges at once, so 3.9% is not directly the
analysis sample. The quantity that matters is the **donor-flow signal**, which
§6 evaluates at `onset − 1 h` and needs `onset − 13 h` for its 12-hour change:

| receiver | donor | events | donor level + 12 h change both available |
| --- | --- | ---: | ---: |
| `herzogenrath_2` | `eschweiler` | 105 | 97 (**92%**) |
| `roetgen_w` | `mulartshuette` | 87 | 74 (**85%**) |
| `kornelimuenster` | `mulartshuette` | 68 | 56 (**82%**) |
| `baltes` | `landesgrenze` | 83 | 64 (**77%**) |
| `honsdorf` | `herzogenrath_2` | 84 | 61 (**73%**) |
| `molzmuehle` | `boisheim` | 128 | 45 (**35%**) |

Event attrition on the donor signal ranges **35% to 92% by pair**, and because
the outages are multi-year blocks rather than scattered hours, **the attrition is
correlated with time block — the exact axis the transfer design holds out.** A
held-out block that coincides with a donor outage yields few or no events, and
`heldout_signal_transfer` `continue`s past an empty fold without recording it.

This makes the fourth pass's §4b (no minimum fold occupancy) load-bearing rather
than hypothetical. Two things follow:

1. Add a **minimum observed fraction over the joint span** to the gate, as the
   fourth pass proposed, and add a **per-signal, per-pair availability gate**.
   The joint-span fraction alone would not have caught the `molzmuehle`/`boisheim`
   case.
2. Pre-specify a **minimum fold occupancy**, and make `heldout_signal_transfer`
   emit a row with `n_heldout_events = 0` rather than skipping. Silence and zero
   are different findings and only one of them is currently visible.

---

## 3. The transfer estimator's signature contradicts the protocol

This is new and it is a design-level defect, not a bug.

The protocol makes two things **fold-specific**:

> §4: "For each crossed validation fold, estimate the receiver's p99 and p95 from
> its observations outside the held time block."
>
> §8: "Before the contrast, express public and Kerkrade summaries relative to the
> quiet-period median and MAD estimated outside the held time block."

So both the **event set** and the **contrast values** differ across folds.

`heldout_signal_transfer(contrasts, ...)` takes **one** contrast table with
columns `watercourse`, `time_block`, `signal`, `contrast`, and then enumerates
all watercourse × block folds internally (`src/event_study.py:119-122`). A single
`contrast` column can only have been computed one way. The function as written
therefore either:

- requires the caller to have standardised **globally**, which is the leak §8
  exists to prevent; or
- is the wrong shape for the protocol, and needs a `fold` key so that each
  (receiver, block) fold carries its own thresholds, scaling and event set.

There is no caller yet, so nothing is currently wrong on disk. But this is the
one function whose output *is* the chapter's answer, and its signature currently
invites the error the protocol was written to forbid. **Fix the signature before
the caller exists**, and add a test that a global-scaling table and a per-fold
table give different answers.

The same class of problem, already named by the fourth pass §4c and confirmed
here: `quiet_control_times` has no holdout-block parameter. §5's rule ("controls
for a held-out event lie inside the held block; controls for a reference event
lie outside it") is delegated entirely to the caller's `available` mask. I had to
construct that mask by hand to test §5 at all (see §5 below). Make the holdout a
parameter.

**A smaller structural note.** The Kerkrade CO2 signals exist in one watercourse
and, because the IoT record is 2025–2026, in one time block. For every fold
either the held set or the reference set is empty, so `heldout_signal_transfer`
will emit **no CO2 rows at all**, silently. The protocol handles CO2 recurrence
separately in §10, so this is correct behaviour — but it should be stated, not
discovered.

---

## 4. The one live analysis has calendar-incoherent folds

`03_eryilmaz_replication.py` is the only completed analytical script in the live
tree. The third pass's two findings against it — hard-coded interpretive prose,
and a 5-cluster bootstrap CI presented as a sampling interval — are both **fully
fixed**. The summary is now computed end to end and reports per-fold gaps instead
of a fake interval. Credit where due.

A different problem remains, and it is the same species the repo has caught
before. `TimeSeriesSplit` slices the **complete-case** frame by row position. The
complete-case frame is 3,964 rows drawn from an 18-month record that is 32%
observed with multi-month outages. The resulting folds:

| fold | test rows | test span | calendar coverage | positives | largest internal gap |
| ---: | ---: | --- | ---: | ---: | --- |
| 1 | 660 | 2025-06-27 → 07-25 | 100% | 158 | — |
| 2 | 660 | 2025-07-25 → 08-21 | 100% | 71 | — |
| 3 | 660 | 2025-08-21 → 09-18 | 100% | **8** | — |
| 4 | 660 | 2025-09-18 → 2026-03-24 | **15%** | 17 | **159 days** |
| 5 | 660 | 2026-03-24 → 07-21 | 23% | 168 | 88 days |

Fold 4's test set is two disconnected chunks six months apart. Fold 3 estimates
an AUROC of 0.962 from **8 positive hours**. Fold 1 trains on what is effectively
February 2025 and tests on July 2025, so the temporal scheme is also a
winter-to-summer comparison. And the headline "mean paired gap −0.012" for
forward chaining is produced entirely by fold 5's −0.104; the other four folds
are +0.016, +0.010, +0.018, +0.001.

Training still precedes testing in every fold, so there is no leakage. The
summary's caveat — that the schemes use different test periods and are not a
leakage-penalty estimate — is directionally right. It understates the problem: it
does not say that two of five folds carry fewer than 20 positive hours or that
one test fold is bisected by a 159-day outage.

Separately, `random_five_fold` shuffles hours inside a record with strong hourly
autocorrelation in both CO2 and pressure, so every test hour has training
neighbours an hour away. Both schemes are defensible only as description.

**Recommendation.** If this stays in the chapter as predecessor context, report
the five forward-chaining folds individually with their positive counts and
calendar spans, drop the mean, and say in one sentence that fold 4 spans an
outage. If it does not stay, delete it rather than carry an artifact that a
referee can take apart.

---

## 5. Checked and sound

Reported because a review that only lists defects misrepresents the state.

- **Control supply is not a constraint.** I expected §5's rules (same calendar
  month, same UTC hour, >7 days from any receiver p95 exceedance and any regional
  storm onset) to starve winter events. They do not. On a ten-gauge German
  cohort, **866 of 866 events receive the full five controls**. Applying the
  stricter §5 holdout rule — a held-out event's controls must lie inside the same
  time block — **also gives 5/5 for all 866 events**. About 49% of the hourly grid
  survives the exclusion, with a January minimum of 34.5%. The design is not
  fragile here.
- **Episode chaining is bounded in practice.** The fourth pass §4d is right that
  `episode_onsets` compares each crossing to the previous crossing, not the last
  kept onset, so chains are unbounded in principle. Measured: **3–5% of episodes
  absorb more than 72 hours**, with a maximum of 199 hours at `herzogenrath_1`.
  It still needs declaring in §4 alongside the storm rule, but it is a footnote,
  not a threat to the ≥20-episode gate.
- **LANUK logging density is not flow-dependent in the modern era.** I checked
  whether the archive logs more densely during events, which would bias each
  gauge's own p99. It does not: `eschweiler` 2010–2019 is 99.5% observed on
  top-5% flow days against 97.4% on median days, and Spearman correlation between
  monthly observed fraction and monthly peak flow is +0.05 to +0.17 across four
  gauges. The low 2005–2026 fractions are multi-year outages, not event-triggered
  sampling.
- **`pressure_residuals` gap handling is correct.** Each lagged difference
  requires `lag + 1` observed values *and* an index span of exactly `lag` hours.
  The fourth pass called this the best code in the repository; I agree.
- **No dangling references in the live documents.** Every file path in the live
  docs either exists or is a contracted input that deliberately does not yet
  exist. The reviews and `decisions.md` reference retired scripts, which is
  correct for historical documents.
- **No secrets in tracked files.** Credentials are read from environment
  variables; `local.settings.json` is ignored and `local.settings.example.json`
  carries placeholders only.
- **Test suite, linting and the gate audit all behave as documented.**

---

## 6. Smaller defects

1. **`environment.yml` has no geospatial stack.** No geopandas, fiona, shapely,
   pyproj or rasterio, while one of nine hard gates is a `.gpkg` and the primary
   rainfall exposure is an area-weighted polygon mean. Confirmed; fourth pass §4f
   stands.
2. **The polygon contract is checked by filename only.** `event_study_catchments.gpkg`
   is never opened — no CRS, no geometry count, no match against the watercourse
   list. Fourth pass §3 item 2 stands.
3. **Nothing gates that the joint span contains July 2021**, though §5 of the
   synthesis calls it a required anchor. Given §1 above, this now matters more,
   not less: the German cohort's July 2021 coverage is gauge-specific.
4. **The pre-committed readings are in the wrong file.** `chapter-synthesis.md`
   §7 holds the interpretive commitments; `chapter-scope-and-preregistration.md`
   is the document that locks and contains none. Fourth pass §4a stands and is
   cheap to fix.
5. **`results/` holds orphaned artifacts from cut lanes.** `results/transferability/`
   (12 files), `results/precursor/`, `results/baseline/` and
   `results/eda/co2_discharge_soft_labels.png` were produced by code that no
   longer exists in the working tree. `results/` is gitignored, so nothing records
   their provenance. This is the hazard the third pass named in its §7, recreated
   in a new place. Delete them or move them under `archive/results/` with a note.
6. **`add(rows, "Primary discharge series", ..., len(gauge_names))`** passes an
   int into an otherwise-text column. Cosmetic.
7. **§5's "exclude an event with fewer than three controls" is not implemented
   anywhere.** `quiet_control_times` returns up to `n_controls` with no minimum.
   Another caller responsibility with no caller.

---

## 7. Document and repository state

**Good.** README, synthesis, protocol, inventory, data-requests and scope
decisions tell one consistent story. `decisions.md` is append-only, dated, and
structured decision/reasoning/consequence throughout — it is the best artifact in
the project and a committee that reads it will trust the author.

**Stale, in order of consequence:**

1. **`chapter-prework/Lit-scaffold - chapter draft.docx` (tracked, 30 KB)
   describes a different chapter.** It frames the work as "ensemble time-series
   anomaly detection with SARIMAX residuals, Kalman innovations, and Isolation
   Forest scores" — everything `analysis-inventory.md` lists as stopped — and
   states that July 2021 "is not in the analyzed data window," which the current
   design contradicts by making it a required anchor. Its literature blocks and
   §1.2 hydrological framing are genuinely valuable and should be kept. The
   framing sections should carry the same superseded banner the archived chapter
   draft carries.
2. **`HANDOFF.md` closes with "The worktree is intentionally uncommitted."** Five
   commits have landed since. It also reports 59 formatted files against a current
   60, and 41 passing tests, which is right.
3. **`chapter-review-2026-08-07-fourth-pass.md` is untracked.** The German-cohort
   proposal — the most consequential idea in the last three passes — exists in one
   untracked file on one machine. The third pass raised exactly this pattern as
   its item 1.

**No chapter prose exists.** The only draft is `archive/chapter/chapter-draft.md`,
correctly banner-marked as machine-generated scaffolding against a retired
question. That is defensible at this stage, but it should be a conscious position
rather than an omission: the repository currently contains a protocol, a gate and
a literature scaffold, and no manuscript.

---

## 8. Do next, in order

1. **Re-run the German-cohort feasibility with §1's numbers in hand**, and take
   the split verdict to the supervisor: transfer study executable, Kerkrade
   recurrence arm at two of three required events and gated on sensor uptime, not
   on any data request.
2. **Fix `heldout_signal_transfer`'s signature** so folds carry their own
   thresholds and scaling (§3), and give `quiet_control_times` a holdout-block
   parameter. Both before a caller exists.
3. **Add the observation-density gate, a per-pair donor-availability gate, a
   July-2021-in-span gate, and open the `.gpkg`** (§2, §6 items 2–3).
4. **Pre-specify minimum fold occupancy** and make empty folds emit a row rather
   than be skipped (§2).
5. **Move `chapter-synthesis.md` §7 into the protocol** (§6 item 4).
6. **Commit the fourth-pass review and this one**; refresh `HANDOFF.md`'s closing
   paragraph.
7. **Banner or split the Lit-scaffold docx** (§7 item 1).
8. **Decide the Eryilmaz script's fate** (§4): per-fold reporting, or delete.
9. **Clear or archive the orphaned `results/` directories** (§6 item 5).
10. **Declare the episode chaining rule** in §4 with its measured reach.

Items 2–5 and 10 are protocol and code work that costs days, not deliveries.
Item 1 is the one that changes what the chapter can promise.

---

## On the state of the project

Three passes have now called the self-review discipline unusual, and it is. What
has changed since the fourth pass is that the discipline is no longer the binding
constraint — execution is. The protocol is tight, the gate refuses to be lowered,
and the definitions that matter are tested. What the repository does not have is
a single event contrast computed under it.

The fourth pass framed that as a strategic risk waiting on external deliveries.
After running the checks, the picture is narrower and more actionable: the
discharge population is already on disk and can be built without correspondence,
the rainfall exposure needs work that is entirely internal, and the only arm that
genuinely depends on something outside the author's control is the Kerkrade CO2
recurrence — where the constraint turns out to be a 31.7%-observed sensor, not a
missing archive. That is a better position than the fourth pass described, and a
worse one than it concluded.
