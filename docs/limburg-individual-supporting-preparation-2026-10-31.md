# Supporting analyses: preparation, 31 October 2026

Prepared alongside the current individual-encoder queue, without changing its code, source hashes, worker allocation or inputs. No new fit, extraction or acquisition was launched. The four work contracts below are **specified/prepared, not executed analyses**. They follow the [existing design](limburg-ten-individual-experiments-plan-2026-10-29.md); they add no research question or model.

## Held inputs and reproducibility

Run `.venv-foundation/bin/python scripts/175_prepare_supporting_analyses.py` from the chapter directory. It verifies all 204 monthly soil/snow files against their receipts and freezes the saved combined-profile definitions, global source-hour clock and block-mask checksums. Output: [prepared contracts and hashes](../config/limburg_individual_supporting_prepared_2026_10_31.json). Re-running with changed inputs requires a versioned destination. The primary queue does not consume or depend on this new file.

ERA5-Land acquisition completed on 30 October: 204/204 months, January 2009–December 2025, 50,356,653 source bytes. Three native fields are held: layer-1/layer-2 volumetric soil water (`swvl1`, `swvl2`) and snow-depth water equivalent (`sd`). Zero snow is valid. Checksums establish source integrity, not catchment aggregation or operational availability.

## Work ready to schedule after primary review

| Supporting analysis | Prepared now | Implementation still required before fitting |
|---|---|---|
| Shared soil/snow control | Complete sources/receipts and tested strict-prior-hour join | Area-weight native grid cells to held catchment polygons; retain spatial/missing coverage; join earlier states to each issue; add identical physical controls to matched raw and encoder heads; refit and audit in separate versioned outputs |
| Two combined scarcity profiles | Saved subsets/phases and missing-mask/clock hashes frozen | Rebuild allowed context **and conventional references** under each realization; refit chronological heads on the same scenario, with shared year/mask inference. No frozen-head distribution-shift replay |
| C+E attribution | Explicit arm contract, distinct from main equal-input comparison | Keep allowed common context/C baseline and chronological tuning; omit model-specific raw descriptors only; retain zero encoder choice and matched support. Do not interpret this as primary evidence of encoder value |
| SatMAE SR/TOA product sensitivity | Existing product-and-support interpretation retained | Inventory matched acquisitions/bands/patches; use checkpoint-specific normalization and exact raw-input parity; score common support separately. Unmatched subtraction cannot isolate radiometry |

The network/schedule profile enumerates 70 four-of-eight tributary subsets × six saved phases = 420 combinations. The network/block profile retains 100 saved network/missingness realizations and its saved 12h/50% mask. Both exclude Maas feeds. Use the global source-hour indexing for training and evaluation, and never redraw masks inside a year/fold. DOFA keeps watercourse exclusions, including grouped Wurm/Worm sites. This is materially more fitting than the three primary regimes; estimate resources before scheduling and retain current 50-GiB reserve.

`src/eo_supporting_controls.py` supplies the strict-prior-hour state join and exact saved-profile selection. It preserves missing requested hours instead of carrying old state silently. Four fixture tests cover future/issue-hour exclusion, zero snow, missing hours, duplicate source times and missing profile definitions. It is a preparation helper, **not** the completed geospatial wrangler or fit runner.

## Interpretation and release sequence

Finish/review Presto and Galileo, consolidate all ten primary results, then implement the supporting runners without changing completed primary outputs. Keep the same full eligible census, uncertainty/dependence accounting and coverage ledger. Document preparation and modeling changes before reading supporting outcomes. No claim of a pristine holdout or preregistration: the research direction developed after earlier results.

Reanalysis timestamps are not release timestamps. The soil/snow control tests retrospective physical context, not as-issued forecast access. ERA5 soil moisture must not substitute for Galileo's unsupported TerraClimate soil-water channel. A supporting positive result cannot erase negative primary or historical retrieval evidence.

## Validation of this preparation

19 targeted helper/acquisition tests pass; Ruff and whitespace checks pass. The existing optional NetCDF fixture emits the previously documented NumPy/binary-size warning; it still passes. All live queue source hashes remain unchanged. Completed fit outputs and their recorded source hashes were verified while building the partial snapshot.
