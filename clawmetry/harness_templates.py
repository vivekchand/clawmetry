"""Per-harness custom-tab template registry.

Every agent runtime ClawMetry monitors exposes a *unique* observable surface
(goose recipes + schedules, cursor edit-ranges, opencode todos, …) that has no
home in the generic, runtime-agnostic tabs (Cost, Brain, Tracing). A **harness
template** is a small declarative JSON object that describes a custom panel for
one runtime: ordered sections, each with a title, a data ``source`` (a path into
the per-runtime data blob the dashboard fetches), and a ``render`` hint the
generic client-side renderer understands. The "Harness" tab renders the selected
runtime's template; the renderer never hard-codes a harness.

Open-core split (mirrors the adapter registry exactly):

* This module + the renderer + the Harness tab shell + the **free** templates
  (openclaw, nemoclaw) ship in OSS clawmetry.
* The **10 closed pro** templates live in ``clawmetry-pro`` and register
  themselves through the ``clawmetry.extensions`` plugin seam at startup
  (``register_all`` calls :func:`register` for each), the same way the closed
  adapters do. A FREE node only ever sees the openclaw/nemoclaw panels; a
  licensed node lights up the rest.

The template ``source`` mini-DSL (resolved client-side against the fetched data):

* ``summary.cost_usd``        → ``data.summary.cost_usd`` (a scalar)
* ``sessions[]``              → ``data.sessions`` (the whole list, for tables)
* ``sessions[].extra.recipe`` → for each session, pluck ``extra.recipe``
* ``extra.recipe``            → ``data.extra.recipe`` (a runtime-wide aggregate)

Render types the client renderer supports: ``count`` (single stat), ``kv``
(key/value), ``table`` (columns), ``badge-list``, ``timeline`` (ts + label),
``bar`` (label + value), ``json`` (collapsible raw). Adding a render type is a
client-only change; templates declaring an unknown type degrade to ``json``.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List

logger = logging.getLogger("clawmetry.harness_templates")

SCHEMA_VERSION = 1

# Render hints the client renderer knows how to draw. Kept here (not just in JS)
# so the guard test + :func:`validate` can reject typo'd templates at registration.
RENDER_TYPES = frozenset(
    {"count", "kv", "table", "badge-list", "timeline", "bar", "json"}
)

_templates: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def validate(template: Dict[str, Any]) -> List[str]:
    """Return a list of human-readable problems with ``template`` (empty = OK).

    Never raises — a malformed pro template must not take down startup; the
    caller logs the problems and skips the template instead.
    """
    errs: List[str] = []
    if not isinstance(template, dict):
        return ["template is not an object"]
    rt = template.get("runtime")
    if not rt or not isinstance(rt, str):
        errs.append("missing/!str 'runtime'")
    if not template.get("title"):
        errs.append("missing 'title'")
    sv = template.get("schema", SCHEMA_VERSION)
    if not isinstance(sv, int):
        errs.append("'schema' must be an int")
    sections = template.get("sections")
    if not isinstance(sections, list) or not sections:
        errs.append("'sections' must be a non-empty list")
        return errs
    seen_ids: set = set()
    for i, s in enumerate(sections):
        if not isinstance(s, dict):
            errs.append(f"section[{i}] is not an object")
            continue
        sid = s.get("id")
        if not sid:
            errs.append(f"section[{i}] missing 'id'")
        elif sid in seen_ids:
            errs.append(f"section[{i}] duplicate id {sid!r}")
        else:
            seen_ids.add(sid)
        if not s.get("title"):
            errs.append(f"section[{i}] ({sid}) missing 'title'")
        if not s.get("source"):
            errs.append(f"section[{i}] ({sid}) missing 'source'")
        render = s.get("render")
        if render not in RENDER_TYPES:
            errs.append(
                f"section[{i}] ({sid}) render {render!r} not in {sorted(RENDER_TYPES)}"
            )
        if render == "table" and not isinstance(s.get("columns"), list):
            errs.append(f"section[{i}] ({sid}) render=table needs 'columns' list")
    return errs


def register(template: Dict[str, Any]) -> bool:
    """Register (or replace, by ``runtime``) one harness template.

    Idempotent on ``runtime`` — a later registration overrides, so a pro package
    can override a built-in if it wants. Invalid templates are rejected (logged,
    not raised) so one bad pro template never blocks the others or startup.
    Returns ``True`` if the template was accepted.
    """
    problems = validate(template)
    rt = template.get("runtime", "?")
    if problems:
        logger.warning("harness template %r rejected: %s", rt, "; ".join(problems))
        return False
    tmpl = dict(template)
    tmpl.setdefault("schema", SCHEMA_VERSION)
    with _lock:
        _templates[rt] = tmpl
    logger.debug("registered harness template %r (%d sections)", rt, len(tmpl["sections"]))
    return True


def unregister(runtime: str) -> None:
    with _lock:
        _templates.pop(runtime, None)


def get(runtime: str) -> Dict[str, Any] | None:
    with _lock:
        t = _templates.get(runtime)
        return dict(t) if t else None


def all_templates() -> Dict[str, Dict[str, Any]]:
    """Snapshot of ``{runtime: template}`` — safe to serialize without the lock."""
    with _lock:
        return {k: dict(v) for k, v in _templates.items()}


def runtimes() -> List[str]:
    with _lock:
        return sorted(_templates.keys())


# --------------------------------------------------------------------------- #
# Built-in FREE templates (openclaw + nemoclaw). Pro templates register from
# clawmetry-pro via the plugin seam. These only reference data the dashboard
# serves today (summary + sessions); richer sections sourced from adapter
# ``extra.*`` fields are added as the harness-observability gap issues land
# (fix a gap -> a new extra key appears -> add its template section).
# --------------------------------------------------------------------------- #
_OPENCLAW_TEMPLATE: Dict[str, Any] = {
    "schema": SCHEMA_VERSION,
    "runtime": "openclaw",
    "title": "OpenClaw specifics",
    "icon": "\U0001F43E",  # paw prints
    "tier": "free",
    "sections": [
        {
            "id": "sessions_count",
            "title": "Sessions observed",
            "source": "summary.sessions",
            "render": "count",
            "unit": "sessions",
        },
        {
            "id": "spend",
            "title": "Spend (API-equivalent)",
            "source": "summary.cost_usd",
            "render": "count",
            "format": "money",
        },
        {
            "id": "recent",
            "title": "Recent sessions",
            "source": "sessions[]",
            "render": "table",
            "columns": ["session_id", "session_type", "cost_usd", "ended_at"],
            "empty": "No sessions yet",
        },
        {
            "id": "channels",
            "title": "Active channels",
            "source": "extra.channels",
            "render": "badge-list",
            "empty": "No chat channels detected",
        },
        {
            "id": "skills",
            "title": "Skills invoked",
            "source": "extra.skills",
            "render": "badge-list",
            "empty": "No skills invoked",
        },
    ],
}

_NEMOCLAW_TEMPLATE: Dict[str, Any] = {
    "schema": SCHEMA_VERSION,
    "runtime": "nemoclaw",
    "title": "NeMo Guardrails specifics",
    "icon": "\U0001F6E1️",  # shield
    "tier": "free",
    "sections": [
        {
            "id": "sessions_count",
            "title": "Sandboxed sessions",
            "source": "summary.sessions",
            "render": "count",
            "unit": "sessions",
        },
        {
            "id": "spend",
            "title": "Spend (API-equivalent)",
            "source": "summary.cost_usd",
            "render": "count",
            "format": "money",
        },
        {
            "id": "recent",
            "title": "Recent sandboxed runs",
            "source": "sessions[]",
            "render": "table",
            "columns": ["session_id", "session_type", "cost_usd", "ended_at"],
            "empty": "No sandboxed runs yet",
        },
        {
            "id": "guardrails",
            "title": "Guardrail actions",
            "source": "extra.guardrails",
            "render": "badge-list",
            "empty": "No guardrail activity observed",
        },
    ],
}


def _register_builtins() -> None:
    register(_OPENCLAW_TEMPLATE)
    register(_NEMOCLAW_TEMPLATE)


_register_builtins()
