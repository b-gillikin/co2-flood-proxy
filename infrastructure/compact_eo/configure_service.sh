#!/usr/bin/env bash
set -euo pipefail
: "${AZURE_VM_RESOURCE_ID:?Set the dedicated VM resource ID}"
: "${EO_DEADLINE_EPOCH:?Set the approved absolute runtime deadline}"
TASK_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEADLINE_CALENDAR="$(date -u -d "@$EO_DEADLINE_EPOCH" '+%Y-%m-%d %H:%M:%S UTC')"
sudo tee /etc/systemd/system/limburg-eo.service >/dev/null <<EOF
[Unit]
Description=Verified Limburg compact EO acquisition
Wants=network-online.target
After=network-online.target
OnFailure=limburg-eo-deallocate.service

[Service]
Type=simple
User=eo
WorkingDirectory=$TASK_ROOT
Environment=AZURE_VM_RESOURCE_ID=$AZURE_VM_RESOURCE_ID
Environment=PYTHONUNBUFFERED=1
ExecStart=$TASK_ROOT/.venv-cloud/bin/python -u $TASK_ROOT/infrastructure/compact_eo/cloud_worker.py --deadline-epoch $EO_DEADLINE_EPOCH --defer-list $TASK_ROOT/data/raw/limburg_compact_eo/seed_pending.json --deallocate
Restart=no
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF
sudo tee /etc/systemd/system/limburg-eo-deallocate.service >/dev/null <<EOF
[Unit]
Description=Deallocate dedicated EO VM to stop compute billing
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=eo
Environment=AZURE_VM_RESOURCE_ID=$AZURE_VM_RESOURCE_ID
ExecStart=$TASK_ROOT/.venv-cloud/bin/python $TASK_ROOT/infrastructure/compact_eo/cloud_worker.py --deallocate-only
EOF
sudo tee /etc/systemd/system/limburg-eo-deadline.timer >/dev/null <<EOF
[Unit]
Description=Absolute fourteen-day EO compute deadline

[Timer]
OnCalendar=$DEADLINE_CALENDAR
Persistent=true
Unit=limburg-eo-deallocate.service

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now limburg-eo-deadline.timer
# Start acquisition only after the cloud export check and local seed handoff.
