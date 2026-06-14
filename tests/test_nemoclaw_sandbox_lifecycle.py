"""Tests for NemoClaw sandbox phase + policy surfacing (issue #3117).

Covers _read_nemoclaw_sandbox_lifecycle() and its integration into
NemoClawAdapter.detect().meta['sandboxes'].
"""
from __future__ import annotations

import importlib
import json
import time
import uuid

import pytest


_HAS_DUCKDB = False
try:
    import duckdb as _duckdb  # noqa: F401
    _HAS_DUCKDB = True
except ImportError:
    pass

requires_duckdb = pytest.mark.skipif(not _HAS_DUCKDB, reason="duckdb not installed")


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    pytest.importorskip("duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    s = _ls.LocalStore()
    s.start()
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: s)
    yield s
    s.stop(flush=True)


def _seed_event(store, *, agent_type="nemoclaw", session_id="s1"):
    store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "node-1",
        "agent_id": "main",
        "agent_type": agent_type,
        "session_id": session_id,
        "event_type": "model.completed",
        "ts": time.time(),
        "token_count": 10,
        "cost_usd": 0.001,
    })


def _wait_flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


# ── _read_nemoclaw_sandbox_lifecycle unit tests ───────────────────────────────


def test_sandbox_lifecycle_no_openshell(monkeypatch):
    """Returns {} when openshell binary is not found."""
    import shutil as _shutil
    monkeypatch.setattr(_shutil, "which", lambda _: None)
    from clawmetry.adapters.nemo import _read_nemoclaw_sandbox_lifecycle
    importlib.reload(importlib.import_module("clawmetry.adapters.nemo"))
    # Patch os.path.isfile to block the hardcoded candidates too
    import os as _os
    monkeypatch.setattr(_os.path, "isfile", lambda _: False)
    from clawmetry.adapters.nemo import _read_nemoclaw_sandbox_lifecycle as fn
    assert fn() == {}


def test_sandbox_lifecycle_json_path(tmp_path, monkeypatch):
    """Parses JSON output from openshell sandbox list --json."""
    import shutil as _shutil, subprocess as _sub, os as _os

    fake_bin = str(tmp_path / "openshell")
    monkeypatch.setattr(_shutil, "which", lambda name: fake_bin if "openshell" in name else None)
    monkeypatch.setattr(_os.path, "isfile", lambda p: p == fake_bin)

    json_out = json.dumps([
        {"name": "alpha", "phase": "Ready", "policy": "strict"},
        {"name": "beta", "status": "Pending", "policy": ""},
    ]).encode()

    def fake_check_output(cmd, **_kw):
        if "--json" in cmd:
            return json_out
        if "get" in cmd:
            return b"Policy: permissive\n"
        return b""

    monkeypatch.setattr(_sub, "check_output", fake_check_output)

    from clawmetry.adapters import nemo as _nemo
    importlib.reload(_nemo)
    result = _nemo._read_nemoclaw_sandbox_lifecycle()
    assert "sandboxes" in result
    sandboxes = result["sandboxes"]
    assert len(sandboxes) == 2
    assert sandboxes[0]["name"] == "alpha"
    assert sandboxes[0]["phase"] == "Ready"
    assert sandboxes[0]["policy"] == "strict"
    # beta has no policy in JSON → should be enriched via `sandbox get`
    assert sandboxes[1]["name"] == "beta"
    assert sandboxes[1]["phase"] == "Pending"
    assert sandboxes[1]["policy"] == "permissive"


def test_sandbox_lifecycle_text_fallback(tmp_path, monkeypatch):
    """Falls back to text parsing when --json raises."""
    import shutil as _shutil, subprocess as _sub, os as _os

    fake_bin = str(tmp_path / "openshell")
    monkeypatch.setattr(_shutil, "which", lambda name: fake_bin if "openshell" in name else None)
    monkeypatch.setattr(_os.path, "isfile", lambda p: p == fake_bin)

    def fake_check_output(cmd, **_kw):
        if "--json" in cmd:
            raise RuntimeError("no --json flag")
        if "get" in cmd:
            return b"Name: gamma\nPhase: Ready\nPolicy: open\n"
        # plain text list
        return b"gamma Ready\ndelta Error\n"

    monkeypatch.setattr(_sub, "check_output", fake_check_output)

    from clawmetry.adapters import nemo as _nemo
    importlib.reload(_nemo)
    result = _nemo._read_nemoclaw_sandbox_lifecycle()
    sandboxes = result.get("sandboxes", [])
    assert len(sandboxes) == 2
    assert sandboxes[0]["name"] == "gamma"
    assert sandboxes[0]["phase"] == "Ready"
    assert sandboxes[0]["policy"] == "open"
    assert sandboxes[1]["name"] == "delta"
    assert sandboxes[1]["phase"] == "Error"


def test_sandbox_lifecycle_empty_list(tmp_path, monkeypatch):
    """Empty openshell output → returns {}."""
    import shutil as _shutil, subprocess as _sub, os as _os

    fake_bin = str(tmp_path / "openshell")
    monkeypatch.setattr(_shutil, "which", lambda name: fake_bin if "openshell" in name else None)
    monkeypatch.setattr(_os.path, "isfile", lambda p: p == fake_bin)
    monkeypatch.setattr(_sub, "check_output", lambda *_, **__: b"[]")

    from clawmetry.adapters import nemo as _nemo
    importlib.reload(_nemo)
    assert _nemo._read_nemoclaw_sandbox_lifecycle() == {}


# ── integration: detect().meta surfaces sandboxes ────────────────────────────


def test_detect_surfaces_sandboxes_in_meta(isolated_store, monkeypatch):
    """detect().meta['sandboxes'] populated when openshell returns data."""
    import shutil as _shutil, subprocess as _sub, os as _os

    _seed_event(isolated_store)
    _wait_flush(isolated_store)

    fake_bin = "/fake/openshell"
    monkeypatch.setattr(_shutil, "which", lambda name: fake_bin if "openshell" in name else None)
    monkeypatch.setattr(_os.path, "isfile", lambda p: p == fake_bin)
    monkeypatch.setattr(_sub, "check_output", lambda cmd, **_kw: (
        json.dumps([{"name": "alpha", "phase": "Ready", "policy": "strict"}]).encode()
        if "--json" in cmd else b""
    ))

    from clawmetry.adapters import nemo as _nemo
    importlib.reload(_nemo)
    import clawmetry.local_store as _ls
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: isolated_store)

    res = _nemo.NemoClawAdapter().detect()
    assert "sandboxes" in res.meta
    assert res.meta["sandboxes"][0]["name"] == "alpha"
    assert res.meta["sandboxes"][0]["phase"] == "Ready"
    assert res.meta["sandboxes"][0]["policy"] == "strict"


def test_detect_no_sandboxes_key_when_openshell_absent(isolated_store, monkeypatch):
    """detect().meta has no 'sandboxes' key when openshell is not installed."""
    import shutil as _shutil, os as _os

    _seed_event(isolated_store)
    _wait_flush(isolated_store)

    monkeypatch.setattr(_shutil, "which", lambda _: None)
    monkeypatch.setattr(_os.path, "isfile", lambda _: False)

    from clawmetry.adapters import nemo as _nemo
    importlib.reload(_nemo)
    import clawmetry.local_store as _ls
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: isolated_store)

    res = _nemo.NemoClawAdapter().detect()
    assert "sandboxes" not in res.meta
