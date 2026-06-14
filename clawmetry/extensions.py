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
# Names of plugin entry points that successfully loaded, in load order.
# A diagnostic-only mirror used by :func:`loaded_plugins` and
# ``GET /api/extensions`` so operators can confirm clawmetry-pro is actually
# wired in without scraping ``pip list``. A plugin that raised during load
# is intentionally NOT recorded here — matches the warning-and-continue
# posture of ``load_plugins`` itself.
_loaded_plugins: List[str] = []


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


def _select_entry_points(group: str):
    """Return entry points for ``group`` across Python versions.

    The ``entry_points(group=...)`` keyword form is Python 3.10+. On 3.9
    ``entry_points()`` returns a dict keyed by group, and passing ``group=``
    raises ``TypeError`` — which previously made ``load_plugins`` silently load
    nothing on 3.9 (still a supported runtime + CI matrix row), so no extension
    package (e.g. clawmetry-pro) ever registered there.
    """
    eps = importlib.metadata.entry_points()
    select = getattr(eps, "select", None)
    if select is not None:  # 3.10+ SelectableGroups / EntryPoints
        return list(select(group=group))
    return list(eps.get(group, []))  # 3.9 dict form


def load_plugins(app=None) -> None:
    """
    Auto-discover and load extension plugins via entry points.
    Called once at dashboard startup.

    Plugins declare themselves in pyproject.toml:
        [project.entry-points."clawmetry.extensions"]
        myplugin = "mypkg.ext:register_all"

    The entry point value is a callable. Backward-compatible signatures:

    * ``register_all()`` (no args) — receives only the event-bus handle via
      :func:`register`. Plugins that only subscribe to events can stay this
      shape; calling them with no args is what shipped pre-2026-05-29.
    * ``register_all(app)`` — receives the Flask app so the plugin can
      register Blueprints on it. Required for plugins that ship routes
      (e.g., ``clawmetry-pro`` ships the runtime-ingest + OTel push
      blueprints).

    Detection is via :func:`inspect.signature`. A plugin that declares an
    ``app`` parameter gets it; one that does not is still called with no
    args. This way old plugins keep working without bumping their pin.
    """
    global _loaded
    if _loaded:
        return
    _loaded = True
    # Reset the diagnostic mirror so a test that flips ``_loaded`` back to
    # False and re-runs the loader doesn't see stale names from the prior pass.
    with _lock:
        _loaded_plugins.clear()

    try:
        eps = _select_entry_points("clawmetry.extensions")
    except Exception:
        return

    import inspect

    for ep in eps:
        try:
            fn = ep.load()
            # Pass ``app`` only when the plugin accepts it. Older plugins
            # with ``register_all()`` (no args) keep working unchanged.
            accepts_app = False
            if app is not None:
                try:
                    sig = inspect.signature(fn)
                    accepts_app = len(sig.parameters) >= 1
                except (TypeError, ValueError):
                    accepts_app = False
            if accepts_app:
                fn(app)
            else:
                fn()
            # Record AFTER a successful invocation so a plugin that raised
            # is reported as not-loaded by ``loaded_plugins`` / /api/extensions.
            name = getattr(ep, "name", "") or ""
            if name:
                with _lock:
                    _loaded_plugins.append(name)
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


def loaded_plugins() -> List[str]:
    """Names of entry-point plugins that loaded successfully in this process.

    The ``clawmetry-pro`` wheel ships as a ``clawmetry.extensions`` entry point;
    this helper lets ``clawmetry status``, ``GET /api/extensions``, and the
    dashboard's diagnostic surface answer "is the paid package actually wired
    in?" without scraping ``pip list`` or importing the package. Returns a
    SHALLOW COPY so callers can't mutate the registry. Names appear in load
    order; entries that raised during load are excluded — matching the
    warning-and-continue posture of :func:`load_plugins`. Never raises.
    """
    with _lock:
        return list(_loaded_plugins)
