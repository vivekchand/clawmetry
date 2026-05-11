"""
routes/reasoning.py — Reasoning chain viewer endpoint.

Implements GH #565: structured visualization of LLM thinking/reasoning content.

  GET /api/reasoning?session=SESSION_ID

Returns a structured breakdown of thinking blocks parsed from session JSONL:
- Chains: each thinking block segmented into typed logical steps
- Summary: aggregate token/efficiency stats across all chains
"""

import glob
import json
import os
import re

from flask import Blueprint, jsonify, request

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

        for thinking_text in thinking_blocks:
            steps = _segment_thinking(thinking_text)
            thinking_word_count = sum(s["word_count"] for s in steps)
            thinking_tokens = int(thinking_word_count * 1.3)
            answer_tokens = int(answer_word_count * 1.3)
            efficiency_ratio = (
                round(thinking_tokens / answer_tokens, 1) if answer_tokens > 0 else 0.0
            )
            chains.append(
                {
                    "timestamp": ts or "",
                    "thinking_tokens": thinking_tokens,
                    "answer_tokens": answer_tokens,
                    "efficiency_ratio": efficiency_ratio,
                    "steps": steps,
                    "raw_thinking": thinking_text,
                }
            )

    return chains


@bp_reasoning.route("/api/reasoning")
def api_reasoning():
    """Return structured reasoning chains for a session."""
    session_id = request.args.get("session", "").strip()
    if not session_id:
        return jsonify({"error": "session parameter required"}), 400

    chains = _parse_session_reasoning(session_id)

    total_thinking_tokens = sum(c["thinking_tokens"] for c in chains)
    total_answer_tokens = sum(c["answer_tokens"] for c in chains)
    avg_efficiency = (
        round(total_thinking_tokens / total_answer_tokens, 1)
        if total_answer_tokens > 0
        else 0.0
    )

    return jsonify(
        {
            "session_id": session_id,
            "chains": chains,
            "summary": {
                "total_thinking_tokens": total_thinking_tokens,
                "total_answer_tokens": total_answer_tokens,
                "avg_efficiency": avg_efficiency,
                "chain_count": len(chains),
            },
        }
    )
