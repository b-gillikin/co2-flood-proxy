# Limburg basin-aware AI code review

**Review date:** 2026-10-12

**Scope update, 2026-10-13:** The evidence-access and generator tasks in this
dated review are historical. The active chapter is the analogue representation
comparison in `../limburg-historical-analogue-active-design-2026-10-13.md`.

## Findings corrected

1. **The repository advertised the wrong chapter.** Root, handoff, inventory
   and script documentation still called the case-crossover design canonical.
   They now point to the basin-aware AI design and one active workflow.
2. **Retired code was still in live test discovery.** Case-crossover,
   cross-tributary prediction, atmospheric, CO2/pressure and Maas branches and
   their tests are now in an indexed archive. The moves preserve Git history.
3. **The event-library default contradicted the fixed model contract.** It
   defaulted to 168 hours although pinned TTM-R2 requires 512 hours without
   padding. The live default is now 512 hours; 168 hours remains available only
   when requested explicitly for historical reproduction.
4. **One live evidence pointer broke when its source note was archived.** The
   RWS Maas audit pointer in the source inventory and checked tool now resolves
   to the archived note.
5. **Two arm taxonomies looked like competing designs.** Documentation now
   distinguishes the evidence-access ablation (A0–A3) from the historical
   representation comparison (R0–R4).
6. **Generated caches were not fully ignored.** Pytest and Ruff caches are now
   explicitly ignored.
7. **The analogue baseline used a broader sample than the frozen comparison.**
   It now requires primary usability and complete 512-hour discharge, rainfall
   and weather histories, matching the 570-event TTM/raw-sequence frame.
8. **The withheld response included the assessment cutoff hour.** The event
   library correctly labels hour 0 as available evidence, but the analogue
   summary had included it in the post-onset response. Outcome summaries now
   start at relative hour +1, protected by a regression test.
9. **Partly observed response windows were scored as if complete.** All 570
   events remain in the fixed representation-input frame, but analogue outcome
   scoring now uses the 558 with all 72 withheld discharge hours. The other 12
   remain documented rather than being assigned partial-response targets.

## Live scientific strengths

- assessment-time evidence and withheld outcomes are explicit;
- analogue candidates are strictly earlier and from different storms;
- conventional hydrological signatures remain the mandatory baseline;
- TTM-R2 and AlphaEarth have fixed, narrow roles and pinned acquisition paths;
- numerical and topology work stays in checked code rather than the LLM; and
- measurement provenance and justified abstention are first-class outcomes.

## Remaining implementation risks

1. **Cross-border claim is not yet earned.** The Dutch event library is ready,
   but the held German records still need the common event/provenance schema.
2. **The frozen TTM comparison is designed but not implemented.** It needs the
   raw-sequence control, hidden-state extractor and identical 570-event frame.
3. **AlphaEarth is validated but not joined by code.** The prior-year rule needs
   a deterministic importer with geometry-hash and coverage checks.
4. **Gold answers need human review.** Current tests establish contract and
   retrieval integrity, not reference-answer validity or scoring reliability.
5. **The pilot retriever is deliberately simple.** It is adequate for checking
   evidence paths. Final retrieval must preserve fixed top-k and report errors;
   it should not be tuned on final assessment scores.

None of these risks requires another model or open-data search. They define the
next implementation sequence already recorded in `docs/HANDOFF.md`.
