"""Tests for the shared fetch helper and geodesy.

These cover the two failure modes that actually cost time in this repository:
a transient read timeout that killed an hour-long pull because one script had
no retry, and coordinate handling that silently placed a third of the gauge
network in the wrong location.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fetching import fetch, fetch_json, great_circle_km, post_json


class FakeResponse:
    """Minimal stand-in for the object urlopen returns as a context manager."""

    def __init__(self, body=b"", status=200):
        self._body = body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FetchRetryTests(unittest.TestCase):
    def test_retries_transient_failure_then_succeeds(self):
        attempts = []

        def flaky(request, timeout=None):
            attempts.append(1)
            if len(attempts) < 3:
                raise TimeoutError("read timed out")
            return FakeResponse(b"ok")

        with patch("src.fetching.urlopen", flaky), patch("src.fetching.time.sleep"):
            self.assertEqual(fetch("https://example.invalid", quiet=True), b"ok")
        self.assertEqual(len(attempts), 3)

    def test_raises_after_exhausting_retries(self):
        with (
            patch("src.fetching.urlopen", side_effect=URLError("down")),
            patch("src.fetching.time.sleep"),
            self.assertRaises(URLError),
        ):
            fetch("https://example.invalid", retries=2, quiet=True)

    def test_does_not_retry_client_errors(self):
        calls = []

        def not_found(request, timeout=None):
            calls.append(1)
            raise HTTPError("u", 404, "Not Found", {}, None)

        with (
            patch("src.fetching.urlopen", not_found),
            patch("src.fetching.time.sleep"),
            self.assertRaises(HTTPError),
        ):
            fetch("https://example.invalid", quiet=True)
        # A 404 must cost exactly one request, not four.
        self.assertEqual(len(calls), 1)

    def test_retries_server_errors(self):
        calls = []

        def flaky(request, timeout=None):
            calls.append(1)
            if len(calls) < 2:
                raise HTTPError("u", 503, "Service Unavailable", {}, None)
            return FakeResponse(b"recovered")

        with patch("src.fetching.urlopen", flaky), patch("src.fetching.time.sleep"):
            self.assertEqual(fetch("https://example.invalid", quiet=True), b"recovered")
        self.assertEqual(len(calls), 2)

    def test_204_returns_none_rather_than_empty(self):
        # The RWS endpoint answers 204 for periods with no data. That must be
        # distinguishable from an empty body, not coerced to one.
        with patch("src.fetching.urlopen", return_value=FakeResponse(b"", status=204)):
            self.assertIsNone(fetch("https://example.invalid"))

    def test_fetch_json_decodes_and_handles_empty(self):
        with patch("src.fetching.urlopen", return_value=FakeResponse(b'{"a": 1}')):
            self.assertEqual(fetch_json("https://example.invalid"), {"a": 1})
        with patch("src.fetching.urlopen", return_value=FakeResponse(b"")):
            self.assertIsNone(fetch_json("https://example.invalid"))

    def test_post_json_sends_encoded_body_and_content_type(self):
        captured = {}

        def capture(request, timeout=None):
            captured["data"] = request.data
            captured["type"] = request.get_header("Content-type")
            return FakeResponse(b'{"ok": true}')

        with patch("src.fetching.urlopen", capture):
            self.assertEqual(post_json("https://example.invalid", {"q": 2}), {"ok": True})
        self.assertEqual(json.loads(captured["data"]), {"q": 2})
        self.assertEqual(captured["type"], "application/json")


class GreatCircleTests(unittest.TestCase):
    def test_zero_distance(self):
        point = (50.9053, 5.7619)
        self.assertAlmostEqual(great_circle_km(point, point), 0.0, places=6)

    def test_known_separation(self):
        # Maastricht Aachen Airport to Jülich, about 46 km apart.
        maastricht = (50.9053, 5.7619)
        julich = (50.9248, 6.3494)
        self.assertAlmostEqual(great_circle_km(maastricht, julich), 41.3, delta=1.5)

    def test_symmetric(self):
        a, b = (50.87, 5.69), (51.10, 6.10)
        self.assertAlmostEqual(great_circle_km(a, b), great_circle_km(b, a), places=9)

    def test_antipodal_does_not_raise_on_domain_error(self):
        # acos of a value fractionally outside [-1, 1] from floating point must
        # be clamped rather than raising.
        self.assertAlmostEqual(great_circle_km((0.0, 0.0), (0.0, 180.0)), 20015.1, delta=1.0)


if __name__ == "__main__":
    unittest.main()
