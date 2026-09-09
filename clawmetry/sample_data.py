"""Synthetic sample sessions, so a fresh install is never an empty product.

Why this exists
---------------
``pip install clawmetry`` on a machine that has never run an agent shows
nothing, and a new user cannot tell that apart from a broken install. The
answer is not a screenshot: it is a small set of *synthetic* sessions loaded
into the normal read path, so every tab renders real content and the
diagnostic workflow is visible before the user has any data of their own.

Three rules this module exists to keep:

1. **Synthetic, never recorded.** Every string here was written for this
   file. No real transcript, path, prompt or customer name is replayed.
2. **Never touches the real store.** The sample lives in its own DuckDB under
   ``~/.clawmetry/sample/``. The daemon owns the writer lock on the real
   store and this must never contend for it, so sample mode also refuses to
   proxy to a running daemon (see ``local_store.get_store``).
3. **Labelled everywhere it surfaces.** Session titles carry
   :data:`SAMPLE_TITLE_PREFIX` and the node is :data:`SAMPLE_NODE_ID`, so a
   row is identifiable as sample data even somewhere the banner is not.

The incident is real, not staged
--------------------------------
The "stuck" session below is not annotated as stuck. It is a tool stream that
genuinely trips :func:`clawmetry.detectors.stuck_loop` — the same detector,
at the same thresholds, that runs over a user's own sessions.
``tests/test_sample_data.py`` asserts that, so if the detector's thresholds
move and the sample stops tripping it, CI fails rather than shipping a demo
that quietly demonstrates nothing.

Event shape is the family-adapter row documented in
``clawmetry/event_shape.py``: ``event_type`` in {message, tool_call,
tool_result, thinking} with ``data.role`` / ``data.content`` /
``data.tool_name`` / ``data.input``, and the error flag at ``data.is_error``.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Iterator

# Marks every sample row. Kept short because it shows in the UI.
SAMPLE_TITLE_PREFIX = "[sample] "
SAMPLE_NODE_ID = "sample-node"
SAMPLE_WORKSPACE = "/sample/checkout-service"

#: One line the UI shows wherever sample data is on screen.
SAMPLE_BANNER = (
    "Sample data — three synthetic sessions, not your machine. "
    "Restart without --sample to see your own agents."
)

_ENV_FLAG = "CLAWMETRY_SAMPLE"
_ENV_PATH = "CLAWMETRY_LOCAL_STORE_PATH"


def is_sample_mode() -> bool:
    """True when this process was started with ``--sample``.

    Read from the environment rather than a module global so that every
    process in the tree (dashboard, an in-process daemon) agrees without
    having to pass a flag through call sites that do not otherwise care.
    """
    return str(os.environ.get(_ENV_FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def sample_db_path() -> Path:
    """Where the sample store lives. Deliberately NOT next to the real one's
    filename: a stray ``--sample`` must never be able to shadow, truncate or
    lock ``clawmetry.duckdb``."""
    return Path(os.path.expanduser("~/.clawmetry/sample/sample.duckdb"))


def enable_sample_mode() -> Path:
    """Turn sample mode on for this process *and* its children.

    Must run before :mod:`clawmetry.local_store` is imported, because that
    module reads ``CLAWMETRY_LOCAL_STORE_PATH`` into ``DB_PATH`` at import
    time. Returns the store path.
    """
    path = sample_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    os.environ[_ENV_FLAG] = "1"
    os.environ[_ENV_PATH] = str(path)
    return path


# ── the sessions ────────────────────────────────────────────────────────────
#
# Times are relative to "now" at build time so the dashboard's recency
# windows (24h / 7d) always have something in them, whenever the sample is
# built. Everything else is deterministic.

_MODEL = "claude-sonnet-4-5"
_PRICE_PER_1K = 0.009  # blended in/out; only used to make cost look sane


def _ts(offset_sec: float) -> str:
    """ISO-8601 UTC, ``offset_sec`` seconds before now."""
    return time.strftime(
        "%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - offset_sec)
    ) + "Z"


def _eid(session_id: str, n: int) -> str:
    """Stable id, so rebuilding the sample upserts instead of duplicating."""
    return hashlib.sha256(f"{session_id}:{n}".encode()).hexdigest()[:32]


def _event(session_id: str, n: int, offset: float, event_type: str,
           data: dict, *, tokens: int = 0, cost: float | None = None) -> dict:
    return {
        "id": _eid(session_id, n),
        "node_id": SAMPLE_NODE_ID,
        "agent_type": "openclaw",
        "agent_id": "main",
        "session_id": session_id,
        "workspace_id": SAMPLE_WORKSPACE,
        "event_type": event_type,
        "ts": _ts(offset),
        "data": data,
        "token_count": tokens or None,
        "cost_usd": (round(tokens / 1000.0 * _PRICE_PER_1K, 6)
                     if cost is None and tokens else cost),
        "model": _MODEL if tokens else None,
    }


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


def _tool_call(name: str, args: dict) -> dict:
    """One tool invocation, in exactly ONE of the shapes the normaliser reads.

    Carrying both ``tool_name`` and a ``tool_calls`` array (which real
    adapters sometimes do) makes ``detectors._iter_tool_calls_from_data``
    yield the call twice with different argument hashes, which silently
    breaks every consecutive-identical-call check. See #5715.
    """
    return {"role": "assistant", "tool_name": name, "input": args,
            "content": ""}


def _tool_result(name: str, output: str, *, is_error: bool = False) -> dict:
    # ``is_error`` at the top level: that is where _structured_is_error looks.
    return {"role": "tool", "tool_name": name, "content": output,
            "output": output, "is_error": is_error}


def _stuck_session() -> tuple[dict, list[dict]]:
    """An agent circling on a failing migration.

    Twelve identical ``Bash`` calls with identical arguments, each failing the
    same way. This is what trips ``stuck_loop`` — nothing here declares the
    session stuck.
    """
    sid = "sample-stuck-0001"
    ev: list[dict] = []
    n = 0
    base = 5400.0  # started 90 minutes ago

    def add(offset: float, et: str, data: dict, **kw) -> None:
        nonlocal n
        ev.append(_event(sid, n, offset, et, data, **kw))
        n += 1

    add(base, "message", _msg(
        "user",
        "The checkout service migration keeps failing on staging. "
        "Get `alembic upgrade head` to run clean."), tokens=180)
    add(base - 20, "thinking", {
        "role": "assistant", "content":
        "The failure mentions a duplicate index. I should re-run the "
        "migration to see the exact error before changing anything."},
        tokens=240)

    # The loop: same tool, same args, same failure, twelve times.
    failure = ("alembic.util.exc.CommandError: Target database is not up to "
               "date.\n  ERROR: duplicate index 'ix_orders_customer_id'")
    for i in range(12):
        t = base - 60 - (i * 210)
        add(t, "tool_call", _tool_call(
            "Bash", {"command": "alembic upgrade head",
                     "cwd": SAMPLE_WORKSPACE}), tokens=310)
        add(t - 8, "tool_result", _tool_result("Bash", failure, is_error=True))
        add(t - 12, "message", _msg(
            "assistant",
            "That failed the same way. Let me try running the migration "
            "again."), tokens=260)

    started = base
    last = base - 60 - (11 * 210) - 12
    total_tokens = sum(int(e.get("token_count") or 0) for e in ev)
    session = {
        "session_id": sid,
        "agent_type": "openclaw",
        "node_id": SAMPLE_NODE_ID,
        "agent_id": "main",
        "workspace_id": SAMPLE_WORKSPACE,
        "title": SAMPLE_TITLE_PREFIX + "Fix failing checkout migration",
        "started_at": _ts(started),
        "last_active_at": _ts(last),
        "status": "active",
        "total_tokens": total_tokens,
        "cost_usd": round(total_tokens / 1000.0 * _PRICE_PER_1K, 4),
        "message_count": len(ev),
        "metadata": {"sample": True},
    }
    return session, ev


def _healthy_session() -> tuple[dict, list[dict]]:
    """A long run that is working, so the contrast with the loop is visible.

    Deliberately long: 'many tool calls' on its own is not evidence of a
    problem, and a demo that implies it is teaches the wrong thing.
    """
    sid = "sample-healthy-0002"
    ev: list[dict] = []
    n = 0
    base = 9000.0

    def add(offset: float, et: str, data: dict, **kw) -> None:
        nonlocal n
        ev.append(_event(sid, n, offset, et, data, **kw))
        n += 1

    add(base, "message", _msg(
        "user", "Add cursor pagination to the public search endpoint, "
                "with tests."), tokens=140)

    steps = [
        ("Grep", {"pattern": "def search", "path": "app/api"},
         "app/api/search.py:41:def search(request):"),
        ("Read", {"file_path": "app/api/search.py"},
         "41 lines read from app/api/search.py"),
        ("Read", {"file_path": "app/middleware/__init__.py"},
         "18 lines read from app/middleware/__init__.py"),
        ("Write", {"file_path": "app/api/pagination.py"},
         "Wrote 64 lines to app/api/pagination.py"),
        ("Edit", {"file_path": "app/api/search.py"},
         "Applied 1 edit to app/api/search.py"),
        ("Write", {"file_path": "tests/test_pagination.py"},
         "Wrote 88 lines to tests/test_pagination.py"),
        ("Bash", {"command": "pytest tests/test_pagination.py -q"},
         "5 passed in 1.24s"),
        ("Bash", {"command": "ruff check app/"},
         "All checks passed!"),
    ]
    for i, (tool, args, out) in enumerate(steps):
        t = base - 120 - (i * 340)
        add(t, "tool_call", _tool_call(tool, args), tokens=290)
        add(t - 9, "tool_result", _tool_result(tool, out))

    add(base - 120 - (len(steps) * 340), "message", _msg(
        "assistant",
        "Cursor pagination is in place on the search endpoint: an opaque "
        "cursor plus a page size capped at 100, and a next-page token in the "
        "response body. Five tests cover the first page, an exhausted "
        "cursor, and a tampered token."), tokens=520)

    last = base - 120 - (len(steps) * 340)
    total_tokens = sum(int(e.get("token_count") or 0) for e in ev)
    session = {
        "session_id": sid,
        "agent_type": "openclaw",
        "node_id": SAMPLE_NODE_ID,
        "agent_id": "main",
        "workspace_id": SAMPLE_WORKSPACE,
        "title": SAMPLE_TITLE_PREFIX + "Paginate the search endpoint",
        "started_at": _ts(base),
        "last_active_at": _ts(last),
        "ended_at": _ts(last),
        "status": "completed",
        "total_tokens": total_tokens,
        "cost_usd": round(total_tokens / 1000.0 * _PRICE_PER_1K, 4),
        "message_count": len(ev),
        "metadata": {"sample": True},
    }
    return session, ev


def _short_session() -> tuple[dict, list[dict]]:
    """A two-minute question. Most real sessions look like this, and a sample
    made only of dramatic ones misrepresents the shape of the data."""
    sid = "sample-quick-0003"
    ev: list[dict] = []
    n = 0
    base = 1500.0

    def add(offset: float, et: str, data: dict, **kw) -> None:
        nonlocal n
        ev.append(_event(sid, n, offset, et, data, **kw))
        n += 1

    add(base, "message", _msg(
        "user", "Which module owns the retry policy for outbound webhooks?"),
        tokens=90)
    add(base - 6, "tool_call",
        _tool_call("Grep", {"pattern": "retry", "path": "app/webhooks"}),
        tokens=150)
    add(base - 14, "tool_result", _tool_result(
        "Grep", "app/webhooks/dispatch.py:77:RETRY_SCHEDULE = (1, 5, 25, 125)"))
    add(base - 20, "message", _msg(
        "assistant",
        "`app/webhooks/dispatch.py` — `RETRY_SCHEDULE` at line 77 defines the "
        "backoff, and `dispatch()` applies it."), tokens=210)

    total_tokens = sum(int(e.get("token_count") or 0) for e in ev)
    session = {
        "session_id": sid,
        "agent_type": "openclaw",
        "node_id": SAMPLE_NODE_ID,
        "agent_id": "main",
        "workspace_id": SAMPLE_WORKSPACE,
        "title": SAMPLE_TITLE_PREFIX + "Where is the webhook retry policy?",
        "started_at": _ts(base),
        "last_active_at": _ts(base - 20),
        "ended_at": _ts(base - 20),
        "status": "completed",
        "total_tokens": total_tokens,
        "cost_usd": round(total_tokens / 1000.0 * _PRICE_PER_1K, 4),
        "message_count": len(ev),
        "metadata": {"sample": True},
    }
    return session, ev


def build_dataset() -> tuple[list[dict], list[dict]]:
    """Return ``(sessions, events)`` — pure, no I/O, safe to call in tests."""
    sessions: list[dict] = []
    events: list[dict] = []
    for factory in (_stuck_session, _healthy_session, _short_session):
        s, ev = factory()
        sessions.append(s)
        events.extend(ev)
    return sessions, events


def populate(store: Any) -> tuple[int, int]:
    """Write the sample dataset into ``store``. Returns ``(sessions, events)``.

    Ids are content-stable, so running this twice upserts rather than
    duplicating and a rebuild is always safe.
    """
    sessions, events = build_dataset()
    for s in sessions:
        meta = s.get("metadata")
        if isinstance(meta, dict):
            s = dict(s, metadata=json.dumps(meta))
        store.ingest_session(s)
    store.ingest_many(events)
    flush = getattr(store, "flush", None)
    if callable(flush):
        try:
            flush()
        except Exception:
            pass
    return len(sessions), len(events)


def ensure_built() -> tuple[int, int]:
    """Build the sample store if it is missing or empty. Idempotent."""
    from clawmetry import local_store

    store = local_store.get_store()
    try:
        existing = store.query_sessions(limit=1)
    except Exception:
        existing = None
    if existing:
        return (0, 0)
    return populate(store)
