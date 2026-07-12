# Week 4 Signal Interpretation

Status: exploratory screening followed by a `NOT SUPPORTED` distributed-lag
test. The current residual window has 3719 hourly rows from
2025-02-01 15:00 UTC to 2026-04-13 02:00 UTC after merging local Blynk exports.
The earlier 14-day lag scan generated a candidate timescale, but the locked
follow-up does not establish an antecedent-wetness signal on this record.

## What Looks Interesting

- The exploratory scan linked the residual to Geul Hommerich discharge at
  roughly 10.6 days of feature lead time, but this is not a finding. At the
  locked 10-day precipitation half-life, the coefficient was not significant,
  the bootstrap interval crossed zero, and the future-rain placebo was stronger
  than the antecedent term.
- Residual random-forest importance is led by indoor relative humidity, Geul
  Hommerich discharge, 24-hour indoor-temperature tendency, indoor temperature,
  and 24-hour outdoor-humidity tendency.
- In the hydrology-proxy scan, the residual appears as a secondary feature after
  indoor temperature and humidity. That is not a negative result; it suggests
  the residual may be useful only after separating ordinary environmental
  co-movement.

## What To Be Careful About

- Treat the high-lag discharge correlations as shared low-frequency structure
  unless the unchanged frozen rerun passes every decision criterion.
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
- Rerun `scripts/12_distributed_lag.py` unchanged on the frozen snapshot.
- Prioritize the locked direct groundwater/mine-water test when those data
  arrive; precipitation is an indirect state proxy.
