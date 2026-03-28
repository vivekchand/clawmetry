"""
Tests for clawmetry.track (GH #374 — zero-config HTTP interceptor).

Validates:
- Provider detection from URL
- Token / cost parsing from mock responses
- Accumulator totals after multiple calls
- Graceful handling of unknown models / missing usage fields
- Import is idempotent (safe to import multiple times)
"""
from __future__ import annotations

import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Disable auto-patching during test collection so we control activation
os.environ["CLAWMETRY_NO_INTERCEPT"] = "1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_anthropic_response(model: str, inp: int, out: int) -> bytes:
    return json.dumps({
        "model": model,
        "usage": {"input_tokens": inp, "output_tokens": out},
    }).encode()


def _make_openai_response(model: str, inp: int, out: int) -> bytes:
    return json.dumps({
        "model": model,
        "usage": {"prompt_tokens": inp, "completion_tokens": out},
    }).encode()


def _make_gemini_response(inp: int, out: int) -> bytes:
    return json.dumps({
        "model": "gemini-1.5-flash",
        "usageMetadata": {"promptTokenCount": inp, "candidatesTokenCount": out},
    }).encode()


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

class TestProviderDetection(unittest.TestCase):
    def _detect(self, url: str):
        from clawmetry.providers_pricing import PROVIDER_MAP
        for hostname, info in PROVIDER_MAP.items():
            if hostname in url:
                return info["name"]
        return None

    def test_anthropic_detected(self):
        self.assertEqual(self._detect("https://api.anthropic.com/v1/messages"), "anthropic")

    def test_openai_detected(self):
        self.assertEqual(self._detect("https://api.openai.com/v1/chat/completions"), "openai")

    def test_gemini_detected(self):
        self.assertIsNotNone(self._detect("https://generativelanguage.googleapis.com/v1beta/models"))

    def test_groq_detected(self):
        self.assertEqual(self._detect("https://api.groq.com/openai/v1/chat/completions"), "groq")

    def test_mistral_detected(self):
        self.assertEqual(self._detect("https://api.mistral.ai/v1/chat/completions"), "mistral")

    def test_together_detected(self):
        self.assertIsNotNone(self._detect("https://api.together.xyz/v1/chat/completions"))

    def test_cohere_detected(self):
        self.assertIsNotNone(self._detect("https://api.cohere.com/v2/chat"))

    def test_unknown_returns_none(self):
        self.assertIsNone(self._detect("https://example.com/api"))

    def test_non_llm_api_returns_none(self):
        self.assertIsNone(self._detect("https://maps.googleapis.com/maps/api"))


# ---------------------------------------------------------------------------
# Token / cost parsing
# ---------------------------------------------------------------------------

class TestCostParsing(unittest.TestCase):
    def setUp(self):
        from clawmetry.providers_pricing import estimate_cost_usd
        self.estimate = estimate_cost_usd

    def test_anthropic_cost_positive(self):
        cost = self.estimate("anthropic", 1000, 500)
        self.assertGreater(cost, 0)

    def test_openai_cost_positive(self):
        cost = self.estimate("openai", 1000, 500)
        self.assertGreater(cost, 0)

    def test_zero_tokens_zero_cost(self):
        cost = self.estimate("anthropic", 0, 0)
        self.assertEqual(cost, 0.0)

    def test_gpt4o_mini_cheaper_than_gpt4o(self):
        mini = self.estimate("openai", 10000, 1000, model="gpt-4o-mini")
        full = self.estimate("openai", 10000, 1000, model="gpt-4o")
        self.assertLess(mini, full)

    def test_claude_haiku_cheaper_than_opus(self):
        haiku = self.estimate("anthropic", 10000, 1000, model="claude-3-5-haiku")
        opus = self.estimate("anthropic", 10000, 1000, model="claude-3-opus")
        self.assertLess(haiku, opus)

    def test_unknown_model_does_not_raise(self):
        # Should return a value >= 0 without raising
        try:
            cost = self.estimate("anthropic", 1000, 500, model="some-future-model-xyz")
            self.assertGreaterEqual(cost, 0.0)
        except Exception as e:
            self.fail(f"estimate_cost_usd raised unexpectedly: {e}")

    def test_unknown_provider_does_not_raise(self):
        try:
            cost = self.estimate("totally-unknown-provider", 1000, 500)
            self.assertGreaterEqual(cost, 0.0)
        except Exception as e:
            self.fail(f"estimate_cost_usd raised unexpectedly for unknown provider: {e}")

    def test_sanity_1k_tokens_under_10_cents(self):
        # Even the most expensive model (claude-3-opus, $75/1M out) should be < $0.10 for 1K tokens
        cost = self.estimate("anthropic", 1000, 1000, model="claude-3-opus")
        self.assertLess(cost, 0.10)


# ---------------------------------------------------------------------------
# Interceptor response parsing
# ---------------------------------------------------------------------------

class TestResponseParsing(unittest.TestCase):
    def _parse(self, provider: str, body: bytes):
        """Call interceptor._handle_response and return what it recorded."""
        from clawmetry import interceptor
        # Reset ledger for isolation
        with interceptor._lock:
            interceptor._ledger["calls"] = 0
            interceptor._ledger["cost_usd"] = 0.0
            interceptor._ledger["tokens_in"] = 0
            interceptor._ledger["tokens_out"] = 0
            interceptor._ledger["providers"] = {}

        url_map = {
            "anthropic": "https://api.anthropic.com/v1/messages",
            "openai": "https://api.openai.com/v1/chat/completions",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/models",
        }
        url = url_map.get(provider, f"https://api.{provider}.com/v1/chat")
        interceptor._handle_response_sync(url, body)

        with interceptor._lock:
            return dict(interceptor._ledger)

    def test_anthropic_tokens_recorded(self):
        body = _make_anthropic_response("claude-3-5-sonnet-20241022", 1234, 456)
        ledger = self._parse("anthropic", body)
        self.assertEqual(ledger["calls"], 1)
        self.assertEqual(ledger["tokens_in"], 1234)
        self.assertEqual(ledger["tokens_out"], 456)
        self.assertGreater(ledger["cost_usd"], 0)

    def test_openai_tokens_recorded(self):
        body = _make_openai_response("gpt-4o", 500, 200)
        ledger = self._parse("openai", body)
        self.assertEqual(ledger["calls"], 1)
        self.assertEqual(ledger["tokens_in"], 500)
        self.assertEqual(ledger["tokens_out"], 200)

    def test_gemini_tokens_recorded(self):
        body = _make_gemini_response(800, 300)
        ledger = self._parse("gemini", body)
        self.assertEqual(ledger["calls"], 1)
        self.assertEqual(ledger["tokens_in"], 800)
        self.assertEqual(ledger["tokens_out"], 300)

    def test_empty_response_ignored(self):
        ledger = self._parse("anthropic", b"{}")
        self.assertEqual(ledger["calls"], 0)

    def test_non_json_response_ignored(self):
        ledger = self._parse("anthropic", b"not-json")
        self.assertEqual(ledger["calls"], 0)

    def test_non_llm_url_ignored(self):
        from clawmetry import interceptor
        with interceptor._lock:
            interceptor._ledger["calls"] = 0
        body = _make_anthropic_response("claude-3-5-sonnet-20241022", 100, 50)
        interceptor._handle_response_sync("https://example.com/api", body)
        with interceptor._lock:
            self.assertEqual(interceptor._ledger["calls"], 0)


# ---------------------------------------------------------------------------
# Accumulator totals (multiple calls)
# ---------------------------------------------------------------------------

class TestAccumulatorTotals(unittest.TestCase):
    def test_multiple_calls_accumulate(self):
        from clawmetry import interceptor
        with interceptor._lock:
            interceptor._ledger["calls"] = 0
            interceptor._ledger["cost_usd"] = 0.0
            interceptor._ledger["tokens_in"] = 0
            interceptor._ledger["tokens_out"] = 0
            interceptor._ledger["providers"] = {}

        for _ in range(3):
            body = _make_anthropic_response("claude-3-5-sonnet-20241022", 100, 50)
            interceptor._handle_response_sync("https://api.anthropic.com/v1/messages", body)

        with interceptor._lock:
            self.assertEqual(interceptor._ledger["calls"], 3)
            self.assertEqual(interceptor._ledger["tokens_in"], 300)
            self.assertEqual(interceptor._ledger["tokens_out"], 150)
            self.assertGreater(interceptor._ledger["cost_usd"], 0)

    def test_multi_provider_accumulate(self):
        from clawmetry import interceptor
        with interceptor._lock:
            interceptor._ledger["calls"] = 0
            interceptor._ledger["providers"] = {}

        interceptor._handle_response_sync(
            "https://api.anthropic.com/v1/messages",
            _make_anthropic_response("claude-3-5-sonnet-20241022", 100, 50),
        )
        interceptor._handle_response_sync(
            "https://api.openai.com/v1/chat/completions",
            _make_openai_response("gpt-4o", 200, 80),
        )

        with interceptor._lock:
            self.assertEqual(interceptor._ledger["calls"], 2)
            providers = interceptor._ledger["providers"]
            self.assertIn("anthropic", providers)
            self.assertIn("openai", providers)


# ---------------------------------------------------------------------------
# clawmetry.track module
# ---------------------------------------------------------------------------

class TestTrackModule(unittest.TestCase):
    def test_import_does_not_raise(self):
        """track.py must be importable without error (even with CLAWMETRY_NO_INTERCEPT=1)."""
        try:
            import importlib
            import clawmetry.track
            importlib.reload(clawmetry.track)
        except Exception as e:
            self.fail(f"import clawmetry.track raised: {e}")

    def test_get_stats_returns_dict(self):
        from clawmetry.track import get_stats
        stats = get_stats()
        # When NO_INTERCEPT=1 the interceptor is not patched but get_stats still returns a dict
        self.assertIsInstance(stats, dict)

    def test_import_idempotent(self):
        """Importing track.py multiple times must not raise."""
        try:
            import clawmetry.track  # noqa: F401
            import clawmetry.track  # noqa: F401
        except Exception as e:
            self.fail(f"double import raised: {e}")


# ---------------------------------------------------------------------------
# Graceful degradation (missing httpx / requests)
# ---------------------------------------------------------------------------

class TestGracefulDegradation(unittest.TestCase):
    def test_patch_all_without_httpx_does_not_raise(self):
        """patch_all() should not raise if httpx is absent."""
        from clawmetry import interceptor
        # Temporarily hide httpx
        with patch.dict(sys.modules, {"httpx": None}):
            try:
                # Reset patch state so patch_all runs
                interceptor._patched["httpx"] = False
                interceptor._patch_httpx()
            except Exception as e:
                self.fail(f"_patch_httpx raised without httpx: {e}")

    def test_patch_all_without_requests_does_not_raise(self):
        """patch_all() should not raise if requests is absent."""
        from clawmetry import interceptor
        with patch.dict(sys.modules, {"requests": None}):
            try:
                interceptor._patched["requests"] = False
                interceptor._patch_requests()
            except Exception as e:
                self.fail(f"_patch_requests raised without requests: {e}")


if __name__ == "__main__":
    unittest.main()
