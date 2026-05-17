"""Synthetic safety net for /api/skills/fidelity DuckDB fast path
(Tier-1 surface #6 in issue #1565).

``routes/usage.py::_try_local_store_skills_fidelity`` reuses the
canonical ``query_recent_read_tool_calls`` LocalStore method (already
serving ``/api/skills`` since #1378) so the two skills-fidelity
surfaces stay aligned on data source — no second walker, no schema
drift.

This file seeds DuckDB with the SAME daemon-normalised event shapes the
OSS sync daemon writes for real OpenClaw v3 sessions
(``reference_openclaw_v3_event_types.md``) and asserts:

1. Populated store + installed skill on disk returns
   ``_source='local_store'`` with the correct active/dead/stuck/orphan
   classification.
2. v3 ``assistant`` event with a ``tool_use`` Read block whose
   ``input.file_path`` ends in ``SKILL.md`` increments
   ``body_fetches`` for that skill — matches the v3 regression that
   broke ``/api/skills`` in #1385.
3. An installed skill with zero Read rows is classified ``dead``.
4. A skill with body fetches but linked files present and unread is
   classified ``stuck``.
5. A body fetch for a skill NOT on disk is classified ``orphan``.
6. When the store is empty AND no skills on disk, helper returns
   ``None`` so the legacy JSONL walker can serve its empty shape.
7. Env flag UNSET → ``_source`` tag absent (legacy walker took over).
"""

from __future__ import annotations

import importlib
import os
import time

import pytest
from flask import Flask


# ── fixtures ───────────────────────────────────────────────────────────────


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _build_app(tmp_path, monkeypatch, *, enable_fast_path: bool,
               install_demo_skill: bool = True,
               with_linked: bool = False):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_READ", "1" if enable_fast_path else "0",
    )

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Steer daemon-proxy discovery away from a developer's real install
    # so the helper falls through to the tmp_path in-process LocalStore.
    import routes.local_query as lq
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json")
    )
    lq._invalidate_daemon_cache()

    workspace = tmp_path / "workspace"
    skills_root = workspace / "skills"
    if install_demo_skill:
        skill_dir = skills_root / "demo-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: demo-skill\n---\nbody\n")
        if with_linked:
            (skill_dir / "helper.py").write_text("print('hi')\n")
    else:
        skills_root.mkdir(parents=True)

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    import dashboard as _d
    monkeypatch.setattr(_d, "WORKSPACE", str(workspace), raising=False)
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(sessions_dir), raising=False)
    monkeypatch.setattr(
        _d, "_get_sessions_dir", lambda: str(sessions_dir), raising=False,
    )

    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    return app, ls, str(workspace)


def _ingest_v3_assistant_read(store, *, sid: str, ts: str, file_path: str,
                              ev_id: str | None = None):
    """v3 real-shape: ``assistant`` event carrying a ``tool_use`` Read
    block inside ``data.message.content`` (Anthropic-SDK echo shape).
    """
    if ev_id is None:
        ev_id = f"asst-{sid}-{ts}-{abs(hash(file_path))}"
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "assistant",
        "ts":         ts,
        "data": {
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": "claude-opus-4-7",
                "content": [
                    {
                        "type":  "tool_use",
                        "id":    "toolu_01",
                        "name":  "Read",
                        "input": {"file_path": file_path},
                    },
                ],
            },
        },
        "model": "claude-opus-4-7",
    })


# ── happy paths ────────────────────────────────────────────────────────────


def test_fidelity_fast_path_active_skill(tmp_path, monkeypatch):
    """One installed skill + two body-fetches for it in the trailing 7d
    → status=active, _source=local_store."""
    app, ls, workspace = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    store = ls.get_store()
    sm = os.path.join(workspace, "skills", "demo-skill", "SKILL.md")
    ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _ingest_v3_assistant_read(store, sid="s1", ts=ts_now, file_path=sm)
    _ingest_v3_assistant_read(store, sid="s2", ts=ts_now, file_path=sm,
                               ev_id="asst-2")
    _wait_flush(store)

    body = app.test_client().get("/api/skills/fidelity").get_json()
    assert body["_source"] == "local_store"
    assert body["total_installed"] == 1
    by_name = {s["name"]: s for s in body["skills"]}
    assert "demo-skill" in by_name
    assert by_name["demo-skill"]["body_fetches"] == 2
    assert by_name["demo-skill"]["sessions_seen"] == 2
    assert by_name["demo-skill"]["status"] == "active"
    assert body["active_count"] >= 1


def test_fidelity_fast_path_dead_when_installed_but_no_fetch(tmp_path, monkeypatch):
    """Installed skill with zero Read rows → dead."""
    app, ls, _workspace = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    # Force a flush of the empty store so query_recent_read_tool_calls
    # returns [] (not None) and the helper proceeds with disk-only data.
    _wait_flush(ls.get_store())

    body = app.test_client().get("/api/skills/fidelity").get_json()
    assert body["_source"] == "local_store"
    by_name = {s["name"]: s for s in body["skills"]}
    assert by_name["demo-skill"]["status"] == "dead"
    assert body["dead_count"] == 1


def test_fidelity_fast_path_stuck_when_linked_files_unread(tmp_path, monkeypatch):
    """Body fetched + linked file on disk + zero linked-fetch rows → stuck."""
    app, ls, workspace = _build_app(
        tmp_path, monkeypatch, enable_fast_path=True, with_linked=True,
    )
    store = ls.get_store()
    sm = os.path.join(workspace, "skills", "demo-skill", "SKILL.md")
    ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _ingest_v3_assistant_read(store, sid="s1", ts=ts_now, file_path=sm)
    _wait_flush(store)

    body = app.test_client().get("/api/skills/fidelity").get_json()
    assert body["_source"] == "local_store"
    by_name = {s["name"]: s for s in body["skills"]}
    assert by_name["demo-skill"]["status"] == "stuck"
    assert body["stuck_count"] == 1


def test_fidelity_fast_path_orphan_when_skill_not_installed(tmp_path, monkeypatch):
    """Body fetch for a skill NOT on disk → orphan."""
    app, ls, _workspace = _build_app(
        tmp_path, monkeypatch, enable_fast_path=True, install_demo_skill=False,
    )
    store = ls.get_store()
    ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _ingest_v3_assistant_read(
        store, sid="s1", ts=ts_now,
        file_path="/random/path/skills/ghost-skill/SKILL.md",
    )
    _wait_flush(store)

    body = app.test_client().get("/api/skills/fidelity").get_json()
    assert body["_source"] == "local_store"
    by_name = {s["name"]: s for s in body["skills"]}
    assert "ghost-skill" in by_name
    assert by_name["ghost-skill"]["status"] == "orphan"
    assert by_name["ghost-skill"]["installed"] is False
    assert body["orphan_count"] == 1


def test_fidelity_fast_path_defers_when_empty_store_and_no_skills(
    tmp_path, monkeypatch,
):
    """No skills on disk AND zero Read rows → helper returns None so
    the legacy JSONL walker serves the empty-shape response."""
    app, ls, _workspace = _build_app(
        tmp_path, monkeypatch, enable_fast_path=True, install_demo_skill=False,
    )
    _wait_flush(ls.get_store())

    body = app.test_client().get("/api/skills/fidelity").get_json()
    # Legacy walker took over → no _source tag.
    assert body.get("_source") != "local_store"
    assert body["total_installed"] == 0


def test_fidelity_legacy_when_env_unset(tmp_path, monkeypatch):
    """Env flag UNSET → fast path skipped entirely (no _source tag),
    even though events exist."""
    app, _ls, _workspace = _build_app(
        tmp_path, monkeypatch, enable_fast_path=False,
    )
    body = app.test_client().get("/api/skills/fidelity").get_json()
    assert body.get("_source") != "local_store"
    # Legacy shape contract still upheld.
    for k in ("skills", "dead_count", "stuck_count", "active_count",
              "orphan_count", "total_installed"):
        assert k in body
