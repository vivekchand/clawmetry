"""QwenCodeAdapter — read Qwen Code chat-recording history from disk.

Qwen Code (https://github.com/QwenLM/qwen-code) is Alibaba's open-source
coding CLI, a fork of Google's Gemini CLI. It supports any OpenAI-compatible
provider (Qwen API, OpenRouter, a local Ollama ``/v1`` endpoint, ...) via the
``OPENAI_API_KEY`` / ``OPENAI_BASE_URL`` / ``OPENAI_MODEL`` env vars.

Like the Claude Code and PicoClaw adapters, this is a non-OpenClaw filesystem
reader that subclasses :class:`AgentAdapter` directly. The native format is
Qwen Code's own Gemini-CLI-lineage chat recording, NOT OpenClaw's v3 envelope.

On-disk layout
--------------
Chat recording is written (when enabled with ``--chat-recording`` or the
``general.chatRecording`` setting) under the per-project directory::

    ~/.qwen/projects/<project-hash>/chats/<sessionId>.jsonl

``<project-hash>`` is the working-directory path with ``/`` replaced by ``-``
(e.g. ``-private-tmp-qwen-real-run``). One ``.jsonl`` file per session; one
JSON record per line.

Each line is a record with a flat envelope plus a nested ``message``::

    {
      "uuid": "...",                 # this record's id
      "parentUuid": "..." | null,    # previous record (a chain, not a tree)
      "sessionId": "...",            # == the file's basename
      "timestamp": "2026-05-25T20:41:03.715Z",   # ISO-8601, UTC "Z"
      "type": "user" | "assistant" | "tool_result" | "system",
      "cwd": "...",
      "version": "0.16.1",
      "model": "qwen3:8b",           # present on assistant records
      "message": { "role": ..., "parts": [ ... ] },
      "usageMetadata": { ... }       # present on assistant records
    }

The ``message.parts`` array is the Gemini ``Content.parts`` shape:
  - user text:        ``{"text": "..."}``                (role ``user``)
  - assistant text:   ``{"text": "..."}``                (role ``model``)
  - assistant reasoning: ``{"text": "...", "thought": true}``
  - tool call:        ``{"functionCall": {"id", "name", "args"}}``
  - tool result:      ``{"functionResponse": {"id", "name", "response": {...}}}``
    (carried on a ``type:"tool_result"`` record whose ``message.role`` is ``user``)

Note the assistant role on disk is the Gemini ``"model"`` string, which we
normalise to ``"assistant"`` for the unified Event schema.

Tokens ARE on disk. Assistant records carry ``usageMetadata`` with
``promptTokenCount`` / ``candidatesTokenCount`` / ``thoughtsTokenCount`` /
``totalTokenCount`` / ``cachedContentTokenCount``. We surface real token
counts and advertise the COST capability. Cost in USD is NOT recorded (the
endpoint may be a free local Ollama), so ``cost_usd`` stays ``None`` and is
left for downstream pricing — we never fabricate a dollar figure.

``type:"system"`` records (``attribution_snapshot`` / ``ui_telemetry``) are
control/telemetry, not conversation, and are skipped for events.

The adapter is read-only and never modifies the Qwen Code data directory.

Why this adapter is FREE and bundled in OSS
-------------------------------------------
``docs/ENTITLEMENTS.md`` states the rule: an open-source runtime gets a free,
open-source adapter; a commercial vendor product stays paid. Qwen Code is
Apache-2.0 (QwenLM/qwen-code), so it qualifies on the rule alone. It is also
the second application of the Goose precedent (2026-08-19): the maintainers
declined a README Ecosystem listing for ClawMetry specifically because this
reader was closed-source and paid --- "we don't want the official README
routing users to a capability behind a paywall [...] happy to reopen if the
Qwen Code adapter moves into the free, open-source package"
(QwenLM/qwen-code#9294, closed 2026-09-18). The reader now ships here, so
``pip install clawmetry`` observes Qwen Code with no account, no licence key
and no wheel download. ``tests/test_phase4_adapter_move.py`` pins that.
"""
from __future__ import annotations

import dataclasses
import glob
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from clawmetry.adapters.base import AgentAdapter, Capability, DetectResult, Event, Session
from clawmetry.adapters.inputs import CAP_INPUTS, context_event, prepend_context

# Trail triad: Capability.REASONING exists on OSS cores that ship the
# decision-trail work; on an older core it is simply absent and the set below
# omits it (the wheel must load on both).
_CAP_REASONING = getattr(Capability, "REASONING", None)
from clawmetry.adapters.cost import derive_cost_usd

logger = logging.getLogger("clawmetry.adapters.qwen_code")

_AGENT = "qwen_code"

# Normalises the fractional-seconds run of an ISO-8601 timestamp to exactly 6
# digits. datetime.fromisoformat() on Python 3.9/3.10 only accepts 0, 3, or 6
# fractional digits; Qwen Code emits millisecond precision (3 digits, e.g.
# ".715Z") which is fine, but we pad/truncate defensively so any odd-length
# fraction from a future version still parses instead of silently becoming 0.0.
# (ClawMetry CI runs Py3.9.)
_FRAC_RE = re.compile(r"\.(\d+)")


# -- helpers -----------------------------------------------------------------


def _qwen_home() -> str:
    return os.environ.get("QWEN_HOME") or os.path.expanduser("~/.qwen")


def _projects_dir() -> str:
    return os.path.join(_qwen_home(), "projects")


def _parse_ts(ts: Any) -> float:
    """Parse an ISO-8601 string or numeric epoch to float seconds.

    Returns 0.0 for anything unparseable so callers never crash on a bad
    or missing timestamp.
    """
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        s = str(ts).strip()
        if not s:
            return 0.0
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        # Pad/truncate fractional seconds to 6 digits for Python 3.9/3.10.
        s = _FRAC_RE.sub(lambda m: "." + (m.group(1) + "000000")[:6], s, count=1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, AttributeError):
        return 0.0


def _norm_role(record_type: str, message: dict[str, Any]) -> str:
    """Normalise the on-disk role to the unified schema.

    Qwen Code (Gemini lineage) uses ``model`` for the assistant role and
    carries tool results on a ``user``-role record tagged ``type:tool_result``.
    We map: model -> assistant, tool_result record -> tool, else the raw role.
    """
    if record_type == "tool_result":
        return "tool"
    role = (message or {}).get("role") or ""
    if role == "model":
        return "assistant"
    return role


def _iter_records(path: str):
    """Yield parsed record dicts from a chat-recording JSONL file.

    Defensive: skips blank lines, lines that do not parse as JSON, and any
    line that is not a dict. Never raises on a single bad line.
    """
    try:
        with open(path, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                yield obj
    except OSError as exc:
        logger.warning("QwenCodeAdapter: cannot read %s: %s", path, exc)
        return


def _parts_text(parts: Any) -> tuple[str, str]:
    """Split a ``message.parts`` array into (final_text, reasoning_text).

    Reasoning parts are ``{"text": ..., "thought": true}``; everything else
    with a ``text`` is treated as visible content. Returns joined strings
    (empty when absent). Non-list / malformed parts yield ("", "").
    """
    if not isinstance(parts, list):
        return "", ""
    visible: list[str] = []
    thoughts: list[str] = []
    for p in parts:
        if not isinstance(p, dict):
            continue
        txt = p.get("text")
        if not isinstance(txt, str) or not txt:
            continue
        if p.get("thought"):
            thoughts.append(txt)
        else:
            visible.append(txt)
    return "\n".join(visible), "\n".join(thoughts)


def _first_user_text(path: str) -> str:
    """Return the first user-message text in a session, for use as a title."""
    for obj in _iter_records(path):
        if obj.get("type") != "user":
            continue
        msg = obj.get("message")
        if not isinstance(msg, dict):
            continue
        visible, _ = _parts_text(msg.get("parts"))
        if visible:
            # Single-line, trimmed title.
            return " ".join(visible.split())[:200]
    return ""


def _first_user_last_assistant(path: str) -> tuple[str, str]:
    """(first user text, last assistant text) from a chat/agent JSONL —
    the context a sub-agent was handed and what it answered. -> ('', '')."""
    prompt = reply = ""
    for obj in _iter_records(path):
        rtype = obj.get("type") or ""
        msg = obj.get("message") or {}
        if not isinstance(msg, dict):
            continue
        parts = msg.get("parts") or []
        text = ""
        for part in parts if isinstance(parts, list) else []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                if part["text"].strip():
                    text = part["text"].strip()
        if not text and isinstance(msg.get("content"), str):
            text = msg["content"].strip()
        if not text:
            continue
        if rtype == "user" and not prompt:
            prompt = text[:400]
        elif rtype == "assistant":
            reply = text[:400]
    return prompt, reply


def _session_from_file(
    path: str, session_id: str, settings_extra: dict[str, Any] | None = None
) -> Session | None:
    """Build a unified :class:`Session` from one chat-recording JSONL file.

    Walks every record once to count conversational messages, find the
    first/last timestamps, the model, and sum the latest usage metadata.
    ``settings_extra`` (the active-provider / telemetry-target summary from
    ``settings.json``) is merged into ``extra`` when provided.
    Returns ``None`` only if the file cannot be stat'd at all.
    """
    model = ""
    msg_count = 0
    first_ts = 0.0
    last_ts = 0.0
    total_tokens = 0
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    reasoning_tokens = 0
    title = ""
    cwd = ""

    for obj in _iter_records(path):
        rtype = obj.get("type") or ""
        # Working directory: stamped on nearly every record. Last non-empty
        # wins (an agent that cd's ends up showing where it IS). Exposed as
        # extra["cwd"] so the session row persists it — the kill/pause pid
        # resolution (process_control.resolve_by_cwd) and qwen's own pid
        # sidecar cross-check both key on it (2026-08-19 matrix-gap sprint).
        _cwd = obj.get("cwd")
        if isinstance(_cwd, str) and _cwd.strip():
            cwd = _cwd.strip()
        # Skip control/telemetry records for counting and titling.
        if rtype == "system":
            continue

        ts = _parse_ts(obj.get("timestamp"))
        if ts:
            if not first_ts:
                first_ts = ts
            last_ts = ts

        if rtype in ("user", "assistant", "tool_result"):
            msg_count += 1

        if rtype == "user" and not title:
            msg = obj.get("message")
            if isinstance(msg, dict):
                visible, _ = _parts_text(msg.get("parts"))
                if visible:
                    title = " ".join(visible.split())[:200]

        if rtype == "assistant":
            mdl = obj.get("model")
            if isinstance(mdl, str) and mdl:
                model = mdl  # last non-empty model wins
            usage = obj.get("usageMetadata")
            if isinstance(usage, dict):
                # usageMetadata is cumulative-per-call; sum across calls so the
                # session total reflects every model round-trip honestly.
                total_tokens += _int(usage.get("totalTokenCount"))
                input_tokens += _int(usage.get("promptTokenCount"))
                output_tokens += _int(usage.get("candidatesTokenCount"))
                cache_read_tokens += _int(usage.get("cachedContentTokenCount"))
                reasoning_tokens += _int(usage.get("thoughtsTokenCount"))

    ended_at: float | None = last_ts or None
    if ended_at is None:
        try:
            ended_at = os.path.getmtime(path)
        except OSError:
            ended_at = None
    if not first_ts and ended_at:
        first_ts = ended_at

    return Session(
        agent=_AGENT,
        id=session_id,
        title=title,
        display_name=title or session_id,
        model=model,
        source="qwen_code",
        started_at=first_ts,
        ended_at=ended_at,
        message_count=msg_count,
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        reasoning_tokens=reasoning_tokens,
        # Cost in USD is not recorded on disk (the endpoint may be a free local
        # Ollama). Derive it from the token split + model (cache-aware); real
        # 0.0 for local models, None only when model/tokens are absent.
        cost_usd=(
            derive_cost_usd(model, input_tokens, output_tokens, cache_read_tokens, 0)
            if (model and (input_tokens or output_tokens or cache_read_tokens))
            else None
        ),
        cost_status="derived" if (model and (input_tokens or output_tokens or cache_read_tokens)) else "tokens_only",
        # Base flag + the read-only settings.json summary (active provider,
        # enabled model set, telemetry target). settings_extra is {} when the
        # file is absent/garbled, so this is always safe.
        extra={"costUsdUnavailable": True,
               **({"cwd": cwd} if cwd else {}),
               **(settings_extra or {})},
        **_cwd_kwargs(cwd),
    )


def _cwd_kwargs(cwd: str) -> dict:
    """``{"cwd": cwd}`` when the installed OSS wheel's Session carries the
    first-class field (added 2026-08-19), ``{}`` on older wheels — so the
    adapter never crashes on version skew. extra["cwd"] mirrors it either
    way for the metadata alias walk."""
    if not cwd:
        return {}
    try:
        import dataclasses
        if any(f.name == "cwd" for f in dataclasses.fields(Session)):
            return {"cwd": cwd}
    except Exception:
        pass
    return {}


def _int(v: Any) -> int:
    """Best-effort int coercion; 0 for anything non-numeric."""
    if isinstance(v, bool):
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    return 0


# -- settings.json (active provider / enabled models / telemetry target) -----


def _strip_jsonc_comments(text: str) -> str:
    """Strip whole-line ``//`` comments so JSONC settings parse as JSON.

    The harness's ``scripts/telemetry.js`` strips *all* ``//…`` runs, which
    also mangles a ``//`` inside a string (e.g. ``https://openrouter.ai/...``).
    We only strip comments that begin a line (after optional whitespace), the
    dominant JSONC form, so inline URLs survive. Anything that still fails to
    parse is caught upstream and ignored.
    """
    return re.sub(r"(?m)^[ \t]*//[^\n]*", "", text)


def _read_settings() -> dict[str, Any]:
    """Read ``$QWEN_HOME/settings.json`` (JSONC). Returns {} on any problem.

    The harness reads ``~/.qwen/settings.json`` to drive auth, the active
    OpenAI-compatible model provider (``modelProviders.openai``), and the
    telemetry target (``telemetry.target``: ``local`` Jaeger vs ``gcp``). We
    surface a read-only summary on each session so the dashboard can show the
    active provider, the curated enabled-model set, and where telemetry ships.
    Never raises — a missing/garbled file just yields no settings extra.
    """
    path = os.path.join(_qwen_home(), "settings.json")
    try:
        with open(path, "r", errors="replace") as fh:
            raw = fh.read()
    except OSError:
        return {}
    # Most settings files are plain JSON. Try that first so we never mangle a
    # ``//`` that lives *inside* a string (e.g. ``https://openrouter.ai/...``);
    # only fall back to the lenient JSONC strip when strict parsing fails.
    obj: Any
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        try:
            obj = json.loads(_strip_jsonc_comments(raw))
        except json.JSONDecodeError:
            return {}
    return obj if isinstance(obj, dict) else {}


def _settings_extra() -> dict[str, Any]:
    """Build the ``extra`` summary from settings.json. Always safe ({} on miss).

    Keys (camelCase, matching the other ``extra`` keys):
      - ``telemetryTarget``   — ``"local"`` | ``"gcp"`` (the shipping target)
      - ``telemetryEnabled``  — bool, whether native OTel telemetry is on
      - ``telemetryOtlpEndpoint`` — OTLP collector endpoint when configured
      - ``activeAuthType``    — e.g. ``"USE_OPENAI"`` (OpenRouter reuses this)
      - ``enabledModels``     — the curated model ids from ``modelProviders.openai``
      - ``modelProviderCount``— number of configured OpenAI-compatible entries
    """
    settings = _read_settings()
    if not settings:
        return {}

    extra: dict[str, Any] = {}

    telemetry = settings.get("telemetry")
    if isinstance(telemetry, dict):
        target = telemetry.get("target")
        if isinstance(target, str) and target:
            extra["telemetryTarget"] = target
        if isinstance(telemetry.get("enabled"), bool):
            extra["telemetryEnabled"] = telemetry["enabled"]
        endpoint = telemetry.get("otlpEndpoint")
        if isinstance(endpoint, str) and endpoint:
            extra["telemetryOtlpEndpoint"] = endpoint

    security = settings.get("security")
    if isinstance(security, dict):
        auth = security.get("auth")
        if isinstance(auth, dict):
            selected = auth.get("selectedType")
            if isinstance(selected, str) and selected:
                extra["activeAuthType"] = selected

    providers = settings.get("modelProviders")
    if isinstance(providers, dict):
        openai = providers.get("openai")
        if isinstance(openai, list):
            ids = [
                m.get("id")
                for m in openai
                if isinstance(m, dict) and isinstance(m.get("id"), str) and m.get("id")
            ]
            if ids:
                extra["enabledModels"] = ids
            extra["modelProviderCount"] = len(openai)

    return extra


def _settings_mcp_servers() -> list[dict[str, Any]]:
    """``[{name}]`` for every entry under ``settings.json`` ``mcpServers``.
    Names only: the command / url / env of a server are configuration the
    dashboard has no business copying. ``[]`` when absent or malformed."""
    servers = _read_settings().get("mcpServers")
    if not isinstance(servers, dict):
        return []
    return [{"name": str(k)} for k in servers if isinstance(k, str) and k.strip()]


def _context_from_file(path: str, session_id: str) -> Event | None:
    """The one ``context.compiled`` event for a Qwen Code chat recording.

    PARTIAL: the ``type:"system"`` records are attribution / ui-telemetry,
    not a system prompt, and no prompt text is persisted. Captured from the
    records themselves: ``cwd`` and ``version`` (stamped on every record),
    the assistant ``model``, the first user message, the INVOKED tool names
    (``functionCall.name``) and the per-tool-call ``uiEvent.decision`` set
    (e.g. ``auto_accept``). From ``settings.json``: MCP server names and the
    selected auth type. Never raises.
    """
    try:
        cwd = version = model = prompt = ""
        tools: set[str] = set()
        decisions: set[str] = set()
        first_ts = 0.0
        for obj in _iter_records(path):
            _cwd = obj.get("cwd")
            if isinstance(_cwd, str) and _cwd.strip():
                cwd = _cwd.strip()
            _ver = obj.get("version")
            if not version and isinstance(_ver, str) and _ver.strip():
                version = _ver.strip()
            rtype = obj.get("type") or ""
            if rtype == "system":
                sp = obj.get("systemPayload")
                ui = sp.get("uiEvent") if isinstance(sp, dict) else None
                if isinstance(ui, dict) and isinstance(ui.get("decision"), str) \
                        and ui["decision"]:
                    decisions.add(ui["decision"])
                continue
            ts = _parse_ts(obj.get("timestamp"))
            if ts and not first_ts:
                first_ts = ts
            msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            parts = msg.get("parts")
            if rtype == "user" and not prompt:
                visible, _ = _parts_text(parts)
                if visible.strip():
                    prompt = visible
            if rtype == "assistant":
                mdl = obj.get("model")
                if isinstance(mdl, str) and mdl:
                    model = mdl
            if isinstance(parts, list):
                for pt in parts:
                    fc = pt.get("functionCall") if isinstance(pt, dict) else None
                    if isinstance(fc, dict) and isinstance(fc.get("name"), str) \
                            and fc["name"].strip():
                        tools.add(fc["name"].strip())
        settings = _settings_extra()
        meta: dict[str, Any] = {
            "cwd": cwd,
            "version": version,
            "model": model,
            "toolDecisions": sorted(decisions) or None,
            "mcpServers": _settings_mcp_servers() or None,
            "activeAuthType": settings.get("activeAuthType") or "",
            "telemetryTarget": settings.get("telemetryTarget") or "",
        }
        return context_event(
            _AGENT, session_id, first_ts,
            prompt=prompt or None,
            tools=sorted(tools) or None,
            runtime_meta=meta,
            source="chat record cwd/version/model; first type=user parts text; "
                   "functionCall.name (invoked names only); ui_telemetry "
                   "uiEvent.decision; settings.json mcpServers keys + "
                   "security.auth.selectedType + telemetry.target",
        )
    except Exception as exc:
        logger.debug("QwenCodeAdapter: context capture skipped: %s", exc)
        return None


# -- adapter -----------------------------------------------------------------


class QwenCodeAdapter(AgentAdapter):
    """Adapter for Qwen Code chat-recording sessions under ``~/.qwen``."""

    name = "qwen_code"
    display_name = "Qwen Code"

    def __init__(self, projects_dir: str | None = None) -> None:
        # Overridable for testing; defaults to QWEN_HOME/projects.
        self._projects_dir = projects_dir or _projects_dir()

    @property
    def projects_dir(self) -> str:
        return self._projects_dir

    # -- discovery (bounded) -------------------------------------------------

    def _subagents_dir_for(self, chat_path: str, session_id: str) -> str | None:
        """``<project>/subagents/<parentSessionId>`` for one chat file.

        Qwen Code >= ~0.17 writes Claude-Code-style per-agent transcripts
        parent-keyed under the PROJECT dir (agent-transcript.ts):
          <project>/chats/<sid>.jsonl                 (parent)
          <project>/subagents/<sid>/agent-<id>.jsonl  (+ .meta.json)
        Verified against a real 0.21.14 capture on this machine.
        """
        try:
            proj = os.path.dirname(os.path.dirname(chat_path))
            d = os.path.join(proj, "subagents", session_id)
            return d if os.path.isdir(d) else None
        except (OSError, TypeError):
            return None

    def _list_subagent_sessions(
        self, chat_path: str, session_id: str,
        settings_extra: dict[str, Any] | None,
    ) -> list[Session]:
        """One child Session per ``agent-*.jsonl`` under the parent's
        subagents dir. Reuses ``_session_from_file`` (same envelope — the
        child records carry usageMetadata like any chat), then re-homes the
        result with the orchestration facts from ``agent-<id>.meta.json``:
        agentType, description, toolUseId, parentAgentId (nested children
        re-parent onto their spawning agent), status
        running|completed|failed|cancelled|paused, isBackgrounded, model.
        Never raises -> [].
        """
        sub_dir = self._subagents_dir_for(chat_path, session_id)
        if not sub_dir:
            return []
        try:
            entries = sorted(
                e for e in os.listdir(sub_dir)
                if e.startswith("agent-") and e.endswith(".jsonl"))
        except OSError:
            return []
        out: list[Session] = []
        for name in entries[:100]:
            stem = name[:-6]
            path = os.path.join(sub_dir, name)
            try:
                base = _session_from_file(path, stem, settings_extra)
            except Exception as exc:
                logger.warning("QwenCodeAdapter: subagent %s skipped: %s",
                               path, exc)
                continue
            if base is None:
                continue
            meta: dict[str, Any] = {}
            try:
                with open(path[:-6] + ".meta.json", encoding="utf-8") as fh:
                    loaded = json.load(fh)
                if isinstance(loaded, dict):
                    meta = loaded
            except (OSError, ValueError):
                meta = {}
            raw_status = str(meta.get("status") or "")
            if raw_status == "running":
                status = "running"
            elif raw_status in ("failed", "cancelled"):
                status = "failed"
            else:
                status = "completed"
            label = (str(meta.get("description") or "").strip()
                     or str(meta.get("agentType") or "").strip() or stem)
            parent_agent = meta.get("parentAgentId")
            parent_ns = (f"{session_id}::agent-{parent_agent}"
                         if parent_agent else session_id)
            prompt, reply = _first_user_last_assistant(path)
            extra = dict(base.extra or {})
            extra.update({
                "kind": "subagent",
                "isSubagent": True,
                "depth": 2 if parent_agent else 1,
                "agentType": str(meta.get("agentType") or ""),
                "label": label[:120],
                "agentFile": stem,
            })
            if meta.get("description"):
                extra["description"] = str(meta["description"])[:120]
            if meta.get("toolUseId"):
                extra["toolUseId"] = str(meta["toolUseId"])
            if meta.get("isBackgrounded"):
                extra["background"] = True
            if raw_status:
                extra["qwenStatus"] = raw_status
            if meta.get("lastError"):
                extra["error"] = str(meta["lastError"])[:200]
            if prompt:
                extra["prompt"] = prompt
            if reply:
                extra["reply"] = reply
            out.append(dataclasses.replace(
                base,
                id=f"{session_id}::{stem}",
                parent_id=parent_ns,
                title=label[:80],
                display_name=label[:80],
                ended_at=None if status == "running" else base.ended_at,
                cost_status="running" if status == "running" else base.cost_status,
                end_reason="error" if status == "failed" else base.end_reason,
                extra=extra,
            ))
        return out

    def _session_files(self) -> list[str]:
        """Return chat-recording .jsonl files across all project dirs.

        Bounded discovery: only globs ``<projects>/*/chats/*.jsonl`` — one
        level of project dirs, never a recursive walk of ``$HOME``.
        """
        root = self._projects_dir
        if not os.path.isdir(root):
            return []
        try:
            return glob.glob(os.path.join(root, "*", "chats", "*.jsonl"))
        except OSError as exc:
            logger.warning("QwenCodeAdapter session glob failed: %s", exc)
            return []

    # -- AgentAdapter contract -----------------------------------------------

    def detect(self) -> DetectResult:
        """Cheap detection. Never raises.

        ``detected`` is True when the projects dir exists with >=1 session
        log, or when the Qwen home exists (installed but no recordings yet).
        ``running`` is always False — there is no live gateway for Qwen Code.
        """
        home = _qwen_home()
        try:
            files = self._session_files()
            session_count = len(files)
            has_home = os.path.isdir(home)
            detected = session_count > 0 or has_home
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=detected,
                running=False,
                workspace=home,
                session_count=session_count,
                capabilities=[c.value for c in self.capabilities()],
                meta={"projectsDir": self._projects_dir},
            )
        except Exception as exc:  # belt-and-suspenders: detect() must never raise
            logger.debug("QwenCodeAdapter detect() failed: %s", exc)
            return DetectResult(
                name=self.name,
                display_name=self.display_name,
                detected=False,
                running=False,
                workspace=home,
                capabilities=[c.value for c in self.capabilities()],
                meta={"error": str(exc)},
            )

    def list_sessions(self, limit: int = 100) -> list[Session]:
        """Return recent sessions, newest first. Never raises on a bad file."""
        files = self._session_files()
        if not files:
            return []

        # Read settings.json once (global to the Qwen home) and stamp the
        # active-provider / telemetry-target summary onto every session.
        settings_extra = _settings_extra()

        sessions: list[Session] = []
        for path in files:
            session_id = os.path.basename(path)[:-6]  # strip ".jsonl"
            try:
                sess = _session_from_file(path, session_id, settings_extra)
            except Exception as exc:
                # Never let one bad session sink the whole list.
                logger.warning("QwenCodeAdapter: skipping bad session %s: %s", path, exc)
                continue
            if sess is not None:
                sessions.append(sess)

        # Sort by logical activity time, newest first. We sort on the parsed
        # timestamp (last record / mtime fallback), NOT raw file mtime, so the
        # ordering is deterministic across a git checkout or file copy in CI.
        sessions.sort(key=lambda s: s.ended_at or s.started_at or 0.0, reverse=True)
        parents = sessions[:limit]
        # Sub-agent fan-out rides after the parent slice so a fanned-out
        # session can't starve others out of the limit budget.
        children: list[Session] = []
        for sess in parents:
            path = self._find_session_path(sess.id)
            if path:
                children.extend(self._list_subagent_sessions(
                    path, sess.id, settings_extra))
        return parents + children

    def list_events(self, session_id: str, limit: int = 500) -> list[Event]:
        """Parse one session's chat recording into unified events.

        Records are already chronological on disk (one append per turn). We
        emit, per record: a ``thinking`` event for any reasoning part, a
        ``message`` event for visible text, a ``tool_call`` event per
        functionCall, and a ``tool_result`` event for a tool-result record.
        """
        path = self._find_session_path(session_id)
        if not path:
            return []

        events: list[Event] = []
        seq = 0
        for obj in _iter_records(path):
            if len(events) >= limit:
                break
            rtype = obj.get("type") or ""
            if rtype == "system":
                # attribution_snapshot / ui_telemetry — not conversation.
                continue

            ts = _parse_ts(obj.get("timestamp"))
            msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            role = _norm_role(rtype, msg)
            parts = msg.get("parts")
            model = obj.get("model") if isinstance(obj.get("model"), str) else ""

            if rtype == "tool_result":
                # parts hold one or more functionResponse objects.
                if isinstance(parts, list):
                    for p in parts:
                        if not isinstance(p, dict):
                            continue
                        if len(events) >= limit:
                            break
                        fr = p.get("functionResponse")
                        if not isinstance(fr, dict):
                            continue
                        resp = fr.get("response")
                        content = ""
                        if isinstance(resp, dict):
                            out = resp.get("output")
                            content = out if isinstance(out, str) else json.dumps(resp)
                        elif resp is not None:
                            content = json.dumps(resp)
                        seq += 1
                        events.append(Event(
                            agent=_AGENT,
                            session_id=session_id,
                            id=f"{session_id}:{seq}",
                            type="tool_result",
                            ts=ts,
                            role="tool",
                            content=content,
                            tool_name=fr.get("name") or "",
                            extra={"toolCallId": fr.get("id") or ""},
                        ))
                continue

            # user / assistant records: split parts into thinking, text, calls.
            visible, reasoning = _parts_text(parts)

            if reasoning:
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="thinking",
                    ts=ts,
                    role=role or "assistant",
                    content=reasoning,
                    tokens=0,
                    extra={"model": model} if model else {},
                ))

            if visible:
                seq += 1
                events.append(Event(
                    agent=_AGENT,
                    session_id=session_id,
                    id=f"{session_id}:{seq}",
                    type="message",
                    ts=ts,
                    role=role,
                    content=visible,
                    tokens=self._record_output_tokens(obj),
                    extra={"model": model} if model else {},
                ))

            # Each functionCall part becomes its own tool_call event.
            if isinstance(parts, list):
                for p in parts:
                    if not isinstance(p, dict):
                        continue
                    if len(events) >= limit:
                        break
                    fc = p.get("functionCall")
                    if not isinstance(fc, dict):
                        continue
                    name = fc.get("name") or "unknown"
                    seq += 1
                    events.append(Event(
                        agent=_AGENT,
                        session_id=session_id,
                        id=f"{session_id}:{seq}",
                        type="tool_call",
                        ts=ts,
                        role=role or "assistant",
                        tool_name=name,
                        tool_calls=[{
                            "id": fc.get("id") or "",
                            "name": name,
                            "arguments": fc.get("args"),
                        }],
                        extra={"model": model} if model else {},
                    ))
        if not events:
            return []
        # Inputs & context: one context.compiled event in front of the
        # transcript (never displaces a row; the limit caps transcript rows).
        return prepend_context(events, _context_from_file(path, session_id))

    def _find_session_path(self, session_id: str) -> str | None:
        """Locate the .jsonl for a session id across project dirs.

        The same session id is the file basename, so a bounded glob across
        the one-level project dirs finds it without walking ``$HOME``.
        """
        if not session_id:
            return None
        # Namespaced sub-agent id "<parent>::agent-<id>": resolve into the
        # parent's subagents dir.
        if "::" in session_id:
            parent_id, _, stem = session_id.partition("::")
            parent_path = self._find_session_path(parent_id)
            if not parent_path or not stem or "/" in stem:
                return None
            sub_dir = self._subagents_dir_for(parent_path, parent_id)
            if not sub_dir:
                return None
            candidate = os.path.join(sub_dir, f"{stem}.jsonl")
            return candidate if os.path.isfile(candidate) else None
        for path in self._session_files():
            if os.path.basename(path)[:-6] == session_id:
                return path
        return None

    @staticmethod
    def _record_output_tokens(obj: dict[str, Any]) -> int:
        """Output (candidate) token count for an assistant record, else 0."""
        usage = obj.get("usageMetadata")
        if isinstance(usage, dict):
            return _int(usage.get("candidatesTokenCount"))
        return 0

    def trail_coverage(self) -> dict:
        """Decision-trail coverage declared for this runtime (see
        ``AgentAdapter.trail_coverage``): what the on-disk format exposes and
        what this adapter actually emits, never what a model could do.
        Inputs and reasoning are declared together; each level names the
        native field it rests on in ``note``."""
        return {
            "inputs": 'partial',
            "reasoning": 'full',
            "note": ('no system prompt on disk (type=system records are attribution_snapshot / ui_telemetry); record cwd and version (every record), assistant model, first user parts text as prompt, functionCall.name invoked names only, ui_telemetry uiEvent.decision set, settings.json mcpServers names + security.auth.selectedType + telemetry.target. Reasoning: parts[].thought. Reasoning: parts flagged thought=true are split into a thinking event ahead of the visible text'),
        }

    def capabilities(self) -> set[Capability]:
        caps = set(self._base_capabilities())
        # REASONING is derived from trail_coverage so the flag and the
        # declaration can never disagree; absent on an older OSS core.
        if _CAP_REASONING is not None and self.trail_coverage()["reasoning"] != "none":
            caps.add(_CAP_REASONING)
        # INPUTS is derived the same way: declared inputs != none means the
        # adapter emits a context.compiled event (conformance-tested).
        if CAP_INPUTS is not None and self.trail_coverage()["inputs"] != "none":
            caps.add(CAP_INPUTS)
        return caps

    def _base_capabilities(self) -> set[Capability]:
        # SESSIONS + EVENTS + COST. Unlike PicoClaw, Qwen Code records real
        # usageMetadata token counts on every assistant record, so COST is
        # honestly claimed (the UI may price tokens). The USD figure itself is
        # not on disk and is left as None.
        # SUBAGENTS: agent-tool children (qwen >= ~0.17 per-agent transcript
        # + meta sidecars) are emitted with parent_id + kind + prompt/reply.
        # INPUTS is partial: no system prompt is persisted (type:"system"
        # records are attribution/ui telemetry). See trail_coverage().
        return ({Capability.SESSIONS, Capability.EVENTS,
                            Capability.COST, Capability.SUBAGENTS})

