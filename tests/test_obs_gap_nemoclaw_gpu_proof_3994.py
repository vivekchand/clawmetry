"""Tests for sandboxGpuProof surfacing in _sandbox_inference_configs() (#3994).

Covers:
- verified/unverified/failed GPU proof status is passed through to the output
- missing sandboxGpuProof key → key absent from result (no KeyError)
- non-dict sandboxGpuProof value is ignored (robustness)
- GPU proof surfaced on both ollama and non-ollama sandboxes
"""
import json
import urllib.error

import pytest

from clawmetry.adapters.openclaw import _sandbox_inference_configs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_sandboxes(home, sandboxes, default=None):
    payload = {"sandboxes": sandboxes}
    if default:
        payload["defaultSandbox"] = default
    (home / ".nemoclaw").mkdir(exist_ok=True)
    (home / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(payload))


@pytest.fixture
def nemoclaw_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".nemoclaw").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# GPU proof on non-ollama sandboxes
# ---------------------------------------------------------------------------

def test_gpu_proof_verified_surfaced_on_openai_sandbox(nemoclaw_home):
    proof = {"status": "verified", "cudaVerified": True, "label": "CUDA OK", "detail": "", "at": 1234567890}
    _write_sandboxes(nemoclaw_home, {
        "gpu-box": {"provider": "openai-api", "model": "gpt-4o", "sandboxGpuProof": proof},
    })
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert "gpu-box" in configs
    assert configs["gpu-box"]["sandboxGpuProof"] == proof
    assert configs["gpu-box"]["sandboxGpuProof"]["status"] == "verified"


def test_gpu_proof_failed_surfaced_with_detail(nemoclaw_home):
    proof = {
        "status": "failed",
        "cudaVerified": False,
        "label": "Jetson /dev/nvmap denied",
        "detail": "NvRmMemInitNvmap permission denied",
        "at": 9876543210,
    }
    _write_sandboxes(nemoclaw_home, {
        "jetson": {"provider": "anthropic-prod", "model": "claude-3-5-sonnet", "sandboxGpuProof": proof},
    })
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["jetson"]["sandboxGpuProof"]["status"] == "failed"
    assert configs["jetson"]["sandboxGpuProof"]["cudaVerified"] is False
    assert "Nvmap" in configs["jetson"]["sandboxGpuProof"]["detail"]


def test_gpu_proof_unverified_surfaced(nemoclaw_home):
    proof = {"status": "unverified", "cudaVerified": False, "label": "", "detail": "", "at": 0}
    _write_sandboxes(nemoclaw_home, {
        "pending": {"provider": "some-managed", "model": "m", "sandboxGpuProof": proof},
    })
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert configs["pending"]["sandboxGpuProof"]["status"] == "unverified"


def test_no_gpu_proof_key_absent_from_result(nemoclaw_home):
    _write_sandboxes(nemoclaw_home, {
        "cpu-box": {"provider": "openai-api", "model": "gpt-4o"},
    })
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert "sandboxGpuProof" not in configs["cpu-box"]


def test_non_dict_gpu_proof_ignored(nemoclaw_home):
    _write_sandboxes(nemoclaw_home, {
        "bad": {"provider": "openai-api", "model": "gpt-4o", "sandboxGpuProof": "not-a-dict"},
    })
    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert "sandboxGpuProof" not in configs["bad"]


# ---------------------------------------------------------------------------
# GPU proof on ollama sandboxes
# ---------------------------------------------------------------------------

def test_gpu_proof_surfaced_on_ollama_sandbox(nemoclaw_home, monkeypatch):
    proof = {"status": "verified", "cudaVerified": True, "label": "RTX OK", "detail": "", "at": 111}
    _write_sandboxes(nemoclaw_home, {
        "gpu-ollama": {"provider": "ollama", "model": "llama3", "sandboxGpuProof": proof},
    })
    monkeypatch.delenv("OLLAMA_HOST_DOCKER_INTERNAL", raising=False)
    monkeypatch.delenv("OLLAMA_LOCALHOST", raising=False)
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **kw: (_ for _ in ()).throw(OSError()),
    )
    import subprocess as _sp
    monkeypatch.setattr(_sp, "run", lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError()))

    configs = {c["sandbox"]: c for c in _sandbox_inference_configs()}
    assert "gpu-ollama" in configs
    assert configs["gpu-ollama"]["sandboxGpuProof"] == proof
