# Week 4 Signal Interpretation

Status: exploratory. The current residual window has 622 hourly rows from
2026-03-17 22:00 UTC to 2026-04-13 02:00 UTC, so the 14-day lag scan is useful
for triage but not yet confirmatory.

## What Looks Interesting

- The strongest lagged correlations link the barometric CO2 residual to Geul
  and Wurm discharge series at roughly 13 days of feature lead time. The top
  current run shows correlations around `r = -0.59` for Geul Meerssen and
  `r = -0.58` for Geul Hommerich.
- Residual random-forest importance is led by indoor relative humidity, Kerkrade
  wind speed, 24-hour humidity tendency, 24-hour wind-speed tendency, and Geul
  Meerssen discharge.
- In the hydrology-proxy scan, the residual appears as a secondary feature after
  indoor temperature and humidity. That is not a negative result; it suggests
  the residual may be useful only after separating ordinary environmental
  co-movement.

## What To Be Careful About

- The high-lag discharge correlations may be window artifacts. A 26-day residual
  window makes a 13- to 14-day lag sensitive to the few events currently present.
- Random forests here are descriptive. They are fit on the same rows they
  explain, so the feature rankings should guide follow-up plots and models, not
  serve as evidence by themselves.
- Indoor humidity and temperature are prominent. That could mean real ventilation
  or building-state behavior, not hydrological forcing.

## Near-Term Follow-Ups

- Re-run the exact Week 4 script after the added IoT data land.
- Use KNMI pressure and temperature to check whether Visual Crossing is adding
  source-specific structure to the residual.
- Use RIVM/Luchtmeetnet transfer data as a broader-air-quality comparison, not
  as a direct CO2 substitute.
- Before Week 5 confirmatory modelling, make one focused plot around the top
  lag windows: residual, discharge, humidity, wind speed, and soft-label state.
