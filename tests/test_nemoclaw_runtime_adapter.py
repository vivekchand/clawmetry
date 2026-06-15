"""Tests for ``NemoClawAdapter`` (Phase 4.5 read-side facade).

The push-side ``NeMoAdapter`` keeps ingesting events into DuckDB; the
new facade makes those events queryable through the standard
:class:`AgentAdapter` shape so:

* /api/agents lists "nemoclaw" alongside openclaw + paid runtimes
* The header runtime switcher can filter to NeMo
* The homepage tooltip "OpenClaw + NemoClaw" stops being a lie

These pin the facade contract: detect/list_sessions/list_events query
DuckDB by ``agent_type='nemoclaw'`` and return the shapes the dashboard
expects.
"""
from __future__ import annotations

import importlib
import time
import uuid

import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Fresh LocalStore at a tmp path so tests don't read the dev DuckDB.

    The adapter calls ``local_store.get_store(read_only=True)`` to fetch
    the singleton; we patch it to return our test instance so the read
    path sees the events we ingest in tests."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("HOME", str(tmp_path))  # daemon-detection shield
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    s = _ls.LocalStore()
    s.start()
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: s)
    yield s
    s.stop(flush=True)


def _seed_nemoclaw_event(store, *, session_id="nemo-sess-1", event_type="model.completed"):
    event_id = str(uuid.uuid4())
    store.ingest({
        "id": event_id,
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "nemoclaw",
        "session_id": session_id,
        "event_type": event_type,
        "ts": time.time(),
        "model": "nv/llama3-70b",
        "data": {"role": "assistant", "content": "hi"},
        "token_count": 42,
        "cost_usd": 0.001,
    })


def _wait_flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


# ── detect ────────────────────────────────────────────────────────────────────────────────


def test_nemoclaw_detect_false_when_no_events(isolated_store):
    """Empty store -> detected=False so we don't clutter /api/agents."""
    from clawmetry.adapters.nemo import NemoClawAdapter
    res = NemoClawAdapter().detect()
    assert res.detected is False
    assert res.name == "nemoclaw"
    assert res.display_name == "NemoClaw"


def test_nemoclaw_detect_true_after_ingest(isolated_store):
    _seed_nemoclaw_event(isolated_store)
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NemoClawAdapter
    res = NemoClawAdapter().detect()
    assert res.detected is True
    assert res.meta["event_count"] == 1


# ── list_sessions ───────────────────────────────────────────────────────────────────────────


def test_nemoclaw_list_sessions_groups_by_session_id(isolated_store):
    _seed_nemoclaw_event(isolated_store, session_id="sess-a")
    _seed_nemoclaw_event(isolated_store, session_id="sess-a", event_type="model.completed")
    _seed_nemoclaw_event(isolated_store, session_id="sess-b")
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NemoClawAdapter
    sessions = NemoClawAdapter().list_sessions()
    ids = {s.id for s in sessions}
    assert ids == {"sess-a", "sess-b"}
    sess_a = next(s for s in sessions if s.id == "sess-a")
    assert sess_a.message_count == 2
    assert sess_a.total_tokens == 84  # 42 + 42


# ── list_events ──────────────────────────────────────────────────────────────────────────


def test_nemoclaw_list_events_for_session(isolated_store):
    _seed_nemoclaw_event(isolated_store, session_id="sess-c", event_type="prompt.submitted")
    _seed_nemoclaw_event(isolated_store, session_id="sess-c", event_type="model.completed")
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NemoClawAdapter
    events = NemoClawAdapter().list_events("sess-c")
    types = [e.type for e in events]
    assert set(types) == {"prompt.submitted", "model.completed"}
    assert all(e.agent == "nemoclaw" for e in events)


# ── capabilities ───────────────────────────────────────────────────────────────────────────


def test_nemoclaw_capabilities():
    from clawmetry.adapters.nemo import NemoClawAdapter
    from clawmetry.adapters.base import Capability
    caps = NemoClawAdapter().capabilities()
    assert Capability.SESSIONS in caps
    assert Capability.EVENTS in caps
    assert Capability.BRAIN in caps
    assert Capability.COST in caps
    assert Capability.SKILLS in caps


# ── skill catalog metadata (issue #2610) ─────────────────────────────────────────────


def test_nemoclaw_detect_surfaces_skill_catalog_meta(isolated_store, tmp_path, monkeypatch):
    """detect() merges skill catalog version fields into meta when catalog-metadata.json exists."""
    import json as _json
    from pathlib import Path

    catalog_dir = tmp_path / ".nemoclaw" / "skills"
    catalog_dir.mkdir(parents=True)
    catalog_path = catalog_dir / "catalog-metadata.json"
    catalog_path.write_text(_json.dumps({
        "metadata": {
            "minNemoClawVersion": "1.2.0",
            "testedNemoClawVersion": "1.4.1",
            "sourceCommit": "deadbeef",
            "schemaVersion": "2.1",
        },
        "exportContentSha256": "abc123",
        "sourceContentSha256": "def456",
        "skills": ["search", {"name": "summarise"}, {"id": "classify"}],
    }))

    _seed_nemoclaw_event(isolated_store)
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    res = NemoClawAdapter().detect()
    assert res.meta["skill_catalog_min_version"] == "1.2.0"
    assert res.meta["skill_catalog_tested_version"] == "1.4.1"
    assert res.meta["skill_catalog_source_commit"] == "deadbeef"
    assert res.meta["skill_catalog_export_sha256"] == "abc123"
    assert res.meta["skill_catalog_source_sha256"] == "def456"
    assert res.meta["skill_catalog_schema_version"] == "2.1"
    assert res.meta["skill_catalog_skill_names"] == ["search", "summarise", "classify"]


def test_nemoclaw_detect_no_catalog_meta_when_file_absent(isolated_store):
    """detect() works normally and emits no skill_catalog_* keys when no catalog file exists."""
    _seed_nemoclaw_event(isolated_store)
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    res = NemoClawAdapter().detect()
    assert "skill_catalog_min_version" not in res.meta


def test_nemoclaw_extract_skill_names_tolerates_mixed_shapes():
    """_extract_skill_names handles str entries, dict-with-name, dict-with-id, dict-with-skillName."""
    from clawmetry.adapters.nemo import _extract_skill_names
    raw = {
        "skills": [
            "plain_string",
            {"name": "by_name"},
            {"id": "by_id"},
            {"skillName": "by_skillName"},
            {},  # empty dict — should be skipped
            {"unrelated": "key"},  # no name/id/skillName — skipped
        ]
    }
    assert _extract_skill_names(raw) == ["plain_string", "by_name", "by_id", "by_skillName"]


# ── isolation: doesn't pick up non-nemo runtimes ───────────────────────────────────────


# ── model-router model_list (issue #3118) ───────────────────────────────────


def test_nemoclaw_detect_surfaces_model_router_model_list(isolated_store, tmp_path, monkeypatch):
    """detect() merges modelRouterModelList when a proxy-config YAML exists."""
    config_path = tmp_path / ".nemoclaw" / "model-router-config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "model_list:\n  - model_name: gpt-4o\n  - model_name: claude-3-haiku\n"
    )
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_CONFIG", str(config_path))

    _seed_nemoclaw_event(isolated_store)
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    res = NemoClawAdapter().detect()
    assert res.meta["modelRouterModelList"] == ["gpt-4o", "claude-3-haiku"]
    assert res.meta["modelRouterModelCount"] == 2


def test_nemoclaw_detect_no_model_list_when_config_absent(isolated_store, tmp_path, monkeypatch):
    """detect() emits no modelRouter* keys when no proxy-config file exists."""
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_CONFIG", "")
    # Point HOME at an empty tmp dir so no candidate path can accidentally resolve
    monkeypatch.setenv("HOME", str(tmp_path))

    _seed_nemoclaw_event(isolated_store)
    _wait_flush(isolated_store)

    from clawmetry.adapters.nemo import NemoClawAdapter
    res = NemoClawAdapter().detect()
    assert "modelRouterModelList" not in res.meta
    assert "modelRouterModelCount" not in res.meta


def test_nemoclaw_model_list_regex_fallback(tmp_path, monkeypatch):
    """_read_model_router_model_list() regex path extracts model names from raw YAML text."""
    import re

    config_text = (
        "model_list:\n"
        "  - model_name: llama-3-70b\n"
        "    provider: ollama\n"
        "  - model_name: mistral-7b\n"
    )
    # Verify the regex pattern that the helper uses produces the expected names
    names = re.findall(r"model_name:\s*(.+?)(?:\s|$)", config_text)
    assert names == ["llama-3-70b", "mistral-7b"]

    # Also verify the helper returns the same result end-to-end via config file
    config_path = tmp_path / "proxy-config.yaml"
    config_path.write_text(config_text)
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_CONFIG", str(config_path))

    from clawmetry.adapters.nemo import _read_model_router_model_list
    result = _read_model_router_model_list()
    assert result.get("modelRouterModelList") == ["llama-3-70b", "mistral-7b"]
    assert result.get("modelRouterModelCount") == 2


# ── isolation: doesn't pick up non-nemo runtimes ────────────────────────────


def test_nemoclaw_ignores_non_nemo_events(isolated_store):
    """A claude_code event seeded into the same store must NOT make NeMo
    detect True. agent_type is the discriminator."""
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "claude_code",
        "session_id": "cc-sess",
        "event_type": "model.completed",
        "ts": time.time(),
    })
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NemoClawAdapter
    assert NemoClawAdapter().detect().detected is False


# ── obs-gap #2959: Ollama inference host + local model roster ────────────────


def test_resolve_ollama_host_loopback(monkeypatch):
    """No OLLAMA_HOST and not in docker -> loopback host."""
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_IN_DOCKER", raising=False)
    monkeypatch.setattr("os.path.exists", lambda p: False)
    from clawmetry.adapters.nemo import _resolve_ollama_host, _OLLAMA_LOCALHOST
    host, mode = _resolve_ollama_host()
    assert host == _OLLAMA_LOCALHOST
    assert mode == "loopback"


def test_resolve_ollama_host_docker(monkeypatch):
    """Inside a container (/.dockerenv present) -> docker-internal host."""
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.setattr("os.path.exists", lambda p: p == "/.dockerenv")
    from clawmetry.adapters.nemo import _resolve_ollama_host, _OLLAMA_HOST_DOCKER_INTERNAL
    host, mode = _resolve_ollama_host()
    assert host == _OLLAMA_HOST_DOCKER_INTERNAL
    assert mode == "docker-internal"


def test_resolve_ollama_host_explicit_normalises_scheme(monkeypatch):
    """An explicit OLLAMA_HOST wins and a bare host:port gets an http:// scheme."""
    monkeypatch.setenv("OLLAMA_HOST", "ollama.internal:11434")
    from clawmetry.adapters.nemo import _resolve_ollama_host
    host, mode = _resolve_ollama_host()
    assert host == "http://ollama.internal:11434"
    assert mode == "explicit"


def test_ollama_inference_roster_parsed(monkeypatch):
    """When /api/tags answers, the model roster is sorted + de-duplicated."""
    import json as _json

    class _FakeResp:
        def __init__(self, body):
            self._b = body.encode("utf-8")
        def read(self):
            return self._b
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    payload = {"models": [{"name": "llama3:8b"}, {"name": "qwen2:7b"}, {"name": "llama3:8b"}]}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, timeout=0: _FakeResp(_json.dumps(payload)),
    )
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.setattr("os.path.exists", lambda p: False)
    from clawmetry.adapters.nemo import _read_nemoclaw_ollama_inference
    info = _read_nemoclaw_ollama_inference()
    assert info["ollama_host_mode"] == "loopback"
    assert info["ollama_local_models"] == ["llama3:8b", "qwen2:7b"]


def test_ollama_inference_unreachable_still_returns_host(monkeypatch):
    """When Ollama is unreachable, host/mode are still surfaced, no roster key."""
    def _boom(url, timeout=0):
        raise OSError("connection refused")
    monkeypatch.setattr("urllib.request.urlopen", _boom)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.setattr("os.path.exists", lambda p: False)
    from clawmetry.adapters.nemo import _read_nemoclaw_ollama_inference
    info = _read_nemoclaw_ollama_inference()
    assert "ollama_host" in info and "ollama_host_mode" in info
    assert "ollama_local_models" not in info


def test_detect_meta_includes_ollama_inference(isolated_store, monkeypatch):
    """detect().meta carries ollama_inference with host + mode (gap #2959)."""
    def _boom(url, timeout=0):
        raise OSError("connection refused")
    monkeypatch.setattr("urllib.request.urlopen", _boom)
    _seed_nemoclaw_event(isolated_store)
    _wait_flush(isolated_store)
    from clawmetry.adapters.nemo import NemoClawAdapter
    meta = NemoClawAdapter().detect().meta
    assert "ollama_inference" in meta
    assert "ollama_host" in meta["ollama_inference"]
    assert "ollama_host_mode" in meta["ollama_inference"]
