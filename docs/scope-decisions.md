# Live Scope Decisions

Status: 2026-08-11. Estimator details are in
`chapter-scope-and-preregistration.md`. Historical decisions remain appended in
`decisions.md`.

1. **Question:** which fixed signals recur before independently defined high
   water, and how do the direction and magnitude of their event-minus-quiet
   contrasts change with distance?
2. **Sequence:** Viefhues single event -> Eryilmaz same-site public explanation
   -> this chapter's recurrence and spatial-extent test.
3. **Transferability:** spatial extent across the observed natural-tributary
   network, not prediction, substitution, propagation, a causal distance
   effect, an operational radius or ungauged-basin performance.
4. **Outcome:** adjacent-observation upward crossing of joint-period p99. Say
   high water, not flood. Receiver flow defines the outcome and is not its own
   signal.
5. **Events:** merge re-crossings and cluster regional storms by unbounded
   72-hour single linkage; report crossing counts and chain spans.
6. **Controls:** take five deterministic same-month/same-hour quiet times;
   require three and exclude p95/storm contamination within seven days.
7. **Signals:** RADOLAN 24/72-hour catchment rainfall and donor-flow level/change
   are principal. ERA5-Land temperature, humidity and pressure form one fixed
   Eryilmaz-derived atmospheric block.
8. **Analysis:** local event-minus-quiet contrasts establish recurrence. Spatial
   contrasts use every other eligible watercourse and are aggregated to one
   median per ordered receiver-donor pair.
9. **Distance model:** for each fixed signal, fit
   `pair_median_contrast ~ 1 + log(1 + distance_km)` with equal pair weights.
   Resample complete storms for uncertainty and refit after omitting each
   watercourse as an influence check. No mixed-effects or held-out prediction
   model.
10. **Public weather:** ERA5-Land is the sole regional source. Acquire
    2001–2025 temperature, dew point and surface pressure; assign the nearest
    grid cell to each fixed catchment centroid and derive relative humidity.
    Visual Crossing is predecessor source context only.
11. **Kerkrade:** July 2021 is required regionally, but new Viefhues reanalysis
    and later CO2 recurrence are conditional. Do not invent a local onset or
    peak. Fit pressure baselines by documented sensor era only if the case gate
    passes.
12. **Groundwater:** secondary mechanism evidence; it cannot block the chapter.
13. **Data floor:** provisionally require 10 watercourses, 10 common years, 20
    p99 episodes per watercourse and 40 storms. These are design safeguards, not
    field standards, and remain subject to a blind audit and supervisor freeze.
14. **Coverage:** provisionally require 80% observed hours overall and 70% in
    every year for each primary series, plus 80% all-donor window availability
    overall, 70% by receiver and distance third, and 10 complete events per
    ordered pair. Missing values stay missing.
15. **Stop rule:** if a core gate fails, return to the supervisor. Do not lower
    it to admit the rolling record. Kerkrade-case failure removes that case only.
16. **Nulls:** null and heterogeneous contrasts are planned results, not prompts
    to search lags, thresholds or model families.
17. **Methods ruled out:** no classifier, SARIMAX, Kalman filter, anomaly
    detector, random-effects framework or best-model exercise.
18. **Claims ruled out:** no flood prediction, causality, FEWS, alert,
    false-alarm, warning-lead, monitoring-placement or general ungauged-basin
    claim.
19. **German route:** the held LANUK archive is not a qualifying cohort. Its
    Wurm gauges do not provide the July 2021/later-IoT support needed for the
    conditional Kerkrade case.
20. **Separate gates:** the six-file regional audit determines whether the core
    chapter can run. IoT provenance, a defensible pair, local bounds and later
    complete events determine whether the Kerkrade case can be added.
21. **Viefhues source:** source-native non-ABC K4 is the reproducible July 2021
    record and is normalised without gap filling. The longer cleaned thesis
    table is processed output with missing intermediates.
