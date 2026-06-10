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
          "plugins":        ["clawmetry-pro", ...],
          "plugin_count":   1,
          "events":         ["session.snapshot", ...],
          "handler_counts": {"session.snapshot": 2, ...}
        }

    Never raises and never returns 5xx — any introspection failure resolves to
    an empty shape so the dashboard's diagnostic panel always has something
    safe to render.
    """
    try:
        from clawmetry import extensions as _ext

        plugins = list(_ext.loaded_plugins())
        events = list(_ext.registered_events())
        handler_counts = {evt: _ext.handler_count(evt) for evt in events}
        return jsonify({
            "plugins": plugins,
            "plugin_count": len(plugins),
            "events": events,
            "handler_counts": handler_counts,
        })
    except Exception as exc:
        logger.warning("extensions: introspection failed: %s", exc)
        return jsonify({
            "plugins": [],
            "plugin_count": 0,
            "events": [],
            "handler_counts": {},
        })
