# Full local EO coverage and acquisition-date audit — 17 October 2026

Internal evidence-workflow report, not dissertation prose or model-performance findings. The complete staged archive was audited using scripts 99 and 104. No embedding extraction, model fitting, event redefinition, new coverage cutoff or acquisition was performed.

## Integrity and chronology

- All 36,304 TIFF/receipt pairs are present locally and were SHA-256 verified during staging.
- The pixel scan verified 27,766 primary tiles, including paired 20 m inputs for Sentinel-2, and produced 14,050 window/catchment/product rows. Zero scan errors.
- All 36,304 jobs have candidate acquisition timestamps within their own requested windows. Actual observed pixel dates passed the input reader’s window checks.
- No future completed windows among 81,702 event/window links. No latest observed pixel at/after assessment in 163,715 available pixel-coverage/event-window joins. No negative mean acquisition ages.
- These establish retrospective chronology, not historical product publication availability. Composite pixels can have different dates; Sentinel-2 ages use the latest band-date surface, with original product dates retained.

## Spatial coverage where source tiles exist

These denominators exclude windows with no catalogued source tile. Fractions use the full catchment area; no renormalization to observed pixels. Full means within numerical tolerance (1e-7). Partial includes arbitrarily small observed areas.

| Product | Window/catchment rows | Zero observed | Partial | Full | Median observed area |
| --- | ---: | ---: | ---: | ---: | ---: |
| hls | 5,458 | 868 | 3,530 | 1,060 | 53.2% |
| s1_ascending | 4,256 | 0 | 12 | 4,244 | 100.0% |
| s2_10m | 4,336 | 209 | 3,378 | 749 | 75.8% |

Source-file inventory additionally retains 3,518 window/catchment/product rows without catalogued source tiles and 4,752 before the archive’s common April 2013 lower bound. Product-specific earlier mission/coverage gaps can also fall in the no-catalogue category. These are not failed downloads or proof of cloudy conditions.

## High-water event readouts

All 1,062 candidate high-water events remain in the inventory; 851 have the inherited Q-only scoring eligibility. Counts below use those 851. A supported context means **some observed catchment area in every requested slot**, not full-area observation, independent events or final encoder eligibility.

| Product | Last completed month | Twelve completed months | Four completed weeks |
| --- | ---: | ---: | ---: |
| s1_ascending | 576 | 437 | 243 |
| s2_10m | 485 | 380 | 298 |
| hls | 637 | 438 | 225 |
| Common source coverage for all ten models | 479 | 357 | 123 |

Among supported optical sequences, median weakest-slot area is 36.2% for twelve-month Sentinel-2 and 29.1% for HLS; for four-week inputs it is only 7.5% and 7.8%. Thus complete-slot counts alone materially overstate spatial completeness. SAR is near full-area where acquired, but the selected orbit does not yield an observation in every weekly bin.

The preceding-month snapshot has median area-weighted acquisition age of 19.0 days (SAR), 24.3 days (S2), and 25.4 days (HLS) among supported high-water contexts. Mean ages across twelve monthly slots are naturally much older; they must not be described as the age of the latest observation. These are antecedent-context inputs, not images of event onset.

Both NL and DE remain represented. For monthly snapshots, supported counts are SAR 433/614 NL and 143/237 DE; S2 372/614 and 113/237; HLS 468/614 and 169/237. The local site-level summary retains each catchment and readout.

## Implications for the existing comparison

1. Proceed to extraction using the existing three readouts and model-specific cohorts. The monthly snapshot supplies the broadest common support; it is not substituted for the temporal analyses.
2. Keep the all-ten intersection as an additional paired comparison: 479 snapshots, 357 twelve-month contexts and 123 four-week contexts before patch/encoder eligibility. It is not a gate on pairwise analysis.
3. Carry area fractions, missing slots and acquisition age into comparison/error interpretation. Do not silently treat tiny optical coverage as a catchment census.
4. No missing planned download needs repair and this audit does not justify an automatic new data pull. Precisely truncated recent scenes could be a targeted later addition if event-age or coverage effects warrant it.
5. Catchment polygons are held analysis inputs, not independently validated by this audit. No hydrological performance conclusion follows from coverage alone.

## Reproduction and local outputs

```sh
.venvs-eo/terramind/bin/python scripts/99_prepare_limburg_eo_comparison.py --scan-local
.venvs-eo/terramind/bin/python scripts/104_summarize_limburg_eo_coverage.py
```

The scan took approximately 40 minutes on this machine. Local, Git-ignored tables: `results/eo_comparison_preparation/{observed_window_coverage,event_model_context_coverage,window_coverage,tile_inventory}.parquet`; `manifest.json`, `pixel_scan.json` and `full_archive_audit_summary.json`. The summary includes hashes of the audit inputs; the manifest records acquisition/input hashes and the code revision. Logs: `logs/eo-full-pixel-audit-2026-10-17.log` and `logs/eo-full-pixel-summary-2026-10-17.json`. The scanner’s generic local-only scope text is retained; the staging completion receipt establishes that this run includes the full remote ledger.
