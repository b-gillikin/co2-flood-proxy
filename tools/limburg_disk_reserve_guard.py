"""Live operational disk guard; leaves frozen scientific code unchanged.

Pause the registered local controller/workers below the configured reserve.
Resume above reserve + 1 GiB. No termination, deletion or cloud action.
"""
import json
import os
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'results/limburg_individual_experiments_v1/queue'
CONFIG = ROOT / 'config/limburg_disk_reserve_guard.json'
STATUS = QUEUE / 'disk-guard.json'


def command(pid):
    result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'command='],
                            text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else ''


def write_status(value):
    stage = STATUS.with_suffix('.tmp')
    stage.write_text(json.dumps(value, indent=2) + '\n')
    stage.replace(STATUS)


def main():
    import fcntl
    lock = (QUEUE / '.disk-guard.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    paused = {}
    try:
        while True:
            config = json.loads(CONFIG.read_text())
            reserve = float(config['minimum_free_gib'])
            assert reserve > 0
            state = json.loads((QUEUE / 'progress.json').read_text())
            controller = int(state['controller_pid'])
            controller_command = command(controller)
            if '173_queue_individual_experiments.py' not in controller_command:
                break
            free = shutil.disk_usage(ROOT).free / 2**30
            if free < reserve:
                # Freeze the scheduler before enumerating its current children.
                if controller not in paused:
                    os.kill(controller, signal.SIGSTOP)
                    paused[controller] = controller_command
                state = json.loads((QUEUE / 'progress.json').read_text())
                for task in state['tasks'].values():
                    if task.get('status') != 'running':
                        continue
                    pid = int(task['pid'])
                    cmd = command(pid)
                    if any(f'{n}_' in cmd for n in (170, 171, 172, 173)) and pid not in paused:
                        try:
                            os.kill(pid, signal.SIGSTOP)
                            paused[pid] = cmd
                        except ProcessLookupError:
                            pass
            elif paused and free >= reserve + 1:
                for pid, cmd in list(paused.items()):
                    if command(pid) == cmd:
                        try:
                            os.kill(pid, signal.SIGCONT)
                        except ProcessLookupError:
                            pass
                    del paused[pid]
            write_status(dict(status='paused_low_disk' if paused else 'monitoring',
                              guard_pid=os.getpid(), controller_pid=controller,
                              minimum_free_gib=reserve, resume_free_gib=reserve+1,
                              disk_free_gib=round(free, 2), paused_pids=list(paused),
                              updated_utc=datetime.now(timezone.utc).isoformat()))
            time.sleep(10)
    finally:
        # An orderly guard shutdown must not strand suspended workers.
        for pid, cmd in paused.items():
            if command(pid) == cmd:
                try:
                    os.kill(pid, signal.SIGCONT)
                except ProcessLookupError:
                    pass


if __name__ == '__main__':
    main()
