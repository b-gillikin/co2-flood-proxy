# Live scripts

## Evidence and execution roles

Main analysis/interpretation runners: **81–83**. Supporting controls: **75–78**;
independent audit: **79**. Scripts **70–74** are original execution/development
and **80** prepares expanded inputs. Preserve them in place because later
runners depend on their code or artifacts; they are not independent chapter
experiments to present by default. See the
[evidence index](../docs/limburg-analogue-evidence-index-2026-10-14.md).

The active code prepares audited basin evidence and evaluates one bounded
basin-aware AI design. Number gaps identify scripts moved to the historical
archive; they are not missing dependencies.

Scripts 25, 31–35, 37 and 39–46 preserve the acquisition, source-semantics,
catchment, rainfall, weather, rating and event-review chain. See
`docs/analysis-inventory.md` for each file's role.

```bash
python scripts/64_build_basin_ai_event_library.py
python scripts/65_hydrological_analogue_baseline.py
python scripts/66_download_limburg_foundation_assets.py
python scripts/68_import_alphaearth_embeddings.py
python scripts/69_raw_hydrograph_analogue_baseline.py
```

Script 63 is retained as an optional evidence-QA pilot; its four-arm RAG
comparison is no longer part of the active chapter. Script 64 defaults to the
fixed 512-hour TTM-R2 history and 72 withheld hours. Script
65 retrieves strictly earlier events from different storms. Script 66 is a dry
run unless `--download` is supplied.

Script 68 validates the held AlphaEarth table against its delivery and native
catchment geometry receipts, then joins prior-year embeddings to events.
Script 69 standardizes each eligible 512-hour discharge history, runs R1
through the same prior-storm retrieval function as R0, and writes paired
comparisons plus the existing measurement-concern sensitivity.

```bash
python scripts/67_export_alphaearth_embeddings.py --project YOUR_EE_PROJECT
```

Raw data, weights and generated results remain outside Git; contracts,
manifests and receipts are versioned. Historical scripts and tests are under
`archive/retired-directions/2026-retrospective-high-water/` and excluded from
live lint/test discovery.
