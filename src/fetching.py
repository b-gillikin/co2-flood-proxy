"""Shared HTTP fetching and geodesy for the ingest scripts.

Every ingest script in this repository talks to a public endpoint that fails
occasionally, and until 2026-08-06 each rolled its own request helper. The
predictable happened: `scripts/26_ingest_rws_maas.py` was written without a
retry and a single read timeout killed a fifty-minute pull on its 78th request,
while `scripts/22_ingest_waterschap_gauges.py` had had retry logic all along.

The point of this module is not abstraction for its own sake. It is that
"retry transient failures, fail fast on everything else" is a decision that
should be made once and applied everywhere, rather than re-litigated per script.

`great_circle_km` lives here for the same reason: it was duplicated verbatim in
two analysis scripts.
"""

from __future__ import annotations

import json
import math
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Failures worth retrying: the connection dropped or stalled. A 4xx means the
# request itself was wrong and retrying only wastes time.
TRANSIENT = (TimeoutError, URLError, ConnectionError, json.JSONDecodeError)

DEFAULT_RETRIES = 4
DEFAULT_TIMEOUT = 300


def fetch(
    url, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, data=None, headers=None, quiet=False
):
    """GET or POST one URL, returning raw bytes, or None on HTTP 204.

    Retries transient network failures with linear backoff. HTTP errors below
    500 are raised immediately, since a 404 will still be a 404 next time.

    Passing ``data`` makes it a POST; ``headers`` is merged in as-is.
    """
    request = Request(url, data=data, headers=headers or {})
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status == 204:
                    return None
                return response.read()
        except HTTPError as exc:
            if exc.code == 204:
                return None
            if attempt == retries or exc.code < 500:
                raise
        except TRANSIENT as exc:
            if attempt == retries:
                raise
            if not quiet:
                print(f"    retry {attempt}/{retries - 1} after {type(exc).__name__}")
        time.sleep(5 * attempt)
    return None


def fetch_json(url, **kwargs):
    """Fetch and decode one JSON payload. Returns None when the body is empty."""
    body = fetch(url, **kwargs)
    return json.loads(body) if body else None


def post_json(url, payload, **kwargs):
    """POST one JSON document and decode the JSON reply."""
    return fetch_json(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        **kwargs,
    )


def great_circle_km(a, b):
    """Distance in kilometres between two (latitude, longitude) pairs."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    inner = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(
        lon2 - lon1
    )
    return 6371.0 * math.acos(min(1.0, max(-1.0, inner)))
