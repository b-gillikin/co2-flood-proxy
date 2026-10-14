# Current warning-threshold progression: full retrospective analysis

Design recorded 2026-10-14 before this analysis's results. Brian requested a
full census, not a sampled pilot. This is an observational retrospective
analysis using the held records and supplied current thresholds; Brian writes
all dissertation prose. No new model training, threshold tuning or data request.

## Question and meaning

How often, and how quickly, do observed high-water episodes progress through
current H1 (increased vigilance), H2 (imminent flood risk) and H3 (flooding)
discharge thresholds? Do the existing historical-analogue representations
retrieve precedents with similar subsequent threshold escalation?

H3 is a provider-defined current warning category, not independently observed
inundation. These thresholds were supplied in September 2026; historical
versions were not retained. Applying them to 2010–2025 is a standardized
retrospective reference, not a reconstruction of historical warnings. Native
15-minute discharge means locate recorded threshold entries to that interval
resolution, not the exact instant water overtopped a bank.

## Full population and timing

- Primary census: all held native 15-minute records at the six chapter gauges,
  with no p99, complete-512h-history or rainfall prerequisite.
- Supplementary census: every other supplied source series with an unambiguous
  station-threshold match. Keep the two Oud-Roosteren columns separate and
  mark their duplicate/indicative status; do not pool them as independent sites.
- Catalogue all threshold upcrossings, including entry after a missing value.
  Form H1-linked episodes by grouping recorded H1-or-higher observations
  separated by no more than the existing 72h recovery convention. Save the
  underlying individual crossings so conclusions are not hidden by grouping.
  Missing recovery intervals or record-end truncation are explicitly censored.
- Within each episode, report first H1/H2/H3 recorded entries, elapsed time,
  adjacent versus gap-censored entries, measured phase hours, peaks, gaps and
  source/rating concerns. Simultaneous first recorded categories are not
  proof of instantaneous physical escalation.
- Compare native-interval results with four-complete-quarter hourly means to
  quantify crossings hidden by averaging. Preserve all 724 existing Dutch
  p99 episodes separately; a p99 episode is not synonymous with an H1 episode.
- Include the supplied final midnight endpoint in native records because its
  preceding 15-minute mean covers the last interval of 2025 local time. Verify
  shared hourly values against the old table; any extra complete endpoint
  hour is listed explicitly rather than rewriting the old input.

## Measurement treatment

Main results describe reported discharge and retain concerns rather than erase
an event. Unknown outcomes cannot be labeled negative. A recorded positive can
remain positive despite missing later observations, while its first-entry time
may be uncertain. Negative classification requires complete observation of the
specified period. Episode closure additionally requires observed recovery.

Preserve literal rating-era/domain metadata, documented July 2021 problems,
Gulp's calibration only to approximately 3 m3/s, and Cottessen's conflicting
approximately-26 versus 27.5 m3/s capacity descriptions. Compute conservative
range-check sensitivities at both Cottessen capacities; do not pick the one
with better outcomes. Untrusted intervals become unknown in sensitivity labels,
not assumed zero. Earlier observed reliable crossings remain usable even if a
later peak is uncertain. Supplied report evidence remains distinct from labels
computed from discharge; no exact inundation onset is manufactured.

## Analogue analysis: census of all available inputs

Use the existing complete event histories and frozen representations. Score
all eligible queries, preserving unavailable archives. No sampled case bank.
No new weights, best-k search or retrained classifier.

At the existing p99 assessment cutoff, classify current H2/H3 status using the
native interval ending at cutoff. The main escalation population is below the
target threshold at cutoff. Apply that same known-at-cutoff condition to the
prior donor archive before retrieval, so an already-H3 donor cannot masquerade
as an H3-escalation precedent. This is phase-conditioned use of the existing
methods, not a new learned model. Prior-24h target exceedance is separately
recorded to distinguish possible recrossings.

- Q-only: raw history, matched raw/state, ordered frozen TTM/state.
- Matched rain/Q cohort: conventional signatures and matched raw/state and TTM.
- Prior-year context cohort: strengthened temporal/state, area, identity,
  fixed-2017 and annual AlphaEarth controls.

Current-threshold outcomes are unavailable for German donors; the threshold
comparison uses Dutch records, not invented German cutoffs. Retain the earlier
cross-border representation results as a separate analysis.

Keep completed earlier 72h responses, one donor per different onset-linked
regional group, all/other-river scenarios, main/existing measurement-concern
sensitivity and five/ten available donors. These conventions preserve the
chapter's actual methods. All population restrictions and coverage are reported.

Measure observed target reach in response hours (0,72], with native quarters
as primary and hourly means as aggregation sensitivity. Donor target-reach
fractions are empirical evidence summaries, not calibrated warning
probabilities. Compare their squared error with the equal-group-mass eligible
archive frequency and matched methods. Report positive and negative losses
separately, counts of events/groups, any-positive-precedent coverage, target
onset timing where both sides actually reach it, and unknown/range-check bounds.
First escalation excluding target exceedance in the previous 24h is a separate
reported subset, not a retrospective deletion of recrossing events.

Use existing 9,999 paired intact query-group resamples, seed 20261013, with
calendar-year sensitivity. Undefined discrimination or timing with no positive
cases is recorded as undefined. Intervals are conditional on held archives,
not measurement uncertainty, model-development choices or a future operator
population. Full-record descriptive counts are a census of this delivery,
not estimates of all floods that occurred in the region.

## Deliverables and verification

Runner `scripts/86_analyse_warning_threshold_progression.py`, separate local
outputs `results/warning_threshold_progression/`: normalized thresholds,
source coverage, all crossings/episodes, phase progression, station/year
summaries, all p99 event outcomes, analogue coverage/results and paired
intervals; complete main H2/H3 episode atlas, aggregate figures and an internal
results readout. Provider records remain local and no human labels are assigned.

Verify fixed UTC+1 conversion, quarter-hour interval endpoints, exact-threshold
inclusion, skip-level entries, missingness/censoring, record boundaries, rating
concerns, native/hourly differences, phase-conditioned donor eligibility and
completed-response chronology against hand-computed windows. Bind input/code
hashes, decisions, seed and outputs to a manifest; verify numeric summaries
and selected donor outcomes from source windows. This is internal reproducible
documentation, not formal preregistration or a new research gate.

## Assessment-clock correction during implementation

The complete native census exposed an Eyserbeek H3 entry outside its earlier
p99-onset 72h window. The primary progression question therefore uses **every
H1-linked episode**, with assessment at the first complete-hour boundary on or
after native H1 entry (0–45 minute delay recorded). Preserve all H1 episodes
and 512h-input availability, including censored/partial records. Extract only
new frozen ordered-TTM backbone vectors for these observed histories; no
training, new checkpoint or altered readout. Use existing era-p99 state scaling
and record unavailable normalizers, rather than silently filling them.

For each target, include known positive outcomes even if later readings are
missing; negatives require complete native follow-up. Report complete-follow-up
comparisons separately because non-random missingness can change the known-
label population. The observed peak of a partial response is explicitly a lower
bound and is not scored as exact discharge. Timing comparisons require an
uncensored first recorded crossing on both sides. Previous-24h reach remains
a reported first-escalation subset. Unknown labels stay visible in census and
coverage tables, never treated as negative.

The p99-anchor analysis is a separate bridge to the chapter's saved donor sets.
Reuse those sets only after checking unchanged phase eligibility, identities,
candidate counts, completed responses and quality flags; do not present them
as H1-started assessments. This correction follows inspection of descriptive
coverage, before the new primary H1 model results; it does not create formal
preregistration, untouched validation data or an experimental design.

## Historical-input missingness refinement

Descriptive coverage checking showed that the strict 512h rule discards four
of seven recorded H3 episodes for isolated old missing hours. The primary H1
representations therefore allow linear interpolation of an isolated incomplete
hour only when it is more than 24h before assessment, both original neighboring
hours are complete and below H1, and at least one native quarter is observed
in the incomplete hour with all observed quarters below H1. Never repair
adjacent missing hours, recent history, crossings or outcomes. This cannot rule
out an unseen brief peak: retain the full observed-history-only sensitivity
and log every substituted input. Apply the same history to all representations.

Short-gap interpolation has precedent, but these exact limits are a transparent
local sensitivity decision, not a literature-established flood guarantee.
See [hourly riverflow gap-filling study](https://link.springer.com/article/10.1007/s11269-023-03625-7)
and [streamflow gap-filling comparison](https://hess.copernicus.org/articles/22/4593/2018/).
Neither justifies inventing missing threshold outcomes.

Also report the conventional R0 method on its maximal available feature cohort:
its rainfall summaries and discharge at 0, -6 and -24h do not require 512h of
complete discharge. Matched model comparisons remain separate. Include a
same-gauge completed-archive frequency reference where prior cases exist;
compare errors on that reference's available queries only. These refinements
follow data-coverage inspection; report them candidly with the results.
