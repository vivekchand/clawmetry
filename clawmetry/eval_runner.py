"""
clawmetry/eval_runner.py — Local-first LLM-as-judge scoring of completed sessions.

This is the MOAT-aligned eval surface (refs #1619 Phase 1 of 4): every
competitor (LangSmith, Langfuse, Phoenix, Helicone) cloud-hosts their eval
product — your prompts + responses leave the box for scoring. ClawMetry runs
the judge LLM call on the user's existing API key, persists the score to the
local DuckDB, and never roundtrips through ClawMetry cloud for scoring. The
cloud only sees the pre-computed aggregate that arrives via the normal
heartbeat-piggyback channel.

Design constraints (see CLAUDE.md + PRD #1619):
  * No new auth path — reuse the user's ANTHROPIC_API_KEY / OPENAI_API_KEY,
    same envelope clawmetry/interceptor.py already monkey-patches.
  * No cloud roundtrip for scoring — judge call goes provider-direct.
  * Cost guard — skip <10-token sessions (trivial heartbeats) and cap at
    100 sessions/hour (worst-case ~$2.40/day per user with Haiku).
  * Default-on but disable-able via CLAWMETRY_EVALS_ENABLED=0.
  * Configurable judge model + rubric in ~/.clawmetry/evals.yaml.
  * Failure is best-effort — judge LLM down → eval_score stays NULL, log
    a warning, scheduler tries again on the next pass. Never crashes the
    daemon.

Public API:
    EvalRunner(rubric_name='default')
        .score_session(session_id, *, dry_run=False) -> EvalResult | None
    load_rubric(name='default') -> dict   # rubric YAML → dict (with defaults)
    parse_score(text) -> (score, reason)  # exposed for testing
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

log = logging.getLogger("clawmetry.eval_runner")


# ── Config ─────────────────────────────────────────────────────────────────────

# Disable the whole eval surface (env switch). Default-on per PRD; user
# escape hatch for cost-sensitive or air-gapped setups.
def is_enabled() -> bool:
    """Env-gated kill switch. Default True (Phase 1 ships default-on)."""
    return os.environ.get("CLAWMETRY_EVALS_ENABLED", "1") not in ("0", "false", "False", "")


# Rate-limit knobs — bound worst-case spend even with a chatty workspace.
# 100/hour × $0.001/Haiku call = ~$2.40/day ceiling, well inside the
# PRD cost envelope. Overridable for ops tuning.
RATE_LIMIT_PER_HOUR = int(os.environ.get("CLAWMETRY_EVALS_RATE_LIMIT", "100"))
# Sessions below this token budget are trivial heartbeats / smoke pings;
# scoring them wastes judge spend and skews the rubric average.
MIN_TOKENS_FOR_SCORING = int(os.environ.get("CLAWMETRY_EVALS_MIN_TOKENS", "10"))
# Judge HTTP timeout — Haiku is fast (<2s typical); cap at 30s so a slow
# judge can't stall the whole scheduler tick.
JUDGE_TIMEOUT_SECS = float(os.environ.get("CLAWMETRY_EVALS_JUDGE_TIMEOUT", "30"))

# Rubric config path. Single file with one top-level dict per rubric name.
RUBRIC_PATH = Path(
    os.environ.get(
        "CLAWMETRY_EVALS_RUBRIC_PATH",
        os.path.expanduser("~/.clawmetry/evals.yaml"),
    )
)


# Default rubric — used when ~/.clawmetry/evals.yaml is absent or doesn't
# define the requested rubric. Codified inline so a fresh install scores
# sessions out of the box without any user setup.
DEFAULT_RUBRIC: dict[str, Any] = {
    "judge_model": "claude-haiku-4-5",
    "prompt": (
        "You're evaluating an AI agent's response. Score 0-5:\n"
        "  5: Fully addressed user's request, correct and complete\n"
        "  4: Mostly correct, minor gaps\n"
        "  3: Partial answer, missed key points\n"
        "  2: Misunderstood the request\n"
        "  1: Wrong or harmful answer\n"
        "  0: Failed to respond\n"
        "Output exactly two lines:\n"
        "SCORE: <0-5>\n"
        "REASON: <one short sentence>"
    ),
}


# Default-rubric YAML written to disk on first save when no file exists.
# Kept in sync with DEFAULT_RUBRIC above so what the user sees in the
# editor matches what the runner uses out of the box.
DEFAULT_RUBRIC_YAML = (
    "# clawmetry evals rubric — edited via the dashboard or by hand.\n"
    "# See clawmetry/eval_runner.py for the in-code default.\n"
    "default:\n"
    "  judge_model: claude-haiku-4-5\n"
    "  prompt: |\n"
    "    You're evaluating an AI agent's response. Score 0-5:\n"
    "      5: Fully addressed user's request, correct and complete\n"
    "      4: Mostly correct, minor gaps\n"
    "      3: Partial answer, missed key points\n"
    "      2: Misunderstood the request\n"
    "      1: Wrong or harmful answer\n"
    "      0: Failed to respond\n"
    "    Output exactly two lines:\n"
    "    SCORE: <0-5>\n"
    "    REASON: <one short sentence>\n"
)


# Centralised event-type set so the bug-class gate (PRD: real v3 event
# shapes) stays satisfied as new shapes appear. Mirrors the canonical
# union-set pattern documented in clawmetry/local_store.py
# (``_ASSISTANT_EVENT_TYPES``) — prompt + assistant turns across legacy
# and OpenClaw v3 shapes.
_PROMPT_EVENT_TYPES = (
    "prompt.submitted",   # OpenClaw v3
    "message",            # legacy + Claude Code synthetic
    "user",               # OpenClaw v3 user-turn
    "subagent:user",      # OpenClaw v3 sub-agent user-turn
)
_RESPONSE_EVENT_TYPES = (
    "model.completed",    # OpenClaw v3 main agent completion
    "assistant",          # OpenClaw v3 assistant turn
    "message",            # legacy + Claude Code synthetic
    "subagent:assistant", # OpenClaw v3 sub-agent assistant turn
)


# ── Rubric loading ─────────────────────────────────────────────────────────────


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    """Parse a YAML file into a dict. Falls back to a minimal parser when
    PyYAML isn't installed (we don't want a new dep just for evals)."""
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        return _minimal_yaml_parse(text)
    except Exception as e:
        log.warning("evals: rubric YAML parse failed (%s); using defaults", e)
        return {}


def _minimal_yaml_parse(text: str) -> dict[str, Any]:
    """Tiny YAML subset parser — handles the rubric shape only.

    Format supported:
        <name>:
          judge_model: <str>
          prompt: |
            <multi-line>

    Returns ``{name: {judge_model, prompt}, ...}``. Anything outside that
    shape is ignored. This exists so installs without PyYAML still get a
    working rubric editor; the dependency is optional.
    """
    out: dict[str, Any] = {}
    cur_name: str | None = None
    cur_dict: dict[str, Any] | None = None
    in_block: str | None = None
    block_lines: list[str] = []
    block_indent: int | None = None
    for raw in text.splitlines():
        if raw.strip().startswith("#") or not raw.strip():
            if in_block is not None:
                # blank lines inside a block scalar are preserved
                block_lines.append("")
            continue
        # Block scalar accumulator
        if in_block is not None and cur_dict is not None:
            stripped = raw.rstrip()
            indent = len(raw) - len(raw.lstrip(" "))
            if block_indent is None:
                block_indent = indent if indent > 0 else 4
            if indent >= block_indent and stripped:
                block_lines.append(raw[block_indent:])
                continue
            # Dedented out of block — flush.
            cur_dict[in_block] = "\n".join(block_lines).rstrip() + "\n"
            in_block = None
            block_lines = []
            block_indent = None
        m_top = re.match(r"^([A-Za-z0-9_\-]+):\s*$", raw)
        if m_top:
            cur_name = m_top.group(1)
            cur_dict = {}
            out[cur_name] = cur_dict
            continue
        m_kv = re.match(r"^\s+([A-Za-z0-9_\-]+):\s*(.*)$", raw)
        if m_kv and cur_dict is not None:
            key = m_kv.group(1)
            val = m_kv.group(2).strip()
            if val == "|" or val == "|-":
                in_block = key
                block_lines = []
                block_indent = None
            else:
                cur_dict[key] = val
    if in_block is not None and cur_dict is not None:
        cur_dict[in_block] = "\n".join(block_lines).rstrip() + "\n"
    return out


def load_rubric(name: str = "default") -> dict[str, Any]:
    """Return the rubric dict for ``name``, falling back to DEFAULT_RUBRIC.

    User rubrics in ``~/.clawmetry/evals.yaml`` override the defaults
    field-by-field — a custom rubric that only sets ``judge_model`` still
    gets the default prompt, and vice versa.
    """
    rubrics = _load_yaml_safe(RUBRIC_PATH)
    merged: dict[str, Any] = dict(DEFAULT_RUBRIC)
    user_rubric = rubrics.get(name) if isinstance(rubrics.get(name), dict) else None
    if user_rubric:
        for k, v in user_rubric.items():
            if v is not None and v != "":
                merged[k] = v
    return merged


def save_rubric_yaml(text: str) -> None:
    """Persist the rubric YAML text verbatim. Validates parse before write
    so a syntax error doesn't brick scoring. Idempotent — re-saving the
    same text is a no-op on the filesystem level."""
    # Parse-validate before write so we never persist a file that
    # ``load_rubric`` can't read back.
    _minimal_yaml_parse(text)
    RUBRIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUBRIC_PATH.write_text(text, encoding="utf-8")


def get_rubric_yaml() -> str:
    """Return the raw YAML on disk, or the default template if absent."""
    if RUBRIC_PATH.exists():
        try:
            return RUBRIC_PATH.read_text(encoding="utf-8")
        except OSError:
            pass
    return DEFAULT_RUBRIC_YAML


# ── Score parsing ──────────────────────────────────────────────────────────────


_SCORE_RE = re.compile(r"SCORE\s*:\s*([0-9]+(?:\.\d+)?)", re.IGNORECASE)
_REASON_RE = re.compile(r"REASON\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.DOTALL)


def parse_score(text: str) -> tuple[float | None, str | None]:
    """Extract ``(score, reason)`` from a judge model's reply.

    Tolerant of leading/trailing whitespace, extra prose, and the model
    occasionally answering as ``Score: 4`` or wrapping the value in
    backticks. Returns ``(None, None)`` if neither field is recognisable
    so the caller can log + skip rather than persist garbage.
    """
    if not text:
        return None, None
    cleaned = text.replace("`", "").strip()
    score: float | None = None
    m = _SCORE_RE.search(cleaned)
    if m:
        try:
            val = float(m.group(1))
            if 0.0 <= val <= 5.0:
                score = val
        except ValueError:
            pass
    reason: str | None = None
    r = _REASON_RE.search(cleaned)
    if r:
        reason = r.group(1).strip()
        # Truncate runaway reasons to a tweet's length so the column
        # doesn't bloat the DuckDB row size.
        if len(reason) > 280:
            reason = reason[:277] + "..."
    return score, reason


# ── Result envelope ────────────────────────────────────────────────────────────


@dataclass
class EvalResult:
    """One scored session. Persisted columns mirror this shape (see
    ``clawmetry/local_store.py`` v8 migration)."""
    session_id: str
    score: float | None
    reason: str | None
    judge_model: str
    rubric_name: str
    scored_at: int  # epoch millis
    skipped: bool = False
    skip_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Rate limiter (in-process, sliding hour window) ────────────────────────────


class _RateLimiter:
    """Simple sliding-window counter. ``allow()`` returns True at most
    ``cap`` times in any 3600-second window. Process-local — the daemon
    is the only scoring writer so we don't need cross-process state."""
    def __init__(self, cap: int):
        self.cap = max(1, int(cap))
        self._lock = threading.Lock()
        self._hits: list[float] = []

    def allow(self, *, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        cutoff = now - 3600.0
        with self._lock:
            # Drop hits outside the window.
            self._hits = [t for t in self._hits if t > cutoff]
            if len(self._hits) >= self.cap:
                return False
            self._hits.append(now)
            return True

    def hits_in_window(self, *, now: float | None = None) -> int:
        now = time.time() if now is None else now
        cutoff = now - 3600.0
        with self._lock:
            self._hits = [t for t in self._hits if t > cutoff]
            return len(self._hits)


# ── Transcript extraction ──────────────────────────────────────────────────────


def _event_text(ev: dict[str, Any], event_types: tuple[str, ...]) -> str:
    """Extract human-readable text from an event row for the judge prompt.

    Probes the v3 + legacy shapes documented in the MEMORY canonical event
    notes: ``finalPromptText`` for prompts; ``message.content`` / ``text``
    / ``output`` for assistants.
    """
    et = ev.get("event_type") or ev.get("type") or ""
    if et not in event_types:
        return ""
    data = ev.get("data") or {}
    if isinstance(data, (bytes, bytearray)):
        try:
            data = json.loads(data.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return ""
    if not isinstance(data, dict):
        return ""
    # Prompt-side probes (v3 + legacy).
    for key in ("finalPromptText", "promptText", "text", "input", "content"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v
    # Anthropic SDK envelope: data.message.content can be str or list-of-blocks.
    msg = data.get("message") if isinstance(data.get("message"), dict) else None
    if msg:
        c = msg.get("content")
        if isinstance(c, str) and c.strip():
            return c
        if isinstance(c, list):
            parts: list[str] = []
            for blk in c:
                if isinstance(blk, dict) and isinstance(blk.get("text"), str):
                    parts.append(blk["text"])
            if parts:
                return "\n".join(parts)
        t = msg.get("text")
        if isinstance(t, str) and t.strip():
            return t
    # v3 model.completed sometimes carries the final text in data.output.
    out = data.get("output")
    if isinstance(out, str) and out.strip():
        return out
    return ""


# ── Runner ─────────────────────────────────────────────────────────────────────


class EvalRunner:
    """Score completed sessions using an LLM-as-judge.

    Usage:
        runner = EvalRunner()
        result = runner.score_session("sess-abc")

    The runner is stateful only for the rate limiter; everything else is
    derived per-call so it's safe to share one instance across the
    scheduler thread + ad-hoc /api/evals/rescore handlers.
    """

    def __init__(
        self,
        *,
        rubric_name: str = "default",
        rate_limiter: _RateLimiter | None = None,
        store: Any = None,
    ):
        self.rubric_name = rubric_name
        self.rate_limiter = rate_limiter or _RateLimiter(RATE_LIMIT_PER_HOUR)
        # ``store`` injectable so tests can hand in a fake without going
        # through the real DuckDB singleton.
        self._store = store

    # -- internals --

    def _get_store(self) -> Any:
        if self._store is not None:
            return self._store
        from clawmetry import local_store
        self._store = local_store.get_store()
        return self._store

    def _build_prompt(self, rubric: dict[str, Any], transcript: str) -> str:
        """Compose the final judge prompt: rubric instructions + transcript."""
        instructions = str(rubric.get("prompt") or DEFAULT_RUBRIC["prompt"])
        # Cap transcript length so a 100K-token session doesn't run the
        # judge bill into the ground. The first/last ~4K chars carry the
        # signal we need (intent + outcome) without the toolchain noise.
        if len(transcript) > 8000:
            head = transcript[:4000]
            tail = transcript[-4000:]
            transcript = head + "\n\n[... transcript truncated ...]\n\n" + tail
        return instructions + "\n\n---\nTRANSCRIPT:\n" + transcript + "\n---"

    def _collect_transcript(self, session_id: str) -> tuple[str, int]:
        """Pull session events from DuckDB and render a compact transcript.

        Returns ``(transcript_text, total_tokens)``. ``total_tokens`` is the
        DuckDB-summed token_count for the session — used by the trivial-
        session guard to skip empty heartbeats.
        """
        store = self._get_store()
        events: list[dict[str, Any]] = []
        try:
            events = store.query_events(session_id=session_id, limit=200)
        except Exception as e:
            log.warning("evals: query_events(%s) failed: %s", session_id, e)
            return "", 0
        # query_events returns DESC; we want chronological for the judge.
        events = list(reversed(events))

        prompts: list[str] = []
        responses: list[str] = []
        total_tokens = 0
        for ev in events:
            tc = ev.get("token_count") or 0
            try:
                total_tokens += int(tc)
            except (TypeError, ValueError):
                pass
            p = _event_text(ev, _PROMPT_EVENT_TYPES)
            if p:
                prompts.append(p)
                continue
            r = _event_text(ev, _RESPONSE_EVENT_TYPES)
            if r:
                responses.append(r)

        if not prompts and not responses:
            return "", total_tokens

        parts: list[str] = []
        # Take the FIRST user prompt and LAST assistant response — that's
        # the canonical intent-vs-outcome pair the rubric scores.
        if prompts:
            parts.append("USER: " + prompts[0].strip())
        if responses:
            parts.append("ASSISTANT: " + responses[-1].strip())
        return "\n\n".join(parts), total_tokens

    # -- public API --

    def score_session(
        self,
        session_id: str,
        *,
        dry_run: bool = False,
        judge_call: Any = None,
    ) -> EvalResult | None:
        """Score one session. Returns ``EvalResult`` (which may be a skip)
        or ``None`` if the env switch disables evals.

        ``dry_run`` runs the full pipeline but skips DuckDB persistence —
        used by the /api/evals/rescore preview path.

        ``judge_call`` is an optional injectable callable
        ``(model, prompt, *, timeout) -> str``. Defaults to the real
        Anthropic Messages call. Tests inject a recorded-response stub.
        """
        if not is_enabled():
            return None

        rubric = load_rubric(self.rubric_name)
        judge_model = str(rubric.get("judge_model") or DEFAULT_RUBRIC["judge_model"])
        scored_at = int(time.time() * 1000)

        transcript, total_tokens = self._collect_transcript(session_id)

        # Trivial-session guard. The threshold is intentionally low —
        # we want to score real sessions, not skip them.
        if total_tokens < MIN_TOKENS_FOR_SCORING:
            result = EvalResult(
                session_id=session_id,
                score=None,
                reason=None,
                judge_model=judge_model,
                rubric_name=self.rubric_name,
                scored_at=scored_at,
                skipped=True,
                skip_reason=f"trivial session ({total_tokens} tokens < {MIN_TOKENS_FOR_SCORING})",
            )
            log.debug("evals: skip %s (%s)", session_id, result.skip_reason)
            return result

        if not transcript:
            return EvalResult(
                session_id=session_id,
                score=None,
                reason=None,
                judge_model=judge_model,
                rubric_name=self.rubric_name,
                scored_at=scored_at,
                skipped=True,
                skip_reason="no extractable transcript",
            )

        # Cost guard — 100 calls/hour ceiling. Returning a skip (not a
        # failure) lets the scheduler retry on the next pass without
        # repeatedly logging warnings.
        if not self.rate_limiter.allow():
            return EvalResult(
                session_id=session_id,
                score=None,
                reason=None,
                judge_model=judge_model,
                rubric_name=self.rubric_name,
                scored_at=scored_at,
                skipped=True,
                skip_reason=f"rate limit hit ({RATE_LIMIT_PER_HOUR}/hour)",
            )

        prompt = self._build_prompt(rubric, transcript)
        caller = judge_call or _call_judge
        try:
            reply = caller(judge_model, prompt, timeout=JUDGE_TIMEOUT_SECS)
        except Exception as e:
            # Judge failure is best-effort — surface as a non-skipped
            # NULL score so the scheduler will pick it up again later,
            # and so /api/evals/recent can show "judge unavailable".
            log.warning("evals: judge call failed for %s: %s", session_id, e)
            return EvalResult(
                session_id=session_id,
                score=None,
                reason=None,
                judge_model=judge_model,
                rubric_name=self.rubric_name,
                scored_at=scored_at,
                skipped=False,
                skip_reason=f"judge error: {type(e).__name__}",
            )

        score, reason = parse_score(reply)
        result = EvalResult(
            session_id=session_id,
            score=score,
            reason=reason,
            judge_model=judge_model,
            rubric_name=self.rubric_name,
            scored_at=scored_at,
        )

        if not dry_run and score is not None:
            try:
                store = self._get_store()
                store.persist_eval_score(
                    session_id=session_id,
                    score=score,
                    reason=reason or "",
                    judge_model=judge_model,
                    scored_at=scored_at,
                    rubric=self.rubric_name,
                )
            except Exception as e:
                log.warning("evals: persist failed for %s: %s", session_id, e)
        return result


# ── Judge LLM call ─────────────────────────────────────────────────────────────


def _call_judge(model: str, prompt: str, *, timeout: float = 30.0) -> str:
    """Call the Anthropic Messages API with the user's existing API key.

    Routed through ``httpx`` so ``clawmetry/interceptor.py``'s cost
    tracking picks up the call — eval spend shows up in /api/usage like
    any other LLM call.

    Returns the judge's reply text. Raises on any HTTP / network /
    JSON-decoding failure — the caller catches and degrades gracefully.

    Provider routing follows the model prefix:
      * ``claude-*``  → api.anthropic.com (ANTHROPIC_API_KEY)
      * ``gpt-*``, ``o1-*``, ``o3-*`` → api.openai.com (OPENAI_API_KEY)
    Anything else falls back to Anthropic — Phase 1 is Haiku-by-default,
    so the long tail of providers can wait for Phase 2.
    """
    import httpx

    model_lower = model.lower()
    if model_lower.startswith(("gpt-", "o1-", "o3-", "o4-")):
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""

    # Default: Anthropic (Claude Haiku/Sonnet/Opus).
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    blocks = data.get("content") or []
    parts: list[str] = []
    for blk in blocks:
        if isinstance(blk, dict) and isinstance(blk.get("text"), str):
            parts.append(blk["text"])
    return "\n".join(parts)


# ── Scheduler ──────────────────────────────────────────────────────────────────


# Module-level singleton rate limiter shared by the scheduler loop and any
# ad-hoc /api/evals/rescore calls so the 100/hour ceiling applies globally.
_GLOBAL_RATE_LIMITER = _RateLimiter(RATE_LIMIT_PER_HOUR)


def _runner_factory() -> EvalRunner:
    return EvalRunner(rate_limiter=_GLOBAL_RATE_LIMITER)


def score_pending_sessions(
    *,
    batch_size: int = 10,
    runner: EvalRunner | None = None,
) -> int:
    """One scheduler tick: pick up to ``batch_size`` unscored completed
    sessions and score them. Returns the count of sessions that produced
    a numeric score (skips + judge failures don't count).

    Called every ``EVAL_INTERVAL_SECS`` by the background thread in
    ``clawmetry/sync.py``. Idempotent — sessions already carrying an
    ``eval_score`` are filtered out at the DuckDB level.
    """
    if not is_enabled():
        return 0
    try:
        from clawmetry import local_store
        store = local_store.get_store()
    except Exception as e:
        log.warning("evals: local store unavailable: %s", e)
        return 0
    try:
        pending = store.query_unscored_sessions(limit=batch_size)
    except Exception as e:
        log.warning("evals: query_unscored_sessions failed: %s", e)
        return 0
    if not pending:
        return 0
    r = runner or _runner_factory()
    scored = 0
    for row in pending:
        sid = row.get("session_id")
        if not sid:
            continue
        try:
            result = r.score_session(sid)
        except Exception as e:
            log.warning("evals: score_session(%s) crashed: %s", sid, e)
            continue
        if result and result.score is not None:
            scored += 1
    return scored
