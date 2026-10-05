"""Bounded, runtime-balanced guidance evidence for local and encrypted views.

AC-ASSIST-006.2 / .4: one daemon-owned query and shared deterministic builder;
no provider calls, file reads, configuration uploads or write actions.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import re
import time
from typing import Any

from clawmetry.config import is_clawmetry_internal_session
from clawmetry.nonsecret_hash import sha1

MAX_ROWS = 5000
MAX_ROWS_PER_RUNTIME = 150
MAX_EVENT_BYTES = 64 * 1024
MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_DECODED_BYTES = 8 * 1024 * 1024
MAX_SLICE_BYTES = 48 * 1024
MAX_SNAPSHOT_BYTES = 256 * 1024
CACHE_SECONDS = 45
CACHE_ENTRIES = 2

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

def _decode_event_data(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("data") or {}
    if isinstance(data, dict):
        return data
    if isinstance(data, (bytes, bytearray, memoryview)):
        from clawmetry.ccr import maybe_decompress
        data = maybe_decompress(bytes(data), max_bytes=MAX_EVENT_BYTES)
        if data is None:
            return {}
        try:
            data = data.decode("utf-8")
        except UnicodeError:
            return {}
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}
    return {}


def _message_text(data: dict[str, Any]) -> str:
    message = data.get("message")
    if isinstance(message, dict):
        data = message
    content = data.get("content") or data.get("text") or data.get("prompt") or ""
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
    message = data.get("message") if isinstance(data.get("message"), dict) else {}
    role = data.get("role") or message.get("role")
    if not role and row.get("event_type") in {"prompt.submitted", "user"}:
        role = "user"
    if str(role or "").lower() not in {"user", "human"}:
        return False
    session_id = row.get("session_id") or ""
    workspace_id = str(row.get("workspace_id") or "").replace("\\", "/").lower()
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
    value = str(workspace_id or "").replace("\\", "/").strip().rstrip("/")
    if not value:
        return None
    # A basename gives the user useful scope without returning a full local
    # filesystem path in an API intended for the dashboard card.
    return value.rsplit("/", 1)[-1][:120] or None


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
    seen_messages: set[tuple[str, str]] = set()

    for row in rows:
        from clawmetry.event_shape import classify, clean_prompt_text
        data = _decode_event_data(row)
        shape = classify(row.get("event_type") or "message", data)
        if shape["role"] != "user" or shape["block_kind"] != "text":
            continue
        data = {"role": "user", "content": clean_prompt_text(shape["text"])}
        text = _message_text(data)
        if not text or not _is_user_message(row, data, text):
            continue
        # Re-scrub legacy rows before keys, excerpts or labels are derived.
        # redact_text deliberately fails open at ingest. The audited API reports
        # internal failures; withhold this entire slice before it can be cached.
        from clawmetry.redaction import scrub_payload
        scrubbed, withheld = scrub_payload({
            "text": text, "workspace": str(row.get("workspace_id") or ""),
        })
        if withheld:
            raise ValueError("Improve evidence could not be redacted")
        text = scrubbed["text"]
        label = _workspace_label(scrubbed["workspace"])
        message_key = (str(row.get("session_id") or ""), text)
        if message_key in seen_messages:
            continue
        seen_messages.add(message_key)
        if row.get("session_id"):
            all_sessions.add(str(row["session_id"]))
        if label:
            all_workspaces.add(label)
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
        if label:
            group["workspaces"].add(label)
            all_workspaces.add(label)
        runtime = str(row.get("runtime") or row.get("agent_type") or "").strip()
        if runtime:
            group["runtimes"].add(runtime)
        group["examples"].append(
            {
                "excerpt": _excerpt(text),
                "ts": row.get("ts"),
                "workspace": label,
                "runtime": runtime,
                "_source": {"session_id": str(row.get("session_id") or ""),
                            "runtime": runtime, "event_id": "events:" + str(row.get("id") or "")}
                if row.get("session_id") and row.get("id") else None,
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
        investigation = examples[0].get("_source")
        investigation_unavailable = None
        if investigation:
            from clawmetry.assistant_improve import validate_reference
            try:
                investigation = validate_reference(investigation)
            except ValueError:
                investigation = None
                investigation_unavailable = (
                    "The recorded context for this runtime cannot yet be attached to Assistant. "
                    "You can review the available evidence below.")
        candidates.append(
            {
                "id": f"{group['kind']}-{digest}",
                "cluster_id": f"{group['kind']}-{digest}",
                "kind": group["kind"],
                "label": f"{kind_label} signal",
                "summary": examples[0]["excerpt"],
                "normalized_key": f"{group['kind']}.{group['key'].replace(' ', '_')}",
                "excerpt": examples[0]["excerpt"],
                "evidence": [{k: v for k, v in example.items() if k != "_source"}
                             for example in examples[:_MAX_EVIDENCE]],
                "investigation": investigation,
                **({"investigation_unavailable": investigation_unavailable}
                   if investigation_unavailable else {}),
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


def unavailable(*, days=30, runtime=None, node_id=None, state="unavailable"):
    """A failed read has no measured counts; never disguise it as no signals."""
    return {"schema_version": 1, "state": state, "available": False, "reason": state, "store_available": False,
            "scope": {"node_id": node_id, "runtime": runtime or "all"},
            "window_days": days, "signals": [], "clusters": [],
            "coverage": {"status": "unavailable"}}


def _size(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _trim(body, budget=MAX_SLICE_BYTES):
    while body["signals"] and _size(body) > budget:
        body["signals"].pop()
        body["clusters"].pop()
    body["candidate_count"] = len(body["signals"])
    body["coverage"]["candidates_truncated"] = body["candidate_count"] < body["total_candidate_count"]
    return body


def _select_rows(store, *, days, node_id, allowed, now):
    """One key-first query, with fair ordering BEFORE global row/byte caps.

    The SQL filters time, node, entitled runtime, message event kinds and
    internal/delegated sessions. A child's user role describes a delegated
    instruction, not a human preference. Keep the exact persisted session id
    (including its runtime prefix), as the subagents agent_type is legacy and
    may be openclaw for other runtimes. Exclude embedded subagent event lanes
    too, since those share the human parent's session id.
    Typed roles exclude assistant/system traffic before ranking. Legacy roles
    and text live inside potentially compressed BLOBs;
    decode only this bounded selection, reporting any omitted evidence.
    No filesystem reads, UDFs, per-runtime scans or second DB connection.
    """
    from clawmetry.local_store import _NON_OPENCLAW_RUNTIME_PREFIXES
    prefixes = sorted(_NON_OPENCLAW_RUNTIME_PREFIXES)
    marks = ",".join("?" for _ in prefixes)
    rt = (f"CASE WHEN lower(split_part(session_id, ':', 1)) IN ({marks}) "
          "THEN lower(split_part(session_id, ':', 1)) "
          "WHEN agent_type IS NULL OR agent_type IN ('main','subagent','cron','') THEN 'openclaw' "
          "ELSE lower(agent_type) END")
    since = (now - timedelta(days=days)).isoformat()
    where = " AND node_id=?" if node_id else ""
    params = [*prefixes, since, now.isoformat()]
    if node_id:
        params.append(node_id)
    params.extend(allowed)
    params.extend([MAX_ROWS_PER_RUNTIME, MAX_ROWS, MAX_EVENT_BYTES, MAX_INPUT_BYTES])
    return store._fetch(f"""
        WITH scoped AS (
            SELECT id, session_id, workspace_id, event_type, ts, node_id,
                   octet_length(data) AS nbytes, {rt} AS runtime
            FROM events
            WHERE ts >= ? AND ts <= ? {where}
              AND (role IN ('user', 'human') OR event_type IN ('message', 'prompt.submitted', 'user', 'user_prompt'))
              AND (role IN ('user', 'human') OR role IS NULL OR role = '')
              AND coalesce(event_type, '') NOT LIKE 'subagent:%'
              AND NOT EXISTS (
                  SELECT 1 FROM subagents child
                  WHERE child.subagent_id = events.session_id
                    AND child.parent_session_id IS NOT NULL
                    AND child.parent_session_id <> ''
              )
              AND agent_id IS DISTINCT FROM 'clawmetry-daemon'
              AND NOT regexp_matches(coalesce(session_id,''), '(^|:)clawmetry-')
              AND NOT contains(replace(lower(coalesce(workspace_id,'')), chr(92), '/'), '/harnessruns')
              AND NOT contains(replace(lower(coalesce(workspace_id,'')), chr(92), '/'), '/.blume/harnessruns')
        ), ranked AS (
            SELECT *, row_number() OVER (PARTITION BY runtime ORDER BY ts DESC, id DESC) AS rn,
                   count(*) OVER (PARTITION BY runtime) AS available
            FROM scoped WHERE runtime IN ({','.join('?' for _ in allowed)})
        ), selected AS (
            SELECT * FROM ranked WHERE rn <= ? ORDER BY rn, runtime LIMIT ?
        ), budgeted AS (
            SELECT *, sum(least(coalesce(nbytes,0), ?)) OVER
                (ORDER BY rn, runtime ROWS UNBOUNDED PRECEDING) AS running_bytes
            FROM selected
        )
        SELECT s.id, s.session_id, s.workspace_id, s.event_type, s.ts, s.runtime,
               s.available, s.nbytes,
               CASE WHEN s.running_bytes <= ? AND s.nbytes <= {MAX_EVENT_BYTES}
                    THEN e.data ELSE NULL END AS data
        FROM budgeted s JOIN events e ON e.id=s.id ORDER BY s.rn, s.runtime
    """, params)


def _build_bundle(store, *, days, node_id, allowed):
    from clawmetry.ccr import maybe_decompress
    now = datetime.now(timezone.utc)
    selected = _select_rows(store, days=days, node_id=node_id, allowed=allowed, now=now)
    by_runtime = defaultdict(list)
    available, inspected, omitted = {}, defaultdict(int), defaultdict(int)
    decoded_bytes = 0
    for eid, sid, workspace, kind, ts, runtime, total, nbytes, blob in selected:
        available[runtime] = int(total)
        inspected[runtime] += 1
        raw = maybe_decompress(blob, max_bytes=MAX_EVENT_BYTES) if blob is not None else None
        if raw is None or decoded_bytes + len(raw) > MAX_DECODED_BYTES:
            omitted[runtime] += 1
            continue
        decoded_bytes += len(raw)
        row = {"id": eid, "session_id": sid, "workspace_id": workspace,
               "event_type": kind, "ts": ts, "runtime": runtime, "data": raw}
        data = _decode_event_data(row)
        if not data:
            omitted[runtime] += 1
            continue
        row["data"] = data
        by_runtime[runtime].append(row)

    def build(runtime=None):
        keys = [runtime] if runtime else list(available)
        rows = [row for key in keys for row in by_runtime[key]]
        total = sum(available.get(key, 0) for key in keys)
        count = sum(inspected[key] for key in keys)
        dropped = sum(omitted[key] for key in keys)
        body = _build_candidates(rows, window_days=days)
        body.update(schema_version=1, state="ready", available=True, store_available=True,
                    source="local_store", generated_at=now.isoformat(),
                    scope={"node_id": node_id, "runtime": runtime or "all"},
                    capabilities={"candidates": True, "suggestions": False, "apply": False,
                                  "note": "Candidates are read-only evidence. No files change from this view."},
                    coverage={"status": "partial" if total > count or dropped else "complete",
                              "candidate_events": total, "inspected_events": count,
                              "omitted_payloads": dropped, "event_limit": MAX_ROWS,
                              "per_runtime_limit": MAX_ROWS_PER_RUNTIME,
                              "candidates_truncated": False})
        return _trim(body)

    # Empty slices for entitled runtimes distinguish no activity from an older
    # daemon missing the field. Selected scope never falls back to node-wide.
    bundle = {"improve": build(), "improveByRuntime": {rt: build(rt) for rt in allowed}}
    # Account sizes once; repeatedly serializing the entire bundle while
    # trimming many runtimes would turn a bounded response into expensive work.
    slices = [bundle["improve"], *bundle["improveByRuntime"].values()]
    sizes = [_size(body) for body in slices]
    total_bytes = _size(bundle)
    while total_bytes > MAX_SNAPSHOT_BYTES:
        populated = [i for i, body in enumerate(slices) if body["signals"]]
        if not populated:
            break
        index = max(populated, key=lambda i: sizes[i])
        body = slices[index]
        # Preserve a quiet runtime's final occurrence when shorter display
        # excerpts can make room for its exact investigation reference.
        compacted = False
        if index and len(body["signals"]) == 1:
            signal = body["signals"][0]
            for item, fields in [(signal, ("summary", "excerpt")),
                                 *[(e, ("excerpt",)) for e in signal["evidence"]]]:
                for field in fields:
                    if len(item.get(field) or "") > 140:
                        item[field] = _excerpt(item[field], 140)
                        compacted = True
        if not compacted:
            body["signals"].pop()
            body["clusters"].pop()
        body["candidate_count"] = len(body["signals"])
        body["coverage"]["candidates_truncated"] = True
        new_size = _size(body)
        total_bytes += new_size - sizes[index]
        sizes[index] = new_size
    return bundle


def query_candidates(store, *, window_days=30, runtime=None, node_id=None, include_by_runtime=False):
    """Cache lives on the owning store, bounded and single-flight across readers.

    Do not hold the writer lock during query/derivation; _fetch uses the store's
    per-thread cursor. Changing entitlement or redaction invalidates the key.
    Returned values are copies so route/snapshot consumers cannot poison cache.
    """
    from clawmetry import entitlements, redaction
    days = max(1, min(int(window_days), 90))
    runtime = str(runtime or "all").lower()
    if node_id is not None and (not isinstance(node_id, str) or len(node_id) > 256):
        return unavailable(days=days, state="invalid_scope")
    known = entitlements.FREE_RUNTIMES | entitlements.PAID_RUNTIMES
    if runtime != "all" and runtime not in known:
        return unavailable(days=days, runtime=runtime, node_id=node_id, state="invalid_scope")
    entitlement = entitlements.get_entitlement()
    allowed = tuple(sorted(rt for rt in known if entitlement.allows_runtime(rt)))
    if runtime != "all" and runtime not in allowed:
        return unavailable(days=days, runtime=runtime, node_id=node_id, state="locked")
    policy = json.dumps(redaction.pii_status(), sort_keys=True)
    key = (days, node_id, allowed, redaction._disabled(), policy)
    with store._improve_cache_lock:
        now = time.monotonic()
        hit = store._improve_cache.get(key)
        if hit and now - hit[0] < CACHE_SECONDS:
            bundle = hit[1]
        else:
            bundle = _build_bundle(store, days=days, node_id=node_id, allowed=allowed)
            # No success cache entry is installed on a query/redaction failure.
            if len(store._improve_cache) >= CACHE_ENTRIES:
                store._improve_cache.pop(next(iter(store._improve_cache)))
            store._improve_cache[key] = (time.monotonic(), bundle)
        result = bundle if include_by_runtime else (
            bundle["improve"] if runtime == "all" else bundle["improveByRuntime"][runtime])
        return deepcopy(result)


def build_snapshot(store, *, node_id=None):
    """Only a caller's encrypted system snapshot may publish this content."""
    try:
        return store.query_improve_candidates(node_id=node_id, include_by_runtime=True)
    except Exception:
        return {"improve": unavailable(node_id=node_id), "improveByRuntime": {}}
