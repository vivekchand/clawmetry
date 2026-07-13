"""
routes/extensions.py — diagnostic introspection for the entry-point plugin loader.

``clawmetry/extensions.py`` discovers external packages via the
``clawmetry.extensions`` entry-point group. The closed-source ``clawmetry-pro``
wheel ships its runtime adapters that way, so operators frequently need to
answer "did the paid package actually load on this node?" — currently the only
way is to scrape daemon logs or run ``pip list``.

This module exposes a tiny, always-Free, never-raise endpoint that surfaces
the in-memory state of the loader so the dashboard, ``clawmetry status``, and
shell wrappers can read it directly. No entitlement check is required: knowing
which plugins are loaded is diagnostic, not gated. Pure read.

Blueprint: ``bp_extensions``.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify

logger = logging.getLogger("clawmetry.routes.extensions")

bp_extensions = Blueprint("extensions", __name__)


@bp_extensions.route("/api/extensions", methods=["GET"])
def api_extensions():
    """Return loaded entry-point plugins + registered event hooks.

    Response shape::

        {
          "plugins":             ["clawmetry-pro", ...],
          "plugin_count":        1,
          "failed_plugins":      [{"name": "clawmetry-pro", "error": "..."}],
          "failed_plugin_count": 1,
          "events":              ["session.snapshot", ...],
          "handler_counts":      {"session.snapshot": 2, ...}
        }

    ``plugins`` and ``failed_plugins`` are complementary — a given entry
    point appears in exactly one of them per load attempt. The pair answers
    the triage question an operator would otherwise tail daemon logs for:
    *did the paid package try to load, and if so did it succeed?* Only the
    exception's ``str`` is surfaced (no traceback) so paths / secrets from
    frames never leak.

    ``failed_plugins`` is derived from an in-memory mirror populated by
    :func:`clawmetry.extensions.load_plugins`. On installs running an older
    ``clawmetry`` where the mirror doesn't exist yet (or if fetching it
    raises), the key falls back to ``[]`` / ``0`` and the rest of the
    envelope still populates — the endpoint never 5xxs.

    Never raises and never returns 5xx — any introspection failure resolves to
    an empty shape so the dashboard's diagnostic panel always has something
    safe to render.
    """
    try:
        from clawmetry import extensions as _ext

        plugins = list(_ext.loaded_plugins())
        # Older ``clawmetry`` may not ship :func:`failed_plugins` yet; degrade
        # to an empty list instead of 5xx'ing the whole envelope so a mixed
        # deploy (new routes, old core) still surfaces the loaded-plugin
        # side.
        try:
            failed = [dict(entry) for entry in _ext.failed_plugins()]
        except Exception as exc:
            logger.warning("extensions: failed_plugins introspection failed: %s", exc)
            failed = []
        events = list(_ext.registered_events())
        handler_counts = {evt: _ext.handler_count(evt) for evt in events}
        return jsonify({
            "plugins": plugins,
            "plugin_count": len(plugins),
            "failed_plugins": failed,
            "failed_plugin_count": len(failed),
            "events": events,
            "handler_counts": handler_counts,
        })
    except Exception as exc:
        logger.warning("extensions: introspection failed: %s", exc)
        return jsonify({
            "plugins": [],
            "plugin_count": 0,
            "failed_plugins": [],
            "failed_plugin_count": 0,
            "events": [],
            "handler_counts": {},
        })
