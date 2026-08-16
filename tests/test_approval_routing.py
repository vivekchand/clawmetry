"""Tests for per-runtime approval routing + the Claude Code mirror gate.

Five surfaces:

  1. ``clawmetry/approval_notify.py`` — routing resolution (per-runtime row,
     default fallback, "no channels chosen" = every configured channel),
     link signing, and the per-channel payload shapes (Telegram buttons,
     Slack decision links).
  2. ``GET/PUT /api/approvals/routing`` — round-trip, and the two 400s that
     keep the config honest (unknown runtime / unknown channel).
  3. ``/a/<id>`` — the phone page: bad signature → 403, GET NEVER decides
     (link prefetch safety), POST decides once.
  4. ``POST /api/hooks/claude-code/permissionrequest`` — mirroring off →
     "ask", human approve → "allow", window elapsed → "ask" (the local
     prompt takes over).
  5. ``claude_code_gate`` mirror installer — installs/removes only its own
     PermissionRequest entry, never confuses it with the PreToolUse gate.
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
def notify(tmp_path, monkeypatch):
    """approval_notify pinned at a tmp HOME (routes + secret + channels)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_PUBLIC_BASE", raising=False)
    import clawmetry.approval_notify as an
    importlib.reload(an)
    monkeypatch.setattr(an, "ROUTES_PATH", str(tmp_path / "routes.json"))
    monkeypatch.setattr(an, "_SECRET_PATH", str(tmp_path / "secret"))
    monkeypatch.setattr(an, "_MSG_STATE_PATH", str(tmp_path / "msgs.json"))
    monkeypatch.setattr(an, "_ALERTS_CONFIG_FILE", str(tmp_path / "ch.json"))
    return an


def _channels(an, **flat):
    with open(an._ALERTS_CONFIG_FILE, "w") as f:
        json.dump(flat, f)


@pytest.fixture
def sent(monkeypatch, notify):
    """Capture every outbound POST instead of hitting the network."""
    calls = []

    def _fake_post(url, payload, **kw):
        calls.append({"url": url, "payload": payload, **kw})
        return {"ok": True, "result": {"chat": {"id": 42}, "message_id": 7}}

    monkeypatch.setattr(notify, "_post", _fake_post)
    return calls


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
                                               "approval_mirror")):
    import clawmetry.entitlements as ent
    e = ent.Entitlement(tier="pro", source="test", grace=False,
                        features=frozenset(features), runtimes=frozenset())
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)


def _no_daemon_proxy(monkeypatch):
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)


# ── 1. routing resolution ──────────────────────────────────────────────────

def test_no_channels_chosen_means_every_configured_channel(notify):
    an = notify
    _channels(an, slack_webhook_url="https://hooks.slack.com/x",
              telegram_bot_token="t", telegram_chat_id="c")
    assert set(an.configured_channels()) == {"slack", "telegram"}
    # Default row has an empty channel list → everything configured.
    assert set(an.resolve_targets("claude_code")) == {"slack", "telegram"}


def test_per_runtime_row_overrides_default(notify):
    an = notify
    _channels(an, slack_webhook_url="https://hooks.slack.com/x",
              telegram_bot_token="t", telegram_chat_id="c")
    an.save_routes({"enabled": True,
                    "default": {"channels": ["slack"]},
                    "runtimes": {"claude_code": {"channels": ["telegram"]}}})
    assert an.resolve_targets("claude_code") == ["telegram"]
    assert an.resolve_targets("openclaw") == ["slack"]      # falls back
    assert an.resolve_targets("cursor") == ["slack"]        # unknown → default


def test_unconfigured_channel_is_dropped_not_attempted(notify):
    an = notify
    _channels(an, telegram_bot_token="t", telegram_chat_id="c")
    an.save_routes({"enabled": True,
                    "default": {"channels": ["slack", "telegram"]},
                    "runtimes": {}})
    assert an.resolve_targets("openclaw") == ["telegram"]


def test_routing_disabled_sends_nowhere(notify):
    an = notify
    _channels(an, telegram_bot_token="t", telegram_chat_id="c")
    an.save_routes({"enabled": False, "default": {"channels": []},
                    "runtimes": {}})
    assert an.resolve_targets("openclaw") == []


def test_mirror_flag_and_window_clamp(notify):
    an = notify
    an.save_routes({"enabled": True, "default": {"channels": []},
                    "runtimes": {"claude_code": {
                        "channels": [], "mirror_permission_prompts": True,
                        "mirror_timeout_s": 5}}})
    assert an.mirror_enabled("claude_code") is True
    assert an.mirror_enabled("openclaw") is False
    # 5 s is unanswerable — clamped up to the 30 s floor.
    assert an.route_for("claude_code")["mirror_timeout_s"] == 30


def test_link_signature_is_scoped_to_one_approval(notify):
    an = notify
    tok = an.sign_link("abc")
    assert an.verify_link("abc", tok)
    assert not an.verify_link("abd", tok)
    assert not an.verify_link("abc", "")


# ── 2. payload shapes ──────────────────────────────────────────────────────

def test_telegram_carries_decide_buttons(notify, sent):
    an = notify
    _channels(an, telegram_bot_token="TOK", telegram_chat_id="99")
    delivered = an.notify_pending({
        "id": "a1", "runtime": "claude_code", "tool_name": "Bash",
        "command": "rm -rf /tmp/x"}, blocking=True)
    assert delivered == ["telegram"]
    body = sent[0]["payload"]
    buttons = body["reply_markup"]["inline_keyboard"][0]
    assert [b["callback_data"] for b in buttons] == ["cma:a1:approve",
                                                     "cma:a1:deny"]
    assert "rm -rf /tmp/x" in body["text"]


def test_slack_carries_decision_links(notify, sent):
    an = notify
    _channels(an, slack_webhook_url="https://hooks.slack.com/services/x")
    assert an.notify_pending({"id": "a2", "runtime": "openclaw",
                              "tool_name": "Bash", "command": "sudo reboot"},
                             blocking=True) == ["slack"]
    blocks = sent[0]["payload"]["blocks"]
    urls = [e["url"] for b in blocks if b["type"] == "actions"
            for e in b["elements"]]
    assert all("/a/a2?t=" in u for u in urls)
    assert any(u.endswith("d=approve") for u in urls)


def test_one_broken_channel_does_not_stop_the_others(notify, monkeypatch):
    an = notify
    _channels(an, telegram_bot_token="t", telegram_chat_id="c",
              slack_webhook_url="https://hooks.slack.com/x")
    monkeypatch.setattr(an, "_send_telegram",
                        lambda cfg, p: (_ for _ in ()).throw(RuntimeError))
    monkeypatch.setattr(an, "_send_slack", lambda cfg, p: True)
    monkeypatch.setattr(an, "_SENDERS", {**an._SENDERS,
                                         "telegram": an._send_telegram,
                                         "slack": an._send_slack})
    assert an.notify_pending({"id": "a3", "runtime": "openclaw",
                              "tool_name": "Bash", "command": "x"},
                             blocking=True) == ["slack"]


# ── 3. the routing API ─────────────────────────────────────────────────────

@pytest.fixture
def routing_app(notify, monkeypatch):
    _pin_entitlement(monkeypatch)
    from routes.approval_routing import bp_approval_routing
    app = Flask(__name__)
    app.register_blueprint(bp_approval_routing)
    return app.test_client()


def test_routing_get_reports_capabilities(routing_app, notify):
    _channels(notify, telegram_bot_token="t", telegram_chat_id="c")
    d = routing_app.get("/api/approvals/routing").get_json()
    assert d["ok"] is True
    by_key = {c["key"]: c for c in d["channels"]}
    assert by_key["telegram"]["configured"] is True
    assert by_key["telegram"]["decide"] is True     # two-way locally
    assert by_key["slack"]["configured"] is False
    assert by_key["slack"]["decide"] is False       # link only — never lie


def test_routing_put_roundtrip(routing_app, notify):
    r = routing_app.put("/api/approvals/routing", json={
        "enabled": True, "default": {"channels": ["slack"]},
        "runtimes": {"claude_code": {"channels": ["telegram"],
                                     "mirror_permission_prompts": True}}})
    assert r.status_code == 200
    assert notify.load_routes()["runtimes"]["claude_code"]["channels"] \
        == ["telegram"]
    assert notify.mirror_enabled("claude_code") is True


def test_routing_put_rejects_unknown_runtime_and_channel(routing_app):
    r = routing_app.put("/api/approvals/routing",
                        json={"runtimes": {"not_a_runtime": {"channels": []}}})
    assert r.status_code == 400
    assert "unknown runtime" in r.get_json()["error"]
    r = routing_app.put("/api/approvals/routing",
                        json={"default": {"channels": ["carrier_pigeon"]}})
    assert r.status_code == 400
    assert "unknown channel" in r.get_json()["error"]


def test_routing_test_reports_hint_when_nothing_configured(routing_app):
    d = routing_app.post("/api/approvals/routing/test",
                         json={"runtime": "claude_code"}).get_json()
    assert d["ok"] is False
    assert "Notifications" in d["hint"]


# ── 4. the phone page ──────────────────────────────────────────────────────

@pytest.fixture
def link_app(fresh_store, notify, monkeypatch):
    _pin_entitlement(monkeypatch)
    _no_daemon_proxy(monkeypatch)
    from routes.approval_routing import bp_approval_routing
    app = Flask(__name__)
    app.register_blueprint(bp_approval_routing)
    store = fresh_store.get_store()
    store.ingest_approval({
        "id": "pending1", "requestor_session_id": "claude_code:s1",
        "action": "Bash: rm -rf /tmp/x", "status": "pending",
        "args": {"runtime": "claude_code", "tool_name": "Bash"},
        "created_at": "2026-08-15T00:00:00Z"})
    return app.test_client(), store


def test_link_page_rejects_a_bad_signature(link_app, notify):
    client, _ = link_app
    assert client.get("/a/pending1?t=nope").status_code == 403


def test_link_get_never_decides(link_app, notify):
    """Mail clients and chat apps prefetch links — a GET that approved
    would let a link preview run the command."""
    client, store = link_app
    tok = notify.sign_link("pending1")
    r = client.get("/a/pending1?t=%s&d=approve" % tok)
    assert r.status_code == 200
    assert b"Approve" in r.data
    row = [x for x in store.query_approvals(limit=10) if x["id"] == "pending1"][0]
    assert row["status"] == "pending"


def test_link_post_decides_once(link_app, notify):
    client, store = link_app
    tok = notify.sign_link("pending1")
    r = client.post("/a/pending1/decide",
                    data={"t": tok, "decision": "approve"})
    assert r.status_code == 200
    row = [x for x in store.query_approvals(limit=10) if x["id"] == "pending1"][0]
    assert row["status"] == "approved"
    # Second tap is a no-op, not a re-decision.
    r2 = client.post("/a/pending1/decide", data={"t": tok, "decision": "deny"})
    assert b"Already decided" in r2.data
    row = [x for x in store.query_approvals(limit=10) if x["id"] == "pending1"][0]
    assert row["status"] == "approved"


def test_link_post_rejects_bad_signature(link_app):
    client, store = link_app
    r = client.post("/a/pending1/decide",
                    data={"t": "forged", "decision": "approve"})
    assert r.status_code == 403
    row = [x for x in store.query_approvals(limit=10) if x["id"] == "pending1"][0]
    assert row["status"] == "pending"


# ── 5. the mirror receiver ─────────────────────────────────────────────────

@pytest.fixture
def mirror_app(fresh_store, notify, monkeypatch):
    _pin_entitlement(monkeypatch)
    _no_daemon_proxy(monkeypatch)
    monkeypatch.setattr(notify, "notify_pending", lambda *a, **k: [])
    import routes.hooks as rh
    monkeypatch.setattr(rh, "_WAIT_SLICE_S", 1.0)
    from routes.hooks import bp_hooks
    app = Flask(__name__)
    app.register_blueprint(bp_hooks)
    return app.test_client(), fresh_store


def _mirror_on(an, window=120):
    an.save_routes({"enabled": True, "default": {"channels": []},
                    "runtimes": {"claude_code": {
                        "channels": [], "mirror_permission_prompts": True,
                        "mirror_timeout_s": window}}})


def _permission_event(**over):
    return {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"},
            "session_id": "s1", "cwd": "/tmp", "tool_use_id": "tu1", **over}


def test_mirror_off_answers_ask(mirror_app, notify):
    client, _ = mirror_app
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_permission_event()).get_json()
    assert d["hookSpecificOutput"] == {"hookEventName": "PermissionRequest",
                                       "decision": "ask"}


def test_mirror_parks_and_human_approval_allows(mirror_app, notify):
    client, ls = mirror_app
    _mirror_on(notify)
    store = ls.get_store()

    def _approve_soon():
        for _ in range(100):
            rows = [r for r in store.query_approvals(status="pending",
                                                     limit=10)]
            if rows:
                store.update_approval_decision(rows[0]["id"], "approve",
                                               "test", "ok")
                return
            time.sleep(0.05)

    t = threading.Thread(target=_approve_soon, daemon=True)
    t.start()
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_permission_event()).get_json()
    t.join(timeout=5)
    assert d["hookSpecificOutput"]["decision"] == "allow"


def test_mirror_window_elapsed_hands_back_to_the_terminal(mirror_app, notify):
    client, ls = mirror_app
    _mirror_on(notify, window=30)
    # Park the row with an already-past deadline: no human, no answer.
    store = ls.get_store()
    store.ingest_approval({
        "id": "expired1", "requestor_session_id": "claude_code:s1",
        "action": "Bash: x", "status": "pending",
        "args": {"runtime": "claude_code", "kind": "permission_prompt",
                 "on_timeout": "ask", "deadline_ms": 1},
        "created_at": "2026-08-15T00:00:00Z"})
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_permission_event(approval_id="expired1")).get_json()
    assert d["hookSpecificOutput"]["decision"] == "ask"


def test_mirror_denied_blocks_the_call(mirror_app, notify):
    client, ls = mirror_app
    _mirror_on(notify)
    store = ls.get_store()
    store.ingest_approval({
        "id": "denied1", "requestor_session_id": "claude_code:s1",
        "action": "Bash: x", "status": "pending",
        "args": {"runtime": "claude_code", "kind": "permission_prompt",
                 "deadline_ms": int(time.time() * 1000) + 60000},
        "created_at": "2026-08-15T00:00:00Z"})
    store.update_approval_decision("denied1", "deny", "test", "nope")
    d = client.post("/api/hooks/claude-code/permissionrequest",
                    json=_permission_event(approval_id="denied1")).get_json()
    assert d["hookSpecificOutput"]["decision"] == "deny"


# ── 6. the mirror installer ────────────────────────────────────────────────

@pytest.fixture
def gate(tmp_path, monkeypatch, notify):
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


def test_mirror_installs_only_when_enabled(gate, notify):
    g = gate
    g.gate_handler(False, [])
    assert not os.path.exists(g._settings_path())

    _mirror_on(notify)
    g.gate_handler(False, [])
    entries = _settings(g)["hooks"]["PermissionRequest"]
    assert len(entries) == 1
    assert "hook claude-code-permission" in entries[0]["hooks"][0]["command"]


def test_mirror_preserves_foreign_permission_hooks(gate, notify):
    g = gate
    os.makedirs(os.path.dirname(g._settings_path()), exist_ok=True)
    with open(g._settings_path(), "w") as f:
        json.dump({"hooks": {"PermissionRequest": [
            {"hooks": [{"type": "command", "command": "/usr/bin/other"}]}]}}, f)
    _mirror_on(notify)
    g.gate_handler(False, [])
    entries = _settings(g)["hooks"]["PermissionRequest"]
    assert len(entries) == 2
    # Turning it back off removes ONLY ours.
    notify.save_routes({"enabled": True, "default": {"channels": []},
                        "runtimes": {}})
    g.gate_handler(False, [])
    entries = _settings(g)["hooks"]["PermissionRequest"]
    assert len(entries) == 1
    assert entries[0]["hooks"][0]["command"] == "/usr/bin/other"


def test_mirror_install_is_idempotent(gate, notify):
    g = gate
    _mirror_on(notify)
    g.gate_handler(False, [])
    first = _settings(g)
    g.gate_handler(False, [])
    g.gate_handler(False, [])
    assert _settings(g) == first


def test_mirror_installs_with_zero_protection_rules(gate, notify, monkeypatch):
    """The whole point: mirroring is about the runtime's OWN prompts, so it
    must arm through the normal watcher seam even when the operator has
    written no policies at all."""
    g = gate
    import clawmetry.approvals as ap
    monkeypatch.setattr(ap, "GATE_HANDLERS", {}, raising=True)
    monkeypatch.setattr(ap, "GATE_WANT_PREDICATES", {}, raising=True)
    monkeypatch.setattr(ap, "_default_gates_registered", True)
    ap.register_gate_handler("claude_code", g.gate_handler)

    _mirror_on(notify)
    ap.sync_runtime_gates([])            # no policies at all

    entries = _settings(g)["hooks"]["PermissionRequest"]
    assert len(entries) == 1
    assert "claude-code-permission" in entries[0]["hooks"][0]["command"]
    # …and the PreToolUse gate stays absent — no rules, nothing to gate.
    assert "PreToolUse" not in _settings(g).get("hooks", {})


def test_pretooluse_ownership_excludes_the_mirror_entry(gate):
    """MIRROR_CMD_MARKER contains HOOK_CMD_MARKER as a substring — the
    PreToolUse uninstaller must not treat a mirror entry as its own."""
    g = gate
    mirror_entry = {"hooks": [{"type": "command",
                               "command": "py -m clawmetry hook "
                                          "claude-code-permission --base x"}]}
    gate_entry = {"hooks": [{"type": "command",
                             "command": "py -m clawmetry hook "
                                        "claude-code --base x"}]}
    assert g._entry_is_ours(mirror_entry) is False
    assert g._entry_is_mirror(mirror_entry) is True
    assert g._entry_is_ours(gate_entry) is True
    assert g._entry_is_mirror(gate_entry) is False


# ── 7. telegram inbound decisions ──────────────────────────────────────────

@pytest.fixture
def inbound(fresh_store, tmp_path, monkeypatch):
    import clawmetry.approval_inbound as ai
    importlib.reload(ai)
    monkeypatch.setattr(ai, "_STATE_PATH", str(tmp_path / "inbound.json"))
    api_calls = []
    monkeypatch.setattr(ai, "_api",
                        lambda *a, **k: api_calls.append(a) or {"ok": True})
    store = fresh_store.get_store()
    store.ingest_approval({
        "id": "tg1", "requestor_session_id": "claude_code:s1",
        "action": "Bash: x", "status": "pending",
        "created_at": "2026-08-15T00:00:00Z"})
    return ai, store, api_calls


def _callback(data, chat_id="55"):
    return {"id": "cb1", "data": data, "from": {"username": "vivek"},
            "message": {"message_id": 3, "chat": {"id": chat_id}}}


def test_telegram_button_decides_the_approval(inbound):
    ai, store, _ = inbound
    ai._handle_callback(_callback("cma:tg1:approve"), "TOK", "55")
    row = [r for r in store.query_approvals(limit=10) if r["id"] == "tg1"][0]
    assert row["status"] == "approved"
    assert row["resolver"] == "telegram:vivek"


def test_telegram_press_from_another_chat_is_ignored(inbound):
    """A bot added to a second group must not be able to approve this
    node's tool calls."""
    ai, store, _ = inbound
    ai._handle_callback(_callback("cma:tg1:approve", chat_id="999"),
                        "TOK", "55")
    row = [r for r in store.query_approvals(limit=10) if r["id"] == "tg1"][0]
    assert row["status"] == "pending"


def test_telegram_ignores_foreign_callback_data(inbound):
    ai, store, _ = inbound
    ai._handle_callback(_callback("someotherbot:thing"), "TOK", "55")
    row = [r for r in store.query_approvals(limit=10) if r["id"] == "tg1"][0]
    assert row["status"] == "pending"


def test_inbound_idles_when_telegram_is_not_a_target(notify, inbound):
    ai, _, _ = inbound
    _channels(notify, telegram_bot_token="t", telegram_chat_id="c")
    notify.save_routes({"enabled": True, "default": {"channels": ["slack"]},
                        "runtimes": {}})
    assert ai._telegram_creds() == (None, None)
    notify.save_routes({"enabled": True,
                        "default": {"channels": ["slack", "telegram"]},
                        "runtimes": {}})
    assert ai._telegram_creds() == ("t", "c")
