"""numbat_ingest.py — map Perplexity numbat NDJSON records into ClawMetry rows.

numbat (github.com/perplexityai/numbat) is an endpoint detection & response
tool for AI coding agents. It emits versioned NDJSON records — findings,
enforcement decisions, events — to a file sink (``~/.numbat/findings.ndjson``)
and/or a batched HTTP sink. ClawMetry consumes both:

- the sync daemon tails the file sink (``sync.sync_numbat_events``), and
- the dashboard accepts HTTP delivery on ``POST /api/numbat/ingest``
  (``routes/infra.py``), which numbat targets via
  ``numbat hook install --output http --http-url http://127.0.0.1:8900/api/numbat/ingest``.

This module is the single mapper both paths share (one collapse engine — the
same rule as brain_dedupe). It is pure: parse + transform only, no I/O, so it
is unit-testable without a store or server.

Mapping (destinations already exist in local_store; both ingest methods are
in the daemon-proxy allowlist):

  record_type "finding"     → security_events   (ingest_security_event)
                              + a shadow ``events`` row (event_type
                              "numbat_finding") so count-over-threshold alert
                              rules fire — the loop_detected precedent.
  record_type "enforcement" → guardrail_events  (ingest_guardrail_event)
  record_type "event"       → SKIPPED by design. numbat events describe the
                              same session activity ClawMetry already ingests
                              from the harnesses' own artifacts; ingesting
                              both would double-count Brain/usage.
  anything else             → counted in ``skipped_other``.

Idempotency: numbat's finding_id is a deterministic hash of
(rule_id, rule_version, cited event ids) and duplicate HTTP batches are by
design (retry semantics), so every mapped id is stable and the destination
upserts (ON CONFLICT / INSERT OR IGNORE) dedupe replays for free.

Schema: numbat versions its wire format independently of releases and
explicitly promises no backward compatibility. We pin on the 0.2.x line and
count (never crash on) records from unknown schema versions.
"""

from __future__ import annotations

import json
from typing import Any

# numbat wire-format line we understand (docs/schema/v0.2.0/ upstream).
# Minor bumps within 0.2.x are additive per JSON Schema semantics; anything
# else is counted as skipped_schema and reported, never ingested.
SCHEMA_PREFIX = "0.2."

# numbat source_agent → ClawMetry runtime prefix for canonical session ids
# (ClawMetry family adapters key sessions as "<runtime>:<native-id>", e.g.
# "claude_code:UUID"). numbat uses kebab-case agent names; ours are
# snake_case. Unknown agents fall through to snake_cased kebab, which keeps
# attribution stable even for harnesses ClawMetry has no adapter for yet
# (windsurf, kiro, goose, …).
_AGENT_TO_RUNTIME = {
    "claude-code": "claude_code",
    "codex": "codex",
    "cursor": "cursor",
    "gemini-cli": "gemini_cli",
    "openclaw": "openclaw",
    "opencode": "opencode",
    "qwen-code": "qwen_code",
    "hermes": "hermes",
    "antigravity": "antigravity",
    "pi": "pi",
}

_SEVERITIES = ("info", "low", "medium", "high", "critical")

SHADOW_EVENT_TYPE = "numbat_finding"


def runtime_for_agent(source_agent: str | None) -> str:
    agent = (source_agent or "").strip().lower()
    if not agent:
        return "numbat"
    return _AGENT_TO_RUNTIME.get(agent, agent.replace("-", "_"))


def _canonical_session_id(rec: dict[str, Any]) -> str | None:
    sid = rec.get("session_id")
    if not sid:
        return None
    runtime = runtime_for_agent(rec.get("source_agent"))
    if runtime == "numbat":
        return str(sid)
    return f"{runtime}:{sid}"


def _norm_ts(value: Any) -> str | None:
    """RFC3339 ('2026-08-01T12:34:56.789Z') → the '%Y-%m-%dT%H:%M:%S' shape
    the security/guardrail tables use for string-ordered comparisons."""
    if not value or not isinstance(value, str):
        return None
    return value.replace("Z", "").replace("+00:00", "")[:19] or None


def parse_records(text: str) -> tuple[list[dict[str, Any]], int]:
    """Split an NDJSON body into record dicts. Returns (records, bad_lines).
    Never raises: malformed lines are counted, not fatal (numbat can
    interleave schema versions in one stream)."""
    records: list[dict[str, Any]] = []
    bad = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            bad += 1
            continue
        if isinstance(rec, dict):
            records.append(rec)
        else:
            bad += 1
    return records, bad


def map_finding(rec: dict[str, Any]) -> dict[str, Any] | None:
    """finding record → ingest_security_event payload."""
    fid = rec.get("finding_id")
    if not fid:
        return None
    severity = rec.get("severity")
    if severity not in _SEVERITIES:
        severity = "info"
    snippet = ""
    for key in (
        "observed_command",
        "observed_url",
        "observed_file_path",
        "observed_content_preview",
    ):
        val = rec.get(key)
        if val:
            snippet = str(val)
            break
    return {
        "id": f"numbat_{fid}",
        "ts": _norm_ts(rec.get("timestamp")) or _norm_ts(rec.get("detected_at")),
        "type": "numbat_finding",
        "severity": severity,
        "session_id": _canonical_session_id(rec),
        "rule_id": rec.get("rule_id"),
        "description": rec.get("title") or rec.get("rule_id") or "numbat finding",
        # numbat redacts secrets before emission; still cap length like the
        # native threat scanner does.
        "snippet": snippet[:200],
    }


def map_enforcement(rec: dict[str, Any]) -> dict[str, Any] | None:
    """enforcement record → ingest_guardrail_event payload."""
    did = rec.get("decision_id")
    if not did:
        return None
    decision = rec.get("decision") or ""
    rule_ids = rec.get("rule_ids") or []
    rule_name = rec.get("deny_rule_id") or (rule_ids[0] if rule_ids else "numbat")
    return {
        "id": f"numbat_{did}",
        "ts": _norm_ts(rec.get("timestamp")),
        "rule_name": rule_name,
        "verdict": decision,
        "session_id": _canonical_session_id(rec),
        # guardrail_events.action is the effect: numbat only ever denies or
        # passes through ("no_override"), and mode/reason explain why.
        "action": "blocked" if decision == "deny" else (rec.get("reason") or "monitored"),
        "latency_ms": None,
    }


def finding_summary(rec: dict[str, Any]) -> str:
    """One human-readable line for a finding: what happened, how bad, which
    rule. This is what the activity feed shows the user."""
    sev = str(rec.get("severity") or "").upper()
    title = rec.get("title") or rec.get("rule_id") or "security finding"
    rule = rec.get("rule_id") or ""
    line = f"{sev} · {title}" if sev else str(title)
    if rule and rule != title:
        line = f"{line} ({rule})"
    return line


def is_live_finding(rec: dict[str, Any]) -> bool:
    """True for findings observed as the agent acts (hooks / OTLP logs).

    ``source_type="artifact"`` findings come from ``numbat scan`` re-reading
    historical transcripts — one scan of a year of history emits thousands at
    once. Those belong on the Security surface, NOT in the live activity feed
    (which is a stream of what's happening now) and NOT in alert-rule
    thresholds, where a single backfill would look like a live incident storm.
    """
    return rec.get("source_type") in ("hook", "otel")


def map_finding_shadow_event(rec: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    """finding record → events-table shadow row so event_type-based alert
    rules fire (the proxy.py loop_detected precedent). Daemon-side only:
    LocalStore.ingest needs node_id and isn't proxy-allowlisted.

    Returns None for at-rest scan findings — see is_live_finding()."""
    fid = rec.get("finding_id")
    if not fid or not node_id:
        return None
    if not is_live_finding(rec):
        return None
    ts = _norm_ts(rec.get("timestamp")) or _norm_ts(rec.get("detected_at"))
    if not ts:
        return None
    return {
        "id": f"numbat_finding_{fid}",
        "node_id": node_id,
        "agent_type": runtime_for_agent(rec.get("source_agent")),
        "event_type": SHADOW_EVENT_TYPE,
        "ts": ts,
        "session_id": _canonical_session_id(rec),
        # ``summary`` is load-bearing: routes/brain.py's detail extractor
        # looks for summary/text/name/... — without it every row rendered
        # blank in the activity feed (founder screenshot 2026-08-01).
        # Payload stays lean otherwise (snapshot bloat rule).
        "data": json.dumps(
            {
                "summary": finding_summary(rec),
                "rule_id": rec.get("rule_id"),
                "severity": rec.get("severity"),
                "title": rec.get("title"),
                "source_agent": rec.get("source_agent"),
            }
        ),
    }


def schema_supported(rec: dict[str, Any]) -> bool:
    return str(rec.get("schema_version", "")).startswith(SCHEMA_PREFIX)


def map_records(
    records: list[dict[str, Any]], node_id: str = ""
) -> dict[str, Any]:
    """Route parsed records to their destinations.

    Returns {security_events, guardrail_events, shadow_events, findings_raw,
    skipped_schema, skipped_events, skipped_other} — findings_raw carries the
    original finding records so callers can fire severity-based alerts
    without re-parsing."""
    out: dict[str, Any] = {
        "security_events": [],
        "guardrail_events": [],
        "shadow_events": [],
        "findings_raw": [],
        "skipped_schema": 0,
        "skipped_events": 0,
        "skipped_other": 0,
    }
    for rec in records:
        if not schema_supported(rec):
            out["skipped_schema"] += 1
            continue
        rtype = rec.get("record_type")
        if rtype == "finding":
            sec = map_finding(rec)
            if sec is None:
                out["skipped_other"] += 1
                continue
            out["security_events"].append(sec)
            out["findings_raw"].append(rec)
            shadow = map_finding_shadow_event(rec, node_id)
            if shadow is not None:
                out["shadow_events"].append(shadow)
        elif rtype == "enforcement":
            gr = map_enforcement(rec)
            if gr is None:
                out["skipped_other"] += 1
                continue
            out["guardrail_events"].append(gr)
        elif rtype == "event":
            # Deliberate: numbat events mirror session activity ClawMetry
            # already ingests from the same on-disk artifacts — storing both
            # would double-count Brain/usage (the 33%-dedupe class of bug,
            # inverted).
            out["skipped_events"] += 1
        else:
            # indicator / scan_summary / diagnostic / future types
            out["skipped_other"] += 1
    return out
