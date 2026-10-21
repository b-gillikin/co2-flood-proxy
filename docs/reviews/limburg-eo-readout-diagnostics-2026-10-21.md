# Why snapshot and weekly coverage differ; conventional-reference comparisons

Internal research-aid note. This completes the two requested tasks without model
scoring, a changed research question, new imagery or changes to active extraction.

## Coverage explanation

Script 113 joins every held observation's snapshot and four-week slots to the
source inventory, observed-pixel audit and completed encoder coverage. It retains
both the high-water and rainfall-episode populations, country, gauge, assessment
year and existing scoring flags. The table concerns the 851 existing baseline-
eligible high-water events; no new event selection is introduced.

Every weekly-available high-water event in these eight models also has a snapshot.
That is a finding about this held inventory, not a necessary calendar relationship.

| Model | Snapshot | Weekly | Lost events | Missing source week | Week with no valid catchment pixels | Encoder/sequence support loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prithvi | 637 | 211 | 426 | 184 | 228 | 14 |
| CROMA | 576 | 243 | 333 | 333 | 0 | 0 |
| TerraMind | 485 | 281 | 204 | 78 | 109 | 17 |
| DOFA | 485 | 281 | 204 | 78 | 109 | 17 |
| Copernicus-FM | 485 | 281 | 204 | 78 | 109 | 17 |
| SatMAE | 485 | 269 | 216 | 78 | 109 | 29 |
| AnySat | 485 | 270 | 215 | 78 | 109 | 28 |
| OlmoEarth, corrected | 576 | 243 | 333 | 333 | 0 | 0 |

These are exact paired losses: snapshot available, weekly unavailable. Reasons
are assigned in order: incomplete local files, missing catalogue source, no valid
catchment pixels, then encoder support. A context can have different problems in
different slots; the full per-slot reason list is retained, so this summary does
not imply the causes are mutually exclusive at pixel level. No context was lost
because a planned local file or S2 companion file was missing.

“Missing source” means no relevant planned tile for that catchment/window from
the held acquisition catalogue. It does not assert that no imagery could exist
in another orbit, sensor, archive or acquisition strategy. Because the lost cases
already have usable monthly imagery, their loss cannot all be attributed to a
sensor not yet existing. For the lost radar cases the median number of missing
source weeks is two of four. Weekly acquisition cadence is therefore a major
limitation even without optical cloud screening.

“No valid pixels” means imagery was planned and local, but the source audit found
zero valid catchment area in a required week. The retained composite masks do
not identify a cloud-specific causal share: quality, nodata and other validity
rules are included. “Encoder support loss” means some raw catchment area exists
in every slot but the fixed extraction/aggregation rules cannot construct a
complete supported representation; it is not a claim of an inference exception.
Patch layout, common tile sequences and native masks matter. No new cutoff is
introduced to hide these losses.

Losses are geographically uneven. For the three shared S2/224-pixel routes,
33 snapshot-available DE events and 171 NL events lose weekly availability:
24 DE / 54 NL missing-source cases, 5 DE / 104 NL zero-valid-pixel cases and
4 DE / 13 NL support cases. The stratified artifact records each gauge and year
as well as country. Country must not be interpreted as a causal explanation
independent of tributary, period and acquisition geometry.

The monthly composite offers a longer opportunity to obtain usable support;
the weekly sequence requires four separate supported windows. The windows also
have different month/week boundaries. These results justify keeping the readouts
separate and matching query/donor populations for any temporal-benefit claim.
They do not establish that either readout or model predicts/explains events better.
No automatic wider-window substitution or new acquisition is added.

## Direct comparison against conventional rainfall/discharge

Script 102 now calculates paired differences against **both TTM/state and the
conventional arm when present**. Conventional remains restricted to the existing
rainfall-matched population. All arms in a comparison retain the same cohort,
query-country stratum, donor policy, river restriction, measurement policy and
five/ten target donor count. The existing pairing additionally requires equal
actual donor counts for each paired event.

The calculation reuses the established storm-group and storm-year cluster
intervals. Differences remain challenger minus reference in each metric's units;
interpret direction according to the metric. An interval is left undefined with
fewer than two independent clusters. Missing conventional arms do not silently
fall back to a different reference, and TTM-reference results remain available.
No new representation or EO-plus-rain arm is introduced. These contrasts compare
the existing candidate systems; they do not isolate a causal incremental EO
feature effect conditional on an otherwise identical conventional model.

This changes the runner, not the empirical findings: no scientific scoring run
was launched. Future claims against rainfall/discharge can now use the direct
paired contrast rather than an indirect comparison through TTM.

## Validation and provenance

Four new tests use the existing real pairing function to verify conventional and
TTM reference differences, removal of unequal-donor-count pairs, absent rainfall
controls, undefined one-cluster intervals and routing to both cluster units.
They also verify reason classification and reject an encoded context that
contradicts raw slot support. Together with the existing EO event and coverage
checks, 18 tests pass. The inherited PROJ data-directory warning occurs on
import; these checks pass without changing any environment or active worker.
Lint and whitespace checks pass.

Local outputs: `results/eo_readout_coverage_diagnostics/` contains observation and
window reasons, gauge/country/year summaries, exact paired readout memberships,
high-water reason counts and a hashed manifest. Raw data and large outputs stay
outside Git. The compact receipt beside this note preserves the summary and
input/output hashes. Source masks cannot answer a cloud-specific attribution;
that limitation is recorded rather than inferred away.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venvs-eo/terramind/bin/python scripts/113_explain_eo_readout_coverage.py
.venv-foundation/bin/python -m pytest tests/test_eo_readout_and_pairing.py tests/test_eo_event_inputs.py tests/test_eo_coverage_review.py -q
```
