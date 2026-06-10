import logging
import os
from datetime import datetime, timezone

import azure.functions as func
from azure.communication.email import EmailClient


def _get_required_env(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


def main(event: func.EventGridEvent) -> None:
    container_name = os.getenv('MONTHLY_DATA_CONTAINER', 'kerkrada-weather-data').strip() or 'kerkrada-weather-data'
    data = event.get_json() if event else {}
    blob_url = data.get('url', '(unknown)')
    subject = event.subject if event else '(unknown)'
    event_type = event.event_type if event else '(unknown)'
    occurred = event.event_time if event and event.event_time else datetime.now(timezone.utc)

    # Extra guardrail: only notify for new blobs created in the configured container.
    if event_type != 'Microsoft.Storage.BlobCreated':
        logging.info('Skipping event type %s', event_type)
        return
    if f'/containers/{container_name}/' not in subject:
        logging.info('Skipping non-%s subject: %s', container_name, subject)
        return

    connection_string = _get_required_env('AZURE_COMMUNICATION_CONNECTION_STRING')
    sender = _get_required_env('ALERT_SENDER')
    recipients = [r.strip() for r in _get_required_env('ALERT_RECIPIENTS').split(',') if r.strip()]

    email_client = EmailClient.from_connection_string(connection_string)

    message = {
        'senderAddress': sender,
        'content': {
            'subject': f'{container_name} updated: new blob created',
            'plainText': (
                f'A new blob was created in {container_name}.\n\n'
                f'Time (UTC): {occurred.isoformat()}\n'
                f'Event type: {event_type}\n'
                f'Subject: {subject}\n'
                f'Blob URL: {blob_url}\n'
            ),
        },
        'recipients': {
            'to': [{'address': addr} for addr in recipients],
        },
    }

    poller = email_client.begin_send(message)
    result = poller.result()
    logging.info('Blob alert email sent. Message ID: %s', result.get('id'))
