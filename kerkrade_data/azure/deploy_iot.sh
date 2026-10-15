#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

resource_group="rg-kerkrade-prod"
function_app="func-kerkrade-monthly-pull-bg"
archive_zip="$(mktemp /tmp/kerkrade-iot-XXXXXX.zip)"
trap 'rm -f "$archive_zip"' EXIT

az functionapp show --resource-group "$resource_group" --name "$function_app" --query name -o tsv >/dev/null
zip -q -r "$archive_zip" host.json requirements.txt air_quality_timer blynk_co2/pin-mapping.json
az functionapp deployment source config-zip \
  --resource-group "$resource_group" --name "$function_app" \
  --src "$archive_zip" --build-remote true --timeout 600
az functionapp function list --resource-group "$resource_group" --name "$function_app" \
  --query '[].{name:name,isDisabled:isDisabled}' -o table
