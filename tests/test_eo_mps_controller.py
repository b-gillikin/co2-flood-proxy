"""A timed-out MPS probe must not leave a production CPU worker suspended."""

import runpy
import signal
import subprocess
import sys
from pathlib import Path

M = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/106_benchmark_limburg_mps.py")
)


def test_model_timeouts_still_resume_cpu_worker(tmp_path, monkeypatch):
    main = M["main"]
    monkeypatch.setitem(main.__globals__, "OUT", tmp_path)
    monkeypatch.setitem(main.__globals__, "prepare_adapter", lambda: None)
    monkeypatch.setattr(sys, "argv", ["probe", "--run", "--pause-pid", "123"])
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda *a, **k: "python scripts/100_extract_limburg_eo_sequences.py --model dofa --run",
    )
    signals = []
    monkeypatch.setattr(M["os"], "kill", lambda pid, sig: signals.append((pid, sig)))
    monkeypatch.setattr(M["signal"], "signal", lambda *a: None)

    class TimeoutChild:
        def __init__(self, *args, **kwargs):
            self.returncode = None

        def wait(self, timeout=None):
            if self.returncode is None:
                raise subprocess.TimeoutExpired("probe", timeout)
            return self.returncode

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr(subprocess, "Popen", TimeoutChild)
    assert main() == 0
    assert signals == [(123, signal.SIGSTOP), (123, signal.SIGCONT)]
    import json

    state = json.loads((tmp_path / "progress.json").read_text())
    assert state["cpu_job_resumed"]
    assert len(state["models"]) == 10
    assert all(r["exit_code"] == 124 for r in state["models"].values())
