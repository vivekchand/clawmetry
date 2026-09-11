"""A person's answer reaches the agent while it can still be used.

A parked approval (Claude Code's PreToolUse gate holding a tool call or an
AskUserQuestion) gives the human a few minutes; after that the runtime's own
terminal prompt takes over. A decision made on a cloud surface travels on the
relay queue, which the daemon drains only when it heartbeats — and the main
loop heartbeats at the END of a cycle.

Burned 2026-09-11 (verified live): an answer clicked on the cloud strip at
20:46:37 UTC, 22 s before the 20:47:00 deadline, was still queued when the
window closed. The node's heartbeats that minute were 20:45:35 then 20:47:05:
a 90-second gap spent syncing 7,388 events. The question went to the terminal
and the answer reached nobody.

These pin the fast path that closes that gap: while a window is open the
daemon heartbeats every couple of seconds, and when nobody is waiting it does
not heartbeat at all (an idle node must stay idle).
"""

from __future__ import annotations

import importlib
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync_mod(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    import clawmetry.sync as s
    importlib.reload(s)

    yield s

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def store():
    from clawmetry import local_store
    return local_store.get_store()


@pytest.fixture
def config():
    return {"node_id": "node-test", "api_key": "cm_test"}


@pytest.fixture
def beats(monkeypatch, sync_mod):
    sent = []
    monkeypatch.setattr(sync_mod, "send_heartbeat",
                        lambda cfg: sent.append(cfg) or True)
    return sent


def _ms(offset_s: float) -> int:
    return int((time.time() + offset_s) * 1000)


def _park(store, approval_id, *, deadline_ms, status="pending", questions=True):
    args = {"tool_name": "AskUserQuestion", "on_timeout": "ask"}
    if deadline_ms is not None:
        args["deadline_ms"] = deadline_ms
    if questions:
        args["_cm_questions"] = [{
            "question": "Ship it?", "header": "Release", "multiSelect": False,
            "options": [{"label": "Ship", "description": ""},
                        {"label": "Hold", "description": ""}],
        }]
    store.ingest_approval({
        "id": approval_id, "requestor_session_id": "claude_code:s1",
        "action": "AskUserQuestion: 1 question", "args": args, "status": status,
        "created_at": "2026-09-11T20:43:59Z",
    })


# ── is anybody still waiting? ───────────────────────────────────────────────

def test_open_while_the_window_has_time_left(sync_mod, store):
    _park(store, "q1", deadline_ms=_ms(120))
    assert sync_mod._answer_window_open() is True


def test_closed_once_the_window_has_passed(sync_mod, store):
    _park(store, "q1", deadline_ms=_ms(-1))
    assert sync_mod._answer_window_open() is False


def test_a_decided_request_holds_nothing_open(sync_mod, store):
    _park(store, "q1", deadline_ms=_ms(120), status="answered")
    assert sync_mod._answer_window_open() is False


def test_a_request_without_a_window_holds_nothing_open(sync_mod, store):
    """An ordinary approval carries no runtime clock: it must not pin the
    daemon to a 2-second heartbeat for as long as it sits in the queue."""
    _park(store, "b1", deadline_ms=None, questions=False)
    assert sync_mod._answer_window_open() is False


def test_an_empty_queue_is_closed(sync_mod):
    assert sync_mod._answer_window_open() is False


def test_a_binary_request_inside_its_window_also_counts(sync_mod, store):
    """Approve/Deny is relayed the same way and is just as time-bound."""
    _park(store, "b1", deadline_ms=_ms(60), questions=False)
    assert sync_mod._answer_window_open() is True


# ── the tick ────────────────────────────────────────────────────────────────

def test_tick_heartbeats_while_someone_is_waiting(sync_mod, store, config, beats):
    _park(store, "q1", deadline_ms=_ms(120))
    assert sync_mod._answer_window_tick(config) is True
    assert beats == [config]


def test_tick_is_silent_when_nobody_is_waiting(sync_mod, store, config, beats):
    _park(store, "q1", deadline_ms=_ms(-1))
    assert sync_mod._answer_window_tick(config) is False
    assert beats == []


def test_tick_does_nothing_without_a_cloud_account(sync_mod, store, beats):
    _park(store, "q1", deadline_ms=_ms(120))
    assert sync_mod._answer_window_tick({"node_id": "n"}) is False
    assert beats == []


def test_tick_respects_local_only_mode(sync_mod, store, config, beats, monkeypatch):
    _park(store, "q1", deadline_ms=_ms(120))
    import clawmetry.config as cfg_mod
    monkeypatch.setattr(cfg_mod, "is_cloud_disabled", lambda: True)
    assert sync_mod._answer_window_tick(config) is False
    assert beats == []


def test_a_store_failure_never_raises(sync_mod, config, beats, monkeypatch):
    from clawmetry import local_store

    def boom(*a, **k):
        raise RuntimeError("store is busy")

    monkeypatch.setattr(local_store, "get_store", boom)
    assert sync_mod._answer_window_open() is False
    assert sync_mod._answer_window_tick(config) is False
    assert beats == []


# ── the thread ──────────────────────────────────────────────────────────────

def test_thread_beats_repeatedly_then_stops(sync_mod, store, config, beats, monkeypatch):
    import threading
    monkeypatch.setattr(sync_mod, "_ANSWER_WINDOW_POLL_SEC", 0.01)
    _park(store, "q1", deadline_ms=_ms(120))
    stop = threading.Event()
    sync_mod._start_answer_window_heartbeat(config, stop_event=stop)
    deadline = time.time() + 3.0
    while len(beats) < 2 and time.time() < deadline:
        time.sleep(0.02)
    stop.set()
    assert len(beats) >= 2, "the relay must be drained repeatedly while waiting"
    time.sleep(0.1)
    seen = len(beats)
    time.sleep(0.1)
    assert len(beats) == seen, "the thread must stop when asked"
