# Limburg: saved four-step continuation plan

17 November 2026. Brian approved saving all four steps and executing **Step 1**.
This remains the current DISE-inspired daily-reconstruction direction. Brian
writes dissertation prose. No new model family, dataset requirement or mandatory
positive-result condition is introduced.

1. **Finish the capacity check.** Give every arm/policy the same 3,000-tree
   maximum, refit capped tuning jobs from scratch, reselect on validation data
   and refit affected final ensembles. Preserve the original benchmark.
2. **Run the agreed multi-year and river-group tests.** Local verification is
   2021–2025; external verification is 2021–2024. Retain the full eligible census,
   fixed spatial strata, common models, chronology and grouped withholding.
3. **Establish whether the finding repeats.** Examine benefits and harms across
   years/rivers and the largest flows. Use paired uncertainty respecting shared
   storms and nested gauges. Keep all-day and high-water evidence distinct.
4. **Consolidate chapter evidence.** Prepare tables, figures, event examples and
   limitations for Brian to write up. Do not translate average reconstruction
   gains into untested high-water or operational-warning claims.

Machine-readable status: `config/limburg_dise_four_step_plan_v1.json`. **Step 1
completed on 17 November 2026**; Steps 2–4 are saved as pending.
[Step 1 results and verification](limburg-dise-capacity-check-2026-11-17.md).

## Step 1 execution specification

- New configuration: `config/limburg_dise_capacity_v1.json`; new outputs under
  `results/limburg_dise_capacity_v1/`. Original 1,500-tree results are immutable.
- The same four candidates, four inner folds, two selection policies, eight
  arm/policy combinations and three final seeds remain. Rows, weights, variable
  definitions, split dates, external withholding and p99 evaluator thresholds
  are unchanged. No new test-dependent tuning criterion is used.
- All 26 capped tuning fits receive fresh fits with the 3,000-tree maximum.
  The other 102 fits already stopped before 1,500. Before reuse, verify source
  identities/runtime and rerun one fixed early-stopped control at 3,000. Its
  stopping iteration/rounds and predictions must match. If not, refit all 128
  tuning jobs under the new maximum; do not stop the research or assume reuse.
- Reuse is a computational shortcut under an identical maximum-budget rule for
  all arms. The control is fixed as primary H, candidate 1, inner fold 0. It is
  chosen without test performance. It is not an extra model candidate.
- Reselect exclusively from validation metrics. Refit three final seeds only
  where selected parameters or tree count change; otherwise verify/reuse the
  original seed models and predictions. Preserve provenance for every reuse.
- Keep raw GEOGLOWS and FDC references fixed. Rescore the exact same test rows
  with the existing evaluator; retain original and expanded-budget estimates.
- Report remaining cap hits, selection changes, affected ensembles, runtime and
  paired result changes. A remaining cap hit is disclosed; this step does not
  automatically escalate the cap again or require an AlphaEarth improvement.
- One worker/two CPU threads; 50-GiB free-disk reserve; no GPU/cloud job. Individual
  fit checkpoints support resumption with verified identical inputs/code.

No additional data download or other-chapter change is needed for Step 1.
