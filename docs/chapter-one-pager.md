# Chapter 1 — Limburg: AI-assisted high-water assessment under monitoring loss

Last substantively reviewed: 2026-10-28. Living supervisor/research brief; not dissertation manuscript prose.

## Research Question(s)

**Can satellite AI help assess developing high water when ground-monitoring data are limited?**

Use the relatively information-rich held NL–DE river records as the reference, then vary observation age and reduce density, completeness, spatial coverage or historical support. Can EO reduce the resulting loss beyond the same scarce conventional inputs and capable simple fallbacks? The earlier question about late/stopped feeds remains the completed information-age component. See the [broader scarcity design](limburg-data-scarcity-design-2026-10-28.md); additional scarcity families are planned, not executed.

## Motivation

An analyst may have a known river but limited observations of its developing high water. Strong held observations allow controlled scarcity while retaining verification evidence. The chapter tests whether satellite context preserves useful assessment capability as conventional information is reduced. Its FEWS/DRR relevance is monitoring contingency and observation priorities. The reference is our held-data assessment system, not the full Dutch/German operational forecasting services. National resources are not an established explanation for negative EO increments, and existing methods have not demonstrated equivalence. Provider records document measurement problems and redundancy; actual live-feed delay/outage frequencies have not been measured.

## Data

Held Dutch/German discharge, hourly catchment rainfall, catchment geography, provider quality notes and ten frozen EO representations support the core analysis without new acquisition. The German-rainfall audit is adopted before scoring: **481 shared regional episodes, 3,848 gauge–storm cases and 100,048 unique issue/information-state opportunities**, including nonresponses, before input/outcome/donor checks. This regroups and extends the older 468 Dutch-triggered episodes; it is not simply 13 additional independent storms. The first observed-prefix 10mm clock uses all eight catchments. The earlier 126-storm six-hour subset remains supporting, not an eligibility cap. Weekly EO support is smaller than monthly support; unavailable cases remain in the coverage ledger. Targeted EO gap recovery is complete (442 validated exports); soil/snow for one supporting physical-state control is downloading sequentially. That later control compares against saved core results; it does not require re-extracting all encoders or repeating the whole core analysis. AlphaEarth, weather, warning thresholds and Sint Pieter/Venlo remain held supporting evidence, not new prerequisites.

## Method

Reassess at 0/6/12/24h after the rainfall landmark. Simulate fixed 1/3/6/12/24h discharge delivery delays and a feed that stops delivering new readings. Compare complete and restricted conventional analogues, a season-aware control, that control plus each EO representation, last-observation persistence and a generic historical distribution. Use same-gauge native-unit donor trajectories primarily; cross-river area-based transfer is supporting. Predict the next 24h distribution and verify CRPS, magnitude, timing and coverage. Four-week EO context is primary; completed-month snapshots assess broader coverage.

That paragraph describes the completed age/outage component. Planned extensions reduce observation density, intermittent completeness and network/context coverage on the same physical situations, with a shorter historical archive as a separate supporting scarcity dimension. Keep full eligible verification outcomes; removing a gauge from the observing inputs does not remove its events from evaluation. The current three-reading Q signature cannot represent every density change, and unused peer/Maas feeds cannot be meaningfully “removed”: implement responsive features and the declared contextual reference before interpreting those contrasts. Use separate scarcity axes before a compact set of combined situations; no automatic full-factorial expansion.

[Literature-based scenario levels](reviews/limburg-scarcity-scenario-precedents-2026-10-28.md) now give the next plan a concrete starting grid, including 0/25/50/75/100% missing inputs and frequency/network precedents from the Meuse basin. Hourly adaptations, placement and masking realism remain explicit; no new scenarios have been run.

Models: DOFA, CROMA, SatMAE, Copernicus-FM, TerraMind, Presto, AnySat, Galileo, Prithvi and OlmoEarth. IBM Tiny Time Mixers R2/raw-history comparisons will use permitted 512h histories ending at the last available reading; annual AlphaEarth is a supporting landscape/cross-river control. Earlier full-information results remain reference evidence; cached full-history vectors cannot be reused when they contain hidden observations.

## Methodology

Retrospective counterfactual observation-availability study, using the full eligible census and earlier completed donor storms. Keep hidden Q and future rainfall out of matching and event scheduling; avoid hidden Q/p99 trajectory anchors. Compare matched and broad archives, account for storm/year dependence and retain unsupported cases/fallback coverage. Equal instantaneous information under delay and failure is the same test case; the difference emerges over successive assessments. EO acquisition age and uncertain product-release times limit real-time claims. This direction was developed after inspecting the earlier results; no untouched-test or preregistration claim is made.

## Findings

**All 42 age/outage comparisons, independent audit, paired review and actual-case reports are complete.** In the primary same-gauge four-week readout, all ten EO additions have higher average error than conventional matching at 12/24h delays; magnitudes and uncertainty differ. Their disadvantage generally narrows with delay, which is not itself a demonstrated advantage. These results do not answer the unrun density, intermittent or spatial-scarcity contrasts. Two pre-publication development defects were corrected and affected scores restarted; invalid outputs remain labelled and excluded.

Completed full-information results remain: conventional rainfall/discharge is a strong reference, with no universal encoder winner. On 111 DE snapshot cases, the earlier AnySat curve improvement of about 11% against restricted conventional matching becomes about 2.1% against its broader archive; the total-difference intervals include zero. In the 364-case Meuse comparison, added mainstem context gives no clear conventional distributional gain and worsens TTM CRPS. These results motivate testing conditional information value, without guaranteeing a positive result. Earlier TTM/AlphaEarth, flood-case and cross-border findings remain in the completed evidence bundle.

Completed component: [held-data run and corrections](limburg-monitoring-first-analysis-2026-10-28.md), following the [earlier six-step plan](limburg-monitoring-implementation-plan-2026-10-28.md). Current organizing direction: [controlled data scarcity](limburg-data-scarcity-design-2026-10-28.md). Review separates archive loss from representation value and keeps unscored opportunities, simple fallbacks and unsupported EO visible. No new provider delivery is essential. [Requests to René/Jens](limburg-monitoring-provider-request-drafts-2026-10-28.md) are drafts for Brian to send, not dispatched messages.

## Maintenance

This is the canonical current one-pager. Retain Research Question(s), Motivation, Data, Method, Methodology and Findings; date substantive changes and distinguish specified, implemented and evidenced work. Preserve dated historical decisions and results. Brian writes dissertation/article prose.
