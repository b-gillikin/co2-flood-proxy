# Limburg whole-code cleanup and download restart

28 October 2026. Brian authorized restarting acquisition, using useful parallelism and a full chapter-code cleanup. This pass changes software reliability, setup and navigation; it adds no research question, model, data restriction or empirical result. Other chapters are untouched.

## Scope and baseline

The pass covered the active tracked tree: 203 Python files (43,475 lines before changes), JSON configurations, the Makefile, environment declaration, script index and current handoff. Whole-tree lint/format, syntax/config parsing and the full scientific test suite were run. Manual review concentrated on acquisition/resume/pause paths, source validation and provenance, output publication/cache boundaries, analogue scoring/bootstrap contracts, Meuse cutoff handling and flood-case evidence linkage. This is not a claim to have rewritten or manually reread every archived line. Retired code remains reproducible in place.

Baseline: 368 tests passed and lint passed; two source files needed formatting. No new failed scientific test was uncovered.

## Download diagnosis and useful parallelism

The old run completed 58/204 monthly sources. Its remaining 146 failures were HTTP 403 responses identifying an unaccepted CDS site-policy revision. They were not missing observations or corrupt source files. A fresh single-month request is now accepted and the resumed worker has advanced beyond the held 58 months. The earlier failure/progress manifest is retained under the raw archive's `run-history/`.

The [ECMWF service notice of 22 October](https://forum.ecmwf.int/t/data-stores-service-protection-measures-affecting-data-downloads-and-account-access-cds-ads-ewds-ecds/15481) asks for sequential submissions. The resumed queue therefore uses **one CDS request at a time**, not four parallel requests. CPU processes cannot accelerate the provider's remote queue. Local lint, tests and read-only result audits ran concurrently with acquisition; `make -j2 check` supports useful local parallelism without increasing provider submissions. No new Azure compute or installed runtime upgrade was performed.

Current command: `.venv-foundation/bin/python scripts/150_fetch_monitoring_land_state.py --download --workers 1`. Live state is `data/raw/limburg_monitoring_land_state/manifest.json`; the resume log is `logs/monitoring-acquisition-2026-10-28/land-state-resume.log`. The complete EO additions remain 442/442 validated files.

## Changes made

- **Stop repeated invalid requests:** account/policy errors now stop the queue immediately. Invalid syntax, provider throttling/outage, source-validation failures and runtime/transfer errors have distinct diagnostics. Unattempted months remain pending instead of becoming misleading failures.
- **Resume accurate progress:** verify all held completed sources before requesting missing months; keep the original acquisition plan unchanged; archive the prior manifest, preserve request-ID history and report the active month, pending months and current runner hash.
- **Recover expired requests/results:** a missing old request or expired result can be renewed once. Permissions or policy errors are not treated as expired data and retried repeatedly. New tests exercise both expiration paths with no network calls.
- **Pause reliably:** SIGTERM/interrupt writes an explicit paused status while retaining completed sources, partial transfers and saved remote request IDs. Lock acquisition precedes plan/progress mutation, preventing a second downloader from rewriting the active state.
- **Portable checks:** the downloader and Makefile discover the existing runtime's PROJ data when not explicitly configured. `make check` now covers lint, format and tests; `-j2` overlaps local checks. The foundation environment declares the existing scientific I/O/CDS/checking dependencies needed by those commands. No packages were installed or changed during cleanup.
- **Consistent source formatting:** scripts 139 and 144 were formatted. Their complete ASTs, including constants, are unchanged. Exact old source snapshots and replacement hashes are recorded in `provenance/source-snapshots/` and the existing compatibility registry. Original scientific manifests were not rewritten to hide the hash change.
- **Current navigation:** the script index distinguishes acquisition (150–152), the latest completed analysis (146–149), flood-case review, and earlier reproduction dependencies. README, one-pager and handoff distinguish resumed acquisition from unimplemented monitoring-loss scoring.

No original delivery, source raster, weight, selected embedding, numerical result table or historical dependency was deleted. No new extraction or scoring job was launched. Existing publication/cache/scoring contracts were kept intact rather than refactored for style alone.

## Verification

- **376 scientific tests passed**, including new resume/circuit-breaker/pause/expiry regressions; **2 retained infrastructure tests passed**.
- Whole active lint and formatting pass; Python syntax and 13 JSON configurations parse.
- The flood-case audit reverified 64 input, 32 source and 50 output hashes plus 52 local links. Its reported visual-review/test counts belong to the original run; this cleanup did not claim to repeat that visual review.
- The latest assessment audit passed its saved-output/provenance checks, 40,128 independent CRPS checks, 2,210,316 paired archive decompositions and cutoff/donor/bootstrap checks. This is verification of existing results, not another scientific analysis.
- The two formatting-only source changes have explicit AST-equivalence proofs and preserved original bytes.

Evidence: `logs/code-cleanup-2026-10-28-checks.log`, `logs/code-cleanup-2026-10-28-flood-audit.log`, `logs/code-cleanup-2026-10-28-assessment-audit.log`, and the accompanying JSON cleanup receipt. One pre-existing NumPy/netCDF C-extension metadata warning remains visible in the test output. Input/source tests pass; the warning was not suppressed and frozen inference runtimes were not upgraded as a cleanup shortcut.

## Remaining work

Let the sequential soil/snow acquisition finish; monitor its manifest rather than infer progress from CPU load. Monitoring-loss simulation/scoring remains the next research implementation task. The completed encoder outputs and earlier findings remain evidence, with their original assumptions and limits.
