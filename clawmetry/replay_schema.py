"""Canonical replay-event schema.

Neutral event shape every runtime adapter maps its native events into,
so the transcript viewer can render a single runtime-aware replay UI
across Claude Code sidechains, OpenClaw subagent/flow DAGs, Antigravity
cascades, n8n workflow executions, Codex per-turn approval policies, etc.

Motivating issue: openclaw/clawmetry#4813. Full initiative index in
``project_session_replay_initiative_2026_08_14`` memory note.

Design notes:

- ``parent_span_id`` is the DELEGATION edge (parent Task/Agent spawned
  this child). It is NOT the transcript-chain parent — OpenClaw v3
  ``parentId`` and Qwen Code ``parentUuid`` are chains, not trees;
  conflating the two silently breaks the delegation tree UI.
- ``kind`` uses dotted names so the renderer can dispatch on prefix
  (``llm.*``, ``tool.*``, ``agent.*``, ``workflow.*``, ``approval.*``).
- ``mode`` and ``approval`` are optional side-channels — most events
  don't change mode and don't concern an approval; only ``mode.changed``
  and ``approval.*`` events populate them.
- ``payload`` is deliberately open — kind-specific fields go there.
  Renderer must tolerate missing keys.

The DuckDB table backing this schema is ``replay_events``, declared
in ``clawmetry/local_store.py`` alongside ``events`` and ``spans``.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

# ── Canonical event kinds ────────────────────────────────────────────────
# Grouped by prefix so the JS renderer can dispatch on the leading token.

KIND_LLM_CALL = "llm.call"
KIND_LLM_RESPONSE = "llm.response"
KIND_THINKING = "thinking"
KIND_TOOL_CALL = "tool.call"
KIND_TOOL_RESULT = "tool.result"
KIND_AGENT_SPAWN = "agent.spawn"
KIND_AGENT_RETURN = "agent.return"
KIND_WORKFLOW_START = "workflow.start"
KIND_WORKFLOW_STAGE = "workflow.stage"
KIND_WORKFLOW_END = "workflow.end"
KIND_APPROVAL_REQUESTED = "approval.requested"
KIND_APPROVAL_DECIDED = "approval.decided"
KIND_MODE_CHANGED = "mode.changed"
KIND_COMPACTION = "compaction"

ALL_KINDS: tuple[str, ...] = (
    KIND_LLM_CALL,
    KIND_LLM_RESPONSE,
    KIND_THINKING,
    KIND_TOOL_CALL,
    KIND_TOOL_RESULT,
    KIND_AGENT_SPAWN,
    KIND_AGENT_RETURN,
    KIND_WORKFLOW_START,
    KIND_WORKFLOW_STAGE,
    KIND_WORKFLOW_END,
    KIND_APPROVAL_REQUESTED,
    KIND_APPROVAL_DECIDED,
    KIND_MODE_CHANGED,
    KIND_COMPACTION,
)

# ── Enums for the side-channel dicts ─────────────────────────────────────

PermissionMode = Literal[
    "default",
    "acceptEdits",
    "plan",
    "bypassPermissions",   # Claude Code YOLO
    "yolo",                # generic alias
    "unknown",             # runtime has no signal; render "not captured"
]

SandboxMode = Literal[
    "read-only",
    "workspace-write",
    "danger-full-access",
    "container",           # NanoClaw etc.
    "unknown",
]

ApprovalStatus = Literal[
    "requested",
    "approved",
    "denied",
    "edited",              # user modified tool args before approving
    "timeout",
]

ApprovalResolver = Literal[
    "user",
    "hook",
    "policy",
    "model",               # apiRefusalCategory / apiRefusalExplanation
    "unknown",
]


class ModeChip(TypedDict, total=False):
    permission: PermissionMode | None
    sandbox: SandboxMode | None
    collaboration: str | None  # runtime-native token, no enum


class ApprovalInfo(TypedDict, total=False):
    status: ApprovalStatus
    decision_reason: str | None
    resolver: ApprovalResolver | None
    edit_diff: dict[str, Any] | None   # {"before": tool_args, "after": tool_args}


class ReplayEvent(TypedDict, total=False):
    """One canonical replay event. Written to ``replay_events`` DuckDB
    table by the daemon, read by ``/api/replay-tree/<session_id>``.
    """
    ts: float
    kind: str                    # one of ALL_KINDS
    span_id: str
    parent_span_id: str | None   # delegation edge, NOT transcript chain
    session_id: str
    runtime: str                 # runtime_kind, e.g. "claude_code"
    payload: dict[str, Any]
    mode: ModeChip | None
    approval: ApprovalInfo | None


# ── Validators / helpers ─────────────────────────────────────────────────


def is_valid_kind(kind: str) -> bool:
    return kind in ALL_KINDS


def validate(event: dict[str, Any]) -> list[str]:
    """Return a list of validation errors. Empty list = valid.

    Cheap enough to run on every insert; not a hard requirement (the
    DuckDB write is authoritative) but useful in tests and when an
    adapter is under active development.
    """
    errors: list[str] = []
    if "ts" not in event:
        errors.append("missing ts")
    elif not isinstance(event["ts"], (int, float)):
        errors.append("ts must be numeric (unix seconds)")
    if "kind" not in event:
        errors.append("missing kind")
    elif not is_valid_kind(event["kind"]):
        errors.append(f"unknown kind: {event['kind']}")
    if "span_id" not in event or not event["span_id"]:
        errors.append("missing span_id")
    if "session_id" not in event or not event["session_id"]:
        errors.append("missing session_id")
    if "runtime" not in event or not event["runtime"]:
        errors.append("missing runtime")
    # mode.changed events must carry a non-empty mode dict; nothing else
    # should carry one (adapters that emit e.g. mode on every tool call
    # bloat the store and confuse the mode-marker UI).
    kind = event.get("kind")
    if kind == KIND_MODE_CHANGED:
        if not event.get("mode"):
            errors.append("mode.changed event must include a mode dict")
    elif event.get("mode") is not None:
        errors.append(f"mode field only valid on {KIND_MODE_CHANGED} events")
    # approval side-channel is only valid on approval.* events.
    if kind and kind.startswith("approval.") and not event.get("approval"):
        errors.append(f"{kind} event must include an approval dict")
    elif kind and not kind.startswith("approval.") and event.get("approval") is not None:
        errors.append("approval field only valid on approval.* events")
    return errors
