# Second-audit fixes — 2026-10-21

Implementation of the [second audit](limburg-eo-second-audit-2026-10-21.md).
The RQ, models, event populations, numerical retrieval/scoring and scientific
interpretation are unchanged. These are publication and reproducibility fixes.

| Finding | Implemented behavior |
| --- | --- |
| Stale comparison outputs | Script 102 planning writes under `<out>/planning/`, preserving any existing scientific results and their receipt. Executed runs publish from a fresh staging directory; a successful zero-score execution has `no_estimable_results` and no leftover score tables. Previous runs are retained under timestamped `.previous-*` directories. Exceptions preserve the prior published run. A manifest binds all output files to input hashes and completion status. |
| Legacy context ledger not rechecked | The same context-ledger hash validator is used at merge and comparison entry, including for legacy runs. A changed ledger cannot pass just because the saved selection dictionary is unchanged. |
| Machine-specific paths | New population identities contain project-relative or logical external-role locations and content hashes. Ordinary byte-identical project restores validate under their new root with the same population identity. External inputs and legacy absolute paths have explicit archive/preparation resolver overrides; old manifests need not be rewritten. |
| Partial/full path aliases | Script 117 resolves output paths before applying destination separation. Relative, absolute and symlink-equivalent spellings all route available-model output to the separate `available/census` destination. Aggregate source-path comparisons also normalize both sides. |
| Overly broad extraction dependency | Future extraction imports/fingerprints the small `src/eo_population.py` builder, independently of downstream integrity/publication code. Two reviewed metadata-only historical source transitions are preserved as exact snapshots and explicitly bound replacement hashes. Numerical dependencies remain checked; unknown revisions are not treated as compatible. |

## Using portable locations

No resolver is needed for normal project-contained inputs. For external archives
or a relocated old absolute-path manifest, provide the physical roots separately
from the extraction identity. An example JSON file is:

```json
{
  "archive": "/new/location/held-compact-eo",
  "preparation": "/new/location/eo-comparison-preparation"
}
```

Script 101 accepts that file through `--input-roots path/to/roots.json`. For
selected finalization/comparison, the selection map may carry an `input_roots`
object with the same keys; relative values resolve against the current project
root. Every resolved ledger must still match its recorded content hash. This
changes data location, not scientific input identity or event selection.

## Validation and scope

The maintained suite passes **273 tests in 46.47 seconds**; Ruff lint and
formatting pass (148 files). Regression coverage includes planning after scoring, a zero-score run after
scoring, failure rollback, comparison-time changes to a legacy context ledger,
byte-identical project restore, explicitly relocated external/legacy paths,
three destination-path spellings, and reviewed-versus-unknown source changes.
The real comparison writer was also exercised with held inputs and temporary
engineering outputs: old scientific receipts stayed intact during planning,
stale tables were absent after a zero-score publication, previous outputs were
retained, and all published hashes verified. No empirical model score was run.

A two-frame real-imagery Galileo smoke completed with zero errors. Its embedding,
validity mask and acquisition-day arrays were **bit-identical** to the previously
validated corrected smoke. The numerical wrapper functions have identical ASTs,
and the earlier source receipts still verify through the reviewed metadata-only
compatibility transitions. This does not claim a full corrected embedding census.

Active legacy model/aggregation processes were not restarted or edited in
memory. Encoder/input/mask source files fingerprinted by those jobs were not
changed. The maintained test/lint/format outcomes and artifact hashes are in
[the check receipt](limburg-eo-second-audit-fix-checks-2026-10-21.json).

Completed-model subsets remain usable explicitly; the fixes add no new research
branch, data request, model, preregistration requirement or blanket stop.
