"""
ClawMetry extension/plugin system.

Allows external packages (e.g. clawmetry-cloud) to hook into ClawMetry events
without modifying this codebase.

Usage (in an external package's pyproject.toml):
    [project.entry-points."clawmetry.extensions"]
    mycloud = "mypkg.extensions:register_all"

Usage (in dashboard.py):
    from clawmetry.extensions import emit
    emit("session.snapshot", {"session_id": sid, "tokens": n})

Registration:
    from clawmetry.extensions import register
    register("session.snapshot", my_handler)
"""
from __future__ import annotations

import importlib.metadata
import logging
import threading
from typing import Any, Callable, Dict, List

logger = logging.getLogger("clawmetry.extensions")

_registry: Dict[str, List[Callable]] = {}
_lock = threading.Lock()
_loaded = False


def register(event: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """Register a handler for a named event."""
    with _lock:
        _registry.setdefault(event, []).append(handler)
        logger.debug(f"Registered handler {handler.__name__!r} for event {event!r}")


def unregister(event: str, handler: Callable) -> None:
    """Remove a specific handler for an event."""
    with _lock:
        if event in _registry:
            try:
                _registry[event].remove(handler)
            except ValueError:
                pass


def emit(event: str, payload: Dict[str, Any] | None = None) -> None:
    """
    Fire an event. All registered handlers are called synchronously.
    Exceptions in handlers are caught and logged — never propagated to caller.
    """
    if payload is None:
        payload = {}
    with _lock:
        handlers = list(_registry.get(event, []))
    for handler in handlers:
        try:
            handler(payload)
        except Exception as exc:
            logger.warning(
                f"Extension handler {handler.__name__!r} raised on event {event!r}: {exc}"
            )


def load_plugins() -> None:
    """
    Auto-discover and load extension plugins via entry points.
    Called once at dashboard startup.

    Plugins declare themselves in pyproject.toml:
        [project.entry-points."clawmetry.extensions"]
        myplugin = "mypkg.ext:register_all"

    The entry point value must be a callable that takes no arguments
    and calls register() for each event it handles.
    """
    global _loaded
    if _loaded:
        return
    _loaded = True

    try:
        eps = importlib.metadata.entry_points(group="clawmetry.extensions")
    except Exception:
        return

    for ep in eps:
        try:
            fn = ep.load()
            fn()
            logger.info(f"Loaded ClawMetry extension plugin: {ep.name!r}")
        except Exception as exc:
            logger.warning(f"Failed to load extension plugin {ep.name!r}: {exc}")


def registered_events() -> List[str]:
    """Return list of events that have at least one handler registered."""
    with _lock:
        return [k for k, v in _registry.items() if v]


def handler_count(event: str) -> int:
    """Return number of handlers registered for an event."""
    with _lock:
        return len(_registry.get(event, []))
