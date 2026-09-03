"""OTel runtime profiles — the seam between the generic OTLP receiver and
runtime-specific knowledge (WO-57).

The receiver in ``dashboard.py`` speaks OpenTelemetry and nothing else: it
stores every span, keeps every log record in the ledger, and lights the
generic tiles from attributes every emitter uses. What it does NOT know is
what a particular runtime calls things: that ``claude_code.token.usage``
splits by a ``type`` attribute, that a ``tool.blocked_on_user`` span is time
spent waiting on a human, that ``session.id`` on the wire is stored as
``<runtime>:<id>`` by the daemon, or which file to write to switch the
runtime's exporter on.

That knowledge is a **profile**, registered here. Free runtimes register
theirs from this repo; paid runtimes register theirs from ``clawmetry-pro``
through the ``clawmetry.extensions`` entry point, the same way their
transcript adapters arrive. No profile registered means the receiver treats
the emitter as any other OTel app: which is exactly what a free install
gets, and exactly what shipped before profiles existed.

A profile is data plus one optional object (the instrumenter). Nothing in
it executes vendor code inside the receiver.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class OtelRuntimeProfile:
    """What the receiver needs to know about one runtime's native exporter.

    Every field has a "do nothing" default, so a partial profile is safe.
    """

    runtime: str
    """ClawMetry runtime id, e.g. ``codex``. Also the CLI target."""

    service_names: Tuple[str, ...] = ()
    """``service.name`` resource values that identify this emitter."""

    aliases: Tuple[str, ...] = ()
    """Extra CLI spellings (``claude`` for ``claude_code``)."""

    label: str = ""

    metric_prefix: str = ""
    """Metrics whose name starts with this belong to the runtime."""

    event_prefix: str = ""
    """Log event names starting with this belong to the runtime."""

    session_key_prefix: str = ""
    """The daemon's session-key form (``codex:``). Empty = no rewriting.
    Applied to events and spans only; the ledger keeps the id as sent."""

    tile_token_metric: str = ""
    """Metric whose typed data points may reach the tokens tile."""

    token_type_fields: Dict[str, str] = field(default_factory=dict)
    """Lower-cased data-point ``type`` -> tokens-cache field name."""

    typed_events: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    """Event-name suffix -> attribute names copied by name onto the event."""

    text_fields: Tuple[str, ...] = ("prompt", "response")
    """Typed-event attributes that are free text: capped and tagged."""

    llm_extra_fields: Tuple[Tuple[str, str], ...] = ()
    """(attribute, data key) pairs copied onto the request (``llm_call``) event."""

    span_attr_aliases: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    """Extra attribute names per canonical span field:
    ``cache_read`` / ``cache_write`` / ``tool_name``."""

    wait_span_suffix: str = ""
    """Span-name suffix meaning "blocked on a human" (``.blocked_on_user``)."""

    instrumenter: Optional[Any] = None
    """Object with ``install(...)``, ``uninstall(...)``, ``status(...)``
    (see ``clawmetry.instrument``). ``None`` = no ``clawmetry instrument``
    support for this runtime."""

    def matches_service(self, service_name: str) -> bool:
        s = (service_name or "").strip().lower()
        return bool(s) and s in tuple(x.lower() for x in self.service_names)

    def session_key(self, raw: Any) -> Optional[str]:
        sid = str(raw or "").strip()
        if not sid:
            return None
        if not self.session_key_prefix or sid.startswith(self.session_key_prefix):
            return sid
        return self.session_key_prefix + sid


_lock = threading.Lock()
_profiles: Dict[str, OtelRuntimeProfile] = {}


def register(profile: OtelRuntimeProfile) -> None:
    """Idempotent by runtime id; a later registration replaces an earlier
    one, so a pro profile can override a stub."""
    with _lock:
        _profiles[profile.runtime] = profile


def unregister(runtime: str) -> None:
    with _lock:
        _profiles.pop(runtime, None)


def all_profiles() -> Tuple[OtelRuntimeProfile, ...]:
    with _lock:
        return tuple(_profiles.values())


def by_runtime(runtime: str) -> Optional[OtelRuntimeProfile]:
    key = (runtime or "").strip().lower()
    with _lock:
        p = _profiles.get(key)
        if p is not None:
            return p
        for prof in _profiles.values():
            if key == prof.runtime or key in tuple(a.lower() for a in prof.aliases):
                return prof
    return None


def by_service_name(service_name: str) -> Optional[OtelRuntimeProfile]:
    with _lock:
        for prof in _profiles.values():
            if prof.matches_service(service_name):
                return prof
    return None


def for_metric(metric_name: str) -> Optional[OtelRuntimeProfile]:
    name = metric_name or ""
    with _lock:
        for prof in _profiles.values():
            if prof.metric_prefix and name.startswith(prof.metric_prefix):
                return prof
    return None


def for_event(event_name: str) -> Optional[OtelRuntimeProfile]:
    name = (event_name or "").lower()
    with _lock:
        for prof in _profiles.values():
            if prof.event_prefix and name.startswith(prof.event_prefix.lower()):
                return prof
    return None


def _reset_for_tests() -> None:
    with _lock:
        _profiles.clear()
