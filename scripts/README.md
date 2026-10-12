# Live scripts

The active code prepares audited basin evidence and evaluates one bounded
basin-aware AI design. Number gaps identify scripts moved to the historical
archive; they are not missing dependencies.

Scripts 25, 31–35, 37 and 39–46 preserve the acquisition, source-semantics,
catchment, rainfall, weather, rating and event-review chain. See
`docs/analysis-inventory.md` for each file's role.

```bash
python scripts/63_build_basin_ai_pilot.py
python scripts/64_build_basin_ai_event_library.py
python scripts/65_hydrological_analogue_baseline.py
python scripts/66_download_limburg_foundation_assets.py
```

Script 63 writes evidence-access prompt packets without calling an LLM. Script
64 defaults to the fixed 512-hour TTM-R2 history and 72 withheld hours. Script
65 retrieves strictly earlier events from different storms. Script 66 is a dry
run unless `--download` is supplied.

```bash
python scripts/67_export_alphaearth_embeddings.py --project YOUR_EE_PROJECT
```

Raw data, weights and generated results remain outside Git; contracts,
manifests and receipts are versioned. Historical scripts and tests are under
`archive/retired-directions/2026-retrospective-high-water/` and excluded from
live lint/test discovery.
