#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip
python3 -m venv "$TASK_ROOT/.venv-cloud"
"$TASK_ROOT/.venv-cloud/bin/pip" install -r "$TASK_ROOT/infrastructure/compact_eo/requirements.txt"
chmod 700 "$HOME/.config/earthengine"
chmod 600 "$HOME/.config/earthengine/credentials"
