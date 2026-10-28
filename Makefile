.PHONY: test lint format-check check recovery-doctor data-inventory data-verify data-backup data-backup-dry-run data-restore recovery-check

PYTHON ?= python3
PYTHONPYCACHEPREFIX ?= /tmp/dissertation-pycache
# The foundation venv uses the existing conda runtime's projection database.
# Respect an explicit caller setting and do not hard-code this machine's path.
PROJ_DATA ?= $(shell $(PYTHON) -c "import sys; from pathlib import Path; p = Path(sys.base_prefix) / 'share/proj'; print(p if (p / 'proj.db').is_file() else '')")
export PROJ_DATA

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format-check:
	$(PYTHON) -m ruff format --check .

check: lint format-check test

recovery-doctor:
	$(PYTHON) tools/disaster_recovery.py doctor

data-inventory:
	$(PYTHON) tools/disaster_recovery.py inventory

data-verify:
	$(PYTHON) tools/disaster_recovery.py verify

data-backup:
	$(PYTHON) tools/disaster_recovery.py backup

data-backup-dry-run:
	$(PYTHON) tools/disaster_recovery.py backup --dry-run

data-restore:
	$(PYTHON) tools/disaster_recovery.py restore

recovery-check:
	PYTHONPYCACHEPREFIX=$(PYTHONPYCACHEPREFIX) $(PYTHON) -m py_compile tools/disaster_recovery.py
	$(PYTHON) tools/disaster_recovery.py inventory
	$(PYTHON) tools/disaster_recovery.py verify
