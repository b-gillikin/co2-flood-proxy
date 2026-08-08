# Live Scope Decisions

Status: 2026-08-08. Detailed estimator rules are in
`chapter-scope-and-preregistration.md`. Historical decisions remain appended in
`decisions.md`.

1. **Question:** recurrence of fixed signals before independently defined
   high-water onset and the change in those contrasts with geographic distance.
2. **Sequence:** Viefhues single event -> Eryilmaz same-site public explanation
   -> this chapter's recurrence and spatial-extent test.
3. **Primary unit:** natural tributary watercourse; transferability means
   spatial extent across the observed network.
4. **Primary target:** adjacent-hour upward crossing of p99, with thresholds
   estimated outside the held period. Say high water, not flood.
5. **Events:** merge re-crossings and cluster regional storms by unbounded
   72-hour single-linkage; report crossings and chain spans.
6. **Controls:** five deterministic month/hour-matched quiet times; require
   three and exclude p95/storm contamination within seven days.
7. **Analysis:** local event-minus-quiet contrasts establish recurrence;
   all-donor contrasts then estimate one prespecified distance gradient per
   signal.
8. **Public exposure:** RADOLAN catchment-average rainfall, not point rainfall.
   Point stations are sensitivity only.
9. **Transfer:** use every other eligible watercourse as a donor and regress
   contrast magnitude on `log(1 + distance_km)`, with receiver, donor and storm
   random intercepts. Hold out one watercourse as both receiver and donor and
   one of five time blocks for fixed-effect validation. Receiver flow defines
   the outcome and is not its own signal.
10. **Kerkrade:** the regional period must contain July 2021, but the Viefhues
    reanalysis and later CO2 recurrence are a conditional case. If available,
    do not impute the local peak/onset and fit pressure baselines by sensor era.
11. **Groundwater:** secondary mechanism evidence; it cannot block the chapter.
12. **Classifiers:** no prospective or robustness classifier. Eryilmaz's model
    remains predecessor context only.
13. **Stop rule:** if any core regional gate fails, return to the supervisor.
    Do not relax to the current two-year record. Kerkrade-case failure removes
    that case only.
14. **Claims:** no flood prediction, causality, FEWS, alert, false-alarm,
    warning-lead, ungauged-basin or monitoring-placement claim.
15. **Nulls:** null and heterogeneous contrasts are planned results, not
    invitations to search lags or model families.
16. **Time-series filters:** SARIMAX and Kalman filters remain retired. They
    estimate expected dynamics/anomalies, not event recurrence or transfer.
17. **Public weather:** temperature, humidity and pressure need 10 common years
    and one pre-outcome source/assignment per watercourse. The existing short
    point tables are candidates, not an implicit choice.
18. **Local recurrence feasibility:** the conditional Kerkrade case requires at
    least three later exact-onset pair events with complete -72 to -1 hour CO2
    and pressure. Fewer events are missing recurrence evidence, not a null and
    not core chapter failure.
19. **Density:** the draft gate requires 80% observed hours overall and 70% in
    every calendar year for every primary series over the joint period. Values
    remain subject to supervisor approval before lock and cannot be chosen from
    signal outcomes. Across all possible receiver-event/donor combinations,
    complete 13-hour donor windows are required for at least 80% overall and
    70% within every receiver and empirical distance third.
20. **Fold occupancy:** emit all planned receiver-by-block folds. A draft
    eligible fold requires at least three receiver events and a complete spatial
    pair in each distance third. Sparse folds remain visible and do not justify
    a reach claim.
21. **German route:** the held LANUK archive is not a qualifying cohort under
    the draft density/episode rule. Official metadata place `herzogenrath_2`
    and `honsdorf` on Broicher Bach and Beeckflies, not the Wurm. The two held
    Wurm gauges do not overlap the later IoT era, so the archive also supplies
    no later Wurm recurrence events.
22. **Fold-specific inputs:** thresholds, events, controls, quiet scaling and
    contrasts are reconstructed within each crossed fold. Every contrast row
    carries the held watercourse and held block; global contrast tables are
    rejected.
23. **Split gate:** six regional files determine whether the core chapter can
    run. Original/later IoT, era provenance, a valid pair and local onset bounds
    determine only whether the Kerkrade case can be added.
24. **Spatial reading:** report the curve at empirical distance quartiles and
    validate held-out magnitude. Do not turn a confidence-interval crossing or
    sign change into a monitoring radius, maximum reach or gauge-substitution
    claim.
