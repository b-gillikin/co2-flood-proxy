"""Checks the small telemetry contract used by the external run monitor."""

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/224_emit_limburg_monitor_event.py"
SPEC = importlib.util.spec_from_file_location("limburg_monitor_event", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_connection_string_reads_private_file(tmp_path, monkeypatch):
    monkeypatch.delenv("LIMBURG_APPINSIGHTS_CONNECTION_STRING", raising=False)
    private = tmp_path / "monitor.env"
    private.write_text("InstrumentationKey=test;IngestionEndpoint=https://example.org/\n")
    value = MODULE.connection_string(private)
    assert MODULE.endpoint_and_key(value) == ("https://example.org/v2/track", "test")


def test_connection_string_requires_https_and_key():
    with pytest.raises(ValueError):
        MODULE.endpoint_and_key("InstrumentationKey=test;IngestionEndpoint=http://example.org/")
    with pytest.raises(ValueError):
        MODULE.endpoint_and_key("IngestionEndpoint=https://example.org/")
