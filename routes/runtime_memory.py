"""routes/runtime_memory.py — Per-runtime Memory & Skills browser API.

Three endpoints backing the file-browser layout in the Memory and Skills
tabs. Everything is read-only (the browser is a viewer, not an editor for
non-OpenClaw runtimes; the OpenClaw-owned Memory tab keeps its own write
endpoint at ``/api/file``). Traversal-safety is enforced inside
:mod:`clawmetry.runtime_memory` — this module is a thin Flask veneer.

  GET /api/runtimes/memory-catalog
      List every catalogued runtime with per-category counts + resolved
      root paths. Powers the runtime chip bar at the top of the tab.

  GET /api/runtimes/<runtime_id>/files?category=<memory|skills|...>
      List every file the runtime exposes, grouped by root.

  GET /api/runtimes/<runtime_id>/file?root=<root>&path=<rel>
      Read one file from within a registered root. ``root`` must appear
      verbatim in the catalog's expanded roots list; ``path`` is relative
      to it.

None of these are gated — memory/skills catalog is universal metadata that
every plan sees. Only the OpenClaw-specific write endpoint (still in
``routes/infra.py``) enforces workspace-write policy.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from clawmetry.runtime_memory import (
    CATEGORIES,
    list_files,
    list_runtimes,
    read_runtime_file,
)


bp_runtime_memory = Blueprint("runtime_memory", __name__)


@bp_runtime_memory.route("/api/runtimes/memory-catalog")
def api_runtime_memory_catalog():
    """List every runtime with counts. Cheap — safe to poll on tab open."""
    return jsonify({
        "categories": list(CATEGORIES),
        "runtimes": list_runtimes(),
    })


@bp_runtime_memory.route("/api/runtimes/<runtime_id>/files")
def api_runtime_files(runtime_id: str):
    """List every file under one runtime, grouped by root.

    Query params:
      - category: optional filter (memory | skills | commands | agents | hooks)
    """
    category = (request.args.get("category") or "").strip() or None
    if category and category not in CATEGORIES:
        return jsonify({"error": "invalid category"}), 400
    payload = list_files(runtime_id, category=category)
    if payload.get("error") == "unknown_runtime":
        return jsonify(payload), 404
    return jsonify(payload)


@bp_runtime_memory.route("/api/runtimes/<runtime_id>/file")
def api_runtime_file(runtime_id: str):
    """Read one file from one registered root of a runtime."""
    root = request.args.get("root", "")
    path = request.args.get("path", "")
    if not root:
        return jsonify({"error": "root is required"}), 400
    result = read_runtime_file(runtime_id, root, path)
    if not result.get("ok"):
        return jsonify({"error": result.get("error")}), int(result.get("status", 500))
    return jsonify(result)
