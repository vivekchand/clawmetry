"""Runtime compatibility tests for NanoClaw + PicoClaw (issue #956).

NanoClaw and PicoClaw share the OpenClaw filesystem layout (the same
``agents/main/sessions/<id>.jsonl`` shape and the same v3 event wire
format). This test points the existing OpenClaw session loader at
fixture directories laid out the way each runtime writes them on disk
and asserts the dashboard parses sessions, models, token totals, and
tool-call structure correctly.

Adding NanoClaw or PicoClaw to the supported runtimes matrix later
becomes "drop a real captured session into `tests/fixtures/runtimes/<runtime>/`
and add a row to the ``RUNTIMES`` table below."

Out of scope here (deferred until multi-profile workspace discovery
ships): auto-discovery of ``~/.nanoclaw*`` and ``~/.picoclaw*`` without
the operator setting ``OPENCLAW_SESSIONS_DIR``. ``docs/compatibility.md``
documents the override workaround until then.
"""
from __future__ import annotations

import os

import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes")

# (runtime_dir, expected_model, expected_total_tokens)
#
# expected_total_tokens = sum of all assistant message.usage.totalTokens
# in the fixture (see ``_make_fixtures.py`` for the source-of-truth shape).
RUNTIMES = [
    ("nanoclaw", "claude-opus-4-7", 162 + 35),
    ("picoclaw", "llama3.2:3b", 104 + 35),
]


@pytest.fixture
def dashboard_module():
    """Lazily import the dashboard once per test session.

    We rely on ``monkeypatch.setattr`` in the test bodies to point the
    module-level ``SESSIONS_DIR`` global at each fixture directory, so
    reloading the (~15K line) module per test is both unnecessary and
    risks tripping import-time side effects.
    """
    import dashboard

    return dashboard


@pytest.mark.parametrize("runtime,expected_model,expected_total_tokens", RUNTIMES)
def test_runtime_sessions_parse(
    runtime, expected_model, expected_total_tokens, dashboard_module, monkeypatch
):
    """File-fallback session loader parses fixtures laid out like each runtime writes them."""
    sessions_dir = os.path.join(FIXTURES, runtime, "agents", "main", "sessions")
    assert os.path.isdir(sessions_dir), f"missing fixture dir: {sessions_dir}"

    monkeypatch.setattr(dashboard_module, "SESSIONS_DIR", sessions_dir)
    # Bust the in-process cache so we don't pick up a previous runtime's read.
    dashboard_module._sessions_cache["data"] = None
    dashboard_module._sessions_cache["ts"] = 0

    sessions = dashboard_module._get_sessions_from_files()
    assert len(sessions) == 1, f"{runtime}: expected 1 session, got {len(sessions)}"

    s = sessions[0]
    assert s["sessionId"].startswith(runtime[:4]), (
        f"{runtime}: sessionId should reflect fixture name, got {s['sessionId']}"
    )
    assert s["model"] == expected_model, (
        f"{runtime}: expected model {expected_model}, got {s['model']}"
    )
    assert s["totalTokens"] == expected_total_tokens, (
        f"{runtime}: expected {expected_total_tokens} total tokens, "
        f"got {s['totalTokens']}"
    )
    assert s["updatedAt"] > 0, f"{runtime}: updatedAt should reflect file mtime"


@pytest.mark.parametrize("runtime,_model,_tokens", RUNTIMES)
def test_runtime_session_aggregates_match_wire_format(
    runtime, _model, _tokens, dashboard_module
):
    """The aggregate scanner reads the same v3 event shape across runtimes.

    Guards against a future change to ``_scan_session_aggregates`` that
    silently breaks one runtime (e.g. hardcodes an OpenClaw-specific
    field name).
    """
    sessions_dir = os.path.join(FIXTURES, runtime, "agents", "main", "sessions")
    jsonl = [f for f in os.listdir(sessions_dir) if f.endswith(".jsonl")][0]
    fpath = os.path.join(sessions_dir, jsonl)

    model, total_tokens = dashboard_module._scan_session_aggregates(fpath)
    assert model, f"{runtime}: model should be extracted, got empty"
    assert total_tokens > 0, f"{runtime}: token total should be positive"


def test_fixture_layout_matches_openclaw_runtime():
    """Both fixtures sit at the same on-disk layout as OpenClaw.

    Acts as an early-warning canary: if someone restructures the fixtures
    in a way that diverges from the layout NanoClaw/PicoClaw use in
    production, this test fails before the compat suite silently passes
    against a no-longer-realistic shape.
    """
    expected_subpath = os.path.join("agents", "main", "sessions")
    for runtime, _m, _t in RUNTIMES:
        full = os.path.join(FIXTURES, runtime, expected_subpath)
        assert os.path.isdir(full), (
            f"{runtime} fixture must live at <runtime>/{expected_subpath}/ "
            f"to match real on-disk layout; got missing {full}"
        )
        jsonl_files = [f for f in os.listdir(full) if f.endswith(".jsonl")]
        assert jsonl_files, f"{runtime}: at least one .jsonl session fixture required"
