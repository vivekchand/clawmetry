"""
helpers/streams.py — Bounded SSE client accounting.

Extracted from dashboard.py as Phase 6.3. Owns the full stream-slot state
machine: counters, lock, per-kind caps, and the acquire/release pair.
No external module reads this state directly — it's purely internal to
the SSE endpoints — so the state lives here cleanly.

Re-exported from dashboard.py: `SSE_MAX_SECONDS`, `_acquire_stream_slot`,
`_release_stream_slot` (what routes/brain.py, routes/health.py, and
routes/infra.py actually use via `_d.<name>`).
"""

import threading

# Maximum wall-clock seconds any SSE stream will keep the connection open.
# Applies to brain-stream, health-stream, and logs-stream — routes read
# this to break out of their generator loops before the client's idle
# timeout kicks in.
SSE_MAX_SECONDS = 300

# Per-kind concurrency caps. When reached, _acquire_stream_slot returns
# False so the handler can 429 instead of leaking threads.
MAX_LOG_STREAM_CLIENTS = 10
MAX_HEALTH_STREAM_CLIENTS = 10
MAX_BRAIN_STREAM_CLIENTS = 5

_stream_clients_lock = threading.Lock()
_active_log_stream_clients = 0
_active_health_stream_clients = 0
_active_brain_stream_clients = 0


def _acquire_stream_slot(kind):
    """Bound concurrent SSE clients per stream type.

    Returns True if a slot was reserved (caller must pair with
    `_release_stream_slot`), False if the cap is already reached and the
    caller should emit a 429.
    """
    global _active_log_stream_clients, _active_health_stream_clients, _active_brain_stream_clients
    with _stream_clients_lock:
        if kind == "log":
            if _active_log_stream_clients >= MAX_LOG_STREAM_CLIENTS:
                return False
            _active_log_stream_clients += 1
            return True
        if kind == "health":
            if _active_health_stream_clients >= MAX_HEALTH_STREAM_CLIENTS:
                return False
            _active_health_stream_clients += 1
            return True
        if kind == "brain":
            if _active_brain_stream_clients >= MAX_BRAIN_STREAM_CLIENTS:
                return False
            _active_brain_stream_clients += 1
            return True
    return False


def _release_stream_slot(kind):
    """Release a slot acquired via `_acquire_stream_slot`. Idempotent floor at 0."""
    global _active_log_stream_clients, _active_health_stream_clients, _active_brain_stream_clients
    with _stream_clients_lock:
        if kind == "log":
            _active_log_stream_clients = max(0, _active_log_stream_clients - 1)
        elif kind == "health":
            _active_health_stream_clients = max(0, _active_health_stream_clients - 1)
        elif kind == "brain":
            _active_brain_stream_clients = max(0, _active_brain_stream_clients - 1)
