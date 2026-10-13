# Basin-Aware AI for Cross-Border High-Water Assessment

Research question:

> **Can basin-aware AI produce reliable cross-border high-water assessments
> from fragmented Dutch and German data?**

The chapter tests whether explicit river structure, measurement provenance and
historical event representations improve source-grounded AI assessments. It is
a retrospective evaluation of evidence use. It is not an automatic warning
system, an operational forecast evaluation or a model leaderboard.

The repository name `chapter1-co2` is historical. CO2, case-crossover,
cross-tributary prediction and pressure diagnostics are preserved under
`archive/retired-directions/2026-retrospective-high-water/`; they are not the
active chapter design.

## Read first

| document | role |
| --- | --- |
| `docs/limburg-basin-ai-active-design-2026-10-11.md` | canonical question, comparisons, policy experiment and scope |
| `docs/limburg-foundation-download-readiness-2026-10-11.md` | fixed TTM-R2 and AlphaEarth implementation contract |
| `docs/limburg-representation-feasibility-2026-10-11.md` | empirical sample and representation feasibility |
| `docs/limburg-basin-ai-literature-refresh-2026-10-12.md` | targeted literature update and bounded improvements |
| `docs/reviews/limburg-scientific-readiness-audit-2026-10-13.md` | final construct, comparison, inference and claim audit |
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
python scripts/63_build_basin_ai_pilot.py
python scripts/64_build_basin_ai_event_library.py
python scripts/65_hydrological_analogue_baseline.py
python scripts/66_download_limburg_foundation_assets.py
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
