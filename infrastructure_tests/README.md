# Infrastructure checks

These tests protect retained legacy IoT ingestion. The retired daily-summary
test is archived with its source. These checks are not part of the dissertation's scientific test surface and
are therefore excluded from the default `pytest` run.

Run them only when changing collection infrastructure:

```bash
python -m pytest infrastructure_tests -q
```

The default `python -m pytest -q` remains limited to event definitions, data
semantics and feasibility checks used by the chapter.
