"""Runtime-aware Logs API tests (Workstream C — runtime feature parity).

Covers the adapter-registry dispatch added to /api/logs and
/api/logs-stream:

  - ?runtime=<rt> with no registered adapter      -> available=false + reason
  - registered adapter with NO log sources        -> available=false + reason
    (HTTP 200 both times — "no logs" is a state, not an error)
  - file-kind LogSource                           -> tail lines served
  - command-kind LogSource ({lines} placeholder)  -> command output served
  - SSE: no source -> single honest event then a clean `done`
  - SSE: file source -> log-meta + initial tail, then live follow

Hermetic: a stub `dashboard` module is injected into sys.modules so the
stream-slot accounting resolves without importing the real 20k-line module.
"""

from __future__ import annotations

import json
import sys
import types

import pytest
from flask import Flask

from clawmetry.adapters import registry
from clawmetry.adapters.base import AgentAdapter, Capability, DetectResult, LogSource


# ── fixtures ───────────────────────────────────────────────────────────────


class _FakeAdapter(AgentAdapter):
    """Minimal adapter whose log_sources() is injectable."""

    def __init__(self, name: str, sources: list[LogSource]):
        self.name = name
        self.display_name = name.replace("_", " ").title()
        self._sources = sources

    def detect(self) -> DetectResult:
        return DetectResult(
            name=self.name, display_name=self.display_name, detected=True
        )

    def list_sessions(self, limit: int = 100):
        return []

    def capabilities(self):
        caps = {Capability.SESSIONS}
        if self._sources:
            caps.add(Capability.LOGS)
        return caps

    def log_sources(self):
        return list(self._sources)


@pytest.fixture
def app(monkeypatch):
    # Stub dashboard so the SSE route's slot accounting stays hermetic.
    stub = types.ModuleType("dashboard")
    stub._acquire_stream_slot = lambda kind: True
    stub._release_stream_slot = lambda kind: None
    stub.SSE_MAX_SECONDS = 30
    stub.LOG_DIR = None
    # Legacy openclaw path helpers (re-exported from helpers/logs.py in the
    # real dashboard module).
    from helpers.logs import _find_log_file, _tail_lines

    stub._find_log_file = _find_log_file
    stub._tail_lines = _tail_lines
    stub._ext_emit = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "dashboard", stub)

    import routes.infra as infra

    app = Flask(__name__)
    app.register_blueprint(infra.bp_logs)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def fake_runtime(tmp_path):
    """Register a fake adapter with one real temp-file LogSource."""
    log_file = tmp_path / "fake.log"
    log_file.write_text("alpha\nbeta\ngamma\ndelta\n")
    adapter = _FakeAdapter(
        "fakert",
        [
            LogSource(
                id="fake-file",
                label="Fake runtime log",
                kind="file",
                path=str(log_file),
                format="text",
            )
        ],
    )
    registry.register(adapter)
    yield adapter, log_file
    registry.unregister("fakert")


# ── /api/logs ──────────────────────────────────────────────────────────────


def test_logs_unknown_runtime_is_honest_200(client):
    r = client.get("/api/logs?runtime=definitely_not_a_runtime")
    assert r.status_code == 200
    d = r.get_json()
    assert d["runtime"] == "definitely_not_a_runtime"
    assert d["available"] is False
    assert d["lines"] == []
    assert "no adapter registered" in d["reason"]


def test_logs_claude_code_no_source_reason(client):
    """(a) runtime registered but exposing no log source -> honest reason."""
    registry.register(_FakeAdapter("claude_code", []))
    try:
        r = client.get("/api/logs?runtime=claude_code")
        assert r.status_code == 200
        d = r.get_json()
        assert d["runtime"] == "claude_code"
        assert d["available"] is False
        assert d["label"] is None and d["source"] is None
        assert d["lines"] == []
        assert "no daemon log stream" in d["reason"]
    finally:
        registry.unregister("claude_code")


def test_logs_file_source_tail(client, fake_runtime):
    _, log_file = fake_runtime
    r = client.get("/api/logs?runtime=fakert&lines=2")
    assert r.status_code == 200
    d = r.get_json()
    assert d["available"] is True
    assert d["runtime"] == "fakert"
    assert d["label"] == "Fake runtime log"
    assert d["source"] == str(log_file)
    assert d["format"] == "text"
    assert d["lines"] == ["gamma", "delta"]
    assert d["reason"] is None


def test_logs_command_source_with_lines_placeholder(client):
    adapter = _FakeAdapter(
        "cmdrt",
        [
            LogSource(
                id="cmd",
                label="Command source",
                kind="command",
                command=[
                    sys.executable,
                    "-c",
                    "import sys; print('n=' + sys.argv[1])",
                    "{lines}",
                ],
                format="text",
            )
        ],
    )
    registry.register(adapter)
    try:
        r = client.get("/api/logs?runtime=cmdrt&lines=7")
        assert r.status_code == 200
        d = r.get_json()
        assert d["available"] is True
        assert d["lines"] == ["n=7"]
        assert "n=" not in (d["reason"] or "")
    finally:
        registry.unregister("cmdrt")


def test_logs_openclaw_default_path_unchanged(client):
    """No runtime param -> legacy shape ({lines, date}), not the new envelope."""
    r = client.get("/api/logs?lines=5")
    assert r.status_code == 200
    d = r.get_json()
    assert "lines" in d and "date" in d
    assert "available" not in d  # legacy envelope untouched


# ── /api/logs-stream ───────────────────────────────────────────────────────


def _sse_events(raw: str) -> list[str]:
    return [b for b in raw.split("\n\n") if b.strip()]


def test_stream_no_source_single_event_then_done(client):
    registry.register(_FakeAdapter("claude_code", []))
    try:
        r = client.get("/api/logs-stream?runtime=claude_code")
        assert r.status_code == 200
        assert r.mimetype == "text/event-stream"
        body = r.get_data(as_text=True)  # generator terminates -> safe
        events = _sse_events(body)
        assert len(events) == 2
        payload = json.loads(events[0].split("data: ", 1)[1])
        assert payload["available"] is False
        assert payload["runtime"] == "claude_code"
        assert "no daemon log stream" in payload["reason"]
        assert "event: done" in events[1]
        assert "no_log_source" in events[1]
    finally:
        registry.unregister("claude_code")


def test_stream_command_follow_source(client):
    """A command source with a follow_command streams its stdout lines."""
    adapter = _FakeAdapter(
        "dockerish",
        [
            LogSource(
                id="cmd-follow",
                label="Follow command",
                kind="command",
                command=[sys.executable, "-c", "print('tail')"],
                follow_command=[
                    sys.executable,
                    "-c",
                    "print('one'); print('two')",
                ],
                format="text",
            )
        ],
    )
    registry.register(adapter)
    try:
        r = client.get("/api/logs-stream?runtime=dockerish")
        assert r.status_code == 200
        body = r.get_data(as_text=True)  # command exits -> stream ends
        events = _sse_events(body)
        assert any("log-meta" in e for e in events)
        lines = [
            json.loads(e.split("data: ", 1)[1])["line"]
            for e in events
            if e.startswith("data: ")
        ]
        assert lines == ["one", "two"]
        assert any("stream_ended" in e for e in events)
    finally:
        registry.unregister("dockerish")


def test_stream_file_source_meta_and_initial_tail(client, fake_runtime):
    _, log_file = fake_runtime
    r = client.get("/api/logs-stream?runtime=fakert")
    assert r.status_code == 200
    assert r.mimetype == "text/event-stream"

    # log-meta + 4 initial tail lines are yielded eagerly, before the
    # follow loop starts sleeping — pull exactly those 5 then close.
    it = iter(r.response)
    chunks: list[str] = []
    for _ in range(5):
        item = next(it)
        chunks.append(item.decode() if isinstance(item, bytes) else item)
    r.response.close()  # stop the follow generator cleanly

    joined = "".join(chunks)
    assert "event: log-meta" in joined
    meta = json.loads(
        [e for e in _sse_events(joined) if "log-meta" in e][0].split("data: ", 1)[1]
    )
    assert meta["available"] is True
    assert meta["source"] == str(log_file)
    lines = [
        json.loads(e.split("data: ", 1)[1])["line"]
        for e in _sse_events(joined)
        if e.startswith("data: ")
    ]
    assert "delta" in lines  # tail reached the end of the file
