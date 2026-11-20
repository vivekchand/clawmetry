"""Traversal containment for the filesystem-backed read endpoints.

Reported privately against 0.12.943 (CWE-22): ``GET /api/reasoning?session=``
joined the query value onto the sessions directory with no validation, so an
absolute or ``../`` value read the assistant thinking out of any ``.jsonl``
the dashboard user could open. Loopback callers are trusted without a
credential, so any other local account could read the dashboard user's
transcripts. GHSA-6r57-3vhv-2wpf set out to contain every transcript
endpoint; this one was missed.

The reporter also flagged ``?date=`` on /api/logs and ``<skill_name>`` on
/api/skills, which build paths the same way.

Each traversal case here is paired with a positive case that reads a real
file through the same code path — a 400 from a handler that could not have
served the file anyway would prove nothing.
"""

from __future__ import annotations

import json
import os
import sys

import pytest
from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THINKING = "SECRET-THOUGHT outside sessions dir"


def _jsonl_line(thought):
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": thought},
                    {"type": "text", "text": "hi"},
                ],
            },
        }
    )


@pytest.fixture
def reasoning(tmp_path, monkeypatch):
    """Flask client for /api/reasoning over a real sessions dir on disk."""
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "s1.jsonl").write_text(_jsonl_line("normal session thought") + "\n")

    outside = tmp_path / "private"
    outside.mkdir()
    secret = outside / "secret.jsonl"
    secret.write_text(_jsonl_line(THINKING) + "\n")

    import dashboard as _d

    # routes/reasoning.py reads SESSIONS_DIR through a late `import dashboard`,
    # so patch the attribute on the real module rather than a reload-local copy.
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(sessions), raising=False)

    import routes.reasoning as rea

    app = Flask(__name__)
    app.register_blueprint(rea.bp_reasoning)
    return app.test_client(), secret


def test_reasoning_serves_a_real_session(reasoning):
    """Positive control: the traversal cases below exercise a live handler."""
    client, _ = reasoning
    r = client.get("/api/reasoning?session=s1")
    assert r.status_code == 200
    assert "normal session thought" in json.dumps(r.get_json())


@pytest.mark.parametrize(
    "payload",
    [
        "{abs}",                      # absolute path — os.path.join drops the base
        "../private/secret",          # relative escape
        "..%2fprivate%2fsecret",      # encoded separator
        "....//private//secret",      # doubled-dot bypass of a naive "../" strip
        "..\\private\\secret",        # Windows separator
    ],
)
def test_reasoning_refuses_to_leave_the_sessions_dir(reasoning, payload):
    client, secret = reasoning
    sid = payload.format(abs=str(secret)[: -len(".jsonl")])
    r = client.get(f"/api/reasoning?session={sid}")
    body = r.get_data(as_text=True)
    assert THINKING not in body, f"leaked thinking for session={sid!r}"
    assert r.status_code == 400, f"expected a rejection for session={sid!r}"


def test_reasoning_parser_contains_a_direct_caller(reasoning, tmp_path):
    """The helper must refuse too — the route is not the only caller."""
    _, secret = reasoning
    import routes.reasoning as rea

    assert rea._parse_session_reasoning(str(secret)[: -len(".jsonl")]) == []
    assert rea._parse_session_reasoning("../private/secret") == []


def test_log_date_cannot_escape_the_log_dir(tmp_path, monkeypatch):
    """?date= is interpolated into openclaw-{date}.log."""
    import dashboard as _d
    import helpers.logs as hl

    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "openclaw-2026-11-18.log").write_text("real log line\n")
    # An existing first segment is all a POSIX ".." escape needs.
    nested = logs / "openclaw-x"
    nested.mkdir()
    (tmp_path / "openclaw-pwn.log").write_text("outside\n")

    monkeypatch.setattr(_d, "LOG_DIR", str(logs), raising=False)
    monkeypatch.setattr(hl, "_get_log_dirs", lambda: [str(logs)])

    assert hl._find_log_file("2026-11-18") == str(logs / "openclaw-2026-11-18.log")
    assert hl._find_log_file("x/../../openclaw-pwn") is None
    assert hl._find_log_file("x\\..\\..\\openclaw-pwn") is None
    assert hl._find_log_file("../openclaw-pwn") is None


def test_skill_name_cannot_select_a_dir_outside_the_skills_root(tmp_path, monkeypatch):
    """<skill_name> is joined onto each skills root."""
    import routes.skills as sk

    root = tmp_path / "skills"
    (root / "real").mkdir(parents=True)
    (root / "real" / "SKILL.md").write_text("---\nname: real\n---\nbody\n")

    # A directory outside the root that also carries a SKILL.md.
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "SKILL.md").write_text("---\nname: pwn\n---\nsecret\n")

    monkeypatch.setattr(sk, "_get_skills_dirs", lambda: [str(root)])

    assert sk._find_skill_dir("real") == str(root / "real")
    assert sk._find_skill_dir("../elsewhere") is None
    assert sk._find_skill_dir("..\\elsewhere") is None
    assert sk._find_skill_dir(str(outside)) is None


@pytest.mark.parametrize("bad", ["", "..", "../x", "a/b", "a\\b", "x\x00y", "a..b", None])
def test_component_check_rejects(bad):
    from clawmetry.file_security import is_safe_path_component

    assert is_safe_path_component(bad) is False


@pytest.mark.parametrize("ok", ["s1", "claudecode:9f3b-12", "2026-11-18", "a.jsonl"])
def test_component_check_allows_real_ids(ok):
    from clawmetry.file_security import is_safe_path_component

    assert is_safe_path_component(ok) is True
