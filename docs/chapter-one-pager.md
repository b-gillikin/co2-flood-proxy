# Chapter 1 — Limburg: AI-assisted high-water assessment under monitoring loss

Last substantively reviewed: 2026-10-28. Living supervisor/research brief; not dissertation manuscript prose.

## Research Question(s)

**Can satellite AI help assess developing high water when a gauge's data are late or stop arriving?**

How does accuracy change with the age of the latest discharge reading? Do frozen EO representations reduce that loss beyond available rainfall/discharge and simple fallbacks? Does any benefit survive controls for season, EO age and archive coverage, and differ between Dutch and German gauges?

## Motivation

An analyst may have a known river and historical record but lack its latest readings. The chapter tests whether satellite context can preserve useful evidence about what happens next. Its FEWS/DRR relevance is monitoring redundancy and contingency assessment. Operational adoption, warning skill and damage reduction are not established. Provider records document measurement problems and sensor redundancy; actual live-feed delay/outage frequencies have not been measured.

## Data

Held Dutch/German discharge, hourly catchment rainfall, catchment geography, provider quality notes and ten frozen EO representations support preparation without new acquisition. The rainfall catalogue has 468 storms and 3,744 opportunities across eight gauges, including nonresponses. The planned primary clock uses each episode's first observed accumulation of 10mm: all 468 held storms have such a timestamp. The earlier 126-storm six-hour subset remains supporting, not an eligibility cap. These counts precede new issue/input/donor checks. Weekly EO support is smaller than monthly support; unavailable cases remain in the coverage ledger. Recommended additions are targeted EO gap recovery and soil/snow context for one supporting physical-state control. AlphaEarth, weather, warning thresholds and Sint Pieter/Venlo context remain held supporting evidence, not new prerequisites.

## Method

Reassess at 0/6/12/24h after the rainfall landmark. Simulate fixed 1/3/6/12/24h discharge delivery delays and a feed that stops delivering new readings. Compare complete and restricted conventional analogues, a season-aware control, that control plus each EO representation, last-observation persistence and a generic historical distribution. Use same-gauge native-unit donor trajectories primarily; cross-river area-based transfer is supporting. Predict the next 24h distribution and verify CRPS, magnitude, timing and coverage. Four-week EO context is primary; completed-month snapshots assess broader coverage.

Models: DOFA, CROMA, SatMAE, Copernicus-FM, TerraMind, Presto, AnySat, Galileo, Prithvi and OlmoEarth. IBM Tiny Time Mixers R2/raw-history comparisons will use permitted 512h histories ending at the last available reading; annual AlphaEarth is a supporting landscape/cross-river control. Earlier full-information results remain reference evidence; cached full-history vectors cannot be reused when they contain hidden observations.

## Methodology

Retrospective counterfactual observation-availability study, using the full eligible census and earlier completed donor storms. Keep hidden Q and future rainfall out of matching and event scheduling; avoid hidden Q/p99 trajectory anchors. Compare matched and broad archives, account for storm/year dependence and retain unsupported cases/fallback coverage. Equal instantaneous information under delay and failure is the same test case; the difference emerges over successive assessments. EO acquisition age and uncertain product-release times limit real-time claims. This direction was developed after inspecting the earlier results; no untouched-test or preregistration claim is made.

## Findings

**Monitoring-loss simulations are specified, not yet run.** No EO compensation finding exists.

Completed full-information results remain: conventional rainfall/discharge is a strong reference, with no universal encoder winner. On 111 DE snapshot cases, the earlier AnySat curve improvement of about 11% against restricted conventional matching becomes about 2.1% against its broader archive; the total-difference intervals include zero. In the 364-case Meuse comparison, added mainstem context gives no clear conventional distributional gain and worsens TTM CRPS. These results motivate testing conditional information value, without guaranteeing a positive result. Earlier TTM/AlphaEarth, flood-case and cross-border findings remain in the completed evidence bundle.

Current execution preparation: [six-step implementation plan](limburg-monitoring-implementation-plan-2026-10-28.md). Rebuild the causal calendar/availability ledger, inventory and acquire useful gaps, construct inputs, verify the runner, score the eligible census and review actual situations. Reuse valid embeddings; extract only genuinely missing/changed contexts. No new provider delivery is essential.

## Maintenance

This is the canonical current one-pager. Retain Research Question(s), Motivation, Data, Method, Methodology and Findings; date substantive changes and distinguish specified, implemented and evidenced work. Preserve dated historical decisions and results. Brian writes dissertation/article prose.
