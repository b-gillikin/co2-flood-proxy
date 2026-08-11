#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PACKAGE_DIR="$ROOT/infrastructure/era5_backfill"
SOURCE_DIR="${SOURCE_DIR:-$ROOT/data/raw/era5_land}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CDS_CONFIG="${CDS_CONFIG:-$HOME/.cdsapirc}"

SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-c7729fd0-7b35-4ec4-b1a3-ec7079b776fa}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-kerkrade-prod}"
LOCATION="${LOCATION:-eastus}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-stkerkradeprod01bg}"
FUNCTION_APP="${FUNCTION_APP:-func-kerkrade-era5-backfill-bg}"
CONTAINER="${CONTAINER:-era5-land}"

if [[ ! -f "$CDS_CONFIG" ]]; then
  echo "Missing CDS configuration: $CDS_CONFIG" >&2
  exit 1
fi

CDS_URL="$(awk -F': ' '$1 == "url" {print $2}' "$CDS_CONFIG")"
CDS_KEY="$(awk -F': ' '$1 == "key" {print $2}' "$CDS_CONFIG")"
if [[ -z "$CDS_URL" || -z "$CDS_KEY" ]]; then
  echo "CDS url/key not found in $CDS_CONFIG" >&2
  exit 1
fi

STORAGE_CONNECTION="$(az storage account show-connection-string \
  --subscription "$SUBSCRIPTION_ID" \
  --resource-group "$RESOURCE_GROUP" \
  --name "$STORAGE_ACCOUNT" \
  --query connectionString -o tsv)"

az storage container create \
  --connection-string "$STORAGE_CONNECTION" \
  --name "$CONTAINER" \
  -o none

TEMP_DIR="$(mktemp -d)"
SCM_POLICY_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$FUNCTION_APP/basicPublishingCredentialsPolicies/scm"
SCM_OPEN=false

cleanup() {
  rm -rf "$TEMP_DIR"
  if [[ "$SCM_OPEN" == true ]]; then
    az resource update \
      --subscription "$SUBSCRIPTION_ID" \
      --ids "$SCM_POLICY_ID" \
      --set properties.allow=false \
      -o none || true
  fi
}
trap cleanup EXIT
MANIFEST="$TEMP_DIR/manifest.csv"

if [[ "${SEED_LOCAL_FILES:-true}" == true ]]; then
  "$PYTHON_BIN" "$PACKAGE_DIR/seed_existing.py" \
    --source-dir "$SOURCE_DIR" \
    --manifest "$MANIFEST"

  az storage blob upload-batch \
    --connection-string "$STORAGE_CONNECTION" \
    --destination "$CONTAINER/source" \
    --source "$SOURCE_DIR" \
    --pattern "era5_land_limburg_????_??.nc" \
    --overwrite true \
    -o none

  az storage blob upload \
    --connection-string "$STORAGE_CONNECTION" \
    --container-name "$CONTAINER" \
    --name manifest.csv \
    --file "$MANIFEST" \
    --overwrite true \
    -o none
fi

if ! az functionapp show \
  --subscription "$SUBSCRIPTION_ID" \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" >/dev/null 2>&1; then
  az functionapp create \
    --subscription "$SUBSCRIPTION_ID" \
    --resource-group "$RESOURCE_GROUP" \
    --name "$FUNCTION_APP" \
    --consumption-plan-location "$LOCATION" \
    --os-type Linux \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --storage-account "$STORAGE_ACCOUNT" \
    -o none
fi

az resource update \
  --subscription "$SUBSCRIPTION_ID" \
  --ids "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$FUNCTION_APP" \
  --set properties.httpsOnly=true \
  -o none

az functionapp config appsettings set \
  --subscription "$SUBSCRIPTION_ID" \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --settings \
    "AzureWebJobsStorage=$STORAGE_CONNECTION" \
    "AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION" \
    "CDSAPI_URL=$CDS_URL" \
    "CDSAPI_KEY=$CDS_KEY" \
    "ERA5_CONTAINER=$CONTAINER" \
    "ERA5_ENABLED=false" \
    "ERA5_TIMER_SCHEDULE=0 */5 * * * *" \
    "FUNCTIONS_WORKER_RUNTIME=python" \
    "FUNCTIONS_WORKER_PROCESS_COUNT=1" \
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true" \
    "ENABLE_ORYX_BUILD=true" \
  -o none

ARCHIVE="$TEMP_DIR/functionapp.zip"
(
  cd "$PACKAGE_DIR"
  zip -q -r "$ARCHIVE" \
    host.json requirements.txt era5_common.py era5_backfill_timer
)

az resource update \
  --subscription "$SUBSCRIPTION_ID" \
  --ids "$SCM_POLICY_ID" \
  --set properties.allow=true \
  -o none
SCM_OPEN=true

SCM_USER="$(az functionapp deployment list-publishing-credentials \
  --subscription "$SUBSCRIPTION_ID" \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --query publishingUserName -o tsv)"
SCM_PASSWORD="$(az functionapp deployment list-publishing-credentials \
  --subscription "$SUBSCRIPTION_ID" \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --query publishingPassword -o tsv)"

DEPLOY_HEADERS="$TEMP_DIR/deploy-headers.txt"
curl --fail --silent --show-error \
  --user "$SCM_USER:$SCM_PASSWORD" \
  --header "Content-Type: application/zip" \
  --request POST \
  --data-binary "@$ARCHIVE" \
  --dump-header "$DEPLOY_HEADERS" \
  --output /dev/null \
  "https://$FUNCTION_APP.scm.azurewebsites.net/api/zipdeploy?isAsync=true"

DEPLOY_URL="$(awk 'tolower($1) == "location:" {gsub(/\r/, "", $2); print $2}' \
  "$DEPLOY_HEADERS")"
if [[ -z "$DEPLOY_URL" ]]; then
  echo "Azure did not return a deployment status URL." >&2
  exit 1
fi

DEPLOY_STATUS=""
for _ in {1..120}; do
  DEPLOY_STATUS="$(curl --fail --silent --show-error \
    --user "$SCM_USER:$SCM_PASSWORD" \
    "$DEPLOY_URL" | jq -r '.status')"
  if [[ "$DEPLOY_STATUS" == 4 ]]; then
    break
  fi
  if [[ "$DEPLOY_STATUS" == 3 ]]; then
    echo "Azure remote build failed; inspect the Kudu deployment log." >&2
    exit 1
  fi
  sleep 10
done

if [[ "$DEPLOY_STATUS" != 4 ]]; then
  echo "Azure remote build did not finish within 20 minutes." >&2
  exit 1
fi

az resource update \
  --subscription "$SUBSCRIPTION_ID" \
  --ids "$SCM_POLICY_ID" \
  --set properties.allow=false \
  -o none
SCM_OPEN=false

az rest \
  --subscription "$SUBSCRIPTION_ID" \
  --method post \
  --url "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$FUNCTION_APP/syncfunctiontriggers?api-version=2022-03-01" \
  -o none

FUNCTIONS="$(az functionapp function list \
  --subscription "$SUBSCRIPTION_ID" \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FUNCTION_APP" \
  --query "[].name" -o tsv)"
if [[ "$FUNCTIONS" != *"/era5_backfill_timer"* ]]; then
  echo "Azure did not discover era5_backfill_timer after deployment." >&2
  exit 1
fi

echo "Deployed $FUNCTION_APP paused."
