# Limburg: full warning-threshold progression analysis

Internal results and interpretation aid for Brian; not dissertation prose.

## What is measured

The supplied current threshold categories are H1 **Increased vigilance**, H2
**Imminent risk of flooding**, and H3 **Flooding**. Apply their discharge values
retrospectively to the supplied 15-minute means. These are neither observed
inundation labels nor a reconstruction of historical warnings: historical
threshold versions are unavailable. Discharge crossings are measured here,
not bankfull stage or flood extent. No equivalent German thresholds are assumed.

All 15 supplied series receive a separate descriptive census (285 linked episodes); the duplicate
Oud-Roosteren series remain separate, not two independent stations. The main
chapter cohort remains six Dutch gauges. Every one of its 724 existing p99
onsets is retained in the threshold bridge, including unknown outcomes.
The primary escalation application starts at H1, not the earlier p99 onset.
The first hourly boundary after H1 is the assessment (0–45-minute delay).
At the rounded assessment, 132 cases remain below H2 and all 133 below H3;
already-above cases are not scored as future escalation. The fixed 72h H1
responses contain 30 H2 positives/one unknown and seven H3 positives/ten
unknown before model-specific input, archive and phase exclusions.
A fixed 72h response and one selected donor per completed prior regional group
preserve the chapter's existing analogue logic. Linking active H1 intervals
within 72h defines episodes; it does not prove that they are individual storms.

## Full native-record census

| Gauge | H1 episodes | Reached H2 | Reached H3 | Unknown H3 outcome |
| --- | ---: | ---: | ---: | ---: |
| Geul / Cottessen | 58 | 16 | 0 | 11 |
| Eyserbeek / Eys | 2 | 1 | 1 | 0 |
| Gulp / Azijnfabriek | 5 | 3 | 0 | 0 |
| Voer / Voervallei | 33 | 2 | 2 | 1 |
| Worm / Hambos | 16 | 8 | 3 | 0 |
| Geleenbeek / Brommelen | 19 | 1 | 1 | 0 |
| **Total** | **133** | **31** | **7** | **12** |

These reach counts cover the linked native episodes and their recovery windows;
the analogue endpoint is the separate fixed 72h period after assessment.
An observed positive survives a later gap; a negative requires complete
follow-up. Unknown outcomes are never converted to negatives.

| Recorded H3 case | H1 entry UTC | First H3 UTC | Elapsed from native H1 |
| --- | --- | --- | ---: |
| Worm 2014 | Jul 8, 15:00 | Jul 9, 23:15 | 32.25h |
| Worm 2018 | Apr 30, 03:00 | Apr 30, 06:30 | 3.5h |
| Eyserbeek 2021 | Jul 13, 18:15 | Jul 14, 13:00 | 18.75h |
| Geleenbeek 2021 | Jul 13, 18:30 | Jul 14, 15:00 | 20.5h |
| Voer 2021 | Jul 13, 19:15 | Jul 14, 16:15 | 21h |
| Worm 2021 | Jul 13, 23:30 | Jul 14, 13:15 | 13.75h |
| Voer 2024 | May 17, 08:15 | May 17, 21:15 | 13h |

Four H3 cases occur in July 2021: seven cases represent four regional episodes,
not seven independent floods. These elapsed times use recorded 15-minute-average crossings, not precise
physical inundation onsets. They are retrospective timings, not available
operational lead times. H1 entry needs observation, and finalized
records, preprocessing and current thresholds are not an as-issued archive.

## Measurement findings that change interpretation

- Correction (2026-10-27): Voer 2024 reaches H3 in both the native and hourly series. The native peak is 5.432 m³/s and the hourly peak is 5.24525 m³/s, both above the current 4.8 m³/s H3 threshold. The earlier statement that averaging hid this crossing was incorrect; the saved numerical outcomes were unchanged.
- The earlier Eyserbeek 2021 p99 onset puts H3 outside its 72h response window.
  H1 anchoring captures that escalation. The p99 bridge therefore has six H3
  positives; its H1/H2 positives are 121/29, with 8/9 unknown respectively and
  18 H3 unknown. Those counts do not replace the native episode census.
- Cottessen's absence of recorded H3 is **not absence of flooding**. Its July
  2021 report describes inundation/out-of-range measurement. The approximate
  26 m³/s capacity in correspondence and 27.5 m³/s in the report/threshold
  table are retained as distinct range sensitivities.
- Gulp's H3 value exceeds the documented rating-domain upper limit; its
  calibration concern around 3 m³/s is separately retained. No reported H3
  cannot establish no physical flood.
- Six of the seven recorded H3 reaches survive the supplied range rules;
  Worm July 2021 remains unknown under that stricter interpretation.
- Eyserbeek/Geleenbeek July 2021 first H3 crossings can remain identifiable
  even where later peaks exceed rating domains. Worm's July 2021 peak is
  provider-flagged. Crossing validity and peak validity are distinct.

## Input availability and comparison rules

Of 133 H1 assessments, 113 have entirely observed 512h discharge histories.
A logged repair of isolated low-flow hours more than 24h before assessment
raises usable temporal histories to 124, retaining all seven H3 cases.
There are 27 substituted hours across 13 histories; two repaired histories
remain incomplete and unavailable. Every native crossing and future response
remains unfilled. Nine episodes still lack a usable full temporal input.
All representations receive the same repaired histories; unrepaired-history
and complete-follow-up results are reported separately. The conventional R0
method also has a maximal cohort requiring its actual features rather than
TTM's 512h history. See the dated design note for exact repair criteria and
literature context. This refinement followed coverage inspection and is not
untouched confirmatory validation.

Donor reach shares are empirical analogue evidence, not calibrated flood
probabilities. Squared errors compare those shares with known native outcomes.
Generic group-balanced prior-archive and same-gauge prior frequencies provide
references. The same-gauge comparison uses only queries with that reference.
Positive-class errors matter because rare positives make low overall errors
possible for an uninformative mostly-negative system. Uncertainty resamples
regional groups and years with 9,999 draws; sparse/undefined contrasts remain
explicit. All/cross-river, 5/10-donor, measurement-quality, old-history and
follow-up sensitivities remain visible rather than selecting a winner.

## What the analogue comparison finds

For the all-river, ten-donor H1 assessment, lower squared error is better:

| Matched cohort / target | Queries (positive cases) | Conventional R0 | Raw + state | TTM + state | Generic archive |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q-history / H2 | 122 (28) | — | 0.2051 | 0.2099 | 0.1914 |
| Q-history / H3 | 114 (7) | — | 0.0614 | 0.0600 | 0.0603 |
| Rain-matched / H2 | 108 (24) | 0.1889 | 0.2078 | 0.2033 | 0.1884 |
| Rain-matched / H3 | 102 (5) | 0.0491 | 0.0505 | 0.0489 | 0.0486 |

These are distinct matched populations, not a ranking across rows. On its
maximal feature cohort, R0 scores 0.2000 versus archive 0.1867 for H2
(129 queries/29 positives), and 0.0573 versus 0.0569 for H3 (121/7).
The broader R0 cohort is not a matched superiority comparison with TTM.

Paired 95% regional-group intervals support the cautious interpretation:
TTM minus generic archive H3 error is -0.00025 [-0.00523, 0.00412];
TTM minus raw/state is -0.00140 [-0.00514, 0.00261]. Annual AlphaEarth
minus temporal-only H3 error is +0.00189 [-0.00544, 0.00883].
Year-resampled H3 TTM-versus-archive results also include zero.

There is a class-specific tradeoff: TTM improves positive-case error over the
near-zero archive frequency by 0.0575 (four-group interval -0.1581 to -0.0172
for TTM minus archive), while worsening negative-case error by 0.00349.
Its positive-case error is still worse than raw/state (0.9186 versus 0.8943).
Report this rather than describing every contrast as null; four positive
regional groups do not establish a generally reliable escalation classifier.

The practical limitation is **poor representation of escalation among selected
precedents**, not just a close contest between foundation and conventional
models. In the Q-history cohort, each method includes any H3-reaching donor
in only three of seven positive cases, though the three cases differ by arm.
TTM's positive-case squared error is 0.9186; its small overall error mostly
reflects the many negatives. The first Worm H3 case (2014) has no completed
H3-reaching precedent anywhere in its eligible archive. July 2021's gauges
cannot donate to each other because their regional event is still underway.
These are observable archive-support limits, not a claim that floods cannot
be forecast by another system.

Same-gauge prior frequencies give a further check: for Q-history H3, the
same-gauge reference scores 0.0624 on 109 available queries; matched TTM
scores 0.0628 and raw/state 0.0642. For H2, that reference scores 0.1876
on 117 queries versus TTM 0.2103 and raw/state 0.2053. Thus the generic
archive comparison is not concealing an obvious advantage over a local
historical base rate.

AlphaEarth does not supply a clear practical escalation gain here. In its
separate 67-query H2 cohort, temporal-only scores 0.2109 versus annual
AlphaEarth 0.2231; in the 64-query H3 cohort, 0.0920 versus 0.0939.
Area, identity and fixed-2017 controls remain in the outputs. This does not
undo the earlier hydrograph-timing results: escalation is a different endpoint.

The Q-history H3 complete-follow-up sensitivity retains only three positives;
its TTM error is 0.0279 versus archive 0.0271. Entirely observed histories also
retain three positives (104 queries), with TTM 0.0306 versus archive 0.0286.
Quality sensitivity retains four positives (103 queries), with TTM 0.0388
versus archive 0.0384. The falling errors mainly accompany removal of positive
cases; they are not evidence that stricter exclusions improve warning skill.
Do not promote a favorable point estimate selected from these comparisons.

This full analysis establishes recorded escalation timings and shows where
measurement resolution, missingness and sparse prior extremes defeat the
analogue application. It does **not** establish useful standalone escalation
prediction or an AI advantage. Preserve the unfavorable result alongside the
chapter's other analogue endpoints, without adding models to chase a gain.

## Reproduce and inspect

```bash
python scripts/86_analyse_warning_threshold_progression.py
python scripts/87_audit_warning_threshold_results.py
```

Use the pinned foundation environment. Local outputs are in
`results/warning_threshold_progression/`: full episode and entry tables,
H1/p99 outcomes, model-specific coverage, all selected donors, event scores,
paired intervals, per-gauge results, source/repair receipts and hashes.
`census_browser.html`, `threshold_episode_counts.png`, and the six-page
`episode_atlas/` expose all 34 primary episodes with H2/H3 or range concerns;
all pages received AI visual inspection, separate from Brian's human review.
The source audit also recovers the supplied final midnight endpoint: six
additional complete final hours are documented, without modifying earlier runs.

Whole-record masking of observed low-flow hours checks how accurately the
neighbor-average input repair reproduces known values. This checks numerical
behavior; it cannot prove that genuinely missing intervals concealed no peak.
The independent audit verifies 2,571 native phase outcomes, all 285 linked
source-series episodes, 519,900 selected donor rows and 109,656 event-score
rows. Summary discrepancies are at most 1.4e-16. All 27 input repairs satisfy
the stated source-record checks. Masking uses 826,445 observed low-flow hours:
mean absolute error ranges 0.0045–0.0610 m³/s by gauge, with a worst case of
5.10 m³/s. The tail error reinforces retaining the unrepaired sensitivity.
All 6,864 estimable intervals have 9,999 finite draws; 304 sparse/undefined
contrasts remain explicitly reported. The complete test suite passes 150 tests.

No new data request, training, operational warning claim, or dissertation prose.
