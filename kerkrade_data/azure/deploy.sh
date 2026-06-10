#!/usr/bin/env bash
set -euo pipefail

# Required env vars:
# SUBSCRIPTION_ID, RESOURCE_GROUP, LOCATION, STORAGE_ACCOUNT, FILE_SHARE,
# CONTAINERAPPS_ENV, ACR_NAME, JOB_NAME, IMAGE_NAME, IMAGE_TAG, API_KEYS

: "${SUBSCRIPTION_ID:?Missing SUBSCRIPTION_ID}"
: "${RESOURCE_GROUP:?Missing RESOURCE_GROUP}"
: "${LOCATION:?Missing LOCATION}"
: "${STORAGE_ACCOUNT:?Missing STORAGE_ACCOUNT}"
: "${FILE_SHARE:?Missing FILE_SHARE}"
: "${CONTAINERAPPS_ENV:?Missing CONTAINERAPPS_ENV}"
: "${ACR_NAME:?Missing ACR_NAME}"
: "${JOB_NAME:?Missing JOB_NAME}"
: "${IMAGE_NAME:?Missing IMAGE_NAME}"
: "${IMAGE_TAG:?Missing IMAGE_TAG}"
: "${API_KEYS:?Missing API_KEYS (comma-separated)}"

az extension add --name containerapp --upgrade
az extension add --name storage-preview --upgrade

az login
az account set --subscription "$SUBSCRIPTION_ID"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2

az storage share-rm create \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT" \
  --name "$FILE_SHARE"

STORAGE_KEY=$(az storage account keys list \
  --resource-group "$RESOURCE_GROUP" \
  --account-name "$STORAGE_ACCOUNT" \
  --query '[0].value' -o tsv)

# Seed current monthly_data into Azure Files so existing backfill state is preserved.
az storage file upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --account-key "$STORAGE_KEY" \
  --destination "$FILE_SHARE" \
  --source ./monthly_data

az acr create \
  --name "$ACR_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Basic

az acr update --name "$ACR_NAME" --admin-enabled true
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query 'passwords[0].value' -o tsv)

az acr build \
  --registry "$ACR_NAME" \
  --image "$IMAGE_NAME:$IMAGE_TAG" \
  .

az containerapp env create \
  --name "$CONTAINERAPPS_ENV" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

az containerapp env storage set \
  --name "$CONTAINERAPPS_ENV" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-name monthlydata \
  --azure-file-account-name "$STORAGE_ACCOUNT" \
  --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$FILE_SHARE" \
  --access-mode ReadWrite

TEMPLATE=azure/job.template.yaml
RENDERED=azure/job.rendered.yaml

sed \
  -e "s|__SUBSCRIPTION_ID__|$SUBSCRIPTION_ID|g" \
  -e "s|__RESOURCE_GROUP__|$RESOURCE_GROUP|g" \
  -e "s|__LOCATION__|$LOCATION|g" \
  -e "s|__CONTAINERAPPS_ENV__|$CONTAINERAPPS_ENV|g" \
  -e "s|__ACR_NAME__|$ACR_NAME|g" \
  -e "s|__JOB_NAME__|$JOB_NAME|g" \
  -e "s|__IMAGE_NAME__|$IMAGE_NAME|g" \
  -e "s|__IMAGE_TAG__|$IMAGE_TAG|g" \
  -e "s|__ACR_USERNAME__|$ACR_USERNAME|g" \
  -e "s|__ACR_PASSWORD__|$ACR_PASSWORD|g" \
  -e "s|__API_KEYS_COMMA_SEPARATED__|$API_KEYS|g" \
  "$TEMPLATE" > "$RENDERED"

if az containerapp job show --name "$JOB_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  az containerapp job update --resource-group "$RESOURCE_GROUP" --name "$JOB_NAME" --yaml "$RENDERED"
else
  az containerapp job create --resource-group "$RESOURCE_GROUP" --name "$JOB_NAME" --yaml "$RENDERED"
fi

az containerapp job start --resource-group "$RESOURCE_GROUP" --name "$JOB_NAME"
az containerapp job execution list --resource-group "$RESOURCE_GROUP" --name "$JOB_NAME" -o table

echo "Deployment complete."
echo "Schedule uses UTC: 00:00, 09:00, 12:00, 15:00, 18:00, 21:00 UTC"
