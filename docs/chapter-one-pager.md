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

The planned analysis and consolidation are complete. In the broad Q-history census (610 NL / 235 DE scored queries), TTM modestly improves individual response-shape matching over raw Q/state; stronger mean-trajectory or peak estimates are less consistent. Conventional matching also finds closer shapes than the generic eligible archive, so similarity retrieval alone is not an AI-specific contribution.

Added EO has conditional value. On 111 DE snapshot cases, AnySat + TTM/state reduces mean-trajectory RMSE by about 11% versus conventional matching, with exploratory storm/year intervals below zero; several peak/timing/late-response contrasts also improve. The curve advantage weakens with other-river donors and k=10. Some attractive Copernicus-FM/CROMA results on the shared all-ten intersection are not reproduced in their larger model-available populations. AlphaEarth has selective timing evidence, without a consistent general shape/trajectory advantage.

Actual cases show useful recession matches, missed later rises, unchanged donor selections and better normalized shape paired with worse severity/duration estimates. Cohort, donor archive and outcome matter; no universal model winner or operational warning skill is established. Full findings, sensitivities, population comparisons and figure links are in the [consolidated findings brief](limburg-findings-consolidated-2026-10-27.md). All original outputs remain preserved; 338 tests pass. Brian can now write from the completed evidence bundle.

## Maintenance

This is the canonical current one-pager. Retain Research Question(s), Motivation, Data, Method, Methodology and Findings. Update after meaningful changes to design, data availability, validated findings or next work; date the substantive review. Check live execution before describing a job as running or complete. Distinguish proposed, implemented and evidenced work. Preserve historical decisions elsewhere rather than presenting superseded directions as current. Brian writes dissertation/article prose.
