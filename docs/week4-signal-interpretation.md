# Week 4 Signal Interpretation

Status: exploratory. The current residual window has 3719 hourly rows from
2025-02-01 15:00 UTC to 2026-04-13 02:00 UTC after merging local Blynk exports.
The 14-day lag scan is more stable than the first pass, but the IoT record is
still gappy enough that this remains characterization rather than confirmation.

## What Looks Interesting

- The strongest lagged correlations now link the barometric CO2 residual to
  Geul Hommerich discharge at roughly 10.6 days of feature lead time. The top
  current run is around `r = 0.246`, much weaker than the short-window first
  pass.
- Residual random-forest importance is led by indoor relative humidity, Geul
  Hommerich discharge, 24-hour indoor-temperature tendency, indoor temperature,
  and 24-hour outdoor-humidity tendency.
- In the hydrology-proxy scan, the residual appears as a secondary feature after
  indoor temperature and humidity. That is not a negative result; it suggests
  the residual may be useful only after separating ordinary environmental
  co-movement.

## What To Be Careful About

- The high-lag discharge correlations are weaker after adding IoT coverage, so
  they should be treated as candidate timing structure rather than a finding.
- Random forests here are descriptive. They are fit on the same rows they
  explain, so the feature rankings should guide follow-up plots and models, not
  serve as evidence by themselves.
- Indoor humidity and temperature are prominent. That could mean real ventilation
  or building-state behavior, not hydrological forcing.

## Near-Term Follow-Ups

- Re-run the exact Week 4 script after any additional IoT data land.
- Use KNMI pressure and temperature to check whether Visual Crossing is adding
  source-specific structure to the residual.
- Use RIVM/Luchtmeetnet transfer data as a broader-air-quality comparison, not
  as a direct CO2 substitute.
- Before Week 5 confirmatory modelling, make one focused plot around the top
  lag windows: residual, discharge, humidity, wind speed, and soft-label state.
