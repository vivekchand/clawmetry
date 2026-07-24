"""Unit tests for the human-in-the-loop questions engine.

Covers ``clawmetry/questions.py`` (question lifecycle, kill switch,
delivery modes, secret redaction), ``clawmetry/agent_hooks.py`` (risky-
command classification, the PreToolUse gate, settings.json install/
remove), and the ``routes/questions.py`` HTTP surface via a minimal
Flask app. Everything runs against a sandboxed tmp_path — no daemon, no
network, no writes to the real ``~/.clawmetry`` or ``~/.claude``.
"""
from __future__ import annotations

import io
import json
import sys

import pytest
from flask import Flask


@pytest.fixture()
def engine(tmp_path, monkeypatch):
    """The questions engine wired to a throwaway home + DuckDB file."""
    from clawmetry import local_store
    from clawmetry import questions as q
    from clawmetry import agent_hooks as ah
    from clawmetry import approvals

    monkeypatch.setattr(local_store, "DB_PATH", tmp_path / "clawmetry.duckdb")
    monkeypatch.setattr(local_store, "LEGACY_DB_PATH", tmp_path / "events.duckdb")
    monkeypatch.setattr(local_store, "_store_rw", None)
    monkeypatch.setattr(local_store, "_store_ro", None)
    monkeypatch.setattr(local_store, "_store_proxy", None)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)

    monkeypatch.setattr(q, "_CLAWMETRY_DIR", tmp_path)
    monkeypatch.setattr(q, "CHANNELS_PATH", tmp_path / "questions-channels.json")
    monkeypatch.setattr(q, "KILLSWITCH_PATH", tmp_path / "killswitch.json")
    monkeypatch.setattr(q, "MODE_PATH", tmp_path / "approval-mode.json")
    monkeypatch.setattr(q, "_read_discovery", lambda: None)

    monkeypatch.setattr(ah, "_CLAUDE_SETTINGS", tmp_path / "claude-settings.json")
    monkeypatch.setattr(approvals, "POLICIES_PATH", tmp_path / "policies.yml")
    return q


@pytest.fixture()
def client(engine):
    from routes.questions import bp_questions
    app = Flask(__name__)
    app.register_blueprint(bp_questions)
    return app.test_client()


# ── Engine: question lifecycle ───────────────────────────────────────────


def test_confirm_lifecycle_first_answer_wins(engine):
    row = engine.create_question("Delete 3 files?", agent_name="T", notify=False)
    assert engine.get_question(row["id"])["status"] == "pending"
    r = engine.answer_question(row["id"], "approve")
    assert r["ok"] and r["answer"] == "yes"
    # second answer is a no-op, first click wins
    assert engine.answer_question(row["id"], "no").get("already")
    final = engine.get_question(row["id"])
    assert final["answer"] == "yes" and final["latency_ms"] is not None


def test_confirm_rejects_non_boolean_answers(engine):
    row = engine.create_question("Proceed?", notify=False)
    assert not engine.answer_question(row["id"], "maybe")["ok"]


def test_select_validates_options(engine):
    row = engine.create_question("Pick", qtype="select",
                                 options=["JWT", "Cookies"], notify=False)
    assert not engine.answer_question(row["id"], "OAuth")["ok"]
    assert engine.answer_question(row["id"], "Cookies")["ok"]


def test_select_requires_2_to_6_options(engine):
    with pytest.raises(ValueError):
        engine.create_question("Pick", qtype="select", options=["only-one"],
                               notify=False)


def test_input_records_free_text(engine):
    row = engine.create_question("Endpoint path?", qtype="input", notify=False)
    assert engine.answer_question(row["id"], "/api/v2/prefs")["ok"]
    assert engine.get_question(row["id"])["answer"] == "/api/v2/prefs"


def test_cancel_and_expire(engine):
    c = engine.create_question("Cancel me", notify=False)
    assert engine.cancel_question(c["id"])["ok"]
    assert engine.get_question(c["id"])["status"] == "cancelled"
    e = engine.create_question("Expire me", expiry_seconds=-1, notify=False)
    assert engine.expire_pending() >= 1
    assert engine.get_question(e["id"])["status"] == "expired"


def test_wait_for_answer_times_out_and_resolves(engine):
    row = engine.create_question("Slow?", notify=False)
    out = engine.wait_for_answer(row["id"], timeout_s=0.1)
    assert out == {"answered": False, "timedOut": True,
                   "correlationId": row["id"]}
    engine.answer_question(row["id"], "yes")
    out = engine.wait_for_answer(row["id"], timeout_s=0.1)
    assert out["answered"] and out["value"] == "yes"


# ── Engine: kill switch / mode / redaction ───────────────────────────────


def test_killswitch_global_and_session_scoped(engine):
    assert not engine.killswitch_active()
    engine.set_killswitch(True, reason="incident")
    assert engine.killswitch_active() and engine.killswitch_active("any")
    engine.set_killswitch(False)
    engine.set_killswitch(True, session_id="s1")
    assert engine.killswitch_active("s1") and not engine.killswitch_active("s2")
    engine.set_killswitch(False, session_id="s1")
    assert not engine.killswitch_active("s1")


def test_mode_override_and_expiry_window(engine):
    assert engine.load_mode()["mode"] == "push_first"  # default
    engine.set_mode("push_only", 3600)
    assert engine.load_mode() == {"mode": "push_only", "until": pytest.approx(
        engine.load_mode()["until"]), "override": True}
    with pytest.raises(ValueError):
        engine.set_mode("bogus")


def test_redact_secrets_masks_credentials(engine):
    assert "[redacted]" in engine.redact_secrets("API_KEY=sk_live_abc4567890123456789")
    assert "hunter2" not in engine.redact_secrets("password: hunter2")
    assert engine.redact_secrets("plain rm -rf build") == "plain rm -rf build"


# ── Hooks: classification + gate ─────────────────────────────────────────


@pytest.mark.parametrize("cmd,category", [
    ("rm -rf /tmp/x", "file_deletion"),
    ("git push --force origin main", "git_history"),
    ("git reset --hard HEAD~3", "git_history"),
    ("psql -c 'DROP TABLE users'", "database"),
    ("kubectl apply -f prod.yaml", "deployment"),
    ("npm publish", "deployment"),
    ("systemctl stop nginx", "system_admin"),
    ("iptables -F", "network_config"),
    ("ls -la", None),
    ("git status", None),
    ("grep -r foo .", None),
])
def test_classify_command(engine, cmd, category):
    from clawmetry import agent_hooks as ah
    assert ah.classify_command("Bash", {"command": cmd}) == category


def test_classify_ignores_read_only_tools(engine):
    from clawmetry import agent_hooks as ah
    assert ah.classify_command("Read", {"file_path": "/etc/passwd"}) is None
    assert ah.classify_command("Grep", {"pattern": "rm -rf"}) is None


def test_gate_killswitch_denies_everything(engine):
    from clawmetry import agent_hooks as ah
    engine.set_killswitch(True)
    assert ah.evaluate_gate("Bash", {"command": "ls"})["decision"] == "deny"
    engine.set_killswitch(False)


def test_gate_passes_benign_and_asks_in_terminal_mode(engine):
    from clawmetry import agent_hooks as ah
    assert ah.evaluate_gate("Read", {"file_path": "a.py"})["decision"] == "pass"
    engine.set_mode("terminal_only")
    assert ah.evaluate_gate("Bash", {"command": "rm -rf build"})["decision"] == "ask"


def test_gate_notify_only_never_blocks(engine):
    from clawmetry import agent_hooks as ah
    engine.set_mode("notify_only")
    assert ah.evaluate_gate("Bash", {"command": "rm -rf build"})["decision"] == "pass"


def test_pretooluse_hook_protocol(engine, monkeypatch, capsys):
    from clawmetry import agent_hooks as ah
    engine.set_mode("terminal_only")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({
        "session_id": "abc", "tool_name": "Bash",
        "tool_input": {"command": "git push --force"}})))
    assert ah.run_pretooluse_hook() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"
    # benign call → no decision emitted (agent's own flow continues)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({
        "tool_name": "Read", "tool_input": {"file_path": "x"}})))
    assert ah.run_pretooluse_hook() == 0
    assert capsys.readouterr().out == ""
    # garbage stdin → silent pass, never a crash
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert ah.run_pretooluse_hook() == 0
    assert capsys.readouterr().out == ""


def test_setup_and_clean_are_idempotent_and_preserve_foreign_hooks(engine):
    from clawmetry import agent_hooks as ah
    first = ah.setup_hooks(quiet=True)
    assert set(first["added"]) == {"PreToolUse", "Notification", "Stop"}
    assert ah.setup_hooks(quiet=True)["added"] == []
    settings = json.loads(ah._CLAUDE_SETTINGS.read_text())
    settings["hooks"]["PreToolUse"].append(
        {"matcher": "Bash", "hooks": [{"type": "command", "command": "other"}]})
    ah._CLAUDE_SETTINGS.write_text(json.dumps(settings))
    assert ah.clean_hooks(quiet=True)["removed"] == 3
    kept = json.loads(ah._CLAUDE_SETTINGS.read_text())["hooks"]["PreToolUse"]
    assert kept == [{"matcher": "Bash",
                     "hooks": [{"type": "command", "command": "other"}]}]


# ── HTTP surface ─────────────────────────────────────────────────────────


def test_ask_answer_roundtrip_over_http(client):
    r = client.post("/api/questions/ask", json={
        "question": "Ship it?", "agent_name": "Claude Code - repo"})
    assert r.status_code == 200
    qid = r.get_json()["correlationId"]
    inbox = client.get("/api/questions").get_json()
    assert inbox["pending_count"] == 1
    r = client.post(f"/api/questions/{qid}/answer", json={"value": "yes"})
    assert r.get_json()["ok"]
    assert client.get(f"/api/questions/{qid}").get_json()["status"] == "answered"


def test_ask_validates_input_over_http(client):
    assert client.post("/api/questions/ask", json={}).status_code == 400
    assert client.post("/api/questions/ask", json={
        "question": "x", "type": "select", "options": ["a"]}).status_code == 400
    assert client.post("/api/questions/nope/answer",
                       json={"value": "yes"}).status_code == 404


def test_answer_via_get_link_button(client):
    qid = client.post("/api/questions/ask", json={"question": "OK?"}) \
        .get_json()["correlationId"]
    r = client.get(f"/api/questions/{qid}/answer?value=no")
    assert r.status_code == 200 and b"recorded" in r.data
    assert client.get(f"/api/questions/{qid}").get_json()["answer"] == "no"


def test_killswitch_over_http(client):
    assert client.get("/api/killswitch").get_json()["engaged"] is False
    r = client.post("/api/killswitch", json={"engaged": True, "reason": "stop"})
    assert r.get_json()["engaged"] is True
    assert client.post("/api/killswitch", json={}).status_code == 400
    client.post("/api/killswitch", json={"engaged": False})


def test_channels_config_masks_credentials(client):
    r = client.post("/api/questions/channels", json={
        "mode": "push_only", "ntfy_topic": "t-abc",
        "pushover_token": "azGDORePK8gMaC0QOYAMyEEuzJnyUi"})
    assert r.get_json()["saved"]
    cfg = client.get("/api/questions/channels").get_json()
    assert cfg["mode"] == "push_only" and cfg["ntfy_topic"] == "t-abc"
    assert cfg["pushover_token"].endswith("…")
    assert client.post("/api/questions/channels",
                       json={"mode": "bogus"}).status_code == 400


def test_audit_csv_export(client):
    qid = client.post("/api/questions/ask", json={"question": "Audit me?"}) \
        .get_json()["correlationId"]
    client.post(f"/api/questions/{qid}/answer", json={"value": "yes"})
    audit = client.get("/api/questions/audit").get_json()
    assert audit["summary"]["total"] >= 1
    csv_resp = client.get("/api/questions/audit?format=csv")
    assert csv_resp.mimetype == "text/csv" and b"Audit me?" in csv_resp.data
