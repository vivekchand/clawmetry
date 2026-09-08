"""The Sessions API's ``surface`` field — where a session was launched from.

Claude Code, the Claude Desktop app (agent mode / Cowork's local ops) and
Agent-SDK runs all write into the same ``~/.claude/projects`` tree. The paid
Claude adapter reads the transcript's ``entrypoint`` and stamps
``metadata["surface"]``; this endpoint passes it through so the session row can
show a badge instead of labelling every desktop run "terminal".

The regression that matters here was caught against live data:
``metadata["source"]`` is ALREADY populated by other adapters with values that
are not surfaces at all — cwd paths (``/Users/…/projects/clawmetry``) and
provider names (``ollama``, ``openai``, ``qwen_code``). Reading ``source`` as a
fallback rendered those as surface badges on unrelated runtimes' sessions.
``surface`` is therefore read from its own key and nothing else.
"""
from __future__ import annotations

import pytest

import routes.sessions as rs


def _rows(*metas):
    return [
        {
            "agent_type": "openclaw",
            "session_id": "s%d" % i,
            "agent_id": "main",
            "title": "t",
            "metadata": m,
        }
        for i, m in enumerate(metas)
    ]


@pytest.fixture
def rows_from(monkeypatch):
    def _apply(*metas):
        monkeypatch.setattr(rs, "_fetch_sessions_table_rows", lambda limit=200: _rows(*metas))
        monkeypatch.setattr(rs, "_decorate_with_channel_context", lambda out: None)
        monkeypatch.setattr(rs, "_decorate_with_authority_counts", lambda out: None)
        return rs._try_local_store_sessions()["sessions"]
    return _apply


@pytest.mark.parametrize("surface", ["terminal", "desktop", "sdk"])
def test_surface_is_passed_through(rows_from, surface):
    out = rows_from({"runtime": "claude_code", "surface": surface})
    assert out[0]["surface"] == surface


def test_missing_surface_is_blank_not_guessed(rows_from):
    """Runtimes with a single surface must produce no badge at all."""
    out = rows_from({"runtime": "openclaw"})
    assert out[0]["surface"] == ""


@pytest.mark.parametrize(
    "source",
    [
        "ollama",                            # provider name (picoclaw, opencode)
        "openai",                            # provider name (codex, pi)
        "qwen_code",                         # adapter's own name
        "/Users/vivek/projects/clawmetry",   # cwd (grok, copilot, deepseek)
        "cli",                               # qm's own slack|web|cli surface
        "vm-usage-log",                      # synthetic ingest marker
    ],
)
def test_other_adapters_source_never_becomes_a_surface(rows_from, source):
    """metadata["source"] is a different field with different semantics.

    Live data on one machine carried all six of these values. Treating any of
    them as a surface puts "ollama" or a full cwd path in the badge slot of a
    session that has nothing to do with Claude's surfaces.
    """
    out = rows_from({"runtime": "picoclaw", "source": source})
    assert out[0]["surface"] == ""


def test_surface_wins_when_both_keys_are_present(rows_from):
    out = rows_from({"runtime": "claude_code", "surface": "desktop", "source": "desktop"})
    assert out[0]["surface"] == "desktop"
