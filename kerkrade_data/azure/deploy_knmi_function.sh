#!/usr/bin/env bash
set -euo pipefail

# Required env vars:
# SUBSCRIPTION_ID, RESOURCE_GROUP, LOCATION, STORAGE_ACCOUNT, FUNCTION_APP, KNMI_API_KEY
# Optional env vars:
# KNMI_CONTAINER (default: knmi-data)
# KNMI_START (default: 2026-06-24T12:00:00Z production handoff)
# KNMI_BACKFILL_DIRECTION (default: forward)
# KNMI_STATE_BLOB (direction-specific default)
# KNMI_AVAILABILITY_LAG_MINUTES (default: 180 for forward collection)
# KNMI_STATIONS (default: selected Meuse/Maas stations)
# KNMI_MAX_DOWNLOADS_PER_RUN (default: 200)
# KNMI_KEEP_RAW (default: false)
# KNMI_BACKFILL_SCHEDULE (default: every 15 minutes)
# PYTHON_VERSION (default: 3.11)

: "${SUBSCRIPTION_ID:?Missing SUBSCRIPTION_ID}"
: "${RESOURCE_GROUP:?Missing RESOURCE_GROUP}"
: "${LOCATION:?Missing LOCATION}"
: "${STORAGE_ACCOUNT:?Missing STORAGE_ACCOUNT}"
: "${FUNCTION_APP:?Missing FUNCTION_APP}"
: "${KNMI_API_KEY:?Missing KNMI_API_KEY}"

KNMI_CONTAINER="${KNMI_CONTAINER:-knmi-data}"
KNMI_START="${KNMI_START:-2026-06-24T12:00:00Z}"
KNMI_BACKFILL_DIRECTION="${KNMI_BACKFILL_DIRECTION:-forward}"
if [[ -z "${KNMI_STATE_BLOB:-}" ]]; then
  if [[ "$KNMI_BACKFILL_DIRECTION" == "forward" ]]; then
    KNMI_STATE_BLOB="state/knmi_forward_state.json"
  else
    KNMI_STATE_BLOB="state/knmi_backfill_state.json"
  fi
fi
KNMI_AVAILABILITY_LAG_MINUTES="${KNMI_AVAILABILITY_LAG_MINUTES:-180}"
KNMI_STATIONS="${KNMI_STATIONS:-06380,06377,06392,06370,06375,06350,06356}"
KNMI_MAX_DOWNLOADS_PER_RUN="${KNMI_MAX_DOWNLOADS_PER_RUN:-200}"
KNMI_DOWNLOAD_SLEEP_SECONDS="${KNMI_DOWNLOAD_SLEEP_SECONDS:-0.0}"
KNMI_KEEP_RAW="${KNMI_KEEP_RAW:-false}"
KNMI_BACKFILL_SCHEDULE="${KNMI_BACKFILL_SCHEDULE:-0 */15 * * * *}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

STORAGE_ACCOUNT="${STORAGE_ACCOUNT#https://}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT#http://}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT%%.blob.core.windows.net*}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT%%.*}"

if [[ ! "$STORAGE_ACCOUNT" =~ ^[a-z0-9]{3,24}$ ]]; then
  echo "STORAGE_ACCOUNT must be the short Azure storage account name only."
  echo "Example: stkerkradeprod01bg, not stkerkradeprod01bg.blob.core.windows.net"
  exit 1
fi

if ! az account show >/dev/null 2>&1; then
  echo "Not logged into Azure CLI. Run: az login --use-device-code"
  exit 1
fi
az account set --subscription "$SUBSCRIPTION_ID"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2

STORAGE_KEY=$(az storage account keys list \
  --resource-group "$RESOURCE_GROUP" \
  --account-name "$STORAGE_ACCOUNT" \
  --query '[0].value' -o tsv)

STORAGE_CONN=$(az storage account show-connection-string \
  --resource-group "$RESOURCE_GROUP" \
  --name "$STORAGE_ACCOUNT" \
  --query connectionString -o tsv)

az storage container create \
  --name "$KNMI_CONTAINER" \
  --account-name "$STORAGE_ACCOUNT" \
  --account-key "$STORAGE_KEY"

if ! az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  az functionapp create \
    --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --consumption-plan-location "$LOCATION" \
    --os-type Linux \
    --runtime python \
    --runtime-version "$PYTHON_VERSION" \
    --functions-version 4 \
    --storage-account "$STORAGE_ACCOUNT"
fi

az functionapp config appsettings set \
  --name "$FUNCTION_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    "FUNCTIONS_WORKER_RUNTIME=python" \
    "AzureWebJobsStorage=$STORAGE_CONN" \
    "AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONN" \
    "KNMI_API_KEY=$KNMI_API_KEY" \
    "KNMI_CONTAINER=$KNMI_CONTAINER" \
    "KNMI_START=$KNMI_START" \
    "KNMI_BACKFILL_DIRECTION=$KNMI_BACKFILL_DIRECTION" \
    "KNMI_STATE_BLOB=$KNMI_STATE_BLOB" \
    "KNMI_AVAILABILITY_LAG_MINUTES=$KNMI_AVAILABILITY_LAG_MINUTES" \
    "KNMI_STATIONS=$KNMI_STATIONS" \
    "KNMI_MAX_DOWNLOADS_PER_RUN=$KNMI_MAX_DOWNLOADS_PER_RUN" \
    "KNMI_DOWNLOAD_SLEEP_SECONDS=$KNMI_DOWNLOAD_SLEEP_SECONDS" \
    "KNMI_KEEP_RAW=$KNMI_KEEP_RAW" \
    "KNMI_BACKFILL_SCHEDULE=$KNMI_BACKFILL_SCHEDULE" \
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true" \
    "ENABLE_ORYX_BUILD=true"

az functionapp config appsettings delete \
  --name "$FUNCTION_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --setting-names WEBSITE_RUN_FROM_PACKAGE \
  --yes >/dev/null 2>&1 || true

mkdir -p build
rm -rf .python_packages
python3 -m pip install \
  --target .python_packages/lib/site-packages \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 311 \
  --only-binary=:all: \
  -r requirements.txt

python3 - <<'PY'
from pathlib import Path
import zipfile

root = Path(".")
out = Path("build/knmi-functionapp.zip")
files = [
    "host.json",
    "requirements.txt",
    "knmi_backfill.py",
    "knmi_backfill_timer/__init__.py",
    "knmi_backfill_timer/function.json",
]

if out.exists():
    out.unlink()

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for name in files:
        path = root / name
        zf.write(path, name)
    for path in (root / ".python_packages").rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            zf.write(path, path.as_posix())
PY

az functionapp deployment source config-zip \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --src build/knmi-functionapp.zip

az functionapp function list \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --query '[].name' -o tsv

echo "KNMI deployment complete."
echo "Timer schedule is UTC: $KNMI_BACKFILL_SCHEDULE"
echo "Direction: $KNMI_BACKFILL_DIRECTION"
echo "Start boundary: $KNMI_START"
echo "State blob: $KNMI_CONTAINER/$KNMI_STATE_BLOB"
echo "Availability lag: $KNMI_AVAILABILITY_LAG_MINUTES minutes"
echo "Raw files:  $KNMI_CONTAINER/raw/10-minute-in-situ/"
