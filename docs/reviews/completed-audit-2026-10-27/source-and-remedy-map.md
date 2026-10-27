# Audit source and remedy map

Read the main audit for the findings, their measured scope and limitations.

| Finding | Direct implementation/evidence | Remedy type |
| --- | --- | --- |
| H1: 66 rainfall exclusions | script 84 `add_rain_signatures`; script 102 `rain_ids`; audit `rain_feature_completeness` | Existing-input benchmark replay; no encoder inference |
| H2: missing matched generic whole-response reference | script 102 `arms`; script 82 generic reference; prior information memo | Downstream analysis on fixed EO cohorts |
| H3/H5: changing populations | Each `eo_event_coverage.csv`; audit JSON coverage; filtered per-arm assessment rows | Explicit support and common query/donor comparisons |
| H4: uncertainty wording | script 102 scores and script 120 review; earlier distribution analysis | Narrow claim or assess saved spread/error evidence |
| I1: wrong browser input text | script 120 `input_note` and all four supplemental HTML pages | Review-only presentation regeneration; no rescore |
| I2: transitive sources | script 84 -> 83 -> 82 -> 81/78/75/74/73/80/70/69/64 dependency chain | Future full dependency contract; dated current snapshot |
| I3: selection-map persistence | Current corrected JSON and exact copies of supplemental selection JSONs | Addressed: version compact maps |
| I4: stale entry points | README/HANDOFF versus dated historical sections | Addressed at entry points; detailed historical notes retained |

No scientific outputs were changed in this audit. The read-only evidence script
checks selected run contracts and the hashes already recorded in completed
comparison/review manifests. It is not a second independent reimplementation of
all 40-million-row donor audits or every metric, and does not claim to be one.
Existing automated donor audits and numerical tests provide that additional layer.

The complete library inventory is 91 entries, with relevance roles recorded in
JSON. No generated bibliography was hand-edited and no Mendeley filing or Overleaf
sync is implied by this review. New useful sources are linked in the audit; the
pooling v2 PDF is locally saved with its source/hash receipt.
