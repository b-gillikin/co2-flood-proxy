# Wurm/CO2 small diagnostic (2026-10-03)

Internal research aid, not dissertation prose or a change to the live Limburg protocol. Reproduce with `python scripts/60_diagnose_wurm_co2.py`; ignored machine-readable output is in `results/event_study/wurm_co2_diagnostic_2026-10-03/`. The output records input hashes and a random seed.

## Question and design

Does the source-native Viefhues basement CO2 record show a repeatable excess before independently reviewed Wurm/Rimburg p99 crossings after a simple pressure and building-clock adjustment? The K4 sensor covers 15 May to 24 September 2021. Six reviewed Wurm onsets occur in that span, but the sensor has no observations around the 25 May onset. Five events can be described; this is too few, within one season and one building, for a transferable CO2 claim.

For a deliberately small diagnostic, fit quiet hours only, excluding ±72 hours around all six Wurm onsets. The least-squares baseline predicts log CO2 from the K4 indoor pressure level, its square, six-hour pressure change, two 24-hour harmonics and a weekend indicator. There are 2,043 quiet fitting hours. The in-sample R² on log CO2 is 0.444; this is *not* held-out predictive skill. Hours at or above 4,990 ppm are treated as sensor-ceiling censored and omitted from adjusted contrasts, while their counts remain visible. Occupancy, ventilation, mine-gas composition, mine-water state and a sensor calibration history are absent. A pressure-adjusted residual therefore cannot be identified as subsurface CO2.

The table shows median observed-minus-baseline CO2 in the 24 hours before each Wurm p99 crossing. The crossing is not the start of the hydrograph rise or necessarily the start of rainfall.

| Wurm crossing UTC | Usable prior hours | Median pressure-adjusted excess (ppm) | Reading |
| --- | ---: | ---: | --- |
| 25 May 2021 22:00 | 0 | — | Sensor gap |
| 3 June 2021 22:00 | 24 | +115 | Small excess; following 24 h negative |
| 20 June 2021 04:00 | 22 | +13 | Essentially baseline; two capped hours |
| 27 June 2021 21:00 | 24 | +952 | Large excess, but not repeated at every rise |
| 13 July 2021 16:00 | 24 | +690 | Elevated; preceding 48–25 h had an even larger +1,360 ppm excess |
| 2 August 2021 10:00 | 24 | −207 | Below baseline |

The July window had high CO2 well before the p99 crossing. During the following 24–47 h, six hours hit the sensor ceiling; discharge near the July peak is also outside the trusted rating range. The onset pair, rather than the peak magnitude, was reviewed as admissible. July therefore confirms a striking coincident building observation, but does not show whether river water, a common storm, barometric dynamics, occupancy or another local process caused it. The event-by-event sign and magnitude are inconsistent. The predecessor's 1,000-ppm threshold would label some ordinary occupied-building conditions and is not used here as evidence of mine-gas leakage.

## Alternative that starts from Eryilmaz's public-weather finding

Eryilmaz's supported result concerns public weather, especially six-hour pressure change, explaining an **indoor CO2** threshold at one building before July 2021. It does not itself establish flood skill. The existing forward-year, six-tributary rain-trigger analysis already asks the next hydrological question: does a six-hour pressure change add information about high water in the next 24 h beyond rainfall observed so far and issue-time discharge? The Wurm subset has 584 decisions, 75 positives. Models were **trained across all six tributaries** and evaluated here on Wurm rows, so this is not a Wurm-only fit.

| Wurm subset, held-out years 2014–2025 | Rain + flow | Add pressure change |
| --- | ---: | ---: |
| ROC AUC | 0.662 | 0.711 |
| Average precision | 0.291 | 0.326 |
| Brier score | 0.1047 | 0.1018 |

The ROC AUC gain is +0.049, with a year-resampled interval of +0.024 to +0.076; omitting 2024 leaves +0.047. The average-precision gain is +0.035 (interval −0.004 to +0.088), and Brier improvement is 0.0029 (−0.0017 to +0.0079). These intervals resample existing forward predictions by year and do not refit models. A positive ranking result remains, but probability accuracy is unresolved. The broader six-tributary test found that pressure improved ranking between storm decisions, not selecting which tributary within the same storm would cross. Its six-hour change correlated with rainfall in the following 24 h, suggesting an atmospheric summary of storm development rather than independent evidence of a direct pressure-to-runoff mechanism. ERA5-Land is retrospective reanalysis, not an archived as-issued forecast.

## Assessment

The CO2 path is not yet a coherent transferable Wurm high-water finding. Two positive events are striking, but one usable event is negative, another is near baseline, one has no sensor coverage, and a building-specific residual cannot be measured at other tributaries. This does not erase the Viefhues observation; it narrows what it can support.

The Eryilmaz-to-public-weather path is more promising: the Wurm subset shows a positive ranking increment for six-hour pressure change, with clear limits. The precise next question is whether that increment survives a Wurm-centred design using the already held rainfall and upstream hydrology, and whether it improves a decision-relevant measure rather than AUC alone. An operational forecast evaluation would separately require as-issued inputs; it is not a prerequisite for this retrospective question. The current diagnostic does not justify claiming FEWS skill or changing the chapter yet. Avoid using an estimated CO2 proxy as an extra transferable variable: if it is computed from pressure, it adds no independent information beyond pressure itself.
