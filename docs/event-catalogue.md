# Soft-Label Event Catalogue

Task 1.4 builds discharge-derived soft labels for the Kerkrade chapter from the
Wurm/Rimburg, Geul/Hommerich, and Geul/Meerssen hourly discharge series.

## Rule Set

- Thresholds are computed separately for each discharge source from the full
  local discharge history.
- Default thresholds are p90, p95, and p99.
- Catalogue events are contiguous threshold exceedances lasting at least 6
  hours.
- Hourly labels are graded:
  - `0`: below p90
  - `1`: at or above p90
  - `2`: at or above p95
  - `3`: at or above p99
- Soft-label columns divide these levels by 3, giving values from 0 to 1.
- Antecedent labels take the maximum hourly level over 24h, 72h, and 168h
  windows.

This is intentionally a soft hydrological-state catalogue, not a hard flood
truth table.

## Outputs

- `data/processed/discharge_thresholds.csv`
- `data/processed/event_catalogue.csv`
- `data/processed/hourly_soft_labels.csv`

Run:

```bash
python scripts/03_build_event_catalogue.py
```
