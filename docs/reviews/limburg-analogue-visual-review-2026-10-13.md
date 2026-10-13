# Selected analogue cases: visual and provenance review

Internal AI-assisted research aid, 2026-10-13. All fourteen generated cards
were inspected alongside the selected-pair metadata. This is not independent
human validation and does not draft dissertation prose. Human verdicts remain
blank in `results/basin_ai_step6/human_review_cases.csv`.

The case IDs below identify PNGs under `results/basin_ai_step6/review_plots/`.
The case table records complete query IDs, UTC cutoffs and selection reasons;
`review_case_pairs.csv` records each donor and its source flags. Selection is
outcome-informed: largest gain/loss, a median contrast and a flagged query per
cohort, plus two German illustrations. Repeated query events across cohorts
are not independent examples. These cards cannot estimate a relevance rate.

The score is the mean of five individual donor peak/p99 ratios, compared with
the query's peak/p99 in hours 1–72. It is not the maximum of the plotted mean
hydrograph. Hour 0 is displayed but excluded from the response score; a peak
ratio below one can therefore be correct for a query already receding.
Response panels share a vertical scale. Values below are rounded.

| Case | Query | Observed response peak/p99; reference → challenger estimate | AI-assisted reading and qualification |
| --- | --- | --- | --- |
| dutch_01 | Eyserbeek, 2018-04-29 | 4.94; raw 1.90 → TTM 3.63 | TTM is closer to the large early response, but selected donor responses are widely dispersed. The query has an `abrupt_rise_review` flag and some donors have concerns; the large gain is not an unqualified exact-peak validation. |
| dutch_02 | Eyserbeek, 2020-03-06 | 1.24; raw 1.49 → TTM 4.75 | TTM selects several large or multi-pulse donor responses while the query recedes. All five TTM donors are unflagged under the existing rules. This failure cannot be explained simply by retained measurement flags. |
| dutch_03 | Worm, 2013-01-30 | 1.59; raw 1.62 → TTM 1.61 | Both mean peak estimates are close, but individual donor timing and magnitudes vary. A close aggregate score does not establish that every donor is a close hydrograph analogue. |
| dutch_04 | Gulp, 2010-11-13 | 4.20; raw 1.06 → TTM 1.17 | Both methods miss the broad large response. The query exceeds the documented Gulp calibration range, weakening the exact peak comparison while preserving the reviewed onset. |
| context_01 | Gulp, 2025-06-08 | 1.33; TTM 3.55 → AlphaEarth+TTM 1.75 | Context shifts from no Gulp donors to four Gulp donors and removes several overly large responses. Both sets still contain flagged donors. This illustrates a useful local preference in one case, not proof that context resolves measurement uncertainty. |
| context_02 | Eyserbeek, 2023-04-01 | 1.62; TTM 1.66 → AlphaEarth+TTM 3.39 | Context selects five Eyserbeek events; a very large 2019 donor response raises the estimate. All are unflagged. Area and AlphaEarth select the same five donors in different orders, hence the same unweighted estimate. Locality does not ensure response suitability. |
| context_03 | Eyserbeek, 2019-10-02 | 1.14; TTM 1.97 → AlphaEarth+TTM 1.94 | Both sets include later donor pulses absent from the rapidly receding query. The small numerical context gain is not a clear improvement in full-response similarity. |
| context_04 | Gulp, 2020-03-10 | 3.21; TTM 2.22 → AlphaEarth+TTM 1.53 | The query has a later secondary peak absent from the donor means. Context worsens the peak estimate; the query's documented calibration-range concern limits interpretation of its exact size. |
| pooled_01 | Eyserbeek, 2018-04-29 | 4.94; raw 1.90 → TTM 3.63 | Same query and scored result as dutch_01. The pooled archive does not provide an independent replication of this apparent gain. |
| pooled_02 | Eyserbeek, 2020-03-06 | 1.24; raw 1.47 → TTM 3.76 | TTM still overestimates through large donor responses after adding the German archive. Pooling changes the estimate but does not eliminate the failure seen in dutch_02. |
| pooled_03 | Eyserbeek, 2014-09-18 | 2.95; raw 2.25 → TTM 2.26 | Both underestimate the early peak and poorly represent a later query pulse. Their almost identical peak errors conceal differences between full response shapes. |
| pooled_04 | Eyserbeek, 2010-07-11 | 1.11; raw 1.12 → TTM 1.36 | The query is already receding after hour 0. Raw donors give a closer aggregate peak, while TTM remains higher. The abrupt-rise flag remains a concern, not proof of measurement error. |
| pooled_05 | Herzogenrath 1, 2019-07-27 | 2.00; raw 2.11 → TTM 1.91 | Both estimates are close. TTM's set contains two same-gauge German and three Dutch donors, with no retained donor flags; individual trajectories still vary. A cross-country donor is not intrinsically inapplicable. This is a pre-provisional, eligible German response. |
| pooled_06 | Herzogenrath 1, 2017-06-15 | 0.72; raw 1.83 → TTM 3.83 | All five TTM donors are Dutch and unflagged; two large Geleenbeek responses drive the high estimate while the query recedes immediately. This does not establish that nationality caused the mismatch. A sub-p99 withheld peak is valid because onset hour 0 is outside the score. |

## Interpretation limits and human review

The clearest recurring distinction is between a similar assessment history,
a similar average peak, and a similar subsequent hydrograph. They are not
interchangeable. Future forcing can differ even when the preceding history
looks similar; these plots do not establish the meteorological cause of any
individual mismatch. No new timing score, storm classification, distance
weight or event exclusion was added from this inspection.

The context cases demonstrate both directions of a same-catchment preference.
They do not isolate what the satellite representation learned. Existing
measurement flags remain explicit; visually unusual behavior alone has not
been relabeled as an error. River aliases, rating periods and provisional
status should accompany any example presented across jurisdictions.

Brian can record his own assessment in the blank human fields of the case
CSV, using the linked plots and pair records. Those judgments may refine the
interpretation; an illustrative, outcome-selected review still does not become
a blinded relevance-accuracy study. It need not introduce another experiment.
