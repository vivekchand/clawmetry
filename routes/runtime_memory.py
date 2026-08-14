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
    list_files,
    list_runtimes,
    read_runtime_file,
)

try:
    # ``allows_runtime`` returns True for OpenClaw/NemoClaw (free) and
    # for any paid runtime covered by the resolved entitlement. In grace
    # mode it is intentionally permissive; the OSS enforcement layer at
    # request time is what turns a denial into HTTP 402.
    from clawmetry.entitlements import (
        FREE_RUNTIMES,
        get_entitlement,
    )
except Exception:  # pragma: no cover — entitlements is core; only fails in tests
    FREE_RUNTIMES = frozenset({"openclaw", "nemoclaw"})

    def get_entitlement(*_a, **_k):
        return None


bp_runtime_memory = Blueprint("runtime_memory", __name__)


def _runtime_is_locked(runtime_id: str) -> bool:
    """True when this runtime needs a paid entitlement the user lacks.

    Free runtimes are never locked. For paid runtimes, ``allows_runtime``
    on the resolved entitlement is authoritative (it already honours
    grace mode). Any exception (entitlement resolution failure) falls
    open — we prefer showing content on the local dashboard over a
    silent lock-out from a resolver hiccup; the actual read endpoint
    still returns 402 if the resolver later hardens.
    """
    if runtime_id in FREE_RUNTIMES:
        return False
    try:
        ent = get_entitlement()
        return not bool(ent.allows_runtime(runtime_id))
    except Exception:
        return False


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


@bp_runtime_memory.route("/api/runtimes/<runtime_id>/files")
def api_runtime_files(runtime_id: str):
    """List every file under one runtime, grouped by root.

    Query params:
      - category: optional filter (memory | skills | commands | agents | hooks)

    Returns HTTP 402 ``upgrade_required`` when the runtime is a paid
    runtime and the resolved entitlement does not cover it. This is the
    OSS conversion moment prescribed by ``FLYWHEEL.md`` §1b — never
    silently disable, always surface the upgrade CTA.
    """
    if _runtime_is_locked(runtime_id):
        return jsonify({
            "error": "upgrade_required",
            "runtime": runtime_id,
            "reason": "paid_runtime_not_entitled",
        }), 402
    category = (request.args.get("category") or "").strip() or None
    if category and category not in CATEGORIES:
        return jsonify({"error": "invalid category"}), 400
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
