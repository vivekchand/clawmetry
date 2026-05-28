"""Daemon-side SIEM/syslog exporter — Issue #2199.

Forwards ClawMetry events to an external syslog collector (Splunk / QRadar /
ArcSight / Elastic SIEM / any RFC 5424 receiver) as CEF (Common Event Format)
or as JSON, framed per RFC 5424. Runs on the daemon side because that is where
the data lives — the cloud is E2E-encrypted and never sees plaintext events.

Off by default. Activated when ``CLAWMETRY_SIEM_HOST`` is set (or via the
``LocalStore`` config hook below). Layered like redaction: pure formatter
functions are independent of the IO, so the exporter class can be tested with
a stub ``writer`` callback instead of opening real sockets.

Wiring: ``LocalStore.ingest()`` forwards each event to ``forward_event()``
*after* the redaction pass, so secrets never reach the SIEM either. The
exporter is fire-and-forget — events go onto a bounded queue and a single
background thread drains them. Ingest is never blocked on socket IO.

Composes with #2204 redaction and #2210 hash chain: by the time an event
reaches ``forward_event`` it has already been scrubbed by ``redact_event``
and stamped with ``chain_prev_hash`` / ``chain_hash``, so the SIEM line
carries the same audit-grade payload that lives in DuckDB.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import socket
import ssl
import threading
import time
from typing import Any, Callable, Iterable, Optional

_log = logging.getLogger(__name__)

# ── RFC 5424 severities ─────────────────────────────────────────────────────
SEV_EMERG = 0
SEV_ALERT = 1
SEV_CRIT = 2
SEV_ERROR = 3
SEV_WARN = 4
SEV_NOTICE = 5
SEV_INFO = 6
SEV_DEBUG = 7

FACILITY_LOCAL0 = 16

# ── Event taxonomy → CEF signature IDs ──────────────────────────────────────
# Keep these stable; SIEM rules key off them. New event types fall through to
# 9999 "Generic Event" rather than crashing, so adding an event type in the
# daemon does not require a SIEM-side change to be observed.
_EVENT_META: dict[str, tuple[int, str]] = {
    # Tool surface.
    "tool.call":         (1001, "Tool Call"),
    "tool_call":         (1001, "Tool Call"),
    "tool.use":          (1001, "Tool Use"),
    "tool.result":       (1002, "Tool Result"),
    "tool_use_result":   (1002, "Tool Result"),
    "mcp_call":          (1003, "MCP Call"),
    # Message / channel surface.
    "message":           (2001, "Message"),
    "channel.in":        (2001, "Message Received"),
    "channel.out":       (2002, "Message Sent"),
    # Model surface.
    "model.completed":   (3001, "LLM Usage"),
    "model_use":         (3001, "LLM Usage"),
    "model.changed":     (3002, "Model Changed"),
    "prompt.submitted":  (3003, "Prompt Submitted"),
    # Session / agent surface.
    "session.started":   (4001, "Session Started"),
    "session.ended":     (4002, "Session Ended"),
    "compaction":        (4003, "Transcript Compaction"),
    # Operational surface (the security-team-interesting bits).
    "budget_exceeded":   (5001, "Budget Limit Exceeded"),
    "security_threat":   (6001, "Threat Signature Match"),
    "approval_required": (7001, "Approval Required"),
    "cron_run":          (8001, "Cron Run"),
    "connector.health":  (8002, "Connector Health"),
    "daemon.error":      (9002, "Daemon Error"),
    "gateway.metric":    (9003, "Gateway Metric"),
}


def _severity_for(event: dict[str, Any]) -> int:
    """Map an event to an RFC 5424 severity. ERROR for known failure shapes,
    INFO for everything else — keep it boring so SIEM rules stay stable."""
    et = (event.get("event_type") or "").strip()
    if et == "daemon.error" or et == "security_threat" or et == "budget_exceeded":
        return SEV_ERROR
    if et == "approval_required":
        return SEV_WARN
    data = event.get("data")
    if isinstance(data, dict):
        # tool.result / tool_use_result carry an is_error flag.
        if data.get("is_error") or data.get("isError"):
            return SEV_ERROR
        if data.get("success") is False:
            return SEV_ERROR
    return SEV_INFO


# ── CEF formatting ──────────────────────────────────────────────────────────
def _cef_escape(value: Any) -> str:
    """Escape per the ArcSight CEF spec: \\, =, |, and newlines in extension
    values. Header pipes are not used because we never emit pipes in the
    header fields themselves."""
    if value is None:
        return ""
    s = value if isinstance(value, str) else str(value)
    return (
        s.replace("\\", "\\\\")
        .replace("=", "\\=")
        .replace("|", "\\|")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def _ext(parts: list[str], key: str, value: Any) -> None:
    """Append ``key=escaped(value)`` to ``parts`` when value is meaningful.
    Empty strings, None, and missing keys are dropped — SIEMs do not need
    parse-noise."""
    if value is None or value == "":
        return
    if isinstance(value, bool):
        parts.append(f"{key}={'true' if value else 'false'}")
        return
    if isinstance(value, (int, float)):
        parts.append(f"{key}={value}")
        return
    parts.append(f"{key}={_cef_escape(value)}")


def _data(event: dict[str, Any]) -> dict[str, Any]:
    """Return event.data as a dict regardless of whether it was stored as a
    dict, a JSON string, or absent. Never raises."""
    d = event.get("data")
    if isinstance(d, dict):
        return d
    if isinstance(d, (bytes, bytearray)):
        try:
            return json.loads(d.decode("utf-8", "replace"))
        except Exception:
            return {}
    if isinstance(d, str):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return {}


def format_cef(event: dict[str, Any], app_name: str = "clawmetry", version: str = "1.0") -> str:
    """Build a CEF line for an event. Stable field keys: SIEM rules read
    ``cs1=sessionKey`` / ``act=toolName`` / ``cn1=durationMs`` / ``cfp1=costUsd`` etc.
    See README in #2199 for the full mapping."""
    et = (event.get("event_type") or "").strip()
    sig_id, name = _EVENT_META.get(et, (9999, et or "Generic Event"))
    sev = _severity_for(event)
    # CEF severity is 0–10; map syslog severity 3 (Error) → 7, anything else → 3.
    cef_sev = 7 if sev <= SEV_ERROR else 3

    parts: list[str] = []
    _ext(parts, "rt", event.get("ts"))
    _ext(parts, "cs1", event.get("session_id"))
    if event.get("session_id"):
        _ext(parts, "cs1Label", "sessionId")
    _ext(parts, "cs2", event.get("agent_id"))
    if event.get("agent_id"):
        _ext(parts, "cs2Label", "agentId")
    _ext(parts, "deviceExternalId", event.get("node_id"))
    _ext(parts, "cs5", event.get("chain_hash"))
    if event.get("chain_hash"):
        _ext(parts, "cs5Label", "chainHash")
    _ext(parts, "cs6", event.get("chain_prev_hash"))
    if event.get("chain_prev_hash"):
        _ext(parts, "cs6Label", "chainPrevHash")

    d = _data(event)
    if et in ("tool.call", "tool_call", "tool.use", "mcp_call"):
        _ext(parts, "act", d.get("name") or d.get("tool_name") or d.get("toolName"))
    elif et in ("tool.result", "tool_use_result"):
        _ext(parts, "act", d.get("name") or d.get("tool_name") or d.get("toolName"))
        is_err = bool(d.get("is_error") or d.get("isError"))
        _ext(parts, "outcome", "failure" if is_err else "success")
        _ext(parts, "cn1", d.get("duration_ms") or d.get("durationMs"))
        if d.get("duration_ms") or d.get("durationMs"):
            _ext(parts, "cn1Label", "durationMs")
    elif et in ("model.completed", "model_use"):
        _ext(parts, "deviceCustomString3", event.get("model") or d.get("model"))
        _ext(parts, "cs3Label", "model")
        _ext(parts, "cn1", d.get("input_tokens") or d.get("inputTokens"))
        if d.get("input_tokens") or d.get("inputTokens"):
            _ext(parts, "cn1Label", "inputTokens")
        _ext(parts, "cn2", d.get("output_tokens") or d.get("outputTokens"))
        if d.get("output_tokens") or d.get("outputTokens"):
            _ext(parts, "cn2Label", "outputTokens")
        _ext(parts, "cfp1", event.get("cost_usd"))
        if event.get("cost_usd") is not None:
            _ext(parts, "cfp1Label", "costUsd")
    elif et in ("channel.in", "message"):
        _ext(parts, "suser", d.get("from") or d.get("user"))
        _ext(parts, "deviceCustomString4", d.get("channel"))
        _ext(parts, "cs4Label", "channel")
    elif et == "channel.out":
        _ext(parts, "duser", d.get("to") or d.get("user"))
        _ext(parts, "deviceCustomString4", d.get("channel"))
        _ext(parts, "cs4Label", "channel")
        is_ok = d.get("success")
        if is_ok is not None:
            _ext(parts, "outcome", "success" if is_ok else "failure")
    elif et == "security_threat":
        _ext(parts, "act", d.get("signature_id") or d.get("rule"))
        _ext(parts, "reason", d.get("description") or d.get("message"))

    ext = " ".join(parts)
    return f"CEF:0|ClawMetry|clawmetry|{version}|{sig_id}|{name}|{cef_sev}|{ext}"


def format_json(event: dict[str, Any]) -> str:
    """Compact JSON line. Drops non-serialisable values rather than crashing."""
    try:
        return json.dumps(event, separators=(",", ":"), default=str, sort_keys=True)
    except Exception as exc:
        _log.warning("siem: json format failed (%s); emitting minimal record", exc)
        return json.dumps(
            {
                "id": event.get("id"),
                "event_type": event.get("event_type"),
                "ts": event.get("ts"),
                "_format_error": str(exc),
            },
            separators=(",", ":"),
        )


def format_syslog_line(
    event: dict[str, Any],
    *,
    fmt: str = "cef",
    facility: int = FACILITY_LOCAL0,
    app_name: str = "clawmetry",
    hostname: str = "-",
    version: str = "1.0",
) -> str:
    """RFC 5424 frame: ``<PRI>1 TIMESTAMP HOSTNAME APP - MSGID - MSG``.
    PRI = facility * 8 + severity. TIMESTAMP is ISO-8601; we use the event's
    own ``ts`` if it parses, else current UTC."""
    sev = _severity_for(event)
    pri = facility * 8 + sev
    ts_raw = event.get("ts")
    timestamp = _iso8601(ts_raw)
    msg_id = (event.get("event_type") or "event").replace(" ", "_")
    body = format_cef(event, app_name=app_name, version=version) if fmt == "cef" else format_json(event)
    return f"<{pri}>1 {timestamp} {hostname} {app_name} - {msg_id} - {body}"


def _iso8601(ts_raw: Any) -> str:
    """Coerce any event timestamp into ISO-8601 UTC. Falls back to now()."""
    if isinstance(ts_raw, str) and ts_raw:
        # Already-good ISO strings pass through unchanged.
        return ts_raw
    try:
        if isinstance(ts_raw, (int, float)):
            # Heuristic: millisecond epochs are > 10^11.
            secs = ts_raw / 1000.0 if ts_raw > 1e11 else float(ts_raw)
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(secs))
    except Exception:
        pass
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── Transport ───────────────────────────────────────────────────────────────
class _UDPWriter:
    def __init__(self, host: str, port: int) -> None:
        self._addr = (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, line: str) -> None:
        self._sock.sendto(line.encode("utf-8"), self._addr)

    def close(self) -> None:
        try:
            self._sock.close()
        except Exception:
            pass


class _TCPWriter:
    """TCP / TCP-TLS writer with lazy connect + auto-reconnect on send error.
    Frames each message with a trailing newline (the common syslog convention
    when no octet-counting framer is configured)."""

    def __init__(self, host: str, port: int, tls: bool = False, connect_timeout: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._tls = tls
        self._timeout = connect_timeout
        self._sock: Optional[socket.socket] = None

    def _connect(self) -> None:
        s = socket.create_connection((self._host, self._port), timeout=self._timeout)
        if self._tls:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self._host)
        s.settimeout(self._timeout)
        self._sock = s

    def write(self, line: str) -> None:
        if self._sock is None:
            self._connect()
        payload = line.encode("utf-8") + b"\n"
        try:
            assert self._sock is not None
            self._sock.sendall(payload)
        except (OSError, ssl.SSLError):
            # one reconnect attempt then re-raise so the worker can re-queue
            self.close()
            self._connect()
            assert self._sock is not None
            self._sock.sendall(payload)

    def close(self) -> None:
        try:
            if self._sock is not None:
                self._sock.close()
        finally:
            self._sock = None


# ── Exporter ────────────────────────────────────────────────────────────────
class SIEMExporter:
    """Bounded-queue, single-thread exporter. Designed to never block ingest:
    ``send()`` is a non-blocking enqueue; the worker drains in the background.
    When the queue is full or the collector is unreachable, events are dropped
    and counted (``dropped_count``) rather than back-pressuring the daemon."""

    def __init__(
        self,
        writer: Callable[[str], None] | Any,
        *,
        fmt: str = "cef",
        facility: int = FACILITY_LOCAL0,
        app_name: str = "clawmetry",
        queue_size: int = 10_000,
        version: str = "1.0",
    ) -> None:
        self._writer = writer
        self._fmt = fmt
        self._facility = facility
        self._app_name = app_name
        self._version = version
        self._q: queue.Queue[Optional[dict[str, Any]]] = queue.Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="siem-exporter", daemon=True)
        self._thread.start()
        self.sent_count = 0
        self.dropped_count = 0
        self.error_count = 0

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
        close = getattr(self._writer, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                event = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            if event is None:
                break
            try:
                line = format_syslog_line(
                    event,
                    fmt=self._fmt,
                    facility=self._facility,
                    app_name=self._app_name,
                    version=self._version,
                )
                write = self._writer if callable(self._writer) else self._writer.write
                write(line)
                self.sent_count += 1
            except Exception as exc:
                # Never let a bad event or a dead collector crash the worker.
                self.error_count += 1
                _log.debug("siem: send failed (%s); dropping event", exc)


# ── Singleton wiring ────────────────────────────────────────────────────────
_singleton: Optional[SIEMExporter] = None
_singleton_lock = threading.Lock()


def _build_default_writer() -> Optional[Any]:
    host = os.environ.get("CLAWMETRY_SIEM_HOST", "").strip()
    if not host:
        return None
    port = int(os.environ.get("CLAWMETRY_SIEM_PORT", "514"))
    protocol = (os.environ.get("CLAWMETRY_SIEM_PROTOCOL", "udp") or "udp").strip().lower()
    if protocol == "udp":
        return _UDPWriter(host, port)
    if protocol == "tcp":
        return _TCPWriter(host, port, tls=False)
    if protocol in ("tcp-tls", "tls", "tcptls"):
        return _TCPWriter(host, port, tls=True)
    _log.warning("siem: unknown CLAWMETRY_SIEM_PROTOCOL=%s; disabling", protocol)
    return None


def get_default_exporter() -> Optional[SIEMExporter]:
    """Return the process-wide exporter, building it from env vars on first
    call. Returns None when ``CLAWMETRY_SIEM_HOST`` is unset (the default)."""
    global _singleton
    if _singleton is not None:
        return _singleton
    with _singleton_lock:
        if _singleton is not None:
            return _singleton
        writer = _build_default_writer()
        if writer is None:
            return None
        fmt = (os.environ.get("CLAWMETRY_SIEM_FORMAT", "cef") or "cef").strip().lower()
        facility = int(os.environ.get("CLAWMETRY_SIEM_FACILITY", str(FACILITY_LOCAL0)))
        app_name = os.environ.get("CLAWMETRY_SIEM_APPNAME", "clawmetry") or "clawmetry"
        _singleton = SIEMExporter(
            writer, fmt=fmt, facility=facility, app_name=app_name,
        )
        _log.info("siem: exporter active (host=%s fmt=%s)", os.environ.get("CLAWMETRY_SIEM_HOST"), fmt)
    return _singleton


def forward_event(event: dict[str, Any]) -> None:
    """Daemon-side hook called from ``LocalStore.ingest`` after redaction.
    Cheap when disabled (single env-var check via the singleton getter)."""
    exp = get_default_exporter()
    if exp is None:
        return
    exp.send(event)


def reset_for_tests() -> None:
    """Test-only helper. Closes the singleton so a fresh one is built next
    call (the next call may again return None if env vars are cleared)."""
    global _singleton
    with _singleton_lock:
        if _singleton is not None:
            try:
                _singleton.close(timeout=0.5)
            except Exception:
                pass
        _singleton = None
