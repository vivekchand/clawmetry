"""Tests for vLLM sandbox detection in _sandbox_inference_configs() (#5579).

Covers:
- _resolve_vllm_base_url() priority: VLLM_HOST > default http://localhost:8000/v1
- vLLM sandbox gets providerKey='vllm', correct primaryModelRef, inferenceBaseUrl
- provider strings "vllm" and "vllm-server" both match the new branch
- Non-vLLM sandboxes are unaffected by the new branch
"""
import json

import pytest

from clawmetry.adapters.openclaw import (
    _resolve_vllm_base_url,
    _sandbox_inference_configs,
)


# ---------------------------------------------------------------------------
# _resolve_vllm_base_url
# ---------------------------------------------------------------------------

def test_resolve_vllm_base_url_default(monkeypatch):
    monkeypatch.delenv("VLLM_HOST", raising=False)
    assert _resolve_vllm_base_url() == "http://localhost:8000/v1"


def test_resolve_vllm_base_url_from_env(monkeypatch):
    monkeypatch.setenv("VLLM_HOST", "http://192.168.1.10:8000/v1")
    assert _resolve_vllm_base_url() == "http://192.168.1.10:8000/v1"


def test_resolve_vllm_base_url_strips_whitespace(monkeypatch):
    monkeypatch.setenv("VLLM_HOST", "  http://my-vllm:8000/v1  ")
    assert _resolve_vllm_base_url() == "http://my-vllm:8000/v1"


def test_resolve_vllm_base_url_empty_env_falls_back(monkeypatch):
    monkeypatch.setenv("VLLM_HOST", "")
    assert _resolve_vllm_base_url() == "http://localhost:8000/v1"


# ---------------------------------------------------------------------------
# _sandbox_inference_configs — vLLM sandbox
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


def test_vllm_sandbox_gets_correct_provider_key(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {"local": {"provider": "vllm", "model": "mistral-7b"}})
    monkeypatch.delenv("VLLM_HOST", raising=False)

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert "local" in configs
    c = configs["local"]
    assert c["providerKey"] == "vllm"
    assert c["primaryModelRef"] == "vllm/mistral-7b"
    assert c["inferenceCompat"] == "openai"
    assert c["inferenceBaseUrl"] == "http://localhost:8000/v1"


def test_vllm_server_provider_string_also_matches(nemoclaw_home, monkeypatch):
    """The 'vllm-server' alias is also recognised (#5579)."""
    _write_sandboxes(nemoclaw_home, {"srv": {"provider": "vllm-server", "model": "llama3"}})
    monkeypatch.delenv("VLLM_HOST", raising=False)

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["srv"]["providerKey"] == "vllm"
    assert configs["srv"]["primaryModelRef"] == "vllm/llama3"


def test_vllm_sandbox_base_url_from_env(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {"gpu": {"provider": "vllm", "model": "qwen"}})
    monkeypatch.setenv("VLLM_HOST", "http://gpu-node:8000/v1")

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["gpu"]["inferenceBaseUrl"] == "http://gpu-node:8000/v1"


def test_vllm_sandbox_no_model_gives_empty_primary_ref(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {"bare": {"provider": "vllm"}})
    monkeypatch.delenv("VLLM_HOST", raising=False)

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["bare"]["primaryModelRef"] == ""


def test_vllm_sandbox_is_default(nemoclaw_home, monkeypatch):
    _write_sandboxes(
        nemoclaw_home,
        {"local": {"provider": "vllm", "model": "phi3"}},
        default="local",
    )
    monkeypatch.delenv("VLLM_HOST", raising=False)
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["local"]["isDefault"] is True


def test_non_vllm_sandboxes_unaffected(nemoclaw_home, monkeypatch):
    _write_sandboxes(nemoclaw_home, {
        "oai": {"provider": "openai-api", "model": "gpt-4o"},
        "anth": {"provider": "anthropic-prod", "model": "claude-x"},
        "managed": {"provider": "some-future-thing", "model": "m"},
    })
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["oai"]["providerKey"] == "openai"
    assert configs["anth"]["providerKey"] == "anthropic"
    assert configs["managed"]["providerKey"] == "inference"
    for key in ("oai", "anth", "managed"):
        assert configs[key]["providerKey"] != "vllm"
