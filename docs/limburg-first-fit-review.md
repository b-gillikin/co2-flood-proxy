# Limburg first-fit measurement review (2026-09-29)

Status: internal evidence record. The first 56 concern flags and the decision
to run a flagged-event sensitivity were recorded before viewing rainfall-onset
associations. After the first computational fit, the audit was amended to show
explicit rating-domain fields and flag two more events whose later peaks
exceeded a rating maximum. That addition was prompted by the measurement audit,
not the fitted associations, but the 58-event sensitivity is labelled
post-fit/exploratory. This is not dissertation prose or formal preregistration.

The six-gauge hourly discharge and documented rating eras generate 724 p99
episodes grouped into 240 regional storms. All 724 onsets are adjacent-hour
crossings with an admissible preceding hour; none is an unobserved entry. The
machine-readable per-event audit is `results/event_study/real_data_v1/events.csv`.
The script reads no rainfall or weather.

I inspected the five contact sheets containing all 58 measurement-concern
events and the two events with nearby gaps. The 33 abrupt-rise flags mostly
have a rapid rise followed by a receding hydrograph; the flag alone does not
establish instrument failure. Twenty-two Gulp events have an observed peak
above the provider's approximate 3 m³/s calibration limit. This limits peak
magnitude interpretation, but their first crossings are around the much lower
within-era p99 and are retained under the onset-only rule. Three episode peaks
exceed a documented rating-domain maximum (Eyserbeek on 10 July 2021, Gulp
and Geleenbeek on 13 July 2021); each onset pair is below that maximum. Five events begin
on 13 July 2021. Cottessen, Rimburg and Azijnfabriek carry the provider's
specific high-flow concerns; their recorded onset pairs are below the later
questionable peak range. The Cottessen and Rimburg peaks must not be reported
as validated discharge magnitudes. The two nearby-gap flags are not missing
at the crossing pair and remain exact onsets. No plotted window alone supplied
evidence for a new dated instrument-failure interval.

**Main decision before signal fitting:** retain all 724 exact onsets in the main
analysis, subject to complete rainfall histories. Exclude the 58 flagged
measurement-concern onsets in one labelled sensitivity analysis while keeping
the original at-risk-hour definition and matching strata. This is a stress
test, not an assertion that those 56 measurements are invalid. Continue to
report source limitations and the unusable high-flow peaks separately. If a
subsequent source document establishes a failure interval, amend the audit
with its date and evidence; do not infer failure from a model result.

The audit's input SHA-256 values are in `event_review_summary.json`. Source
notes are in `docs/waterschap-source-metadata.md` and
`data/processed/waterschap_station_source_qa.csv`. The use of relative p99
crossings, rather than absolute peak discharge, is the scientific reason the
known July 2021 peak issues do not automatically erase those onsets.
