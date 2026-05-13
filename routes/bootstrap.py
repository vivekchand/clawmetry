"""routes/bootstrap.py — "First Contact" bootstrap artifact endpoints.

Exposes the BOOTSTRAP.md snapshots captured by ``clawmetry/sync.py``
(:func:`capture_bootstrap_if_present`) over HTTP. OpenClaw's BOOTSTRAP.md
runs once at first startup to negotiate agent identity, then SELF-DELETES.
The daemon captures it before it disappears; these routes surface the
read-only artifact to the dashboard / cloud UI.

  GET /api/bootstrap                — list captured snapshots for this node
  GET /api/bootstrap/<agent_id>     — single snapshot (newest) + linked first-session ref

Both endpoints return HTTP 404 when no bootstrap has been captured yet
(fresh install, OpenClaw not running, or workspace already past first-contact
when ClawMetry was installed). Zero coupling to ``dashboard.py``; talks
directly to ``clawmetry.local_store``.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

bp_bootstrap = Blueprint("bootstrap", __name__)


def _store():
    """Return a read-only LocalStore handle, or None when unavailable.

    The daemon owns the writer lock; the dashboard process opens a separate
    RO handle on the same DuckDB file. Falls back to ``None`` cleanly if
    ``duckdb`` isn't installed or the store file doesn't exist yet (fresh
    install — no bootstrap to surface anyway)."""
    try:
        from clawmetry import local_store
        return local_store.get_store(read_only=True)
    except Exception:
        return None


def _node_id_filter() -> str | None:
    """Scope queries to the current node when possible.

    Reads the node_id from the on-disk sync config (the same file the daemon
    consults). Returns None when the config is missing or unreadable — the
    query helper treats None as "no scope" so we still return the full table
    in that case (acceptable for OSS single-node installs)."""
    try:
        from clawmetry import sync
        cfg = sync.load_config()
        nid = cfg.get("node_id")
        return str(nid) if nid else None
    except Exception:
        return None


def _row_to_summary(row: dict) -> dict:
    """Strip the heavy `content` field for list responses — clients can fetch
    one snapshot at a time for the full text."""
    return {
        "node_id": row.get("node_id"),
        "agent_id": row.get("agent_id"),
        "captured_at": row.get("captured_at"),
        "file_mtime": row.get("file_mtime"),
        "content_sha256": row.get("content_sha256"),
        "first_session_id": row.get("first_session_id"),
        "size_bytes": row.get("size_bytes"),
        "source_path": row.get("source_path"),
    }


@bp_bootstrap.route("/api/bootstrap")
def api_bootstrap_list():
    """List captured BOOTSTRAP.md snapshots for the current node.

    Returns 404 when no snapshots exist — the absence of an artifact is
    a meaningful 404 (vs. an empty list) so clients can branch on it
    without parsing the body."""
    try:
        limit = max(1, min(200, int(request.args.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50
    store = _store()
    if store is None:
        return jsonify({"error": "local store unavailable"}), 503
    node_id = _node_id_filter()
    try:
        rows = store.query_bootstrap_archive(node_id=node_id, limit=limit)
    except Exception as exc:
        return jsonify({"error": f"query failed: {exc}"}), 500
    if not rows:
        return jsonify({
            "error": "no bootstrap snapshots captured yet",
            "node_id": node_id,
            "snapshots": [],
        }), 404
    return jsonify({
        "node_id": node_id,
        "snapshots": [_row_to_summary(r) for r in rows],
        "_source": "local_store",
    })


@bp_bootstrap.route("/api/bootstrap/<agent_id>")
def api_bootstrap_detail(agent_id: str):
    """Return the newest BOOTSTRAP.md snapshot for ``agent_id`` on this node.

    Returns 404 when no snapshot exists for that agent. Includes the full
    `content` field (BOOTSTRAP.md is tiny — typically <8 KB)."""
    store = _store()
    if store is None:
        return jsonify({"error": "local store unavailable"}), 503
    node_id = _node_id_filter()
    try:
        rows = store.query_bootstrap_archive(
            node_id=node_id, agent_id=agent_id, limit=1,
        )
    except Exception as exc:
        return jsonify({"error": f"query failed: {exc}"}), 500
    if not rows:
        return jsonify({
            "error": f"no bootstrap snapshot for agent_id={agent_id!r}",
            "agent_id": agent_id,
            "node_id": node_id,
        }), 404
    row = rows[0]
    return jsonify({
        "snapshot": row,
        "first_session_id": row.get("first_session_id"),
        "_source": "local_store",
    })
