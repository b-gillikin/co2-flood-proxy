# Regional gauge/model correspondence: resolution and explicit strata

16 November 2026. Internal evidence record, not dissertation prose. This completes
the requested spatial review without selecting matches from discharge errors or
requiring every uncertain source record to become unambiguous.

## Result

Of the original **44 flags**:

| Disposition | Records | Treatment |
| --- | ---: | --- |
| Directional footprint difference | 23 | Keep the global reach as an explicitly coarser/contained footprint proxy; report its stratum. This is not exact gauge equivalence. |
| Mixed partial overlap | 9 | Retain and report the partial-overlap stratum. |
| Conflicting station/reference location | 7 | Preserve the source conflict; geometry does not identify which source is wrong. |
| Minimal/disjoint footprint with no large station/reference offset | 4 | Preserve the unresolved correspondence and report separately. |
| Original search-boundary case | 1 | Resolve to a high-overlap proxy through the bounded extension below; acquire its missing inputs. |

The wider station/reference check identified **eight additional large location
conflicts** outside the original overlap-only flags. All original flags and these
eight cases were inspected in a seven-page, 52-case geometry atlas. The maps show
provided station points, reference catchments, reconstructed global upstream
footprints and nearby model stream segments, without discharge outcomes or a
basemap-based assertion of river-name identity.

No existing matched river ID, observation, coordinate or reference polygon was
silently changed. The full matched pool expands from **386 to 387 gauges**,
comprising **337 provisional donors and 50 reserved external records**. The new
gauge shares an existing global reach, so the pool still uses **371 distinct
model reaches**. The original donor/external section grouping and the four
local-connected exclusions are retained. Neither gauge count nor section count
is a count of independent river systems.

## The search-boundary correction

`DEA13500`, Seidfeld3 / Settmecke, had no segment within the original 2-km
search. Its nearest global stream is only **2,089.7 m** away. That is an initial
search-limit result, not proof that the model has no relevant coverage.

For this single case, evaluate **every segment within 5 km** (nine candidates)
using the same ordering as the original method: largest upstream-polygon Dice,
then smallest point-to-stream distance. The chosen reach, **230292043**, is
**2,355.2 m** from the provided station point, with **Dice 0.9562**, reference
coverage 0.9320 and model-footprint purity 0.9817. It is not the nearest line.
This reach is already used by `DEA13210` and has the existing topology group
`DEA10520`; the new record remains in that same group, not a new independent
replicate. The source point remains approximately 985 m outside the reference
polygon. This is a high-overlap proxy, not independent validation of exact gauge
identity, management or measurement quality.

The spatial decision was saved **before** opening the new discharge record.
The one-gauge supplement has all matching model, weather, 2017 AlphaEarth and
conventional-control inputs, plus **2,556 complete observed days during
2018–2024**. Its source delivery and receipts remain separate. Original files,
registers and 386-record completion receipts remain unchanged.

The 5-km extension applies only to the original no-candidate case. It is not a
new rule forcing all gauges to accept the nearest stream, a search chosen from
model skill, or a relaxation of a scientific validity threshold.

## Executable analysis strata

The resolved register supplies these overlap groups across the full pool:

| Overlap description | Gauges |
| --- | ---: |
| High-overlap proxy | 344 |
| Reference mostly inside a larger model footprint | 24 |
| Model mostly inside a larger reference footprint | 1 |
| Mixed partial overlap | 9 |
| Minimal/disjoint footprints | 9 |
| **Full mapped census** | **387** |

Location evidence is separate: 364 points are on/within 100 m of their reference
footprints, eight are 100–1,000 m away, and 15 are farther than 1 km away.
The overlap and location axes intersect; do not add their counts as if disjoint.

The machine-readable views retain **all 387** for the full proxy-correction
census, **344** for a high-overlap sensitivity, and **331** for a high-overlap,
location-consistent sensitivity. **19** records have minimal overlap and/or a
large location conflict; this is a severe mapping-stress view, not every case
with any footprint difference. These views do not assign measurement quality.

For the regional comparison:

- Freeze correspondence and views before fitting. Report identical eligible
  gauge/day populations across feature arms within each view.
- Report the full-census contrast and the overlap/location strata; do not replace
  an unfavourable full result with the smaller sensitivity population.
- Distinguish improvement at a plausible matching footprint from correction of
  an imperfect global proxy. An aggregate result does not establish that the
  severe spatial conflicts are valid same-catchment pairs.
- Keep observation coverage and provider QA separate. A high-overlap footprint
  is not proof that a discharge value, peak or rating relation is verified.
- Keep grouped withholding and resampling: several gauges sharing a model reach
  or nested section do not create independent generalization tests.

The numeric bands are **descriptive reporting conventions**, not validated
uncertainty limits or automatic exclusions: retain the earlier Dice 0.8 screen;
Dice below 0.1 identifies very little shared footprint; directional coverage
of 0.9 identifies nearly complete containment. The 100-m and 1-km distance bands
make the scale of station/reference disagreement visible. They do not establish
provider coordinate-error tolerances. Continuous overlap, distance, area ratios
and candidate margins remain in the register. No band was chosen from a
favourable encoder result, and no new model/loss/threshold tournament is added.

## Source and geometry checks

The polygon/network join is **LINKNO**, which joins all 45,338 source polygons
one-to-one to the routed stream network. The `TDXHydroLinkNo` field retains
original component identifiers; 17,262 differ from the routed IDs and are absent
from that network. Replacing the join with that original-component field would
be incorrect. Every selected incremental polygon touches its corresponding
stream geometry. Recomputed flagged upstream footprints reproduce the original
overlap metrics. This resolves the identifier/join concern; it does not certify
source delineation or gauge placement.

Reconstructed upstream-polygon area and the stream's reported outlet area remain
separate diagnostics. Their ratios are retained; source aggregation/segment
representation can make them differ. We did not force one to equal the other,
rescale observed Q from an assumed corrected area, or infer which source is
wrong from model performance.

[GEOGLOWS guidance](https://training.geoglows.org/rfs/tutorials/find-river-numbers/)
explicitly treats automated snapping as imperfect and recommends checking
upstream area and other evidence. The
[CAMELS-DE-1h primary source](https://essd.copernicus.org/preprints/essd-2026-289/)
provides the station/catchment records. Our disagreement strata are derived
from those held records; no source claims all our cross-product pairs are
validated. The retained primary-source QA qualifications continue to apply.

## Artifacts, checks and next work

Resolved registers, candidate evidence, views and atlas:
`results/limburg_dise_v2/spatial_review_v1/`.
Current matched input tables (model, weather, embedding, controls, observations):
`results/limburg_dise_v2/regional_inputs_resolved_v1/`.

The matched model and weather tables each have **1,272,069 gauge-days** over
2017–2025; embedding/control tables each have 387 rows. The combined observation
table preserves missingness and unknown QA, with **823,956 complete observed
days in 2018–2024**. Raw observations outside the common predictor period remain
in their original per-source archives. Regional 2025 labels remain unavailable;
2025 predictors must not be treated as creating verification observations.

The [final receipt](reviews/limburg-dise-spatial-resolution-2026-11-16.json)
pins original and supplementary input hashes, output hashes, code, counts and
unchanged original matches. **46 tests pass**, including retention of difficult
cases, explicit missing/unknown classifications, role boundaries and independent
location sensitivity. All seven atlas pages were visually inspected.

No new regional model fit, Azure action or other-chapter change occurred. No new
provider response is required to continue with explicit uncertainty strata.
Next: assemble the common regional feature table and benchmark the actual
regional training size before the full comparison. Spatial uncertainty remains
an interpretive limitation, not a blanket stop.
