"""Tail existing local Asimov journals on the daemon-owned DuckDB connection.

This worker never installs SDK tracing or opens a robot connection. Live
observation and application instrumentation are separate, explicit operations.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

from .store import AsimovLocalStore

log = logging.getLogger(__name__)
_lock = threading.Lock()
_worker = None
_stop = threading.Event()


def journal_directory():
    return Path(os.environ.get("CLAWMETRY_ROBOTICS_DIR") or
                Path.home() / ".clawmetry" / "robotics" / "journal").expanduser()


def daemon_writer(store):
    """Return a handle that can actually write, asking again when it cannot.

    The daemon warms ``local_store.get_store`` up before ``local_server``
    marks this process the writer owner, so the handle captured at that
    moment can be the read-only proxy the dashboard uses. Collection is
    started with that captured handle and refused forever, while every later
    caller in the same process is handed the real writer. Resolve it here
    instead of trusting the handle the caller happened to hold.
    """
    if store is not None and not getattr(store, "_read_only", True):
        return store
    from clawmetry import local_store

    return local_store.get_store(read_only=False)


def start(store):
    """Start local journal ingestion once; replace a previously ended worker.

    Ordinary ingest errors are logged and retried by the same live thread on
    its next pass. The worker imports no SDK and uses no robot credentials.
    """
    global _worker
    with _lock:
        if _worker is not None and _worker.is_alive():
            return
        reader = AsimovLocalStore(daemon_writer(store), initialize=True)
        _stop.clear()

        def collect():
            while not _stop.is_set():
                try:
                    reader.ingest(journal_directory())
                except Exception:
                    log.warning("Asimov ingestion could not finish. The collector will try again.", exc_info=True)
                _stop.wait(1.0)

        _worker = threading.Thread(target=collect, name="asimov-ingest", daemon=True)
        _worker.start()


def stop():
    _stop.set()
    worker = _worker
    if worker is not None and worker is not threading.current_thread():
        worker.join(timeout=3.0)


def snapshot(store):
    return AsimovLocalStore(store).snapshot()
