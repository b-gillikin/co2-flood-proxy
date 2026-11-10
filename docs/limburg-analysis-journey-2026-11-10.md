# Limburg: what we tried, in plain language

10 November 2026. Internal orientation aid for Brian, not dissertation prose. These are stages of one exploratory project, often using overlapping records. They are not independent studies that can be counted as repeated confirmations.

## 1. Can indoor CO2 provide a useful flood-related signal?

The original motivation involved the Kerkrade building/sensor records and earlier work by Viefhues and Eryilmaz. We checked data lineage, gaps, pressure adjustment and whether unusual CO2 preceded Wurm high water. The usable original window covered only a handful of onsets in one building and season, with a missing event and substantial non-river influences. A later-record CO2 classification check did not recreate the original flood-period experiment. We did not establish a dependable or transferable flood precursor. This direction is retired.

Evidence: archived `wurm-co2-small-diagnostic-2026-10-03.md`, `iot-sources.md`, `results/eryilmaz/summary.md` and `archive/README.md`.

## 2. How does rainfall before high water differ across seasons?

We reviewed gauge problems and compared rainfall before high-water onset with rainfall during comparable ordinary hours. Warm and cold timing estimates overlapped: the first fit's median lags were approximately 17 and 19 hours, with an uncertain difference. A cumulative rainfall contrast also proved unrealistic as a literal storm effect, so that magnitude could not be presented as a credible flood risk ratio. This was a real retrospective timing analysis, but did not yield a distinctive forecast or warning result.

Evidence: archived `limburg-first-fit-results-guide.md` and associated fit/support review.

## 3. Why do tributaries respond differently to the same storm?

We compared storms affecting several rivers, including antecedent flow, rainfall amount/location, peer-river behavior and repeated rain before recovery. Later analyses included the two German Wurm gauges and mainstem Maas context where compatible. Rainfall and river state help describe differing responses, but the peer/repeat-pulse analyses did not establish a strong, stable new general mechanism. The mainstem addition supplied context, not a consistent predictive improvement.

Evidence: archived cross-tributary analyses; `limburg-storm-response-results-2026-10-15.md`; `limburg-assessment-synthesis-2026-10-27.md`. Populations and event definitions changed between stages; counts must remain attached to their own analyses.

## 4. Could an AI assistant assemble better cross-border flood assessments?

We prepared an evidence inventory, river/agency facts, checked numerical tools, a question bank and a four-arm RAG design. This tested feasibility and evidence plumbing. It was not a completed comparison of language models answering all the questions. Brian chose to move toward hydrology/geospatial representations; this route was archived, not empirically disproved.

Evidence: `archive/retired-basin-ai-pilot/docs/limburg-basin-ai-pilot-2026-10-11.md`.

## 5. Can similar historical events tell us what happens next?

We built an event library and retrieved earlier analogues using rainfall/discharge, raw hydrograph shape and Tiny Time Mixers (TTM), including cross-river and Dutch/German comparisons. Conventional matching found useful precedents. Strengthened TTM representations made the selected individual response shapes somewhat closer, but often did not improve the average future trajectory or its uncertainty range over strong conventional/generic references. A better-looking precedent and a better prediction are different outcomes. Severe cases exposed missing precedents, missed extreme donors and peaks diluted by averaging.

Evidence: `limburg-analogue-information-review-2026-10-14.md`, `limburg-analogue-distribution-results-2026-10-15.md` and October 27 synthesis.

## 6. Can AlphaEarth landscape context improve those analogue choices?

It materially changed which rivers/events were selected, often favoring the same catchment. We compared it with simple area and gauge-identity information, fixed versus annual imagery, and stronger temporal representations. It was not merely ignored or dropped: its extra predictive value was conditional and inconsistent. Landscape similarity did not reliably identify the best precedent for a particular storm.

Evidence: `limburg-alphaearth-detailed-review-2026-10-14.md` and later cross-border/distributional analyses.

## 7. Can analogues identify progression toward flooding?

We linked high-water events to current Dutch H1/H2/H3 thresholds and tested escalation from H1. Current thresholds applied backward are not a historical warning archive or independently observed inundation. The six-gauge census had only seven recorded H3 reaches across four regional episodes, with measurement gaps/range concerns. Analogue predictions did not clearly outperform simple references for escalation. This work clarified what can be measured and why rare severe cases defeat apparently reasonable averages, but did not produce a reliable flood-escalation system.

Evidence: `limburg-warning-threshold-results-2026-10-14.md`. Changing percentile/event separation did not uncover a broad breakthrough.

## 8. Would ten other EO representations capture useful storm/catchment information?

We extracted corrected, model-specific satellite representations and compared monthly snapshots, temporal sequences and conventional inputs. Some initially promising differences weakened when we allowed the conventional method its full historical archive: imagery requirements had removed useful potential donors. Real satellite representations did contain some information relative to time-shuffled imagery and particular learned controls. That did not consistently improve the strongest existing assessment method.

Evidence: `limburg-assessment-synthesis-2026-10-27.md` and `limburg-eo-signal-findings-2026-10-29.md`.

## 9. Could satellite AI compensate for late, missing or sparse ground data?

We deliberately delayed/stopped feeds, removed gauges, thinned observations, introduced gaps and limited available history. The fixed EO-plus-analogue recipe did not show an average advantage over conventional matching. We then treated the encoders individually, using model-appropriate spatial/temporal inputs, matched raw controls and learned corrections. Some individual conditions improved, but the completed ten-experiment discharge review still found no broad benefit, including for high-water assessment. The scarcity simulation retains historical response labels: it is not an evaluation in wholly unmonitored basins.

Evidence: `limburg-scarcity-results-2026-10-29.md`, `limburg-individual-experiments-implementation-2026-10-29.md`, and `limburg-completed-discharge-readout-2026-11-02.md`.

## 10. What if we use the models for their spatial water-mapping tasks?

We ran four task-specific adaptations with trained raw-input controls, physical controls, event-held-out evaluation and three training-label budgets. This was the latest 720-job run. TerraMind, Galileo and Prithvi generally underperformed trained controls. Galileo deteriorated sharply with 5% training labels. Copernicus-FM radar change retained much of its accuracy and consistently beat the implemented physical change baseline, but did not clearly beat U-Net. Local maps showed substantial timing/coverage/target limitations. Lower training-label fractions were not equally low total annotation budgets because validation labels remained available.

Evidence: `limburg-consolidated-findings-2026-11-10.md` and companion complete numerical tables.

## What this adds up to

We have not found a strong general case that these pretrained representations improve Limburg high-water prediction or replace conventional assessment. We have found narrower task-dependent information, clear limitations, useful measurement/observability evidence and one repeatable positive mapping contrast. These are empirical results, but they are not the broad positive or operational contribution originally hoped for. Whether the resulting evaluation is best presented as a chapter or a smaller paper needs an academic judgment, not another automatic model sweep.

The data audit and software corrections preserve the later valid comparisons; early exploratory configurations should remain historical/supporting evidence. Improving an implementation did not consistently turn the scientific result positive. Nothing in this summary creates a new research question, data request or run.
