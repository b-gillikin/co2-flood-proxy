# Meuse inclusion: tributary analogue context

Implemented 2026-10-27 at Brian's request. Internal research aid, not manuscript prose.

## Role in the chapter

The Meuse is now included through Sint Pieter and Venlo as mainstem context for tributary events and their saved analogues. The RQ remains whether basin-aware AI finds useful historical high-water analogues across Dutch/German tributaries. This addition asks whether apparent tributary similarity conceals different mainstem conditions, and makes those differences inspectable.

This is executed contextual analysis, not a Meuse prediction experiment or a claim of improved retrieval. Mainstem events have not been mixed into the tributary donor pool. There is no new EO extraction, model fitting, reranking or change to the completed model scores. The archived Venlo increment pilot addressed a different target and retains its negative result.

## Implemented data and methods

- Runner: `scripts/145_add_meuse_context.py`; helpers: `src/meuse_context.py`.
- Output: [context browser](../results/meuse_context_2026_10_27/index.html), event/context Parquets, case-context CSV, annual coverage, source-block audit, four timelines and a hash manifest.
- Inputs: held annual RWS JSON for Sint Pieter and Venlo, 2000–2025; 1,062 tributary inventory events, 2010–2025; all 15 flood-register rows; 641 unique saved query–donor pairs across the three continuously scored flood-review queries. These are unique pairs across saved configurations, not independent tests or additional floods.
- Methods, processing, units, status and quality code stay visible. Select high-frequency F103 unprocessed discharge in m³/s with controlled status. Source-block cadence must support the nominal ten-minute series. Daily records can share F103/NVT metadata, so method names alone are insufficient. Cadence, metadata and quality counts for every block are retained. Conflicting values at a shared timestamp raise rather than silently average incompatible records; identical annual-boundary duplicates are removed.
- Two views: ordinary controlled code `00`, and a clearly labelled broader controlled view using codes `00,10,20,25,30,40`, including interpolation code `25`. The latter is context with provenance, not an independently observed discharge benchmark. A code-00 discharge record is not necessarily a direct instrument measurement either.
- F103 values describe five minutes before and after the source timestamp. Hourly bins use `ceil(timestamp + 5 minutes)` and at least four distinct readings. This guarantees contributing temporal support ends by the hourly context label. No interpolation, forward filling or substitution of stale state is performed. This is more conservative than assigning a centred reading directly to its nominal timestamp; the old pilot's numerical outputs remain unchanged.
- At each event cutoff: discharge, six- and 24-hour changes, past-window coverage, interpolation counts, and empirical rank in that site's ordinary controlled hourly values from **earlier calendar years only**. Reference observation/year counts are retained. Same-year/future observations do not define ranks. These descriptive ranks are not official warning levels or bankfull estimates; evolving reference coverage, regulation, seasonality and unequal source quality limit cross-year interpretation.
- Saved donor pairs receive each site's query/donor ranks and their absolute difference. Missing context stays missing; an event or donor is not removed from the original experiment. Whole-register timelines preserve documentary-date uncertainty. They do not convert year-only German evidence into an exact flood onset.

## Coverage

| Context at event cutoff | Sint Pieter | Venlo |
| --- | ---: | ---: |
| Total held tributary events | 1,062 | 1,062 |
| Ordinary controlled discharge and prior-year rank available | 931 | 613 |
| Broader controlled discharge available | 1,011 | 625 |

This is the full inventory, including events ineligible for particular earlier scoring arms. It does not replace their declared sample counts. Venlo's early-period high-frequency ordinary-code coverage is limited. No context value is invented for those events.

## What the first paired review adds

| Tributary query, UTC | Sint Pieter state | Venlo state | Interpretation |
| --- | --- | --- | --- |
| Worm, 2014-07-08 12:00 | 168.05 m³/s; prior-year rank 0.505; +115.42 m³/s over 24h | No eligible high-frequency value | A tributary extreme need not start during an already exceptional mainstem discharge; downstream context remains unknown here. |
| Eyserbeek, 2021-07-10 19:00 | 160.79; rank 0.505; +61.80 over 24h | 151.71; rank 0.436; +1.01 over 24h | The original early p99 anchor precedes the much larger basin wave. It is not the same assessment time as H1/H3 escalation several days later. |
| Voer, 2024-05-17 07:00 | 340.52; rank 0.777; +30.46 over 24h | 373.21; rank 0.746; +85.33 over 24h | Both mainstem gauges are rising at the pre-flood query. Neither rank alone establishes inundation. |
| Voer, 2024-05-20 18:00 | 372.93; rank 0.802; +226.03 over 24h | 612.23; rank 0.878; **−86.85** over 24h | This is a Voer recovery query with contrasting mainstem trends. A single basin-wide rising/falling label would lose information. |

For the 252 saved Voer May 17 query–donor pairs with Sint Pieter ranks available, median absolute rank difference is 0.150, ranging 0.003–0.721. At Venlo, 229 pairs have ranks: median difference 0.167, range 0.001–0.743. Existing representations select analogues across appreciably different mainstem contexts. These post-hoc descriptive differences are not evidence that a rank gap caused a response error or that filtering by rank improves skill.

During the 101 hourly labels in Eyserbeek's July 2021 register window, Sint Pieter has 94 ordinary controlled values; Venlo has none, while its broader view has 101 and 606 interpolated readings. The visible Venlo wave therefore cannot serve as an independently measured exact-discharge validation target for that case. The plot keeps it visible with its provenance. Incomplete-window maxima are explicitly labelled observed maxima rather than certified event peaks.

## Hydrological and policy interpretation

Sint Pieter and Venlo provide regional context at different mainstem locations. They are not universal upstream/downstream boundary gauges for every tributary: Voer enters above Sint Pieter, and connected tributaries have intervening reaches/inflows. Source simultaneity, peak order or discharge difference alone does not establish tributary contribution, travel time or backwater. A confluence mechanism requires suitable local stage/geometry evidence; that is not a prerequisite for this descriptive context inclusion.

The motivation is grounded in two relevant studies:

- [Strijker et al. (2023), The 2021 floods in the Netherlands from a river engineering perspective](https://doi.org/10.59490/jcrfr.2023.0006): downstream peak attenuation and floodplain storage altered the Meuse wave. This supports distinguishing mainstem context and location rather than assuming one basin-wide response pattern.
- [Geertsema et al. (2018), Anatomy of simultaneous flood peaks at a lowland confluence](https://doi.org/10.5194/hess-22-5599-2018): at a different, lowland Meuse confluence, overlapping high-water duration and backwater matter. It motivates examining whole waves; its mechanism or magnitudes cannot simply be assigned to the held Limburg sites.

Operationally relevant direction: an analyst could inspect both a local historical analogue and the contemporaneous wider-basin situation, including unsupported records. This work has not tested operator decisions or demonstrated an operational benefit.

## Next analysis, if pursued

The direct extension is a matched comparison of the existing baseline against the same retrieval plus a compact Meuse context representation, using only cutoff-available inputs, identical donor eligibility and storm/year uncertainty. Preserve the full census and explicitly report reduced matched coverage rather than presenting complete-context cases as the whole population. Keep site-specific state/trend distinct; do not call a source-quality gap a hydrological negative. The observational review is already included and does not depend on that comparison succeeding.

A separate mainstem analogue population or a confluence-specific interaction study would answer additional questions. Neither is silently added to the required work by this inclusion.

## Validation and reproduction

Run `MPLCONFIGDIR=/private/tmp/limburg-mpl .venv-foundation/bin/python scripts/145_add_meuse_context.py`. Source/input/output hashes are in the generated manifest. Tests cover centred-time support, missingness, interpolation, duplicate/conflicting records, prior-year-only normalization and daily-method/cadence exclusion. The full chapter suite requires its existing local PROJ_DATA setting; see the retained test log and compact verification receipt under `docs/reviews/meuse-context-2026-10-27/`.

All pre-existing results and data are preserved. No other chapter's files or data were modified. Brian retains all dissertation writing.
