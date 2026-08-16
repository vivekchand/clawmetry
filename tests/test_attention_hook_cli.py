"""`clawmetry hook attention` — the one-line runtime wiring client.

This runs INSIDE somebody's agent, at the moment that agent is asking a human
for permission. So the contract under test is mostly about what it must never
do: never exit non-zero, never write to stdout, never hang, never decide
anything. A hook that breaks any of those can change what the runtime does
next, and no badge is worth that.

Losing a report costs precision, not the feature — the daemon's inference
pass still covers the session. That asymmetry is why every failure path here
is a silent no-op rather than an error.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from clawmetry.attention_hook import attention_main


@pytest.fixture()
def sink():
    """A local receiver that records what the client sends."""
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            seen.append({"path": self.path,
                         "body": self.rfile.read(n).decode()})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    srv.seen = seen
    srv.base = f"http://127.0.0.1:{srv.server_port}"
    yield srv
    srv.shutdown()


def _run(monkeypatch, capsys, payload, *args):
    monkeypatch.setattr("sys.stdin",
                        __import__("io").StringIO(payload))
    rc = attention_main(list(args))
    out = capsys.readouterr()
    return rc, out


# ── it forwards what the runtime said ───────────────────────────────────────

def test_forwards_the_payload_unmodified(sink, monkeypatch, capsys):
    """The client stays dumb: the receiver knows every spelling of session id
    and tool name, so translating here would be a second place to get it
    wrong."""
    body = '{"session_id":"cli-1","tool_name":"Bash","extra":"kept"}'
    rc, _ = _run(monkeypatch, capsys, body,
                 "--runtime", "qwen_code", "--base", sink.base)
    assert rc == 0
    assert len(sink.seen) == 1
    assert json.loads(sink.seen[0]["body"]) == json.loads(body)


def test_runtime_and_event_ride_the_query_string(sink, monkeypatch, capsys):
    _run(monkeypatch, capsys, '{"session_id":"a"}',
         "--runtime", "gemini_cli", "--base", sink.base)
    assert "runtime=gemini_cli" in sink.seen[0]["path"]
    assert "event=waiting" in sink.seen[0]["path"]


def test_resolved_event_is_passed_through(sink, monkeypatch, capsys):
    _run(monkeypatch, capsys, '{"session_id":"a"}',
         "--runtime", "qwen_code", "--event", "resolved", "--base", sink.base)
    assert "event=resolved" in sink.seen[0]["path"]


# ── it never disturbs the agent ─────────────────────────────────────────────

def test_stdout_stays_empty_on_success(sink, monkeypatch, capsys):
    """Anything on stdout can be read by the runtime as a hook decision."""
    _, out = _run(monkeypatch, capsys, '{"session_id":"a"}',
                  "--runtime", "codex", "--base", sink.base)
    assert out.out == ""
    assert out.err == ""


def test_missing_runtime_is_a_silent_noop(sink, monkeypatch, capsys):
    rc, out = _run(monkeypatch, capsys, '{"session_id":"a"}',
                   "--base", sink.base)
    assert rc == 0 and out.out == ""
    assert sink.seen == [], "nothing attributable — must not guess a runtime"


@pytest.mark.parametrize("payload", ["", "not json", "[1,2,3]", "null"])
def test_malformed_stdin_still_exits_zero(sink, monkeypatch, capsys, payload):
    rc, out = _run(monkeypatch, capsys, payload,
                   "--runtime", "codex", "--base", sink.base)
    assert rc == 0 and out.out == ""


def test_unreachable_dashboard_exits_zero(monkeypatch, capsys):
    """Port 9 is reliably closed. Losing the report costs precision; a
    non-zero exit could cost the user their turn."""
    rc, out = _run(monkeypatch, capsys, '{"session_id":"a"}',
                   "--runtime", "codex", "--base", "http://127.0.0.1:9")
    assert rc == 0 and out.out == ""


def test_flag_at_end_of_argv_does_not_crash(sink, monkeypatch, capsys):
    """`--runtime` with nothing after it is a typo, not a reason to raise."""
    rc, out = _run(monkeypatch, capsys, '{"session_id":"a"}', "--runtime")
    assert rc == 0 and out.out == ""


def test_it_never_answers_the_prompt(sink, monkeypatch, capsys):
    """Observation only. If this ever printed a hookSpecificOutput envelope
    it would be deciding on the user's behalf from the wrong code path."""
    _, out = _run(monkeypatch, capsys, '{"session_id":"a","tool_name":"Bash"}',
                  "--runtime", "qwen_code", "--base", sink.base)
    assert "hookSpecificOutput" not in out.out
    assert "permissionDecision" not in out.out
