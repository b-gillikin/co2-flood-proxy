# Kerkrade IoT collector

The retained `air_quality_timer` collects the Kerkrade Blynk device stream
into `stkerkradeprod01bg/air-quality-device-data-1`. On 2026-10-15 the daily
email, hourly weather and monthly weather timers were disabled in Azure and
their source was moved to `../archive/retired-kerkrade-alert-weather/`.

The Azure Function App `func-kerkrade-monthly-pull-bg` remains running for the
IoT timer. Do not stop the app or delete its storage account while that stream
is wanted. The separate KNMI and ERA5 backfill apps are stopped.

The source tree now packages only the IoT timer. To redeploy it, use
`azure/deploy_iot.sh` from this directory with an authenticated Azure CLI.
The script targets the existing app and storage; it does not create resources.
Existing Blynk and storage credentials stay in Azure app settings.
