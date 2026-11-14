"""Independent, bounded daemon cadence for local and encrypted node views."""
from __future__ import annotations

import logging
import threading
import time

from clawmetry.node_activity import collect_node_activity, unavailable

log = logging.getLogger("clawmetry.node_activity_service")
INTERVAL_SECONDS = 30
_LOCK = threading.Lock()
_LAST_TICKS = {}


def tick_node_activity(store, *, node_id="", now=None, stop_event=None):
    """Collect at most once per cadence. A request handler must never call this."""
    if not _LOCK.acquire(blocking=False):
        return None
    try:
        monotonic = time.monotonic()
        # Store identity is stable during a daemon lifetime; no daemon JSON state.
        key = (id(store), node_id)
        if monotonic - _LAST_TICKS.get(key, float("-inf")) < INTERVAL_SECONDS:
            return None
        _LAST_TICKS[key] = monotonic
        state = store.get_node_activity_state()
        observation = collect_node_activity(preferences=state["preferences"], node_id=node_id,
                                            now=now, fingerprint_key=state["fingerprint_key"])
        if stop_event is not None and stop_event.is_set():
            return None
        return store.record_node_activity(observation)
    except Exception as exc:
        log.warning("Node observation was not saved: %s", type(exc).__name__)
        try:
            return store.query_node_activity()
        except Exception:
            return unavailable("The node observation store is unavailable.")
    finally:
        _LOCK.release()


# One worker replaces the old ingest-loop trigger. Only resource/process
# frames accelerate while a viewer is present; expensive sources stay at 30s.
LIVE_INTERVAL_SECONDS = 2
VIEW_LEASE_SECONDS = 40
_WORKER_LOCK = threading.Lock()
_WORKER = None
_VIEW_UNTIL = 0.0
_REMOTE_UNTIL = 0.0


def touch_node_activity_view(*, remote=False, lease_seconds=None):
    global _VIEW_UNTIL, _REMOTE_UNTIL
    with _WORKER_LOCK:
        until = time.monotonic() + (min(VIEW_LEASE_SECONDS, max(0, lease_seconds)) if lease_seconds is not None else VIEW_LEASE_SECONDS)
        _VIEW_UNTIL = until
        if remote:
            _REMOTE_UNTIL = until
        worker = _WORKER
    if worker is not None:
        worker.wake.set()


def _view_active(remote=False):
    return time.monotonic() < (_REMOTE_UNTIL if remote else _VIEW_UNTIL)


class _NodeActivityWorker:
    def __init__(self, store, node_id, publish):
        self.store, self.node_id, self.publish = store, node_id, publish
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.publish_ready = threading.Event()
        self.frame_lock = threading.Lock()
        self.latest = None
        self.last_full = float('-inf')
        self.last_sample = float('-inf')
        self.thread = threading.Thread(target=self.run, name='clawmetry-node-activity', daemon=True)
        self.publisher = threading.Thread(target=self.send, name='clawmetry-node-live-publish', daemon=True) if publish else None

    def run(self):
        while not self.stop.is_set():
            now = time.monotonic()
            interval = LIVE_INTERVAL_SECONDS if _view_active() else INTERVAL_SECONDS
            if now - self.last_sample >= interval:
                self.last_sample = now
                try:
                    if now - self.last_full >= INTERVAL_SECONDS:
                        body = tick_node_activity(self.store, node_id=self.node_id, stop_event=self.stop)
                        self.last_full = now
                    else:
                        state = self.store.get_node_activity_state()
                        with _LOCK:
                            body = collect_node_activity(preferences=state['preferences'], node_id=self.node_id,
                                                         fingerprint_key=None, resources_only=True)['public']
                    if body and not self.stop.is_set():
                        frame = {k: body.get(k) for k in ('schema_version', 'available', 'scope', 'node', 'collected_at', 'summary', 'preferences')}
                        frame.update(live=True, refresh_seconds=LIVE_INTERVAL_SECONDS, stale_after_seconds=8,
                                     coverage={k: body.get('coverage', {}).get(k, {}) for k in ('resources', 'processes')},
                                     processes=body.get('processes', []))
                        at = frame['collected_at']
                        frame['processes'] = [dict(row, observed_at=at, stale=False) for row in frame['processes'] if not row.get('stale')]
                        self.store.record_node_activity_live(frame)
                        if self.publish and _view_active(remote=True):
                            with self.frame_lock:
                                self.latest = frame  # At most one unsent frame.
                            self.publish_ready.set()
                except Exception as exc:
                    log.warning('Node live measurement failed: %s', type(exc).__name__)
            self.wake.wait(timeout=max(0.05, interval - (time.monotonic() - self.last_sample)))
            self.wake.clear()

    def send(self):
        while not self.stop.is_set():
            self.publish_ready.wait()
            self.publish_ready.clear()
            with self.frame_lock:
                frame, self.latest = self.latest, None
            if frame is not None and not self.stop.is_set() and _view_active(remote=True):
                try:
                    self.publish(frame)
                except Exception as exc:
                    log.warning('Node live publication failed: %s', type(exc).__name__)


def start_node_activity(store, *, node_id='', publish=None):
    global _WORKER
    if store is None:
        return False
    if getattr(store, '_read_only', True):
        raise RuntimeError('Node measurements require the daemon writer')
    with _WORKER_LOCK:
        if _WORKER is not None and _WORKER.thread.is_alive():
            return False
        _WORKER = worker = _NodeActivityWorker(store, node_id, publish)
        worker.thread.start()
        if worker.publisher:
            worker.publisher.start()
    return True


def stop_node_activity(timeout=3.5):
    global _WORKER
    with _WORKER_LOCK:
        worker = _WORKER
        if worker is None:
            return
        worker.stop.set()
        worker.wake.set()
        worker.publish_ready.set()
    worker.thread.join(timeout=timeout)
    if worker.publisher:
        worker.publisher.join(timeout=0.2)
    with _WORKER_LOCK:
        if not worker.thread.is_alive() and _WORKER is worker:
            _WORKER = None
