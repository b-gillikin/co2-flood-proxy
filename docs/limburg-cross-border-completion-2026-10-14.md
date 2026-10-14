# Completing the Dutch–German analogue comparison

Internal research aid; Brian writes dissertation prose. Authorized 2026-10-14
following the country-comparison inventory. Runner:
`scripts/84_complete_cross_border_analogues.py`. Separate local outputs:
`results/basin_ai_cross_border_completion/`. No model training or new download.

## Scope and comparisons

1. On the expanded Q-only census, compare pooled, domestic-only and foreign-only
   donor archives. Keep the raw, matched raw/state and ordered-TTM/state methods.
2. Extend the strengthened TTM/state spatial comparison to held Dutch and German
   catchments: temporal-only, log area, gauge identity, fixed-2017 AlphaEarth and
   prior-year annual AlphaEarth. This is a Q-only context population, independent
   of rainfall/weather completeness; it does not overwrite the earlier matched
   Dutch context results or imply that their numerical scores are comparable.
3. Derive German catchment rainfall from held RADOLAN crops and validated
   foundation catchments. Compare the unchanged conventional rain/Q features
   and temporal methods on identical rainfall-complete events and donor pools.
4. Separate Dutch and German estimates and paired model/archive differences;
   retain quality exclusions, all/other-river scenarios and five/ten donors.
5. Preserve and quantify provider-status/measurement differences. Dutch Worm and
   German Wurm remain one physical river throughout.

Country restrictions act on candidates before prior-pool scaling and donor
selection. Thus archive comparisons test the complete archive-conditioned
retrieval method, including its scaling, not a causal effect of foreign data
alone. Eligibility still requires a completed 72h response before query onset,
a different onset-linked regional group and one selected donor per prior group.
Both query and donor quality flags are excluded in the existing sensitivity.

## Comparability and coverage

Report coverage of every scorable event separately from matching performance.
Intervals use the same query IDs on both sides. The primary archive comparison
also requires equal actual donor counts (including equal short archives).
An all-shared-query sensitivity allows different available donor counts and
must be interpreted as a combined archive/count change. Missing comparisons
and too few resampling clusters are recorded explicitly, never filled with zero.
Use the fixed 9,999 paired intact-group draws and calendar-year sensitivity;
intervals remain conditional on the archive and exploratory development.

German-only other-river retrieval is structurally unavailable: both German
stations observe the Wurm. Pooled/foreign archives can provide other rivers,
but that coverage gain is distinct from better accuracy on shared queries.
A German event with no domestic other-river reference cannot contribute to a
paired accuracy difference against that nonexistent reference.

## German rainfall and context preparation

Map provider station IDs `2828300000200` / `2828900000200` to the held
`herzogenrath_1` / `randerath` foundation catchments and embedding identifiers.
Use the validated catchment-year table with the previous calendar year's
embedding. No current/future annual embedding fills an unsupported year.
Keep the fixed 2017 vector as the existing static control, not an as-issued
historical asset. Use all eight held years where supported.

Both German catchments lie entirely inside the held radar crop. Area-average
all intersecting cells using the existing 0.1-mm hourly values. A missing cell
with positive catchment weight makes that hour missing; no spatial filling.
The accumulation ending HH:50 UTC is labeled the following whole-hour end,
matching the Dutch rainfall convention. Require all 512 historical rainfall
hours for the matched rain/Q population, as in the original common-input rule.
No weather, pressure, new stage export or additional provider response is
required for this benchmark. German rainfall extraction is a new derived
product of held data, not a new observation or assumption of perfect rainfall.

## Measurement and inference limits

Dutch and German records are aligned to UTC from fixed UTC+1 source clocks;
German 15-minute right-interval records are aggregated only with complete
quarters. Dutch genuine zeros remain observations. Cottessen flume-capacity
and rating-domain concerns remain part of the existing event review.
German literal rating-period/domain boundaries, complete response stage and
provisional high-flow status remain explicit; all provisional events stay in
the inventory and affected responses remain outside exact-Q scoring.
Redundant-local-sensor continuity is documented without inventing row-level
reconstruction flags. A current datum is not proof of historical datum stability.

Countries are confounded with river composition, station position, record
periods and measurement regimes. Germany contributes two nested gauges on one
river, not a national sample. Country-stratified scores establish behavior in
these archives, not causal national differences or policy performance.
Normalized discharge is not a shared water level or official warning threshold.
Annual AlphaEarth has few independent catchments/years; event counts are not
independent spatial replications. Source-linked analogues remain retrospective,
not warning lead-time or forecast skill, and AI notes remain distinct from
independent human validation.

## Reproduction and checks

```sh
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/84_complete_cross_border_analogues.py
```

The runner checks held prepared inputs and radar crop hashes, records all
consumed numerical and geometry inputs plus relevant code hashes, and saves
coverage, selected donors, event assessments, country/watercourse summaries,
paired intervals and measurement inventory. It checks country/river constraints,
chronology, group uniqueness and quality for every selected set, and requires
its pooled Q-only branch to reproduce existing scores, IDs, ranks and distances
within 1e-12. Original runs and human review fields are untouched.

## Completed readout

The pass is complete: 160,588 repeated score sets and 780,312 selected slots
across configurations. These are computational totals, not independent events.
The actual main populations and archive availability are:

| Cohort | Scorable Dutch / German events | Pooled queries with donors, Dutch / German |
| --- | --- | --- |
| Expanded Q-only | 614 / 237 | 610 / 235 |
| Matched complete rainfall histories | 558 / 212 | 554 / 210 |
| Prior-year context with complete Q histories/responses | 300 / 73 | 294 / 71 |

The Q-only context cohort adds four Dutch scorable events beyond the original
rainfall-covered 296-event context population. Its pooled archive also adds
German donors; earlier Dutch-only scores cannot be treated as the same
comparison. All unsupported years and no-archive records remain in coverage.

### Archive-sharing effects

For ordered TTM/state, all-river five-donor comparisons, requiring identical
query IDs and equal actual donor counts:

- German domestic-to-pooled timing mismatch decreases **1.845h** on 230 paired
  queries: group interval [-2.681, -1.029], year interval [-2.442, -1.231].
  Peak error increases **0.0689** in p99-ratio units: group [0.0264, 0.1129],
  year [0.0335, 0.1077]. Shape difference -0.0017 has intervals including zero.
  The quality sensitivity retains improved timing and worse peak magnitude.
- Dutch domestic-to-pooled shape difference is **-0.00051**, peak difference
  **-0.01281**, timing difference **+0.102h**, on 610 paired queries. All main
  group/year intervals include zero. The quality sensitivity has a supported
  peak increment, so do not describe every Dutch result as identically null.
- German other-river coverage rises from **zero to 235** Q-only queries when
  Dutch donors are allowed. This is additional usable coverage, not an accuracy
  improvement against a nonexistent German-only other-river reference.
- Foreign-only other-river Q retrieval covers **471 Dutch / 235 German** queries.
  The 139 Dutch Wurm/Worm queries cannot use Germany's same-river Wurm records
  under whole-river exclusion. Full pooled coverage remains 610 / 235.

Sharing expands available experience but does not uniformly improve accuracy.
Do not select a country restriction solely from the best observed outcome;
report its coverage and magnitude/shape/timing trade-offs together.

### Country-specific temporal and rainfall benchmarks

Five-donor, pooled, all-river main comparisons. Shape and peak errors are lower
when better; peak errors are relative to the existing era-specific p99.

| Cohort / country | Method | Shape error | Peak error |
| --- | --- | ---: | ---: |
| Q-only NL | raw + state | 0.2003 | 0.6445 |
| Q-only NL | ordered TTM + state | 0.1962 | 0.6346 |
| Q-only DE | raw + state | 0.2011 | 0.4830 |
| Q-only DE | ordered TTM + state | 0.1957 | 0.5138 |
| Rain-matched NL | conventional rain/Q | 0.1996 | 0.6188 |
| Rain-matched NL | ordered TTM + state | 0.1988 | 0.6212 |
| Rain-matched DE | conventional rain/Q | 0.1966 | 0.4161 |
| Rain-matched DE | ordered TTM + state | 0.1970 | 0.4841 |

Against matched raw/state, TTM's Q-only all-river shape increment is -0.00407
NL (about 2.0%) and -0.00543 DE (about 2.7%), supported by main group/year
intervals. Quality filtering retains both directions; the Dutch group interval
then includes zero while its year interval remains negative. This does not establish a
consistent peak advantage. Dutch other-river shape intervals include zero;
the German other-river shape increment remains supported.

The newly possible German conventional benchmark has lower peak error than
TTM in the main rain-matched comparison: TTM-minus-R0 +0.06804, group interval
[0.01832, 0.11939], year [0.01538, 0.12190]. Quality sensitivity narrows this
claim: difference +0.04621, with group/year intervals including zero. Shape
is essentially tied in both countries, not statistically proven equivalent.
Dutch TTM donor-timing mismatch versus R0 improves about 0.80h in the main
all-river run; quality sensitivity makes that increment uncertain. R0 supplies
rainfall whereas these TTM arms use Q/state, so this is a practical benchmark,
not a same-input isolation of learned representations.

### Geographic context: different behavior at the German sites

Pooled other-river, five-donor main context results:

| Country | Context on ordered TTM/state | Shape error | Peak error | Donor timing mismatch, h |
| --- | --- | ---: | ---: | ---: |
| NL | temporal/state only | 0.2126 | 0.6719 | 10.936 |
| NL | fixed 2017 AlphaEarth | 0.2177 | 0.6646 | 9.833 |
| NL | annual AlphaEarth | 0.2177 | 0.6697 | 9.434 |
| DE | temporal/state only | 0.2175 | 0.4514 | 10.279 |
| DE | fixed 2017 AlphaEarth | 0.2170 | 0.5846 | 10.679 |
| DE | annual AlphaEarth | 0.2117 | 0.5082 | 10.262 |

For Dutch queries, annual context reduces timing mismatch **1.502h** versus
strengthened temporal/state: group interval [-2.334, -0.755], year
[-2.928, -0.559]. This direction is supported in the quality sensitivity.
The further five-donor annual-versus-fixed increment **-0.399h** has group/year
intervals including zero. Ten-donor main timing retains an annual-versus-fixed
increment, but that comparison weakens in quality sensitivity. Ten-donor
annual-versus-temporal Dutch shape matching worsens; timing is not a universal
accuracy improvement.

For German queries, annual-versus-temporal main timing difference **-0.017h**
is essentially absent, and shape intervals include zero. Peak error is higher
by **0.05684** (group interval includes zero; year interval is positive).
Annual context improves peak magnitude versus the weak fixed-2017 control
in the five-donor main run, but that difference disappears in the quality
sensitivity. Quality filtering changes German point readings, with group/year
interval disagreement for shape/timing. Do not claim the Dutch timing benefit
has been established at the German sites or that annual embeddings always help.

All area/identity/fixed/annual, country-archive, five/ten and quality comparisons
are retained in the tidy tables. The German other-river area control has much
worse shape than temporal-only, so beating area alone cannot establish an
AlphaEarth advantage over the stronger temporal comparator.

### Provider limitations remain visible

The full German inventory has 338 episodes: 240 documented pre-flood-rating
status and 98 provisional high-flow status; 336 complete Q histories and 237
admissible scoring responses. Two responses cross rating periods. Complete
response-stage coverage does not make an unapproved high-flow Q curve exact.
The redundant-sensor metadata describe unavailable row-level substitution
flags; they do **not** mean every record or event was reconstructed.
Country/provider flag counts are in `measurement_inventory.csv`, and all
selected queries/donors retain the existing quality/chronology restrictions.

Herzogenrath 2 (Broicher Bach) and Honsdorf (Beeckflies) remain outside this
prepared Wurm/foundation cohort; they are not incorrectly labeled Wurm gauges.
This pass completes the requested comparisons within the active cohort, not
an exhaustive analysis of every possible German station or national FEWS.
No additional data request is needed for this pass.

## Remaining-column completion record

| Previously remaining work | Executed evidence |
| --- | --- |
| Domestic versus pooled archive value on matched queries | archive coverage and equal-count/all-shared paired intervals; foreign-only control included |
| Cross-country versus cross-river distinction | independent country policy plus whole-physical-river restriction; structural unavailable cases explicitly recorded |
| Dedicated country-specific paired performance | country summaries and paired model/archive intervals, with main/quality, group/year and five/ten sensitivities |
| Held German AlphaEarth extension | eight gauge catchments, six physical rivers; prior-year context joined to provider IDs and strengthened temporal/state controls |
| German rainfall practical benchmark | full German catchment weights, crop hashes, hour-end labels and 512h completeness; common input/donor populations across R0 and temporal controls |
| Individual measurement differences | provider-status/flag inventory, selected-slot validation and narrow claim definitions; no assumption of equivalent datum, warning thresholds or reconstructed-value flags |

## Validation and reproducible evidence

- **138 tests pass**, including five new country/context/rainfall/pairing tests.
  Repository lint and changed-file formatting/whitespace checks pass. The
  whole-repository formatting check identifies an unrelated pre-existing
  formatting issue in `tools/disaster_recovery.py`; that file is untouched.
- The pooled Q-only scores and selected donor IDs/ranks/distances reproduce
  the previous run within **1e-12**. No upstream result is rewritten.
- Independent script **85**, `scripts/85_audit_cross_border_results.py`,
  reconstructs every selected pair's six response metrics directly from held
  curves and every saved country-summary metric from the event rows: **780,312
  slots / 528 summary rows**, maximum pair difference **2.85e-14**. It verifies
  numerical inputs, source hashes and saved output hashes before inspection.
- A separate direct polygon-intersection check reproduces the nonzero
  2017-07-19 14:00 UTC German rainfall values: Herzogenrath 1 **7.601mm**,
  Randerath **5.296mm**. Missing weighted cells remain missing, verified in tests.
- **21,120** paired interval records include **1,152** explicitly unavailable
  comparisons and **19,968** estimated group/year intervals. No undefined
  comparison is silently dropped or assigned a favorable zero.

Run the independent numerical audit with the same environment as script 84:

```sh
MPLCONFIGDIR=/tmp/limburg-mpl \
PROJ_DATA=/Users/briangillikin/miniforge3/envs/chapter1-co2/share/proj \
.venv-foundation/bin/python scripts/85_audit_cross_border_results.py
```

Main artifacts: `archive_coverage.csv`, `context_event_coverage.csv`,
`rainfall_event_coverage.csv`, `event_assessments.csv`, `selected_donors.csv`,
`summary_by_country.csv`, `summary_by_watercourse.csv`, `paired_intervals.csv`,
`measurement_inventory.csv`, `manifest.json`, `validation.json` and
`independent_pair_audit.json`. Raw provider records and generated evidence
remain local/ignored; only code, tests, internal documentation and decisions
are committed. Numerical trade-offs are not independent human relevance
judgments, calibrated forecast intervals or evidence of operator benefit.
