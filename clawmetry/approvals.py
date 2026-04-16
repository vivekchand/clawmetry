"""clawmetry/approvals.py — cloud-mediated approval policy engine.

Watches the OpenClaw session JSONL stream for tool calls that match a
user-defined approval policy. When a match fires:

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

Design notes:
  * Stateless watcher — restartable any time, replays from current end-of-file
    and only processes new events. We track per-session high-water-mark to
    avoid double-firing on policy reload.
  * One in-flight approval per (session, tool_call_id). Multiple matches on
    the same call collapse into one request — important so a session that
    matches both "rm" AND "outside-tmp" policies doesn't get duplicate Slack
    pings.
  * NO HTTP retry storm — cloud round-trip uses the existing ``_post`` helper
    which already backs off + handles 429s.
  * Soft-fail in OSS-only mode (no cloud configured): log and pass through.
    The same code runs in pure-local installs without crashing.
"""
from __future__ import annotations

import os
import re
import json
import time
import uuid
import glob
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


def load_policies() -> list[dict]:
    """Load + compile policies from disk. Returns empty list when no file."""
    if not POLICIES_PATH.exists():
        return []
    try:
        raw = POLICIES_PATH.read_text(errors="replace")
        policies = _load_yaml(raw)
    except Exception as e:
        log.warning(f"failed to read {POLICIES_PATH}: {e}")
        return []
    compiled = []
    for p in policies:
        if not isinstance(p, dict):
            continue
        match = p.get("match") or {}
        try:
            cmd_re = match.get("command_regex")
            cmd_not_re = match.get("command_not_regex")
            compiled.append({
                "name": p.get("name") or "(unnamed)",
                "tool": (match.get("tool") or "").strip(),
                "command_regex": re.compile(cmd_re) if cmd_re else None,
                "command_not_regex": re.compile(cmd_not_re) if cmd_not_re else None,
                "args_regex": re.compile(match["args_regex"]) if match.get("args_regex") else None,
                "action": (p.get("action") or "require_approval").strip(),
                "timeout": int(p.get("timeout") or 60),
                "on_timeout": (p.get("on_timeout") or "deny").strip(),
            })
        except re.error as re_err:
            log.warning(f"policy '{p.get('name')}' has bad regex: {re_err}")
    if compiled:
        log.info(f"loaded {len(compiled)} approval policies from {POLICIES_PATH}")
    return compiled


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


# ── Watcher: scan session JSONL tail for new toolCalls ────────────────────


def _sessions_dir() -> Optional[str]:
    """Locate OpenClaw's sessions directory."""
    for cand in (
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ):
        if os.path.isdir(cand):
            return cand
    return None


# Per-file high-water-mark (byte offset) so we don't reprocess on restart
_file_offsets: dict[str, int] = {}


def watch_iteration(api_key: str, node_id: str,
                    policies: Optional[list[dict]] = None) -> int:
    """One pass over all session JSONLs. Returns count of toolCalls processed."""
    sd = _sessions_dir()
    if not sd:
        return 0
    if policies is None:
        policies = load_policies()
    if not policies:
        return 0
    processed = 0
    for fpath in glob.glob(os.path.join(sd, "*.jsonl")):
        if ".checkpoint." in fpath or ".deleted." in fpath:
            continue
        try:
            size = os.path.getsize(fpath)
            offset = _file_offsets.get(fpath, size)  # default: start at EOF
            if offset > size:
                offset = 0  # log rotated
            if offset == size:
                continue
            with open(fpath, "r", errors="replace") as fh:
                fh.seek(offset)
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if ev.get("type") != "message":
                        continue
                    msg = ev.get("message") or {}
                    if msg.get("role") != "assistant":
                        continue
                    for blk in msg.get("content") or []:
                        if not isinstance(blk, dict):
                            continue
                        if blk.get("type") != "toolCall":
                            continue
                        sid = os.path.basename(fpath).replace(".jsonl", "").split(".")[0]
                        # Run in a background thread so a long approval
                        # timeout doesn't stall the watcher loop.
                        t = threading.Thread(
                            target=process_tool_call,
                            args=(api_key, node_id, sid, blk.get("id", ""),
                                  blk.get("name", ""), blk.get("arguments") or {},
                                  policies),
                            daemon=True,
                        )
                        t.start()
                        processed += 1
                _file_offsets[fpath] = fh.tell()
        except Exception as e:
            log.debug(f"scan error on {fpath}: {e}")
    return processed


def watcher_loop(api_key: str, node_id: str,
                 interval_sec: float = 2.0, stop_event: Optional[threading.Event] = None):
    """Long-running loop. Reloads policies on disk every iteration so users
    don't need to restart the daemon to add/remove rules."""
    log.info(f"approvals watcher started (poll {interval_sec}s) for node {node_id}")
    while True:
        if stop_event and stop_event.is_set():
            log.info("approvals watcher stop signal received")
            return
        try:
            policies = load_policies()
            n = watch_iteration(api_key, node_id, policies=policies)
            if n:
                log.debug(f"approvals: scanned {n} new toolCalls")
        except Exception as e:
            log.warning(f"approvals watcher iteration error: {e}")
        time.sleep(interval_sec)
