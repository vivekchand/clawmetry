"""clawmetry/query_contract.py — the declared q/1 query contract registry.

Single source of truth for the node query surface (issue #2987, Query
Spine P1). ``routes/local_query.py`` derives its ``_SHAPES`` allowlist
from this registry; ``docs/QUERY_CONTRACT.md`` is generated from it by
``scripts/gen_query_contract_doc.py``; and
``tests/test_query_contract_drift.py`` fails CI when any of the three
drift apart.

Versioning rule (q/1): evolution inside q/1 is ADDITIVE ONLY. New
methods and new optional args may be added; renaming or removing a
method, an arg, or a response field requires bumping to q/2. A
"planned" entry is a declared target that is not served yet — flipping
it to "live" is the additive act that turns it on (the drift test
enforces that a shape cannot ship without its registry entry, and that
a planned entry cannot be served while still marked planned).

Trust classes:

* ``plaintext`` — aggregate counters / metadata the server may see in
  cleartext (e.g. the heartbeat piggyback). Never raw content.
* ``e2e`` — session/content-bearing payloads. These must only ever
  leave the machine AES-256-GCM encrypted (the sync daemon's snapshot
  path); they must never ride a plaintext push list. Grep-level guard
  in the drift test today; hard enforcement lands in P4.

Spec fields per method:

* ``status``  — "live" (served today via _SHAPES/_dispatch) or
                "planned" (declared target, not yet served).
* ``args``    — allowed arg names -> {"required": bool, plus optional
                "default"/"lo"/"hi" for ints}. For live methods this
                MUST mirror what ``_coerce_args`` actually allows.
* ``trust``   — "plaintext" or "e2e" (see above).
* ``backing`` — the LocalStore method serving it (live) or the planned
                rollup table / store method (planned).
* ``doc``     — one-line description.

This module is intentionally dependency-free plain data so the doc
generator, the routes layer, firmware CIs, and the cloud repo can all
import (or vendor) it cheaply.
"""

from __future__ import annotations

CONTRACT_VERSION = "q/1"

STATUS_LIVE = "live"
STATUS_PLANNED = "planned"

TRUST_PLAINTEXT = "plaintext"
TRUST_E2E = "e2e"


def _arg(required: bool = False, **extra) -> dict:
    """Tiny spec-builder so the registry below reads as a table."""
    spec = {"required": bool(required)}
    spec.update(extra)
    return spec


QUERY_CONTRACT: dict = {
    # ── live: served today by routes/local_query.py (_SHAPES/_dispatch) ──
    "events": {
        "status": STATUS_LIVE,
        "args": {
            "session_id": _arg(),
            "agent_id": _arg(),
            "event_type": _arg(),
            "since": _arg(),
            "until": _arg(),
            "limit": _arg(default=200, lo=1, hi=5000),
        },
        "trust": TRUST_E2E,
        "backing": "query_events",
        "doc": "Raw event rows (tool calls, messages, errors), newest first.",
    },
    "sessions": {
        "status": STATUS_LIVE,
        "args": {
            "agent_id": _arg(),
            "since": _arg(),
            "until": _arg(),
            "limit": _arg(default=100, lo=1, hi=2000),
        },
        "trust": TRUST_E2E,
        "backing": "query_sessions",
        "doc": "One row per session_id with start/end, event count, cost.",
    },
    "aggregates": {
        "status": STATUS_LIVE,
        "args": {
            "agent_id": _arg(),
            "since": _arg(),
            "until": _arg(),
        },
        "trust": TRUST_PLAINTEXT,
        "backing": "query_aggregates",
        "doc": "Per-day rollup of events/tokens/cost (aggregate counters only).",
    },
    "health": {
        "status": STATUS_LIVE,
        "args": {},
        "trust": TRUST_PLAINTEXT,
        "backing": "health",
        "doc": "Store health snapshot (engine, size, ring depth, flush age).",
    },
    "transcript": {
        "status": STATUS_LIVE,
        "args": {
            "session_id": _arg(required=True),
            "limit": _arg(default=500, lo=1, hi=5000),
        },
        "trust": TRUST_E2E,
        "backing": "query_events",
        "doc": "Alias of events scoped to one required session_id.",
    },
    "spans": {
        "status": STATUS_LIVE,
        "args": {
            "trace_id": _arg(),
            "session_id": _arg(),
            "agent_type": _arg(),
            "since": _arg(),
            "until": _arg(),
            "limit": _arg(default=200, lo=1, hi=2000),
        },
        "trust": TRUST_E2E,
        "backing": "query_spans",
        "doc": "OTel span rows with full filters (trace/session/agent/time).",
    },
    "traces": {
        "status": STATUS_LIVE,
        "args": {
            "session_id": _arg(),
            "agent_type": _arg(),
            "since": _arg(),
            "until": _arg(),
            "limit": _arg(default=100, lo=1, hi=1000),
        },
        "trust": TRUST_E2E,
        "backing": "query_traces",
        "doc": "One row per trace_id with aggregate span stats.",
    },
    "external_calls": {
        "status": STATUS_LIVE,
        "args": {
            "session_id": _arg(),
            "since": _arg(),
            "until": _arg(),
            "limit": _arg(default=200, lo=1, hi=2000),
        },
        "trust": TRUST_E2E,
        "backing": "query_external_calls",
        "doc": "External (non-LLM) API calls captured by the interceptor.",
    },
    "search": {
        "status": STATUS_LIVE,
        "args": {
            "q": _arg(required=True),
            "model": _arg(),
            "status": _arg(),
            "since": _arg(),
            "until": _arg(),
            "limit": _arg(default=50, lo=1, hi=500),
        },
        "trust": TRUST_E2E,
        "backing": "query_search",
        "doc": "Full-text search over session titles and eval reasons.",
    },
    # ── planned: declared q/1 targets from the Query Spine PRD ──────────
    # Not served yet. The drift test fails if any of these appear in
    # _SHAPES without this registry entry being flipped to "live".
    "glance": {
        "status": STATUS_PLANNED,
        "args": {},
        "trust": TRUST_PLAINTEXT,
        "backing": "rollup_glance",
        "doc": ("Device-facing top-line counters (sessions, cost, alerts). "
                "Non-goal: no per-model data in glance."),
    },
    "runtimes": {
        "status": STATUS_PLANNED,
        "args": {
            "since": _arg(),
            "until": _arg(),
        },
        "trust": TRUST_PLAINTEXT,
        "backing": "rollup_runtimes",
        "doc": "Per-runtime activity/cost rollup (claude_code, openclaw, ...).",
    },
    "models": {
        "status": STATUS_PLANNED,
        "args": {
            "runtime": _arg(),
            "since": _arg(),
            "until": _arg(),
        },
        "trust": TRUST_PLAINTEXT,
        "backing": "rollup_models",
        "doc": "Per-model token/cost rollup across runtimes.",
    },
    "usage": {
        "status": STATUS_PLANNED,
        "args": {
            "runtime": _arg(),
            "since": _arg(),
            "until": _arg(),
        },
        "trust": TRUST_PLAINTEXT,
        "backing": "rollup_usage_daily",
        "doc": "Daily token/cost usage series (input/output/cache splits).",
    },
    "session": {
        "status": STATUS_PLANNED,
        "args": {
            "session_id": _arg(required=True),
        },
        "trust": TRUST_E2E,
        "backing": "query_sessions_table",
        "doc": "Single-session detail row (title, status, outcome, totals).",
    },
    "brain": {
        "status": STATUS_PLANNED,
        "args": {
            "session_id": _arg(),
            "since": _arg(),
            "limit": _arg(default=200, lo=1, hi=2000),
        },
        "trust": TRUST_E2E,
        "backing": "query_events",
        "doc": "Reasoning/tool event slice powering the Brain feed.",
    },
    "approvals": {
        "status": STATUS_PLANNED,
        "args": {
            "status": _arg(),
            "limit": _arg(default=100, lo=1, hi=1000),
        },
        "trust": TRUST_PLAINTEXT,
        "backing": "query_approvals",
        "doc": "Approval queue metadata (ids, states, timestamps; no content).",
    },
}


# ``_dispatch`` special-cases that don't follow the plain
# "getattr(store, backing)(**args)" call shape. health calls
# ``store.health()`` directly, signalled by a None method name in _SHAPES.
_DISPATCH_OVERRIDES: dict = {"health": None}


def live_shapes() -> dict:
    """The shape -> LocalStore-method allowlist served by
    ``routes/local_query.py``. Byte-identical to the historical hand
    written ``_SHAPES`` dict (health maps to None: special-cased in
    ``_dispatch``)."""
    out = {}
    for name, spec in QUERY_CONTRACT.items():
        if spec["status"] != STATUS_LIVE:
            continue
        out[name] = _DISPATCH_OVERRIDES.get(name, spec["backing"])
    return out


def methods_by_status(status: str) -> list:
    return sorted(n for n, s in QUERY_CONTRACT.items() if s["status"] == status)


def methods_by_trust(trust: str) -> list:
    return sorted(n for n, s in QUERY_CONTRACT.items() if s["trust"] == trust)
