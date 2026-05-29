"""clawmetry/otel_push.py: OSS delegating shim after the impl moved to clawmetry-pro.

The real OTLP/HTTP push exporter (bounded queue, background thread,
batching, OTLP envelope builder) ships in the closed-source
``clawmetry-pro`` package as ``clawmetry_pro/otel_push.py``. When that
package is installed, this shim delegates ``forward_event(event)`` +
``stats()`` to it.

When clawmetry-pro is NOT installed (vanilla OSS), every public function
here is a cheap no-op. ``LocalStore.ingest()`` calls ``forward_event()``
on every ingest; the no-op path adds one attribute lookup per event,
which is the same cost as the previous module-not-found ``try / except
ImportError`` shape.

The status + flush HTTP endpoints that used to live in OSS
``routes/otel_export.py`` also moved to clawmetry-pro; OSS keeps only
the pull endpoint at ``GET /api/otel/export``.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("clawmetry.otel_push")


def _pro():
    """Return ``clawmetry_pro.otel_push`` when importable, else ``None``.

    Cached implicitly by the Python import system; the first call after
    install pays one ImportError, subsequent calls are dict lookups.
    """
    try:
        from clawmetry_pro import otel_push as _otelp
        return _otelp
    except Exception:
        return None


def forward_event(event: dict[str, Any]) -> None:
    """Daemon hook called from ``LocalStore.ingest`` after redaction.

    Delegates to clawmetry-pro's exporter when installed; no-op otherwise.
    Never raises; never blocks ingest. Same contract as the pre-move
    implementation.
    """
    pro = _pro()
    if pro is None:
        return
    try:
        pro.forward_event(event)
    except Exception as exc:
        logger.warning("otel_push delegation failed: %s", exc)


def stats() -> dict:
    """Return a snapshot of the exporter's counters, or
    ``{"running": False}`` when the closed package is not installed
    or the exporter is not configured. Used by the
    ``GET /api/otel/push/status`` endpoint (also moved to clawmetry-pro)."""
    pro = _pro()
    if pro is None:
        return {"running": False, "reason": "clawmetry-pro not installed"}
    try:
        return pro.stats()
    except Exception as exc:
        return {"running": False, "error": str(exc)}


def reset_for_tests() -> None:
    """Test-only helper. Forwards to clawmetry-pro's reset; no-op
    when the closed package is unavailable."""
    pro = _pro()
    if pro is None:
        return
    try:
        pro.reset_for_tests()
    except Exception:
        pass
