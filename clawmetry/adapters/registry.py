"""Process-wide adapter registry.

Adapters register themselves at startup (from ``dashboard.py`` or via
entry-point plugins using :mod:`clawmetry.extensions`). The dashboard
then iterates the registry to build the multi-agent chip bar and route
per-agent requests.
"""
from __future__ import annotations

import logging
import threading
from typing import List, Optional

from .base import AgentAdapter, DetectResult

logger = logging.getLogger("clawmetry.adapters")

_adapters: List[AgentAdapter] = []
_lock = threading.Lock()


def register(adapter: AgentAdapter) -> None:
    """Register an adapter instance. Idempotent on ``adapter.name``.

    Later registrations for the same name overwrite — lets plugin
    packages override the built-in adapter if they want.
    """
    if not adapter.name:
        raise ValueError(f"Adapter {adapter!r} missing .name")
    with _lock:
        for i, existing in enumerate(_adapters):
            if existing.name == adapter.name:
                _adapters[i] = adapter
                logger.debug(f"Replaced adapter {adapter.name!r}")
                return
        _adapters.append(adapter)
        logger.debug(f"Registered adapter {adapter.name!r}")


def unregister(name: str) -> None:
    with _lock:
        _adapters[:] = [a for a in _adapters if a.name != name]


def all_adapters() -> List[AgentAdapter]:
    """Snapshot of registered adapters — safe to iterate without the lock."""
    with _lock:
        return list(_adapters)


def get(name: str) -> Optional[AgentAdapter]:
    with _lock:
        for a in _adapters:
            if a.name == name:
                return a
    return None


def detect_all() -> List[DetectResult]:
    """Run :meth:`AgentAdapter.detect` on every registered adapter.

    Errors are caught and logged — one broken adapter never blocks the
    others. Result order matches registration order.
    """
    results: List[DetectResult] = []
    for a in all_adapters():
        try:
            results.append(a.detect())
        except Exception as exc:
            logger.warning(f"Adapter {a.name!r} detect() raised: {exc}")
            results.append(
                DetectResult(
                    name=a.name,
                    display_name=a.display_name or a.name,
                    detected=False,
                    meta={"error": str(exc)},
                )
            )
    return results
