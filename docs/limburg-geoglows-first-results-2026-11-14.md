# GEOGLOWS comparison: first interpretation

14 November 2026 local run date. Internal results aid; not dissertation prose.
All four v2 fits and the automated review completed. All six baseline/score
receipts and the review receipt verified against their inputs and output hashes.
Runtime approximately 26 minutes. No model refit or outcome-selected exclusion
was made during this first interpretation.

## What the completed run supports

On 2,482 valid high-water assessments spanning 273 regional storms at seven
gauges, conventional analogue MAE rises from 0.065400 to 0.073094 mm/h when
observed input Q is replaced by GEOGLOWS: **+11.8%**. The paired difference is
+0.007694 mm/h, with shared whole-year bootstrap interval [0.005517, 0.010580].
These are repeated gauge/issue assessments, not 2,482 independent floods.

| Method | Observed-input high-water MAE | GEOGLOWS-input high-water MAE |
| --- | --- | --- |
| Conventional analogue mean | 0.065400 | 0.073094 |
| Hydrology-only correction | 0.066897 | 0.070645 |
| Presto-equipped correction | 0.090349 | 0.075533 |
| AnySat-equipped correction | 0.069554 | 0.071981 |

Lower is better. The same full high-water assessment cohort supports these
rows. Relative to each source's conventional baseline, the changes are:
hydrology +2.3% / −3.4%, Presto +38.1% / +3.3%, AnySat +6.4% / −1.5%
(observed / GEOGLOWS). These percentages are point estimates, not independent
significance tests or a model ranking across all possible settings.

Hydrology-only correction improves GEOGLOWS assessment by −0.002449 mm/h
[−0.003443, −0.001573]. The AnySat-equipped pipeline's small net gain against
conventional GEOGLOWS assessment is uncertain: −0.001113
[−0.002688, 0.000548]. Its actual encoder increment over its matched raw control
is adverse, +0.000339 [0.000007, 0.000808]. Presto's GEOGLOWS encoder increment
is +0.000474 [−0.000201, 0.001100]. No reliable incremental encoder improvement
is established, including the source-by-encoder interaction, whose intervals
span zero for both models.

The specified simple calibration also helps. On its eligible 2,354 high-water
assessments (255 storms, 2011–2025), calibrated analogue matching reduces MAE
by about 3.6% versus uncalibrated GEOGLOWS matching: −0.002507
[−0.004367, −0.000587]. Its difference versus hydrology-only correction on that
same support is +0.000086 [−0.002158, 0.002539], so this run does not distinguish
the two approaches clearly. Do not insert its absolute MAE into the table above
without accounting for the first-year calibration-support difference.

## A concrete correction failure requiring review

For Randerath at the 6 June 2016, 15:00 UTC assessment, the next-24h observed
peak is 15.37 m3/s. Conventional matching estimates 12.27, the Presto raw-control
head 61.01, and the Presto-equipped head **316.41 m3/s**. The 21:00 assessment
also overestimates severely. Several other Randerath 2016 storms contribute to
the large observed-input Presto average.

The Randerath 2016 fold has 704 historical training assessments but only 52
EO-supported assessments across **13 storms and four monthly Presto contexts**.
AnySat has 36 supported assessments across nine storms/seven weekly contexts.
Validation uses 2015 and 2014; 2014 has no Sentinel-2 support. This is evidence of
thin effective EO support and a failed local correction, not proof that this
support limitation alone caused the failure or that the pretrained encoder is
intrinsically unsuitable. The raw head also fails, so an encoder-only explanation
is inadequate. Large errors survive restricting evaluation to clean verification;
they are not simply July 2021 rating uncertainty.

Later encoder changes are mostly zero or small. Do not silently remove 2016,
publish its disproportionate mean effect as a universal model verdict, or infer
that excluding it would establish a general encoder advantage. Preserve the
full result and diagnose the fitted transformation/support/extrapolation first.

## Interpretation boundary and next useful work

This run establishes an input-source challenge and useful improvement from
ordinary correction. It does not establish satellite-encoder value for this
discharge-assessment pipeline, a live fallback, warning lead time or avoided
flood impacts. Global model output remains a reanalysis-based proxy at
approximate gauge locations, not lower-quality measured gauge data.

Next: review effective EO training support, scaling/extrapolation and actual
helped/harmed event trajectories, starting with Randerath 2016. This needs the
existing outputs, not another encoder sweep or a new data collection campaign.
The first readout is not a completed causal diagnosis of the local head failure.

Sources: `results/limburg_geoglows_stages12_v2/review/{within_stage_effects.csv,
source_effects.csv,source_by_encoder_interaction.csv}`, saved per-job predictions
and tuning records. Additional calibration-versus-hydrology contrasts use the
same saved 999 year multiplicities and fixed-population summary. A compact
[absolute/relative readout](reviews/limburg-geoglows-first-results-2026-11-14.json)
records the table calculations. No new empirical fit was performed.
