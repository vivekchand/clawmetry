"""
routes/rules.py — Rule Builder backend endpoints.

Phase 1 of issue #1517. Stores rule definitions as JSON files at
``~/.clawmetry/rules/<id>.json`` and exposes a 30-day backtest against
the local DuckDB event store via the existing daemon proxy.

Routes:
  GET    /api/v2/rules                — list saved rules
  GET    /api/v2/rules/<rid>          — fetch one rule
  PUT    /api/v2/rules/<rid>          — create / update a rule
  DELETE /api/v2/rules/<rid>          — delete a rule
  POST   /api/v2/rules/<rid>/backtest — count + sample matching events
"""

from __future__ import annotations

import json
import os
import pathlib
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

bp_rules = Blueprint("rules", __name__)

_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,80}$")


def _rules_dir() -> pathlib.Path:
    base = os.environ.get("CLAWMETRY_RULES_DIR") or os.path.expanduser(
        "~/.clawmetry/rules"
    )
    p = pathlib.Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe_id(rid: str) -> bool:
    return bool(_ID_RE.match(rid))


def _load_rule(rid: str) -> dict | None:
    path = _rules_dir() / f"{rid}.json"
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _store_via_daemon_or_direct(method_name: str, **kwargs):
    """Daemon HTTP proxy first, then direct DuckDB read-only fallback."""
    try:
        from routes.local_query import local_store_via_daemon

        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store

        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


@bp_rules.route("/api/v2/rules", methods=["GET"])
def list_rules():
    """Return summary of all saved rules."""
    try:
        items = []
        for fp in sorted(_rules_dir().glob("*.json")):
            try:
                rule = json.loads(fp.read_text())
                items.append(
                    {
                        "id": fp.stem,
                        "title": rule.get("title", fp.stem),
                        "enabled": rule.get("enabled", True),
                        "updated_at": rule.get("updated_at"),
                    }
                )
            except Exception:
                continue
        return jsonify({"rules": items})
    except Exception as exc:
        return jsonify({"rules": [], "error": str(exc)[:300]})


@bp_rules.route("/api/v2/rules/<rid>", methods=["GET"])
def get_rule(rid: str):
    """Fetch a single rule by id."""
    if not _safe_id(rid):
        return jsonify({"error": "invalid rule id"}), 400
    rule = _load_rule(rid)
    if rule is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(rule)


@bp_rules.route("/api/v2/rules/<rid>", methods=["PUT"])
def put_rule(rid: str):
    """Create or replace a rule. Body must be a JSON object."""
    if not _safe_id(rid):
        return jsonify({"error": "invalid rule id"}), 400
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "body must be a JSON object"}), 400
    body["id"] = rid
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = _rules_dir() / f"{rid}.json"
    try:
        path.write_text(json.dumps(body, ensure_ascii=False, indent=2))
    except OSError as exc:
        return jsonify({"error": str(exc)[:300]}), 500
    return jsonify({"ok": True, "id": rid, "updated_at": body["updated_at"]})


@bp_rules.route("/api/v2/rules/<rid>", methods=["DELETE"])
def delete_rule(rid: str):
    """Delete a saved rule."""
    if not _safe_id(rid):
        return jsonify({"error": "invalid rule id"}), 400
    path = _rules_dir() / f"{rid}.json"
    try:
        path.unlink()
    except FileNotFoundError:
        return jsonify({"error": "not found"}), 404
    except OSError as exc:
        return jsonify({"error": str(exc)[:300]}), 500
    return jsonify({"ok": True, "id": rid})


@bp_rules.route("/api/v2/rules/<rid>/backtest", methods=["POST"])
def backtest_rule(rid: str):
    """Count and sample events matching this rule over N days.

    Query param: ``days`` (int, 1–90, default 30).
    Reads ``rule.event_type`` (or ``rule.filter.event_type``) to filter events.
    Uses ``query_events`` via the daemon proxy so the dashboard process never
    opens DuckDB writable.
    """
    if not _safe_id(rid):
        return jsonify({"error": "invalid rule id"}), 400
    rule = _load_rule(rid)
    if rule is None:
        return jsonify({"error": "not found"}), 404

    try:
        days = max(1, min(90, int(request.args.get("days", 30))))
    except (TypeError, ValueError):
        days = 30

    event_type = rule.get("event_type") or (
        rule.get("filter") or {}
    ).get("event_type")
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    rows = (
        _store_via_daemon_or_direct(
            "query_events",
            event_type=event_type or None,
            since=since,
            limit=200,
        )
        or []
    )

    return jsonify(
        {
            "rule_id": rid,
            "window_days": days,
            "matched": len(rows),
            "sampled": rows[:10],
        }
    )
