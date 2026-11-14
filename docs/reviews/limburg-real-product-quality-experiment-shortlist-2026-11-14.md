# Which completed experiments fit real input-quality comparisons?

14 November 2026. Internal recommendation in response to Brian's three-stage concept: existing NL/DE reference-information work → same catchments with actual alternative observation products → other rivers if a specific insight merits replication. No study, product, model shortlist or evaluation protocol is adopted by this note. No analysis or download launched.

## Recommended backbone

Reuse the **model-specific next-24-hour discharge-correction comparison**, rather than the original forced EO/ground distance fusion. Its useful structure is:

- C: the existing strong conventional analogue trajectory.
- C+R: a small learned correction using the permitted ground inputs and matched raw EO descriptors.
- C+R+E: the same correction with the corresponding encoder representation added, allowing zero EO influence.

The target is the next 24 hourly discharge values, evaluated against the same best-supported held observations across input conditions. This is a retrospective assessment experiment; finalized historical inputs or retrospectively processed satellite products are not automatically as-issued operational feeds.

Two contrasts should remain separate: total value of the candidate pipeline against C, and the encoder-specific increment against C+R. If the learned correction alone accounts for a gain, that is a substantive result, but it is not an encoder contribution. A smaller loss under an alternative input product is not proof of recovery to reference-input performance. Comparisons must be within matched opportunities and their own supported model/input contracts, not an encoder league table.

This backbone already has chronology, source-aware controls, high-water diagnostics and full-census accounting. It can test actual rainfall-product errors or, if archived raw gauge pairs are obtainable, gauge-input errors. It does not require another extraction campaign by default. Cached representation identity, dates and access would still need verification before reuse.

## Shortlist by experiment

| Earlier work | Recommended role | Reason |
| --- | --- | --- |
| Model-specific next-24h residual correction, completed 2 November | Primary backbone | Changes actual inputs while retaining an interpretable outcome, strong baseline and raw-versus-encoded attribution |
| Conventional hydrological analogue retrieval | Required reference; selected analogue inspection as explanation | Shows how product changes affect available/matched precedents; useful even if no AI increment appears |
| TTM versus raw hydrograph representation | Conditional secondary candidate, strongest fit to genuine gauge-history quality changes | Same Q history represented differently; plausible temporal-pattern question. Rainfall-only changes do not directly change the TTM input. Earlier favorable shape results do not establish forecast benefit. |
| Analogue distribution/CRPS comparison | Alternative primary if the substantive task is a distributional assessment; not an automatic extra endpoint for ridge correction | Existing point corrections do not supply predictive distributions. Do not call seed spread predictive uncertainty or compare MAE and CRPS as identical quantities. |
| Original fixed 50/50 EO-fusion scarcity matrix | Preserve as earlier evidence, not preferred rerun | Forced influence and altered donor pools confound an inference that the encoder contains no useful information |
| H1/H2/H3 escalation analysis | Supporting event relevance only for this proposal | Few severe events and historical threshold limitations do not support making it the broad primary target by default |
| Water/flood-map segmentation and reference-image replacement | Separate completed research | Gauge/rainfall products are not inputs to those image mappers; swapping weather does not test their mapping quality |
| Building CO2 / pressure precursor work | No default inclusion | A separate mechanism/question, not a necessary test of the current product-quality proposal |

## Which model-specific corrections are most plausible?

**AnySat** is a reasonable shortlisting candidate for testing whether the held recent spatial/temporal optical context adds information under imperfect rainfall observations. The existing individual experiment uses four completed weeks and matched raw spatial descriptors. The hypothesis concerns antecedent/landscape state; it is not that imagery reconstructs the storm's true hourly rain. Its prior German snapshot improvement is exploratory supporting evidence, not the selection criterion or a guarantee of repetition.

**Presto** is a complementary candidate for the held seasonal/antecedent-state route. Its individual experiment uses twelve completed monthly observations with pixel-level moments and matched raw seasonal descriptors. It should not be described as an hourly storm sensor. Its small prior conditional gains justify retaining the evidence, but do not establish compensation for rainfall errors.

**TTM** is most directly connected to genuinely noisier gauge histories. It would need the same permitted histories as the raw temporal control; a transformed high-quality Q history cannot be presented as a rescue of lower-quality inputs. Its earlier frozen representation/analogue experiment is a different pipeline from the EO correction experiment and should not be silently folded into it.

DOFA's earlier watercourse-holdout design belongs to a distinct transfer question and is not directly comparable to same-gauge fits. AlphaEarth is stable catchment/year context; within-catchment product replacement does not make it a direct measurement of missing storm dynamics. Neither is a default addition to Stage 2. Other encoders are not ruled out permanently; there is currently no task-based reason to rerun all ten or choose whichever had the most favorable historical cell.

Published model records: https://openaccess.thecvf.com/content/CVPR2025/html/Astruc_AnySat_One_Earth_Observation_Model_for_Many_Resolutions_Scales_and_CVPR_2025_paper.html ; https://arxiv.org/abs/2304.14065 . These establish model capabilities, not the proposed hydrological benefit. Exact held inputs/readouts are defined in `config/limburg_individual_encoder_experiments_v1.json` and the completed run receipts, not inferred from the general papers.

## What Stage 1 actually supplies

Stage 1 supplies completed reference-information results and reusable infrastructure. The earlier primary comparison removed local Q; the proposed initial rainfall-quality comparison may retain Q. Use the existing rich-information branch where compatible, not the headline local-Q-absent result as though it were the same condition.

A matched reference-information rerun may be necessary after product overlap, issue times and pipeline are fixed. Eligibility, dates, causal histories, baseline updates and scoring support must match Stage 2. Rebuilding these joins/fits is different from re-extracting satellite imagery. The earlier studies remain exploratory evidence, not an untouched new validation set.

The primary deployment interpretation also needs one choice: a system developed using the alternative product, or a reference-trained system suddenly receiving an alternative feed. These are different questions. For persistent use of a global product, product-consistent training and testing is the more natural primary comparison; swapping products only at test time primarily measures distribution shift. A frozen-feed-swap sensitivity is not an automatic second full matrix.

All derivatives of a downgraded source must change consistently in both the baseline and learning arms: rainfall accumulation, antecedent summaries, spatial summaries and any data-dependent archive/query features. Keep higher-quality data for permitted verification/reference roles, not hidden predictors. A RADOLAN-derived event clock can define a retrospective common storm population, but cannot demonstrate that an alternative-data system would itself detect those starts in real time.

No newly favorable score is required to report Stage 2 honestly. Stage 3 should replicate a specific finding about errors, recovery, limitations or conditions, with the question and method fixed before examining external outcomes. It should not become another watercourse/model search.

## Evidence consulted

- `docs/limburg-completed-discharge-readout-2026-11-02.md`.
- `config/limburg_individual_encoder_experiments_v1.json` (historical planning statuses are stale; completed readout/receipts establish execution).
- `docs/limburg-eo-signal-findings-2026-10-29.md` and its diagnostic specification.
- `docs/limburg-scarcity-results-2026-10-29.md`.
- `docs/limburg-analogue-distribution-results-2026-10-15.md`.
- `docs/limburg-findings-consolidated-2026-10-27.md`.

This is a shortlist and justification, not the research-argument, executable specification or readiness report. No alternate product has been declared intrinsically lower quality, and the proposed benefit remains an untested hypothesis.
