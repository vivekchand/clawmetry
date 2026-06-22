"""Tests for Ollama sandbox detection in _sandbox_inference_configs() (#3201).

Covers:
- Ollama sandbox gets providerKey='ollama', ollamaHost, ollamaModels
- _resolve_ollama_host() priority: OLLAMA_HOST_DOCKER_INTERNAL > OLLAMA_LOCALHOST > default
- _list_ollama_models(): HTTP /api/tags path and ollama-list CLI fallback
- Non-Ollama sandboxes are unaffected by the new branch
"""
import json
import types
import urllib.error

import pytest

from clawmetry.adapters.openclaw import (
    _resolve_ollama_host,
    _list_ollama_models,
    _sandbox_inference_configs,
)


# ---------------------------------------------------------------------------
# _resolve_ollama_host
# ---------------------------------------------------------------------------

def test_resolve_ollama_host_prefers_docker_internal(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST_DOCKER_INTERNAL", "http://docker-host:11434")
    monkeypatch.setenv("OLLAMA_LOCALHOST", "http://other:11434")
    assert _resolve_ollama_host() == "http://docker-host:11434"


def test_resolve_ollama_host_falls_back_to_localhost_var(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST_DOCKER_INTERNAL", raising=False)
    monkeypatch.setenv("OLLAMA_LOCALHOST", "http://my-ollama:11434")
    assert _resolve_ollama_host() == "http://my-ollama:11434"


def test_resolve_ollama_host_default_when_no_vars(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST_DOCKER_INTERNAL", raising=False)
    monkeypatch.delenv("OLLAMA_LOCALHOST", raising=False)
    assert _resolve_ollama_host() == "http://localhost:11434"


def test_resolve_ollama_host_prepends_http_scheme(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST_DOCKER_INTERNAL", "172.17.0.1:11434")
    monkeypatch.delenv("OLLAMA_LOCALHOST", raising=False)
    assert _resolve_ollama_host() == "http://172.17.0.1:11434"


def test_resolve_ollama_host_bare_ip_gets_default_port(monkeypatch):
    """Bare IP/hostname without port must get :11434, not :80 (regression #3253)."""
    monkeypatch.setenv("OLLAMA_HOST_DOCKER_INTERNAL", "172.17.0.1")
    monkeypatch.delenv("OLLAMA_LOCALHOST", raising=False)
    assert _resolve_ollama_host() == "http://172.17.0.1:11434"


# ---------------------------------------------------------------------------
# _list_ollama_models — HTTP path
# ---------------------------------------------------------------------------

def _make_urlopen_mock(payload: dict):
    """Return a monkeypatch target for urllib.request.urlopen that yields payload."""
    class _FakeResp:
        def __init__(self):
            self._data = json.dumps(payload).encode()

        def read(self):
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    def _fake_urlopen(url, timeout=None):
        return _FakeResp()

    return _fake_urlopen


def test_list_ollama_models_http_success(monkeypatch):
    payload = {"models": [{"name": "llama3"}, {"name": "mistral"}]}
    monkeypatch.setattr("urllib.request.urlopen", _make_urlopen_mock(payload))
    assert _list_ollama_models("http://localhost:11434") == ["llama3", "mistral"]


def test_list_ollama_models_http_empty_list(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", _make_urlopen_mock({"models": []}))
    assert _list_ollama_models("http://localhost:11434") == []


def test_list_ollama_models_http_missing_name_skipped(monkeypatch):
    payload = {"models": [{"name": "llama3"}, {}, {"name": ""}]}
    monkeypatch.setattr("urllib.request.urlopen", _make_urlopen_mock(payload))
    assert _list_ollama_models("http://localhost:11434") == ["llama3"]


# ---------------------------------------------------------------------------
# _list_ollama_models — CLI fallback
# ---------------------------------------------------------------------------

def test_list_ollama_models_cli_fallback(monkeypatch):
    def _fail_urlopen(url, timeout=None):
        raise urllib.error.URLError("refused")

    monkeypatch.setattr("urllib.request.urlopen", _fail_urlopen)

    import subprocess as _sp

    class _FakeResult:
        stdout = "NAME\nllama3:latest\nmistral:7b\n"

    monkeypatch.setattr(_sp, "run", lambda *a, **kw: _FakeResult())
    assert _list_ollama_models("http://localhost:11434") == ["llama3:latest", "mistral:7b"]


def test_list_ollama_models_returns_empty_on_both_failures(monkeypatch):
    import subprocess as _sp

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: (_ for _ in ()).throw(OSError()))

    def _raise(*a, **kw):
        raise FileNotFoundError("ollama not found")

    monkeypatch.setattr(_sp, "run", _raise)
    assert _list_ollama_models("http://localhost:11434") == []


# ---------------------------------------------------------------------------
# _sandbox_inference_configs — Ollama sandbox
# ---------------------------------------------------------------------------

@pytest.fixture
def nemoclaw_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".nemoclaw").mkdir()
    return tmp_path


def _write_sandboxes(home, sandboxes, default=None):
    payload = {"sandboxes": sandboxes}
    if default:
        payload["defaultSandbox"] = default
    (home / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(payload))


def test_ollama_sandbox_gets_correct_provider_key(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {"local": {"provider": "ollama", "model": "llama3"}})
    monkeypatch.delenv("OLLAMA_HOST_DOCKER_INTERNAL", raising=False)
    monkeypatch.delenv("OLLAMA_LOCALHOST", raising=False)
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda *a, **kw: (_ for _ in ()).throw(OSError()))
    import subprocess as _sp
    monkeypatch.setattr(_sp, "run", lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError()))

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert "local" in configs
    c = configs["local"]
    assert c["providerKey"] == "ollama"
    assert c["primaryModelRef"] == "ollama/llama3"
    assert c["inferenceCompat"] == "openai"
    assert c["ollamaHost"] == "http://localhost:11434"
    assert c["ollamaModels"] == []


def test_ollama_sandbox_surfaces_models(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {"local": {"provider": "ollama", "model": "llama3"}})
    monkeypatch.delenv("OLLAMA_HOST_DOCKER_INTERNAL", raising=False)
    monkeypatch.delenv("OLLAMA_LOCALHOST", raising=False)
    payload = {"models": [{"name": "llama3:latest"}, {"name": "phi3"}]}
    monkeypatch.setattr("urllib.request.urlopen", _make_urlopen_mock(payload))

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["local"]["ollamaModels"] == ["llama3:latest", "phi3"]


def test_ollama_sandbox_host_from_env(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {"local": {"provider": "ollama", "model": "m"}})
    monkeypatch.setenv("OLLAMA_HOST_DOCKER_INTERNAL", "http://172.17.0.1:11434")
    monkeypatch.setattr("urllib.request.urlopen", _make_urlopen_mock({"models": []}))

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["local"]["ollamaHost"] == "http://172.17.0.1:11434"
    assert configs["local"]["inferenceBaseUrl"] == "http://172.17.0.1:11434"


def test_non_ollama_sandboxes_unaffected(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {
        "oai": {"provider": "openai-api", "model": "gpt-4o"},
        "anth": {"provider": "anthropic-prod", "model": "claude-x"},
        "managed": {"provider": "some-future-thing", "model": "m"},
    })
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["oai"]["providerKey"] == "openai"
    assert "ollamaHost" not in configs["oai"]
    assert configs["anth"]["providerKey"] == "anthropic"
    assert "ollamaHost" not in configs["anth"]
    assert configs["managed"]["providerKey"] == "inference"
    assert "ollamaHost" not in configs["managed"]


def test_ollama_sandbox_is_default(nemoclaw_home, monkeypatch):
    _write_sandboxes(
        nemoclaw_home,
        {"local": {"provider": "ollama", "model": "llama3"}},
        default="local",
    )
    monkeypatch.setattr("urllib.request.urlopen", _make_urlopen_mock({"models": []}))
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["local"]["isDefault"] is True
