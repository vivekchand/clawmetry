"""Tests for clawmetry.interceptor — zero-config HTTP interceptor."""
import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def temp_openclaw_dir(tmp_path, monkeypatch):
    """Point OpenClaw dir to a temp directory so tests don't pollute real data."""
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    return tmp_path


def _fresh_interceptor(tmp_path):
    """Import interceptor in a fresh state by re-importing with patching reset."""
    import importlib
    import clawmetry.interceptor as ci
    # Reset patch state so tests are independent
    ci._patched_httpx = False
    ci._patched_requests = False
    importlib.reload(ci)
    return ci


class TestUrlDetection:
    def test_anthropic(self):
        from clawmetry import interceptor as ci
        assert ci._is_llm_url("https://api.anthropic.com/v1/messages") is True

    def test_openai(self):
        from clawmetry import interceptor as ci
        assert ci._is_llm_url("https://api.openai.com/v1/chat/completions") is True

    def test_google(self):
        from clawmetry import interceptor as ci
        assert ci._is_llm_url("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent") is True

    def test_openrouter(self):
        from clawmetry import interceptor as ci
        assert ci._is_llm_url("https://openrouter.ai/api/v1/chat/completions") is True

    def test_non_llm(self):
        from clawmetry import interceptor as ci
        assert ci._is_llm_url("https://example.com/api") is False
        assert ci._is_llm_url("https://github.com") is False
        assert ci._is_llm_url("") is False


class TestProviderDetection:
    def test_providers(self):
        from clawmetry import interceptor as ci
        assert ci._detect_provider("https://api.anthropic.com/v1/messages") == "anthropic"
        assert ci._detect_provider("https://api.openai.com/v1/chat") == "openai"
        assert ci._detect_provider("https://generativelanguage.googleapis.com") == "google"
        assert ci._detect_provider("https://openrouter.ai/api/v1") == "openrouter"


class TestModelExtraction:
    def test_from_body(self):
        from clawmetry import interceptor as ci
        body = json.dumps({"model": "claude-3-5-sonnet-20241022"}).encode()
        assert ci._extract_model_from_body(body, "") == "claude-3-5-sonnet-20241022"

    def test_google_url_fallback(self):
        from clawmetry import interceptor as ci
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
        assert ci._extract_model_from_body(b"{}", url) == "gemini-1.5-pro"

    def test_missing_body(self):
        from clawmetry import interceptor as ci
        assert ci._extract_model_from_body(b"", "") is None

    def test_invalid_json(self):
        from clawmetry import interceptor as ci
        assert ci._extract_model_from_body(b"not-json", "") is None


class TestTokenExtraction:
    def test_anthropic(self):
        from clawmetry import interceptor as ci
        body = json.dumps({"usage": {"input_tokens": 1500, "output_tokens": 250}}).encode()
        assert ci._extract_tokens_from_response(body, "anthropic") == {"input_tokens": 1500, "output_tokens": 250}

    def test_openai(self):
        from clawmetry import interceptor as ci
        body = json.dumps({"usage": {"prompt_tokens": 200, "completion_tokens": 50}}).encode()
        assert ci._extract_tokens_from_response(body, "openai") == {"input_tokens": 200, "output_tokens": 50}

    def test_openrouter(self):
        from clawmetry import interceptor as ci
        body = json.dumps({"usage": {"prompt_tokens": 100, "completion_tokens": 30}}).encode()
        assert ci._extract_tokens_from_response(body, "openrouter") == {"input_tokens": 100, "output_tokens": 30}

    def test_google(self):
        from clawmetry import interceptor as ci
        body = json.dumps({"usageMetadata": {"promptTokenCount": 300, "candidatesTokenCount": 80}}).encode()
        assert ci._extract_tokens_from_response(body, "google") == {"input_tokens": 300, "output_tokens": 80}

    def test_empty_body(self):
        from clawmetry import interceptor as ci
        assert ci._extract_tokens_from_response(b"", "anthropic") == {"input_tokens": 0, "output_tokens": 0}


class TestCostEstimation:
    def test_claude_sonnet(self):
        from clawmetry import interceptor as ci
        cost = ci._estimate_cost("claude-3-5-sonnet-20241022", 1_000_000, 0)
        assert cost == pytest.approx(3.0)

    def test_gpt4o(self):
        from clawmetry import interceptor as ci
        cost = ci._estimate_cost("gpt-4o", 1_000_000, 0)
        assert cost == pytest.approx(2.5)

    def test_unknown_model(self):
        from clawmetry import interceptor as ci
        assert ci._estimate_cost("unknown-model-xyz", 1000, 500) is None

    def test_zero_tokens(self):
        from clawmetry import interceptor as ci
        assert ci._estimate_cost("gpt-4o", 0, 0) is None


class TestEventWriting:
    def test_write_and_read(self, tmp_path):
        from clawmetry import interceptor as ci
        event = ci._build_event("anthropic", "https://api.anthropic.com/v1/messages", "claude-3-5-sonnet-20241022", 1500, 250, 523.4, 200, "httpx")
        ci._write_event(event)

        out = Path(tmp_path) / "clawmetry-intercepted.jsonl"
        assert out.exists()
        data = json.loads(out.read_text().strip())
        assert data["type"] == "llm_call"
        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-3-5-sonnet-20241022"
        assert data["input_tokens"] == 1500
        assert data["output_tokens"] == 250
        assert data["total_tokens"] == 1750
        assert "cost_usd" in data
        assert data["library"] == "httpx"
        assert data["status_code"] == 200

    def test_write_without_model(self, tmp_path):
        from clawmetry import interceptor as ci
        event = ci._build_event("openai", "https://api.openai.com/v1/chat", None, 100, 50, 200.0, 200, "requests")
        ci._write_event(event)
        out = Path(tmp_path) / "clawmetry-intercepted.jsonl"
        data = json.loads(out.read_text().strip())
        assert "model" not in data
        assert "cost_usd" not in data


class TestActivate:
    def test_activate_returns_dict(self):
        from clawmetry import interceptor as ci
        result = ci.activate()
        assert isinstance(result, dict)
        assert "httpx" in result
        assert "requests" in result
        # Both should be True since both are installed in test env
        assert result["httpx"] is True
        assert result["requests"] is True

    def test_idempotent(self):
        from clawmetry import interceptor as ci
        r1 = ci.activate()
        r2 = ci.activate()
        assert r1 == r2
