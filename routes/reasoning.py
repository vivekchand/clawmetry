"""
routes/reasoning.py — Reasoning chain viewer endpoint.

Implements GH #565: structured visualization of LLM thinking/reasoning content.
Extends  GH #572: coherence score — detect when reasoning doesn't support the answer.

  GET /api/reasoning?session=SESSION_ID

Returns a structured breakdown of thinking blocks parsed from session JSONL:
- Chains: each thinking block segmented into typed logical steps
- Summary: aggregate token/efficiency stats + avg coherence across all chains
"""

import glob
import json
import os
import re

from flask import Blueprint, jsonify, request

bp_reasoning = Blueprint("reasoning", __name__)

# ── Coherence scoring (GH #572) ──────────────────────────────────────────────

_STOP_WORDS = frozenset(
    "the a an and or but in on at to for of with is are was were be been "
    "have has had do does did will would could should may might must shall "
    "i we you he she it they this that these those which who what when "
    "how why where my your his her our their its if then else so because "
    "as by from into through out up down about after before between over "
    "under more most some all any no not just also only even still same "
    "can need want get go make take see know think look say come back "
    "let set use put show keep run try give very well good great here "
    "there now then too such each both few many much since while".split()
)


def _extract_keywords(text):
    """Return significant lowercase words (≥4 chars, not stop words)."""
    return {
        w
        for w in re.findall(r"[a-z]{4,}", text.lower())
        if w not in _STOP_WORDS
    }


def _coherence_score(thinking_text, answer_text):
    """Compute a reasoning coherence score (0–100) and label.

    Measures keyword overlap between the thinking block and the final answer.
    High overlap → thinking vocabulary appears in the answer → likely genuine.
    Low overlap → thinking may be post-hoc rationalization or boilerplate.

    Returns (score: int, label: str) where label is "high" | "medium" | "low".
    """
    if not thinking_text or not answer_text:
        return 0, "low"
    think_kw = _extract_keywords(thinking_text)
    answer_kw = _extract_keywords(answer_text)
    if not think_kw or not answer_kw:
        return 0, "low"
    overlap = len(think_kw & answer_kw)
    score = min(100, round(overlap / len(answer_kw) * 100))
    if score >= 70:
        label = "high"
    elif score >= 35:
        label = "medium"
    else:
        label = "low"
    return score, label


# ── Step classification ───────────────────────────────────────────────────────

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
        answer_texts = []

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
                if text:
                    answer_texts.append(text)

        answer_combined = " ".join(answer_texts)

        for thinking_text in thinking_blocks:
            steps = _segment_thinking(thinking_text)
            thinking_word_count = sum(s["word_count"] for s in steps)
            thinking_tokens = int(thinking_word_count * 1.3)
            answer_tokens = int(answer_word_count * 1.3)
            efficiency_ratio = (
                round(thinking_tokens / answer_tokens, 1) if answer_tokens > 0 else 0.0
            )
            c_score, c_label = _coherence_score(thinking_text, answer_combined)
            chains.append(
                {
                    "timestamp": ts or "",
                    "thinking_tokens": thinking_tokens,
                    "answer_tokens": answer_tokens,
                    "efficiency_ratio": efficiency_ratio,
                    "coherence_score": c_score,
                    "coherence_label": c_label,
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

    scored_chains = [c for c in chains if c["coherence_score"] > 0]
    avg_coherence_score = (
        round(sum(c["coherence_score"] for c in scored_chains) / len(scored_chains))
        if scored_chains
        else 0
    )
    if avg_coherence_score >= 70:
        avg_coherence_label = "high"
    elif avg_coherence_score >= 35:
        avg_coherence_label = "medium"
    else:
        avg_coherence_label = "low"

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
