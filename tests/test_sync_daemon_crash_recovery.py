"""Crash-recovery contract for the sync daemon's DuckDB write-through.

Audit (2026-05-17, fix/sync-duckdb-write-through-robust) found that:

  1. ``sync.py`` historically advanced ``state["last_event_ids"][fname]`` and
     persisted it via ``save_state(state)`` while the rows it represented
     were still in the local-store ring buffer (volatile memory). A SIGKILL
     between ring-enqueue and the background flusher tick (every 2 s) would
     leave the on-disk cursor pointing past lines that were never durable in
     DuckDB — silent ingest gap.

  2. Local-store write failures had no bounded-retry — a transient lock
     contention or disk hiccup would drop the batch on the floor with only a
     warning, even though the ring still held the rows.

The fix wraps:

  * Per-batch ``_flush_session_batch`` calls ``LocalStore.flush()`` AFTER
    ``_local_ingest_session_batch`` so the DuckDB COMMIT happens before the
    caller's offset advance.
  * The daemon's tick checkpoint calls ``LocalStore.flush()`` BEFORE
    ``save_state(state)`` as a belt-and-suspenders guard for all the other
    ingest paths (logs / channels / telegram / …).
  * ``LocalStore._flush_now`` now retries up to ``FLUSH_MAX_ATTEMPTS`` times
    with exponential backoff before re-raising; the ring still holds the
    batch on failure, so the next tick (or process restart) gets another
    deterministic attempt.

This test file pins those invariants:

  * ``test_crash_after_half_burst_no_loss_no_dupes``
        Fires N events, SIGKILLs the daemon process mid-burst, restarts, and
        re-fires the same N events. The DuckDB must end with exactly N rows
        — no loss (proves the write-then-checkpoint ordering) and no dupes
        (proves the INSERT OR IGNORE idempotency key on the per-event UUID).

  * ``test_local_ingest_succeeds_without_cloud_sync``
        Disables the cloud POST (raises on every call) and verifies all N
        events still land in DuckDB. Pins the MOAT mandate that cloud-sync
        is a separate task that never blocks the local-first ingest path.

Both tests run inside a tmp dir; no real ``~/.openclaw`` or
``~/.clawmetry`` is touched.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import textwrap
import time
import uuid
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_session_jsonl(sessions_dir: Path, session_uuid: str, n: int) -> Path:
    """Write ``n`` synthetic OpenClaw transcript events to a JSONL file.
    Each event has a stable per-line id (the index) so a replay produces the
    SAME canonical event id and INSERT OR IGNORE deduplicates."""
    sessions_dir.mkdir(parents=True, exist_ok=True)
    fpath = sessions_dir / f"{session_uuid}.jsonl"
    with open(fpath, "w") as f:
        for i in range(n):
            ev = {
                "id": f"ev-{i:04d}",  # stable id → idempotency key on replay
                "type": "tool_call",
                "timestamp": f"2026-05-17T10:00:{i:02d}Z",
                "tool": "Bash",
                "tokens": 10,
                "cost_usd": 0.001,
            }
            f.write(json.dumps(ev) + "\n")
    return fpath


def _spawn_ingest_worker(
    *,
    workspace: Path,
    db_path: Path,
    n_to_emit: int,
    fail_cloud: bool,
    pause_per_event: float,
    max_ticks: int = 1,
) -> subprocess.Popen:
    """Spawn a Python subprocess that imports ``clawmetry.sync`` and pumps the
    session JSONL into DuckDB one event at a time, pausing between events so
    the test can SIGKILL it mid-burst.

    The worker writes a one-line progress file ``<workspace>/progress`` after
    each successfully-ACK'd event so the test can SIGKILL deterministically at
    the N/2 mark instead of racing on timing.

    Stays as a single subprocess.Popen because we kill -9 it later — we can't
    SIGKILL an in-process thread.

    ``max_ticks`` lets the cloud-independence test simulate multiple daemon
    loop iterations: each tick re-enters ``sync_sessions`` from the saved
    cursor, so when cloud raises and the cursor stays put, the next tick
    picks up the same batch and pushes it again (idempotent on local).
    """
    workspace_str = str(workspace)
    db_path_str = str(db_path)
    progress_str = str(workspace / "progress")
    fail_cloud_str = "1" if fail_cloud else "0"
    pause_str = repr(pause_per_event)

    script = textwrap.dedent(f"""
        import json, os, sys, time
        os.environ['CLAWMETRY_LOCAL_STORE_PATH'] = {db_path_str!r}
        # Fast flusher so a SIGKILL between ring-enqueue and the fix's
        # explicit flush() is the ONLY thing that can lose an event —
        # otherwise the background ticker hides bugs we want to catch.
        os.environ.setdefault('CLAWMETRY_LOCAL_FLUSH_SECS', '60.0')
        os.environ.setdefault('CLAWMETRY_LOCAL_FLUSH_BATCH', '99999')
        os.environ['HOME'] = {workspace_str!r}
        os.environ['CLAWMETRY_HOME'] = {workspace_str!r}
        sys.path.insert(0, {str(REPO_ROOT)!r})

        from clawmetry import sync, local_store

        # State + paths live inside the test's workspace so each subprocess
        # gets a fresh, isolated bootstrap.
        sessions_dir = os.path.join({workspace_str!r}, '.openclaw', 'agents', 'main', 'sessions')
        state_file = os.path.join({workspace_str!r}, 'state.json')
        progress_file = {progress_str!r}

        def load_state():
            if os.path.exists(state_file):
                with open(state_file) as f:
                    return json.load(f)
            return {{'last_event_ids': {{}}, 'last_log_offsets': {{}}}}

        def save_state(s):
            tmp = state_file + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(s, f)
            os.replace(tmp, state_file)

        # Monkey-patch sync.save_state / load_state so they point at our tmp.
        sync.save_state = save_state
        sync.load_state = load_state
        sync._sync_allowed = lambda: True
        # Stub the cloud POST.
        cloud_fail = {fail_cloud_str!r} == '1'
        def fake_post(path, payload, api_key, timeout=45):
            if cloud_fail:
                raise RuntimeError('cloud-sync disabled for this test')
            return {{'ok': True}}
        sync._post = fake_post

        # Tiny BATCH_SIZE so each event hits the local-store ingest+flush
        # path on its own — easy to SIGKILL between events.
        sync.BATCH_SIZE = 1
        sync.MAX_EVENTS_PER_CYCLE = 99999

        config = {{
            'api_key': 'cm_test',
            'encryption_key': None,
            'node_id': 'crash-test-node',
        }}
        paths = {{'sessions_dir': sessions_dir}}

        # We want to pause AFTER every per-event flush so the parent test
        # can SIGKILL deterministically. Wrap _flush_session_batch.
        orig_flush = sync._flush_session_batch
        emitted = [0]
        def slow_flush(batch, fname, api_key, enc_key, node_id, subagent_id=None):
            # Local ingest+flush happens inside orig_flush; if cloud raises
            # below, the local rows are still durable. We bump the progress
            # marker only when the WHOLE call succeeds (local + cloud) so
            # the parent's mid-burst SIGKILL targets are exact.
            orig_flush(batch, fname, api_key, enc_key, node_id, subagent_id)
            emitted[0] += len(batch)
            with open(progress_file, 'w') as f:
                f.write(str(emitted[0]))
            f = None
            time.sleep({pause_str})
            if emitted[0] >= {n_to_emit}:
                local_store.get_store().flush()
                sys.exit(0)
        sync._flush_session_batch = slow_flush

        # Multi-tick driver — under cloud-failure the per-file ``except`` in
        # sync_sessions catches each batch's POST error and moves on to the
        # next file. With cloud failing every batch and only ONE file in
        # play, the loop bails after batch 1 of the file with the cursor
        # unchanged. Looping re-enters sync_sessions from the same cursor
        # and re-emits the same line; local INSERT OR IGNORE de-dupes.
        #
        # NOTE: This is the contract we *want* in a future PR to make smarter
        # (decouple local cursor from cloud cursor). For now the test
        # documents the observable behaviour.
        for _tick in range({max_ticks}):
            state = load_state()
            try:
                sync.sync_sessions(config, state, paths)
                save_state(state)
            except SystemExit:
                raise
            except Exception as e:
                print('worker error tick', _tick, ':', e, file=sys.stderr)
                # Don't kill the worker on per-tick error — that's the cloud
                # exception we're stress-testing. Save what we have and move
                # to the next tick.
                try:
                    save_state(state)
                except Exception:
                    pass
            local_store.get_store().flush()

        local_store.get_store().flush()
        save_state(state)
    """)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.Popen(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _wait_for_progress(workspace: Path, target: int, timeout: float = 15.0) -> int:
    """Block until ``<workspace>/progress`` reaches at least ``target``."""
    progress_file = workspace / "progress"
    deadline = time.monotonic() + timeout
    last = 0
    while time.monotonic() < deadline:
        if progress_file.exists():
            try:
                last = int(progress_file.read_text().strip() or "0")
            except Exception:
                pass
            if last >= target:
                return last
        time.sleep(0.02)
    raise AssertionError(
        f"progress did not reach {target} within {timeout}s "
        f"(last seen: {last})"
    )


def _count_durable_events(db_path: Path) -> int:
    """Open the DuckDB file in read-only mode (a separate process / connection
    from the worker, which is already dead by the time this is called) and
    count event rows. read_only=True bypasses the writer lock."""
    import duckdb
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM events").fetchone()[0])
    finally:
        conn.close()


def _query_durable_event_ids(db_path: Path) -> list[str]:
    import duckdb
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = conn.execute("SELECT id FROM events ORDER BY id").fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


# ── tests ─────────────────────────────────────────────────────────────────


@pytest.fixture
def crash_workspace(tmp_path: Path):
    """Fresh per-test workspace with an empty sessions dir + DuckDB target.
    The DuckDB file is created lazily by the worker on first ingest."""
    sessions_dir = tmp_path / ".openclaw" / "agents" / "main" / "sessions"
    db_path = tmp_path / "clawmetry.duckdb"
    yield {
        "workspace": tmp_path,
        "sessions_dir": sessions_dir,
        "db_path": db_path,
    }


def test_crash_after_half_burst_no_loss_no_dupes(crash_workspace):
    """SIGKILL the worker after it ACKs N/2 events. Restart, re-fire the same
    JSONL. DuckDB must end with exactly N rows — no loss, no duplicates.

    Why this proves the audit fix:
      * No loss → ``state["last_event_ids"]`` never advances past events that
        are not yet durable in DuckDB (write-then-ack ordering).
      * No dupes → on replay, INSERT OR IGNORE on the canonical event id
        collapses repeated writes (idempotency key invariant).
    """
    N = 10  # small enough that a 0.1 s/event pause keeps the test under 5 s
    session_uuid = str(uuid.uuid4())
    _make_session_jsonl(crash_workspace["sessions_dir"], session_uuid, N)

    # ── Run 1 — kill mid-burst ─────────────────────────────────────────
    proc = _spawn_ingest_worker(
        workspace=crash_workspace["workspace"],
        db_path=crash_workspace["db_path"],
        n_to_emit=N,
        fail_cloud=False,
        pause_per_event=0.1,
    )
    try:
        # Wait until at least N/2 events have been ACK'd by the worker.
        _wait_for_progress(crash_workspace["workspace"], N // 2, timeout=15.0)
        # SIGKILL — no chance for atexit / final flush. The audit fix says
        # the cursor on disk must NEVER point past events that aren't in
        # DuckDB.
        os.kill(proc.pid, signal.SIGKILL)
    finally:
        proc.wait(timeout=5.0)

    # Sanity: the worker actually durably wrote SOMETHING. (At least N/2
    # because flush happens before progress marker.)
    mid_count = _count_durable_events(crash_workspace["db_path"])
    assert mid_count >= N // 2, (
        f"expected >= {N // 2} events durable after SIGKILL, got {mid_count}"
    )
    assert mid_count <= N, (
        f"DuckDB has {mid_count} > N={N} events after partial burst — "
        "something is double-writing"
    )

    # ── Run 2 — restart, re-fire the same N events ─────────────────────
    proc2 = _spawn_ingest_worker(
        workspace=crash_workspace["workspace"],
        db_path=crash_workspace["db_path"],
        n_to_emit=N,
        fail_cloud=False,
        pause_per_event=0.02,  # faster on the resume — no reason to crawl
    )
    try:
        rc = proc2.wait(timeout=20.0)
    except subprocess.TimeoutExpired:
        proc2.kill()
        raise
    # Worker exits with 0 once it has emitted N events (sys.exit(0) inside
    # slow_flush). A non-zero exit means the run errored, not "ran clean".
    assert rc == 0, (
        f"resume worker exited with rc={rc}; stderr=\n"
        f"{proc2.stderr.read().decode(errors='replace')}"
    )

    # ── Assertions ──────────────────────────────────────────────────────
    final_count = _count_durable_events(crash_workspace["db_path"])
    assert final_count == N, (
        f"expected exactly {N} durable events after crash+resume, "
        f"got {final_count}. Either the write-then-ack ordering is broken "
        f"(loss) or the idempotency key is broken (dupes)."
    )
    ids = _query_durable_event_ids(crash_workspace["db_path"])
    expected = sorted([f"ev-{i:04d}" for i in range(N)])
    assert ids == expected, (
        f"event ids drifted from the source JSONL — expected {expected}, "
        f"got {ids}"
    )


def test_local_ingest_succeeds_without_cloud_sync(crash_workspace):
    """MOAT mandate: cloud-sync independence. If every ``_post`` call raises,
    the local DuckDB must still receive ALL N events in a single sync pass.
    Pins that cloud is a separate task that never blocks the local-first
    ingest path: ``_flush_session_batch`` swallows cloud exceptions so the
    caller's per-file iteration keeps draining local batches even with cloud
    100% down.
    """
    N = 8
    session_uuid = str(uuid.uuid4())
    _make_session_jsonl(crash_workspace["sessions_dir"], session_uuid, N)

    proc = _spawn_ingest_worker(
        workspace=crash_workspace["workspace"],
        db_path=crash_workspace["db_path"],
        n_to_emit=N,
        fail_cloud=True,
        pause_per_event=0.0,
        max_ticks=1,  # one tick is enough — fix makes cloud failures non-fatal
    )
    try:
        proc.wait(timeout=20.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise

    final_count = _count_durable_events(crash_workspace["db_path"])
    # The strong invariant: ALL N events land in DuckDB even with cloud
    # failing every POST, in a SINGLE tick (no retry needed).
    assert final_count == N, (
        f"expected ALL {N} durable events with cloud disabled, "
        f"got {final_count}. Cloud-sync failures are blocking the local "
        f"write path — either _flush_session_batch is letting cloud "
        f"exceptions propagate or local ingest happens AFTER cloud POST."
    )
    ids = _query_durable_event_ids(crash_workspace["db_path"])
    assert len(set(ids)) == N, (
        f"replay introduced duplicates: {sorted(ids)}"
    )
