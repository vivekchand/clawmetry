"""Sessions must carry their OWN runtime, not a blanket 'openclaw'.

Founder live-hit 2026-08-23: the Fleet showed `Claude Code · 537` stuck on
"detected here — syncing to cloud" on the Linux node while the Mac's
`Claude Code · 49` synced green — and the Brain/Activity tab on that same
Linux node was streaming live Claude Code events the whole time.

Root cause: ``sync._local_ingest_sessions_batch`` stamped

    "agent_type": s.get("agent_type") or "openclaw"

but the family adapters never set ``agent_type`` — they carry the runtime in
``runtime`` and in the ``<runtime>:<uuid>`` session_id prefix. So every paid
runtime's sessions were written as 'openclaw'. Live store at the time:

    query_rollup_sessions(limit=500) -> 152 rows, Counter({'openclaw': 152})
    ...including session_id 'claude_code:36f12caf-...' labelled openclaw.

``_refresh_runtime_day_session_counts_locked`` filters ``WHERE agent_type = ?``,
so claude_code rolled up with sessions=0 and the Fleet card had nothing to
mark synced. The event side was fine because it splits on the session_id
prefix, which is why Activity worked and Fleet did not.

Acceptance criteria covered:

* AC-OBS-003.1 -- when the system recognizes a supported runtime, it associates
  that runtime's activity with it: ``test_batch_ingest_stamps_the_real_runtime``
  proves a Claude Code / Codex session is stored under its own runtime instead
  of being folded into openclaw.
"""

import pytest

from clawmetry.sync import _session_agent_type
from clawmetry.local_store import _NON_OPENCLAW_RUNTIME_PREFIXES


def test_runtime_from_session_id_prefix():
    """The prefix is authoritative when the adapter sets no explicit field."""
    assert _session_agent_type({}, "claude_code:66bfb3ac-b2b8-4700") == "claude_code"
    assert _session_agent_type({}, "codex:abc-123") == "codex"
    assert _session_agent_type({}, "cursor:xyz") == "cursor"


def test_explicit_agent_type_wins():
    got = _session_agent_type({"agent_type": "goose"}, "claude_code:1")
    assert got == "goose"


def test_runtime_field_is_used_when_agent_type_absent():
    got = _session_agent_type({"runtime": "aider"}, "whatever")
    assert got == "aider"


@pytest.mark.parametrize(
    "sid",
    [
        "",
        "main",
        "some-plain-uuid-with-no-prefix",
        # A colon alone must not invent a runtime, or an OpenClaw session key
        # would be silently re-homed under a bogus runtime name.
        "telegram:12345",
        "unknown_runtime:abc",
    ],
)
def test_openclaw_remains_the_default(sid):
    assert _session_agent_type({}, sid) == "openclaw"


def test_every_known_prefix_round_trips():
    """Guards the constant and the helper against drifting apart."""
    for prefix in _NON_OPENCLAW_RUNTIME_PREFIXES:
        assert _session_agent_type({}, f"{prefix}:sid-1") == prefix


def test_batch_ingest_stamps_the_real_runtime(monkeypatch):
    """End-to-end through the batch builder: the rows handed to the store must
    carry per-runtime agent_type, since that column is what the Fleet counts."""
    import clawmetry.sync as sync

    captured = {}

    class _FakeStore:
        def ingest_sessions_batch(self, rows):
            captured["rows"] = rows

    monkeypatch.setattr("clawmetry.local_store.get_store", lambda: _FakeStore())

    sync._local_ingest_sessions_batch(
        [
            {"session_id": "claude_code:aaa", "total_tokens": 10},
            {"session_id": "codex:bbb", "total_tokens": 20},
            {"session_id": "plain-openclaw-session", "total_tokens": 30},
        ],
        node_id="node-1",
    )

    by_id = {r["session_id"]: r["agent_type"] for r in captured["rows"]}
    assert by_id == {
        "claude_code:aaa": "claude_code",
        "codex:bbb": "codex",
        "plain-openclaw-session": "openclaw",
    }
