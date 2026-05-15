"""clawmetry/approvals.py — cloud-mediated approval policy engine.

Watches the unified DuckDB event store (``clawmetry/local_store.py``) for
tool calls that match a user-defined approval policy. When a match fires:

  1. POST the request to ClawMetry cloud (`/api/approvals/request`)
  2. Notify a human (cloud handles delivery — Slack/email/browser link)
  3. Poll cloud (`/api/approvals/<id>`) every 3 s up to policy.timeout
  4. On `denied` → call gateway `sessions_kill(session_id)` to abort the agent
  5. On `timeout` → apply policy.on_timeout (default: deny → kill)
  6. On `approved` → no-op, the action proceeds

Policies live in `~/.clawmetry/policies.yml`. See README + the in-app
Policies tab for the YAML format.

Companion to vivekchand/clawmetry#667 (issue) and the cloud receiver in
vivekchand/clawmetry-cloud#337.

Backward-compat NOTE (PRD vivekchand/clawmetry-cloud#779, audit P0 #6):
  Prior to 2026-05-13 the watcher tail-globbed
  ``~/.openclaw/agents/main/sessions/*.jsonl`` directly. That worked only
  for OpenClaw — Hermes / Codex / Claude Code adapters were invisible to
  the policy engine. The watcher now reads from
  ``local_store.query_events()`` which every adapter feeds, so a policy
  fires regardless of which framework produced the toolCall. The legacy
  JSONL paths are no longer scanned. If you had tooling that depended on
  the watcher reading JSONL directly, point it at the DuckDB store
  (``~/.clawmetry/clawmetry.duckdb``) instead — the same events live
  there. No flag is provided for graceful migration: the unified store
  has a strict superset of the old data.

Design notes:
  * Stateless watcher — restartable any time, resumes from a single
    ``approvals_last_check_ts`` watermark persisted in
    ``~/.clawmetry/sync-state.json``. The watermark survives daemon
    restarts, so already-decided approvals are not re-evaluated.
  * One in-flight approval per (session, tool_call_id). Multiple matches
    on the same call collapse into one request — important so a session
    that matches both "rm" AND "outside-tmp" policies doesn't get
    duplicate Slack pings.
  * NO HTTP retry storm — cloud round-trip uses the existing ``_post``
    helper which already backs off + handles 429s.
  * Soft-fail in OSS-only mode (no cloud configured): log and pass
    through. The same code runs in pure-local installs without crashing.
"""
from __future__ import annotations

import os
import re
import json
import time
import uuid
import logging
import threading
from pathlib import Path
from typing import Optional

log = logging.getLogger("clawmetry-approvals")

POLICIES_PATH = Path.home() / ".clawmetry" / "policies.yml"

# Default poll interval when waiting on a decision; cloud has 60-300 s timeouts
# typically so 3 s gives the user perceived responsiveness without hammering
# the API.
_POLL_INTERVAL_SEC = 3.0

# Track in-flight approvals so we don't re-request on a watcher restart that
# replays the same toolCall row. Keyed by tool_call_id (or composite when
# missing — `f"{session_id}:{ts}"`).
_in_flight: dict[str, dict] = {}
_in_flight_lock = threading.Lock()


# ── Policy loading ────────────────────────────────────────────────────────


def _load_yaml(text: str) -> list[dict]:
    """Tiny YAML subset reader so we don't add PyYAML as a daemon dep.

    Supports the exact shape we document: a top-level list of dicts where
    each dict has scalar values OR a nested ``match`` dict. No anchors,
    multi-line strings, or other YAML exotica.

    For anything beyond the trivial format users hit, they can install
    pyyaml and we'll prefer that — see the import-fallback below.
    """
    try:
        import yaml as _yaml  # type: ignore
        return _yaml.safe_load(text) or []
    except ImportError:
        pass
    # Hand-rolled minimal parser. Documented as "best-effort"; users with
    # complex policies are expected to `pip install pyyaml`.
    out: list[dict] = []
    cur: Optional[dict] = None
    cur_match: Optional[dict] = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("- "):
            cur = {}
            cur_match = None
            out.append(cur)
            kv = line[2:]
            if ":" in kv:
                k, _, v = kv.partition(":")
                cur[k.strip()] = _yaml_scalar(v.strip())
            continue
        if cur is None:
            continue
        # Nested ``match:``
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.endswith(":") and indent <= 4:
            key = stripped[:-1].strip()
            if key == "match":
                cur_match = {}
                cur[key] = cur_match
            continue
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            target = cur_match if (cur_match is not None and indent >= 4) else cur
            target[k.strip()] = _yaml_scalar(v.strip())
    return [d for d in out if d]


def _yaml_scalar(s: str):
    if s == "" or s in ("~", "null"):
        return None
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    try:
        if "." not in s:
            return int(s)
    except ValueError:
        pass
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s[1:-1]
    return s


def _compile_policy(p: dict) -> Optional[dict]:
    """Compile a single raw policy dict into a match-ready dict, or None."""
    match = p.get("match") or {}
    # Cloud-stored policies use top-level fields instead of nested `match`
    tool = (match.get("tool") or p.get("tool") or "").strip()
    cmd_re_str = match.get("command_regex") or (
        p.get("pattern") if p.get("pattern_type") == "command_regex" else None
    )
    cmd_not_re = match.get("command_not_regex")
    args_re = match.get("args_regex")
    try:
        return {
            "name": p.get("name") or "(unnamed)",
            "tool": tool,
            "command_regex": re.compile(cmd_re_str) if cmd_re_str else None,
            "command_not_regex": re.compile(cmd_not_re) if cmd_not_re else None,
            "args_regex": re.compile(args_re) if args_re else None,
            "action": (p.get("action") or "require_approval").strip(),
            "timeout": int(p.get("timeout") or 60),
            "on_timeout": (p.get("on_timeout") or "deny").strip(),
        }
    except re.error as re_err:
        log.warning(f"policy '{p.get('name')}' has bad regex: {re_err}")
        return None


def load_policies(api_key: Optional[str] = None) -> list[dict]:
    """Load policies from local YAML + cloud (if api_key is set).

    Cloud-stored policies (created from the UI) take precedence and are
    merged with local YAML policies. This lets non-technical users create
    rules from the dashboard while power users keep their YAML.
    """
    compiled: list[dict] = []

    # 1) Cloud-stored policies (UI-created)
    if api_key:
        try:
            cloud = _fetch_cloud_policies(api_key)
            for p in cloud:
                if not p.get("enabled", True):
                    continue
                c = _compile_policy(p)
                if c:
                    compiled.append(c)
            if compiled:
                log.debug(f"loaded {len(compiled)} cloud policies")
        except Exception as e:
            log.debug(f"cloud policies fetch failed (will use local): {e}")

    # 2) Local YAML policies
    if POLICIES_PATH.exists():
        try:
            raw = POLICIES_PATH.read_text(errors="replace")
            for p in _load_yaml(raw):
                if not isinstance(p, dict):
                    continue
                c = _compile_policy(p)
                if c:
                    compiled.append(c)
        except Exception as e:
            log.warning(f"failed to read {POLICIES_PATH}: {e}")

    if compiled:
        log.info(f"loaded {len(compiled)} approval policies "
                 f"(cloud + {POLICIES_PATH})")
    return compiled


_cloud_policies_cache: tuple = (0.0, [])
_CLOUD_CACHE_TTL = 30.0  # re-fetch from cloud every 30 s


def _fetch_cloud_policies(api_key: str) -> list[dict]:
    """GET /api/cloud/policies with a short TTL cache."""
    global _cloud_policies_cache
    now = time.time()
    if now - _cloud_policies_cache[0] < _CLOUD_CACHE_TTL:
        return _cloud_policies_cache[1]
    import urllib.request
    from clawmetry.sync import INGEST_URL
    req = urllib.request.Request(
        f"{INGEST_URL.rstrip('/')}/api/cloud/policies",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    policies = data.get("policies") or []
    _cloud_policies_cache = (now, policies)
    return policies


# ── Match engine ──────────────────────────────────────────────────────────


def _extract_command(tool_name: str, args: dict) -> str:
    """Best-effort: derive the human-readable 'command' string from toolCall args.

    Different OpenClaw tools name the field differently (`command`, `cmd`,
    `script`, `query`, `path`, …). Match on whichever is present.
    """
    if not isinstance(args, dict):
        return ""
    for k in ("command", "cmd", "script", "query", "url", "path", "file_path",
              "task", "message", "content"):
        v = args.get(k)
        if isinstance(v, str) and v:
            return v
    # Fallback: stringify args
    try:
        return json.dumps(args)[:500]
    except Exception:
        return ""


def match_policy(policies: list[dict], tool_name: str, args: dict):
    """Return the FIRST matching policy or None.

    Tool-name match is exact (case-insensitive); command/args matches are
    regex .search() so partial matches count.
    """
    cmd = _extract_command(tool_name, args)
    args_str = ""
    try:
        args_str = json.dumps(args, sort_keys=True) if isinstance(args, dict) else str(args)
    except Exception:
        pass
    for p in policies:
        if p.get("tool") and tool_name.lower() != p["tool"].lower():
            continue
        if p.get("command_regex") and not p["command_regex"].search(cmd):
            continue
        if p.get("command_not_regex") and p["command_not_regex"].search(cmd):
            continue
        if p.get("args_regex") and not p["args_regex"].search(args_str):
            continue
        return p
    return None


# ── Cloud round-trip ──────────────────────────────────────────────────────


def _post_approval_request(api_key: str, payload: dict) -> Optional[dict]:
    """POST to cloud's /api/approvals/request. Returns dict or None on failure.

    We don't reuse `clawmetry.sync._post` because that ships X-Api-Key, but
    the cloud auth shim only honors `Authorization: Bearer` for /api/* paths.
    """
    import urllib.request, urllib.error
    from clawmetry.sync import INGEST_URL
    try:
        body = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if payload.get("node_id"):
            headers["X-Node-Id"] = payload["node_id"]
        req = urllib.request.Request(
            f"{INGEST_URL.rstrip('/')}/api/approvals/request",
            data=body, headers=headers, method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            err_body = ""
        log.warning(f"approval request POST failed: HTTP {e.code} — {err_body}")
        return None
    except Exception as e:
        log.warning(f"approval request POST failed: {e}")
        return None


def _poll_decision(api_key: str, approval_id: str, timeout_s: int) -> str:
    """Poll cloud for the decision. Returns one of: approved/denied/timeout/error."""
    import urllib.request
    deadline = time.time() + timeout_s + 5  # 5 s grace past policy expiry
    last_status = "pending"
    while time.time() < deadline:
        try:
            from clawmetry.sync import INGEST_URL
            req = urllib.request.Request(
                f"{INGEST_URL.rstrip('/')}/api/approvals/{approval_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                last_status = data.get("status", "pending")
                if last_status in ("approved", "denied", "timeout", "expired"):
                    return last_status
        except Exception as e:
            log.debug(f"poll error (will retry): {e}")
        time.sleep(_POLL_INTERVAL_SEC)
    return last_status if last_status != "pending" else "timeout"


def _kill_session(session_id: Optional[str]) -> bool:
    """Best-effort kill of an OpenClaw session via the gateway WebSocket RPC."""
    if not session_id:
        return False
    try:
        # Late import to avoid pulling Flask into the daemon. helpers/gateway
        # is the OSS package's gateway WS client.
        import importlib.util as _ilu, sys as _s, os as _o
        try:
            import clawmetry as _cm
            oss_root = _o.path.dirname(_o.path.dirname(_cm.__file__))
        except Exception:
            return False
        helpers_path = _o.path.join(oss_root, "helpers", "gateway.py")
        if not _o.path.isfile(helpers_path):
            return False
        if "helpers.gateway" not in _s.modules:
            spec = _ilu.spec_from_file_location("_oss_gw_for_kill", helpers_path)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
        else:
            mod = _s.modules["helpers.gateway"]
        rpc = getattr(mod, "_gw_ws_rpc", None)
        if not rpc:
            return False
        # OpenClaw's session-kill RPC name varies: try a few
        for method in ("sessions_kill", "session_kill", "kill_session"):
            try:
                r = rpc(method, {"sessionId": session_id})
                if r is not None:
                    log.info(f"killed session {session_id} via {method}")
                    return True
            except Exception:
                continue
        return False
    except Exception as e:
        log.warning(f"kill_session({session_id}) failed: {e}")
        return False


# ── Public entry point: process one toolCall event ────────────────────────


def process_tool_call(api_key: str, node_id: str, session_id: Optional[str],
                       tool_call_id: str, tool_name: str, args: dict,
                       policies: Optional[list[dict]] = None) -> dict:
    """Check a fresh toolCall against active policies and (if matched) request
    a cloud-mediated approval.

    Blocks for up to policy.timeout seconds while waiting for the decision.
    Returns: {decision: approved|denied|timeout|no_policy|error,
              policy: <name or None>, killed: bool}
    """
    if policies is None:
        policies = load_policies()
    if not policies:
        return {"decision": "no_policy", "policy": None, "killed": False}
    policy = match_policy(policies, tool_name, args)
    if not policy:
        return {"decision": "no_policy", "policy": None, "killed": False}
    # Dedup
    key = tool_call_id or f"{session_id}:{int(time.time()*1000)}"
    with _in_flight_lock:
        if key in _in_flight:
            return _in_flight[key]
        _in_flight[key] = {"decision": "pending", "policy": policy["name"], "killed": False}

    cmd_preview = _extract_command(tool_name, args)[:140]
    log.info(f"[approval] policy='{policy['name']}' tool={tool_name} "
             f"cmd={cmd_preview!r} session={session_id}")

    approval_id = uuid.uuid4().hex
    req = {
        "id": approval_id,
        "node_id": node_id,
        "session_id": session_id,
        "tool_name": tool_name,
        "args": args,
        "context": f"Policy '{policy['name']}' fired on {tool_name}: {cmd_preview}",
        "policy_name": policy["name"],
        "timeout": policy["timeout"],
    }
    resp = _post_approval_request(api_key, req)
    if not resp:
        # Cloud unreachable — fail-open by default (don't block the agent)
        result = {"decision": "error", "policy": policy["name"], "killed": False}
        with _in_flight_lock:
            _in_flight[key] = result
        return result

    decision = _poll_decision(api_key, approval_id, policy["timeout"])
    if decision == "timeout" or decision == "expired":
        # Apply on_timeout
        decision = policy["on_timeout"]
    killed = False
    if decision == "denied":
        killed = _kill_session(session_id)
    result = {"decision": decision, "policy": policy["name"], "killed": killed,
              "approval_id": approval_id}
    log.info(f"[approval] {approval_id} → {decision}, killed={killed}")
    with _in_flight_lock:
        _in_flight[key] = result
    return result


# ── Watcher: scan unified DuckDB event store for new toolCalls ────────────
#
# The watermark is the most recent event ts (ISO-8601 string) we've examined
# AND completely processed. Persisted in ``~/.clawmetry/sync-state.json``
# under the key ``approvals_last_check_ts`` so a daemon restart doesn't
# re-evaluate already-decided approvals.
#
# We deliberately store/compare ``ts`` as a string. Every adapter ingests its
# event timestamps as strings (see ``clawmetry/local_store.py`` schema) and
# DuckDB's ``ORDER BY ts`` sort is lexicographic on that VARCHAR column.
# Lexicographic sort on properly-padded ISO-8601 timestamps is the same as
# chronological — that's the whole point of the format. Mixing in a numeric
# epoch would break the comparison.

# In-memory mirror of the persisted watermark, primed lazily on first
# iteration. ``None`` → not yet read from disk.
#
# ``last_check_ts`` is an ISO-8601 timestamp string. We query
# ``query_events(since=last_check_ts)`` which uses ``ts >= since``
# (inclusive). To prevent an event whose ``ts`` exactly equals
# ``last_check_ts`` from being re-processed on every iteration, we also
# track ``seen_ids_at_boundary`` — the set of event ids we've already
# dispatched at the current watermark ts. The set is reset whenever the
# watermark advances to a strictly newer ts.
_state: dict = {
    "last_check_ts": None,        # Optional[str]
    "seen_ids_at_boundary": set(),  # set[str]
}
_state_lock = threading.Lock()

# Issue #1343 Phase 2 — event-driven kick.
#
# Today the watcher_loop polls every 2 s. That's wasted work when the agent
# is idle, AND it means a tool_call event sitting in DuckDB waits up to 2 s
# before the policy engine sees it. Real fix: any code that ingests a
# ``tool_call`` event (sync.py mappers, gateway tap, claude_code adapter)
# calls ``watcher_kick()`` after the row lands; the watcher_loop wakes
# immediately and processes.
#
# Kept as a separate sentinel so multiple kicks coalesce into one wakeup —
# ingesting 50 tool_calls in a burst should not 50× trigger watch_iteration.
_kick_event = threading.Event()


def watcher_kick():
    """Wake the policy watcher from its current sleep so it processes
    queued tool_call events immediately. Safe to call from any thread; calls
    coalesce until the watcher consumes them.

    Callers: sync.py mappers, gateway tap, claude_code adapter, anywhere
    a fresh ``tool_call`` row lands in the local DuckDB. No-op when the
    watcher isn't running.
    """
    _kick_event.set()

# Where the watermark lives on disk. Co-located with the daemon's other state
# (``sync-state.json``) so an ops engineer who pokes around ``~/.clawmetry``
# doesn't have to learn a second file. We use the same key namespace the
# sync daemon uses (separate top-level key, no collision).
_STATE_PATH = Path.home() / ".clawmetry" / "sync-state.json"
_STATE_KEY = "approvals_last_check_ts"
# Companion key: the set of event ids we've already dispatched at the
# watermark ts. Persisted alongside the watermark so a daemon restart
# doesn't replay a boundary event that's already been processed (the
# events table's ``ts >= since`` filter is inclusive).
_STATE_KEY_SEEN = "approvals_seen_ids_at_boundary"

# Recognised "this content block is a tool invocation" types. Both flavours
# coexist in the wild because adapters mirror their underlying agent's wire
# format:
#   * OpenClaw / Claude Agent SDK     → ``toolCall``  +  ``arguments``
#   * Claude Code / Anthropic Messages → ``tool_use`` +  ``input``
# The watcher tolerates either. ``process_tool_call`` itself is shape-agnostic
# (it takes a parsed args dict).
_TOOL_BLOCK_TYPES = ("toolCall", "tool_use")


def _read_persisted_watermark() -> tuple[Optional[str], set[str]]:
    """Read the persisted watermark + boundary-id set from sync-state.json.

    Returns ``(ts, seen_ids)``. ``ts`` is None if the file or key is missing
    or unreadable; ``seen_ids`` is empty in the same cases. Never raises —
    a corrupt state file must not stop the watcher from running, only
    forces a one-time replay."""
    try:
        if not _STATE_PATH.exists():
            return None, set()
        with _STATE_PATH.open("r", encoding="utf-8") as fh:
            blob = json.load(fh)
        v = blob.get(_STATE_KEY)
        ts = v if isinstance(v, str) and v else None
        ids_raw = blob.get(_STATE_KEY_SEEN) or []
        ids = {s for s in ids_raw if isinstance(s, str)}
        return ts, ids
    except Exception as e:
        log.debug(f"approvals: could not read watermark from {_STATE_PATH}: {e}")
        return None, set()


def _persist_watermark(ts: str, seen_ids: set[str]) -> None:
    """Atomically update the watermark + boundary-id set in sync-state.json.
    Reads the existing blob (so we don't clobber sibling keys owned by
    sync.py) and writes back. Never raises — losing one watermark write
    means at most a re-replay on the next restart, which is benign because
    ``_in_flight`` deduplicates."""
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        blob: dict = {}
        if _STATE_PATH.exists():
            try:
                with _STATE_PATH.open("r", encoding="utf-8") as fh:
                    blob = json.load(fh) or {}
            except Exception:
                blob = {}
        blob[_STATE_KEY] = ts
        # Cap the persisted set: a single ts shouldn't accumulate more than
        # a few dozen ids in practice, but a buggy adapter could spam the
        # same ts. 1000 is generous and bounds the on-disk size.
        blob[_STATE_KEY_SEEN] = sorted(seen_ids)[:1000]
        tmp_path = _STATE_PATH.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(blob, fh, indent=2)
        os.replace(tmp_path, _STATE_PATH)
    except Exception as e:
        log.debug(f"approvals: could not persist watermark to {_STATE_PATH}: {e}")


def _extract_tool_blocks(row: dict) -> list[tuple[str, str, dict]]:
    """Walk a single events-table row and return ``(tool_call_id, tool_name,
    args)`` for every tool-invocation content block found.

    The ``data`` column is the raw transcript event dict (see
    ``sync._local_ingest_session_batch``). Shape varies by adapter:

      OpenClaw / Hermes / Claude Agent SDK:
        data = {type: "message", message: {role: "assistant",
                content: [{type: "toolCall", id, name, arguments}, …]}}

      Claude Code / Anthropic Messages:
        data = {type: "message", message: {role: "assistant",
                content: [{type: "tool_use", id, name, input}, …]}}

    Some adapters (notably the relay path) flatten ``message`` onto the top
    level, e.g. ``{role: "assistant", content: [...]}``. Handle both.
    Adapters that emit one event per tool invocation (instead of nested
    inside an assistant message) put the toolCall block at the top level —
    handle that too. All branches are tolerant: bad/missing keys just
    yield nothing.
    """
    out: list[tuple[str, str, dict]] = []
    data = row.get("data")
    if not isinstance(data, dict):
        return out
    # Case A: ``data.message.content[]`` (assistant turn carries toolCalls)
    msg = data.get("message")
    if isinstance(msg, dict):
        # Filter to assistant-role messages so we don't fire on tool_result
        # blocks coming back from the user side (which carry the same
        # block type names in some transcript formats).
        if msg.get("role") in (None, "assistant"):
            for blk in msg.get("content") or []:
                if isinstance(blk, dict) and blk.get("type") in _TOOL_BLOCK_TYPES:
                    out.append((
                        str(blk.get("id") or ""),
                        str(blk.get("name") or ""),
                        blk.get("arguments") or blk.get("input") or {},
                    ))
    # Case B: ``data.content[]`` (flattened — no nested message)
    if not out and isinstance(data.get("content"), list):
        if data.get("role") in (None, "assistant"):
            for blk in data["content"]:
                if isinstance(blk, dict) and blk.get("type") in _TOOL_BLOCK_TYPES:
                    out.append((
                        str(blk.get("id") or ""),
                        str(blk.get("name") or ""),
                        blk.get("arguments") or blk.get("input") or {},
                    ))
    # Case C: ``data`` IS the toolCall block (one-event-per-tool emitters)
    if not out and data.get("type") in _TOOL_BLOCK_TYPES:
        out.append((
            str(data.get("id") or ""),
            str(data.get("name") or ""),
            data.get("arguments") or data.get("input") or {},
        ))
    return out


def _query_new_events(since: Optional[str], limit: int) -> list[dict]:
    """Fetch candidate event rows from the local store since ``since`` (ts).

    ``query_events`` accepts only one ``event_type`` filter at a time, but
    different adapters ingest the same conceptual "assistant turn" event
    under different ``event_type`` strings (OpenClaw uses ``"message"``;
    some Anthropic-shape adapters use ``"assistant"``). Issue both queries
    and merge. Cost is negligible — both are indexed by
    ``idx_events_type_ts``.
    """
    from clawmetry import local_store
    try:
        store = local_store.get_store(read_only=True)
    except Exception as e:
        # Daemon may have closed the store, or DuckDB optional dep missing
        # in a pure-OSS install. Either way the watcher should no-op rather
        # than crash the loop.
        log.debug(f"approvals: local_store unavailable ({e})")
        return []
    rows: list[dict] = []
    for et in ("message", "assistant"):
        try:
            rows.extend(store.query_events(event_type=et, since=since, limit=limit))
        except Exception as e:
            log.debug(f"approvals: query_events({et}) failed: {e}")
    return rows


def watch_iteration(api_key: str, node_id: str,
                    policies: Optional[list[dict]] = None) -> int:
    """One pass over the unified event store. Returns count of toolCalls
    dispatched to ``process_tool_call`` (each in its own thread).

    Re-entrancy: the watermark moves forward only AFTER all matching rows
    in this pass have been spawned. ``query_events(since=…)`` uses ``ts >=
    since`` (inclusive), so on the next iteration we may re-see the row at
    the boundary timestamp; the per-tool-call dedup in ``process_tool_call``
    (``_in_flight`` keyed by tool_call_id) absorbs the duplicate without a
    second cloud round-trip.
    """
    if policies is None:
        policies = load_policies()
    if not policies:
        return 0

    # Lazy-prime the watermark from disk on first iteration. Subsequent
    # iterations use the in-memory copy.
    with _state_lock:
        if _state["last_check_ts"] is None:
            persisted_ts, persisted_ids = _read_persisted_watermark()
            # First-ever start: anchor to "now" so we don't replay the entire
            # event history on a fresh install. ISO-8601 with "Z" suffix to
            # match the format adapters emit.
            if persisted_ts is None:
                persisted_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                _persist_watermark(persisted_ts, set())
            _state["last_check_ts"] = persisted_ts
            _state["seen_ids_at_boundary"] = persisted_ids
        since = _state["last_check_ts"]
        seen_at_boundary: set[str] = set(_state["seen_ids_at_boundary"])

    # ``limit=500`` matches the PRD spec. At 2 s polling cadence that's a
    # 250 toolCalls/sec ceiling, well above any realistic agent throughput.
    rows = _query_new_events(since=since, limit=500)
    if not rows:
        return 0

    processed = 0
    max_seen_ts = since
    new_seen_at_boundary: set[str] = set(seen_at_boundary)
    for row in rows:
        ts = row.get("ts")
        eid = row.get("id")
        # Skip rows we've already dispatched at the boundary. ``query_events``
        # is inclusive on ``since`` (ts >= since), so without this filter we'd
        # re-fire on every poll for any event whose ts equals our watermark.
        if isinstance(ts, str) and ts == since and eid in seen_at_boundary:
            continue
        if isinstance(ts, str) and (max_seen_ts is None or ts > max_seen_ts):
            max_seen_ts = ts
        sid = row.get("session_id") or ""
        row_blocks = _extract_tool_blocks(row)
        # Even if a row had no toolCall blocks we still mark it as "seen at
        # this boundary" — otherwise the next poll would keep re-extracting
        # the same plain assistant message until a later event nudges the
        # watermark forward.
        if isinstance(ts, str) and ts == since and isinstance(eid, str):
            new_seen_at_boundary.add(eid)
        for tool_call_id, tool_name, args in row_blocks:
            if not tool_name:
                # No tool name → no policy can match. Skip rather than
                # bother process_tool_call.
                continue
            # Run in a background thread so a long approval timeout
            # doesn't stall the watcher loop.
            t = threading.Thread(
                target=process_tool_call,
                args=(api_key, node_id, sid, tool_call_id, tool_name,
                      args if isinstance(args, dict) else {}, policies),
                daemon=True,
            )
            t.start()
            processed += 1

    # Advance the watermark and persist. We move it forward whether or not
    # any toolCalls fired — the goal is to avoid re-scanning rows whose
    # timestamp is already in our rear-view mirror, even when none of them
    # were assistant-with-toolCall events. When the watermark advances to a
    # strictly newer ts, the boundary-id set is reset (those older events
    # are now in the rear-view and can't be re-seen with ts >= since).
    advanced = isinstance(max_seen_ts, str) and max_seen_ts != since
    with _state_lock:
        if advanced:
            _state["last_check_ts"] = max_seen_ts
            # Anything at the new boundary ts is captured here — repopulate
            # from this iteration's rows so we don't redispatch them on the
            # next poll (still within the inclusive ``ts >= since`` window).
            _state["seen_ids_at_boundary"] = {
                str(r.get("id")) for r in rows
                if isinstance(r.get("ts"), str) and r.get("ts") == max_seen_ts
                and r.get("id") is not None
            }
        else:
            _state["seen_ids_at_boundary"] = new_seen_at_boundary
        snapshot_ts = _state["last_check_ts"]
        snapshot_ids = set(_state["seen_ids_at_boundary"])
    # Persist on every successful iteration. Cheap (single small JSON file)
    # and means a daemon crash mid-poll loses at most the events from this
    # iteration — bounded by limit=500.
    if isinstance(snapshot_ts, str):
        _persist_watermark(snapshot_ts, snapshot_ids)

    return processed


def watcher_loop(api_key: str, node_id: str,
                 interval_sec: float = 2.0, stop_event: Optional[threading.Event] = None):
    """Long-running loop. Reloads policies on disk every iteration so users
    don't need to restart the daemon to add/remove rules.

    Phase 2 (#1343): the inter-iteration sleep now uses ``_kick_event.wait()``
    instead of ``time.sleep()``. ``interval_sec`` becomes the FALLBACK
    heartbeat — the watcher still wakes on schedule even if nothing kicked
    it (defends against a kick caller bug, and gives policies-on-disk
    reloads their guaranteed cadence). Any caller that ingests a
    ``tool_call`` event can call ``watcher_kick()`` to wake immediately;
    p99 detection latency drops from interval_sec → ~0 ms in the wired
    paths.
    """
    log.info(f"approvals watcher started (kick + {interval_sec}s heartbeat) for node {node_id}")
    while True:
        if stop_event and stop_event.is_set():
            log.info("approvals watcher stop signal received")
            return
        try:
            policies = load_policies(api_key=api_key)
            n = watch_iteration(api_key, node_id, policies=policies)
            if n:
                log.debug(f"approvals: scanned {n} new toolCalls")
        except Exception as e:
            log.warning(f"approvals watcher iteration error: {e}")
        # Wait for kick OR fallback heartbeat. Clear before re-checking so
        # we don't process the same kick twice.
        _kick_event.wait(timeout=interval_sec)
        _kick_event.clear()
