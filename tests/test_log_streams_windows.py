"""Regression tests for portable log streaming (#windows-streams).

Windows broke every log stream three different ways:
- ``Popen(["openclaw", ...])`` cannot launch the npm ``openclaw.cmd``
  wrapper (CreateProcess wants the full name with extension), so
  /api/logs-stream crashed with FileNotFoundError mid-SSE and the
  frontend's retries then drowned in 429s.
- ``select.select()`` on a pipe is POSIX-only (Windows select works on
  sockets exclusively), used by both SSE generators, the daemon
  gateway-log streamer, and the sandbox OCSF drain.
- ``tail`` does not exist on Windows (dashboard fallback stream and the
  daemon streamer spawned it).

The fix: ``process_control.PipeLineReader`` (thread+queue pump) for
subprocess pipes, pure-Python file follows instead of ``tail``, and
``shutil.which()`` resolution for the openclaw binary.
"""

import io
import re
import subprocess
import sys
import time
import types
from pathlib import Path

from clawmetry.process_control import PipeLineReader


def test_pipe_line_reader_reads_live_subprocess():
    proc = subprocess.Popen(
        [sys.executable, "-c", "print('alpha'); print('beta')"],
        stdout=subprocess.PIPE, text=True,
    )
    reader = PipeLineReader(proc.stdout)
    lines = []
    deadline = time.time() + 10
    while len(lines) < 2 and time.time() < deadline:
        line = reader.readline(0.5)
        if line is not None:
            lines.append(line.strip())
    proc.wait(timeout=10)
    assert lines == ["alpha", "beta"]
    deadline = time.time() + 5
    while not reader.eof and time.time() < deadline:
        time.sleep(0.05)
    assert reader.eof
    assert reader.readline(0) is None


def test_pipe_line_reader_timeout_zero_polls_buffered_only():
    reader = PipeLineReader(io.StringIO("one\n"))
    deadline = time.time() + 5
    line = None
    while line is None and time.time() < deadline:
        line = reader.readline(0)
    assert line == "one\n"
    assert reader.readline(0) is None


def test_json_log_stream_uses_resolved_binary_and_no_select(monkeypatch):
    """Red on the un-fixed code twice over: argv[0] was a bare "openclaw"
    (WinError 2 on Windows), and select.select on a fake pipe raises."""
    import routes.infra as infra

    captured = {}

    class _FakeProc:
        def __init__(self):
            self.stdout = io.StringIO(
                '{"type":"log","message":"hello-stream"}\n'
            )
        def kill(self):
            pass

    def fake_popen(argv, **kwargs):
        captured["argv"] = argv
        return _FakeProc()

    monkeypatch.setattr(infra.subprocess, "Popen", fake_popen)
    import shutil as _shutil
    monkeypatch.setattr(_shutil, "which", lambda name: r"C:\fake\openclaw.CMD")

    released = []
    gen = infra._generate_openclaw_json_logs(
        started_at=time.time(), sse_max_seconds=5, release_fn=lambda: released.append(1)
    )
    events = []
    for ev in gen:
        events.append(ev)
        if len(events) >= 2:
            break
    assert captured["argv"][0] == r"C:\fake\openclaw.CMD"
    assert any("hello-stream" in e for e in events)
    # Stream ends (eof) rather than spinning until max_duration.
    assert any("stream_ended" in e or "max_duration" in e for e in events)


# ── Class guard: the POSIX idioms must not come back ──────────────────────

_REPO = Path(__file__).resolve().parents[1]
_STREAM_FILES = [
    _REPO / "routes" / "infra.py",
    _REPO / "clawmetry" / "sync.py",
]


def _code_lines(path):
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
    ):
        yield lineno, line.split("#", 1)[0]


def test_no_select_on_pipes_in_stream_paths():
    offenders = [
        f"{p.name}:{n}" for p in _STREAM_FILES
        for n, code in _code_lines(p) if re.search(r"\bselect\.select\(", code)
    ]
    assert offenders == [], (
        f"select.select on a pipe is POSIX-only; use PipeLineReader: {offenders}"
    )


def test_no_tail_subprocess_in_stream_paths():
    offenders = [
        f"{p.name}:{n}" for p in _STREAM_FILES
        for n, code in _code_lines(p) if re.search(r"\"tail\"", code)
    ]
    assert offenders == [], (
        f"`tail` does not exist on Windows; follow the file in Python: {offenders}"
    )
