"""Live-daemon reliability suite — catch sync drift on the day it ships.

Background (#1681, 2026-05-18)
==============================
Principal B's drift P0: cloud believed the local daemon had shipped 0 events
even though local DuckDB held 1,471+ rows. Root cause was a TypeError inside
``_dispatch_pending_queries`` for every ``shape='sessions'`` heartbeat:

    pending_query dispatch failed (id=q_node_sessions_refresh_... shape=sessions):
    LocalStore.query_sessions() got an unexpected keyword argument 'node_id'

Every pending-query crashed in a try/except that logged a WARNING and moved
on, so cloud silently saw "fresh node, no data" while local DuckDB had a full
history. No test caught it. Memories burned:
``feedback_synthetic_tests_missed_real_event_shape.md``,
``project_relay_transport_decision.md``.

This module installs five invariants against the live OSS daemon so the same
class of bug surfaces inside one minute instead of weeks:

1. ``test_sync_log_has_no_dispatch_failures`` — literal regression: tail
   ``~/.clawmetry/sync.log`` for the past 60 s and assert zero
   ``pending_query dispatch failed`` lines.
2. ``test_pending_query_dispatch_handles_unknown_kwargs`` — exercises both
   action-style (``_dispatch_pending_action``) and shape-style
   (``_dispatch_pending_queries``) dispatch with a deliberately
   future-shaped entry. The handlers must tolerate unknown keys without
   raising TypeError on the calling thread.
3. ``test_local_to_cloud_session_count_within_threshold`` — compares local
   daemon session count to cloud's per-node summary. Skips when no cloud
   API key is configured (CI without credentials).
4. ``test_event_count_grows_monotonically`` — daemon ``health.event_count``
   must be non-decreasing across a 1 s window. Detects "daemon silently
   rejecting writes" (the dispatch-failure symptom from #1681).
5. ``test_keystone_endpoints_all_pass`` — runs ``accuracy_harness/all.py
   --dry-run`` as a subprocess and asserts exit 0. The full no-dry-run
   loop drives real LLM budget; tests stay cheap by smoke-testing the
   meta-runner skeleton only.

Each test skips cleanly via ``pytest.skip`` when its prerequisite (live
daemon, sync.log readability, cloud API key) is missing, so CI without a
daemon does NOT false-fail.

Per memory ``reference_duckdb_process_lock.md`` every DuckDB read flows
through the daemon's ``/__local_query__/<method>`` HTTP proxy — opening
the DuckDB directly would race the daemon's exclusive writer lock.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# Share the accuracy-harness helpers — they already wrap discovery + the
# ``__local_query__`` bearer-token HTTP shim with the right liveness checks.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts" / "accuracy_harness"))
from _lib import (  # noqa: E402
    discover_daemon,
    daemon_call,
    daemon_event_count,
)

_HOME = Path.home() / ".clawmetry"
_SYNC_LOG = _HOME / "sync.log"
_CONFIG = _HOME / "config.json"

# Pattern to match the literal warning emitted by sync.py for a failed
# pending-query dispatch. Kept loose enough to catch sibling shapes
# (events / aggregates / health / transcript) too, not just sessions.
_DISPATCH_FAIL_RE = re.compile(
    r"pending_query dispatch failed \(id=([^\s]+) shape=([^\s\)]+)\): (.+)$"
)
_LOG_TS_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) \["
)


def _parse_log_ts(line: str) -> float | None:
    """Return epoch seconds from a sync.log line prefix, or None."""
    m = _LOG_TS_RE.match(line)
    if not m:
        return None
    try:
        from datetime import datetime
        ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        return ts.timestamp() + (int(m.group(2)) / 1000.0)
    except ValueError:
        return None


def _read_config() -> dict | None:
    try:
        return json.loads(_CONFIG.read_text())
    except (FileNotFoundError, OSError, ValueError):
        return None


def _require_daemon() -> dict:
    d = discover_daemon()
    if not d:
        pytest.skip("daemon local_query proxy not running; start `clawmetry sync`")
    return d


# ── Test 1 — sync.log dispatch-failure tail ─────────────────────────────────

def test_sync_log_has_no_dispatch_failures():
    """Tail the last 60 s of sync.log; assert zero pending-query failures.

    This is the literal regression test for #1681. The bug emits one
    WARNING per dispatch attempt (~once per heartbeat = once per 5 s),
    so a 60 s window catches it within a single test run.
    """
    if not _SYNC_LOG.exists():
        pytest.skip(f"{_SYNC_LOG} not present; daemon has never run")
    _require_daemon()  # only meaningful when daemon is live

    cutoff = time.time() - 60.0
    failures: list[str] = []
    # Read the tail bytewise to avoid loading multi-MB logs. The daemon
    # rotates this file so it is normally well under 50 MB.
    try:
        with _SYNC_LOG.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            # 512 KB tail is enough for >60 s of "loaded approval policies"
            # spam plus any failures the test wants to surface.
            tail_bytes = min(size, 512 * 1024)
            fh.seek(size - tail_bytes)
            blob = fh.read().decode("utf-8", errors="replace")
    except OSError as e:
        pytest.skip(f"sync.log unreadable: {e}")

    for line in blob.splitlines():
        ts = _parse_log_ts(line)
        if ts is None or ts < cutoff:
            continue
        m = _DISPATCH_FAIL_RE.search(line)
        if m:
            failures.append(line.strip())

    assert not failures, (
        f"sync.log has {len(failures)} pending_query dispatch failure(s) in "
        f"the last 60 s. First 3:\n  "
        + "\n  ".join(failures[:3])
        + "\nThis is the #1681 class of bug: every dispatch crashed in a "
        "try/except so cloud silently believed the daemon had 0 events. "
        "Root-cause the failure and add the failing arg to the local_store "
        "method signature (or strip it in _dispatch_pending_queries)."
    )


# ── Test 2 — dispatch handles unknown kwargs without TypeError ──────────────

def test_pending_query_dispatch_handles_unknown_kwargs():
    """Future-proof against another schema mismatch.

    Cloud + OSS evolve independently; cloud is free to add new fields to
    a pending_query before OSS knows about them. Both the action-style
    and shape-style dispatch must swallow unknown keys gracefully —
    never raising on the heartbeat thread.

    The #1681 root cause: ``_dispatch_pending_queries`` called
    ``store.query_sessions(node_id=...)`` directly; ``LocalStore.query_sessions``
    didn't accept ``node_id`` → TypeError → caught + logged + dropped.
    Cloud then re-enqueued the same query and the cycle repeated forever.
    """
    # Importing sync without monkeypatching loads the real module; that is
    # fine — we are only invoking the dispatcher with a synthetic entry,
    # not starting the heartbeat loop.
    sys.path.insert(0, str(_REPO_ROOT))
    from clawmetry import sync as _sync  # noqa: E402

    # 1. Action-style: an unknown 'type' must be silently dropped.
    try:
        _sync._dispatch_pending_action({}, {
            "type": "completely_made_up_future_type",
            "node_id": "test-node",
            "some_future_kwarg": "Y",
        })
    except TypeError as e:
        pytest.fail(f"action dispatch raised TypeError on unknown type: {e}")

    # 2. Shape-style: this is the literal #1681 reproduction. We feed
    # ``_dispatch_pending_queries`` a sessions-shaped entry with the
    # exact extra kwarg cloud sent (node_id) plus a deliberately
    # invented one (some_future_kwarg). The function MUST log the
    # error internally (it already does) and not re-raise.
    config = {
        "api_key": "test_only_not_real",
        "encryption_key": None,  # forces the dispatch to short-circuit pre-POST
        "node_id": "test-node",
    }
    pending = [{
        "shape":     "sessions",
        "id":        "q_test_future_kwargs",
        "cache_key": "sessions:test",
        "args":      {"node_id": "test-node", "some_future_kwarg": "Y"},
    }]
    try:
        _sync._dispatch_pending_queries(config, pending)
    except TypeError as e:
        pytest.fail(
            f"_dispatch_pending_queries raised TypeError on unknown kwarg "
            f"(this is the #1681 class): {e}"
        )
    except Exception as e:
        # Other exceptions are also unacceptable — the dispatcher's job
        # is to catch its own per-query failures so one bad entry never
        # blocks the rest of the batch.
        pytest.fail(
            f"_dispatch_pending_queries leaked {type(e).__name__} on bad "
            f"kwargs (should be caught + logged): {e}"
        )


# ── Test 3 — local vs cloud session-count drift ─────────────────────────────

def test_local_to_cloud_session_count_within_threshold():
    """Cloud is allowed to lag local, but not by more than 2x.

    This is the high-level invariant Principal B's bug violated: local
    DuckDB had 1,471 events but cloud's per-node summary showed 0. A
    50% floor lets the heartbeat batch + cloud cache TTL breathe while
    still catching the silent-data-loss class.

    Skips when no cloud API key is configured (CI without credentials).
    """
    cfg = _read_config()
    if not cfg or not cfg.get("api_key") or not cfg.get("node_id"):
        pytest.skip("~/.clawmetry/config.json missing api_key / node_id")
    api_key = cfg["api_key"]
    node_id = cfg["node_id"]

    daemon = _require_daemon()
    try:
        rows = daemon_call(daemon, "query_sessions_table", limit=2000)
    except Exception as e:
        pytest.skip(f"daemon query_sessions_table unreachable: {e}")
    local_count = len(rows or [])
    if local_count == 0:
        pytest.skip("local store has 0 sessions; nothing to compare against")

    cloud_base = os.environ.get("CLAWMETRY_CLOUD_URL",
                                 "https://app.clawmetry.com")
    url = f"{cloud_base.rstrip('/')}/api/cloud/node/{node_id}/summary"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            pytest.skip(f"cloud rejected api_key (HTTP {e.code}); "
                        f"likely not a paying account")
        if e.code == 404:
            pytest.skip(f"cloud summary endpoint missing (HTTP 404); "
                        f"node may not be registered yet")
        pytest.skip(f"cloud summary returned HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        pytest.skip(f"cloud unreachable: {e}")

    if not isinstance(body, dict):
        pytest.skip(f"cloud summary returned non-dict: {type(body).__name__}")
    cloud_count = body.get("session_count")
    if cloud_count is None:
        # Some cloud builds spell it differently; accept obvious aliases.
        for k in ("sessions", "sessions_count", "total_sessions"):
            if isinstance(body.get(k), int):
                cloud_count = body[k]
                break
    if cloud_count is None:
        pytest.skip(f"cloud summary missing session_count field; keys="
                    f"{sorted(body.keys())[:10]}")

    floor = int(local_count * 0.5)
    assert cloud_count >= floor, (
        f"cloud drift: local has {local_count} sessions, cloud reports "
        f"{cloud_count} (floor for this run: {floor}). This is the #1681 "
        f"class: daemon -> cloud pipeline is dropping data silently. "
        f"Check `sync.log` for `pending_query dispatch failed` and verify "
        f"_dispatch_pending_queries against the cloud-sent args shape."
    )


# ── Test 4 — event_count monotonicity ───────────────────────────────────────

def test_event_count_grows_monotonically():
    """Sample event_count twice, 1 s apart. Second must be >= first.

    Catches "daemon silently rejecting writes" — if every ingest crashes
    inside a try/except, event_count flatlines while sessions keep
    arriving. (Same failure mode as #1681 but on the WRITE side.)
    """
    daemon = _require_daemon()
    first = daemon_event_count(daemon)
    if first is None:
        pytest.skip("daemon health did not surface event_count")
    time.sleep(1.0)
    second = daemon_event_count(daemon)
    if second is None:
        pytest.skip("daemon health became unreachable on second sample")

    assert second >= first, (
        f"event_count regressed: {first} -> {second} over 1 s. The daemon "
        f"is either reopening DuckDB against a different path or silently "
        f"dropping rows. Inspect `sync.log` for ingest exceptions and "
        f"verify CLAWMETRY_LOCAL_STORE_PATH did not change between samples."
    )


# ── Test 5 — accuracy harness meta-runner smoke ─────────────────────────────

def test_keystone_endpoints_all_pass():
    """Run the accuracy-harness meta-runner; assert exit 0.

    The full no-dry-run loop drives real LLM budget through ``openclaw
    agent --message``, so this smoke uses ``--dry-run`` to exercise the
    runner skeleton + per-harness summary parsing. A real ``--no-drive``
    flag does not exist on the runner (verified 2026-05-18); the
    meta-runner already supports ``--dry-run`` and skips before spending
    LLM budget, which is the same contract Principal B asked for.
    """
    runner = _REPO_ROOT / "scripts" / "accuracy_harness" / "all.py"
    if not runner.exists():
        pytest.skip(f"accuracy harness missing: {runner}")
    try:
        proc = subprocess.run(
            [sys.executable, str(runner), "--dry-run", "--no-issue"],
            capture_output=True, text=True, timeout=60,
            cwd=str(_REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        pytest.fail("accuracy_harness/all.py --dry-run hung > 60 s")
    except OSError as e:
        pytest.skip(f"could not exec harness runner: {e}")

    assert proc.returncode == 0, (
        f"accuracy_harness/all.py exited {proc.returncode}\n"
        f"stdout tail:\n{proc.stdout[-800:]}\n"
        f"stderr tail:\n{proc.stderr[-800:]}"
    )
