#!/usr/bin/env bash
set -euo pipefail
: "${AZURE_VM_RESOURCE_ID:?Set the existing dedicated acquisition VM resource ID}"
: "${EO_DEADLINE_EPOCH:?Keep the existing absolute acquisition deadline}"
TASK_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CLOUD_PYTHON="/home/eo/limburg-eo/.venv-cloud/bin/python"
sudo systemctl disable --now limburg-eo.service
sudo tee /etc/systemd/system/limburg-eo-expansion.service >/dev/null <<EOF
[Unit]
Description=Verified supplemental Limburg EO acquisition
Wants=network-online.target
After=network-online.target
OnFailure=limburg-eo-deallocate.service

[Service]
Type=simple
User=eo
WorkingDirectory=$TASK_ROOT
Environment=AZURE_VM_RESOURCE_ID=$AZURE_VM_RESOURCE_ID
Environment=PYTHONUNBUFFERED=1
Environment=OPENBLAS_NUM_THREADS=1
Environment=OMP_NUM_THREADS=1
Environment=GDAL_NUM_THREADS=1
ExecStart=$CLOUD_PYTHON -u $TASK_ROOT/infrastructure/eo_expansion/cloud_worker.py --max-gb 300 --workers 3 --deadline-epoch $EO_DEADLINE_EPOCH --defer-list $TASK_ROOT/data/raw/limburg_eo_expansion/seed_pending.json --deallocate
Restart=no
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
# Start explicitly after cloud smoke and local seed-list publication.
