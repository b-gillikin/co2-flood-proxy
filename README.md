# Basin-Aware AI for Historical High-Water Analogues

Research question:

> **Can basin-aware AI find useful past high-water events across Limburg's
> Dutch and German tributaries, and identify when the evidence is too
> uncertain to use?**

The chapter compares conventional hydrological summaries, raw hydrograph
similarity, a frozen time-series foundation-model representation and bounded
AlphaEarth catchment context. It reviews whether river identity and measurement
provenance make retrieved analogues usable. It is a retrospective archive
study, not an automatic warning system or operational forecast evaluation.

The repository name `chapter1-co2` is historical. CO2, case-crossover,
cross-tributary prediction and pressure diagnostics are preserved under
`archive/retired-directions/2026-retrospective-high-water/`; they are not the
active chapter design.

## Read first

| document | role |
| --- | --- |
| [Evidence index](docs/limburg-analogue-evidence-index-2026-10-14.md) | main evidence, useful controls and superseded development stages |
| [Active design](docs/limburg-historical-analogue-active-design-2026-10-13.md) | question, comparison and scope; dated development sections preserved |
| [Expanded event pass](docs/limburg-expanded-event-pass-2026-10-13.md) | main temporal census and short/no-archive coverage |
| [Information review](docs/limburg-analogue-information-review-2026-10-14.md) | generic-archive references and event interpretation |
| [AlphaEarth review](docs/limburg-alphaearth-detailed-review-2026-10-14.md) | main matched spatial-context evidence |
| [Literature bridge](docs/limburg-analogue-literature-bridge-2026-10-13.md) | event-similarity and cross-border foundation |
| [Inventory](docs/analysis-inventory.md) | code, dependencies and supporting work |
| [Handoff](docs/HANDOFF.md) | current state followed by historical execution ledger |
| `docs/data-requests.md`, `docs/decisions.md` | provider status and append-only design history |

Earlier execution notes and controls are indexed separately rather than
presented as equally current main findings. Numerical outputs remain local;
no raw provider data is published.

## Reproduction chain

The commands below preserve the upstream dependency chain. They are not a
list of separate active experiments. For analysis and interpretation, use the
evidence index to start with scripts 81–83 and their existing held inputs;
rerun upstream stages only when rebuilding or checking provenance.

```bash
conda env create -f environment.yml
conda activate chapter1-co2

python scripts/39_delineate_catchments.py
python scripts/46_review_events.py
python scripts/64_build_basin_ai_event_library.py
python scripts/65_hydrological_analogue_baseline.py
python scripts/66_download_limburg_foundation_assets.py
python scripts/68_import_alphaearth_embeddings.py
python scripts/69_raw_hydrograph_analogue_baseline.py
```

With the pinned foundation environment/source installed as described in the
Steps 3–5 execution note:

```bash
python scripts/70_ttm_analogue_comparison.py
python scripts/71_alphaearth_analogue_increment.py
python scripts/72_german_wurm_analogue_extension.py
python scripts/73_analogue_uncertainty_review.py
python scripts/74_review_analogue_census.py
python scripts/75_strengthen_foundation_representations.py
python scripts/77_plot_representation_checks.py
python scripts/78_cross_river_analogue_checks.py
python scripts/79_audit_analogue_consistency.py
python scripts/80_prepare_event_interpretation.py
python scripts/81_run_expanded_event_analogues.py
python scripts/82_review_analogue_information.py
python scripts/83_review_alphaearth_event_information.py
```

The event-library default is the fixed 512-hour assessment history required by
TTM-R2, followed by 72 withheld hours. AlphaEarth export is an authenticated
Earth Engine step documented in the download-readiness note.
The separate metric-grid QA table is retrieved with
`python scripts/76_check_alphaearth_metric_grid.py --download`; the original
export remains preserved. The latest checks note documents the tested
representation variations and keeps them separate from the original run.
The cross-river checks use other physical rivers as donors, compare fixed
3/5/10-storm neighborhoods, and test matched conventional/raw and
conventional/TTM fusion. See
`docs/limburg-cross-river-checks-2026-10-13.md` for interpretation boundaries.
The pre-interpretation audit is in
`docs/limburg-consistency-audit-2026-10-13.md`; it independently checks event
windows, representations, identities, candidate pools and response metrics.
`docs/limburg-event-interpretation-readiness-2026-10-13.md` documents the
broader Q-only inputs, explicit reference measures and blank event-review
packet. Script 81 runs the expanded Q-only census and writes a local event
browser, phase evidence, paired intervals and explicit unavailable-archive rows.
See `docs/limburg-expanded-event-pass-2026-10-13.md` for the resulting evidence.

The information and policy interpretation is in
`docs/limburg-analogue-information-review-2026-10-14.md`: generic-archive
reference checks, actual benefit/failure cases and separately attributed AI
notes. Independent human review fields remain untouched.

AlphaEarth’s detailed matched review is in
`docs/limburg-alphaearth-detailed-review-2026-10-14.md`: donor replacements,
area/identity/static controls and geographic context alongside strengthened TTM.

## Verify

```bash
python -m pytest -q
ruff check .
ruff format --check .
```

Historical code is retained for reproducibility but excluded from live lint
and tests.
