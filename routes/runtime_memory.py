"""routes/runtime_memory.py — Per-runtime Memory & Skills browser API.

Three endpoints backing the file-browser layout in the Memory and Skills
tabs. Everything is read-only (the browser is a viewer, not an editor for
non-OpenClaw runtimes; the OpenClaw-owned Memory tab keeps its own write
endpoint at ``/api/file``). Traversal-safety is enforced inside
:mod:`clawmetry.runtime_memory` — this module is a thin Flask veneer.

  GET /api/runtimes/memory-catalog
      List every catalogued runtime with per-category counts + resolved
      root paths, tagged with ``locked: bool``. Powers the runtime chip
      bar at the top of the Memory / Skills tabs. Always returns every
      runtime (locked or not) so the UI can render an honest upgrade CTA
      without pretending the runtime is absent (per the ERS-001.3
      "don't hide paid adapters" acceptance criterion).

  GET /api/runtimes/<runtime_id>/files?category=<memory|skills|...>
      List every file the runtime exposes, grouped by root. Gated by
      :func:`clawmetry.entitlements.allows_runtime`. Free runtimes
      (OpenClaw, NemoClaw) are always readable; paid runtimes return
      HTTP 402 ``upgrade_required`` when the resolved entitlement does
      not cover them (grace still permissive — see the entitlements
      module).

      ``runtime_id`` may be the literal ``all``, which sweeps every
      entitled runtime and returns only groups that exist on disk, each
      tagged with its owning ``runtime`` / ``runtime_label``. This is the
      DEFAULT scope of the Memory and Skills tabs (the global runtime
      switcher's "All runtimes"), so it never 402s — a locked runtime is
      left out of the sweep instead, because paywalling the aggregate
      would also paywall the free runtimes the user IS entitled to. The
      conversion moment stays on an explicit per-runtime selection.

      ``all`` is a list-only sentinel: read a file back through the
      ``runtime`` its group carries, never through ``all``.

  GET /api/runtimes/<runtime_id>/file?root=<root>&path=<rel>
      Read one file from within a registered root. Same entitlement gate
      as ``/files``.

Design note: this module is the source of truth for **where on-disk
memory / skills / commands / agents / hooks files live** for every
supported runtime. It complements — and does not replace — the
``clawmetry.adapters.AgentAdapter`` layer, which normalises live
Session / Event data. The two concerns are intentionally separate: an
agent adapter can be un-shipped for a runtime while the user's
filesystem still holds that runtime's memory files, so the file browser
must resolve independently.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from clawmetry.runtime_memory import (
    CATEGORIES,
    list_all_files,
    list_files,
    list_runtimes,
    parse_categories,
    read_runtime_file,
    # THE paywall predicate. It lives in clawmetry/runtime_memory.py rather
    # than here because the sync daemon needs the same answer twice — once to
    # decide what it may ingest, once to decide what it may ship — and a copy
    # per caller is how the daemon ended up pushing files this route 402s on.
    runtime_is_locked as _runtime_is_locked,
)

bp_runtime_memory = Blueprint("runtime_memory", __name__)


@bp_runtime_memory.route("/api/runtimes/memory-catalog")
def api_runtime_memory_catalog():
    """List every runtime with counts + a ``locked`` flag.

    Cheap — safe to poll on tab open. Always returns every catalogued
    runtime (locked or not) so the UI can render an honest upgrade CTA
    on paid runtimes without pretending they don't exist (matches the
    ERS-001.3 acceptance criterion: "when an extension is absent or not
    entitled, do not present it as available" — we surface the label
    but tag it locked, so the user sees the option and the upsell).
    """
    runtimes = list_runtimes()
    for rt in runtimes:
        rt["locked"] = _runtime_is_locked(rt["id"])
    return jsonify({
        "categories": list(CATEGORIES),
        "runtimes": runtimes,
    })


@bp_runtime_memory.route("/api/runtimes/all/files")
def api_runtime_files_all():
    """Aggregate every entitled runtime's files for one category.

    A dedicated rule rather than a magic value inside
    :func:`api_runtime_files` — Werkzeug matches this static rule ahead of
    the ``<runtime_id>`` converter either way, and a grep for the URL the
    frontend actually calls should land on a handler.

    Never returns 402. This is the DEFAULT scope of the Memory and Skills
    tabs, so paywalling it because the user also happens to have an
    unentitled runtime installed would paywall the free runtimes they ARE
    entitled to. Locked runtimes are simply left out of the sweep; the
    conversion moment stays on an explicit per-runtime selection, which
    still 402s below.
    """
    category = (request.args.get("category") or "").strip() or None
    if category and not parse_categories(category):
        return jsonify({"error": "invalid category"}), 400
    allowed = [rt["id"] for rt in list_runtimes()
               if not _runtime_is_locked(rt["id"])]
    return jsonify(list_all_files(category=category, allowed=allowed))


@bp_runtime_memory.route("/api/runtimes/<runtime_id>/files")
def api_runtime_files(runtime_id: str):
    """List every file under one runtime, grouped by root.

    Query params:
      - category: optional filter (memory | skills | commands | agents | hooks)

    ``runtime_id`` may be the literal ``all``, which aggregates every
    runtime the caller is entitled to. That is the default scope of the
    Memory / Skills tabs (the global runtime switcher's "All runtimes"),
    so it must never 402 — locked runtimes are simply left out of the
    sweep rather than turning the whole page into an upsell.

    Returns HTTP 402 ``upgrade_required`` when the runtime is a paid
    runtime and the resolved entitlement does not cover it. This is the
    OSS conversion moment prescribed by ``FLYWHEEL.md`` §1b — never
    silently disable, always surface the upgrade CTA.
    """
    category = (request.args.get("category") or "").strip() or None
    if category and not parse_categories(category):
        return jsonify({"error": "invalid category"}), 400
    if runtime_id == "all":
        # Defensive: the static rule above normally wins the match. Kept so
        # a caller that reaches here (a blueprint mounted under a prefix, a
        # hand-built url_for) still gets the aggregate rather than a 404.
        return api_runtime_files_all()
    if _runtime_is_locked(runtime_id):
        return jsonify({
            "error": "upgrade_required",
            "runtime": runtime_id,
            "reason": "paid_runtime_not_entitled",
        }), 402
    payload = list_files(runtime_id, category=category)
    if payload.get("error") == "unknown_runtime":
        return jsonify(payload), 404
    return jsonify(payload)


@bp_runtime_memory.route("/api/runtimes/<runtime_id>/file")
def api_runtime_file(runtime_id: str):
    """Read one file from one registered root of a runtime.

    Same entitlement gate as ``/files``: paid runtimes return HTTP 402
    when the resolved entitlement does not cover them.
    """
    if _runtime_is_locked(runtime_id):
        return jsonify({
            "error": "upgrade_required",
            "runtime": runtime_id,
            "reason": "paid_runtime_not_entitled",
        }), 402
    root = request.args.get("root", "")
    path = request.args.get("path", "")
    if not root:
        return jsonify({"error": "root is required"}), 400
    result = read_runtime_file(runtime_id, root, path)
    if not result.get("ok"):
        return jsonify({"error": result.get("error")}), int(result.get("status", 500))
    return jsonify(result)
