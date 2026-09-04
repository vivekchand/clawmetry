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

# The judge posts a redacted transcript excerpt to a third-party model API.
# That is content leaving the machine, so it is OPT-IN: the presence of an
# ANTHROPIC_API_KEY / OPENAI_API_KEY in the environment is not consent.
# Enable with CLAWMETRY_EVALS_ENABLED=1 or ``"evals": true`` in
# ~/.clawmetry/config.json. CLAWMETRY_EVALS_ENABLED=0 always wins.
_TRUTHY = ("1", "true", "True", "yes", "on")
_FALSY = ("0", "false", "False", "no", "off")


def _config_opt_in() -> bool:
    try:
        path = Path(os.path.expanduser("~/.clawmetry/config.json"))
        if not path.exists():
            return False
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        return bool(isinstance(data, dict) and data.get("evals") is True)
    except Exception:
        return False


def is_enabled() -> bool:
    """Opt-in switch. Default False: no transcript excerpt leaves the machine
    for scoring until the user asks for it."""
    env = os.environ.get("CLAWMETRY_EVALS_ENABLED", "").strip()
    if env in _FALSY:
        return False
    if env in _TRUTHY:
        return True
    return _config_opt_in()


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
    "judge_provider": "anthropic",
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
        # PRIVACY: the transcript is about to leave the machine for a THIRD-PARTY
        # judge LLM (Anthropic/OpenAI). Everything else in ClawMetry is E2E
        # encrypted so even our own cloud cannot read it; the judge is the one
        # place raw session text goes out. Redact secrets + PII first. Done
        # BEFORE the length cap so a secret near the truncation boundary is still
        # scrubbed.
        transcript = _redact_for_judge(transcript)
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

        # Judge-key guard. Evals are default-on, but the judge calls a real LLM
        # (Anthropic/OpenAI) that needs an API key in the env. With no key,
        # return a quiet SKIP (not a per-session WARNING) so we (a) never spam
        # sync.log every scheduler tick when the feature simply isn't configured,
        # and (b) never spend silently. The user opts in implicitly by setting
        # ANTHROPIC_API_KEY / OPENAI_API_KEY. Logged once per process.
        if not _judge_key_present(judge_model):
            global _NO_KEY_LOGGED
            if not _NO_KEY_LOGGED:
                log.info(
                    "evals: no judge API key in env (set ANTHROPIC_API_KEY or "
                    "OPENAI_API_KEY to enable session scoring) — skipping until then"
                )
                _NO_KEY_LOGGED = True
            return EvalResult(
                session_id=session_id,
                score=None,
                reason=None,
                judge_model=judge_model,
                rubric_name=self.rubric_name,
                scored_at=scored_at,
                skipped=True,
                skip_reason="no judge API key configured",
            )

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
            _record_judge_status(True, None, judge_provider_for(rubric), judge_model)
        except Exception as e:
            # Judge failure is best-effort — surface as a non-skipped
            # NULL score so the scheduler will pick it up again later,
            # and so /api/evals/recent can show "judge unavailable".
            log.warning("evals: judge call failed for %s: %s", session_id, e)
            _record_judge_status(
                False, _classify_judge_error(e), judge_provider_for(rubric), judge_model,
            )
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


# Logged once per process when evals are on but no judge key is configured, so
# we don't repeat the notice on every scheduler tick.
_NO_KEY_LOGGED = False

# Email PII pattern, redacted before the transcript goes to the third-party
# judge LLM. The personal-data tier in clawmetry/redaction.py (WO-61) now
# does this inside redact_text with the same ``[email]`` placeholder; this
# stays as the belt-and-braces scrub for an operator who switched that
# category off, because the judge is a third party either way.
_JUDGE_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")


def _redact_for_judge(text: str) -> str:
    """Scrub secrets + PII from a transcript before it leaves the machine for
    the third-party judge LLM. Reuses the ingest secret redactor (API keys,
    tokens, Bearer, private keys) and adds email PII. Respects the global
    CLAWMETRY_REDACT opt-out (so a user who explicitly disables redaction owns
    that). Never raises; never returns None."""
    if not text:
        return text
    try:
        from clawmetry import redaction as _redaction
        if _redaction._disabled():
            return text
        text = _redaction.redact_text(text)
        text = _JUDGE_EMAIL_RE.sub("[email]", text)
    except Exception:
        # Never lose the transcript on a redaction bug, but also never send raw
        # if we cannot confirm redaction ran: on import/other failure, drop a
        # conservative best-effort email scrub at minimum.
        try:
            text = _JUDGE_EMAIL_RE.sub("[email]", text)
        except Exception:
            pass
    return text


# Local judge-key store, so the dashboard can enable evals by saving a key (no
# need to set an env var + restart the daemon). Lives ONLY on disk (chmod 600),
# never in the cloud snapshot — it's a real LLM API key. Read fresh per call so
# a key saved from the UI takes effect on the next scheduler tick without a
# daemon restart.
_EVAL_KEYS_PATH = os.path.expanduser("~/.clawmetry/eval_keys.json")

# The judge works with various providers, not just Claude. Each entry drives
# the UI (label, default model, key hint) and the wire call (env var, auth
# style). "custom" is any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM,
# LiteLLM, ...) reached via a user-supplied base URL.
JUDGE_PROVIDERS_INFO: dict[str, dict[str, Any]] = {
    "anthropic": {
        "label": "Anthropic (Claude)",
        "env": ("ANTHROPIC_API_KEY",),
        "default_model": "claude-haiku-4-5",
        "key_hint": "sk-ant-...",
        "needs_base_url": False,
    },
    "openai": {
        "label": "OpenAI",
        "env": ("OPENAI_API_KEY",),
        "default_model": "gpt-5-mini",
        "key_hint": "sk-...",
        "needs_base_url": False,
    },
    "google": {
        "label": "Google (Gemini)",
        "env": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "default_model": "gemini-2.5-flash",
        "key_hint": "AIza...",
        "needs_base_url": False,
    },
    "openrouter": {
        "label": "OpenRouter (any model)",
        "env": ("OPENROUTER_API_KEY",),
        "default_model": "google/gemini-2.5-flash",
        "key_hint": "sk-or-...",
        "needs_base_url": False,
    },
    "custom": {
        "label": "Custom (OpenAI-compatible, e.g. Ollama)",
        "env": ("CLAWMETRY_JUDGE_API_KEY",),
        "default_model": "llama3.1",
        "key_hint": "optional for local servers",
        "needs_base_url": True,
    },
}

_JUDGE_PROVIDERS = tuple(JUDGE_PROVIDERS_INFO.keys())


def _provider_for_model(model: str) -> str:
    """Best-effort provider inference from a model id — the fallback when the
    rubric doesn't carry an explicit ``judge_provider``."""
    m = (model or "").lower()
    if m.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return "openai"
    if m.startswith("gemini"):
        return "google"
    if "/" in m:
        return "openrouter"
    return "anthropic"


def judge_provider_for(rubric: dict[str, Any] | None = None) -> str:
    """The provider the judge will actually use: the rubric's explicit
    ``judge_provider`` when valid, else inferred from the judge model id."""
    r = rubric if rubric is not None else load_rubric("default")
    prov = str(r.get("judge_provider") or "").strip().lower()
    if prov in _JUDGE_PROVIDERS:
        return prov
    return _provider_for_model(str(r.get("judge_model") or DEFAULT_RUBRIC["judge_model"]))


def _stored_judge_key(provider: str) -> str:
    """Read the UI-saved key for ``provider`` from the local key store. Never
    raises; returns '' when absent."""
    try:
        import json as _json
        with open(_EVAL_KEYS_PATH, encoding="utf-8") as fh:
            data = _json.load(fh)
        return str((data or {}).get(provider, "") or "").strip()
    except Exception:
        return ""


def _judge_api_key_for_provider(provider: str) -> str:
    """The API key for ``provider``: env var(s) first (operator intent / CI),
    then the UI-saved local key. Empty string when neither is set."""
    info = JUDGE_PROVIDERS_INFO.get(provider) or {}
    for env_name in info.get("env", ()):
        v = os.environ.get(env_name, "").strip()
        if v:
            return v
    return _stored_judge_key(provider)


def _judge_api_key(model: str) -> str:
    """Back-compat shape (clawmetry-pro calls this with a model id): resolve
    the provider from the default rubric (explicit judge_provider wins, else
    inferred from the model string), then look up its key."""
    try:
        rubric = load_rubric("default")
    except Exception:
        rubric = None
    if rubric and str(rubric.get("judge_model") or "") != (model or ""):
        # Caller asked about a model that is not the configured judge —
        # infer its provider from the id alone.
        provider = _provider_for_model(model)
    else:
        provider = judge_provider_for(rubric)
    return _judge_api_key_for_provider(provider)


def judge_base_url() -> str:
    """Base URL for the ``custom`` provider (OpenAI-compatible server).
    Env wins; else the UI-saved value; empty when unset."""
    env = os.environ.get("CLAWMETRY_JUDGE_BASE_URL", "").strip()
    if env:
        return env.rstrip("/")
    try:
        with open(_EVAL_KEYS_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return str((data or {}).get("custom_base_url", "") or "").strip().rstrip("/")
    except Exception:
        return ""


def save_judge_key(provider: str, api_key: str, *, base_url: str | None = None) -> None:
    """Persist a judge API key locally (chmod 600). Used by the dashboard so a
    user can enable evals without setting an env var. ``api_key=""`` clears it.
    For the ``custom`` provider, ``base_url`` stores the OpenAI-compatible
    endpoint alongside the (possibly empty — local servers) key."""
    import json as _json
    provider = (provider or "").strip().lower()
    if provider not in _JUDGE_PROVIDERS:
        raise ValueError(f"unknown provider {provider!r} (expected one of {_JUDGE_PROVIDERS})")
    os.makedirs(os.path.dirname(_EVAL_KEYS_PATH), exist_ok=True)
    data = {}
    try:
        with open(_EVAL_KEYS_PATH, encoding="utf-8") as fh:
            data = _json.load(fh) or {}
    except Exception:
        data = {}
    key = (api_key or "").strip()
    if key:
        data[provider] = key
    else:
        data.pop(provider, None)
    if base_url is not None:
        url = base_url.strip().rstrip("/")
        if url:
            data["custom_base_url"] = url
        else:
            data.pop("custom_base_url", None)
    # Write 0600 so the key is not world-readable.
    fd = os.open(_EVAL_KEYS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        _json.dump(data, fh)
    try:
        os.chmod(_EVAL_KEYS_PATH, 0o600)
    except Exception:
        pass


def judge_keys_present() -> dict:
    """Presence map for the UI — NEVER returns the key values themselves. Each
    provider is True if a key is available via env OR the local store. The
    ``custom`` provider counts as configured when a base URL is set, even with
    no key (local servers like Ollama need none)."""
    out = {}
    for prov in _JUDGE_PROVIDERS:
        out[prov] = bool(_judge_api_key_for_provider(prov))
    if not out.get("custom") and judge_base_url():
        out["custom"] = True
    return out


def _judge_key_present(model: str) -> bool:
    """True if credentials to judge with ``model`` are available (env or the
    UI-saved local store). Provider resolution mirrors ``_call_judge``: the
    rubric's explicit provider when asking about the configured judge model,
    else inferred from the model id. ``custom`` needs only a base URL — a key
    is optional (local servers)."""
    try:
        rubric = load_rubric("default")
    except Exception:
        rubric = None
    if rubric and str(rubric.get("judge_model") or "") == (model or ""):
        provider = judge_provider_for(rubric)
    else:
        provider = _provider_for_model(model)
    if provider == "custom":
        return bool(judge_base_url())
    return bool(_judge_api_key_for_provider(provider))


def _judge_http_post_json(url: str, payload: dict, headers: dict, timeout: float) -> dict:
    """POST JSON to ``url`` and return the parsed response dict.

    Prefers ``httpx`` when installed (so ``clawmetry/interceptor.py`` cost
    tracking picks up eval spend), but FALLS BACK to the stdlib ``urllib`` when
    httpx is absent. httpx is NOT a clawmetry dependency (deps stay minimal:
    flask + waitress + cryptography), so on the daemon's own venv the judge used
    to die with ``No module named 'httpx'`` and no session ever got scored.
    Raises on HTTP / network / JSON error; the caller catches and degrades."""
    try:
        import httpx  # noqa: F401
        _have_httpx = True
    except Exception:
        _have_httpx = False
    if _have_httpx:
        import httpx
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
    # stdlib fallback (always available). urlopen raises HTTPError on 4xx/5xx,
    # mirroring httpx's raise_for_status so the caller's error handling is uniform.
    import json as _json
    import urllib.request as _ur

    body = _json.dumps(payload).encode("utf-8")
    req = _ur.Request(
        url, data=body, method="POST",
        headers={**(headers or {}), "Content-Type": "application/json"},
    )
    with _ur.urlopen(req, timeout=timeout) as resp:
        return _json.loads(resp.read() or b"{}")


def _judge_request(
    provider: str,
    model: str,
    prompt: str,
    *,
    api_key: str,
    base_url: str = "",
    timeout: float = 30.0,
    max_tokens: int = 200,
) -> str:
    """One provider-routed judge call. Returns the reply text; raises on any
    HTTP / network / JSON failure — callers catch and degrade.

    Wire shapes (raw HTTP by design — deps stay flask+waitress+cryptography):
      * anthropic  → api.anthropic.com/v1/messages (x-api-key)
      * openai     → api.openai.com/v1/chat/completions (Bearer,
                     max_completion_tokens — required by current OpenAI models)
      * google     → generativelanguage.googleapis.com v1beta generateContent
                     (x-goog-api-key)
      * openrouter → openrouter.ai/api/v1/chat/completions (Bearer)
      * custom     → {base_url}/chat/completions (Bearer optional — any
                     OpenAI-compatible server: Ollama, LM Studio, vLLM, ...)
    """
    if provider == "anthropic":
        if not api_key:
            raise RuntimeError("no Anthropic judge key configured (set ANTHROPIC_API_KEY or add a key in the dashboard)")
        data = _judge_http_post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout,
        )
        parts = [
            blk["text"] for blk in (data.get("content") or [])
            if isinstance(blk, dict) and isinstance(blk.get("text"), str)
        ]
        return "\n".join(parts)

    if provider == "google":
        if not api_key:
            raise RuntimeError("no Google judge key configured (set GEMINI_API_KEY or add a key in the dashboard)")
        data = _judge_http_post_json(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent",
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
            {"x-goog-api-key": api_key, "Content-Type": "application/json"},
            timeout,
        )
        cands = data.get("candidates") or []
        if not cands:
            return ""
        parts = [
            p.get("text", "")
            for p in ((cands[0].get("content") or {}).get("parts") or [])
            if isinstance(p, dict)
        ]
        return "\n".join(x for x in parts if x)

    # OpenAI-compatible chat/completions: openai, openrouter, custom.
    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        if not api_key:
            raise RuntimeError("no OpenAI judge key configured (set OPENAI_API_KEY or add a key in the dashboard)")
        # Current OpenAI models reject max_tokens; older compatible servers
        # reject max_completion_tokens — so the real OpenAI endpoint gets the
        # new field and everything else keeps the widely-supported one.
        limit_field = "max_completion_tokens"
    elif provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        if not api_key:
            raise RuntimeError("no OpenRouter judge key configured (set OPENROUTER_API_KEY or add a key in the dashboard)")
        limit_field = "max_tokens"
    elif provider == "custom":
        base = (base_url or judge_base_url()).rstrip("/")
        if not base:
            raise RuntimeError("no base URL configured for the custom judge provider")
        url = f"{base}/chat/completions"
        limit_field = "max_tokens"
    else:
        raise RuntimeError(f"unknown judge provider {provider!r}")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = _judge_http_post_json(
        url,
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            limit_field: max_tokens,
        },
        headers,
        timeout,
    )
    choices = data.get("choices") or []
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "") or ""


def _call_judge(
    model: str, prompt: str, *, timeout: float = 30.0, max_tokens: int = 200,
) -> str:
    """Call the configured judge provider with the user's own key.

    Back-compat entry point (clawmetry-pro's faithfulness evaluator calls
    this with ``(model, prompt, timeout=...)``). Provider comes from the
    rubric's ``judge_provider`` when set, else is inferred from the model id.
    ``max_tokens`` defaults to the classic SCORE/REASON budget; structured
    judges (the DeepEval bridge) pass a larger cap for JSON replies.
    """
    rubric = load_rubric("default")
    if str(rubric.get("judge_model") or "") == (model or ""):
        provider = judge_provider_for(rubric)
    else:
        provider = _provider_for_model(model)
    return _judge_request(
        provider,
        model,
        prompt,
        api_key=_judge_api_key_for_provider(provider),
        timeout=timeout,
        max_tokens=max_tokens,
    )


# ── Judge health: validate-on-save + last-call status (issue #4313) ───────────

# The most recent judge call outcome, so the UI can say honestly whether the
# configured key actually works instead of "Scoring is ON" over silent 401s.
_LAST_JUDGE_STATUS: dict[str, Any] = {"ok": None, "error": None, "at": None,
                                      "provider": None, "model": None}
_LAST_JUDGE_LOCK = threading.Lock()

# Shared across processes (daemon writes, dashboard reads). No key material —
# ok/error/provider/model/at only. Mirrors _EVAL_KEYS_PATH convention.
_EVAL_STATUS_PATH = os.path.expanduser("~/.clawmetry/eval_status.json")


def _record_judge_status(ok: bool, error: str | None, provider: str, model: str) -> None:
    with _LAST_JUDGE_LOCK:
        _LAST_JUDGE_STATUS.update({
            "ok": ok,
            "error": (error or None) if not ok else None,
            "at": int(time.time() * 1000),
            "provider": provider,
            "model": model,
        })
        snapshot = dict(_LAST_JUDGE_STATUS)
    try:
        Path(_EVAL_STATUS_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(_EVAL_STATUS_PATH).write_text(json.dumps(snapshot))
    except Exception:
        pass


def last_judge_status() -> dict[str, Any]:
    """A copy of the most recent judge call outcome (never key material).

    Reads from the shared file when it's newer than the in-memory copy so that
    the dashboard process reflects daemon-side judge outcomes without a restart
    (fix for issue #4332: status was per-process, 401s from the daemon never
    surfaced in the dashboard card until a dashboard-side call happened).
    """
    with _LAST_JUDGE_LOCK:
        mem = dict(_LAST_JUDGE_STATUS)
    try:
        file_status = json.loads(Path(_EVAL_STATUS_PATH).read_text())
        if (file_status.get("at") or 0) > (mem.get("at") or 0):
            return file_status
    except Exception:
        pass
    return mem


def _classify_judge_error(exc: Exception) -> str:
    """Small human-readable classification for a judge failure. 'auth' means
    the key was rejected — the UI turns that into a re-add-your-key state."""
    text = str(exc)
    code = getattr(getattr(exc, "response", None), "status_code", None)
    if code is None:
        m = re.search(r"\b(401|403|404|429)\b", text)
        code = int(m.group(1)) if m else None
    if code in (401, 403):
        return "auth"
    if code == 404:
        return "model_not_found"
    if code == 429:
        return "rate_limited"
    return "network"


def validate_judge_key(
    provider: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> tuple[bool, str]:
    """Fire a tiny real call ("Reply with exactly: OK", a few tokens) against
    ``provider`` to prove the credentials work BEFORE they are saved. Returns
    ``(ok, detail)`` — detail is a plain-language reason on failure. Costs a
    fraction of a cent on hosted providers; nothing on local servers."""
    provider = (provider or "").strip().lower()
    if provider not in _JUDGE_PROVIDERS:
        return False, f"unknown provider {provider!r}"
    info = JUDGE_PROVIDERS_INFO[provider]
    use_model = (model or "").strip() or str(info["default_model"])
    key = api_key if api_key is not None else _judge_api_key_for_provider(provider)
    try:
        reply = _judge_request(
            provider,
            use_model,
            "Reply with exactly: OK",
            api_key=(key or "").strip(),
            base_url=(base_url or "").strip(),
            timeout=min(JUDGE_TIMEOUT_SECS, 20.0),
            max_tokens=8,
        )
    except RuntimeError as e:
        return False, str(e)
    except Exception as e:
        kind = _classify_judge_error(e)
        if kind == "auth":
            return False, "the provider rejected this key (unauthorized)"
        if kind == "model_not_found":
            return False, f"model {use_model!r} was not found at this provider"
        if kind == "rate_limited":
            return False, "the provider rate-limited the test call — try again shortly"
        return False, f"could not reach the provider: {type(e).__name__}"
    if not isinstance(reply, str):
        return False, "unexpected reply shape from the provider"
    return True, ""


def set_judge_selection(provider: str, model: str) -> None:
    """Persist the judge provider + model into the rubric YAML so the daemon
    scheduler picks them up on its next tick. Rewrites only the two keys,
    preserving the user's prompt and any other rubric fields."""
    provider = (provider or "").strip().lower()
    model = (model or "").strip()
    if provider not in _JUDGE_PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}")
    if not model:
        model = str(JUDGE_PROVIDERS_INFO[provider]["default_model"])
    text = get_rubric_yaml()
    if re.search(r"(?m)^\s+judge_model:\s*\S.*$", text):
        text = re.sub(r"(?m)^(\s+)judge_model:\s*\S.*$", rf"\g<1>judge_model: {model}", text, count=1)
    else:
        text = re.sub(r"(?m)^(default:\s*)$", rf"\g<1>\n  judge_model: {model}", text, count=1)
    if re.search(r"(?m)^\s+judge_provider:\s*\S.*$", text):
        text = re.sub(r"(?m)^(\s+)judge_provider:\s*\S.*$", rf"\g<1>judge_provider: {provider}", text, count=1)
    else:
        text = re.sub(r"(?m)^(\s+judge_model:.*)$", rf"\g<1>\n  judge_provider: {provider}", text, count=1)
    save_rubric_yaml(text)


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
