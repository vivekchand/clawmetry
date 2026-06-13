"""Tests for the snapshot `deviceSummary` slice (clawmetry/sync.py).

The WiFi hardware companion decrypts the cloud snapshot and reads this one
small slice. It must:
  1. Always be a well-formed shape (never crash — the device must always get a
     valid payload), carrying cost/tokens straight from the spending inputs.
  2. Count active sessions across runtimes and surface the OLDEST pending
     approval (the Approve/Deny button's source).
  3. Flip health to amber while an approval is waiting.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def sync_with_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()  # own the writer so the tmp store opens in-process

    import clawmetry.sync as sync
    importlib.reload(sync)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _keys():
    return ("schema", "cost_today_usd", "tokens_today", "active_sessions",
            "runtimes_active", "health", "alert", "approval")


def test_shape_and_cost_tokens_passthrough(sync_with_store):
    sync, _ls = sync_with_store
    s = sync._build_device_summary({"today": 4.2}, {"today": 1000})
    for k in _keys():
        assert k in s, f"missing key: {k}"
    # schema 2 = the additive per-runtime `runtimes` array (sync.py docstring);
    # every schema-1 field is preserved, asserted by _keys() above.
    assert s["schema"] == 2
    assert s["cost_today_usd"] == 4.2
    assert s["tokens_today"] == 1000
    assert s["active_sessions"] == 0
    assert s["runtimes_active"] == []
    assert s["health"] == "green"
    assert s["approval"] is None


def test_never_raises_on_missing_inputs(sync_with_store):
    sync, _ls = sync_with_store
    s = sync._build_device_summary(None, None)
    assert s["cost_today_usd"] == 0.0
    assert s["tokens_today"] == 0
    assert s["health"] == "green"


def test_active_sessions_and_oldest_approval(sync_with_store):
    sync, ls = sync_with_store
    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-active",
        "agent_type": "openclaw",
        "status": "active",
        "started_at": "2026-06-04T10:00:00+00:00",
        "last_active_at": "2026-06-04T11:00:00+00:00",
    })
    store.ingest_session({
        "session_id": "sess-ended",
        "agent_type": "openclaw",
        "status": "ended",
        "started_at": "2026-06-03T09:00:00+00:00",
        "last_active_at": "2026-06-03T10:00:00+00:00",
    })
    store.ingest_approval({
        "id": "app-new", "requestor_session_id": "sess-active",
        "action": "write_file", "status": "pending",
        "created_at": "2026-06-04T10:05:00+00:00",
    })
    store.ingest_approval({
        "id": "app-old", "requestor_session_id": "sess-active",
        "action": "bash", "status": "pending",
        "created_at": "2026-06-04T10:00:00+00:00",  # older
    })
    # drain ring so the SELECTs see the rows
    import time
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and store.health()["ring_depth"] != 0:
        time.sleep(0.02)

    s = sync._build_device_summary({"today": 0}, {"today": 0})
    assert s["active_sessions"] == 1
    assert s["runtimes_active"] == ["openclaw"]
    assert s["approval"] is not None
    assert s["approval"]["id"] == "app-old"  # oldest pending, not newest
    assert s["approval"]["action"] == "bash"
    assert s["approval"]["runtime"] == "openclaw"
    assert s["health"] == "amber"  # a human is needed


def test_session_titles_ride_encrypted_summary_not_uuid(sync_with_store):
    """The device's runtime-detail recent-session rows must show the session's
    first-message title (real content), not a raw UUID. That title is content,
    so it rides the ENCRYPTED deviceSummary (sessionTitles), keyed by the BARE
    session id, never the plaintext device-agent endpoint."""
    import time
    sync, ls = sync_with_store
    store = ls.get_store()
    store.ingest_session({
        "session_id": "claude_code:e149acae-8789-4f61-b365-3b356bf07f88",
        "agent_type": "claude_code",
        "status": "ended",
        "title": "read flywheel.md && ../clawmetry-cloud/flywheel.md",
        "started_at": "2026-06-08T09:00:00+00:00",
        "last_active_at": "2026-06-08T11:00:00+00:00",
    })
    store.ingest_session({
        "session_id": "claude_code:e0dbf7e3-2301-4abc-9def-000000000000",
        "agent_type": "claude_code",
        "status": "ended",
        "title": "what does github sponsoring mean??",
        "started_at": "2026-06-08T08:00:00+00:00",
        "last_active_at": "2026-06-08T10:00:00+00:00",
    })
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and store.health()["ring_depth"] != 0:
        time.sleep(0.02)

    s = sync._build_device_summary({"today": 0}, {"today": 0})
    titles = s.get("sessionTitles")
    assert isinstance(titles, dict) and titles, s
    # keyed by the BARE id (post-':'), value is the human title, never the uuid
    assert titles.get("e149acae-8789-4f61-b365-3b356bf07f88") == \
        "read flywheel.md && ../clawmetry-cloud/flywheel.md"
    assert titles.get("e0dbf7e3-2301-4abc-9def-000000000000") == \
        "what does github sponsoring mean??"
    # the prefixed form is NOT a key (firmware looks up the bare device-agent id)
    assert "claude_code:e149acae-8789-4f61-b365-3b356bf07f88" not in titles
    # values are never a bare uuid (i.e. content, not an id)
    import re
    uuid = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-')
    for v in titles.values():
        assert not uuid.match(v), v


def test_efficiency_subslice_present_when_graded(sync_with_store):
    """A valid efficiency slice yields a one-letter grade + summed monthly
    savings on deviceSummary; the device renders it as the glance sub-line."""
    sync, _ls = sync_with_store
    eff = {
        "grade": "B", "score": 78, "insufficient_data": False,
        "actions": [
            {"id": "model_downgrade", "savings_monthly_usd": 14.2},
            {"id": "context_trim", "savings_monthly_usd": 9.1},
            {"id": "cache_warm", "savings_monthly_usd": "garbage"},  # coerced to 0
        ],
    }
    s = sync._build_device_summary({"today": 1.0}, {"today": 10}, efficiency=eff)
    assert s["efficiency"] == {"grade": "B", "save_monthly_usd": 23.3}


def test_efficiency_subslice_omitted_when_thin_or_absent(sync_with_store):
    """insufficient_data / missing grade / no slice -> the key is OMITTED
    (older firmware tolerates unknown fields; a fake grade is never sent)."""
    sync, _ls = sync_with_store
    thin = {"grade": None, "insufficient_data": True, "actions": []}
    for eff in (None, thin, {"grade": "A", "insufficient_data": True}, "junk", 42):
        s = sync._build_device_summary({"today": 1.0}, {"today": 10}, efficiency=eff)
        assert "efficiency" not in s, f"leaked for {eff!r}"
