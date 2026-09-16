"""Durable first-install readiness, written only by the ingest daemon.

The progress JSON file is a legacy banner transport. This record lives in
DuckDB so both local readers and encrypted cloud snapshots see the same state.
Finishing once is sticky across daemon restarts, including empty installs.
"""
import json
import logging
import time

log = logging.getLogger(__name__)
SETTING = "dashboard_startup"


def read_progress(store):
    raw = store.get_node_setting(SETTING)
    try:
        value = json.loads(raw) if raw else {}
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        log.warning("Ignoring unreadable dashboard startup progress")
        return {}


def record_progress(store, phase, done=0, total=0, complete=False):
    """Use the daemon's existing writer handle; never open a second writer."""
    previous = read_progress(store)
    now = time.time()
    initialized = bool(previous.get("initialized"))
    if not previous:
        # An upgrade is not a fresh install. Do not hold a populated store
        # hostage while the restarted daemon refreshes its data.
        initialized = store.query_startup_status()["has_data"]
    store.set_node_setting(SETTING, json.dumps({
        "initialized": initialized or complete,
        "phase": phase,
        "done": max(0, int(done)),
        "total": max(0, int(total)),
        "started_at": previous.get("started_at") or now,
        "updated_at": now,
    }))
