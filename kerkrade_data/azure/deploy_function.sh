#!/usr/bin/env bash
set -euo pipefail

# Required env vars:
# SUBSCRIPTION_ID, RESOURCE_GROUP, LOCATION, STORAGE_ACCOUNT, FUNCTION_APP, API_KEYS
# Optional env vars:
# MONTHLY_DATA_CONTAINER (default: kerkrada-weather-data), PYTHON_VERSION (default: 3.11)

: "${SUBSCRIPTION_ID:?Missing SUBSCRIPTION_ID}"
: "${RESOURCE_GROUP:?Missing RESOURCE_GROUP}"
: "${LOCATION:?Missing LOCATION}"
: "${STORAGE_ACCOUNT:?Missing STORAGE_ACCOUNT}"
: "${FUNCTION_APP:?Missing FUNCTION_APP}"
: "${API_KEYS:?Missing API_KEYS (comma-separated)}"

MONTHLY_DATA_CONTAINER="${MONTHLY_DATA_CONTAINER:-kerkrada-weather-data}"
LOCATION_CONTAINER_MAP="${LOCATION_CONTAINER_MAP:-Kerkrade:kerkrada-weather-data;Liege:liege-weather-data;Maastricht:maastricht-weather-data;Aachen:aachen-weather-data;Cologne:cologne-weather-data}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

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
  --name "$MONTHLY_DATA_CONTAINER" \
  --account-name "$STORAGE_ACCOUNT" \
  --account-key "$STORAGE_KEY"

# Seed existing data/state.
az storage blob upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --account-key "$STORAGE_KEY" \
  --destination "$MONTHLY_DATA_CONTAINER" \
  --source ./monthly_data \
  --overwrite

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
    "API_KEYS=$API_KEYS" \
    "AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONN" \
    "MONTHLY_DATA_CONTAINER=$MONTHLY_DATA_CONTAINER" \
    "LOCATION_CONTAINER_MAP=$LOCATION_CONTAINER_MAP" \
    "AzureWebJobsStorage=$STORAGE_CONN" \
    "WEBSITE_RUN_FROM_PACKAGE=1"

mkdir -p build
rm -f build/functionapp.zip
python3 - <<'PY'
from pathlib import Path
import zipfile

root = Path('.')
out = Path('build/functionapp.zip')
exclude_prefixes = {
    '.venv/',
    '__pycache__/',
    'monthly_data/',
    'logs/',
    'azure/',
    'build/',
}
exclude_names = {'.DS_Store'}

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for p in root.rglob('*'):
        if p.is_dir():
            continue
        rel = p.as_posix()
        if any(rel.startswith(prefix) for prefix in exclude_prefixes):
            continue
        if p.name in exclude_names or rel.endswith('.pyc'):
            continue
        zf.write(p, rel)
PY

az functionapp deployment source config-zip \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --src build/functionapp.zip

az functionapp function list \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --query '[].name' -o tsv

echo "Deployment complete."
echo "Timer schedule is UTC: 00:00, 09:00, 12:00, 15:00, 18:00, 21:00"
