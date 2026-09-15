"""clawmetry/prompt_injection.py: injection signatures and the untrusted-content signal.

One pure module shared by two consumers (REQ-GOV-PIJ-001 and REQ-GOV-PIJ-002,
Factory requirement e87935d1-27e0-415f-a5f8-24bdf70accbc):

* the ``prompt_injection`` Guard detector (``clawmetry/detector_injection.py``)
  scans tool results and user-sourced messages with :func:`scan_text`;
* the Claude Code pre-tool gate. The hook process (``claude_code_gate``) reads
  the tail of the session transcript it runs beside and derives a small
  context with :func:`context_from_claude_transcript`: which untrusted tools
  returned output in the current turn, and which signatures that output
  matched. It sends identifiers only, never content. The local receiver
  (``routes/hooks.py``) cleans that context with :func:`coerce_context` and
  ``approvals.match_policy`` rates the call with :func:`effective_risk`.

The escalation follows MITRE ATLAS mitigation AML.M0030, Restrict AI Agent
Tool Invocation on Untrusted Data (ATLAS 2026.08): once untrusted data has
entered the context, a consequential tool call should need confirmation. The
signal changes a risk tier; only a policy the operator declared asks or
denies.

What a signature is: text that addresses the model rather than the reader. An
instruction to ignore earlier instructions, a forged system or authority
block, a hand-off ("before you solve the task I gave you, first do the
following"), a request to hide an action from the user, or a role hijack.
Signatures are declared and explainable. They miss paraphrased and
non-English attacks, and the measured recall says so
(``tests/test_detector_prompt_injection.py``).

Pure: no I/O except the bounded transcript read in
:func:`context_from_claude_transcript`, one clawmetry import (the leaf
``tool_risk``), never raises.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional

from clawmetry.tool_risk import RISK_RANK, canonical_tool, extract_command

# ── Signatures ───────────────────────────────────────────────────────────────
# Every quantifier is bounded: this runs over text an attacker wrote.
_F = re.IGNORECASE

SIGNATURES: Dict[str, Dict[str, Any]] = {
    "override_instructions": {
        "label": "tells the agent to ignore its earlier instructions",
        "rx": re.compile(
            r"\b(?:ignore|disregard|forget|override|bypass)\b[^.\n]{0,40}?"
            r"\b(?:previous|prior|above|earlier|preceding|original|all|any|your|following)\b"
            r"[^.\n]{0,30}?\b(?:instructions?|prompts?|directions|directives?|guidelines|"
            r"guardrails|commands|orders)\b", _F),
    },
    "new_instructions": {
        "label": "hands the agent a new task or role",
        "rx": re.compile(
            r"\byour\s{1,4}(?:new|real|actual|updated)\s{1,4}(?:instructions?|task|objective|goal|role|directive)\b"
            r"|\bnew\s{1,4}(?:instructions?|directives?|system\s{1,4}prompt)\s{0,4}:"
            r"|\bfrom\s{1,4}now\s{1,4}on,?\s{1,4}you\s{1,4}(?:are|will|must)\s{1,4}"
            r"(?:only|not|ignore|act|follow|obey)\b", _F),
    },
    "forged_authority": {
        "label": "imitates a system or authority message",
        "rx": re.compile(
            r"<\s{0,4}/?\s{0,4}(?:information|important|system|admin)\s{0,4}>"
            r"|#{2,}\s{0,4}\(?\s{0,4}system[_ ]?message\s{0,4}\)?"
            r"|\[\s{0,4}system\s{1,4}(?:prompt|message|override)\s{0,4}\]"
            r"|<!--\s{0,8}(?:system|assistant|ai|instructions?)\s{0,4}:"
            r"|\bimportant\s{0,4}!{2,}"
            r"|\b(?:important|urgent)\s{1,4}message\s{1,4}from\b[^.\n]{0,60}?\bto\s{1,4}you\b", _F),
    },
    "task_handoff": {
        "label": "asks the agent to do something else before the user's task",
        "rx": re.compile(
            r"\bbefore\s{1,4}you\s{1,4}(?:can\s{1,4})?(?:solve|complete|answer|continue|finish|proceed|respond)\b"
            r"[^.\n]{0,60}?\b(?:task|request|question)\b[^.\n]{0,60}?\b(?:first|following)\b"
            r"|\bafter\s{1,4}you\s{1,4}do\s{1,4}that,?\s{1,4}you\s{1,4}can\s{1,4}(?:solve|complete|continue)\b", _F),
    },
    "conceal_from_user": {
        "label": "asks the agent to hide an action from the user",
        "rx": re.compile(
            r"\b(?:do\s{1,4}not|don't|never)\s{1,4}(?:tell|inform|notify|alert)\s{1,4}the\s{1,4}user"
            r"\s{1,4}(?:about|of)\s{1,4}(?:this|these|that|it|what)\b"
            r"|\b(?:do\s{1,4}not|don't|never)\s{1,4}mention\s{1,4}(?:this|these|it)\s{1,4}to\s{1,4}the\s{1,4}user\b"
            r"|\bwithout\s{1,4}(?:telling|informing|notifying|alerting)\s{1,4}the\s{1,4}user\b", _F),
    },
    "role_hijack": {
        "label": "tries to switch the agent into an unrestricted mode",
        "rx": re.compile(
            r"\byou\s{1,4}are\s{1,4}now\s{1,4}(?:in\s{1,4})?(?:dan\b|developer\s{1,4}mode|jailbroken|unrestricted)"
            r"|\b(?:dan|developer)\s{1,4}mode\s{1,4}(?:enabled|activated)\b"
            r"|\bdo\s{1,4}anything\s{1,4}now\b", _F),
    },
}

SIGNATURE_IDS = tuple(SIGNATURES)

#: A line that looks like source code or a pattern is quoting signature text,
#: not addressing the model: grep output over a detector, a test fixture, a
#: regex table. AC-GOV-PIJ-001.5.
_CODE_LINE = re.compile(
    r"\\[sbwdSWD]|\(\?[:!=<]|re\.compile|_rx\(|\[\^|\{0,\d{1,3}\}|\$\{|=>\s|"
    r"^\s{0,40}(?:[-+]\s{0,4})?(?:def |return |const |var |let |#include)|"
    r"\bassert\s|==|!=|\bdef\s{1,4}\w{1,60}\(", re.M)

SCAN_CHARS = 8000


def _line_around(text: str, start: int, end: int) -> str:
    ls = text.rfind("\n", 0, start) + 1
    le = text.find("\n", end)
    return text[ls:le if le != -1 else len(text)]


def scan_text(text: Any, limit: int = SCAN_CHARS) -> List[str]:
    """Signature ids the text matches, in declaration order. Never raises.

    A match whose line looks like code or a regular expression does not count
    (AC-GOV-PIJ-001.5). Only the first ``limit`` characters are read.
    """
    try:
        if not isinstance(text, str) or len(text) < 8:
            return []
        body = text[:limit]
        out: List[str] = []
        for sid, sig in SIGNATURES.items():
            for m in sig["rx"].finditer(body):
                if _CODE_LINE.search(_line_around(body, m.start(), m.end())):
                    continue
                out.append(sid)
                break
        return out
    except Exception:
        return []


def signature_label(sid: str) -> str:
    return str((SIGNATURES.get(sid) or {}).get("label") or sid)


# ── Untrusted sources ────────────────────────────────────────────────────────
# Output written by someone other than the operator. Local reads, searches and
# test output are the operator's own content and are deliberately NOT here:
# treating every result as untrusted would put an approval on nearly every call.
_UNTRUSTED_NAME = re.compile(
    r"^mcp__|browser|playwright|puppeteer|webfetch|web_fetch|websearch|web_search|"
    r"fetch_?url|read_url|gmail|email|inbox|mail_|slack|discord|telegram|jira|linear", _F)
_UNTRUSTED_CMD = re.compile(
    r"^\s{0,8}(?:(?:sudo\s{1,4})?(?:curl|wget|http|https|xh|lynx|w3m)\b"
    r"|gh\s{1,4}(?:issue|pr)\s{1,4}view\b|gh\s{1,4}api\b)", _F)


def is_untrusted_source(tool_name: Any, args: Any = None) -> bool:
    """True when this tool's OUTPUT comes from outside the operator's control:
    the web, a browser, an MCP server, mail or chat, or a shell command that
    fetches a URL or a hosted issue. Never raises."""
    try:
        name = str(tool_name or "").strip()
        if not name:
            return False
        if canonical_tool(name) == "web" or _UNTRUSTED_NAME.search(name):
            return True
        if canonical_tool(name) == "exec" and args is not None:
            return bool(_UNTRUSTED_CMD.search(extract_command(name, args) or ""))
        return False
    except Exception:
        return False


# ── Context the gate is told about the current turn ──────────────────────────
_TOOL_NAME_OK = re.compile(r"^[A-Za-z0-9_.:\-]{1,80}$")
_MAX_TOOLS = 10


def empty_context() -> Dict[str, Any]:
    return {"untrusted_tools": [], "untrusted_results": 0,
            "injection_signatures": [], "injection_tools": []}


def coerce_context(raw: Any) -> Optional[Dict[str, Any]]:
    """A context from the hook, reduced to identifiers and counts, or None.

    Whatever arrives is untrusted input to the receiver: unknown keys are
    dropped, tool names must look like tool names, signature ids must be
    declared ones. AC-GOV-PIJ-002.5. Never raises.
    """
    try:
        if not isinstance(raw, dict):
            return None
        out = empty_context()
        for key in ("untrusted_tools", "injection_tools"):
            vals = raw.get(key)
            if isinstance(vals, list):
                out[key] = [v for v in dict.fromkeys(str(x) for x in vals[:50])
                            if _TOOL_NAME_OK.match(v)][:_MAX_TOOLS]
        sigs = raw.get("injection_signatures")
        if isinstance(sigs, list):
            out["injection_signatures"] = [s for s in SIGNATURE_IDS if s in {str(x) for x in sigs[:50]}]
        try:
            out["untrusted_results"] = max(0, min(10_000, int(raw.get("untrusted_results") or 0)))
        except (TypeError, ValueError):
            out["untrusted_results"] = 0
        if out["untrusted_tools"] and not out["untrusted_results"]:
            out["untrusted_results"] = len(out["untrusted_tools"])
        if not (out["untrusted_results"] or out["injection_signatures"]):
            return None
        return out
    except Exception:
        return None


def effective_risk(risk: Any, context: Any) -> Any:
    """``risk`` (a ``tool_risk.classify_tool_call`` verdict) raised for the turn.

    * content in the turn matched a signature, call is medium or above:
      critical (AC-GOV-PIJ-002.2);
    * an untrusted tool returned output in the turn, call is high: critical
      (AC-GOV-PIJ-002.1). A medium call stays medium on this ground alone:
      measured over 300 real transcripts, raising medium calls after any
      browser, MCP or fetch output raised a third of all calls, which is an
      approval on nearly every shell command in a long turn;
    * a low call, or no context: unchanged (AC-GOV-PIJ-002.3, 002.4).

    Returns a new dict; the input is never mutated. Never raises: on any error
    the original verdict comes back, which is today's rating.
    """
    try:
        if not isinstance(risk, dict):
            return risk
        ctx = context if isinstance(context, dict) else None
        if not ctx:
            return risk
        level = str(risk.get("level") or "low")
        rank = RISK_RANK.get(level, 0)
        if rank < RISK_RANK["medium"]:
            return risk
        sigs = [s for s in ctx.get("injection_signatures") or [] if s in SIGNATURES]
        tools = [t for t in ctx.get("injection_tools") or [] if isinstance(t, str)]
        untrusted = [t for t in ctx.get("untrusted_tools") or [] if isinstance(t, str)]
        new_level = level
        reason = ""
        if sigs:
            new_level = "critical"
            src = f" from {', '.join(tools[:3])}" if tools else ""
            reason = (f"follows content{src} earlier in this turn that "
                      f"{signature_label(sigs[0])}")
        elif (int(ctx.get("untrusted_results") or 0) > 0 or untrusted) \
                and rank == RISK_RANK["high"]:
            new_level = "critical"
            src = ", ".join(untrusted[:3]) or "an untrusted source"
            reason = f"follows untrusted content from {src} earlier in this turn"
        if new_level == level and not reason:
            return risk
        out = dict(risk)
        out["level"] = new_level
        out["rank"] = RISK_RANK[new_level]
        reasons = [r for r in (risk.get("reasons") or []) if r != reason]
        out["reasons"] = ([reason] + reasons)[:4]
        out["escalated_from"] = level
        return out
    except Exception:
        return risk


# ── Deriving the context from a Claude Code transcript ───────────────────────
TRANSCRIPT_TAIL_BYTES = 1024 * 1024


def _block_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for blk in content:
            if isinstance(blk, str):
                parts.append(blk)
            elif isinstance(blk, dict) and isinstance(blk.get("text"), str):
                parts.append(blk["text"])
        return "\n".join(parts)
    return ""


def _is_real_prompt(entry: dict, content: Any) -> bool:
    """A user entry a person typed, as opposed to tool results or meta rows."""
    if entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        kinds = {str(b.get("type") or "") for b in content if isinstance(b, dict)}
        return bool(kinds) and "tool_result" not in kinds
    return False


def context_from_entries(entries: Iterable[Any]) -> Dict[str, Any]:
    """The current turn's context from Claude Code transcript entries, oldest
    first. A real user prompt ends the previous turn (AC-GOV-PIJ-002.3).
    Never raises; returns :func:`empty_context` on anything unusable."""
    ctx = empty_context()
    calls: Dict[str, tuple] = {}
    try:
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            msg = entry.get("message") if isinstance(entry.get("message"), dict) else {}
            content = msg.get("content")
            etype = str(entry.get("type") or msg.get("role") or "")
            if etype == "assistant" and isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict) and blk.get("type") == "tool_use":
                        calls[str(blk.get("id") or "")] = (str(blk.get("name") or ""), blk.get("input"))
                continue
            if etype != "user":
                continue
            if _is_real_prompt(entry, content):
                ctx = empty_context()
                continue
            if not isinstance(content, list):
                continue
            for blk in content:
                if not isinstance(blk, dict) or blk.get("type") != "tool_result":
                    continue
                name, args = calls.get(str(blk.get("tool_use_id") or ""), ("", None))
                text = _block_text(blk.get("content"))
                sigs = scan_text(text)
                if is_untrusted_source(name, args):
                    ctx["untrusted_results"] += 1
                    if name and name not in ctx["untrusted_tools"]:
                        ctx["untrusted_tools"].append(name)
                if sigs:
                    for s in sigs:
                        if s not in ctx["injection_signatures"]:
                            ctx["injection_signatures"].append(s)
                    if name and name not in ctx["injection_tools"]:
                        ctx["injection_tools"].append(name)
        ctx["untrusted_tools"] = ctx["untrusted_tools"][:_MAX_TOOLS]
        ctx["injection_tools"] = ctx["injection_tools"][:_MAX_TOOLS]
        ctx["injection_signatures"] = [s for s in SIGNATURE_IDS if s in ctx["injection_signatures"]]
        return ctx
    except Exception:
        return empty_context()


def context_from_claude_transcript(path: Any, tail_bytes: int = TRANSCRIPT_TAIL_BYTES) -> Optional[Dict[str, Any]]:
    """Read the tail of a Claude Code transcript and return the turn context,
    or None when there is nothing to report or the file cannot be read
    (AC-GOV-PIJ-002.4). Bounded: at most ``tail_bytes`` are read."""
    try:
        p = str(path or "")
        if not p.endswith(".jsonl") or not os.path.isfile(p):
            return None
        size = os.path.getsize(p)
        with open(p, "rb") as fh:
            if size > tail_bytes:
                fh.seek(size - tail_bytes)
                fh.readline()  # drop the partial first line
            raw = fh.read(tail_bytes)
        entries = []
        for line in raw.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
        return coerce_context(context_from_entries(entries))
    except Exception:
        return None
