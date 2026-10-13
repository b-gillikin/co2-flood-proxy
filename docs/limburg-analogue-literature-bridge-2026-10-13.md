# Literature bridge for the active Limburg analogue chapter

**Date:** 2026-10-13. Internal research aid, not dissertation prose. This note
updates the relevance of the earlier foundation-model and event-literature
reviews after the four-arm RAG experiment was removed. It adds no model arm or
data requirement.

## What the literature supports

| Chapter idea | Direct foundation | What it does not establish |
| --- | --- | --- |
| High-water events have distinct combinations of storm forcing, antecedent state and catchment response. | Merz and Blöschl (2003); Tarasova et al. (2020); Tsiokanos et al. (2024). | That one Limburg similarity measure will identify the most useful prior event. |
| Historical flood hydrographs can be compared as whole shapes and against conventional signatures. | Wendi, Merz and Marwan (2019) compare historical Elbe flood hydrographs using cross-recurrence plots and conventional descriptors. | Their method and finding are not validation of raw nearest-neighbour or TTM retrieval in Limburg. Cross-recurrence plots are context, not a newly required arm. |
| Time-series foundation models warrant a controlled streamflow test, with particular care at peaks. | Sun and Sun (2026) evaluate zero-shot streamflow forecasting and find task-dependent performance and difficult peak behavior. | Forecast performance elsewhere does not imply useful event embeddings here. |
| Satellite embeddings can be catchment descriptors, distinct from hourly storm state. | Brown et al. (2025) describe AlphaEarth; Liu et al. (2026) evaluate geospatial embeddings as hydrological catchment attributes. | Annual embeddings do not observe an event's hourly wetness or prove an increment for this small Limburg sample. |
| NL and DE flood-warning evidence sits in different institutional and measurement contexts. | Busker et al. (2026) compare northwestern-European forecasting and warning systems; held WL and LANUK provider records document the specific station and quality semantics used here. | Institutional difference alone does not show that a cross-border analogue is invalid or that this study improves official warnings. |

The [Wendi et al. article](https://doi.org/10.1029/2018WR024111) is the most
direct missing methodological anchor in the previous targeted review. The
[Busker et al. article](https://doi.org/10.5194/nhess-26-1457-2026) supplies
the regional FEWS context. The prior literature map already records the
remaining sources and their limitations.

## What remains this chapter's empirical question

Whether conventional summaries, raw 512-hour discharge histories, frozen
TTM-R2 embeddings or prior-year AlphaEarth context retrieve *more useful*
earlier events is not settled by these papers. The 512-hour input and 72-hour
withheld-response windows are this study's fixed evaluation design, not a
universal hydrological rule established by the literature. Report their effect
on which events are eligible and what outcome can be scored.

Likewise, the literature motivates attention to cross-border heterogeneity;
only the held gauge and source audits can establish which particular analogue
pairs are comparable. Keep any policy recommendation tied to documented
identity or measurement failures in the evaluated pairs. This retrospective
test does not establish as-issued forecast skill or operator benefit.
