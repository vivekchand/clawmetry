"""Read-only guidance candidates derived from observed agent conversations.

This is the OSS foundation for an Improve surface. It deliberately stops at
evidence-backed candidates: turning a candidate into a file patch belongs to
the existing Pro self-evolve implementation and must remain an explicit
review action.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Blueprint, jsonify, request

from clawmetry.config import is_clawmetry_internal_session
from clawmetry.nonsecret_hash import sha1


bp_improve = Blueprint("improve", __name__)

_LOGGER = logging.getLogger(__name__)
_CACHE_TTL_SECONDS = 45.0
_EVENT_LIMIT = 5000
_MAX_SIGNAL_COUNT = 40
_MAX_EVIDENCE = 3
_MAX_KEY_TOKENS = 24

_PREFERENCE_RE = re.compile(
    r"\b(?:from now on|going forward|for future|every time|always|never|"
    r"make sure|please keep|do not|don't|without em dashes|without those)\b",
    re.IGNORECASE,
)
_CORRECTION_RE = re.compile(
    r"\b(?:no|wrong|actually|instead|not quite|that's not|that is not|"
    r"you missed|you forgot|change|fix|remove|stop|not what i asked|"
    r"you did not)\b",
    re.IGNORECASE,
)
_FRUSTRATION_RE = re.compile(
    r"\b(?:again|still|why did|doesn't work|does not work|not working|"
    r"broken|failed|useless|shitty|wtf|ugh|come on|what's up)\b|[!?]{2,}",
    re.IGNORECASE,
)

# Blume's local improvement worker writes its own completed conversations into
# the same event store. They are useful for understanding the competitor, but
# must never become ClawMetry guidance candidates for the user.
_SYNTHETIC_MARKERS = (
    "<codex_internal_context",
    "<environment_context",
    "<scheduled-task",
    "<task-notification>",
    "you are analyzing one completed agent conversation",
    "you are an expert sql author for clawmetry",
    "you are clawmetry\'s read-only analytics planner",
    "you are clawmetry\'s helpful analytics assistant",
    "you are clustering newly extracted guidance signals",
    "professional software-localization translator",
    "the following is the codex agent history",
    "bounded live observability verification",
)

_CACHE: dict[str, Any] = {"expires": 0.0, "key": None, "data": None}


def _store_call(method_name: str, **kwargs):
    """Read through the daemon first, then use a read-only local fallback."""
    try:
        from routes.local_query import local_store_via_daemon

        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception as exc:  # pragma: no cover - depends on install mode
        _LOGGER.debug("improve daemon query failed: %s", exc)
    try:
        from clawmetry import local_store

        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception as exc:  # pragma: no cover - empty/uninitialised store
        _LOGGER.warning("improve local store query failed: %s", exc)
        return None


def _decode_event_data(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("data") or {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}
    return {}


def _message_text(data: dict[str, Any]) -> str:
    content = data.get("content") or data.get("text") or ""
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                value = item.get("text") or item.get("content") or ""
            else:
                value = item
            if value:
                parts.append(str(value))
        content = " ".join(parts)
    text = str(content)
    # Transcript wrappers often carry temporary screenshot paths. They are
    # useful to the transcript viewer but are noise and local-path leakage in
    # a guidance card.
    text = re.sub(r"<image\b[^>]*>.*?</image>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[image(?:\s+#[^\]]+|:\s*source:[^\]]+)?\]", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split()).strip()


def _is_user_message(row: dict[str, Any], data: dict[str, Any], text: str) -> bool:
    if str(data.get("role") or "").lower() not in {"user", "human"}:
        return False
    session_id = row.get("session_id") or ""
    workspace_id = str(row.get("workspace_id") or "").lower()
    lowered = text.lower()
    if is_clawmetry_internal_session(session_id):
        return False
    if "/.blume/harnessruns" in workspace_id or "/harnessruns" in workspace_id:
        return False
    return not any(marker in lowered for marker in _SYNTHETIC_MARKERS)


def _candidate_kind(text: str) -> str | None:
    # Durable preferences win when one message contains several signals. A
    # correction is the next strongest signal; frustration remains useful as
    # evidence but is not presented as a durable instruction automatically.
    if _PREFERENCE_RE.search(text):
        return "preference"
    if _CORRECTION_RE.search(text):
        return "correction"
    if _FRUSTRATION_RE.search(text):
        return "frustration"
    return None


def _normalise_key(text: str) -> str:
    """Return a stable, conservative key for a repeated guidance signal.

    Blume's signal records are keyed by a normalized concept rather than the
    raw transcript sentence.  We keep this dependency-free: normalize common
    durable-instruction phrases and remove conversational scaffolding while
    preserving the words that carry the instruction's meaning.
    """
    value = re.sub(r"https?://\S+", " ", text.lower())
    value = re.sub(r"\[image[^\]]*\]", " ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("don't", "do not").replace("doesn't", "does not")
    value = value.replace("can't", "cannot").replace("isn't", "is not")
    value = re.sub(
        r"\b(?:from now on|going forward|for future|every time|always)\b",
        " durable ",
        value,
    )
    value = re.sub(r"\b(?:do not|never|without|no)\b", " avoid ", value)
    value = re.sub(
        r"\b(?:please|actually|just|really|can you|could you|would you|"
        r"i need you to|i want you to|make sure)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    stop_words = {
        "a", "an", "and", "are", "be", "for", "i", "in", "is", "it",
        "me", "of", "on", "or", "that", "the", "this", "to", "use",
        "want", "we", "with", "you",
    }
    tokens = []
    seen = set()
    for token in value.split():
        if token in stop_words or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
        if len(tokens) >= _MAX_KEY_TOKENS:
            break
    return " ".join(tokens)[:180]


def _excerpt(text: str, limit: int = 280) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _workspace_label(workspace_id: Any) -> str | None:
    value = str(workspace_id or "").strip().rstrip("/")
    if not value:
        return None
    # A basename gives the user useful scope without returning a full local
    # filesystem path in an API intended for the dashboard card.
    return value.rsplit("/", 1)[-1] or None


def _confidence(kind: str, message_count: int, conversation_count: int) -> str:
    score = (2 if kind == "preference" else 1) + min(message_count, 3)
    score += min(conversation_count, 2)
    return "high" if score >= 5 else "medium"


def _confidence_score(kind: str, message_count: int, conversation_count: int) -> float:
    """Return a small explainable confidence score for the review surface."""
    score = 0.42
    score += 0.10 * min(message_count, 3)
    score += 0.12 * min(conversation_count, 3)
    if kind == "preference":
        score += 0.08
    return round(min(score, 0.96), 2)


def _pain_score(kind: str, message_count: int, conversation_count: int) -> int:
    """Map recurrence and signal kind to Blume-like 1–5 pain metadata."""
    score = {"preference": 1, "correction": 2, "frustration": 3}.get(kind, 1)
    score += min(max(message_count - 1, 0), 1)
    score += min(max(conversation_count - 1, 0), 1)
    return min(score, 5)


def _build_candidates(rows: list[dict[str, Any]], *, window_days: int) -> dict[str, Any]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    message_count = 0
    all_sessions: set[str] = set()
    all_workspaces: set[str] = set()

    for row in rows:
        data = _decode_event_data(row)
        text = _message_text(data)
        if not text or not _is_user_message(row, data, text):
            continue
        message_count += 1
        kind = _candidate_kind(text)
        if not kind:
            continue
        key = _normalise_key(text)
        if not key:
            continue
        group = groups.setdefault(
            (kind, key),
            {
                "kind": kind,
                "key": key,
                "examples": [],
                "sessions": set(),
                "workspaces": set(),
                "runtimes": set(),
            },
        )
        # Event replication can repeat the same message with a slightly
        # different ingest timestamp. A signal is recurrence across
        # conversations, so count one exact message once per session.
        event_key = (str(row.get("session_id") or ""), text)
        if event_key in group.setdefault("event_keys", set()):
            continue
        group["event_keys"].add(event_key)
        group["sessions"].add(str(row.get("session_id") or ""))
        if row.get("session_id"):
            all_sessions.add(str(row.get("session_id")))
        label = _workspace_label(row.get("workspace_id"))
        if label:
            group["workspaces"].add(label)
            all_workspaces.add(label)
        runtime = str(row.get("agent_type") or "").strip()
        if runtime:
            group["runtimes"].add(runtime)
        group["examples"].append(
            {
                "excerpt": _excerpt(text),
                "ts": row.get("ts"),
                "workspace": label,
            }
        )

    candidates = []
    for group in groups.values():
        examples = sorted(group["examples"], key=lambda item: str(item.get("ts") or ""), reverse=True)
        sessions = {sid for sid in group["sessions"] if sid}
        workspaces = sorted(group["workspaces"])
        conversation_count = len(sessions)
        count = len(group.get("event_keys") or ())
        confidence = _confidence(group["kind"], count, conversation_count)
        confidence_score = _confidence_score(
            group["kind"], count, conversation_count
        )
        pain_score = _pain_score(group["kind"], count, conversation_count)
        score = (conversation_count * 3) + count + (2 if group["kind"] == "preference" else 0)
        digest = sha1(f"{group['kind']}:{group['key']}".encode()).hexdigest()[:12]
        kind_label = group["kind"].capitalize()
        scope = "project" if len(workspaces) == 1 else "workspace"
        runtimes = sorted(group["runtimes"])
        candidates.append(
            {
                "id": f"{group['kind']}-{digest}",
                "cluster_id": f"{group['kind']}-{digest}",
                "kind": group["kind"],
                "label": f"{kind_label} signal",
                "summary": examples[0]["excerpt"],
                "normalized_key": f"{group['kind']}.{group['key'].replace(' ', '_')}",
                "excerpt": examples[0]["excerpt"],
                "evidence": examples[:_MAX_EVIDENCE],
                "signal_count": count,
                "seen_count": count,
                "conversation_count": conversation_count,
                "project_count": len(workspaces),
                "projects": workspaces[:5],
                "runtimes": runtimes,
                "harness_applicability": runtimes,
                "observed_harness": runtimes[0] if len(runtimes) == 1 else "multiple",
                "scope": scope,
                "pain_score": pain_score,
                "confidence_score": confidence_score,
                "last_seen": examples[0].get("ts"),
                "confidence": confidence,
                "status": "candidate",
                "_score": score,
            }
        )

    candidates.sort(key=lambda item: (item["_score"], str(item.get("last_seen") or "")), reverse=True)
    for item in candidates:
        item.pop("_score", None)
    return {
        "window_days": window_days,
        "message_count": message_count,
        "candidate_count": min(len(candidates), _MAX_SIGNAL_COUNT),
        "total_candidate_count": len(candidates),
        "conversation_count": len(all_sessions),
        "project_count": len(all_workspaces),
        "signals": candidates[:_MAX_SIGNAL_COUNT],
        "clusters": [
            {
                "cluster_id": item["cluster_id"],
                "normalized_key": item["normalized_key"],
                "signal_count": item["signal_count"],
                "conversation_count": item["conversation_count"],
                "project_count": item["project_count"],
                "scope": item["scope"],
                "pain_score": item["pain_score"],
                "confidence_score": item["confidence_score"],
                "harnesses": item["harness_applicability"],
                "status": "open",
            }
            for item in candidates[:_MAX_SIGNAL_COUNT]
        ],
    }


def _window_days() -> int:
    raw = (request.args.get("window") or request.args.get("days") or "30").strip().lower().rstrip("d")
    try:
        return min(90, max(1, int(raw)))
    except (TypeError, ValueError):
        return 30


@bp_improve.route("/api/improve/candidates", methods=["GET"])
def get_improve_candidates():
    """Return local, read-only candidates for improving agent guidance."""
    window_days = _window_days()
    cache_key = str(window_days)
    now = time.monotonic()
    if (
        _CACHE.get("data") is not None
        and _CACHE.get("key") == cache_key
        and now < float(_CACHE.get("expires") or 0)
    ):
        return jsonify(_CACHE["data"])

    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    rows = _store_call(
        "query_events",
        event_type="message",
        since=since,
        limit=_EVENT_LIMIT,
        exclude_daemon=True,
    ) or []
    if not isinstance(rows, list):
        rows = []
    result = _build_candidates(rows, window_days=window_days)
    result.update(
        {
            "source": "local_store",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "capabilities": {
                "candidates": True,
                "suggestions": False,
                "apply": False,
                "note": "Candidates are read-only evidence. Reviewable diffs require the Pro self-evolve implementation.",
            },
        }
    )
    _CACHE.update({"key": cache_key, "data": result, "expires": now + _CACHE_TTL_SECONDS})
    return jsonify(result)
