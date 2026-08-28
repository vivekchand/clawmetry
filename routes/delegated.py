"""Connect a Cursor account from the dashboard, and read delegated usage.

The opt-in for pricing work a runtime handed to Cursor cloud agents (see
``clawmetry.delegated_usage``). This exists as a UI surface because the CLI-only
version was a bad funnel: the people who benefit are looking at a Cursor or
Grok Bot runtime view when the question "what did that delegated work cost"
occurs to them, and telling them to go and run a terminal command loses most
of them.

Why a browser form is an acceptable home for a credential HERE:

* The dashboard is the operator's own machine on loopback, and the key is their
  own Cursor key. This is the same trust boundary as typing it into a terminal.
* Every state-changing ``/api/*`` request already passes the app-wide
  cross-origin write guard, so another page cannot post a key or read status
  on the operator's behalf.
* **The key is write-only over HTTP.** No endpoint here returns it, and there
  is deliberately no "show key" affordance. Status returns the masked form and
  nothing else, so a compromised page that could read this API still learns
  four characters.
* Storage stays exactly where the CLI put it -- 0600, outside the DuckDB store,
  and never part of a synchronised snapshot.

The hosted dashboard is read-only over a decrypted snapshot and has no local
key file, so these endpoints report ``supported: false`` there rather than
offering a control that cannot work.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.delegated")

bp_delegated = Blueprint("delegated", __name__)


def _local_key_store_available() -> bool:
    """False in the hosted dashboard, which has no local filesystem to write."""
    try:
        import clawmetry.cursor_connector  # noqa: F401
        return True
    except Exception:
        return False


@bp_delegated.route("/api/cursor/status")
def api_cursor_status():
    """Connection state for the runtime views. Never returns the key."""
    if not _local_key_store_available():
        return jsonify({"supported": False, "connected": False})
    from clawmetry import cursor_connector as cc
    from clawmetry.delegated_usage import get_store

    try:
        observed = sorted(get_store().observed())
    except Exception:
        observed = []
    return jsonify({
        "supported": True,
        "connected": cc.is_connected(),
        # The masked form is the ONLY key-derived value this API emits.
        "maskedKey": cc.masked_key(),
        "delegatedAgents": len(observed),
        "endpoint": cc.API_BASE,
        # Said plainly so the UI can set expectations rather than let a user
        # discover the gate by getting nothing back.
        "requiresPaidCursorPlan": True,
    })


@bp_delegated.route("/api/cursor/connect", methods=["POST"])
def api_cursor_connect():
    """Store the operator's Cursor key. Write-only: the key is never returned."""
    if not _local_key_store_available():
        return jsonify({"error": "not_supported_here"}), 400
    from clawmetry import cursor_connector as cc

    payload = request.get_json(silent=True) or {}
    if not str(payload.get("apiKey") or "").strip():
        return jsonify({"error": "missing_api_key"}), 400
    try:
        # save_key_from_body never returns the raw secret; the handler never
        # binds it under a local name (same structural guarantee as the CLI).
        masked = cc.save_key_from_body(payload)
    except Exception:
        # No exception text: this path handles a credential and an exception
        # string is an uncontrolled channel.
        logger.warning("cursor connect: could not store key")
        return jsonify({"error": "could_not_store"}), 500
    return jsonify({"connected": True, "maskedKey": masked})


@bp_delegated.route("/api/cursor/disconnect", methods=["POST"])
def api_cursor_disconnect():
    if not _local_key_store_available():
        return jsonify({"error": "not_supported_here"}), 400
    from clawmetry import cursor_connector as cc

    return jsonify({"connected": False, "removed": bool(cc.forget_key())})


@bp_delegated.route("/api/cursor/sync", methods=["POST"])
def api_cursor_sync():
    """Refresh usage for locally-observed agents. Summary carries no key."""
    if not _local_key_store_available():
        return jsonify({"error": "not_supported_here"}), 400
    from clawmetry import cursor_connector as cc

    try:
        return jsonify(cc.sync())
    except Exception:
        logger.warning("cursor sync failed", exc_info=False)
        return jsonify({"error": "sync_failed"}), 500


@bp_delegated.route("/api/delegated-usage")
def api_delegated_usage():
    """Delegated rollup for the agent ids passed in ``agents`` (comma-separated).

    Bounded by the same rule as ingest: an id the local transcripts never named
    is not in the store and therefore rolls up to nothing.
    """
    from clawmetry.delegated_usage import get_store

    raw = (request.args.get("agents") or "").strip()
    agents = [a.strip() for a in raw.split(",") if a.strip()]
    if not agents:
        return jsonify({"vendor": "cursor", "agentsSeen": 0, "costUsd": None,
                        "costStatus": "unavailable", "totalTokens": 0})
    try:
        return jsonify(get_store().rollup(agents))
    except Exception:
        logger.debug("delegated rollup failed", exc_info=True)
        return jsonify({"error": "rollup_failed"}), 500
