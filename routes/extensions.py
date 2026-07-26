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
          "plugins":              ["clawmetry-pro", ...],
          "plugin_count":         1,
          "failed_plugins":       [{"name": "clawmetry-pro", "error": "..."}],
          "failed_plugin_count":  1,
          "probed_plugins":       [{"name": "clawmetry-pro",
                                    "value": "clawmetry_pro.ext:register_all",
                                    "importable": true, "error": null}, ...],
          "probed_plugin_count":  1,
          "events":               ["session.snapshot", ...],
          "handler_counts":       {"session.snapshot": 2, ...}
        }

    ``plugins`` and ``failed_plugins`` are complementary — a given entry
    point appears in exactly one of them per load attempt. The pair answers
    the triage question an operator would otherwise tail daemon logs for:
    *did the paid package try to load, and if so did it succeed?* Only the
    exception's ``str`` is surfaced (no traceback) so paths / secrets from
    frames never leak.

    ``probed_plugins`` is a third, orthogonal view produced by
    :func:`clawmetry.extensions.probe_plugins`: a side-effect-free
    enumeration of every ``clawmetry.extensions`` entry point currently
    visible to ``importlib.metadata``, with each entry's ``value`` string
    and whether ``ep.load()`` (import only — not invocation) succeeds
    RIGHT NOW. Complements the in-process ``plugins`` /
    ``failed_plugins`` mirrors, which reflect the state captured when
    :func:`clawmetry.extensions.load_plugins` last ran at daemon startup.
    The probe answers "would ClawMetry try to load this on the next
    restart, and would the import work?" — the two questions diverge when
    a wheel is installed after startup, when a post-startup dependency
    upgrade broke the import, or when the on-disk marker exists but the
    module can't actually be imported.

    ``failed_plugins`` is derived from an in-memory mirror populated by
    :func:`clawmetry.extensions.load_plugins`. On installs running an older
    ``clawmetry`` where the mirror doesn't exist yet (or if fetching it
    raises), the key falls back to ``[]`` / ``0`` and the rest of the
    envelope still populates — the endpoint never 5xxs.

    ``probed_plugins`` degrades the same way: an older ``clawmetry`` that
    lacks :func:`probe_plugins` reports ``[]`` / ``0`` here while the
    other fields still populate. That way a mixed deploy (new routes,
    old core) never 5xxs the dashboard's diagnostic panel just because a
    younger field is missing on the core side.

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
        # Same defensive posture for the newer :func:`probe_plugins` accessor:
        # an older core wheel that predates it should still let the rest of
        # the envelope populate.
        try:
            probed = [dict(entry) for entry in _ext.probe_plugins()]
        except Exception as exc:
            logger.warning("extensions: probe_plugins introspection failed: %s", exc)
            probed = []
        events = list(_ext.registered_events())
        handler_counts = {evt: _ext.handler_count(evt) for evt in events}
        return jsonify({
            "plugins": plugins,
            "plugin_count": len(plugins),
            "failed_plugins": failed,
            "failed_plugin_count": len(failed),
            "probed_plugins": probed,
            "probed_plugin_count": len(probed),
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
            "probed_plugins": [],
            "probed_plugin_count": 0,
            "events": [],
            "handler_counts": {},
        })
