.PHONY: test recovery-doctor data-inventory data-verify data-backup data-backup-dry-run data-restore recovery-check

PYTHON ?= python3
PYTHONPYCACHEPREFIX ?= /tmp/dissertation-pycache

test:
	$(PYTHON) -m pytest

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
