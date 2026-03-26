"""
tests/test_interceptor.py — Basic tests for the zero-config HTTP interceptor.

Tests verify that:
- httpx calls to LLM APIs are intercepted and tracked
- Costs are recorded correctly in the ledger
- Non-LLM hosts are ignored
- The interceptor is idempotent (safe to patch twice)
"""
from __future__ import annotations

import json
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_httpx(response_body: bytes):
    """Return a minimal fake httpx module with controllable Client.send."""
    httpx = types.ModuleType("httpx")

    class FakeURL:
        def __init__(self, url):
            self._url = url
        def __str__(self):
            return self._url

    class FakeRequest:
        def __init__(self, url):
            self.url = FakeURL(url)

    class FakeResponse:
        def __init__(self, body: bytes):
            self.content = body
            self.request = None

    class Client:
        def send(self, request, **kwargs):
            resp = FakeResponse(response_body)
            resp.request = request
            return resp

    class AsyncClient:
        async def send(self, request, **kwargs):
            resp = FakeResponse(response_body)
            resp.request = request
            return resp

    httpx.Client = Client
    httpx.AsyncClient = AsyncClient
    httpx.URL = FakeURL
    httpx.Request = FakeRequest
    return httpx, FakeRequest


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInterceptorRecordsCall(unittest.TestCase):
    """Interceptor should record a call when httpx hits an LLM host."""

    def setUp(self):
        # Ensure a fresh global ledger for each test
        import importlib
        import clawmetry.ledger as ledger_mod
        ledger_mod._ledger = None

    def _anthropic_body(self, model="claude-sonnet-4", input_tokens=100, output_tokens=50) -> bytes:
        payload = {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": "Hello!"}],
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }
        return json.dumps(payload).encode()

    def test_anthropic_call_is_tracked(self):
        """An httpx call to api.anthropic.com should be recorded in the ledger."""
        body = self._anthropic_body(input_tokens=1000, output_tokens=500)
        fake_httpx, FakeRequest = _make_fake_httpx(body)

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            # Re-import interceptor with the fake httpx in place
            import importlib
            import clawmetry.interceptor as interceptor_mod
            importlib.reload(interceptor_mod)

            from clawmetry.ledger import get_ledger
            ledger = get_ledger()

            # Patch and simulate a send
            interceptor_mod.patch()
            req = FakeRequest("https://api.anthropic.com/v1/messages")
            client = fake_httpx.Client()
            client.send(req)

            stats = ledger.session_total()

        self.assertEqual(stats["calls"], 1)
        self.assertIn("anthropic", stats["by_provider"])
        self.assertGreater(stats["total_usd"], 0.0)

    def test_non_llm_host_is_ignored(self):
        """Calls to non-LLM hosts should not be recorded."""
        body = json.dumps({"html": "<html></html>"}).encode()
        fake_httpx, FakeRequest = _make_fake_httpx(body)

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            import importlib
            import clawmetry.interceptor as interceptor_mod
            importlib.reload(interceptor_mod)

            from clawmetry.interceptor import _handle_response
            from clawmetry.ledger import get_ledger
            ledger = get_ledger()

            interceptor_mod._handle_response("https://example.com/api", body)
            stats = ledger.session_total()

        self.assertEqual(stats["calls"], 0)

    def test_patch_is_idempotent(self):
        """Calling patch() twice should not double-wrap or raise."""
        body = self._anthropic_body(input_tokens=200, output_tokens=100)
        fake_httpx, FakeRequest = _make_fake_httpx(body)

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            import importlib
            import clawmetry.interceptor as interceptor_mod
            importlib.reload(interceptor_mod)

            from clawmetry.ledger import get_ledger
            ledger = get_ledger()

            interceptor_mod.patch()
            interceptor_mod.patch()  # second call — must be no-op

            req = FakeRequest("https://api.anthropic.com/v1/messages")
            client = fake_httpx.Client()
            client.send(req)

            stats = ledger.session_total()

        # Only one call should be recorded
        self.assertEqual(stats["calls"], 1)

    def test_patch_http_alias(self):
        """patch_http() is an alias for patch() and accepts an optional ledger arg."""
        body = self._anthropic_body(input_tokens=100, output_tokens=50)
        fake_httpx, FakeRequest = _make_fake_httpx(body)

        with patch.dict(sys.modules, {"httpx": fake_httpx}):
            import importlib
            import clawmetry.interceptor as interceptor_mod
            importlib.reload(interceptor_mod)

            from clawmetry.ledger import get_ledger
            ledger = get_ledger()

            # Should not raise even with a ledger argument
            interceptor_mod.patch_http(ledger)

            req = FakeRequest("https://api.anthropic.com/v1/messages")
            client = fake_httpx.Client()
            client.send(req)

            stats = ledger.session_total()

        self.assertEqual(stats["calls"], 1)


class TestProviders(unittest.TestCase):
    """Unit tests for provider detection and cost calculation."""

    def test_detect_anthropic(self):
        from clawmetry.providers import detect_provider
        self.assertEqual(detect_provider("https://api.anthropic.com/v1/messages"), "anthropic")

    def test_detect_openai(self):
        from clawmetry.providers import detect_provider
        self.assertEqual(detect_provider("https://api.openai.com/v1/chat/completions"), "openai")

    def test_detect_unknown(self):
        from clawmetry.providers import detect_provider
        self.assertIsNone(detect_provider("https://example.com/api"))

    def test_cost_calculation(self):
        from clawmetry.providers import get_cost
        # claude-sonnet-4: $3/M input, $15/M output
        cost = get_cost("anthropic", "claude-sonnet-4-20250514", 1_000_000, 1_000_000)
        self.assertAlmostEqual(cost, 18.0, places=2)

    def test_cost_default_fallback(self):
        from clawmetry.providers import get_cost
        # Unknown model falls back to default pricing
        cost = get_cost("anthropic", "claude-unknown-v99", 1_000_000, 0)
        self.assertGreater(cost, 0.0)


class TestLedgerPublicAPI(unittest.TestCase):
    """Tests for the public query API on the ledger."""

    def setUp(self):
        import clawmetry.ledger as ledger_mod
        ledger_mod._ledger = None

    def test_session_total_structure(self):
        from clawmetry.ledger import get_ledger
        ledger = get_ledger()
        stats = ledger.session_total()
        self.assertIn("total_usd", stats)
        self.assertIn("calls", stats)
        self.assertIn("by_provider", stats)
        self.assertIn("duration_seconds", stats)

    def test_today_total_structure(self):
        from clawmetry.ledger import get_ledger
        ledger = get_ledger()
        stats = ledger.today_total()
        self.assertIn("total_usd", stats)
        self.assertIn("calls", stats)
        self.assertIn("by_provider", stats)

    def test_monthly_estimate_is_float(self):
        from clawmetry.ledger import get_ledger
        ledger = get_ledger()
        result = ledger.monthly_estimate()
        self.assertIsInstance(result, float)

    def test_record_updates_session(self):
        from clawmetry.ledger import get_ledger
        ledger = get_ledger()
        ledger.record("openai", "gpt-4o", 1000, 500, 0.01)
        stats = ledger.session_total()
        self.assertEqual(stats["calls"], 1)
        self.assertAlmostEqual(stats["total_usd"], 0.01)
        self.assertIn("openai", stats["by_provider"])


if __name__ == "__main__":
    unittest.main()
