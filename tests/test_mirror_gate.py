"""The Claude Code permission-prompt mirror — the OSS half.

The mirror INSTALLER (``clawmetry/claude_code_gate.py``) and RECEIVER
(``routes/hooks.py``) stay open source: they are the code that touches the
user's Claude Code settings and answers its hook, and OSS owns everything
that pauses an agent. What they no longer own is the DECISION to arm — that
comes from the paid delivery layer through ``clawmetry.approval_events``.

So these tests drive the SEAM, not a routing config: a fake handler stands
in for clawmetry-pro. That is also the honest shape of the contract — OSS
must behave correctly for any answer, from any implementation, including
none at all.

  1. receiver — off → ask, approved → allow, denied → deny, window elapsed
     → ask (the terminal prompt takes over).
  2. installer — installs only when armed, never touches a foreign
     PermissionRequest hook, idempotent, and arms with zero protection
     rules (mirroring is about the runtime's OWN prompts, not your rules).
  3. the unlicensed path — nothing registered means nothing installed.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import threading
import time

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def seam(monkeypatch):
    """A clean extension registry standing in for the paid layer.

    ``arm(window)`` registers handlers that answer like clawmetry-pro would;
    leaving it unarmed is the unlicensed node.

    MUST clear the registry on the way out. ``clawmetry.extensions``
    registrations are module-global and monkeypatch cannot undo them, so a
    leaked ``MIRROR_WANTED → True`` makes every later ``gate_handler`` call
    in the session install a mirror hook — which is exactly how this
    fixture broke two unrelated gate tests the first time round.
    """
    import clawmetry.extensions as ext
    importlib.reload(ext)
    import clawmetry.approval_events as ev
    importlib.reload(ev)
    monkeypatch.setattr(ev, "extensions", ext)
    monkeypatch.setattr(ev, "_ensure_local_handlers", lambda: None)

    class Seam:
        module = ev

        def arm(self, window=120):
            ext.register(ev.MIRROR_WANTED, lambda p: True)
            ext.register(ev.MIRROR_WINDOW, lambda p: window)

        def pages(self):
            seen = []
            ext.register(ev.APPROVAL_PENDING, lambda p: seen.append(p))
            return seen

    yield Seam()
    importlib.reload(ext)   # drop every handler this test registered


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                       str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    yield ls
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def _pin_entitlement(monkeypatch, *, features=("approval_queue",
                                               "approval_routing",
                                               "approval_mirror")):
    import clawmetry.entitlements as ent
    e = ent.Entitlement(tier="pro", source="test", grace=False,
                        features=frozenset(features), runtimes=frozenset())
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)


@pytest.fixture
def mirror_app(fresh_store, seam, monkeypatch):
    _pin_entitlement(monkeypatch)
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    import routes.hooks as rh
    monkeypatch.setattr(rh, "_WAIT_SLICE_S", 1.0)
    from routes.hooks import bp_hooks
    app = Flask(__name__)
    app.register_blueprint(bp_hooks)
    return app.test_client(), fresh_store, seam


def _event(**over):
    return {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"},
            "session_id": "s1", "cwd": "/tmp", "tool_use_id": "tu1", **over}


# ── 1. the receiver ────────────────────────────────────────────────────────

def test_unarmed_answers_ask(mirror_app):
    """The unlicensed node: nothing registered → Claude Code's own prompt."""
    client, _, _ = mirror_app
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_event()).get_json()
    assert d["hookSpecificOutput"] == {"hookEventName": "PermissionRequest",
                                       "decision": "ask"}


def test_armed_parks_and_human_approval_allows(mirror_app):
    client, ls, seam = mirror_app
    seam.arm()
    store = ls.get_store()

    def _approve_soon():
        for _ in range(100):
            rows = store.query_approvals(status="pending", limit=10)
            if rows:
                store.update_approval_decision(rows[0]["id"], "approve",
                                               "test", "ok")
                return
            time.sleep(0.05)

    t = threading.Thread(target=_approve_soon, daemon=True)
    t.start()
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_event()).get_json()
    t.join(timeout=5)
    assert d["hookSpecificOutput"]["decision"] == "allow"


def test_armed_parks_and_denial_blocks(mirror_app):
    client, ls, seam = mirror_app
    seam.arm()
    store = ls.get_store()
    store.ingest_approval({
        "id": "denied1", "requestor_session_id": "claude_code:s1",
        "action": "Bash: x", "status": "pending",
        "args": {"runtime": "claude_code", "kind": "permission_prompt",
                 "deadline_ms": int(time.time() * 1000) + 60000},
        "created_at": "2026-08-15T00:00:00Z"})
    store.update_approval_decision("denied1", "deny", "test", "nope")
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_event(approval_id="denied1")).get_json()
    assert d["hookSpecificOutput"]["decision"] == "deny"


def test_window_elapsed_hands_back_to_the_terminal(mirror_app):
    client, ls, seam = mirror_app
    seam.arm(window=30)
    store = ls.get_store()
    store.ingest_approval({
        "id": "expired1", "requestor_session_id": "claude_code:s1",
        "action": "Bash: x", "status": "pending",
        "args": {"runtime": "claude_code", "kind": "permission_prompt",
                 "on_timeout": "ask", "deadline_ms": 1},
        "created_at": "2026-08-15T00:00:00Z"})
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_event(approval_id="expired1")).get_json()
    assert d["hookSpecificOutput"]["decision"] == "ask"


def test_receiver_announces_the_parked_approval(mirror_app):
    """OSS parks and ANNOUNCES; whoever is listening does the paging."""
    client, ls, seam = mirror_app
    seam.arm()
    paged = seam.pages()
    client.post("/api/hooks/claude-code/permissionrequest", json=_event())
    assert paged, "the seam never saw the parked approval"
    assert paged[0]["kind"] == "permission_prompt"
    assert paged[0]["runtime"] == "claude_code"


def test_unentitled_answers_ask(mirror_app, monkeypatch):
    client, _, seam = mirror_app
    seam.arm()
    _pin_entitlement(monkeypatch, features=("approval_queue",))  # no mirror
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_event()).get_json()
    assert d["hookSpecificOutput"]["decision"] == "ask"


def test_loopback_only(mirror_app):
    client, _, seam = mirror_app
    seam.arm()
    r = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_event(), environ_overrides={"REMOTE_ADDR": "10.0.0.9"})
    assert r.status_code == 403


# ── 2. the installer ───────────────────────────────────────────────────────

@pytest.fixture
def gate(tmp_path, monkeypatch, seam):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.setenv("CLAWMETRY_DASHBOARD_BASE", "http://127.0.0.1:8900")
    import clawmetry.claude_code_gate as g
    importlib.reload(g)
    monkeypatch.setattr(g, "_MIRROR_STATE_PATH",
                        str(tmp_path / "mirror_state.json"))
    monkeypatch.setattr(g, "_STATE_PATH", str(tmp_path / "gate_state.json"))
    return g


def _settings(g):
    with open(g._settings_path()) as f:
        return json.load(f)


def test_unarmed_installs_nothing(gate):
    """THE safety property. No paid layer → no hook in the user's settings,
    so a node that loses its license reverts to the terminal prompt rather
    than keeping a hook aimed at a feature that stopped answering."""
    gate.gate_handler(False, [])
    assert not os.path.exists(gate._settings_path())


def test_armed_installs_the_permissionrequest_hook(gate, seam):
    seam.arm()
    gate.gate_handler(False, [])
    entries = _settings(gate)["hooks"]["PermissionRequest"]
    assert len(entries) == 1
    assert "hook claude-code-permission" in entries[0]["hooks"][0]["command"]


def test_arms_with_zero_protection_rules(gate, seam, monkeypatch):
    """Mirroring is about the runtime's OWN prompts, so it must arm through
    the normal watcher seam even with no policies written."""
    import clawmetry.approvals as ap
    monkeypatch.setattr(ap, "GATE_HANDLERS", {}, raising=True)
    monkeypatch.setattr(ap, "GATE_WANT_PREDICATES", {}, raising=True)
    monkeypatch.setattr(ap, "_default_gates_registered", True)
    ap.register_gate_handler("claude_code", gate.gate_handler)
    seam.arm()

    ap.sync_runtime_gates([])

    assert len(_settings(gate)["hooks"]["PermissionRequest"]) == 1
    # …and the PreToolUse gate stays absent — no rules, nothing to gate.
    assert "PreToolUse" not in _settings(gate).get("hooks", {})


def test_preserves_a_foreign_permission_hook(gate, seam):
    os.makedirs(os.path.dirname(gate._settings_path()), exist_ok=True)
    with open(gate._settings_path(), "w") as f:
        json.dump({"hooks": {"PermissionRequest": [
            {"hooks": [{"type": "command", "command": "/usr/bin/other"}]}]}}, f)
    seam.arm()
    gate.gate_handler(False, [])
    assert len(_settings(gate)["hooks"]["PermissionRequest"]) == 2


def test_disarming_removes_only_ours(gate, seam, monkeypatch):
    os.makedirs(os.path.dirname(gate._settings_path()), exist_ok=True)
    with open(gate._settings_path(), "w") as f:
        json.dump({"hooks": {"PermissionRequest": [
            {"hooks": [{"type": "command", "command": "/usr/bin/other"}]}]}}, f)
    seam.arm()
    gate.gate_handler(False, [])
    # License lapses / operator turns it off: the seam stops saying yes.
    monkeypatch.setattr(gate, "_mirror_wanted", lambda: False)
    gate.gate_handler(False, [])
    entries = _settings(gate)["hooks"]["PermissionRequest"]
    assert len(entries) == 1
    assert entries[0]["hooks"][0]["command"] == "/usr/bin/other"


def test_install_is_idempotent(gate, seam):
    seam.arm()
    gate.gate_handler(False, [])
    first = _settings(gate)
    gate.gate_handler(False, [])
    gate.gate_handler(False, [])
    assert _settings(gate) == first


def test_pretooluse_ownership_excludes_the_mirror_entry(gate):
    """MIRROR_CMD_MARKER contains HOOK_CMD_MARKER as a substring — the
    PreToolUse uninstaller must not claim the mirror entry as its own."""
    mirror = {"hooks": [{"type": "command",
                         "command": "py -m clawmetry hook "
                                    "claude-code-permission --base x"}]}
    pretool = {"hooks": [{"type": "command",
                          "command": "py -m clawmetry hook "
                                     "claude-code --base x"}]}
    assert gate._entry_is_ours(mirror) is False
    assert gate._entry_is_mirror(mirror) is True
    assert gate._entry_is_ours(pretool) is True
    assert gate._entry_is_mirror(pretool) is False


def test_window_comes_from_the_seam(gate, seam):
    seam.arm(window=600)
    assert gate.mirror_timeout_s() == 600
    gate.gate_handler(False, [])
    entry = _settings(gate)["hooks"]["PermissionRequest"][0]
    # +15s so our own "ask" fallback always lands before Claude Code's hook
    # timeout would cancel us and leave the row pending with nobody waiting.
    assert entry["hooks"][0]["timeout"] == 615
