# Kill-check and pre-registration pattern

The execution plan should include explicit decision points where the user pauses, runs a defined check, and either proceeds with the plan or redirects. Designing these into the schedule up front protects against sunk-cost continuation.

## What a kill-check is

A kill-check is a decision point with:

- A specific empirical criterion (a number, a comparison, a binary outcome)
- A defined decision rule (proceed / pause / redirect)
- A scheduled position in the timeline
- A short reasoning paragraph attached if the decision goes against expectations

Without these, projects accumulate momentum and become hard to redirect — the most expensive kind of methodological failure in a PhD.

## Where to place kill-checks

Typically one or two per month in a sprint schedule:

- **End of Month 1** (foundation): does the empirical foundation hold? If not, what reframing is required?
- **Mid Month 2** (modeling): are the methods producing interpretable, defensible outputs? If not, simpler alternatives.
- **End of Month 3** (transfer / external validation): do the headline results hold up against the baselines?

For shorter chapters, fewer kill-checks. For longer chapters, a kill-check per major decision.

## Pre-registration discipline

For any chapter with a hypothesis-test character — especially transfer experiments, cross-validation, comparative method studies — pre-register the test specification before inspecting the outcome data.

Pre-registration document should specify:

- The data (what's in scope, what's excluded, the windows)
- The experiment procedure (training, deployment, evaluation steps)
- The success criterion (what counts as a positive result)
- The baselines that have to be beaten
- The statistical test
- What constitutes a null / negative result

Commit the pre-registration to git so the timestamp is verifiable. Cite it in the methods chapter.

## Pattern for writing kill-checks in the execution plan

Each kill-check entry should have:

```
KILL CHECK [n]: [name]
  Criterion: [specific, measurable]
  Rule: 
    [outcome A] → proceed as planned
    [outcome B] → pause; document; consult supervisor
    [outcome C] → redirect framing toward [alternative]
  Compare to: [external benchmark if applicable]
  Output: decision recorded in decisions log
```

## Example

```
KILL CHECK 1: Is there residual hydrological signal in CO2?
  Criterion: R² of CO2 ~ pressure + pressure-tendency regression
  Rule:
    R² ≤ 0.85 → proceed as planned
    0.85 < R² ≤ 0.95 → proceed with caution; document
    R² > 0.95 → redirect (chapter becomes barometric-decomposition
                 methods paper, not hydrological-signal paper)
  Compare to: Wrona 2025 reports R² ≈ 0.67 for pressure tendency
              vs. CO2 in closed Polish shaft.
  Output: decision recorded in docs/decisions.md
```

The criterion is specific and measurable. The decision rule is explicit. The comparison to external work gives a sanity-check anchor. The output is documented for later defense.

## Honest framing

The chapter is structured to survive failed kill-checks via narrative repositioning, not by hiding them. A negative result with a clear analysis of why is more valuable than a positive result with hand-waving. Examiners reward methodological honesty more than they reward clean stories.
