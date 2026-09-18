# Live Scope Decisions

Status: 2026-09-18, protocol draft 0.9. Estimator details are in
`chapter-scope-and-preregistration.md`. Historical decisions, including the
draft 0.8 design, remain appended in `decisions.md`.

1. **Question:** how are public signals in the 72 hours before high-water onset
   associated with that onset, and does the timing differ between warm and
   cold seasons?
2. **Design:** time-stratified case-crossover, analysed as conditional
   quasi-Poisson regression with distributed-lag cross-bases.
3. **Sequence:** Viefhues and Eryilmaz motivate the question. No CO2 is
   analysed.
4. **Outcome:** adjacent-observation upward crossing of the watercourse's own
   p99, per rating era. Say high water, not flood. Receiver flow is never its
   own signal.
5. **Events:** merge re-crossings and cluster regional storms by unbounded
   72-hour single linkage.
6. **Comparison:** at-risk hours in watercourse × year × month × hour-of-day
   strata. At risk means flow in the previous hour at or below p99 and no upward
   crossing in the preceding 72 hours. There are no other exclusion windows.
7. **Signals:** hourly catchment rainfall (principal); hourly relative humidity
   and six-hour pressure change (ERA5-Land). Temperature and pressure level are
   dropped. Network state is descriptive only.
8. **Primary estimand:** warm-minus-cold difference in the rainfall
   lag-response over lags 1–72, as cumulative association and median
   association lag.
9. **Uncertainty:** calendar year-month block bootstrap, 999 replicates.
10. **Rainfall source:** RADKLIM-RW if it covers the joint period, otherwise
    operational RADOLAN RW throughout. Never splice them.
11. **Weather source:** ERA5-Land only; nearest cell to each fixed catchment
    centroid.
12. **Catchments:** delineated from a cross-border DEM.
13. **Floors:** at least 5 natural, hydrologically independent watercourses
    (6 for the S3 sign test);
    10 common years including July 2021; 40 regional storms, 15 per season;
    20 episodes per watercourse; 80% overall and 70% annual coverage.
14. **Independence:** branches of one split system count as one watercourse,
    which applies to Geleenbeek and Vloedgraaf.
15. **Censoring:** censor only onsets whose onset hour is missing, failed or
    outside the rating domain.
16. **Stage:** conditional, onset-timing recovery only.
17. **Distance:** a conditional module only if the LANUK export passes the gates
    before lock; the lock date is the cutoff.
18. **Stop rule:** if a core gate fails, stop and record a dated rescoping
    decision. Never substitute the rolling record.
19. **Nulls:** null and heterogeneous results are planned results, not prompts
    to search lags, bases, thresholds or model families.
20. **Methods ruled out:** classifiers, SARIMAX, Kalman filters, anomaly
    detectors, best-model exercises and any degree-of-freedom search.
21. **Claims ruled out:** prediction, causality, FEWS performance, warning lead
    time, alert or trigger claims, damage, monitoring placement and ungauged
    basins.
22. **Waterschap sampling:** each value is the mean of the preceding 15 minutes;
    a blank is unavailable. Build an hour only from four admissible
    quarter-hours.
23. **Availability is not validity:** apply rating domains and documented
    failures before events are built.
