"""OpenClawAdapter — thin wrapper around existing dashboard.py helpers.

This adapter does NOT re-implement OpenClaw session parsing. It delegates
to the long-standing helpers in ``dashboard.py`` via a late import, the
same way ``routes/*.py`` modules do. The point of this file is to expose
the existing OpenClaw observability surface through the unified
:class:`~clawmetry.adapters.base.AgentAdapter` interface, so the dashboard
treats OpenClaw exactly like any other agent.

Zero behavior change: when no other adapter is registered, the UI looks
identical to the pre-refactor dashboard.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time as _time
from typing import List, Optional, Set

from .base import AgentAdapter, Capability, DetectResult, Event, Session

logger = logging.getLogger("clawmetry.adapters.openclaw")

# NeMo Guardrails compact tool-catalog injects these three meta-tool names into
# the JSONL transcript when NEMOCLAW_TOOL_CATALOG is active. They are guardrail
# dispatches, not real agent actions; tag them so consumers can filter/style
# them separately from ordinary tool calls.
_NEMOCLAW_CATALOG_TOOLS: frozenset = frozenset({
    "tool_search",
    "tool_describe",
    "tool_call",
})


def _d():
    """Late import to avoid circular init with dashboard module."""
    import dashboard as _dash

    return _dash


def _gateway_live() -> bool:
    """True only if the OpenClaw gateway is actually up (pid alive or port
    18789 listening). Never raises."""
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    pid_file = os.path.join(home, "gateway", "gateway.pid")
    try:
        if os.path.exists(pid_file):
            with open(pid_file) as fh:
                pid = int((fh.read() or "0").strip())
            if pid > 0:
                os.kill(pid, 0)
                return True
    except (OSError, ValueError):
        pass
    try:
        import socket as _sock
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
        s.settimeout(0.2)
        rc = s.connect_ex(("127.0.0.1", 18789))
        s.close()
        return rc == 0
    except Exception:
        return False


def _real_install(sessions_dir: str) -> bool:
    """A genuine OpenClaw install signal, NOT the bare ~/.openclaw dir that
    ClawMetry itself creates as a scratch workspace. Any one of: the openclaw
    CLI/app, a gateway.pid, real session .jsonl files, or workspace markers."""
    import shutil as _shutil
    if _shutil.which("openclaw") or os.path.isdir("/Applications/OpenClaw.app"):
        return True
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    if os.path.exists(os.path.join(home, "gateway", "gateway.pid")):
        return True
    if sessions_dir and os.path.isdir(sessions_dir):
        try:
            if any(n.endswith(".jsonl") for n in os.listdir(sessions_dir)):
                return True
        except OSError:
            pass
    ws = os.path.join(home, "workspace")
    return any(os.path.exists(os.path.join(ws, m))
               for m in ("SOUL.md", "AGENTS.md", "MEMORY.md"))


def _model_router_fingerprint() -> dict:
    """Read the NemoClaw model-router source fingerprint (``git:<sha>``)
    written by harness onboarding to ``<venv>/.nemoclaw-source-fingerprint``
    (model-router.ts writeModelRouterInstalledFingerprint). Surfaces the
    install-provenance / version-drift signal on DetectResult.meta (#2608).

    Read-only and never raises. Returns ``{}`` when the file/venv is absent
    (plain OpenClaw or old NemoClaw installs), so the meta dict is unchanged.
    """
    venv = os.environ.get("NEMOCLAW_MODEL_ROUTER_VENV") or os.path.expanduser(
        os.path.join("~", ".nemoclaw", "model-router-venv"))
    fp_path = os.path.join(venv, ".nemoclaw-source-fingerprint")
    try:
        with open(fp_path, encoding="utf-8") as fh:
            raw = (fh.read() or "").strip()
        if not raw:
            return {}
        out = {"modelRouterFingerprint": raw}
        # raw looks like "git:<40hex>" / "gitlink:<40hex>" / "files:<hex>"
        if ":" in raw:
            kind, _, val = raw.partition(":")
            out["modelRouterFingerprintKind"] = kind
            if kind in ("git", "gitlink") and val:
                out["modelRouterSourceSha"] = val[:12]
        return out
    except (OSError, ValueError):
        return {}


def _model_router_liveness() -> dict:
    """Check whether the NemoClaw model-router proxy is currently running.

    Returns ``{}`` when NemoClaw is not installed (fingerprint file absent),
    so the caller's meta dict is unchanged on plain OpenClaw installs.
    Otherwise scans for a running ``model-router proxy`` process and returns
    ``{"modelRouterRunning": True, "modelRouterPort": <port>}`` when healthy,
    or ``{"modelRouterRunning": False}`` when the proxy is down or not found
    (allows dashboard to distinguish a crashed proxy from a healthy one).

    Uses ``ps aux`` (no new deps) and a 0.2 s socket-connect probe.
    Never raises.
    """
    venv = os.environ.get("NEMOCLAW_MODEL_ROUTER_VENV") or os.path.expanduser(
        os.path.join("~", ".nemoclaw", "model-router-venv"))
    if not os.path.exists(os.path.join(venv, ".nemoclaw-source-fingerprint")):
        return {}

    import re as _re
    import socket as _sock
    import subprocess as _sp

    try:
        result = _sp.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        for line in result.stdout.splitlines():
            if "model-router" not in line or "--port" not in line:
                continue
            m = _re.search(r"--port[=\s]+(\d+)", line)
            if not m:
                continue
            port = int(m.group(1))
            s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
            s.settimeout(0.2)
            rc = s.connect_ex(("127.0.0.1", port))
            s.close()
            return {"modelRouterRunning": rc == 0, "modelRouterPort": port}
    except Exception:
        pass
    return {"modelRouterRunning": False}


# NOTE (#2610, deferred): NemoClaw's skill-catalog version/provenance lives in
# ``skills/catalog-metadata.json`` (min/tested NemoClaw version, content shas),
# but that file is a SOURCE-repo build artifact — it is not shipped in the npm
# ``files`` list and no install/Docker step copies it to any host-readable path,
# and the NemoClaw skills bundle lives inside the sandbox container, not the host
# ``~/.openclaw`` ClawMetry reads. So there is no reliable on-disk location to
# read it from today. Deferred rather than ship a dead read; revisit if NemoClaw
# starts exporting the catalog to the host (e.g. ~/.nemoclaw/skills/).


def _scan_openclaw_selection_runtime() -> tuple[bool, bool]:
    """Scan the pinned OpenClaw ``selection-*.js`` once and report whether
    (a) the NemoClaw compact-catalog patch marker is present, and
    (b) all three native tool-search symbols are present.

    Returns ``(nemoclaw_patched, native_tool_search)``. Never raises.
    """
    nemoclaw_marker = b"/* nemoclaw compact tool catalog (#2600) */"
    # Mirror scripts/patch-openclaw-tool-catalog.js NATIVE_TOOL_SEARCH_PATTERNS:
    # all three symbols must be present before the patch script considers the
    # dist to already have a native tool-search build (#2732).
    native_markers = (
        b"applyToolSearchCatalog",
        b"buildToolSearchRunPlan",
        b"uncompactedEffectiveTools",
    )
    patched = False
    native = False
    try:
        home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
        dist_dirs = [
            os.path.join(home, "node_modules", "openclaw", "dist"),
            "/usr/local/lib/node_modules/openclaw/dist",
        ]
        for dist in dist_dirs:
            if not os.path.isdir(dist):
                continue
            try:
                names = os.listdir(dist)
            except OSError:
                continue
            for n in names:
                if not (n.startswith("selection-") and n.endswith(".js")):
                    continue
                fp = os.path.join(dist, n)
                try:
                    with open(fp, "rb") as fh:
                        # Patch marker + native symbols sit early in the
                        # rewritten module; cap the read.
                        blob = fh.read(2_000_000)
                except OSError:
                    continue
                if not patched and nemoclaw_marker in blob:
                    patched = True
                if not native and all(m in blob for m in native_markers):
                    native = True
                if patched and native:
                    break
            if patched and native:
                break
    except Exception:
        return patched, native
    return patched, native


def _nemoclaw_tool_catalog_state() -> Optional[bool]:
    """Whether the NemoClaw compact tool-catalog wrapper is active for this
    runtime (#2683).

    The harness patch (scripts/patch-openclaw-tool-catalog.js) injects
    ``NEMOCLAW_TOOL_CATALOG !== "0"`` into every agent turn, after rewriting
    the pinned OpenClaw ``selection-*.js`` and stamping the marker
    ``/* nemoclaw compact tool catalog (#2600) */``. We surface a defensive
    session-level boolean so the dashboard can tell a guardrail-wrapped
    session from one where the catalog was disabled.

    Returns ``True``/``False`` ONLY when there is positive NemoClaw signal
    (the patch marker is present in the openclaw dist, or the env var is
    explicitly set); returns ``None`` on plain OpenClaw so we never assert a
    catalog state that doesn't exist. Never raises.
    """
    env = os.environ.get("NEMOCLAW_TOOL_CATALOG")
    patched, _native = _scan_openclaw_selection_runtime()
    if not patched and env is None:
        # No NemoClaw signal at all -> don't claim a catalog state.
        return None
    # Mirror the harness gate exactly: enabled unless explicitly "0".
    return env != "0"


def _openclaw_tool_catalog_kind() -> Optional[str]:
    """Provenance of the active OpenClaw tool-catalog mechanism, if any (#2732).

    Returns:
        ``"nemoclaw"`` when the NemoClaw compact-catalog patch is applied
        (matches ``_nemoclaw_tool_catalog_state() is True``).
        ``"native"`` when the dist ships native ``applyToolSearchCatalog`` /
        ``buildToolSearchRunPlan`` / ``uncompactedEffectiveTools`` symbols and
        the NemoClaw patch was skipped — previously indistinguishable from
        "no catalog at all".
        ``None`` when neither signal is present.

    The NemoClaw patch wins over native detection: when both fire (e.g. a
    forward-port window) the patched wrapper is what's actually intercepting
    catalog calls. Never raises.
    """
    patched, native = _scan_openclaw_selection_runtime()
    if patched:
        return "nemoclaw"
    if native:
        return "native"
    return None


class OpenClawAdapter(AgentAdapter):
    name = "openclaw"
    display_name = "OpenClaw"

    def detect(self) -> DetectResult:
        try:
            d = _d()
            workspace = getattr(d, "WORKSPACE", None) or ""
            sessions_dir = getattr(d, "SESSIONS_DIR", None) or ""
            gateway_url = getattr(d, "GATEWAY_URL", None) or ""
            sessions = []
            try:
                sessions = d._get_sessions() or []
            except Exception as exc:
                logger.debug(f"OpenClaw _get_sessions() failed in detect: {exc}")

            default_home = os.path.expanduser("~/.openclaw")
            running = _gateway_live()
            # Require a GENUINE signal: real sessions, or an actual install
            # artifact, or a live gateway. The bare ~/.openclaw (or its
            # workspace dir) is NOT a signal — ClawMetry creates it, which
            # false-positived OpenClaw on uninstalled machines.
            detected = bool(sessions) or running or _real_install(sessions_dir)
            meta = {
                "gatewayUrl": gateway_url,
                "sessionsDir": sessions_dir,
            }
            # NemoClaw install-provenance signal (#2608). Returns {} on plain
            # OpenClaw, so meta is unchanged there. (#2610 skill-catalog deferred
            # — see note above: no host-readable on-disk location.)
            meta.update(_model_router_fingerprint())
            # NemoClaw model-router proxy liveness (#2795). Returns {} on plain
            # OpenClaw (fingerprint absent); otherwise emits modelRouterRunning
            # + modelRouterPort so a crashed proxy is distinguishable from healthy.
            meta.update(_model_router_liveness())
            _tc_enabled = _nemoclaw_tool_catalog_state()
            if _tc_enabled is not None:
                meta["nemoclawToolCatalogEnabled"] = _tc_enabled
            # Provenance — distinguish NemoClaw patch from native OpenClaw
            # tool-search builds where the patch is a no-op (#2732). Stamped
            # in addition to the back-compat boolean above.
            _tc_kind = _openclaw_tool_catalog_kind()
            if _tc_kind is not None:
                meta["openclawToolCatalogKind"] = _tc_kind
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=running,
                workspace=workspace or default_home,
                session_count=len(sessions),
                capabilities=[c.value for c in self.capabilities()],
                meta=meta,
            )
        except Exception as exc:
            logger.warning(f"OpenClaw detect() raised: {exc}")
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                meta={"error": str(exc)},
            )

    def list_sessions(self, limit: int = 100) -> List[Session]:
        try:
            raw = _d()._get_sessions() or []
        except Exception as exc:
            logger.warning(f"OpenClaw list_sessions() failed: {exc}")
            return []
        # Runtime-level NemoClaw tool-catalog state (#2683): whether the
        # compact tool-catalog wrapper is active for this install. None on
        # plain OpenClaw (no NemoClaw signal) — we don't stamp a state then.
        _tc_enabled = _nemoclaw_tool_catalog_state()
        # Catalog provenance (#2732): "nemoclaw" or "native" when either
        # signal is present, so native-tool-search OpenClaw builds are no
        # longer indistinguishable from "no catalog at all".
        _tc_kind = _openclaw_tool_catalog_kind()
        out: List[Session] = []
        for s in raw[:limit]:
            updated_ms = s.get("updatedAt") or 0
            started_at = (updated_ms / 1000.0) if updated_ms else 0.0
            extra = {
                "kind": s.get("kind") or "direct",
                "contextTokens": s.get("contextTokens"),
                "agentId": s.get("agent") or "main",
            }
            if _tc_enabled is not None:
                extra["nemoclawToolCatalogEnabled"] = _tc_enabled
            if _tc_kind is not None:
                extra["openclawToolCatalogKind"] = _tc_kind
            out.append(
                Session(
                    agent=self.name,
                    id=s.get("sessionId") or s.get("key") or "",
                    display_name=s.get("displayName") or "",
                    model=s.get("model") or "",
                    source=s.get("channel") or "",
                    started_at=started_at,
                    total_tokens=int(s.get("totalTokens") or 0),
                    input_tokens=int(s.get("inputTokens") or 0),
                    output_tokens=int(s.get("outputTokens") or 0),
                    cache_read_tokens=int(s.get("cacheReadTokens") or 0),
                    cache_write_tokens=int(s.get("cacheWriteTokens") or 0),
                    cost_usd=float(s["costUsd"]) if s.get("costUsd") is not None else None,
                    extra=extra,
                )
            )
        return out

    def read_session(self, session_id: str) -> Optional[Session]:
        for s in self.list_sessions(limit=1000):
            if s.id == session_id or s.id.startswith(session_id):
                return s
        return None

    def list_events(self, session_id: str, limit: int = 500) -> List[Event]:
        """Return events for a session in the unified Event shape.

        Reads from the DuckDB events table (filtered by agent_type='openclaw'
        and session_id) so per-agent session views and runtime-aware
        endpoints stay consistent with what /api/transcript would render.

        Falls back to ``[]`` on any error so a flaky local store never
        breaks the dashboard. The legacy rich transcript route in
        ``dashboard.py`` is unchanged.
        """
        events: List[Event] = []
        try:
            from clawmetry import local_store as _ls
            store = _ls.get_store(read_only=True)
            rows = store._fetch(
                "SELECT id, event_type, ts, model, token_count, data, agent_id, node_id "
                "FROM events WHERE agent_type = ? AND session_id = ? "
                "ORDER BY ts ASC LIMIT ?",
                ["openclaw", str(session_id), int(limit)],
            )
            for r in rows or []:
                # ts column is VARCHAR; coerce to float, default 0.0.
                ts_raw = r[2]
                try:
                    ts_f = float(ts_raw) if ts_raw not in (None, "") else 0.0
                except (TypeError, ValueError):
                    ts_f = 0.0
                extra: dict = {}
                content_text = ""
                if r[3]:
                    extra["model"] = r[3]
                # r[6] = agent_id, r[7] = node_id — surface structured log
                # context fields so callers can correlate events by agent and node.
                if r[6]:
                    extra["agent_id"] = r[6]
                if r[7]:
                    extra["node_id"] = r[7]
                # r[5] = data BLOB — decode and surface per-type token split
                # (input/output/cache_read/cache_write) so callers can measure
                # per-turn cache efficiency without re-reading the raw file.
                # Also extract channel/hostname from gateway log record top-level
                # fields when present (no dedicated DB columns for these).
                raw_data = r[5]
                if raw_data is not None:
                    try:
                        if isinstance(raw_data, (bytes, bytearray)):
                            raw_data = bytes(raw_data).decode("utf-8", "replace")
                        obj = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                        if isinstance(obj, dict):
                            for _field in ("channel", "hostname"):
                                _val = obj.get(_field)
                                if _val:
                                    extra[_field] = _val
                            msg = obj.get("message")
                            if isinstance(msg, str):
                                content_text = msg
                            src = msg if isinstance(msg, dict) else obj
                            usage = src.get("usage") if isinstance(src.get("usage"), dict) else {}
                            if usage:
                                for dst, *keys in [
                                    ("inputTokens", "input_tokens", "inputTokens"),
                                    ("outputTokens", "output_tokens", "outputTokens"),
                                    ("cacheReadTokens", "cache_read_input_tokens", "cacheReadInputTokens", "cacheRead"),
                                    ("cacheWriteTokens", "cache_creation_input_tokens", "cacheCreationInputTokens", "cacheWrite"),
                                ]:
                                    for k in keys:
                                        v = usage.get(k)
                                        if v is not None:
                                            extra[dst] = int(v)
                                            break
                    except Exception:
                        pass
                events.append(Event(
                    agent=self.name,
                    session_id=str(session_id),
                    id=str(r[0]),
                    type=str(r[1] or "event"),
                    ts=ts_f,
                    content=content_text,
                    tokens=int(r[4] or 0),
                    extra=extra,
                ))
        except Exception as exc:
            logger.debug("openclaw list_events read failed: %s", exc)
        return events

    def capabilities(self) -> Set[Capability]:
        return {
            Capability.SESSIONS,
            Capability.EVENTS,
            Capability.COST,
            Capability.SUBAGENTS,
            Capability.CRONS,
            Capability.SKILLS,
            Capability.MEMORY,
            Capability.BRAIN,
            Capability.LOGS,
            Capability.GATEWAY_RPC,
            Capability.CHANNELS,
        }

    # ── Span reconstruction (issue #1010 / Trace 4) ────────────────────────

    @staticmethod
    def _span_id(*parts: str) -> str:
        return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]

    @staticmethod
    def _trace_id(session_id: str) -> str:
        return hashlib.sha256(session_id.encode()).hexdigest()[:32]

    @staticmethod
    def _build_spans_from_events(events: list, session_id: str) -> list:
        """Map raw JSONL objects to OTel-shaped span dicts.

        Mapping per issue #1010:
        - ``session`` (version set)    → root span (INTERNAL)
        - ``message`` (role=assistant) → llm.call span (CLIENT, child of root)
          - each tool_use block        → tool.<name> span (CLIENT, child of llm)
        - ``message`` (role=user)      → matched tool_result blocks fold their
          structured ``details`` payload + ``is_error`` flag + text content back
          onto the tool span identified by ``tool_use_id`` (#2733).
        - ``subagent_spawn``           → agent.spawn span (INTERNAL, link to child trace)

        Span IDs are deterministic SHA-256 prefixes so re-ingesting is idempotent.
        """
        _sid = OpenClawAdapter._span_id
        trace_id = OpenClawAdapter._trace_id(session_id)
        session_span_id = _sid("session", session_id)
        now = _time.time()
        spans: list = []
        # tool_use_id → tool span dict, populated as assistant tool_use blocks
        # are emitted; consumed when a later user tool_result block references
        # the same id (#2733).
        tool_span_by_id: dict = {}

        for obj in events:
            if not isinstance(obj, dict):
                continue
            t = obj.get("type")
            raw_ts = obj.get("timestamp") or obj.get("ts") or now
            try:
                ts = float(raw_ts)
            except (TypeError, ValueError):
                ts = now

            if t == "session" and obj.get("version") is not None:
                spans.append({
                    "span_id": session_span_id,
                    "trace_id": trace_id,
                    "name": "session",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": "openclaw",
                    "attributes": {"session.version": obj.get("version"), "session.id": session_id},
                })

            elif t == "message" and isinstance(obj.get("message"), dict):
                msg = obj["message"]
                role = msg.get("role")
                content = msg.get("content") or []
                if role == "user":
                    # Tool results live in user-role messages. Fold the
                    # structured details payload + is_error flag + text content
                    # back onto the originating tool span (#2733). Orphan
                    # tool_results (no matching tool_use_id) are skipped.
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_result":
                            continue
                        tu_id = block.get("tool_use_id") or block.get("toolUseId") or ""
                        target = tool_span_by_id.get(tu_id)
                        if target is None:
                            continue
                        attrs = target.get("attributes") or {}
                        attrs["tool.result_present"] = True
                        if "is_error" in block:
                            attrs["tool.result_is_error"] = bool(block.get("is_error"))
                        # NemoClaw nemoClawBuildToolResult helper attaches a
                        # top-level structured ``details`` dict on the result
                        # (catalog hits, schemas, dispatch output). Surface it
                        # so downstream Tracing/Event.extra can render the real
                        # payload instead of just the stringified text wrapper.
                        details = block.get("details")
                        if details is not None:
                            attrs["tool.result_details"] = details
                            if isinstance(details, dict):
                                attrs["tool.result_details_keys"] = sorted(details.keys())
                        # Walk the tool_result content array. Text blocks
                        # collapse into a single string for quick read
                        # (NemoClaw JSON-stringified wrapper, or plain text
                        # from native tools). Non-text block types
                        # (resource_link, resource, audio, image) are
                        # surfaced by sorted type-list so downstream UI can
                        # see that MCP returned a non-text payload (#2731).
                        # Coercion metadata (the harness preserves the
                        # original block type when it materializes a
                        # resource_link / resource / audio / malformed-image
                        # into a text-safe shape) is recorded as
                        # {from, to} pairs. Accepts the common field-name
                        # variants seen in the wild.
                        result_content = block.get("content")
                        text_parts: list = []
                        types_seen: set = set()
                        coercions: list = []
                        if isinstance(result_content, str):
                            text_parts.append(result_content)
                        elif isinstance(result_content, list):
                            for inner in result_content:
                                if not isinstance(inner, dict):
                                    continue
                                inner_type = inner.get("type")
                                if isinstance(inner_type, str) and inner_type:
                                    types_seen.add(inner_type)
                                if inner_type == "text":
                                    val = inner.get("text")
                                    if isinstance(val, str):
                                        text_parts.append(val)
                                coerced_from = (
                                    inner.get("coerced_from")
                                    or inner.get("coercedFrom")
                                    or inner.get("original_type")
                                    or inner.get("originalType")
                                )
                                if isinstance(coerced_from, str) and coerced_from:
                                    coercions.append({
                                        "from": coerced_from,
                                        "to": inner_type if isinstance(inner_type, str) and inner_type else "unknown",
                                    })
                        if text_parts:
                            attrs["tool.result_text"] = "".join(text_parts)
                        if types_seen:
                            attrs["tool.result_content_types"] = sorted(types_seen)
                        if coercions:
                            attrs["tool.result_coercions"] = coercions
                        target["attributes"] = attrs
                        # End-time the tool span to whatever the result arrived
                        # at. start_ts ≤ end_ts isn't enforced (assistant emits
                        # tool_use and user tool_result share clock); but the
                        # signal is still useful for duration heuristics.
                        target["end_ts"] = ts
                    continue
                if role != "assistant":
                    continue
                model = msg.get("model") or ""
                usage = msg.get("usage") or {}
                tok_in = int(usage.get("input_tokens") or usage.get("inputTokens") or 0)
                tok_out = int(usage.get("output_tokens") or usage.get("outputTokens") or 0)
                llm_sid = _sid("llm", session_id, str(raw_ts))
                spans.append({
                    "span_id": llm_sid,
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": f"llm.call {model}".strip() if model else "llm.call",
                    "kind": "CLIENT",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": "openclaw",
                    "model": model or None,
                    "tokens_input": tok_in or None,
                    "tokens_output": tok_out or None,
                    "token_count": (tok_in + tok_out) or None,
                })
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        orig_name = block.get("name") or "tool"
                        tool_name = orig_name
                        tool_id = block.get("id") or ""
                        blk_input = block.get("input")
                        # NemoClaw compact tool-catalog dispatch (#2682): the
                        # injected meta-tool is named "tool_call" and carries the
                        # REAL dispatched tool in input.name (the wrapper
                        # dispatches via catalog.get(name)). Unwrap it so the
                        # Tracing tab shows the real tool, not a generic
                        # "tool_call" span. Falls back to the literal name on
                        # old/missing data so it never crashes.
                        attrs: dict = {}
                        if tool_name == "tool_call" and isinstance(blk_input, dict):
                            real = blk_input.get("name")
                            if isinstance(real, str) and real.strip():
                                real = real.strip()
                                attrs.update({
                                    "nemoclaw.catalog_dispatch": True,
                                    "nemoclaw.meta_tool": "tool_call",
                                    "nemoclaw.dispatched_tool": real,
                                })
                                tool_name = real
                        # Catalog meta-tools (tool_search/tool_describe/tool_call)
                        # are guardrail dispatches, not real agent actions — tag
                        # by the ORIGINAL name (tool_name may now be the unwrapped
                        # real tool).
                        if orig_name in _NEMOCLAW_CATALOG_TOOLS:
                            attrs["nemoclaw.catalog_guardrail"] = True
                        tool_span: dict = {
                            "span_id": _sid("tool", session_id, str(raw_ts), tool_id, tool_name),
                            "trace_id": trace_id,
                            "parent_span_id": llm_sid,
                            "name": f"tool.{tool_name}",
                            "kind": "CLIENT",
                            "start_ts": ts,
                            "session_id": session_id,
                            "agent_type": "openclaw",
                            "tool_name": tool_name,
                            "input": blk_input,
                            "attributes": attrs or None,
                        }

                        spans.append(tool_span)
                        if tool_id:
                            tool_span_by_id[tool_id] = tool_span

            elif t in ("subagent_spawn", "agent_spawn"):
                sub_id = (
                    obj.get("subagent_id") or obj.get("agentId") or obj.get("agent_id") or ""
                )
                child_trace = hashlib.sha256(sub_id.encode()).hexdigest()[:32] if sub_id else ""
                spans.append({
                    "span_id": _sid("spawn", session_id, str(raw_ts), sub_id),
                    "trace_id": trace_id,
                    "parent_span_id": session_span_id,
                    "name": "agent.spawn",
                    "kind": "INTERNAL",
                    "start_ts": ts,
                    "session_id": session_id,
                    "agent_type": "openclaw",
                    "links": [{"trace_id": child_trace, "span_id": "0" * 16}] if child_trace else None,
                    "attributes": {"subagent_id": sub_id} if sub_id else None,
                })

        return spans

    def reconstruct_spans(self, jsonl_path: str) -> list:
        """Read an OpenClaw JSONL transcript and return OTel-shaped span dicts.

        The returned list can be fed directly to ``local_store.ingest_span()``.
        Returns an empty list and logs a warning on I/O errors.
        """
        session_id = os.path.basename(jsonl_path).split(".jsonl", 1)[0]
        try:
            with open(jsonl_path, encoding="utf-8", errors="replace") as fh:
                events = []
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError as exc:
            logger.warning("reconstruct_spans: cannot read %s: %s", jsonl_path, exc)
            return []
        return self._build_spans_from_events(events, session_id)

    def running(self) -> bool:
        try:
            return bool(getattr(_d(), "GATEWAY_URL", None))
        except Exception:
            return False
