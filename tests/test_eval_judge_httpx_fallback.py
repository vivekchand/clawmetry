"""The evals judge must work without httpx (a non-dependency).

Burned 2026-06-06: `_call_judge` hard-imported `httpx` to route through the
cost interceptor, but httpx is NOT a clawmetry dependency, so on the daemon's
own venv every judge call died with "No module named 'httpx'" and no session
was ever scored. The judge now prefers httpx (cost tracking) and falls back to
stdlib urllib.
"""
import json
import sys

import clawmetry.eval_runner as er


class _Resp:
    def __init__(self, body):
        self._b = body

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_post_json_urllib_fallback_when_httpx_absent(monkeypatch):
    # Simulate httpx not installed: `import httpx` raises ImportError.
    monkeypatch.setitem(sys.modules, "httpx", None)
    import urllib.request as ur
    captured = {}

    def _fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return _Resp(json.dumps({"content": [{"text": "ok"}]}).encode())

    monkeypatch.setattr(ur, "urlopen", _fake_urlopen)
    out = er._judge_http_post_json("https://api.anthropic.com/v1/messages",
                                   {"model": "claude-haiku-4-5"}, {"x-api-key": "k"}, 5.0)
    assert out == {"content": [{"text": "ok"}]}
    assert captured["url"].startswith("https://api.anthropic.com")
    assert b"claude-haiku" in captured["data"]  # payload was JSON-encoded


def test_call_judge_anthropic_parses_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(er, "_judge_http_post_json",
                        lambda url, payload, headers, timeout: {"content": [{"text": "Score: 8"}]})
    assert er._call_judge("claude-haiku-4-5", "rate this") == "Score: 8"


def test_call_judge_openai_parses_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(er, "_judge_http_post_json",
                        lambda url, payload, headers, timeout: {"choices": [{"message": {"content": "Score: 7"}}]})
    assert er._call_judge("gpt-4o-mini", "rate this") == "Score: 7"


def test_call_judge_missing_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        er._call_judge("claude-haiku-4-5", "x")
        assert False, "expected RuntimeError for missing key"
    except RuntimeError as e:
        assert "ANTHROPIC_API_KEY" in str(e)
