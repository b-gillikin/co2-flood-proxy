# Chapter 1 — Limburg: historical high-water analogues

Last substantively reviewed: 2026-10-27. Living supervisor/research brief; not dissertation manuscript prose.

## Research Question(s)

Can basin-aware AI find useful past high-water events across Limburg's Dutch and German tributaries, and identify when the evidence is too uncertain to use?

Supporting questions concern improvements in analogue selection, transfer between rivers/countries, and what analogues reveal about subsequent event behaviour.

## Motivation

Past events can help interpret developing high water, but superficially similar events differ in catchment context, storm history, river state and measurement quality. Test whether learned representations identify informative precedents and expose misleading matches. The potential application is source-linked situation assessment; operator benefit is not established here.

## Data

Held inputs for the declared comparisons: Dutch/German gauge records, catchment rainfall for the conventional comparison, river/catchment geography, provider quality information, AlphaEarth embeddings and EO imagery. Each arm uses its declared subset; Q-only comparisons do not require rainfall or every EO model. Held weather data and current warning thresholds support earlier explanatory/progression analyses; they are not prerequisites for the core EO analogue comparison. The full eligible event census retains explicit no-analogue cases. The supplemental archive's 66,913 files are locally staged and pixel/date audited; acquisition does not itself establish complete model support.

## Method

Compare conventional hydrological summaries, raw hydrographs, generic historical references, frozen IBM Tiny Time Mixers R2, AlphaEarth and ten frozen EO encoders: DOFA, CROMA, SatMAE, Copernicus-FM, TerraMind, Presto, AnySat, Galileo, Prithvi and OlmoEarth. Aggregate embeddings by observed catchment area; retrieve earlier events and evaluate subsequent response shape, severity and timing. Examine matched populations, cross-river and NL–DE contrasts, uncertainty and actual selections.

## Methodology

Retrospective comparative evaluation of representations and retrieval. Subsequent responses are withheld from matching and used for evaluation. Account for storm dependence, unequal archive support, missing coverage and measurement problems. This is not operational forecast verification. Supplemental analyses retain ten models but re-extract three across four configurations: SatMAE TOA/QA60, Copernicus-FM TOA/QA60 and two separate ascending-orbit CROMA routes. Each comparison replaces one arm and reuses nine; seven distinct models receive no supplemental extraction. Do not pool orbits or attribute TOA/QA-support differences solely to reflectance level.

## Findings

Earlier analyses found better matching of individual response shapes without consistent superiority for averaged response estimates. Conventional references remain competitive; AlphaEarth has not shown a strong general advantage. Corrected ten-model extraction, aggregation, merge, scoring and automated analogue review are complete. The review contains 656 unique scored queries and reports zero audited donor-rule violations; repeated configuration rows are not independent events. Scientific interpretation of the corrected comparison remains pending. All four supplemental configurations have completed extraction, aggregation, scoring and automated review, with the queue finishing on October 27. The CROMA support rule explicitly records patches with undefined sample-SD normalization as encoder-unsupported; raw observations and the full event inventory remain preserved. The original computational queue is complete. The authorized October 27 downstream follow-up is complete: corrected provenance pages, actual-feature rainfall eligibility, matched generic archive references and common-query/common-donor supplemental contrasts. The corrected rainfall review contains 646 unique scored queries, versus 603 in the original rainfall cohorts; the 836 feature-complete events are not all EO-score eligible. All 18 archive-reference batches and the final results memo are published. The latest re-audit passes 331 tests and verifies the final receipt; no encoder restart is indicated. The October 27 audit verified 149 unique recorded files with no hash mismatch and all 319 tests passed with the existing PROJ setting. It identified an avoidable 512-hour rainfall-history restriction, sharply unequal supplemental support and reporting/provenance fixes. Support-aware interpretation of the completed follow-up remains; completion alone does not establish model superiority. Operational warning skill is not claimed.

## Maintenance

This is the canonical current one-pager. Retain Research Question(s), Motivation, Data, Method, Methodology and Findings. Update after meaningful changes to design, data availability, validated findings or next work; date the substantive review. Check live execution before describing a job as running or complete. Distinguish proposed, implemented and evidenced work. Preserve historical decisions elsewhere rather than presenting superseded directions as current. Brian writes dissertation/article prose.
