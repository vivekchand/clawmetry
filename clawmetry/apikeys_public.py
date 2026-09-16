"""clawmetry/apikeys_public.py -- read-side helpers for the keyed public API.

Factored out of apikeys.py so Drift Bot can find these symbols in a short
file (it reads only the head of large files; functions buried deep are
reported as "not defined" forever -- see CLAUDE.md).

All four functions use lazy imports to break the circular dependency on
clawmetry.apikeys private helpers.
"""

from __future__ import annotations

from typing import Any


def all_live_origins() -> list:
    """All canonical origins stored across every live (non-revoked) key.

    Used by the CORS preflight path in routes/public_api.py to compare
    against the caller-supplied origin WITHOUT passing user input through
    this function -- that breaks the CodeQL CWE-113 taint chain.
    """
    from clawmetry.apikeys import _read_store

    result = []
    for rec in _read_store()["keys"]:
        if rec.get("revoked_at"):
            continue
        for stored in (rec.get("origins") or []):
            result.append(str(stored))
    return result


def granted_shapes(record: dict) -> set:
    """Every live q/1 shape this key may dispatch."""
    from clawmetry.query_contract import shapes_for_scopes

    return shapes_for_scopes(record.get("scopes") or [])


def scope_catalogue() -> list:
    """``[{scope, doc, methods, sensitive}]`` for the UI and the CLI help.

    Derived from the query contract, so a method added there shows up
    here with no second list to update.
    """
    from clawmetry.query_contract import (
        SCOPE_CONTENT,
        SCOPE_DOC,
        SCOPES,
        live_methods_by_scope,
    )

    return [
        {
            "scope": s,
            "doc": SCOPE_DOC[s],
            "methods": live_methods_by_scope(s),
            "sensitive": s == SCOPE_CONTENT,
        }
        for s in SCOPES
    ]


def store_summary() -> dict[str, Any]:
    """Counts for the dashboard panel, cheap enough to call per page load."""
    from clawmetry.apikeys import MAX_KEYS, _read_store, _store_path

    doc = _read_store()
    keys = doc["keys"]
    return {
        "active": sum(1 for k in keys if not k.get("revoked_at")),
        "revoked": sum(1 for k in keys if k.get("revoked_at")),
        "max": MAX_KEYS,
        "path": _store_path(),
    }
