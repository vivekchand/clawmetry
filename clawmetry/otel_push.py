"""clawmetry/otel_push.py - OTLP/HTTP push exporter (Pro feature).

Periodically POSTs recent ClawMetry events as OTLP/JSON logRecords to a
customer-configured OpenTelemetry collector (Datadog, Grafana, Honeycomb,
or any OTel-compatible endpoint). Companion to ``routes/otel_export.py``
which is the *pull* shape (collector polls us).

Why push as well as pull?
* Push fits the Datadog / Honeycomb / Grafana Cloud model (their agents
  read from sources, they don't host pull endpoints).
* It works behind NAT / firewalls without exposing the dashboard.

Wiring: ``LocalStore.ingest()`` forwards each event to ``forward_event()``
(non-blocking enqueue). A background thread batches up to N events or
waits up to flush_interval seconds, then POSTs the OTLP envelope.

Defense-in-depth: by the time an event reaches us it has already been
scrubbed by ``redact_event``, so no secret values leave the box even if
the collector is hostile.

Config (env vars; all optional, exporter is off by default):

    CLAWMETRY_OTLP_ENDPOINT      collector URL, e.g.
                                 https://api.honeycomb.io/v1/logs
                                 https://http-intake.logs.datadoghq.com/api/v2/logs
                                 http://localhost:4318/v1/logs
    CLAWMETRY_OTLP_HEADERS       comma-separated "Key: Value" pairs
                                 e.g. "x-honeycomb-team: abc123,x-honeycomb-dataset: clawmetry"
    CLAWMETRY_OTLP_BATCH_MAX     max events per flush (default 200)
    CLAWMETRY_OTLP_FLUSH_SECS    flush cadence in seconds (default 10)
    CLAWMETRY_OTLP_TIMEOUT_SECS  HTTP timeout (default 5)
    CLAWMETRY_OTLP_QUEUE_MAX     bounded queue size (default 10000)

Entitlement: ``otel_export`` (Pro tier; see clawmetry.com/pricing). When
``CLAWMETRY_OTLP_ENDPOINT`` is set but the tier doesn't unlock the key,
the exporter logs a clear warning and refuses to start.
"""
from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from typing import Any, Optional
from urllib import error as urlerror
from urllib import request as urlrequest

_log = logging.getLogger("clawmetry.otel_push")


# ── envelope helpers (mirror routes/otel_export.py) ───────────────────────────


def _event_to_log_record(ev: dict) -> dict:
    """Map a ClawMetry event row to an OTLP LogRecord (JSON)."""
    ts = ev.get("ts") or ev.get("timestamp") or 0
    try:
        ts_ns = str(int(float(ts) * 1_000_000_000))
    except Exception:
        ts_ns = "0"
    event_type = str(ev.get("event_type") or ev.get("type") or "event")
    body = event_type
    role = ev.get("role")
    if not role and isinstance(ev.get("data"), dict):
        role = ev["data"].get("role")

    attrs: list[dict] = []

    def _add(k: str, v):
        if v is None or v == "":
            return
        if isinstance(v, bool):
            attrs.append({"key": k, "value": {"boolValue": v}})
        elif isinstance(v, int):
            attrs.append({"key": k, "value": {"intValue": str(v)}})
        elif isinstance(v, float):
            attrs.append({"key": k, "value": {"doubleValue": v}})
        else:
            attrs.append({"key": k, "value": {"stringValue": str(v)[:512]}})

    _add("session_id", ev.get("session_id"))
    _add("event_type", event_type)
    _add("role", role)
    _add("tool_name", ev.get("tool_name") or ev.get("toolName"))
    _add("model", ev.get("model"))
    _add("agent_type", ev.get("agent_type") or "openclaw")
    _add("node_id", ev.get("node_id"))

    return {
        "timeUnixNano": ts_ns,
        "severityNumber": 9,
        "severityText": "INFO",
        "body": {"stringValue": body},
        "attributes": attrs,
    }


def _build_otlp_envelope(events: list[dict]) -> dict:
    """Wrap LogRecords in the OTLP/JSON resourceLogs/scopeLogs envelope."""
    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "clawmetry"}},
                        {"key": "telemetry.sdk.name", "value": {"stringValue": "clawmetry-otel-push"}},
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": "clawmetry.events", "version": "1"},
                        "logRecords": [_event_to_log_record(e) for e in events],
                    }
                ],
            }
        ]
    }


def _parse_headers(raw: str) -> dict[str, str]:
    """Parse a ``"K1: V1, K2: V2"`` string into a dict. Tolerant of bad
    pieces (drops a malformed pair, keeps going)."""
    out: dict[str, str] = {}
    if not raw:
        return out
    for piece in raw.split(","):
        piece = piece.strip()
        if not piece or ":" not in piece:
            continue
        k, _, v = piece.partition(":")
        k = k.strip()
        v = v.strip()
        if k and v:
            out[k] = v
    return out


# ── HTTP writer ───────────────────────────────────────────────────────────────


class _HTTPWriter:
    """Tiny OTLP/HTTP poster using urllib (no requests dep)."""

    def __init__(self, endpoint: str, headers: dict[str, str], timeout: float) -> None:
        self._endpoint = endpoint
        self._headers = dict(headers)
        self._headers.setdefault("content-type", "application/json")
        self._timeout = timeout

    def send(self, envelope: dict) -> None:
        """POST an OTLP envelope. Raises on transport error or non-2xx."""
        body = json.dumps(envelope).encode("utf-8")
        req = urlrequest.Request(self._endpoint, data=body, method="POST")
        for k, v in self._headers.items():
            req.add_header(k, v)
        try:
            with urlrequest.urlopen(req, timeout=self._timeout) as resp:
                code = getattr(resp, "status", 200)
                if not (200 <= int(code) < 300):
                    raise RuntimeError(f"otel-collector returned {code}")
        except urlerror.HTTPError as exc:
            raise RuntimeError(f"otel-collector {exc.code} {exc.reason}") from exc

    def close(self) -> None:
        # urllib has no persistent connection to close.
        pass


# ── Exporter ──────────────────────────────────────────────────────────────────


class OTLPPushExporter:
    """Bounded-queue, single-thread batching exporter.

    Designed to never block ingest: ``send()`` is a non-blocking enqueue;
    the worker drains in the background. When the queue is full or the
    collector is unreachable, events are dropped and counted rather than
    back-pressuring the daemon.
    """

    def __init__(
        self,
        writer: _HTTPWriter,
        *,
        batch_max: int = 200,
        flush_secs: float = 10.0,
        queue_size: int = 10_000,
    ) -> None:
        self._writer = writer
        self._batch_max = int(batch_max)
        self._flush_secs = float(flush_secs)
        self._q: queue.Queue[Optional[dict[str, Any]]] = queue.Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="otel-push-exporter", daemon=True)
        self._thread.start()
        self.sent_count = 0
        self.dropped_count = 0
        self.error_count = 0
        self.flush_count = 0

    def send(self, event: dict[str, Any]) -> None:
        try:
            self._q.put_nowait(event)
        except queue.Full:
            self.dropped_count += 1

    def close(self, timeout: float = 2.0) -> None:
        self._stop.set()
        try:
            self._q.put_nowait(None)
        except queue.Full:
            pass
        self._thread.join(timeout=timeout)
        try:
            self._writer.close()
        except Exception:
            pass

    def _drain_batch(self, max_wait: float) -> list[dict[str, Any]]:
        """Pull up to ``batch_max`` events; return early when ``max_wait``
        seconds have elapsed since the first event was pulled."""
        batch: list[dict[str, Any]] = []
        deadline: float | None = None
        while len(batch) < self._batch_max:
            timeout = max_wait if not batch else max(0.0, (deadline or 0.0) - time.monotonic())
            if not batch and self._stop.is_set():
                break
            try:
                ev = self._q.get(timeout=timeout)
            except queue.Empty:
                break
            if ev is None:
                self._stop.set()
                break
            batch.append(ev)
            if deadline is None:
                deadline = time.monotonic() + max_wait
        return batch

    def _run(self) -> None:
        while not self._stop.is_set():
            batch = self._drain_batch(self._flush_secs)
            if not batch:
                continue
            envelope = _build_otlp_envelope(batch)
            try:
                self._writer.send(envelope)
                self.sent_count += len(batch)
                self.flush_count += 1
            except Exception as exc:
                self.error_count += 1
                self.dropped_count += len(batch)
                _log.debug("otel-push: flush failed (%s); dropped %d", exc, len(batch))

    def stats(self) -> dict:
        return {
            "sent": self.sent_count,
            "dropped": self.dropped_count,
            "errors": self.error_count,
            "flushes": self.flush_count,
            "queue_size": self._q.qsize(),
        }


# ── Singleton wiring ──────────────────────────────────────────────────────────


_singleton: Optional[OTLPPushExporter] = None
_singleton_lock = threading.Lock()


def _otel_push_entitled() -> bool:
    """Whether this install may run the OTLP push exporter. Grace mode
    lets everyone through; after enforce, only Pro+ installs do."""
    try:
        from clawmetry import entitlements as _ent
        return _ent.get_entitlement().allows_feature("otel_export")
    except Exception:  # pragma: no cover
        return True


def _build_default_writer() -> Optional[_HTTPWriter]:
    endpoint = os.environ.get("CLAWMETRY_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return None
    headers = _parse_headers(os.environ.get("CLAWMETRY_OTLP_HEADERS", ""))
    try:
        timeout = float(os.environ.get("CLAWMETRY_OTLP_TIMEOUT_SECS", "5") or "5")
    except ValueError:
        timeout = 5.0
    return _HTTPWriter(endpoint, headers, timeout=timeout)


def get_default_exporter() -> Optional[OTLPPushExporter]:
    """Return the process-wide exporter, building it from env vars on
    first call. Returns ``None`` when ``CLAWMETRY_OTLP_ENDPOINT`` is
    unset OR the install's tier doesn't unlock ``otel_export``."""
    global _singleton
    if _singleton is not None:
        return _singleton
    with _singleton_lock:
        if _singleton is not None:
            return _singleton
        writer = _build_default_writer()
        if writer is None:
            return None
        if not _otel_push_entitled():
            _log.warning(
                "otel-push: CLAWMETRY_OTLP_ENDPOINT is set but the current tier "
                "does not unlock 'otel_export' (Pro feature on clawmetry.com/pricing). "
                "Exporter will not start. Set CLAWMETRY_ENFORCE=0 to bypass."
            )
            return None
        try:
            batch_max = int(os.environ.get("CLAWMETRY_OTLP_BATCH_MAX", "200") or "200")
        except ValueError:
            batch_max = 200
        try:
            flush_secs = float(os.environ.get("CLAWMETRY_OTLP_FLUSH_SECS", "10") or "10")
        except ValueError:
            flush_secs = 10.0
        try:
            queue_max = int(os.environ.get("CLAWMETRY_OTLP_QUEUE_MAX", "10000") or "10000")
        except ValueError:
            queue_max = 10_000
        _singleton = OTLPPushExporter(
            writer,
            batch_max=batch_max,
            flush_secs=flush_secs,
            queue_size=queue_max,
        )
        _log.info(
            "otel-push: exporter active (endpoint=%s batch_max=%d flush_secs=%.1f)",
            os.environ.get("CLAWMETRY_OTLP_ENDPOINT"),
            batch_max,
            flush_secs,
        )
    return _singleton


def forward_event(event: dict[str, Any]) -> None:
    """Daemon-side hook called from ``LocalStore.ingest`` after redaction.
    Cheap when disabled (single env-var check via the singleton getter)."""
    exp = get_default_exporter()
    if exp is None:
        return
    exp.send(event)


def reset_for_tests() -> None:
    """Test-only helper. Closes the singleton so a fresh one is built
    next call (the next call may again return None if env vars are cleared)."""
    global _singleton
    with _singleton_lock:
        if _singleton is not None:
            try:
                _singleton.close(timeout=0.5)
            except Exception:
                pass
        _singleton = None


def stats() -> dict:
    """Return a snapshot of the exporter's counters, or an empty dict
    when the exporter isn't running. Useful for the status endpoint."""
    exp = _singleton
    if exp is None:
        return {"running": False}
    s = exp.stats()
    s["running"] = True
    return s
