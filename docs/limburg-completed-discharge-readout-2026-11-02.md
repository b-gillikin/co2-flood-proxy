# Completed discharge experiments — 2 November 2026

Internal interpretation aid; Brian writes dissertation prose.

All ten model-specific experiments and declared configuration comparisons are complete. These results concern next 24h discharge correction. Spatial mapping tests are a separate task; their results cannot be inferred here.

| Model | Local-Q-absent high-water MAE difference (mm/h) | Whole-year interval | Assessments / storms |
|---|---:|---:|---:|
| presto | -5.10551e-05 | [-0.000118909, 0] | 3001 / 309 |
| anysat | -3.21289e-05 | [-9.7645e-05, 6.05994e-06] | 3001 / 309 |
| galileo | 2.26777e-06 | [1.17389e-07, 6.06177e-06] | 3001 / 309 |
| olmoearth | 1.29201e-05 | [-5.64185e-07, 3.45277e-05] | 3001 / 309 |
| croma | 2.85676e-06 | [0, 9.26752e-06] | 3001 / 309 |
| prithvi | -9.38951e-06 | [-3.84351e-05, 4.68242e-06] | 3001 / 309 |
| copernicus_fm | 9.77334e-07 | [-1.49735e-05, 1.68721e-05] | 3001 / 309 |
| dofa | -0.000147946 | [-0.0002982, -1.71032e-06] | 3001 / 309 |
| terramind | 1.5656e-06 | [-1.53144e-05, 1.88476e-05] | 3001 / 309 |
| satmae | 7.59091e-07 | [-5.57621e-06, 7.73226e-06] | 3001 / 309 |

DOFA uses held-watercourse transfer; its rich-basin regime aliases local-Q absence. Other experiments use same-gauge annual heads. See readout.json for every model-specific design.

Negative differences favor the encoder increment over its matched raw-input correction. Assessments, sites, source years and feature support differ between model-specific tests; do not rank these point estimates as an encoder tournament.

Read effects.csv for every scenario, country, gauge, watercourse and flood stratum; read diagnostic-cases.csv for the previously selected helped/harmed cases. Uncertainty is the existing999 shared whole-year bootstrap conditional on fitted procedures. Nonfinite draws and undefined strata remain in the tables. No multiplicity-adjusted superiority claim.

Presto and Galileo complete the earlier partial evidence: neither establishes broad discharge benefit. Presto has some high-water improvements but mixed all-flow effects; Galileo is worse overall when all discharge is absent. The documented-flood evidence is sparse and often falls back identically. Consult support-specific contrasts before attributing differences to the encoder.

The applied mapping branch tests spatial outputs, label efficiency, cost and local reference agreement. Its justification is the distinct task, not an expectation that a more favorable result must appear.
