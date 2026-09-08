"""Multi-provider judge tests (founder ask 2026-07-31: "should work with
various models -- not just claude" + issue #4313 validate-on-save).

Covers:
  1. Wire routing: each provider hits its endpoint with the right auth header
     and token-limit field (OpenAI gets max_completion_tokens; OpenAI-compatible
     servers keep max_tokens).
  2. Provider resolution: explicit rubric judge_provider wins; else inference
     from the model id (gpt-* / gemini* / vendor-slash / default anthropic).
  3. validate_judge_key: ok on a working reply, plain-language failures on
     401 (auth) and missing config; nothing is written by validation.
  4. set_judge_selection: rewrites judge_provider + judge_model in the rubric
     YAML while preserving the prompt.
  5. Key store: custom provider counts as configured with only a base URL.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import eval_runner as er  # noqa: E402


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """No env keys, empty key store, empty rubric file — a fresh box."""
    monkeypatch.setattr(er, "_EVAL_KEYS_PATH", str(tmp_path / "eval_keys.json"))
    monkeypatch.setattr(er, "RUBRIC_PATH", tmp_path / "evals.yaml")
    for env in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
                "GOOGLE_API_KEY", "OPENROUTER_API_KEY",
                "CLAWMETRY_JUDGE_API_KEY", "CLAWMETRY_JUDGE_BASE_URL"):
        monkeypatch.delenv(env, raising=False)
    return tmp_path


class _Capture:
    def __init__(self, reply):
        self.calls = []
        self.reply = reply

    def __call__(self, url, payload, headers, timeout):
        self.calls.append({"url": url, "payload": payload, "headers": headers})
        return self.reply


def test_wire_shapes_per_provider(isolated, monkeypatch):
    cases = [
        ("anthropic", "claude-haiku-4-5", {"content": [{"type": "text", "text": "SCORE: 5"}]},
         "api.anthropic.com/v1/messages", "x-api-key", "max_tokens"),
        ("openai", "gpt-5-mini", {"choices": [{"message": {"content": "SCORE: 5"}}]},
         "api.openai.com/v1/chat/completions", "Authorization", "max_completion_tokens"),
        ("google", "gemini-2.5-flash",
         {"candidates": [{"content": {"parts": [{"text": "SCORE: 5"}]}}]},
         "generativelanguage.googleapis.com", "x-goog-api-key", None),
        ("openrouter", "meta-llama/llama-3.3-70b",
         {"choices": [{"message": {"content": "SCORE: 5"}}]},
         "openrouter.ai/api/v1/chat/completions", "Authorization", "max_tokens"),
    ]
    for provider, model, reply, url_frag, auth_header, limit_field in cases:
        cap = _Capture(reply)
        monkeypatch.setattr(er, "_judge_http_post_json", cap)
        out = er._judge_request(provider, model, "hi", api_key="k-test")
        assert "SCORE: 5" in out, provider
        call = cap.calls[0]
        assert url_frag in call["url"], provider
        assert auth_header in call["headers"], provider
        if limit_field:
            assert limit_field in call["payload"], provider


def test_custom_provider_uses_base_url_and_optional_key(isolated, monkeypatch):
    cap = _Capture({"choices": [{"message": {"content": "OK"}}]})
    monkeypatch.setattr(er, "_judge_http_post_json", cap)
    out = er._judge_request("custom", "llama3.1", "hi", api_key="",
                            base_url="http://localhost:11434/v1")
    assert out == "OK"
    call = cap.calls[0]
    assert call["url"] == "http://localhost:11434/v1/chat/completions"
    assert "Authorization" not in call["headers"]  # keyless local server
    with pytest.raises(RuntimeError):
        er._judge_request("custom", "llama3.1", "hi", api_key="")  # no base URL


def test_rubric_provider_wins_over_inference(isolated, monkeypatch):
    er.save_rubric_yaml(
        "default:\n"
        "  judge_model: my-team-model\n"
        "  judge_provider: openrouter\n"
    )
    assert er.judge_provider_for() == "openrouter"
    # A different model than the configured judge falls back to inference.
    assert er._provider_for_model("gpt-5-mini") == "openai"
    assert er._provider_for_model("gemini-2.5-flash") == "google"
    assert er._provider_for_model("vendor/some-model") == "openrouter"
    assert er._provider_for_model("claude-haiku-4-5") == "anthropic"


def test_validate_judge_key_paths(isolated, monkeypatch):
    calls = {}

    def fake_request(provider, model, prompt, **kw):
        calls["provider"] = provider
        calls["model"] = model
        return "OK"

    monkeypatch.setattr(er, "_judge_request", fake_request)
    ok, detail = er.validate_judge_key("openai", api_key="sk-x", model="gpt-5-mini")
    assert ok and detail == ""
    assert calls == {"provider": "openai", "model": "gpt-5-mini"}
    # Validation must not persist anything.
    assert not os.path.exists(er._EVAL_KEYS_PATH)

    class _Resp:
        status_code = 401

    class _AuthError(Exception):
        response = _Resp()

    def bad_request(provider, model, prompt, **kw):
        raise _AuthError("401 Unauthorized")

    monkeypatch.setattr(er, "_judge_request", bad_request)
    ok, detail = er.validate_judge_key("anthropic", api_key="sk-ant-bad")
    assert not ok
    assert "rejected" in detail

    ok, detail = er.validate_judge_key("not-a-provider")
    assert not ok and "unknown provider" in detail


def test_set_judge_selection_preserves_prompt(isolated):
    er.save_rubric_yaml(er.DEFAULT_RUBRIC_YAML)
    er.set_judge_selection("google", "gemini-2.5-flash")
    rubric = er.load_rubric("default")
    assert rubric["judge_model"] == "gemini-2.5-flash"
    assert er.judge_provider_for(rubric) == "google"
    # The scoring prompt survives the rewrite.
    assert "SCORE:" in rubric["prompt"]
    # Second switch updates in place (no duplicate keys).
    er.set_judge_selection("openrouter", "vendor/model-x")
    text = er.get_rubric_yaml()
    assert text.count("judge_provider:") == 1
    assert text.count("judge_model:") == 1
    assert er.load_rubric("default")["judge_model"] == "vendor/model-x"


def test_custom_counts_as_configured_with_base_url_only(isolated):
    assert er.judge_keys_present()["custom"] is False
    er.save_judge_key("custom", "", base_url="http://localhost:11434/v1")
    present = er.judge_keys_present()
    assert present["custom"] is True
    assert er.judge_base_url() == "http://localhost:11434/v1"
    # Clearing the base URL deconfigures it again.
    er.save_judge_key("custom", "", base_url="")
    assert er.judge_keys_present()["custom"] is False
