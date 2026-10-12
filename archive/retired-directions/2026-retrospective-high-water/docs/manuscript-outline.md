# Manuscript outline: pre-high-water signals across Limburg tributaries

Status: working analysis outline; no result reported
Status date: 2026-09-24 (protocol draft 0.10)

This outline turns the live protocol into a paper-shaped chapter. It does not
alter the estimands or measurement-validity rules in
`chapter-scope-and-preregistration.md`.

## Working title

**How far ahead? Seasonal lag structure of public hydrometeorological signals
before high water on Limburg tributaries: a time-stratified case-crossover
study**

If the seasonal fallback applies (§2 of the protocol), drop "seasonal" from the
title and lead with the pooled lag structure.

## Abstract

The question, the case-crossover design, the cohort and storm counts, the
seasonal lag result, the atmospheric-block result, and the feasibility-bounded
implication for warning on small tributaries. No flood-prediction, causal or
warning-performance language.

## 1. Introduction

### 1.1 Small tributaries and the warning gap

- Main-river warning in the Netherlands is national, while tributaries fall to
  the water boards. July 2021 showed the cost of that gap on the Geul and its
  neighbours.
- Check the exact recommendations of the post-2021 Dutch reviews before citing
  them.

### 1.2 From one Kerkrade observation to a regional question

- Viefhues and Eryilmaz as motivation: an indoor anomaly, then a public-weather
  explanation.
- Why the transferable question concerns public regional signals, not one
  sensor.

### 1.3 Question, estimand and contribution

- State the question verbatim from the protocol.
- Primary estimand: the seasonal difference in the rainfall lag-response.
- Contribution: evidence on how far ahead public signals depart from normal,
  and a design new to this literature.

### 1.4 Boundaries

- High water is not relabelled as damaging flooding.
- "Association lag" is not an operational warning lead time.
- No prediction, causal, trigger or ungauged-basin claim.

## 2. Study area and data

### 2.1 Limburg tributaries and the cohort

- Hydrological setting, cross-border headwaters, the independence rule for
  split systems and the final cohort.

### 2.2 Discharge records

- Waterschap provenance, sampling semantics, rating eras, July 2021 station
  status and the onset-only censoring rule.

### 2.3 Rainfall and weather

- RADKLIM or RADOLAN catchment rainfall over cross-border catchments.
- ERA5-Land relative humidity and pressure change.

## 3. Methods

### 3.1 High-water onsets and regional storms

- Adjacent-hour p99 crossings per rating era; 72-hour single linkage.

### 3.2 The time-stratified case-crossover design

- At-risk hours; watercourse × year × month × hour-of-day strata.
- Why this removes overlap and seasonal-trend bias.

### 3.3 Distributed-lag conditional Poisson models

- The cross-basis, the fixed rainfall contrast and the season interaction.
- Model specifications: primary and S1–S4.

### 3.4 Uncertainty

- Calendar year-month block bootstrap.

### 3.5 Secondary and descriptive analyses

- Exposure-response shape, the Fase comparison where supplied, stability, July
  2021 and the two-stage pooling sensitivity.

## 4. Results

### 4.1 Gate and sample audit

- Watercourses, storms per season, onsets, censored onsets and coverage.

### 4.2 Seasonal lag structure (primary)

- Lag-response curves by season, cumulative association and median association
  lag, with intervals.

### 4.3 Beyond rainfall

- Humidity and pressure-change lag-responses adjusted for rainfall.

### 4.4 Replication and stability

- Watercourse forest plot and sign count; the 2010–2017 and 2018–2025
  comparison; the two-stage pooling sensitivity.

### 4.5 Exposure-response shape and operational thresholds

- Rainfall exposure-response, and the Fase comparison where thresholds exist.

### 4.6 July 2021

- The regional trajectory and its position against the pooled relationship.

## 5. Discussion

- Answer the question at the achieved scale.
- What seasonal lag structure implies for warning on small tributaries:
  nowcasting and prepared responses where association is short, anticipatory
  action where it builds over days. Feasibility claims only.
- Cross-border headwaters and upstream information.
- Relation to the predecessor studies.
- Limitations: achieved watercourse count, shared storms, associational design, rating
  stability, radar quality at the edge of the domain.

## 6. Conclusion

- One direct answer on seasonal lag structure.
- One answer on whether the atmospheric block adds anything.
- The minimum further evidence needed for any operational claim.

## Planned core artifacts

1. Study network and cross-border catchment map.
2. Gate and input-provenance table.
3. Onset, storm and at-risk-hour flow diagram.
4. Seasonal rainfall lag-response figure (primary).
5. Watercourse forest plot.
6. Network-state event-time profiles.
7. July 2021 regional trajectory.
8. Result-to-claim table.
