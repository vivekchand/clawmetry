"""Find applications on this machine that already emit OpenTelemetry (#4784).

Runtime detection is filesystem-shaped: ``~/.claude``, ``~/.codex`` and
friends. It cannot see the LangChain service two terminal windows over that is
already exporting OTLP, to a collector or to nowhere. Discovery is passive
today, so such an app becomes visible only once somebody points it at us.

Two cheap, read-only strategies:

* **port probe** - something is listening on a conventional collector port
  (4317 OTLP/gRPC, 4318 OTLP/HTTP). Stdlib, every platform, no permissions;
* **process env scan** - a same-user process carries
  ``OTEL_EXPORTER_OTLP_ENDPOINT`` or a per-signal sibling. Names the app AND
  the endpoint it currently uses, which is what makes the suggestion
  actionable.

READ-ONLY, and it stays that way (ADR-005). Nothing here modifies another
application's environment, config or files. We detect and suggest; the person
applies. A detected app has sent us nothing, so it is never reported as an
observed runtime: counting it as one with zero cost would be a lie about
coverage.

THE PLATFORM FACT, measured rather than assumed. The issue expected macOS to
block reading another process's environment, and to degrade to port-probing
there. That is not what happens: on macOS 26 with psutil 7.2.2, a same-user
process's environ reads fine (699 readable, 39 blocked, of this machine's own
processes). Same-user is the only population this module is allowed to look at
anyway, so there is no macOS-specific degradation to declare, and declaring
one would tell users about a limitation they do not have.

What DOES degrade is psutil's absence: it is not in ``install_requires`` (it
is lazily imported in three places in ``sync.py``), so on an install without
it the env scan cannot run and the result says exactly that.

CROSS-USER IS FILTERED, NOT CAUGHT. Another user's process must never be read,
and the guard is an explicit username comparison rather than waiting for
``AccessDenied``. Measured why: ``psutil.Process(0).environ()`` on macOS
returns ``{}`` and raises NOTHING, so an implementation that relies on the
exception has no boundary at all where the kernel task is concerned.

Product record: requirement "OpenTelemetry Emitter Discovery"
(8c1ea52d-df48-4b74-b0d2-cbe0488535ad), a child of Local Agent Observability.
Repo-side design: ``docs/blueprints/otel-sdk-and-ingest.md``, component
``#OtelEmitterDiscovery``, ADR-005. The three measured facts above are
AC-OTD-001.1, .3 and .7 there, and blueprint ADR-001/002/004, recorded so they
are not re-assumed next time.
"""

from __future__ import annotations

import os
import socket
import time
from typing import Any

# Conventional OTLP collector ports. Deliberately short: a long list turns a
# cheap probe into a port scan of the user's own machine.
COLLECTOR_PORTS: tuple = (
    (4317, "OTLP/gRPC"),
    (4318, "OTLP/HTTP"),
)

# The endpoint variables an exporter actually reads, most specific first, so a
# per-signal override is reported ahead of the general one.
_ENDPOINT_VARS: tuple = (
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
)

_PROBE_TIMEOUT_S = 0.1
_MAX_PROCESSES = 2000


def _port_is_listening(port: int, timeout: float = _PROBE_TIMEOUT_S) -> bool:
    """True when something accepts a loopback TCP connection on ``port``.

    Loopback only and a 100 ms budget, so the whole sweep costs well under a
    second on a quiet machine and never touches a remote host.
    """
    for family, addr in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        s = None
        try:
            s = socket.socket(family, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((addr, port)) == 0:
                return True
        except OSError:
            continue
        finally:
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
    return False


def _own_receiver_port() -> int | None:
    """The port ClawMetry's OWN OTLP receiver is listening on, if any.

    Without this the feature suggests redirecting the user's app to
    ClawMetry... at ClawMetry. Measured on this machine: :4318 was live and
    the listener was our own Flask compat receiver
    (``instrument._COMPAT_PORT``), which a naive probe reports as "a
    collector is running, send us a copy".
    """
    try:
        from clawmetry import instrument as _inst
        info = _inst.probe_receiver()
        if info and info.get("listening"):
            return int(info.get("port") or 0) or None
    except Exception:
        pass
    return None


def probe_collector_ports() -> list:
    """Conventional collector ports with something listening on them.

    A port probe proves something ACCEPTS a connection. It cannot prove WHO,
    and on this platform it cannot be made to: ``psutil.net_connections()``
    raises ``AccessDenied`` on macOS without root, and requiring root to
    render a suggestion is not a trade this product makes. So a finding here
    is reported as what it is, and a port ClawMetry may itself own carries
    ``is_clawmetry_receiver`` and is never offered a redirect instruction.
    """
    mine = _own_receiver_port()
    out = []
    for port, proto in COLLECTOR_PORTS:
        try:
            if not _port_is_listening(port):
                continue
            is_self = (mine is not None and port == mine)
            out.append({
                "name": ("ClawMetry's own OTLP receiver" if is_self
                         else f"something listening on :{port}"),
                "endpoint": f"http://localhost:{port}",
                "protocol": proto,
                "evidence": "port_probe",
                "is_clawmetry_receiver": is_self,
                # A port probe never identifies the process, so never claim it
                # did. The env scan below is what NAMES an application.
                "identified": False,
            })
        except Exception:
            continue
    return out


def _current_username() -> str:
    for getter in (lambda: os.getlogin(), lambda: os.environ.get("USER", ""),
                   lambda: os.environ.get("USERNAME", "")):
        try:
            v = getter()
            if v:
                return str(v)
        except Exception:
            continue
    return ""


def scan_process_env() -> tuple:
    """Same-user processes exporting OTLP. Returns ``(apps, degraded_reason)``.

    ``degraded_reason`` is a plain-words sentence when the scan could not run
    at all, and ``None`` when it did. A caller must be able to tell "nothing
    is exporting" from "I could not look", which is the same distinction the
    rest of the product draws between an empty result and an unreadable one.
    """
    try:
        import psutil  # type: ignore
    except ImportError:
        return [], ("Cannot list processes: psutil is not installed. "
                    "Install it (pip install psutil) to also find apps that "
                    "export to somewhere other than a local collector.")

    me = _current_username()
    apps: list = []
    seen: set = set()
    scanned = 0
    try:
        procs = psutil.process_iter(["pid", "name", "username"])
    except Exception as exc:  # pragma: no cover - defensive
        return [], f"Cannot list processes on this machine ({type(exc).__name__})."

    for proc in procs:
        if scanned >= _MAX_PROCESSES:
            break
        scanned += 1
        info = getattr(proc, "info", {}) or {}
        owner = info.get("username") or ""
        # Explicit ownership filter. NOT a try/except around environ(): a
        # process we do not own must never be read, and on macOS pid 0
        # answers {} without raising, so the exception is not a boundary.
        if not me or owner != me:
            continue
        try:
            env = proc.environ() or {}
        except Exception:
            continue
        endpoint = None
        for var in _ENDPOINT_VARS:
            if env.get(var):
                endpoint = env[var]
                break
        if not endpoint:
            continue
        # OTEL_SERVICE_NAME is the app's own name for itself and is what a
        # reader recognises; the process name is often just "Python".
        proc_name = info.get("name") or f"pid {info.get('pid')}"
        name = env.get("OTEL_SERVICE_NAME") or proc_name
        key = (name, endpoint)
        if key in seen:
            continue
        seen.add(key)
        apps.append({
            "name": str(name),
            "process": str(proc_name),
            "endpoint": str(endpoint),
            "evidence": "process_env",
            "service_name": env.get("OTEL_SERVICE_NAME") or None,
            "identified": True,
        })
    return apps, None


def discover_otel_emitters(now_ms: int | None = None) -> dict:
    """Applications on this machine that already emit OpenTelemetry.

    Returns ``{apps, degraded, degraded_reason, checked_ports, scanned_at_ms}``.
    Never raises: discovery is a suggestion, and a suggestion that can break
    the snapshot is worse than no suggestion.
    """
    now_ms = int(now_ms if now_ms is not None else time.time() * 1000)
    apps: list = []
    try:
        apps.extend(probe_collector_ports())
    except Exception:
        pass
    try:
        env_apps, reason = scan_process_env()
    except Exception as exc:  # pragma: no cover - defensive
        env_apps, reason = [], f"Process scan failed ({type(exc).__name__})."
    apps.extend(env_apps)
    for a in apps:
        a.setdefault("first_seen_ms", now_ms)
        a.setdefault("is_clawmetry_receiver", False)
    # Only somebody else's exporter is worth a redirect suggestion. Ours is
    # already here, and an unidentified listener might be ours.
    suggestable = [a for a in apps if not a.get("is_clawmetry_receiver")]
    return {
        "apps": apps,
        "suggestable": suggestable,
        "degraded": bool(reason),
        "degraded_reason": reason,
        "checked_ports": [p for p, _ in COLLECTOR_PORTS],
        "scanned_at_ms": now_ms,
    }


def redirect_instruction(endpoint_here: str = "http://localhost:8900") -> str:
    """The copyable line that points an app's exporter at ClawMetry.

    A suggestion, never applied for the user (ADR-005): we do not edit another
    application's environment.
    """
    return f"OTEL_EXPORTER_OTLP_ENDPOINT={endpoint_here} <your app command>"
