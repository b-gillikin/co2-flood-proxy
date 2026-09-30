# Limburg next-pass method note

Status: internal research aid, 2026-09-29. This does not change the chapter
question, write dissertation prose, or replace the completed first fit.

## What the first-fit diagnostic now shows

`scripts/50_audit_observed_rainfall_histories.py` reconstructs the existing
at-risk rows and compares each onset with non-onset hours in the same
watercourse × year × month × hour-of-day stratum. Its windows exclude the onset
hour and use complete rainfall histories only. Re-run it to recreate the
ignored CSV files prefixed `observed_rainfall_` in
`results/event_study/real_data_v1/`.

`scripts/51_fit_observed_window_followup.py` makes one explicitly exploratory
fit of the two windows, with the same onset, comparison hours, strata and joint
year-month bootstrap as the original fit. Its estimates, all attempted draws,
least-expected onsets, month-influence checks and run manifest are also in that
ignored directory.

| Season | Onsets | Median 1–24 h rainfall at onset | Median matched control mean | Median paired difference | Median 25–72 h paired difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cold | 391 | 11.23 mm | 1.23 mm | 9.89 mm | 0.87 mm |
| Warm | 330 | 17.20 mm | 1.89 mm | 15.10 mm | 0.85 mm |

Across the six watercourses, the 1–24 h paired difference is positive for
roughly 92–100% of onsets in each site-season cell. The 25–72 h difference is
positive for only about half, with site-season medians from −0.44 to 3.56 mm.
These are descriptive onset-level summaries: shared storms mean that 721 onsets
are not 721 independent weather events. The warmer season's larger rainfall
differences do not overturn the first fit's uncertain *seasonal lag-timing*
difference; those are different quantities.

The first model's 2.236 mm/h constant contrast across all 72 lags represents
160.99 mm in 72 h. Among fitted onsets, observed 72 h catchment rainfall has a
median of 18.13 mm, a 90th percentile of 31.59 mm, and a maximum of 80.54 mm.
This strengthens the case for withholding that cumulative model index as a
literal event-scale effect. The issue is the assumed *shape* as well as total
volume: no catchment has 72 consecutive hours at that intensity. The fitted
lag curves and seasonal timing comparison remain documented first-pass
results. The very large conditional Pearson dispersion and a highly unlikely
2021-07-04 Geleenbeek onset also warrant model-fit review; that onset has
16.36 mm in the preceding 24 h and is not thereby a bad gauge measurement.

In the two-window fit, the log association per additional 10 mm in the prior
1–24 h is 3.56 (95% joint-block bootstrap interval 3.16–4.19) for warm months
and 6.05 (5.17–7.39) for cold months; the warm-minus-cold difference is −2.50
(−3.84 to −1.40). For the 25–72 h window, the corresponding values are 0.99
(0.63–1.44) and 1.75 (1.21–2.43). All 999 draws fit, now resampling the same
192 calendar blocks as the first fit, including blocks with no onset. The
conditional Pearson dispersion drops from roughly 5,294 in the original spline fit to 8.3, though
8.3 is still large and the two models answer different timing questions. The
earlier-window model coefficient is positive despite the weak unadjusted paired
rainfall difference; it is conditional on recent rainfall and should not be
read as independent evidence of antecedent soil moisture. These effect scales
are strong enough that leverage, exposure support and residual behavior need
inspection before substantive interpretation. Larger warm-season *observed*
rainfall and stronger cold-season *per-mm fitted association* are not the same
claim. The original median-lag seasonal comparison remains uncertain.

For recent rain, only 1.8% of cold-season and 4.5% of warm-season matched
non-onset rows have at least 10 mm, versus 61% and 83% of onset rows. Thus a
10 mm model increment is observed but lies in a thinly populated comparison
region; avoid presenting its exponentiated coefficient as a broadly calibrated
flood-risk multiplier. The least-expected simpler-model onset is Geul at
2010-02-04 17:00 UTC: 0.59 mm in lags 1–24 but 35.87 mm in lags 25–72.
Geleenbeek at 2021-07-04 19:00 UTC remains unusual. These warrant hydrograph
and input review, not automatic exclusion. Both crossings were retained as
exact onsets by the prior measurement review, without nearby gaps, rating-era
changes or abrupt-rise flags.
Their two window sums were independently recomputed from the held hourly radar
CSV at the exact UTC timestamps and match the diagnostic output. The same
check passed for Geleenbeek and Gulp onsets on 2021-07-13.
Omitting all of July 2021 changes the recent-rain warm-minus-cold point estimate
from −2.50 to −2.39; omitting each of the five months with the most onsets gives
−2.62 to −2.34. These are point-estimate influence checks, not new uncertainty
intervals, and do not remove the broader model-support caution.

## Literature-checked diagnostic and interpretation

Four direct radar source-sum checks, including two July 2021 onsets, pass; the
automated lag-index test verifies the window boundaries. The two figures
generated by `scripts/52_review_retrospective_fit.py` show observed rainfall
distributions and selected 72 h rainfall–discharge histories. Two unusual
crossings have a plausible time sequence rather than a demonstrated gauge
error: Geul on 2010-02-04 follows an earlier wet pulse and a near-p99 flow
crest; Geleenbeek on 2021-07-04 follows a short, intense catchment-rain pulse.
The label *onset* means p99 threshold crossing, not the start of a storm or the
start of the hydrograph rise. At the Geul crossing, prior-hour discharge was
95% of p99. Across all 724 reviewed onsets, 61% have prior-hour discharge at
least 80% of p99. This is part of the outcome definition, not grounds to
discard these events.

The 1–24 h onset rainfall exceeds every matched control hour in its own
stratum for 291/391 cold onsets (74%) and 243/330 warm onsets (74%). By
contrast, the corresponding 25–72 h percentages are 11% in both seasons.
Observed recent rainfall and control rainfall have limited within-stratum
overlap. This supports the direction of the *observed* contrast but means the
large per-10-mm model coefficients lean heavily on an assumed linear response
where comparators are sparse. Sparse conditional-model data can exaggerate
effect magnitudes even when estimates converge
([Greenland et al. 2000](https://academic.oup.com/aje/article-abstract/151/5/531/117288));
overdispersion is also consequential in case-crossover inference
([2024 Biometrics study](https://academic.oup.com/biometrics/article/80/4/ujae117/7829046)).

Joint 192-month-block bootstrap intervals for median *case minus matched
control mean* rainfall are 9.89 mm (9.02–10.51) cold and 15.10 mm
(13.83–16.95) warm at lags 1–24. At lags 25–72, the medians are 0.87 mm
(−0.48 to 2.23) cold and 0.85 mm (−0.46 to 2.45) warm. These are descriptive
summaries of clustered onsets, not causal effects or forecast accuracy.

The original distributed-lag curve is positive and greatest close to onset in
both seasons, but it rises again near the 72 h boundary; the latter is
model-dependent and not direct evidence of a second physical response. Its
warm-minus-cold median association lag is −2 h (95% joint-block interval
−10 to +4): no resolved seasonal timing difference. Predicting a distributed-
lag summary for an actual exposure history is supported by the method
([Gasparrini 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4098103/)); the
first fit's constant 72 h contrast should not be translated into a real storm
effect. The simpler two-window fit improves that contrast's *physical form*
but does not solve the sparse control support, so it remains exploratory.

The pre-existing humidity-plus-pressure model uses the same 721 onsets. Its
humidity index is positive after rainfall adjustment, but its cumulative
72 h contrast is also difficult to interpret and its conditional Pearson
dispersion is extreme. The pressure-change estimate spans zero and its lag
summary is mostly undefined. Neither atmospheric result establishes an
independent physical mechanism or useful forecast signal; report humidity as
an exploratory association and pressure as unresolved.

The Geul event study finds that daily extreme rain alone is insufficient and
that prolonged rain and wet initial conditions matter
([Tsiokanos et al. 2024](https://hess.copernicus.org/articles/28/3327/2024/)).
German and British event studies distinguish rainfall properties from
antecedent catchment state
([Tarasova et al. 2018](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2018WR022587),
[Zheng et al. 2023](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2022WR033226)).
Our 25–72 h rainfall total is not a soil-moisture measurement; its weak
unadjusted matched difference does not imply that antecedent wetness is
unimportant. These sources do not require new data for the present analysis.

**Recommended result hierarchy, decided after seeing the first fit:** Lead
the internal interpretation with observed matched rainfall histories and
their block intervals across the six tributaries. Report the original
seasonal lag estimate, including its null interval, as a model-based secondary
result. Keep the two-window coefficients and atmospheric model as exploratory
checks, without headline risk ratios. This preserves the question, event
definition, cohort and comparison design while making the supported claim
scale explicit. It does not retroactively make the post-fit diagnostics
prespecified. The resulting contribution is a documented cross-tributary
comparison of observed signals before threshold crossing; the simple fact
that rain precedes high flow is not itself a novel mechanism.

## Separate simulated-storm prospect

Once the retrospective result is stable, a bounded scenario study could use
one well-observed tributary, several *observed* radar rainfall profiles, and
contrasting plausible antecedent states. A rainfall–runoff model would have to
be calibrated and validated against observed discharge before producing
conditional hydrographs or threshold crossings. Recombining historical
rainfall and antecedent states has a published precedent
([Han et al. 2025](https://www.nature.com/articles/s43247-025-02691-6)).
The present case-crossover association model cannot itself simulate discharge.
Scenario outcomes would describe what the calibrated model produces under
specified inputs, not forecast skill or operational warning lead time. Testing
prediction would be a further, distinct hindcast design with issue-time input
discipline, held-out storms and a persistence benchmark
([Harrigan et al. 2023](https://hess.copernicus.org/articles/27/1/2023/)).
