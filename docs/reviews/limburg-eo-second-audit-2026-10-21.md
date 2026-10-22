# Second audit of the Limburg EO workflow — 2026-10-21

The first correction pass repaired aggregation and explicit model selection, but
it missed the analogous stale-output problem in the comparison writer. This
second audit found that issue plus four reproducibility/maintenance weaknesses.
These findings concern execution integrity; they do not establish corruption of
existing scientific findings or require a new RQ, dataset or model.

This pass audits the fixes and their handoffs. It does not repeat every historic
chapter analysis or certify every line of archived code. Production code and
active jobs were left unchanged; only audit records were written.

## Findings, in priority order

### 1. High: comparison output can mix an old result with a new run record

**Location:** [script 102](../../scripts/102_connect_limburg_eo_experiments.py),
lines 305–315 and the final `experiment_plan.json` write.

Score tables are written only if `scores`/`donors` are nonempty. Existing tables
are never cleared or isolated. Planning also writes its new coverage/plan into
the same destination as an earlier scored run.

**Reproduced using the real writer in temporary directories:** pre-existing
`event_assessments.parquet`, `selected_donors.parquet` and `paired_intervals.csv`
survived a planning invocation while the plan became `executed=false`. They also
survived a `--run` invocation with explicit empty engineering vectors, where the
new plan said `executed=true` and `scored_sets=0`. No empirical scoring was invoked
in that fixture. The files remained beside the new plan without output hashes
binding them to it.

**Consequence:** a subsequent reader could mistake leftover scores for the output
of the latest inputs/run. The aggregate-layer fix does not protect this writer.
No held new EO scientific result has been demonstrated to be contaminated.

**Correction:** give planning a separate destination; publish each scientific
run from a fresh staging directory with input/output hashes and an explicit
completion/no-estimable-result state. Preserve the preceding complete run rather
than overwriting its receipt during planning. Test planning-after-scoring and
zero-score-after-scoring, not just fresh empty destinations.

### 2. Medium: comparison validation does not recheck the selected context ledger for legacy runs

**Location:** [selected_aggregates and validate_comparison_inputs](../../src/eo_integrity.py),
lines 125–130 and 228–274.

Merge-time validation checks the current `contexts.json` against the selected
hash. Comparison-time validation compares the saved selection dictionary and
checks run/aggregate receipts, but does not repeat that ledger hash check. New
population-bound runs can catch this through `validate_run`; the held legacy
runs have no such binding.

**Reproduced:** after building a valid ten-model temporary merge from legacy-style
runs, changing the context ledger's window definition without changing the
selection dictionary was accepted by `validate_comparison_inputs`. The actual
ledger hash differed from `selection.contexts_sha256`.

**Correction:** validate the selection's current context file/hash at comparison
entry, regardless of whether individual runs predate population binding. Keep
legacy limitations explicit. This concerns a changed experiment input, not a
reason to discard scientifically usable partial observations.

### 3. Medium: the new input manifest is tied to one machine's absolute paths

**Location:** [input_population](../../src/eo_integrity.py), lines 25–29;
[validate_run](../../src/eo_integrity.py), lines 53–59.

The fingerprint includes absolute paths to both ledgers, and validation opens
those old paths even when supplied a different restored project root. Identical
data moved to another directory or machine get different identities or fail
validation.

**Reproduced:** a completed temporary run passed validation; a byte-identical
copy restored under a new root failed with `FileNotFoundError` for the original
`jobs.json` after the original temporary directory was removed. No provider file
or production artifact was moved.

**Correction:** use stable logical/relative locations and content hashes, with
an explicit resolver for genuinely external archives. Normalize both sides of
run-path comparisons; the current aggregate check also compares an unresolved
source parent with a resolved selected path, which rejects equivalent symlink
aliases. Moving bytes must not imply a scientific input change.

### 4. Medium: a relative output path bypasses partial/full destination separation

**Location:** [script 117](../../scripts/117_finalize_selected_eo_runs.py), lines 28–36.

The `--available-only` safeguard compares an unnormalized `Path` directly with an
absolute reserved destination. Supplying the relative spelling
`--out results/eo_catchment_representations/selected/census` therefore leaves that
same complete-result destination selected rather than routing to `available`.

**Reproduced:** a temporary invocation with a captured merge function received
the reserved relative destination unchanged. This proved the routing bypass;
it did not overwrite any production directory. A partial manifest would still
be rejected by a later complete-only comparison, but a complete handoff could
be displaced unnecessarily.

**Correction:** resolve/normalize output paths before enforcing destination
separation; test relative, absolute and symlink-equivalent spellings. Continue
allowing explicitly labelled completed-model subsets to proceed.

### 5. Medium: unrelated finalization edits invalidate corrected extraction runs

**Location:** [script 118 fingerprint](../../scripts/118_extract_versioned_eo_sequences.py),
lines 62–68; [validate_run code checks](../../src/eo_integrity.py), lines 49–51.

The extractor uses `input_population` from `eo_integrity.py` but fingerprints the
entire module, including selected-run merging and result validation. A fix to
an unrelated merge/path check consequently changes the extraction identity and
causes existing corrected runs to fail the current-source check, even if their
inputs, encoder and numeric output are unchanged. This dependency is present in
the actual corrected Galileo smoke manifest, not merely a hypothetical schema.

**Correction:** separate the stable extraction-population builder from output
publication/validation code. Retain historical source snapshots and receipts;
distinguish a changed numerical dependency from an unrelated downstream edit.
Do not turn every maintenance edit into a requirement to recompute embeddings.
The active legacy runs do not fingerprint this new helper and are unaffected by
this particular coupling.

## What passed and what remains scientifically unchanged

- Maintained suite: **261 tests passed in 42.70 seconds**. Ruff lint and formatting
  pass; 146 Python files are formatted. Passing tests do not cover the newly
  reproduced conditions above.
- Selected-run readiness still verifies the eight completed aggregates. Presto
  extraction is now complete and its aggregation is pending; Galileo aggregation
  is also pending. These are execution stages, not new scientific failures.
- The full S2 date census remains complete: 8,538 pairs, zero errors. Its
  area-window masking losses describe coverage, not model-score effects. The
  same-day loader remains an implemented, real-imagery-smoke-tested correction;
  full corrected embeddings and final ten-model comparisons remain unexecuted.
- No new chronological-leakage or estimator change was identified in the checked
  retrieval/control paths. The claim remains retrospective analogue usefulness,
  not historical warning skill, observed inundation or an operational forecast.

The useful next correction pass is publication isolation, a shared portable
selection validator and a smaller extraction fingerprint dependency. No new
research branch, model, data request or blanket stop is warranted. Existing
model completion and other chapter work can continue concurrently.

[Compact evidence receipt](limburg-eo-second-audit-checks-2026-10-21.json) records
source hashes, test outcomes, current readiness and reproduction results.
Detailed local evidence is in `logs/eo-second-audit-2026-10-21/`; tests used
only temporary fixtures, with held inputs read for the real comparison writer.
