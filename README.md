# Pre-High-Water Signal Recurrence and Spatial Transferability

Prospective research question:

> Across Limburg tributaries, which public hydrometeorological signals recur
> during the 72 hours before independently defined high-water onset, and do
> those signals remain detectable at unseen watercourses and periods? At
> Kerkrade, does pressure-adjusted CO2 recur as a local manifestation of that
> regional state?

Status: **data-gated; no new chapter result exists**. The current repository
does not contain the original 2020–2021 IoT package, the contracted long
tributary record, catchment-average RADOLAN series or a frozen long-record
public-weather assignment. The prospective protocol therefore remains unlocked
and the outcome analysis has not been run.

## Read first

| document | role |
| --- | --- |
| `docs/chapter-synthesis.md` | canonical question, contribution, design and current status |
| `docs/chapter-scope-and-preregistration.md` | draft estimator protocol; lock only after gates and supervisor approval |
| `docs/analysis-inventory.md` | prospective, secondary and stopped analyses |
| `docs/data-requests.md` | exact blockers and delivery contracts |
| `docs/predecessor-notes.md` | Viefhues and Eryilmaz source notes |
| `docs/HANDOFF.md` | session state only |

The intended sequence is Viefhues MSc -> Eryilmaz paper -> this chapter:
single-event observation -> same-site public-signal explanation -> recurrence
and spatial transfer.

## Audit the hard gates

```bash
conda env create -f environment.yml
conda activate chapter1-co2
python scripts/31_event_study_gates.py --report-only
```

`--report-only` writes `results/event_study/gate_audit.{csv,md}` while allowing
the known failure. Omit it for the binding gate: a failed audit exits nonzero.
Do not point the audit at the rolling two-year files.

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

## Verify

```bash
python -m pytest -q
ruff check .
ruff format --check .
```

## Conventions

- Hourly UTC; missing hours remain missing and crossings never bridge gaps.
- One pre-declared representative per natural watercourse.
- RADOLAN catchment averages are primary; point rainfall is sensitivity only.
- Receiver flow defines high-water onset and is not a candidate signal.
- Thresholds, scaling and pressure adjustment exclude held-out periods.
- Derive held-out signal directions from other watercourses and periods only.
- Aggregate events within watercourse before describing the network.
- No operational, causal, FEWS or monitoring-placement claim.
