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
| `docs/limburg-historical-analogue-active-design-2026-10-13.md` | canonical question, comparison, cross-border limits and scope |
| `docs/limburg-analogue-steps-3-5-2026-10-13.md` | executed representations, German extension, results and reproduction |
| `docs/limburg-analogue-step6-2026-10-13.md` | paired uncertainty, river influence, provenance and interpretation limits |
| `docs/reviews/limburg-analogue-visual-review-2026-10-13.md` | AI-assisted observations on fourteen illustrative cases; human review pending |
| `docs/limburg-basin-ai-active-design-2026-10-11.md` | superseded RAG-centered design retained as history |
| `docs/limburg-foundation-download-readiness-2026-10-11.md` | fixed TTM-R2 and AlphaEarth implementation contract |
| `docs/limburg-representation-feasibility-2026-10-11.md` | empirical sample and representation feasibility |
| `docs/limburg-basin-ai-literature-refresh-2026-10-12.md` | historical RAG literature update; no active tasks |
| `docs/limburg-analogue-literature-bridge-2026-10-13.md` | direct event-similarity and cross-border literature for current scope |
| `docs/reviews/limburg-scientific-readiness-audit-2026-10-13.md` | dated scientific audit; RAG requirements superseded |
| `docs/reviews/limburg-second-pass-2026-10-13.md` | dated audit that exposed the extra RAG scope |
| `docs/reviews/limburg-analogue-alignment-audit-2026-10-13.md` | current code, literature and documentation alignment audit |
| `docs/analysis-inventory.md` | live code, inputs and completed supporting work |
| `docs/data-requests.md` | provider deliveries and remaining source questions |
| `docs/decisions.md` | dated design history; earlier entries remain historical |
| `docs/HANDOFF.md` | concise current state and next actions |

## Active workflow

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
```

The event-library default is the fixed 512-hour assessment history required by
TTM-R2, followed by 72 withheld hours. AlphaEarth export is an authenticated
Earth Engine step documented in the download-readiness note.

## Verify

```bash
python -m pytest -q
ruff check .
ruff format --check .
```

Historical code is retained for reproducibility but excluded from live lint
and tests.
