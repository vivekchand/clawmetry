"""
clawmetry/deepeval_bridge.py — optional DeepEval metric engine (local-first).

DeepEval (Apache-2.0, github.com/confident-ai/deepeval) ships the best OSS
catalogue of agent metrics (argument correctness, multi-turn conversation
quality, G-Eval custom criteria). This bridge lets ClawMetry run a curated
subset of those metrics on completed sessions WITHOUT giving up the moat:

  * **Optional extra.** DeepEval pulls ~70 transitive packages, so it can
    never be a base dependency (deps stay flask+waitress+cryptography+duckdb).
    Install with ``pip install clawmetry[deepeval]``; everything in this
    module degrades to an honest skip when the import is missing, and
    importing THIS module never imports deepeval (lazy, guarded).
  * **Telemetry forced off.** DeepEval phones PostHog by default and once
    shipped a release that exported host-app spans to its vendor account
    (confident-ai/deepeval#2497). ``_force_local_env()`` sets the opt-out
    env vars BEFORE any deepeval import, every time, no exceptions.
  * **The judge is OURS.** Metrics run against ``ClawMetryJudgeLLM``, a thin
    DeepEvalBaseLLM wrapper over ``eval_runner._call_judge`` — the user's own
    provider + key (Anthropic/OpenAI/Google/OpenRouter/custom incl. keyless
    local servers), redaction upstream, no vendor SDKs, cost visible to the
    interceptor. DeepEval's own model classes are never used, so no judge
    traffic can bypass the provider the user configured.
  * **Honest degrade everywhere.** No extra -> skip. No judge key -> skip
    (never spend). Judge/schema failure -> a persisted skip row (score NULL,
    reason recorded) so the scheduler doesn't retry-burn the same session.

Scored results land in the ``eval_metrics`` table with ``engine='deepeval'``
(one row per session+metric, latest-only), the same surface the free
deterministic checks write to.

Scheduling: OFF by default. Judge-backed metrics spend money, so the daemon
tick only runs when ``CLAWMETRY_DEEPEVAL_METRICS`` names at least one metric
(comma-separated slugs from ``SUPPORTED_METRICS``).

Public API:
    is_available() -> bool
    supported_metrics() -> list[str]
    score_session_deepeval(session_id, *, metrics=None, store=None,
                           judge_call=None, dry_run=False) -> list[dict]
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Callable

log = logging.getLogger("clawmetry.deepeval_bridge")


# Curated metric set v1. Values: which test-case shape the metric consumes.
# TaskCompletion is deliberately absent (it needs DeepEval @observe traces,
# which post-hoc stored sessions do not have). Tool-correctness is absent
# here because it needs expected_tools — that is suite territory, where the
# golden YAML supplies them.
SUPPORTED_METRICS: dict[str, str] = {
    "argument-correctness": "single_turn",
    "conversation-completeness": "conversational",
}

# Env knobs. Rate limit is separate from the answer-quality judge cap: this
# engine can run several judge calls per session.
RATE_LIMIT_PER_HOUR = int(os.environ.get("CLAWMETRY_DEEPEVAL_RATE_LIMIT", "50"))
MAX_OUTPUT_CHARS = int(os.environ.get("CLAWMETRY_DEEPEVAL_MAX_OUTPUT", "4000"))
MAX_TURNS = int(os.environ.get("CLAWMETRY_DEEPEVAL_MAX_TURNS", "40"))
MAX_TOOL_CALLS = int(os.environ.get("CLAWMETRY_DEEPEVAL_MAX_TOOLS", "50"))
JUDGE_MAX_TOKENS = int(os.environ.get("CLAWMETRY_DEEPEVAL_JUDGE_MAX_TOKENS", "1500"))

# The env contract that keeps DeepEval fully local. Forced (not setdefault):
# the privacy posture is not user-tunable through this code path.
_LOCAL_ENV = {
    "DEEPEVAL_TELEMETRY_OPT_OUT": "1",
    "ERROR_REPORTING": "0",
    "DEEPEVAL_UPDATE_WARNING_OPT_IN": "0",
}


def _force_local_env() -> None:
    """Set DeepEval's telemetry opt-outs. MUST run before any deepeval
    import; called from every entry point that may trigger one."""
    for k, v in _LOCAL_ENV.items():
        os.environ[k] = v


def is_available() -> bool:
    """True when the ``deepeval`` package is installed (the clawmetry[deepeval]
    extra). Probes the spec WITHOUT importing — importing deepeval is heavy
    (pydantic v2 + OTel + rich) and must stay off the CLI startup path."""
    try:
        import importlib.util
        return importlib.util.find_spec("deepeval") is not None
    except Exception:
        return False


def supported_metrics() -> list[str]:
    return list(SUPPORTED_METRICS)


_DEEPEVAL_NS: dict[str, Any] | None = None


def _deepeval_ns() -> dict[str, Any]:
    """Import deepeval lazily (telemetry env first) and cache the symbols the
    bridge needs. Raises ImportError when the extra is not installed."""
    global _DEEPEVAL_NS
    if _DEEPEVAL_NS is not None:
        return _DEEPEVAL_NS
    _force_local_env()
    from deepeval.metrics import (  # noqa: PLC0415
        ArgumentCorrectnessMetric,
        ConversationCompletenessMetric,
    )
    from deepeval.models.base_model import DeepEvalBaseLLM  # noqa: PLC0415
    from deepeval.test_case import (  # noqa: PLC0415
        ConversationalTestCase,
        LLMTestCase,
        ToolCall,
        Turn,
    )
    _DEEPEVAL_NS = {
        "ArgumentCorrectnessMetric": ArgumentCorrectnessMetric,
        "ConversationCompletenessMetric": ConversationCompletenessMetric,
        "DeepEvalBaseLLM": DeepEvalBaseLLM,
        "ConversationalTestCase": ConversationalTestCase,
        "LLMTestCase": LLMTestCase,
        "ToolCall": ToolCall,
        "Turn": Turn,
    }
    return _DEEPEVAL_NS


# ── The judge: DeepEval schema contract over ClawMetry's own HTTP judge ────────

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _extract_json(raw: str) -> Any:
    """Pull the first JSON object out of a judge reply that may wrap it in
    prose or a code fence (small local models routinely do)."""
    m = _FENCE_RE.search(raw or "")
    if m:
        raw = m.group(1)
    start = (raw or "").find("{")
    end = (raw or "").rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in judge reply")
    return json.loads(raw[start:end + 1])


_JUDGE_CLS: type | None = None


def _judge_cls() -> type:
    """Build (once) the DeepEvalBaseLLM subclass that routes every metric
    judge call through ``eval_runner._call_judge``: the user's configured
    provider + key, redacted inputs, interceptor-visible spend."""
    global _JUDGE_CLS
    if _JUDGE_CLS is not None:
        return _JUDGE_CLS
    ns = _deepeval_ns()

    class ClawMetryJudgeLLM(ns["DeepEvalBaseLLM"]):
        def __init__(self, model: str, judge_call: Callable[..., str] | None = None):
            self.model = model
            self._judge_call = judge_call
            self.calls = 0

        def load_model(self):
            return self

        def get_model_name(self) -> str:
            return f"clawmetry-judge:{self.model}"

        def _raw(self, prompt: str) -> str:
            from clawmetry import eval_runner
            self.calls += 1
            caller = self._judge_call or eval_runner._call_judge
            return caller(
                self.model, prompt,
                timeout=eval_runner.JUDGE_TIMEOUT_SECS,
                max_tokens=JUDGE_MAX_TOKENS,
            )

        def generate(self, prompt: str, schema: Any = None):
            if schema is None:
                return self._raw(prompt)
            # DeepEval metrics require a populated pydantic model back.
            # Ask for schema-conformant JSON; one corrective retry, then a
            # final raise that the per-metric runner catches as a skip.
            sch = json.dumps(schema.model_json_schema())
            ask = (
                prompt
                + "\n\nRespond with ONLY a JSON object that validates against "
                  "this JSON schema. No prose, no code fences.\nSCHEMA: " + sch
            )
            last_err: Exception | None = None
            for _attempt in range(2):
                raw = self._raw(ask)
                try:
                    return schema.model_validate(_extract_json(raw))
                except Exception as e:  # noqa: BLE001 — retried once, then raised
                    last_err = e
                    ask = (
                        prompt
                        + "\n\nYour previous reply was not valid JSON for the "
                          "schema (" + str(e)[:120] + "). Respond with ONLY the "
                          "JSON object, nothing else.\nSCHEMA: " + sch
                    )
            raise RuntimeError(f"judge schema contract failed: {last_err}")

        async def a_generate(self, prompt: str, schema: Any = None):
            return self.generate(prompt, schema)

    _JUDGE_CLS = ClawMetryJudgeLLM
    return _JUDGE_CLS


# ── Test-case builders (redacted before anything reaches a metric) ─────────────


def _redact(text: str) -> str:
    try:
        from clawmetry import eval_runner
        return eval_runner._redact_for_judge(text or "")
    except Exception:
        return text or ""


def _build_single_turn_case(rows: list, ns: dict[str, Any]):
    """LLMTestCase: first user prompt, last assistant reply, tool calls."""
    from clawmetry import deterministic_evaluators as de

    turns = de.turns_from_stored_rows(rows)
    eval_input = de.eval_input_from_stored_rows(rows)
    first_user = next((t["content"] for t in turns if t["role"] == "user"), "")
    # The reply being judged must be an actual ASSISTANT turn; the raw
    # output_text fallback would happily grade the user's own words on a
    # session with no reply yet.
    actual = next(
        (t["content"] for t in reversed(turns) if t["role"] == "assistant"), "")
    if not actual:
        return None
    tools = []
    for tc in eval_input.tool_calls[:MAX_TOOL_CALLS]:
        name = tc.get("name")
        if not name:
            continue
        args = tc.get("arguments")
        tools.append(ns["ToolCall"](
            name=str(name),
            input_parameters=args if isinstance(args, dict) else {},
        ))
    return ns["LLMTestCase"](
        input=_redact(first_user)[:MAX_OUTPUT_CHARS] or "(no prompt captured)",
        actual_output=_redact(actual)[:MAX_OUTPUT_CHARS],
        tools_called=tools,
    )


def _build_conversational_case(rows: list, ns: dict[str, Any]):
    """ConversationalTestCase from the session's chronological turns."""
    from clawmetry import deterministic_evaluators as de

    turns = de.turns_from_stored_rows(rows)
    if len(turns) < 2 or not any(t["role"] == "user" for t in turns):
        return None
    tail = turns[-MAX_TURNS:]
    return ns["ConversationalTestCase"](turns=[
        ns["Turn"](role=t["role"], content=_redact(t["content"])[:MAX_OUTPUT_CHARS])
        for t in tail
    ])


def _build_metric(slug: str, judge: Any, ns: dict[str, Any]):
    if slug == "argument-correctness":
        return ns["ArgumentCorrectnessMetric"](
            model=judge, async_mode=False, include_reason=True,
        )
    if slug == "conversation-completeness":
        return ns["ConversationCompletenessMetric"](
            model=judge, async_mode=False, include_reason=True,
        )
    raise ValueError(f"unsupported deepeval metric {slug!r}")


# ── Rate limiter (reuse the judge's sliding-window impl) ───────────────────────

_LIMITER = None


def _rate_limiter():
    global _LIMITER
    if _LIMITER is None:
        from clawmetry import eval_runner
        _LIMITER = eval_runner._RateLimiter(RATE_LIMIT_PER_HOUR)
    return _LIMITER


# ── The scorer ─────────────────────────────────────────────────────────────────


def _judge_ready() -> bool:
    """A judge call can succeed on this box: configured provider has a key,
    or is the custom provider with a base URL (keyless local server OK)."""
    try:
        from clawmetry import eval_runner
        rubric = eval_runner.load_rubric("default") or {}
        provider = eval_runner.judge_provider_for(rubric)
        if provider == "custom":
            return bool(eval_runner.judge_base_url())
        return bool(eval_runner._judge_api_key_for_provider(provider))
    except Exception:
        return False


def score_session_deepeval(
    session_id: str,
    *,
    metrics: list[str] | None = None,
    store: Any = None,
    judge_call: Callable[..., str] | None = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Run the requested DeepEval metrics on one stored session.

    Returns one result dict per metric: ``{session_id, metric_slug, score,
    passed, reason, engine, judge_model, scored_at, skipped, skip_reason}``.
    Persists non-dry-run results (including judge-error skips, so the
    scheduler never retry-burns a broken session). Returns ``[]`` when evals
    are disabled, deepeval is not installed, or there is nothing to score.
    """
    from clawmetry import eval_runner

    if not eval_runner.is_enabled():
        return []
    slugs = [s for s in (metrics or list(SUPPORTED_METRICS))
             if s in SUPPORTED_METRICS]
    if not slugs:
        return []
    if not is_available():
        log.info("deepeval bridge: package not installed; skipping "
                 "(pip install clawmetry[deepeval])")
        return []
    if judge_call is None and not _judge_ready():
        # Quiet skip, never spend, nothing persisted: key may appear later.
        return []

    scored_at = int(time.time() * 1000)
    rubric = eval_runner.load_rubric("default") or {}
    judge_model = str(rubric.get("judge_model")
                      or eval_runner.DEFAULT_RUBRIC["judge_model"])

    rows = _load_rows(session_id, store)
    if not rows:
        return []

    try:
        ns = _deepeval_ns()
    except Exception as e:  # import half-broken (version conflict etc.)
        log.warning("deepeval bridge: import failed: %s", e)
        return []

    judge = _judge_cls()(judge_model, judge_call=judge_call)
    results: list[dict[str, Any]] = []
    cases: dict[str, Any] = {}
    for slug in slugs:
        shape = SUPPORTED_METRICS[slug]
        if shape not in cases:
            builder = (_build_single_turn_case if shape == "single_turn"
                       else _build_conversational_case)
            try:
                cases[shape] = builder(rows, ns)
            except Exception as e:  # noqa: BLE001 — builder must not kill the pass
                log.warning("deepeval bridge: case build failed (%s): %s", shape, e)
                cases[shape] = None
        case = cases[shape]
        base = {
            "session_id": session_id, "metric_slug": slug, "engine": "deepeval",
            "judge_model": judge_model, "scored_at": scored_at,
        }
        if case is None:
            results.append({**base, "score": None, "passed": None,
                            "reason": "not enough transcript to build this metric's input",
                            "skipped": True, "skip_reason": "no_input"})
            continue
        if judge_call is None and not _rate_limiter().allow():
            results.append({**base, "score": None, "passed": None,
                            "reason": f"rate limit hit ({RATE_LIMIT_PER_HOUR}/hour)",
                            "skipped": True, "skip_reason": "rate_limit"})
            continue
        try:
            metric = _build_metric(slug, judge, ns)
            metric.measure(case)
            score = float(metric.score) if metric.score is not None else None
            results.append({
                **base,
                "score": score,
                "passed": bool(metric.is_successful()) if score is not None else None,
                "reason": str(metric.reason or "")[:500],
                "skipped": False, "skip_reason": None,
            })
        except Exception as e:  # noqa: BLE001 — a judge outage is a skip, not a crash
            log.warning("deepeval bridge: %s failed for %s: %s", slug, session_id, e)
            results.append({**base, "score": None, "passed": None,
                            "reason": f"judge error: {type(e).__name__}",
                            "skipped": True, "skip_reason": "judge_error"})

    if not dry_run:
        _persist(results, store)
    return results


def _load_rows(session_id: str, store: Any) -> list:
    try:
        s = store
        if s is None:
            from clawmetry import local_store
            s = local_store.get_store()
        return s.query_events(session_id=session_id, limit=500) or []
    except Exception:
        return []


def _persist(results: list[dict[str, Any]], store: Any) -> None:
    """Write every non-empty verdict (including judge-error skips) through
    the store so the session leaves the pending set. Never raises."""
    try:
        s = store
        if s is None:
            from clawmetry import local_store
            s = local_store.get_store()
        for r in results:
            # Do not mark no_input/rate_limit skips as done: the transcript
            # may still be filling in, and a rate-limited session deserves a
            # retry next tick. judge_error IS persisted (retrying would burn
            # the same call again).
            if r.get("skip_reason") in ("no_input", "rate_limit"):
                continue
            s.persist_eval_metric(
                session_id=r["session_id"],
                metric_slug=r["metric_slug"],
                score=r.get("score"),
                passed=r.get("passed"),
                reason=r.get("reason") or "",
                detail="",
                engine="deepeval",
                judge_model=r.get("judge_model") or "",
                scored_at=r.get("scored_at") or 0,
            )
    except Exception:
        log.warning("deepeval bridge: persist failed", exc_info=True)


def score_pending_deepeval(*, batch_size: int = 5, store: Any = None) -> int:
    """Scheduler entry: run the env-configured metrics over sessions that
    have no deepeval verdicts yet. Returns sessions touched. All the guards
    (enabled/available/key/rate) live in ``score_session_deepeval``."""
    metrics = [s.strip() for s in
               os.environ.get("CLAWMETRY_DEEPEVAL_METRICS", "").split(",")
               if s.strip() and s.strip() in SUPPORTED_METRICS]
    if not metrics:
        return 0
    if not (is_available() and _judge_ready()):
        return 0
    try:
        s = store
        if s is None:
            from clawmetry import local_store
            s = local_store.get_store()
        pending = s.query_sessions_missing_eval_metrics(
            engine="deepeval", limit=batch_size, lookback_hours=24,
        )
    except Exception:
        return 0
    touched = 0
    for sess in pending or []:
        sid = sess.get("session_id")
        if not sid:
            continue
        if score_session_deepeval(sid, metrics=metrics, store=s):
            touched += 1
    return touched
