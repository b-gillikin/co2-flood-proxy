"""Finite GPU throughput sweep with guaranteed resume of an existing fit.

The old process is temporarily suspended, never terminated/restarted. A
separate watchdog resumes it even if this profiling controller disappears.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "results/applied_optimization_2026_11_02"
    before = json.loads((out / "inherited-state.json").read_text())
    pid = before["actor"]["pid"]
    suspended = False
    watchdog = None
    started = time.time()
    jobs = []
    try:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pid = None
        if pid:
            command = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "command="], text=True
            ).strip()
            if "192_tune_applied_water.py" not in command:
                raise ValueError("Unexpected inherited PID")
            watchdog_code = (
                'import os,signal,subprocess,time; time.sleep(1200); command=subprocess.check_output(["ps","-p",'
                + repr(str(pid))
                + ',"-o","command="],text=True).strip(); os.kill('
                + str(pid)
                + ",signal.SIGCONT) if command=="
                + repr(command)
                + " else None"
            )
            watchdog = subprocess.Popen(
                [sys.executable, "-c", watchdog_code],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            os.kill(pid, signal.SIGSTOP)
            suspended = True
            time.sleep(0.3)
        settings = {
            "galileo": dict(
                linear=[64, 256, 512],
                native=[64, 256, 512],
                unet=[64, 256, 512],
                unet_standard=[64, 256, 512],
            ),
            "prithvi": dict(
                linear=[2, 8, 16], native=[2, 8, 16], unet=[2, 8, 16], unet_standard=[2, 8, 16]
            ),
            "terramind": dict(linear=[8, 16], native=[8, 16], unet=[8, 16], unet_standard=[8, 16]),
            "copernicus": dict(
                linear=[2, 16, 32, 64],
                native=[2, 16, 32, 64],
                unet=[2, 16, 32, 64],
                unet_standard=[2, 16, 32, 64],
            ),
        }
        for task, learners in settings.items():
            for learner, batches in learners.items():
                py = (
                    ROOT
                    / f".venvs-applied/{'galileo' if task == 'galileo' else 'copernicus' if task == 'copernicus' else 'spatial'}/bin/python"
                )
                output = out / f"{task}-{learner}-mps-fast.json"
                if output.exists():
                    continue
                cmd = [
                    str(py),
                    "-u",
                    "scripts/219_profile_fast_spatial.py",
                    "--task",
                    task,
                    "--learner",
                    learner,
                    "--device",
                    "mps",
                    "--batches",
                    *[str(b) for b in batches],
                    "--output",
                    str(output),
                ]
                with (out / f"{task}-{learner}-mps-fast.log").open("ab") as log:
                    try:
                        r = subprocess.run(
                            cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=120
                        )
                    except subprocess.TimeoutExpired:
                        jobs.append(
                            dict(
                                task=task,
                                learner=learner,
                                status="profile_timeout_partial_results_preserved",
                            )
                        )
                        continue
                jobs.append(dict(task=task, learner=learner, returncode=r.returncode))
                (out / "mps-profile-progress.json").write_text(
                    json.dumps(
                        dict(jobs=jobs, started_unix=started, old_fit_suspended=suspended), indent=2
                    )
                    + "\n"
                )
                if time.time() - started > 1100:
                    break
    finally:
        if suspended:
            try:
                os.kill(pid, signal.SIGCONT)
            except ProcessLookupError:
                pass
        if watchdog:
            watchdog.terminate()
        (out / "mps-profile-progress.json").write_text(
            json.dumps(
                dict(
                    status="finished",
                    jobs=jobs,
                    elapsed_s=time.time() - started,
                    old_fit_resumed=suspended,
                ),
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
