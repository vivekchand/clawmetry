"""clawmetry/approvals.py — cloud-mediated approval policy engine.

Watches the unified DuckDB event store (``clawmetry/local_store.py``) for
tool calls that match a user-defined approval policy. When a match fires:

  1. POST the request to ClawMetry cloud (`/api/approvals/request`)
  2. Notify a human (cloud handles delivery — Slack/email/browser link)
  3. Poll cloud (`/api/approvals/<id>`) every 3 s up to policy.timeout
  4. On `denied` → abort the agent: gateway `sessions_kill(session_id)` for
     OpenClaw sessions, the pid-based `process_control.kill_session` engine
     (same one the Stop button uses) for family runtimes
     (claude_code/codex/goose/opencode/aider — ids like `claude_code:UUID`)
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
    ``approvals_last_ingest_ms`` watermark (the events table's INGEST
    stamp, not the event ts — see the watermark-race note above
    ``watch_iteration``) persisted in ``~/.clawmetry/sync-state.json``.
    The watermark survives daemon restarts, so already-decided approvals
    are not re-evaluated.
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

# Harness-agnostic tool categories. Approval policies are authored against
# OpenClaw's tool names (``exec``, ``read``, …), but other harnesses emit the
# SAME semantic tool under a different name — claude-cli/Claude Code calls the
# shell ``Bash``, Codex ``shell``, etc. Without this map a policy with
# ``tool: exec`` silently never matches a ``Bash`` toolCall, so no approval
# ever fires (the recurring "I toggled rules but never see a pending
# approval" bug). Map both sides to a canonical category before comparing.
_TOOL_CANON = {}
for _canon, _aliases in {
    "exec": ["exec", "bash", "sh", "shell", "zsh", "fish", "powershell", "pwsh",
             "cmd", "command", "run", "run_command", "run_terminal_cmd",
             "terminal", "execute", "shell_command", "bashtool"],
    "read": ["read", "cat", "view", "open", "read_file", "get_file", "fs_read"],
    "write": ["write", "edit", "multiedit", "str_replace", "str_replace_editor",
              "create", "apply_patch", "write_file", "fs_write"],
    "web": ["web_fetch", "webfetch", "fetch", "curl", "wget", "http",
            "web_search", "websearch", "browser", "browse"],
    "search": ["grep", "glob", "ls", "find", "search", "memory_search"],
}.items():
    for _a in _aliases:
        _TOOL_CANON[_a] = _canon


def _canonical_tool(name: str) -> str:
    """Map a harness-specific tool name to its canonical category (or itself)."""
    return _TOOL_CANON.get((name or "").strip().lower(), (name or "").strip().lower())


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
        # Harness-agnostic tool match: a policy authored for ``exec`` matches a
        # ``Bash`` / ``shell`` toolCall (see _canonical_tool). Falls back to a
        # plain case-insensitive compare when neither side maps to a category.
        if p.get("tool") and _canonical_tool(tool_name) != _canonical_tool(p["tool"]):
            continue
        if p.get("command_regex") and not p["command_regex"].search(cmd):
            continue
        if p.get("command_not_regex") and p["command_not_regex"].search(cmd):
            continue
        if p.get("args_regex") and not p["args_regex"].search(args_str):
            continue
        return p
    return None


def replay_policy(policy: dict, rows: list[dict], max_samples: int = 20) -> dict:
    """Replay a CANDIDATE policy over historical tool-call events and report
    what it WOULD have paused — without creating approvals, blocking anything,
    or touching the cloud (the "eval before you enable" loop, CrabTrap-style).

    ``policy`` is a raw policy dict (same shape as ``policies.yml`` / the
    cloud builder rows — ``_compile_policy`` handles both). ``rows`` are
    events-table rows in ``query_events`` shape. Pure function: no store
    access and no network, so callers fetch rows however they like (route
    handlers go through the daemon proxy) and pass them in.

    Returns ``{ok, policy, scanned_events, scanned_tool_calls, matches,
    by_runtime, by_tool, samples}`` or ``{ok: False, error}`` on a bad policy.
    """
    compiled = _compile_policy(policy)
    if compiled is None:
        return {"ok": False, "error": "invalid policy (bad regex or shape)"}
    try:
        from clawmetry.sync import _runtime_of_session as _rt_of
    except Exception:  # pure-OSS edge: attribution degrades, replay still works
        def _rt_of(sid: str) -> str:
            return "openclaw"
    scanned_events = 0
    scanned_tool_calls = 0
    matches = 0
    by_runtime: dict[str, int] = {}
    by_tool: dict[str, int] = {}
    samples: list[dict] = []
    seen_rows: set = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        rid = row.get("id")
        if rid is not None:
            # The caller merges per-event_type queries; dedup row ids so an
            # event present in both result sets counts once.
            if rid in seen_rows:
                continue
            seen_rows.add(rid)
        data = row.get("data")
        if isinstance(data, str):
            # Cross-process transports may serialise the data column.
            try:
                row = dict(row, data=json.loads(data))
            except Exception:
                pass
        scanned_events += 1
        sid = row.get("session_id") or ""
        for _tcid, tool_name, args in _extract_tool_blocks(row):
            if not tool_name:
                continue
            args = args if isinstance(args, dict) else {}
            scanned_tool_calls += 1
            if match_policy([compiled], tool_name, args) is None:
                continue
            matches += 1
            rt = _rt_of(sid)
            by_runtime[rt] = by_runtime.get(rt, 0) + 1
            canon = _canonical_tool(tool_name)
            by_tool[canon] = by_tool.get(canon, 0) + 1
            if len(samples) < max_samples:
                samples.append({
                    "ts": row.get("ts"),
                    "session_id": sid,
                    "runtime": rt,
                    "tool": tool_name,
                    "command": _extract_command(tool_name, args)[:160],
                })
    return {
        "ok": True,
        "policy": compiled["name"],
        "scanned_events": scanned_events,
        "scanned_tool_calls": scanned_tool_calls,
        "matches": matches,
        "by_runtime": by_runtime,
        "by_tool": by_tool,
        "samples": samples,
    }


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


def _session_runtime(session_id: str) -> str:
    """Runtime of a session id (its ``<runtime>:`` prefix, else openclaw).

    Prefers ``sync._runtime_of_session`` (the canonical prefix map) and falls
    back to a plain prefix parse so this module keeps working if sync isn't
    importable (pure-OSS unit tests)."""
    try:
        from clawmetry.sync import _runtime_of_session
        return _runtime_of_session(session_id)
    except Exception:
        sid = session_id or ""
        i = sid.find(":")
        if i > 0:
            return sid[:i].lower()
        return "openclaw"


def _session_cwd_hint(session_id: str) -> str:
    """Best-effort working-directory hint for cwd-resolved runtimes
    (codex/goose/opencode/aider). Family adapters store the agent's cwd in
    the event ``workspace_id`` column when known; claude_code doesn't need
    it (per-pid session map). Never raises; '' when unknown."""
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        for r in store.query_events(session_id=session_id, limit=1):
            ws = r.get("workspace_id")
            if isinstance(ws, str) and (
                ws.startswith("/") or ws.startswith("~")
                or (len(ws) > 2 and ws[1] == ":")
            ):
                return ws
    except Exception:
        pass
    return ""


def _gateway_kill_session(session_id: str) -> bool:
    """Kill an OpenClaw session via the gateway WebSocket RPC."""
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
                    log.info(f"killed session {session_id} via gateway {method}")
                    return True
            except Exception:
                continue
        return False
    except Exception as e:
        log.warning(f"gateway kill_session({session_id}) failed: {e}")
        return False


def _process_control_kill(session_id: str, runtime: str) -> bool:
    """Kill a family-runtime session via the SAME pid-based engine the
    Stop button uses (``clawmetry/process_control.py``): resolve the session
    to its live pid (pid-reuse guarded), SIGTERM, escalate to SIGKILL of the
    descendant tree. Never raises."""
    try:
        from clawmetry import process_control as _pc
    except Exception as e:
        log.warning(f"process_control unavailable for kill of {session_id}: {e}")
        return False
    # The store keys family sessions as '<runtime>:<bare-id>'; the process
    # maps (e.g. ~/.claude/sessions/<pid>.json) key by the BARE id.
    bare = (session_id or "").rsplit(":", 1)[-1]
    cwd = _session_cwd_hint(session_id)
    try:
        res = _pc.kill_session(runtime, bare, cwd) or {}
    except Exception as e:
        log.warning(f"process_control kill_session({session_id}) raised: {e}")
        return False
    if res.get("ok"):
        log.info(f"killed session {session_id} via process_control "
                 f"(pid={res.get('pid')}, detail={res.get('detail')})")
        return True
    log.warning(f"process_control kill failed for {session_id}: "
                f"{res.get('detail') or res.get('reason') or 'unknown'}")
    return False


def _kill_session(session_id: Optional[str]) -> bool:
    """Best-effort kill of a denied session, runtime-aware.

    * OpenClaw sessions -> gateway WebSocket RPC (the historical path).
    * Family runtimes (claude_code / codex / goose / opencode / aider / ...,
      session ids like ``claude_code:UUID``) -> the pid-based
      ``process_control.kill_session`` engine the Stop button uses. The
      gateway does not know these sessions, so before 2026-07-02 a DENY
      logged ``killed=False`` and the denied agent KEPT RUNNING (live repro:
      approval 7d202307907a4f12bd8af5aa17c62c76).

    Fail-safe: if the primary mechanism fails we try the other one, and if
    neither works we return False (callers log the warning)."""
    if not session_id:
        return False
    runtime = _session_runtime(session_id)
    if runtime != "openclaw":
        if _process_control_kill(session_id, runtime):
            return True
        # Last resort: some wrapped setups register the session with the
        # gateway anyway. Harmless when it doesn't.
        return _gateway_kill_session(session_id)
    return _gateway_kill_session(session_id)


# ── Public entry point: process one toolCall event ────────────────────────


def process_tool_call(api_key: str, node_id: str, session_id: Optional[str],
                       tool_call_id: str, tool_name: str, args: dict,
                       policies: Optional[list[dict]] = None) -> dict:
    """Check a fresh toolCall against active policies and (if matched) request
    a cloud-mediated approval.

    Blocks for up to policy.timeout seconds while waiting for the decision.
    A policy with ``action: monitor`` never blocks: it records a
    ``simulated`` approval row (dry-run) and returns immediately.
    Returns: {decision: approved|denied|timeout|monitored|no_policy|error,
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

    if (policy.get("action") or "") == "monitor":
        # Dry-run mode: record what WOULD have paused so the audit feed shows
        # it, but never block the agent, never round-trip the cloud, never
        # kill. Lets a user trial a rule live before flipping it to
        # require_approval.
        try:
            import hashlib as _hl
            from clawmetry import local_store as _lsm
            _lsm.get_store().ingest_approval({
                "id": approval_id,
                "owner_hash": _hl.sha256((api_key or "").encode()).hexdigest(),
                "requestor_session_id": session_id,
                "action": f"{tool_name}: {cmd_preview}",
                "args": args,
                "status": "simulated",
                "decision_reason": (f"monitor mode: policy '{policy['name']}' "
                                    "would have paused this"),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
        except Exception as _me:
            log.debug("monitor-mode approval persist failed: %s", _me)
        try:
            from clawmetry import audit as _audit
            _audit.audit_event(
                "approval.simulated",
                actor="policy",
                target=tool_name,
                result="monitored",
                source="approvals",
                metadata={
                    "approval_id": approval_id,
                    "policy": policy["name"],
                    "session_id": session_id,
                    "command": cmd_preview,
                },
            )
        except Exception:
            pass
        result = {"decision": "monitored", "policy": policy["name"],
                  "killed": False, "approval_id": approval_id}
        log.info(f"[approval] {approval_id} → monitored (dry-run, not blocked)")
        with _in_flight_lock:
            _in_flight[key] = result
        return result

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
    # Persist to local DuckDB so the daemon's heartbeat cache_push surfaces
    # this in the cloud Approvals inbox — which reads the
    # approvals:{owner_hash}:queue Redis key, NOT the legacy
    # _post_approval_request endpoint. Without this the watcher fired but the
    # inbox stayed empty ("toggled rules but never see a pending approval").
    try:
        import hashlib as _hl
        from clawmetry import local_store as _lsa
        _lsa.get_store().ingest_approval({
            "id": approval_id,
            "owner_hash": _hl.sha256((api_key or "").encode()).hexdigest(),
            "requestor_session_id": session_id,
            "action": f"{tool_name}: {cmd_preview}",
            "args": args,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except Exception as _ae:
        log.debug("approval DuckDB persist failed: %s", _ae)

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
    # Mirror the resolution into DuckDB so the approval leaves the cloud
    # pending queue (the next cache_push won't re-surface it as pending).
    try:
        from clawmetry import local_store as _lsa2
        _lsa2.get_store().update_approval_decision(
            approval_id, decision, "cloud", None)
    except Exception as _ue:
        log.debug("approval decision update failed: %s", _ue)
    result = {"decision": decision, "policy": policy["name"], "killed": killed,
              "approval_id": approval_id}
    # Enterprise audit-log producer — record the approval outcome (approve /
    # deny / timeout-default) with who/what/where. Never raises into the
    # policy path.
    try:
        from clawmetry import audit as _audit
        _audit.audit_event(
            "approval.decision",
            actor="cloud",
            target=tool_name,
            result=decision,
            source="approvals",
            metadata={
                "approval_id": approval_id,
                "policy": policy["name"],
                "session_id": session_id,
                "killed": killed,
                "command": cmd_preview,
            },
        )
    except Exception:
        pass
    log.info(f"[approval] {approval_id} → {decision}, killed={killed}")
    with _in_flight_lock:
        _in_flight[key] = result
    return result


# ── Watcher: scan unified DuckDB event store for new toolCalls ────────────
#
# The watermark is the most recent INGEST stamp (``events.created_at``,
# epoch-ms set at INSERT time) we've examined AND completely processed.
# Persisted in ``~/.clawmetry/sync-state.json`` under
# ``approvals_last_ingest_ms`` so a daemon restart doesn't re-evaluate
# already-decided approvals.
#
# Why ingest time and NOT the event's own ``ts`` (the pre-2026-07-02
# design): family adapters (claude_code / codex / cursor / ...) can ingest a
# session MINUTES after its events' timestamps (live repro: a brand-new
# project dir ingested ~4 min late). By then newer events had already
# advanced a ts-based watermark past them, so those tool calls were NEVER
# evaluated — approval-gated actions silently sailed through. ``created_at``
# is monotone with insertion (up to a few seconds of flush-retry skew,
# covered by ``_INGEST_LOOKBACK_MS`` below), so a cursor on it sees every
# row when it LANDS, no matter how stale its ``ts`` is.

# In-memory mirror of the persisted watermark, primed lazily on first
# iteration. ``last_ingest_ms is None`` → not yet read from disk.
#
# ``seen_recent_ids`` maps event id -> created_at (ms) for every row we've
# already dispatched whose stamp is still within the lookback window. The
# window re-scan (``created_at >= watermark - lookback``) exists to catch
# rows whose stamp predates their COMMIT (ring rows are stamped before the
# writer lock is taken; flush retries add seconds); this set is what makes
# that re-scan dispatch each row exactly once. Pruned every iteration to
# ids still inside the window, so it stays bounded.
_state: dict = {
    "last_ingest_ms": None,     # Optional[int]  (epoch-ms, ingest stamp)
    "seen_recent_ids": {},      # dict[str, int]  event id -> created_at ms
    "resume_cursor": None,      # Optional[tuple[int, Optional[str]]] — keyset after page cap
}
_state_lock = threading.Lock()

# How far behind the ingest watermark each iteration re-scans (with id-level
# dedup) to absorb created_at-stamp-vs-commit skew. Flush retries cap out
# around ~3 s; 60 s is a generous, still-bounded margin.
_INGEST_LOOKBACK_MS = int(os.environ.get(
    "CLAWMETRY_APPROVALS_INGEST_LOOKBACK_MS", "60000") or 60000)
# Keyset pages fetched per iteration (500 rows each). Bounds one iteration's
# work; anything beyond is picked up by the next 2 s poll.
_MAX_PAGES_PER_ITERATION = 4
# Hard caps on the dedup set (in-memory / persisted) so a pathological burst
# can't bloat memory or the on-disk state file.
_SEEN_IDS_MEM_CAP = 20000
_SEEN_IDS_DISK_CAP = 5000

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
# Ingest-time (created_at, epoch-ms) watermark. Replaces the legacy
# ``approvals_last_check_ts`` event-ts watermark (see the watermark-race
# note above); a stale legacy key in the file is simply ignored.
_STATE_KEY = "approvals_last_ingest_ms"
# Companion key: event id -> created_at (ms) for rows already dispatched
# inside the lookback window. Persisted alongside the watermark so a daemon
# restart doesn't replay a window row that's already been processed.
_STATE_KEY_SEEN = "approvals_seen_ingest_ids"

# Recognised "this content block is a tool invocation" types. Both flavours
# coexist in the wild because adapters mirror their underlying agent's wire
# format:
#   * OpenClaw / Claude Agent SDK     → ``toolCall``  +  ``arguments``
#   * Claude Code / Anthropic Messages → ``tool_use`` +  ``input``
# The watcher tolerates either. ``process_tool_call`` itself is shape-agnostic
# (it takes a parsed args dict).
_TOOL_BLOCK_TYPES = ("toolCall", "tool_use")

# Event types that can carry tool invocations. The watcher
# (``_query_new_events``) and the replay route (``routes/policy.py``) MUST
# query the same list or they drift: the family adapters (claude_code,
# codex, cursor, …) ingest one row PER tool call under
# ``event_type='tool_call'`` with an OpenAI-style ``data.tool_calls`` array
# — a type the watcher historically never queried, so approval policies
# silently never fired for those runtimes (found 2026-06-10 by replaying a
# policy over the live store: 2,539 tool_call rows in 3 days, 0 visible to
# the watcher).
_TOOL_EVENT_TYPES = ("message", "assistant", "tool_call")


def _read_persisted_watermark() -> "tuple[Optional[int], dict[str, int]]":
    """Read the persisted ingest watermark + dispatched-id map from
    sync-state.json.

    Returns ``(watermark_ms, seen_ids)``. ``watermark_ms`` is None if the
    file or key is missing or unreadable; ``seen_ids`` is empty in the same
    cases. Never raises — a corrupt state file must not stop the watcher
    from running, only forces a one-time re-anchor."""
    try:
        if not _STATE_PATH.exists():
            return None, {}
        with _STATE_PATH.open("r", encoding="utf-8") as fh:
            blob = json.load(fh)
        v = blob.get(_STATE_KEY)
        wm = int(v) if isinstance(v, (int, float)) and v > 0 else None
        ids_raw = blob.get(_STATE_KEY_SEEN) or {}
        ids: dict[str, int] = {}
        if isinstance(ids_raw, dict):
            for k, c in ids_raw.items():
                if isinstance(k, str) and isinstance(c, (int, float)):
                    ids[k] = int(c)
        return wm, ids
    except Exception as e:
        log.debug(f"approvals: could not read watermark from {_STATE_PATH}: {e}")
        return None, {}


def _persist_watermark(watermark_ms: int, seen_ids: "dict[str, int]") -> None:
    """Atomically update the ingest watermark + dispatched-id map in
    sync-state.json. Reads the existing blob (so we don't clobber sibling
    keys owned by sync.py) and writes back. Never raises — losing one
    watermark write means at most a re-replay on the next restart, which is
    benign because the persisted id map + ``_in_flight`` deduplicate."""
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        blob: dict = {}
        if _STATE_PATH.exists():
            try:
                with _STATE_PATH.open("r", encoding="utf-8") as fh:
                    blob = json.load(fh) or {}
            except Exception:
                blob = {}
        blob[_STATE_KEY] = int(watermark_ms)
        # Cap the persisted map (newest stamps win) so a burst can't bloat
        # the on-disk state file.
        if len(seen_ids) > _SEEN_IDS_DISK_CAP:
            keep = sorted(seen_ids.items(), key=lambda kv: kv[1],
                          reverse=True)[:_SEEN_IDS_DISK_CAP]
            blob[_STATE_KEY_SEEN] = dict(keep)
        else:
            blob[_STATE_KEY_SEEN] = dict(seen_ids)
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
    # Case D: family adapters (claude_code / codex / cursor / …) ingest one
    # row per tool call under ``event_type='tool_call'`` with an OpenAI-style
    # array: ``data = {_runtime, role: "assistant", tool_name,
    # tool_calls: [{id, name, input}]}``. Args may be ``input`` /
    # ``arguments`` / ``args`` depending on the adapter.
    if not out and isinstance(data.get("tool_calls"), list):
        if data.get("role") in (None, "assistant"):
            for blk in data["tool_calls"]:
                if not isinstance(blk, dict):
                    continue
                name = blk.get("name") or data.get("tool_name")
                if not name:
                    continue
                args = blk.get("input") or blk.get("arguments") or blk.get("args") or {}
                out.append((
                    str(blk.get("id") or ""),
                    str(name),
                    args if isinstance(args, dict) else {},
                ))
    return out


def _query_new_events(created_after: int, after_id: Optional[str],
                      limit: int) -> list[dict]:
    """Fetch candidate event rows from the local store by INGEST order.

    One indexed keyset query covers all of ``_TOOL_EVENT_TYPES`` (the
    conceptual "assistant turn" lands under ``"message"`` / ``"assistant"``
    / one ``"tool_call"`` row per invocation depending on the adapter).
    Rows come back oldest-ingested first with their ``created_at`` stamp.
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
    try:
        return store.query_events_by_ingest(
            created_after=created_after, after_id=after_id,
            event_types=_TOOL_EVENT_TYPES, limit=limit)
    except Exception as e:
        log.debug(f"approvals: query_events_by_ingest failed: {e}")
        return []


def watch_iteration(api_key: str, node_id: str,
                    policies: Optional[list[dict]] = None) -> int:
    """One pass over the unified event store, in INGEST order. Returns the
    count of toolCalls dispatched to ``process_tool_call`` (each in its own
    thread).

    The cursor is ``events.created_at`` (insert stamp), NOT the event's own
    ``ts`` — a family session ingested minutes after its events' timestamps
    is still evaluated (the 2026-07-02 watermark race). Each iteration
    re-scans a bounded lookback window behind the watermark (indexed, never
    a full-table scan) to absorb stamp-vs-commit skew; ``seen_recent_ids``
    guarantees each row is dispatched exactly once across polls AND daemon
    restarts (it is persisted with the watermark). ``process_tool_call``'s
    ``_in_flight`` map dedups at the (session, tool_call_id) level as the
    final belt-and-braces, so an already-decided approval is never re-fired.
    """
    if policies is None:
        policies = load_policies()
    if not policies:
        return 0

    # Lazy-prime the watermark from disk on first iteration. Subsequent
    # iterations use the in-memory copy.
    with _state_lock:
        if _state["last_ingest_ms"] is None:
            persisted_ms, persisted_ids = _read_persisted_watermark()
            # First-ever start (or upgrade from the legacy ts watermark):
            # anchor to "now" so we don't replay the entire event history.
            # The lookback window below still covers anything ingested in
            # the last minute (e.g. during a daemon restart).
            if persisted_ms is None:
                persisted_ms = int(time.time() * 1000)
                _persist_watermark(persisted_ms, {})
            _state["last_ingest_ms"] = persisted_ms
            _state["seen_recent_ids"] = persisted_ids
        watermark = int(_state["last_ingest_ms"])
        seen: dict = dict(_state["seen_recent_ids"])
        resume_cursor = _state.get("resume_cursor")

    processed = 0
    max_ingest = watermark
    saw_rows = False
    # If the previous iteration hit the page cap, resume from where it stopped
    # so we advance past row 2,000 instead of rescanning the same first 2,000
    # rows forever (see #3558).  Otherwise start from the lookback window.
    if resume_cursor is not None:
        cursor_ca, cursor_id = resume_cursor
    else:
        cursor_ca = max(0, watermark - _INGEST_LOOKBACK_MS)
        cursor_id = None
    hit_page_cap = False
    for _page in range(_MAX_PAGES_PER_ITERATION):
        # ``limit=500`` per page matches the PRD spec; the page cap bounds
        # one iteration's work (the next 2 s poll picks up the rest).
        rows = _query_new_events(created_after=cursor_ca, after_id=cursor_id,
                                 limit=500)
        if not rows:
            break
        saw_rows = True
        for row in rows:
            eid = str(row.get("id") or "")
            ca = row.get("created_at")
            ca = int(ca) if isinstance(ca, (int, float)) else watermark
            if ca > max_ingest:
                max_ingest = ca
            # Exactly-once inside the lookback window: skip rows already
            # dispatched on a previous poll (or before a daemon restart —
            # the map is persisted alongside the watermark).
            if eid and eid in seen:
                continue
            # Mark every examined row (even without toolCall blocks) so the
            # window re-scan never re-extracts it.
            if eid:
                seen[eid] = ca
            sid = row.get("session_id") or ""
            for tool_call_id, tool_name, args in _extract_tool_blocks(row):
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
        if len(rows) < 500:
            break
        # Strict keyset continuation from the last row — pages always make
        # progress even when hundreds of rows share one millisecond stamp
        # (a single flush batch does).
        last = rows[-1]
        last_ca = last.get("created_at")
        cursor_ca = int(last_ca) if isinstance(last_ca, (int, float)) else cursor_ca
        cursor_id = str(last.get("id") or "")
    else:
        # All pages exhausted without a short final page: save the keyset
        # cursor so the next iteration resumes here instead of restarting
        # from the lookback window (#3558 page-cap starvation fix).
        hit_page_cap = True

    if not saw_rows:
        # Nothing to scan.  Clear any stale resume cursor so the next
        # iteration doesn't try to pick up mid-way through an empty window.
        if resume_cursor is not None:
            with _state_lock:
                _state["resume_cursor"] = None
        return 0

    # Advance the watermark, prune the dedup map to the new lookback window
    # (older rows can never be re-fetched), and persist. Cheap (single small
    # JSON file); a daemon crash mid-poll loses at most this iteration's
    # rows, which the persisted map + ``_in_flight`` absorb on replay.
    cutoff = max_ingest - _INGEST_LOOKBACK_MS
    seen = {i: c for i, c in seen.items() if c >= cutoff}
    if len(seen) > _SEEN_IDS_MEM_CAP:
        seen = dict(sorted(seen.items(), key=lambda kv: kv[1],
                           reverse=True)[:_SEEN_IDS_MEM_CAP])
    with _state_lock:
        _state["last_ingest_ms"] = max_ingest
        _state["seen_recent_ids"] = seen
        _state["resume_cursor"] = (cursor_ca, cursor_id) if hit_page_cap else None
        snapshot_ms = int(_state["last_ingest_ms"])
        snapshot_ids = dict(_state["seen_recent_ids"])
    _persist_watermark(snapshot_ms, snapshot_ids)

    return processed


# ── OpenClaw native exec-approval gate (2026-07-08) ─────────────────────────
# ClawMetry's own watcher is REACTIVE: it sees a tool_call only after the
# transcript records it, so a destructive `rm -rf` on an OpenClaw agent has
# already run by the time a policy could match (confirmed live 2026-07-08:
# rm -rf executed, dir gone, no approval fired — OpenClaw never emitted a
# matchable tool_call event either). The real fix is OpenClaw's OWN
# pre-execution gate: `openclaw exec-policy preset cautious` sets
# security=allowlist / ask=on-miss / askFallback=deny, so a non-allowlisted
# exec PAUSES before running and is denied if unanswered.
#
# We drive it from the daemon (not a cloud→host call): the daemon already
# runs inside the OpenClaw box and already fetches the cloud policies every
# 2s. When an enabled require-approval policy that covers exec is present we
# apply `cautious`; when none are, we restore `yolo` — but only when WE were
# the one who changed it (tracked in a small state file), so we never clobber
# a posture the operator set by hand. Best-effort; never raises into the loop.
_EXEC_POLICY_STATE = Path.home() / ".clawmetry" / "exec_policy_applied"


def _openclaw_env_and_bin():
    """Resolve the `openclaw` binary with an augmented PATH (the daemon runs
    under a minimal launchd/systemd PATH where node-shim CLIs aren't found —
    same gotcha cli.py handles). Returns (bin_path, env) or (None, env)."""
    import shutil
    extra = ["/usr/local/bin", "/opt/homebrew/bin",
             os.path.expanduser("~/.local/bin"), "/usr/bin"]
    env = os.environ.copy()
    env["PATH"] = ":".join(extra) + ":" + env.get("PATH", "")
    return shutil.which("openclaw", path=env["PATH"]), env


def _policies_want_exec_gate(policies) -> bool:
    """True when any active policy asks for approval on a shell/exec command.
    These are exactly the presets the UI ships (rm_rf, force_push, db, sudo,
    package installs, network, system-config) plus the tool-agnostic secrets
    rule — all `require_approval` and all covering `exec` (tool 'exec' or '')."""
    for p in policies or []:
        if not isinstance(p, dict):
            continue
        if (p.get("action") or "require_approval") != "require_approval":
            continue
        tool = (p.get("tool") or "").lower()
        if tool in ("", "exec", "shell", "bash"):
            return True
    return False


def _apply_openclaw_exec_preset(preset: str) -> bool:
    """Run `openclaw exec-policy preset <preset>` locally. Returns True on a
    clean apply. Never raises."""
    import subprocess
    ocbin, env = _openclaw_env_and_bin()
    if not ocbin:
        return False
    try:
        r = subprocess.run([ocbin, "exec-policy", "preset", preset, "--json"],
                           capture_output=True, text=True, timeout=60, env=env)
        if r.returncode != 0:
            log.warning("openclaw exec-policy preset %s failed: %s",
                        preset, (r.stderr or "")[-300:])
            return False
        log.info("openclaw exec-policy → %s (native pre-exec gate)", preset)
        return True
    except Exception as e:
        log.warning("openclaw exec-policy preset %s error: %s", preset, e)
        return False


def sync_openclaw_exec_policy(policies) -> None:
    """Align OpenClaw's native exec-approval posture with the active policies.
    Only touches OpenClaw when the desired posture CHANGES, and only restores
    `yolo` if a prior run was the one that set `cautious` (state file), so a
    hand-configured posture is never clobbered. No-op when openclaw isn't on
    this host."""
    ocbin, _ = _openclaw_env_and_bin()
    if not ocbin:
        return  # not an OpenClaw box — nothing to gate
    want = "cautious" if _policies_want_exec_gate(policies) else "yolo"
    try:
        prev = _EXEC_POLICY_STATE.read_text().strip() if _EXEC_POLICY_STATE.exists() else ""
    except Exception:
        prev = ""
    if want == prev:
        return  # already in the posture we last applied
    # Guard the restore: only relax to yolo if WE previously set cautious.
    # (Fresh install with no gate wanted + no prior state → don't force yolo
    # onto an operator who may have set deny-all by hand.)
    if want == "yolo" and prev != "cautious":
        return
    if _apply_openclaw_exec_preset(want):
        try:
            _EXEC_POLICY_STATE.parent.mkdir(parents=True, exist_ok=True)
            _EXEC_POLICY_STATE.write_text(want)
        except Exception:
            pass


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
            # Drive OpenClaw's native pre-execution gate from the same policy
            # set (the reactive watcher below can't PREVENT a command, only
            # catch it after the fact — see sync_openclaw_exec_policy).
            try:
                sync_openclaw_exec_policy(policies)
            except Exception as _pe:
                log.debug("exec-policy sync skipped: %s", _pe)
            n = watch_iteration(api_key, node_id, policies=policies)
            if n:
                log.debug(f"approvals: scanned {n} new toolCalls")
        except Exception as e:
            log.warning(f"approvals watcher iteration error: {e}")
        # Wait for kick OR fallback heartbeat. Clear before re-checking so
        # we don't process the same kick twice.
        _kick_event.wait(timeout=interval_sec)
        _kick_event.clear()
