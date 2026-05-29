"""clawmetry/siem.py: OSS delegating shim after the impl moved to clawmetry-pro.

The real SIEM/syslog forward (UDP/TCP/TLS, CEF/JSON, RFC 5424 framing,
bounded-queue background exporter) ships in the closed-source
``clawmetry-pro`` package as ``clawmetry_pro/lib/siem.py``. SIEM export
is an Enterprise feature (entitlement key ``siem_export``).

When clawmetry-pro is installed, this shim re-exports the real symbols
so ``from clawmetry import siem; siem.forward_event(event)`` keeps
working unchanged for ``LocalStore.ingest`` and the rest of the daemon
hot path.

When clawmetry-pro is NOT installed, all public functions are cheap
no-ops and ``get_default_exporter`` returns ``None`` (matches the
pre-move behavior when ``CLAWMETRY_SIEM_HOST`` was unset).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("clawmetry.siem")


def _pro():
    """Return ``clawmetry_pro.lib.siem`` when importable, else ``None``."""
    try:
        from clawmetry_pro.lib import siem as _s
        return _s
    except Exception:
        return None


# ── public surface ─────────────────────────────────────────────────────────────


def forward_event(event: dict[str, Any]) -> None:
    """Daemon hook called from ``LocalStore.ingest`` after redaction.

    Delegates to clawmetry-pro's exporter when installed; no-op otherwise.
    Never raises; never blocks ingest. Same contract as the pre-move impl.
    """
    pro = _pro()
    if pro is None:
        return
    try:
        pro.forward_event(event)
    except Exception as exc:
        logger.warning("siem delegation failed: %s", exc)


def get_default_exporter() -> Optional[Any]:
    """Return the process-wide SIEMExporter when clawmetry-pro is
    installed and ``CLAWMETRY_SIEM_HOST`` is configured. ``None`` otherwise."""
    pro = _pro()
    if pro is None:
        return None
    try:
        return pro.get_default_exporter()
    except Exception as exc:
        logger.warning("siem get_default_exporter delegation failed: %s", exc)
        return None


def reset_for_tests() -> None:
    """Test-only helper. No-op when clawmetry-pro is not installed."""
    pro = _pro()
    if pro is None:
        return
    try:
        pro.reset_for_tests()
    except Exception:
        pass


# ── format_* helpers (only useful when pro is present) ───────────────────────


def format_cef(event: dict[str, Any], app_name: str = "clawmetry", version: str = "1.0") -> str:
    pro = _pro()
    if pro is None:
        return ""
    try:
        return pro.format_cef(event, app_name=app_name, version=version)
    except Exception:
        return ""


def format_json(event: dict[str, Any]) -> str:
    pro = _pro()
    if pro is None:
        return ""
    try:
        return pro.format_json(event)
    except Exception:
        return ""


def format_syslog_line(*args, **kwargs) -> str:
    pro = _pro()
    if pro is None:
        return ""
    try:
        return pro.format_syslog_line(*args, **kwargs)
    except Exception:
        return ""


# ── class re-export ───────────────────────────────────────────────────────────


def __getattr__(name: str):
    """Lazy-export ``SIEMExporter`` and other class symbols from the Pro
    package. Raises ``AttributeError`` when the symbol does not exist
    in the closed package (so callers see the same error they would
    pre-move) and when ``clawmetry-pro`` is not installed at all.
    """
    if name in ("SIEMExporter", "FACILITY_LOCAL0"):
        pro = _pro()
        if pro is None:
            raise AttributeError(
                f"clawmetry.siem.{name} requires clawmetry-pro. Install with "
                "a license key, or use Cloud Pro."
            )
        return getattr(pro, name)
    raise AttributeError(f"module 'clawmetry.siem' has no attribute {name!r}")
