# Pre-High-Water Signal Recurrence and Spatial Transferability

Prospective research question:

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and how
> does their event-minus-quiet signal change with distance from the affected
> watercourse? At
> Kerkrade, if the source data support the case, does pressure-adjusted CO2
> recur as a local manifestation of that regional state?

Status: **data-gated; no new chapter result exists**. The primary ERA5-Land
source has been approved and its fixed 2001–2025 CDS extract is being acquired.
A
validated 2001–2025 KNMI station table is held for observational sensitivity;
neither file is an event-study result. The repository still lacks the other
contracted regional inputs. A newly delivered
Viefhues source package contains a cleaned hourly 2020–2021 table, raw
May–September 2021 IoT files and the historical ABC-processing code. The
source-native K4 record is now normalised and covers every July 2021 hour;
older lineage, sensor-era metadata and later-event feasibility remain
unresolved. The protocol therefore remains unlocked and no outcome analysis
has been run.

## Read first

| document | role |
| --- | --- |
| `docs/chapter-synthesis.md` | canonical question, contribution, design and current status |
| `docs/chapter-scope-and-preregistration.md` | draft estimator protocol; lock only after gates and supervisor approval |
| `docs/analysis-inventory.md` | prospective, secondary and stopped analyses |
| `docs/data-requests.md` | exact blockers and delivery contracts |
| `docs/lanuk-feasibility.md` | reproducible decision on the held German gauge route |
| `docs/supervisor-decision-memo.md` | recorded approvals, remaining design questions and recommendations |
| `docs/student-next-actions.md` | detailed five-task student handoff and send-ready institutional requests |
| `docs/literature-source-notes.md` | source-by-source notes; no aggregate literature synthesis |
| `docs/literature-evidence-matrix.csv` | evidence-question/source relationships |
| `docs/chapter-references.bib` | verified bibliography for the retained corpus |
| `docs/HANDOFF.md` | session state only |

`chapter-prework/` retains only the two supplied predecessor PDFs and a README.
Obsolete scaffolds, generated source corpora, How-To documents and the legacy
bibliography were removed; Git history remains their archive.

The intended sequence is Viefhues MSc -> Eryilmaz paper -> this chapter:
single-event observation -> same-site public-signal explanation -> recurrence
and the spatial extent of those signals.

## Audit the hard gates

```bash
conda env create -f environment.yml
conda activate chapter1-co2
python scripts/31_event_study_gates.py --report-only
```

`--report-only` writes `results/event_study/gate_audit.{csv,md}` while allowing
the known failure. Omit it for the binding gate: a failed regional audit exits
nonzero. The conditional Kerkrade case is assessed separately when a qualifying
hydrological pair and onset evidence exist. Do not point the audit at the
rolling two-year files.

Normalize and audit the source-native Viefhues K4 record with:

```bash
python scripts/33_ingest_viefhues_iot.py
```

The separate LANUK source audit is safe to rerun before protocol lock because
it uses discharge availability and metadata only:

```bash
python scripts/32_lanuk_feasibility.py
```

It writes tidy QA tables under `results/feasibility/` and regenerates
`docs/lanuk-feasibility.md`. It does not calculate public-signal or CO2
contrasts.

## Existing predecessor check

```bash
python scripts/update_data.py --skip-download
python scripts/03_eryilmaz_replication.py
```

This re-evaluates Eryilmaz's same-site indoor-versus-public comparison on the
later sensor era. It is predecessor context, not the chapter's transfer method.
`update_data.py` refreshes only Kerkrade IoT/weather and their QC frame; network
source pulls are separate because their public rolling records do not pass the
chapter gate.

The approved primary public-weather pull is:

```bash
python scripts/34_fetch_era5_land.py
```

It needs the user's Copernicus CDS token in `~/.cdsapirc`. The validated KNMI
sensitivity is reproducible without a key:

```bash
python scripts/35_ingest_knmi_validated.py
```

## Verify

```bash
python -m pytest -q
python -m pytest infrastructure_tests -q  # only when legacy ingestion changes
ruff check .
ruff format --check .
```

## Conventions

- Hourly UTC; missing hours remain missing and crossings never bridge gaps.
- Joint-period density is audited; endpoint span cannot substitute for observed hours.
- One pre-declared representative per natural watercourse.
- RADOLAN catchment averages are primary; point rainfall is sensitivity only.
- Receiver flow defines high-water onset and is not a candidate signal.
- Thresholds, scaling and pressure adjustment exclude held-out periods.
- Estimate spatial extent from every eligible receiver-donor pair, not a chosen
  nearest donor.
- Fit one prespecified distance relationship per signal; validate its magnitude
  at held-out receiver-period intersections. The held watercourse is absent
  from training as both receiver and donor.
- Aggregate events within watercourse before describing the network.
- No operational, causal, FEWS or monitoring-placement claim.
