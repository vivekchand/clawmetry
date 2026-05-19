"""
routes/reasoning.py — Reasoning chain viewer endpoint.

Implements GH #565: structured visualization of LLM thinking/reasoning content.

  GET /api/reasoning?session=SESSION_ID

Returns a structured breakdown of thinking blocks parsed from session JSONL:
- Chains: each thinking block segmented into typed logical steps
- Summary: aggregate token/efficiency stats across all chains
"""

from __future__ import annotations

import glob
import json
import os
import re

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

# Tier-1 DuckDB fast path: enable by exporting CLAWMETRY_LOCAL_STORE_READ=1.
# When set, /api/reasoning reads thinking blocks from the local events
# table instead of scanning JSONL on disk. Falls through cleanly when
# the store is empty or local_store is unimportable.

bp_reasoning = Blueprint("reasoning", __name__)

# Keyword heuristics for step classification
_PREMISE_RE = re.compile(
    r"\b(user wants|the question|looking at|need to|understand|analyz|request)\b",
    re.IGNORECASE,
)
_HYPOTHESIS_RE = re.compile(
    r"\b(if I|could use|one approach|let me try|maybe|perhaps|what if)\b",
    re.IGNORECASE,
)
_CONSTRAINT_RE = re.compile(
    r"\b(but|however|constraint|can't|won't work|problem is|issue is|limitation)\b",
    re.IGNORECASE,
)
_CONCLUSION_RE = re.compile(
    r"\b(so I should|therefore|I'll|the solution|final answer|in conclusion|thus)\b",
    re.IGNORECASE,
)


_STOP_WORDS = frozenset({
    "that", "this", "with", "from", "have", "been", "they", "what",
    "when", "will", "also", "more", "some", "your", "like", "their",
    "into", "than", "then", "these", "those", "such", "just", "about",
    "which", "where", "here", "there", "over", "only", "both", "each",
    "most", "other", "same", "very", "well", "make", "made", "want",
    "would", "could", "should", "need", "does", "done", "used", "using",
    "after", "before", "while", "being", "because", "through",
})


def _coherence_score(thinking_text: str, answer_text: str):
    """Keyword-overlap coherence score (0–100) between thinking and answer.

    Extracts ≥4-char non-stop words from each side and measures how many
    answer keywords appear in the thinking.  High overlap = thinking drove the
    answer; low overlap = possible post-hoc rationalization.

    Returns (score_int, label_str) where label is 'high', 'medium', or 'low'.
    """
    def _kw(text):
        return {w for w in re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
                if w not in _STOP_WORDS}

    think_kw = _kw(thinking_text)
    answer_kw = _kw(answer_text)
    if not answer_kw:
        return 0, "low"
    score = min(100, int(len(think_kw & answer_kw) / len(answer_kw) * 100))
    label = "high" if score >= 70 else ("medium" if score >= 35 else "low")
    return score, label


def _classify_step(text):
    """Classify a thinking step using keyword heuristics."""
    if _PREMISE_RE.search(text):
        return "premise"
    if _HYPOTHESIS_RE.search(text):
        return "hypothesis"
    if _CONSTRAINT_RE.search(text):
        return "constraint"
    if _CONCLUSION_RE.search(text):
        return "conclusion"
    return "analysis"


def _segment_thinking(text):
    """Split thinking text into logical steps and classify each."""
    # Split on double newlines first, then fallback to sentence boundaries
    raw_segments = re.split(r"\n\s*\n", text.strip())
    steps = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        # Further split very long segments at sentence boundaries (. ! ?)
        # but only if the segment is longer than ~200 chars
        if len(seg) > 200:
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", seg)
            for s in sentences:
                s = s.strip()
                if s:
                    word_count = len(s.split())
                    steps.append(
                        {
                            "type": _classify_step(s),
                            "content": s,
                            "word_count": word_count,
                        }
                    )
        else:
            word_count = len(seg.split())
            steps.append(
                {
                    "type": _classify_step(seg),
                    "content": seg,
                    "word_count": word_count,
                }
            )
    return steps


def _parse_session_reasoning(session_id):
    """Parse thinking blocks from a session JSONL file and build reasoning chains."""
    import dashboard as _d

    session_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    jsonl_path = os.path.join(session_dir, f"{session_id}.jsonl")

    chains = []

    if not os.path.isfile(jsonl_path):
        return chains

    try:
        with open(jsonl_path, "r", errors="replace") as fh:
            lines = fh.readlines()
    except Exception:
        return chains

    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except Exception:
            continue

        ts = obj.get("timestamp") or obj.get("time")
        role = obj.get("role", "")
        content_obj = obj.get("content", "")

        # Unwrap OpenClaw / claude-cli message wrappers
        if obj.get("type") in ("message", "user", "assistant") and isinstance(
            obj.get("message"), dict
        ):
            inner = obj["message"]
            role = inner.get("role", role) or obj.get("type", "")
            content_obj = inner.get("content", content_obj)

        if role != "assistant" or not isinstance(content_obj, list):
            continue

        # Collect thinking + answer blocks from this assistant turn
        thinking_blocks = []
        answer_word_count = 0
        answer_parts: list[str] = []

        for block in content_obj:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")
            if btype == "thinking":
                thinking_text = block.get("thinking", "")
                if thinking_text:
                    thinking_blocks.append(thinking_text)
            elif btype == "text":
                text = block.get("text", "") or ""
                answer_word_count += len(text.split())
                answer_parts.append(text)

        answer_text = " ".join(answer_parts)
        for thinking_text in thinking_blocks:
            steps = _segment_thinking(thinking_text)
            thinking_word_count = sum(s["word_count"] for s in steps)
            thinking_tokens = int(thinking_word_count * 1.3)
            answer_tokens = int(answer_word_count * 1.3)
            efficiency_ratio = (
                round(thinking_tokens / answer_tokens, 1) if answer_tokens > 0 else 0.0
            )
            c_score, c_label = _coherence_score(thinking_text, answer_text)
            chains.append(
                {
                    "timestamp": ts or "",
                    "thinking_tokens": thinking_tokens,
                    "answer_tokens": answer_tokens,
                    "efficiency_ratio": efficiency_ratio,
                    "steps": steps,
                    "raw_thinking": thinking_text,
                    "coherence_score": c_score,
                    "coherence_label": c_label,
                }
            )

    return chains


def _try_local_store_reasoning(session_id: str):
    """Tier-1 DuckDB fast path for /api/reasoning.

    Reads ``message`` events for the requested ``session_id`` from the
    local store, extracts thinking/text blocks from each assistant turn,
    and returns the same ``{session_id, chains, summary, _source}`` shape
    the legacy JSONL parser produces.

    Returns ``None`` to defer to the legacy fallback if:
      - the ``local_store`` module isn't importable
      - no message events exist for this session
      - no thinking blocks are present (chains would be empty)
      - any unexpected error happens (we'd rather degrade than 500)
    """
    # Issue #1282 / memory `feedback_daemon_proxy_pattern.md`: writable
    # ``get_store`` raced the sync daemon's exclusive DuckDB writer lock
    # on multi-process installs (launchd/systemd). Try the daemon HTTP
    # proxy first; fall back to a direct read-only open for single-process
    # boots (tests, dev mode).
    #
    # 2026-05-18 silent-zero bug-class fix (7th instance today, per memory
    # ``feedback_synthetic_tests_missed_real_event_shape.md`` +
    # ``reference_openclaw_v3_event_types.md``). Assistant turns land in
    # DuckDB under THREE different ``event_type`` values:
    #   * ``message``         — legacy installs, data.message.content[]
    #   * ``assistant``       — Claude Code daemon-normalised
    #   * ``model.completed`` — OpenClaw v3 daemon-normalised (no nested
    #                           message; thinking lives in
    #                           data.assistantTexts + data.completionText)
    # Querying only ``message`` returned 0 rows on real installs → the
    # Brain tab reasoning view rendered an empty timeline.
    rows = []
    try:
        from routes.local_query import local_store_via_daemon
        for et in ("message", "assistant", "model.completed"):
            sub = local_store_via_daemon(
                "query_events",
                session_id=session_id, event_type=et, limit=2000,
            )
            if sub:
                rows.extend(sub)
    except Exception:
        rows = []
    if not rows:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            for et in ("message", "assistant", "model.completed"):
                sub = store.query_events(
                    session_id=session_id, event_type=et, limit=2000,
                ) or []
                rows.extend(sub)
        except Exception:
            return None
    if not rows:
        return None

    # query_events returns most-recent-first; reasoning chains read forward
    # in time (legacy parser walks the JSONL top-to-bottom). Sort the
    # unioned list by ts to keep that contract when the three event-type
    # buckets above were merged out of order.
    rows = sorted(rows, key=lambda r: (r.get("ts") or ""))
    chains = []
    for r in rows:
        data = r.get("data") if isinstance(r, dict) else None
        if not isinstance(data, dict):
            continue

        # Resolve thinking + answer text across three shapes:
        #   (A) data.message.content = list of {type:thinking|text} blocks
        #       (legacy ``message`` + Claude-Code ``assistant``)
        #   (B) v3 ``model.completed`` with NO data.message — thinking +
        #       answer live in top-level data.{assistantTexts,
        #       completionText}. assistantTexts is a list[str] of extracted
        #       thinking; completionText is the final answer text. The
        #       daemon never emits separate ``{type:thinking}`` blocks for
        #       this shape, so we treat assistantTexts entries as
        #       independent thinking blocks.
        thinking_blocks: list[str] = []
        answer_word_count = 0
        answer_parts: list[str] = []

        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        content_obj = msg.get("content") if isinstance(msg, dict) else None

        if isinstance(content_obj, list):
            # Shape A — content-block walk
            if isinstance(msg, dict) and msg.get("role") and msg.get("role") != "assistant":
                continue
            for block in content_obj:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")
                if btype == "thinking":
                    tt = block.get("thinking", "")
                    if tt:
                        thinking_blocks.append(tt)
                elif btype == "text":
                    text = block.get("text", "") or ""
                    answer_word_count += len(text.split())
                    answer_parts.append(text)
        else:
            # Shape B — v3 model.completed. Skip non-assistant events that
            # leaked into the union (eg legacy ``message`` with role=user
            # and string content).
            et = (r.get("event_type") or "").lower()
            if et not in ("model.completed", "assistant"):
                continue
            atexts = data.get("assistantTexts")
            if isinstance(atexts, list):
                for t in atexts:
                    if isinstance(t, str) and t:
                        thinking_blocks.append(t)
            answer = data.get("completionText")
            if isinstance(answer, str) and answer:
                answer_word_count = len(answer.split())
                answer_parts.append(answer)

        ts = r.get("ts") or ""
        answer_text = " ".join(answer_parts)
        for thinking_text in thinking_blocks:
            steps = _segment_thinking(thinking_text)
            thinking_word_count = sum(s["word_count"] for s in steps)
            thinking_tokens = int(thinking_word_count * 1.3)
            answer_tokens = int(answer_word_count * 1.3)
            efficiency_ratio = (
                round(thinking_tokens / answer_tokens, 1) if answer_tokens > 0 else 0.0
            )
            c_score, c_label = _coherence_score(thinking_text, answer_text)
            chains.append({
                "timestamp":        ts,
                "thinking_tokens":  thinking_tokens,
                "answer_tokens":    answer_tokens,
                "efficiency_ratio": efficiency_ratio,
                "steps":            steps,
                "raw_thinking":     thinking_text,
                "coherence_score":  c_score,
                "coherence_label":  c_label,
            })

    if not chains:
        return None

    total_thinking_tokens = sum(c["thinking_tokens"] for c in chains)
    total_answer_tokens = sum(c["answer_tokens"] for c in chains)
    avg_efficiency = (
        round(total_thinking_tokens / total_answer_tokens, 1)
        if total_answer_tokens > 0 else 0.0
    )
    scored = [c["coherence_score"] for c in chains if c.get("coherence_score", 0) > 0]
    avg_coherence_score = int(sum(scored) / len(scored)) if scored else 0
    avg_coherence_label = "high" if avg_coherence_score >= 70 else ("medium" if avg_coherence_score >= 35 else "low")
    return {
        "session_id": session_id,
        "chains":     chains,
        "summary": {
            "total_thinking_tokens": total_thinking_tokens,
            "total_answer_tokens":   total_answer_tokens,
            "avg_efficiency":        avg_efficiency,
            "chain_count":           len(chains),
            "avg_coherence_score":   avg_coherence_score,
            "avg_coherence_label":   avg_coherence_label,
        },
        "_source": "local_store",
    }


@bp_reasoning.route("/api/reasoning")
def api_reasoning():
    """Return structured reasoning chains for a session."""
    session_id = request.args.get("session", "").strip()
    if not session_id:
        return jsonify({"error": "session parameter required"}), 400

    # Tier-1 DuckDB fast path — opt-in via CLAWMETRY_LOCAL_STORE_READ=1.
    # Falls through to legacy JSONL parser when flag is unset, the store
    # has no events for this session, or no thinking blocks are present.
    if is_local_store_read_enabled():
        fast = _try_local_store_reasoning(session_id)
        if fast is not None:
            return jsonify(fast)

    chains = _parse_session_reasoning(session_id)

    total_thinking_tokens = sum(c["thinking_tokens"] for c in chains)
    total_answer_tokens = sum(c["answer_tokens"] for c in chains)
    avg_efficiency = (
        round(total_thinking_tokens / total_answer_tokens, 1)
        if total_answer_tokens > 0
        else 0.0
    )
    scored = [c["coherence_score"] for c in chains if c.get("coherence_score", 0) > 0]
    avg_coherence_score = int(sum(scored) / len(scored)) if scored else 0
    avg_coherence_label = "high" if avg_coherence_score >= 70 else ("medium" if avg_coherence_score >= 35 else "low")

    return jsonify(
        {
            "session_id": session_id,
            "chains": chains,
            "summary": {
                "total_thinking_tokens": total_thinking_tokens,
                "total_answer_tokens": total_answer_tokens,
                "avg_efficiency": avg_efficiency,
                "chain_count": len(chains),
                "avg_coherence_score": avg_coherence_score,
                "avg_coherence_label": avg_coherence_label,
            },
        }
    )
