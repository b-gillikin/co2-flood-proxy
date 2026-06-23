#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/Users/briangillikin/Desktop/chapter1-co2"
PYTHON="/Users/briangillikin/miniforge3/envs/chapter1-co2/bin/python"

cd "$REPO_ROOT"
mkdir -p logs .matplotlib
export MPLCONFIGDIR="$REPO_ROOT/.matplotlib"

LOCK_DIR="$REPO_ROOT/logs/knmi-hourly.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Another KNMI hourly job is already running; exiting."
  exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT

if [[ -z "${KNMI_API_KEY:-}" && -f "$HOME/.knmi_api_key" ]]; then
  export KNMI_API_KEY="$(tr -d '\n\r' < "$HOME/.knmi_api_key")"
fi

if [[ -z "${KNMI_API_KEY:-}" ]]; then
  echo "KNMI_API_KEY is not set and $HOME/.knmi_api_key was not found."
  exit 1
fi

KNMI_DEFAULT_END="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

"$PYTHON" scripts/04_ingest_knmi.py \
  --start "${KNMI_START:-2020-01-01T00:00:00Z}" \
  --end "${KNMI_END:-$KNMI_DEFAULT_END}" \
  --max-files "${KNMI_MAX_FILES:-0}" \
  --max-downloads "${KNMI_MAX_DOWNLOADS:-800}" \
  --download-sleep-seconds "${KNMI_DOWNLOAD_SLEEP_SECONDS:-4.0}" \
  --station-set "${KNMI_STATION_SET:-meuse}" \
  --comparison-station "${KNMI_COMPARISON_STATION:-06380}"
