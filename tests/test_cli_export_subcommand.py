"""``clawmetry export`` — audit export CLI against a fixture HTTP endpoint.

Regression note: the CSV branch once dropped every row because a NameError
inside its per-line try/except was silently swallowed — these tests assert
actual row content, not just exit codes.
"""
import argparse
import http.server
import json
import threading

import pytest

from clawmetry import cli

EVENTS = [
    {
        "id": "e1",
        "node_id": "n1",
        "agent_type": "claude_code",
        "agent_id": "main",
        "session_id": "s1",
        "event_type": "tool.call",
        "ts": "2026-07-30T10:00:00",
        "model": "",
        "token_count": 5,
        "cost_usd": 0.01,
        "data": {"name": "Bash"},
        "received_at": "2026-07-30T10:00:01",
    },
    {
        "id": "e2",
        "node_id": "n1",
        "agent_type": "claude_code",
        "agent_id": "main",
        "session_id": "s1",
        "event_type": "message",
        "ts": "2026-07-30T11:00:00",
        "model": "m",
        "token_count": None,
        "cost_usd": None,
        "data": None,
        "received_at": "2026-07-30T11:00:01",
    },
]


@pytest.fixture
def export_server(monkeypatch):
    requests_seen = []

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            requests_seen.append(
                {"path": self.path, "api_key": self.headers.get("X-Api-Key")}
            )
            if self.headers.get("X-Api-Key") != "cm_export_tok":
                self.send_response(401)
                self.end_headers()
                return
            body = "".join(json.dumps(e) + "\n" for e in EVENTS).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv(
        "CLAWMETRY_ENDPOINT", f"http://127.0.0.1:{server.server_port}"
    )
    monkeypatch.setenv("CLAWMETRY_API_KEY", "cm_export_tok")
    yield requests_seen
    server.shutdown()
    server.server_close()


def _ns(**kw):
    defaults = {
        "date_from": None,
        "date_to": None,
        "format": "jsonl",
        "out": None,
    }
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def test_export_jsonl_to_file(export_server, tmp_path):
    out = tmp_path / "events.jsonl"
    cli._cmd_export(_ns(date_from="2026-07-01", date_to="2026-07-31", out=str(out)))
    lines = [json.loads(ln) for ln in out.read_text().splitlines()]
    assert [ln["id"] for ln in lines] == ["e1", "e2"]
    assert lines[0]["data"] == {"name": "Bash"}
    # Range params reached the server.
    assert "from=2026-07-01" in export_server[0]["path"]
    assert "to=2026-07-31" in export_server[0]["path"]


def test_export_csv_has_all_rows(export_server, tmp_path):
    out = tmp_path / "events.csv"
    cli._cmd_export(_ns(format="csv", out=str(out)))
    rows = out.read_text().splitlines()
    assert rows[0].startswith("id,node_id,agent_type")
    assert len(rows) == 1 + len(EVENTS)  # header + every event, none dropped
    assert rows[1].startswith("e1,")
    # dict data is embedded as a JSON string cell
    assert '{""name"":""Bash""}' in rows[1]


def test_export_bad_key_exits_nonzero(export_server, monkeypatch, capsys):
    monkeypatch.setenv("CLAWMETRY_API_KEY", "cm_wrong")
    with pytest.raises(SystemExit) as exc:
        cli._cmd_export(_ns())
    assert exc.value.code == 1
    assert "Unauthorized" in capsys.readouterr().out
