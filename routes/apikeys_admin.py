"""routes/apikeys_admin.py -- create, list and revoke the node's API keys.

Requirement: "Build your own UI: a keyed, scoped read API for custom
dashboards" (64c10afd-038d-4fde-9c55-ddca80aaff1e), blueprint
0ea7523c-12b5-4033-84ea-bf1f46e20d70, "API Surface" -> "Key management".

    GET    /api/apikeys            this node's keys + the scope catalogue
    POST   /api/apikeys            mint one; the secret is in the response
    DELETE /api/apikeys/<key_id>   revoke one

These MINT and REVOKE credentials for ``routes/public_api.py``, which is the
cross-origin surface those credentials open. That relationship is the whole
reason they live apart:

* **This module is behind the dashboard's own gate.** ``dashboard.py``'s
  ``_cross_origin_write_blocked`` refuses a cross-origin POST/DELETE to any
  ``/api/*`` path, and ``public_api._add_cors`` is pinned to ``/api/q/`` so no
  CORS header ever reaches these routes. A page holding a read key can
  therefore never list the node's keys, and never issue itself a better one.
* **It is its own blueprint, not a few functions on ``bp_security``.** Both
  placements are equally safe, since the guards above are path-based rather
  than blueprint-based. This one is legible: credential management is a
  distinct concern from the security tab's scanners, and a reader (human or
  tool) sees the whole surface in one short file instead of at 97% of a
  3,000-line module.

Nothing here reads agent data. The keys it manages are read-only by
construction; see ``clawmetry/apikeys.py`` for what they can and cannot do.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.apikeys_admin")

bp_apikeys_admin = Blueprint("apikeys_admin", __name__)


@bp_apikeys_admin.route("/api/apikeys", methods=["GET"])
def api_keys_list():
    """This node's API keys, plus the scope catalogue the UI renders.

    Secrets are never included: only a SHA-256 is stored, and even that is
    stripped by ``apikeys.list_keys``.
    """
    from clawmetry import apikeys as _ak
    try:
        return jsonify({
            "ok": True,
            "keys": _ak.list_keys(include_revoked=True),
            "scopes": _ak.scope_catalogue(),
            "summary": _ak.store_summary(),
        })
    except Exception as exc:
        logger.warning("apikeys list failed: %s", exc)
        return jsonify({
            "ok": False,
            "keys": [],
            "scopes": [],
            "error": "ClawMetry could not read its key file. Check that "
                     "~/.clawmetry is readable by you.",
        }), 200


@bp_apikeys_admin.route("/api/apikeys", methods=["POST"])
def api_keys_create():
    """Mint a key. The secret is in this response and nowhere else, ever."""
    from clawmetry import apikeys as _ak
    body = request.get_json(silent=True) or {}
    origins = body.get("origins") or []
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.replace(",", " ").split() if o.strip()]
    scopes = body.get("scopes") or []
    if isinstance(scopes, str):
        scopes = [s.strip() for s in scopes.replace(",", " ").split() if s.strip()]
    browser = bool(body.get("browser", True))
    if browser and not origins:
        return jsonify({
            "ok": False,
            "error": "Name the site that will use this key, for example "
                     "http://localhost:3000. There is no wildcard: any page "
                     "in any tab can already reach this machine, and the "
                     "origin list is what stops it reading the answer.",
        }), 400
    try:
        record, plaintext = _ak.create(
            body.get("name") or "",
            scopes,
            [] if not browser else origins,
            note=body.get("note") or "",
        )
    except _ak.ApiKeyError as exc:
        # The sentence comes from apikeys.REFUSAL_REASONS, keyed by the
        # refusal code, NOT from str(exc). The CLI does print the exception
        # (it names the offending value, which is worth more than it costs
        # in a terminal); an HTTP response must not carry exception-derived
        # text to a caller who may not be the operator.
        return jsonify({
            "ok": False,
            "reason": exc.reason,
            "error": _ak.message_for(exc.reason),
        }), 400
    except Exception as exc:
        logger.warning("apikeys create failed: %s", exc)
        return jsonify({
            "ok": False,
            "error": "ClawMetry could not write its key file. Check that "
                     "~/.clawmetry is writable by you.",
        }), 500
    return jsonify({
        "ok": True,
        "key": plaintext,
        "record": {k: v for k, v in record.items() if k != "hash"},
    })


@bp_apikeys_admin.route("/api/apikeys/<key_id>", methods=["DELETE"])
def api_keys_revoke(key_id: str):
    """Revoke a key. Takes effect on that key's next request."""
    from clawmetry import apikeys as _ak
    try:
        ok = _ak.revoke(key_id)
    except Exception as exc:
        logger.warning("apikeys revoke failed: %s", exc)
        return jsonify({
            "ok": False,
            "error": "ClawMetry could not write its key file. Check that "
                     "~/.clawmetry is writable by you.",
        }), 500
    if not ok:
        return jsonify({
            "ok": False,
            "error": "There is no active key with that id on this machine.",
        }), 404
    return jsonify({"ok": True, "id": key_id})
