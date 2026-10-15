# Limburg: current research ideas

Internal research aid. These ideas are distinct from the archived October 4
Idea 1/Idea 2 numbering. Saving an idea does not implement it or change the
current empirical results. Brian writes dissertation prose.

## Idea 1 — Predicting divergence between apparently similar events

Saved at Brian's request on 2026-10-15. Status: proposed extension, not run.

**Question:** Can we tell, while an event is unfolding, whether it will develop
differently from its apparent historical analogues?

**Operator-facing interpretation:** Given an ongoing rise and similar past
events, distinguish an approaching peak from continued escalation, and estimate
the additional rise with uncertainty. This would test early identification,
whereas the current explanation conditions on rainfall observed later.

**Smallest useful design:**

- Primary outcomes: additional peak discharge over the next 6 and 12 hours.
- Inputs: rainfall/discharge history available at the assessment time, plus
  available peer-gauge observations. No realized future rainfall in prediction.
- Comparators: persistence/simple trend, conventional rainfall–flow analogues,
  and the existing frozen TTM representation. No automatic new model family.
- Fit or retrieve from earlier years, test later years; keep all gauges from
  the same storm together and purge overlapping reference outcomes.
- Define assessment times from observations already available, without using
  eventual storm totals or storm endings. Use past-only normalization and
  scaling. Separate verification-quality flags from issue-time information.
- Select queries independently of later outcome completeness, then score each
  horizon where verifiable. Preserve unknown/uncertain extremes.
- Show when predictions for similar events separate and whether the separation
  is correct, alongside the complete eligible population and calibration checks.

Held data can support an observation-history-only retrospective forecasting
test. Its limitations from unknown future rainfall are part of the result.
Archived rainfall forecasts could support a later weather-informed version;
they are not a new requirement for the first test. Reanalysis is not an
as-issued forecast. Modern pretrained weights also do not recreate the models
available to historical operators.

AlphaEarth remains optional static/catchment context for cross-river transfer;
it is not forced into dynamic state prediction. The [dynamic foundation-model
review](reviews/limburg-dynamic-foundation-model-shortlist-2026-10-15.md)
assesses complementary candidates separately. Model comparison
does not by itself identify a flood-generating mechanism or prove operator
benefit. No implementation or model/data download has been initiated for Idea 1.

Sources motivating the task: [Tarasova et al. (2018), event response dynamics](https://doi.org/10.1029/2018WR022587)
and [Bellier et al. (2017), meteorological analogues in forecasting](https://doi.org/10.1002/2017WR021245).
The [existing scientific review](reviews/limburg-analogue-forecasting-review-2026-10-15.md)
sets out prior-only selection, transfer and calibration considerations. Its
distributional recommendation has already been executed; Idea 1 proposes the
separate past-only prediction question.
