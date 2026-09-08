"""Behaviour Signals: what people and agents *say* about a run (WO-58).

Guard reads the tool stream to ask "is the agent stuck?". This module reads
the words in the same transcripts to ask "is the agent frustrating the person
using it, and is it giving up on them?". Six preset signals, each a binary
match against ONE turn of a session:

  user_frustration    the person swears at or corrects the agent
  user_praise         the person says thanks / perfect / nice
  assistant_refusal   the agent declines ("I can't help with", "as an AI")
  assistant_laziness  the agent hands the work back ("you can do this
                      manually", "left as an exercise", TODO placeholders)
  task_failure        the agent says it could not finish
  user_retry          the person re-sends substantially the same request

Rules this module enforces:

* **Judge-free.** Every matcher is a precompiled regular expression or a
  small structural check (token Jaccard between consecutive user turns).
  There is no LLM on this path and there never will be on the hot path.
* **The matched text is never stored.** A match record carries the signal
  name, the turn reference, the matcher that fired and a short category.
  A stored "this sucks" next to a developer's name is a privacy problem, so
  matches point at the turn and the transcript viewer shows it under the
  existing access rules.
* **Bounded per tick.** The daemon scans at most ``MAX_EVENTS_PER_TICK``
  turn events per pass, reads at most ``SCAN_CAP_CHARS`` of each turn, and
  advances a watermark on ``events.created_at`` so a turn is evaluated once.
* **Coverage is stated, never implied.** A runtime that does not write user
  prompts to disk reports ``user_text: false`` and the surface says "not
  exposed by this runtime" rather than 0%.
* **Precision over recall.** Word boundaries everywhere, a negation guard
  ("not bad", "this doesn't suck") and a positive-context guard ("pretty
  damn good") on the profanity group. "kill the process" matches nothing.

Public surface::

    SIGNALS                       -> the six preset definitions
    match_turn(side, text)        -> [(signal, matcher, category), ...]
    classify_turn(row)            -> (side, text, model, runtime_version)
    run_tick(store, state)        -> int matches recorded this pass
    shape_rates(...)              -> the /api/signals response body
    build_snapshot_slices(store)  -> ("signals", "signalsByRuntime") payloads
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Iterable

log = logging.getLogger("clawmetry.behaviour_signals")

# ── budget knobs ───────────────────────────────────────────────────────────

#: Turn events scanned per daemon tick. 2000 turns of 2 kB is a few MB of
#: text and well under a second of regex work; a backlog drains over a few
#: ticks instead of stalling the daemon on first run.
MAX_EVENTS_PER_TICK = int(os.environ.get("CLAWMETRY_SIGNALS_EVENTS_PER_TICK", "2000"))
#: Characters of a turn the matchers read. A pasted 40 kB log is not a
#: conversation; the words that carry a signal are at the front.
SCAN_CAP_CHARS = int(os.environ.get("CLAWMETRY_SIGNALS_SCAN_CHARS", "2000"))
#: On a fresh install the watermark starts this far back so the surface is
#: not blank for a month while it waits for new turns.
BACKFILL_DAYS = int(os.environ.get("CLAWMETRY_SIGNALS_BACKFILL_DAYS", "30"))
#: Token-set Jaccard at or above which a user turn is a re-send of the
#: previous one.
RETRY_JACCARD = 0.8
RETRY_MIN_TOKENS = 3

WINDOWS_DAYS = {"1d": 1, "7d": 7, "30d": 30}

#: Event types that carry a user or assistant turn, across both dialects the
#: store holds (family adapters: ``message`` + ``data.role``; OpenClaw v3:
#: ``prompt.submitted`` / ``model.completed``).
TURN_EVENT_TYPES = ("message", "user", "assistant",
                    "prompt.submitted", "model.completed")

# ── the six presets ────────────────────────────────────────────────────────

SIGNALS: dict[str, dict[str, str]] = {
    "user_frustration": {"side": "user", "label": "Frustration",
                         "kind": "keyword"},
    "user_praise": {"side": "user", "label": "Praise", "kind": "keyword"},
    "assistant_refusal": {"side": "assistant", "label": "Refusals",
                          "kind": "keyword"},
    "assistant_laziness": {"side": "assistant", "label": "Work handed back",
                           "kind": "keyword"},
    "task_failure": {"side": "assistant", "label": "Gave up",
                     "kind": "keyword"},
    "user_retry": {"side": "user", "label": "Retries", "kind": "structural"},
}
SIGNAL_NAMES = tuple(SIGNALS)
USER_SIGNALS = tuple(s for s, d in SIGNALS.items() if d["side"] == "user")
ASSISTANT_SIGNALS = tuple(s for s, d in SIGNALS.items() if d["side"] == "assistant")


def _rx(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


# Each entry: (matcher_name, category, compiled_regex). Order matters only for
# which matcher name is recorded when several fire; the first wins.
_FRUSTRATION: list[tuple[str, str, re.Pattern]] = [
    ("acronym", "profanity", _rx(r"\b(?:wtf|wth|ffs)\b")),
    ("what_the", "profanity", _rx(r"\bwhat the (?:hell|fuck|heck|actual)\b")),
    ("swear", "profanity", _rx(
        r"\b(?:fuck(?:ing|ed)?|fucks|shit(?:ty)?|bullshit|dammit|damn ?it|"
        r"goddamn|crap|bloody hell|for fuck'?s sake|jesus christ)\b")),
    ("exasperation", "profanity", _rx(r"\b(?:ugh+|argh+|arg+h|grr+|ffs|omfg)\b")),
    ("disgust", "quality", _rx(
        r"\b(?:this|that|it|which) (?:really |just |completely |totally )?"
        r"(?:sucks|blows)\b")),
    ("is_bad", "quality", _rx(
        r"\b(?:this|that|it|which) (?:is|was|'s|looks|seems) "
        r"(?:really |just |completely |totally |absolutely |utterly |so )?"
        r"(?:terrible|horrible|awful|garbage|useless|rubbish|trash|"
        r"pathetic|ridiculous|absurd|unacceptable|a (?:mess|disaster)|"
        r"worse than before)\b")),
    ("you_are_wrong", "correction", _rx(
        r"\b(?:you'?re|you are|that'?s|that is|this is|it'?s|it is) "
        r"(?:still |completely |totally |just |all )?"
        r"(?:wrong|incorrect|not (?:right|correct|helpful|working|even close)|"
        r"making it worse|not listening|hopeless|useless)\b")),
    ("not_what_i_asked", "correction", _rx(
        r"\b(?:that'?s |this is |it'?s )?not what i (?:asked|wanted|said|meant|"
        r"told you|asked for)\b")),
    ("already_told", "correction", _rx(
        r"\bi (?:already|just|literally) (?:told|said|asked|explained)\b")),
    ("how_many_times", "correction", _rx(r"\bhow many times\b")),
    ("are_you_listening", "correction", _rx(
        r"\b(?:are you (?:even )?(?:listening|reading|paying attention)|"
        r"did you even (?:read|look|check|test|run)|"
        r"do you even)\b")),
    ("you_keep", "correction", _rx(
        r"\byou (?:keep|still|again|just) (?:doing|breaking|ignoring|making|"
        r"changing|deleting|adding|removing|reverting|repeating) "
        r"(?:the same|this|that|it|things)\b")),
    ("you_broke", "correction", _rx(
        r"\byou (?:broke|ruined|destroyed|wiped|deleted|messed up|screwed up) "
        r"(?:my|the|our|everything|all)\b")),
    ("why_did_you", "correction", _rx(r"\bwhy (?:did|would|on earth did) you\b")),
    ("nth_time", "correction", _rx(
        r"\b(?:for the |this is the )(?:second|third|fourth|fifth|\d+(?:st|nd|rd|th)|"
        r"last|hundredth|millionth) time\b")),
    ("not_again", "correction", _rx(r"\b(?:not again|no no no|nooo+|noooo+)\b")),
    ("waste", "quality", _rx(r"\bwaste of (?:my )?(?:time|money|tokens|effort)\b")),
    ("still_broken", "correction", _rx(
        r"\bstill (?:broken|not working|doesn'?t work|does not work|fails|"
        r"failing|wrong|the same|not fixed|crashes|crashing)\b")),
    ("give_up", "quality", _rx(r"\b(?:i give up|forget it|never mind,? i'?ll do it)\b")),
    ("seriously", "correction", _rx(r"\b(?:seriously|come on|oh come on)\s*[?!]")),
    ("stop_it", "stop", _rx(
        r"\b(?:please )?stop (?:it|that|this|now|doing that|doing this|"
        r"changing|touching|breaking|adding|deleting|guessing|"
        r"making (?:things|stuff) up)\b")),
    ("stop_alone", "stop", _rx(r"^\s*(?:please\s+)?(?:stop|no)\s*[!.]*\s*$")),
    ("insult", "quality", _rx(r"\b(?:stupid|idiotic|dumb|moronic|braindead|incompetent)\b")),
]

# Words that make a swear positive rather than angry ("pretty damn good").
_POSITIVE_AFTER = _rx(
    r"^\W*(?:\w+\W+){0,2}?(?:good|great|nice|awesome|cool|fast|well|"
    r"impressive|solid|amazing|love|brilliant|beautiful|clean|happy|"
    r"excellent|perfect|fantastic|incredible|smart|clever|sweet|"
    r"right|correct)\b")
# Negation within the two words before a match kills it ("not bad" style,
# "this doesn't suck", "no, that's not wrong").
_NEGATION_BEFORE = _rx(
    r"(?:\b(?:not|no|never|isn'?t|aren'?t|wasn'?t|weren'?t|don'?t|doesn'?t|"
    r"didn'?t|without|hardly|nothing|nobody|barely|rarely|nor|neither|"
    r"if|unless|whether)\W+(?:\w+\W+)?|\bn't\W+)$")

_PRAISE: list[tuple[str, str, re.Pattern]] = [
    ("gratitude", "thanks", _rx(r"\b(?:thanks?|thank you|thx|ty|cheers|much appreciated|appreciate it)\b")),
    ("perfection", "approval", _rx(r"\bperfect(?:o|ly done)?\b")),
    ("great_job", "approval", _rx(
        r"\b(?:great|good|nice|excellent|awesome|amazing|fantastic|brilliant|"
        r"superb|solid|wonderful|beautiful|impressive|outstanding|stellar) "
        r"(?:job|work|stuff|one|catch|fix|call|answer|find|thinking)\b")),
    ("well_done", "approval", _rx(r"\b(?:well done|nailed it|nicely done|spot on|bravo|kudos)\b")),
    ("exclaim", "approval", _rx(
        r"\b(?:love it|love this|looks (?:great|good|perfect)|"
        r"works (?:now|great|perfectly|like a charm)|that worked|"
        r"much better|exactly (?:right|what i (?:wanted|needed|meant))|"
        r"congrats|congratulations)\b")),
    # A bare adjective is praise only when it IS the message ("awesome!"),
    # not when it is one word in a paragraph ("an awesome-list PR sweep").
    ("exclaim_word", "approval", _rx(
        r"\b(?:awesome|excellent|brilliant|fantastic|wonderful|superb|amazing|"
        r"perfect|great|nice|neat|sweet|cool|lovely)\b")),
    ("bare_ok", "approval", _rx(r"^\s*(?:nice|neat|sweet|cool|great|lovely|excellent)\s*[!.]*\s*$")),
    ("you_rock", "approval", _rx(r"\byou(?:'re| are) (?:the best|a (?:star|legend|lifesaver)|awesome|amazing|brilliant)\b")),
]

_REFUSAL: list[tuple[str, str, re.Pattern]] = [
    ("as_an_ai", "policy", _rx(r"\bas an ai(?: (?:language )?model| assistant)?\b")),
    ("cant_help", "decline", _rx(
        r"\bi (?:can'?t|cannot|can not|won'?t|will not|am unable to|'m unable to|"
        r"am not able to|'m not able to|'m not going to|am not going to) "
        r"(?:help (?:you )?with|assist (?:you )?with|do that|provide (?:that|this)|"
        r"comply|write (?:that|this)|create (?:that|this)|generate (?:that|this)|"
        r"fulfil?l (?:that|this)|help (?:you )?(?:do|with) (?:that|this))\b")),
    ("must_decline", "decline", _rx(
        r"\bi (?:must|have to|need to|'ll have to|will have to) (?:decline|refuse)\b")),
    ("not_comfortable", "policy", _rx(
        r"\bi'?m not comfortable (?:doing|writing|creating|with)\b")),
    ("guidelines", "policy", _rx(
        r"\b(?:against|violates?|outside) (?:my|our) (?:guidelines|policies|policy|"
        r"principles|usage policy|content policy)\b")),
    ("wont_do", "decline", _rx(r"\bi (?:won'?t|will not|refuse to) (?:do|write|create|produce|generate) (?:that|this|it)\b")),
]

_LAZINESS: list[tuple[str, str, re.Pattern]] = [
    ("do_it_yourself", "handoff", _rx(
        r"\byou (?:can|could|may|should|will need to|'ll need to|need to|"
        r"will have to|'ll have to|have to|might want to) "
        r"(?:then )?(?:do|run|implement|add|handle|finish|complete|fix|update|"
        r"write|fill in|wire up|hook up|adapt|apply|repeat|extend) "
        r"(?:this|that|it|the rest|these|those|the (?:same|remaining|other)[^.]{0,40}?) "
        r"(?:yourself|manually|on your (?:own|end|side))\b")),
    ("manually", "handoff", _rx(
        r"\byou (?:can|could|should|will need to|'ll need to|need to|will have to|'ll have to) "
        r"(?:manually|yourself)\b")),
    ("exercise", "handoff", _rx(r"\bleft as an exercise\b")),
    ("leave_to_you", "handoff", _rx(
        r"\bi'?ll leave (?:the rest|that|this|it|those|the (?:remaining|other)[^.]{0,30}?) "
        r"(?:to|up to|for) you\b")),
    ("rest_up_to_you", "handoff", _rx(
        r"\b(?:the )?rest (?:is|are|would be) (?:left )?(?:up to|for) you\b")),
    ("implement_rest", "handoff", _rx(
        r"\byou (?:can|could|may|should) (?:then )?(?:implement|complete|finish|fill in|flesh out) "
        r"the (?:rest|remaining|remainder|other|actual)\b")),
    ("todo_placeholder", "placeholder", _rx(
        r"(?:#|//|/\*|<!--)\s*TODO:?\s*(?:implement|add|fill|complete|write|handle|finish|logic|rest)\b")),
    ("rest_of_code", "placeholder", _rx(
        r"(?:#|//|/\*|\.\.\.)\s*(?:\.\.\.\s*)?(?:rest of|remaining|remainder of|existing|other) "
        r"(?:the )?(?:code|implementation|logic|methods|functions|cases|file|handlers)"
        r"(?: (?:goes |remains |stays )?(?:here|unchanged|as before|as is|omitted))?\b")),
    ("similar_for_others", "handoff", _rx(
        r"\b(?:apply|make|repeat|do) (?:the )?(?:same|similar|analogous|equivalent) "
        r"(?:changes?|logic|edits?|updates?|fix|pattern) (?:for|to|in|across) "
        r"(?:the )?(?:other|remaining|rest of the)\b")),
    ("placeholder_here", "placeholder", _rx(
        r"\b(?:your (?:code|logic|implementation) (?:goes )?here|"
        r"insert (?:your )?(?:code|logic|implementation) here|"
        r"implementation (?:goes |is )?(?:here|omitted|left out))\b")),
]

_TASK_FAILURE: list[tuple[str, str, re.Pattern]] = [
    ("unable_to_complete", "gave_up", _rx(
        r"\bi (?:was|am|'m|have been|'ve been) (?:still )?(?:unable|not able) to "
        r"(?:complete|finish|resolve|fix|solve|get (?:this|that|it) (?:to )?work(?:ing)?|"
        r"reproduce|make (?:this|that|it) work|find (?:a|the) (?:fix|solution|cause|root cause))\b")),
    ("couldnt_get_working", "gave_up", _rx(
        r"\bi (?:could ?n(?:o|')t|can ?n(?:o|')t|cannot|was not able to) "
        r"(?:get (?:this|that|it|the \w+) (?:to )?work(?:ing)?|"
        r"make (?:this|that|it|the \w+) work|"
        r"complete (?:this|that|the) (?:task|request|change|fix|work)|"
        r"finish (?:this|that|the) (?:task|request|change|fix|work)|"
        r"resolve (?:this|that|the) (?:issue|problem|error|failure|bug)|"
        r"fix (?:this|that|the) (?:issue|problem|error|failure|bug|test))\b")),
    ("gave_up", "gave_up", _rx(
        r"\bi (?:give|gave|'m giving|am giving|have given|'ve given) up\b")),
    ("unfortunately_could_not", "gave_up", _rx(
        r"\b(?:unfortunately|sadly|regrettably),? i (?:could not|couldn'?t|was unable|"
        r"wasn'?t able|am unable|'m unable|have not been able|haven'?t been able)\b")),
    ("out_of_ideas", "blocked", _rx(
        r"\b(?:i'?m (?:stuck|out of (?:ideas|options|attempts))|"
        r"ran out of (?:attempts|ideas|options|time|retries)|"
        r"i (?:have|'ve) (?:exhausted|run out of) (?:my |the |all )?(?:options|ideas|approaches|attempts))\b")),
    ("cannot_be_done_now", "blocked", _rx(
        r"\b(?:cannot|can'?t|could not|couldn'?t) be (?:completed|fixed|resolved|finished|done) "
        r"(?:at this time|right now|in this session|from here|with (?:the )?current)\b")),
    ("no_longer_able", "blocked", _rx(r"\bi (?:am|'m) no longer able to\b")),
    ("failed_to", "gave_up", _rx(
        r"\bi (?:have )?failed to (?:complete|finish|fix|resolve|solve|get (?:this|that|it) working)\b")),
]

_MATCHERS: dict[str, list[tuple[str, str, re.Pattern]]] = {
    "user_frustration": _FRUSTRATION,
    "user_praise": _PRAISE,
    "assistant_refusal": _REFUSAL,
    "assistant_laziness": _LAZINESS,
    "task_failure": _TASK_FAILURE,
}
_GUARDED_POSITIVE = frozenset({"swear", "exasperation", "insult"})

_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_QUOTED_LINE = re.compile(r"^\s*>.*$", re.MULTILINE)
_XML_TAG_LINE = re.compile(r"^\s*<[a-z][a-z0-9_-]*[^>]*>.*?</[a-z][a-z0-9_-]*>\s*$",
                           re.IGNORECASE | re.DOTALL)
_TOKEN = re.compile(r"[a-z0-9]+")
_SYSTEM_PREFIXES = (
    "<", "[image", "[request interrupted", "[system", "stop hook", "you are a ",
    "you are an ", "<task-notification", "base directory", "caveat:",
    "[tool_use_error]", "[tool_result]",
    # Claude Code re-injects the goal text under the user role when a
    # session-scoped Stop hook fires; the person typed it once already.
    "a session-scoped stop hook", "the stop hook", "stop hook feedback",
    # Agent-to-agent traffic that rides the user role.
    "another claude session sent", "the coordinator sent", "<cross-session",
    "cross-session message", "# /", "# autonomous loop", "# scheduled",
)
#: Session ids of turns a PROGRAM wrote under the user role: Claude Code
#: sub-agents (``::agent-`` in the id) get their prompts from the parent
#: agent, not a person. SDK-driven sessions are flagged from the session
#: row by ``run_tick`` (see ``programmatic_sessions``).
_SUBAGENT_MARKER = "::agent-"
#: Correction / quality / stop matchers only count near the front of a turn
#: or in a short turn. "still broken" 3 kB into a pasted incident brief is a
#: report, not a person losing patience; the swear group is exempt because a
#: swear anywhere is the signal.
_FRONT_CHARS = 240
_BARE_WORD_TURN_CHARS = 80
_SHORT_TURN_CHARS = 600
_FRONT_ONLY_CATEGORIES = frozenset({"correction", "quality", "stop", "thanks", "approval"})
#: "be able to stop it", "how to stop it", "want to stop this": an
#: instruction about stopping, not an order to stop.
_INFINITIVE_BEFORE = _rx(
    r"\b(?:to|can|could|should|would|will|may|might|must|cannot|can'?t|"
    r"able to|how to|want to|need to|'ll|let'?s|and|or)\W*$")
_MAX_SCAN_TEXT = max(200, SCAN_CAP_CHARS)


# ── turn classification ────────────────────────────────────────────────────

def _decode_data(data: Any) -> dict:
    if isinstance(data, dict):
        return data
    if isinstance(data, (bytes, bytearray)):
        try:
            data = data.decode("utf-8", "replace")
        except Exception:
            return {}
    if isinstance(data, str):
        try:
            v = json.loads(data)
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}
    return {}


def _text_of(data: dict) -> str:
    """Turn text across every shape the store holds. Mirrors
    ``quality_signals._text_of`` (family ``content`` string / block list,
    OpenClaw v3 ``finalPromptText`` / ``completionText``)."""
    try:
        from clawmetry.quality_signals import _text_of as _qs_text
        t = _qs_text(data)
        if t:
            return t
    except Exception:
        pass
    c = data.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text") for b in c
                        if isinstance(b, dict) and isinstance(b.get("text"), str))
    for k in ("finalPromptText", "completionText", "text"):
        v = data.get(k)
        if isinstance(v, str) and v:
            return v
    return ""


def resolve_runtime(session_id: str, data: dict | None = None,
                    agent_type: str = "") -> str:
    """Which runtime a turn belongs to. The session-id prefix is the identity
    the rest of the product uses (``sessions.agent_type`` reads ``openclaw``
    for nearly every row on a real install); ``data._runtime`` and then
    ``agent_type`` are the fallbacks."""
    sid = str(session_id or "")
    if ":" in sid:
        head = sid.split(":", 1)[0].strip().lower()
        try:
            from clawmetry.entitlements import ALL_RUNTIMES
            if head in ALL_RUNTIMES:
                return head
        except Exception:
            if head and len(head) <= 32 and head.replace("_", "").isalnum():
                return head
    if isinstance(data, dict):
        rt = data.get("_runtime")
        if isinstance(rt, str) and rt.strip():
            return rt.strip().lower()
    return (str(agent_type or "").strip().lower()) or "openclaw"


def _runtime_version(data: dict) -> str | None:
    for k in ("runtime_version", "runtimeVersion", "cli_version", "cliVersion", "version"):
        v = data.get(k)
        if isinstance(v, (str, int, float)) and str(v).strip():
            return str(v).strip()[:32]
    extra = data.get("extra")
    if isinstance(extra, dict):
        for k in ("runtime_version", "runtimeVersion", "cli_version", "cliVersion", "version"):
            v = extra.get(k)
            if isinstance(v, (str, int, float)) and str(v).strip():
                return str(v).strip()[:32]
    return None


def classify_turn(row: dict) -> tuple[str, str, str, str | None] | None:
    """``(side, text, model, runtime_version)`` for a turn event, or ``None``
    when the row is not a user/assistant turn (tool role, system role,
    injected notification, empty)."""
    et = str(row.get("event_type") or "").strip().lower()
    if et not in TURN_EVENT_TYPES:
        return None
    data = _decode_data(row.get("data"))
    role = str(data.get("role") or "").strip().lower()
    if et in ("prompt.submitted", "user"):
        side = "user"
    elif et in ("model.completed", "assistant"):
        side = "assistant"
    elif role in ("user", "human"):
        side = "user"
    elif role in ("assistant", "model", "ai"):
        side = "assistant"
    else:
        return None
    text = _text_of(data)
    if not isinstance(text, str) or not text.strip():
        return None
    model = str(row.get("model") or data.get("model") or data.get("modelId") or "").strip()
    if not model:
        extra = data.get("extra")
        if isinstance(extra, dict) and isinstance(extra.get("model"), str):
            model = extra["model"].strip()
    return side, text, model or "unknown", _runtime_version(data)


def is_human_prompt(text: str, session_id: str = "") -> bool:
    """A user turn that a person typed, as opposed to a notification the
    runtime injected under the user role (task notifications, image
    placeholders, interrupt markers, hook feedback, system prompts) or a
    prompt another agent wrote (sub-agent sessions)."""
    if session_id and _SUBAGENT_MARKER in str(session_id):
        return False
    t = (text or "").lstrip()
    if not t:
        return False
    low = t[:40].lower()
    for p in _SYSTEM_PREFIXES:
        if low.startswith(p):
            return False
    return True


def programmatic_sessions(store, session_ids: Iterable[str]) -> set[str]:
    """Session ids whose user role is a program, from the session row:
    an SDK entrypoint (``entrypoint`` / ``surface`` / ``source`` of ``sdk``
    or ``sdk-cli``) or an explicit ``isSubagent`` flag. Their user turns are
    not a person's words and are left out of the user-side denominators.
    Empty set when the store cannot answer."""
    ids = [str(x) for x in session_ids if x]
    if not ids:
        return set()
    try:
        fn = getattr(store, "query_signal_session_flags", None)
        if not callable(fn):
            return set()
        flags = fn(session_ids=ids) or {}
    except Exception:
        return set()
    return {sid for sid, f in flags.items() if isinstance(f, dict) and f.get("programmatic")}


def _scan_text(text: str) -> str:
    """The part of a turn the matchers read: capped, with code fences, inline
    code and quoted lines removed so a pasted log or a quoted error message
    cannot fire a keyword."""
    t = (text or "")[:_MAX_SCAN_TEXT]
    t = _FENCED_CODE.sub(" ", t)
    t = _INLINE_CODE.sub(" ", t)
    t = _QUOTED_LINE.sub(" ", t)
    return t


def _guarded(name: str, category: str, text: str, m: re.Match) -> bool:
    """True when a match should be suppressed by its context."""
    before = text[max(0, m.start() - 40):m.start()]
    if _NEGATION_BEFORE.search(before):
        return True
    if name in _GUARDED_POSITIVE:
        after = text[m.end():m.end() + 40]
        if _POSITIVE_AFTER.search(after):
            return True
    if name in ("stop_it", "stop_alone") and _INFINITIVE_BEFORE.search(before[-16:]):
        return True
    if name == "exclaim_word" and len(text.strip()) > _BARE_WORD_TURN_CHARS:
        return True
    if (category in _FRONT_ONLY_CATEGORIES and m.start() >= _FRONT_CHARS
            and len(text) > _SHORT_TURN_CHARS):
        return True
    return False


def match_text(signal: str, text: str) -> tuple[str, str] | None:
    """``(matcher, category)`` for the first matcher of ``signal`` that fires
    on ``text``, else ``None``. Pure."""
    rules = _MATCHERS.get(signal)
    if not rules:
        return None
    scan = _scan_text(text)
    if not scan.strip():
        return None
    for name, category, rx in rules:
        for m in rx.finditer(scan):
            if _guarded(name, category, scan, m):
                continue
            return name, category
    return None


def match_turn(side: str, text: str) -> list[tuple[str, str, str]]:
    """Every keyword signal that fires on one turn:
    ``[(signal, matcher, category), ...]``. Pure; ``user_retry`` is
    structural and handled by :func:`retry_match`."""
    out: list[tuple[str, str, str]] = []
    names = USER_SIGNALS if side == "user" else ASSISTANT_SIGNALS
    for sig in names:
        if SIGNALS[sig]["kind"] != "keyword":
            continue
        hit = match_text(sig, text)
        if hit:
            out.append((sig, hit[0], hit[1]))
    return out


def tokens_of(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall((text or "")[:_MAX_SCAN_TEXT].lower()))


def retry_match(prev_tokens: frozenset[str] | None, cur_tokens: frozenset[str]
                ) -> tuple[str, str] | None:
    """``("jaccard", "repeat")`` when the current user turn re-sends the
    previous one (token-set Jaccard >= RETRY_JACCARD, both long enough to
    be a request rather than an acknowledgement)."""
    if not prev_tokens or len(prev_tokens) < RETRY_MIN_TOKENS:
        return None
    if len(cur_tokens) < RETRY_MIN_TOKENS:
        return None
    inter = len(prev_tokens & cur_tokens)
    union = len(prev_tokens | cur_tokens)
    if union and (inter / union) >= RETRY_JACCARD:
        return "jaccard", "repeat"
    return None


def _epoch_ms(ts: Any) -> int | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        v = float(ts)
        return int(v if v > 1e11 else v * 1000)
    s = str(ts).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        pass
    try:
        v = float(s)
        return int(v if v > 1e11 else v * 1000)
    except Exception:
        return None


# ── the daemon tick ────────────────────────────────────────────────────────

def evaluate_rows(rows: Iterable[dict], prev_user: dict[str, frozenset[str]] | None = None,
                  programmatic: set[str] | None = None,
                  ) -> tuple[list[dict], list[dict]]:
    """Turn raw event rows into ``(turns, matches)`` ready for the store.

    ``turns`` is one row per eligible user/assistant turn (the rate's
    denominator); ``matches`` is one row per (turn, signal). ``prev_user``
    is the per-session memory of the last human user turn's token set used
    by ``user_retry``; it is mutated so a caller can carry it across ticks.
    Nothing here stores text: the token sets live only in memory.
    """
    if prev_user is None:
        prev_user = {}
    programmatic = programmatic or set()
    turns: list[dict] = []
    matches: list[dict] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        cls = classify_turn(r)
        if not cls:
            continue
        side, text, model, rver = cls
        sid = str(r.get("session_id") or "")
        eid = str(r.get("id") or "")
        if not sid or not eid:
            continue
        if side == "user" and (sid in programmatic or not is_human_prompt(text, sid)):
            continue
        data = _decode_data(r.get("data"))
        runtime = resolve_runtime(sid, data, str(r.get("agent_type") or ""))
        turn_ms = _epoch_ms(r.get("ts")) or int(r.get("created_at") or 0) or int(time.time() * 1000)
        base = {
            "session_id": sid, "agent_type": runtime,
            "node_id": str(r.get("node_id") or ""), "model": model,
            "runtime_version": rver, "turn_ts": str(r.get("ts") or ""),
            "turn_ms": turn_ms, "event_id": eid, "side": side,
        }
        turns.append(dict(base))
        for sig, matcher, category in match_turn(side, text):
            matches.append(dict(base, signal=sig, matcher=matcher, category=category))
        if side == "user":
            cur = tokens_of(text)
            hit = retry_match(prev_user.get(sid), cur)
            if hit:
                matches.append(dict(base, signal="user_retry", matcher=hit[0], category=hit[1]))
            prev_user[sid] = cur
    return turns, matches


_STATE_KEY = "behaviour_signals"


def run_tick(store, state: dict) -> int:
    """One daemon pass: read new turn events past the watermark, evaluate,
    persist. Returns the number of matches recorded. Never raises."""
    try:
        st = state.get(_STATE_KEY)
        if not isinstance(st, dict):
            st = {}
            state[_STATE_KEY] = st
        wm = st.get("created_at")
        after_id = st.get("after_id")
        if not isinstance(wm, int):
            wm = int((time.time() - BACKFILL_DAYS * 86400) * 1000)
            after_id = None
        rows = store.query_events_by_ingest(
            created_after=wm, after_id=after_id,
            event_types=TURN_EVENT_TYPES, limit=MAX_EVENTS_PER_TICK,
        ) or []
        if not rows:
            return 0
        prev_raw = st.get("prev_user")
        prev_user: dict[str, frozenset[str]] = {}
        if isinstance(prev_raw, dict):
            for k, v in prev_raw.items():
                if isinstance(v, list):
                    prev_user[str(k)] = frozenset(str(x) for x in v)
        prog = programmatic_sessions(store, {str(r.get("session_id") or "") for r in rows})
        turns, matches = evaluate_rows(rows, prev_user, prog)
        n = 0
        if turns:
            n = int(store.record_signal_turns(turns, matches) or 0)
        last = rows[-1]
        st["created_at"] = int(last.get("created_at") or wm)
        st["after_id"] = str(last.get("id") or "")
        # Bound the retry memory to the most recently active sessions; a
        # token set is a few hundred short strings and the memory is kept
        # only for the sessions touched in the last passes.
        keep = list(prev_user.items())[-200:]
        st["prev_user"] = {k: sorted(v)[:400] for k, v in keep}
        st["last_run"] = time.time()
        st["last_scanned"] = len(rows)
        return n
    except Exception as e:  # noqa: BLE001
        log.warning("behaviour signals: tick failed: %s", e)
        return 0


# ── coverage ───────────────────────────────────────────────────────────────

def adapter_coverage_overrides() -> dict[str, dict]:
    """``{runtime: {"user_text": bool, "assistant_text": bool}}`` declared by
    adapters that expose ``signal_coverage()``. A declaration wins over
    inference. Optional everywhere: no adapter has to implement it."""
    out: dict[str, dict] = {}
    try:
        from clawmetry.sync import _FAMILY_ADAPTER_SPECS
    except Exception:
        return out
    for mod_name, cls_name in _FAMILY_ADAPTER_SPECS:
        try:
            mod = __import__(mod_name, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            fn = getattr(cls, "signal_coverage", None)
            if not callable(fn):
                continue
            try:
                decl = fn()
            except TypeError:
                decl = fn(cls())
            rt = str(getattr(cls, "RUNTIME_ID", None) or getattr(cls, "runtime", None)
                     or getattr(cls, "name", None) or "").strip().lower()
            if not rt or not isinstance(decl, dict):
                continue
            out[rt] = {"user_text": bool(decl.get("user_text")),
                       "assistant_text": bool(decl.get("assistant_text")),
                       "source": "adapter"}
        except Exception:
            continue
    return out


def coverage_state(user_text: bool, assistant_text: bool) -> str:
    if user_text and assistant_text:
        return "user_text+assistant_text"
    if user_text:
        return "user_text"
    if assistant_text:
        return "assistant_text"
    return "none"


def shape_coverage(inferred: dict[str, dict] | None,
                   overrides: dict[str, dict] | None = None) -> dict[str, dict]:
    """Merge store inference with adapter declarations into the shape the
    API and the snapshot both emit::

        {runtime: {user_text, assistant_text, state, source, user_turns,
                   assistant_turns}}
    """
    out: dict[str, dict] = {}
    for rt, row in (inferred or {}).items():
        ut = int(row.get("user_turns") or 0)
        at = int(row.get("assistant_turns") or 0)
        out[rt] = {"user_text": ut > 0, "assistant_text": at > 0,
                   "user_turns": ut, "assistant_turns": at,
                   "source": "inferred"}
    for rt, decl in (overrides or {}).items():
        cur = out.setdefault(rt, {"user_turns": 0, "assistant_turns": 0})
        cur["user_text"] = bool(decl.get("user_text"))
        cur["assistant_text"] = bool(decl.get("assistant_text"))
        cur["source"] = "adapter"
    for rt, cur in out.items():
        cur["state"] = coverage_state(cur["user_text"], cur["assistant_text"])
    return out


# ── aggregation into the API shape ─────────────────────────────────────────

_DAY_MS = 86400 * 1000


def _day_iso(day_index: int) -> str:
    return datetime.fromtimestamp(day_index * 86400, tz=timezone.utc).strftime("%Y-%m-%d")


def _rate(count: int, eligible: int) -> float | None:
    return round(count / eligible, 4) if eligible > 0 else None


def shape_rates(turn_rows: list[dict], match_rows: list[dict], *,
                window_days: int, now_ms: int | None = None,
                runtime: str | None = None) -> dict:
    """Fold grouped store rows into per-signal rates.

    ``turn_rows``: ``{agent_type, side, model, runtime_version, day, n}``
    ``match_rows``: ``{agent_type, signal, model, runtime_version, day, n}``
    Both cover the current window AND the one before it (2 x window_days),
    so the trend is computed here. ``day`` is ``turn_ms // 86400000``.
    """
    now_ms = now_ms or int(time.time() * 1000)
    today = now_ms // _DAY_MS
    cur_start = today - window_days + 1
    prev_start = cur_start - window_days

    def _in_cur(d: int) -> bool:
        return d >= cur_start

    def _in_prev(d: int) -> bool:
        return prev_start <= d < cur_start

    # denominators
    elig: dict[str, dict] = {"user": {}, "assistant": {}}
    for side in elig:
        elig[side] = {"cur": 0, "prev": 0, "day": {}, "model": {}, "ver": {},
                      "rt": {}}
    for t in turn_rows:
        side = str(t.get("side") or "")
        if side not in elig:
            continue
        d = int(t.get("day") or 0)
        n = int(t.get("n") or 0)
        e = elig[side]
        if _in_cur(d):
            e["cur"] += n
            e["day"][d] = e["day"].get(d, 0) + n
            e["model"][t.get("model") or "unknown"] = e["model"].get(t.get("model") or "unknown", 0) + n
            v = t.get("runtime_version") or "unknown"
            e["ver"][v] = e["ver"].get(v, 0) + n
            rt = t.get("agent_type") or "openclaw"
            e["rt"][rt] = e["rt"].get(rt, 0) + n
        elif _in_prev(d):
            e["prev"] += n

    signals: dict[str, dict] = {}
    for sig, meta in SIGNALS.items():
        e = elig[meta["side"]]
        signals[sig] = {
            "label": meta["label"], "side": meta["side"],
            "count": 0, "eligible": e["cur"], "rate": None,
            "trend": {"previous_count": 0, "previous_eligible": e["prev"],
                      "previous_rate": None, "delta": None, "direction": "flat"},
            "per_day": [], "by_model": {}, "by_runtime_version": {},
            "by_runtime": {},
            "_day": {}, "_model": {}, "_ver": {}, "_rt": {},
        }
    for m in match_rows:
        sig = str(m.get("signal") or "")
        if sig not in signals:
            continue
        d = int(m.get("day") or 0)
        n = int(m.get("n") or 0)
        s = signals[sig]
        if _in_cur(d):
            s["count"] += n
            s["_day"][d] = s["_day"].get(d, 0) + n
            mk = m.get("model") or "unknown"
            s["_model"][mk] = s["_model"].get(mk, 0) + n
            v = m.get("runtime_version") or "unknown"
            s["_ver"][v] = s["_ver"].get(v, 0) + n
            rt = m.get("agent_type") or "openclaw"
            s["_rt"][rt] = s["_rt"].get(rt, 0) + n
        elif _in_prev(d):
            s["trend"]["previous_count"] += n

    for sig, s in signals.items():
        e = elig[s["side"]]
        s["rate"] = _rate(s["count"], s["eligible"])
        pr = _rate(s["trend"]["previous_count"], s["trend"]["previous_eligible"])
        s["trend"]["previous_rate"] = pr
        if s["rate"] is not None and pr is not None:
            delta = round(s["rate"] - pr, 4)
            s["trend"]["delta"] = delta
            s["trend"]["direction"] = "up" if delta > 0.005 else ("down" if delta < -0.005 else "flat")
        for d in range(cur_start, today + 1):
            c = s["_day"].get(d, 0)
            el = e["day"].get(d, 0)
            s["per_day"].append({"day": _day_iso(d), "count": c, "eligible": el,
                                 "rate": _rate(c, el)})
        for mk, el in e["model"].items():
            c = s["_model"].get(mk, 0)
            s["by_model"][mk] = {"count": c, "eligible": el, "rate": _rate(c, el)}
        for v, el in e["ver"].items():
            c = s["_ver"].get(v, 0)
            s["by_runtime_version"][v] = {"count": c, "eligible": el, "rate": _rate(c, el)}
        for rt, el in e["rt"].items():
            c = s["_rt"].get(rt, 0)
            s["by_runtime"][rt] = {"count": c, "eligible": el, "rate": _rate(c, el)}
        for k in ("_day", "_model", "_ver", "_rt"):
            s.pop(k, None)

    return {
        "window": f"{window_days}d", "window_days": window_days,
        "runtime": runtime or "all",
        "eligible_turns": {"user": elig["user"]["cur"], "assistant": elig["assistant"]["cur"]},
        "signals": signals,
        "generated_at": datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc).isoformat(),
    }


_RUNTIME_LABELS = {
    "claude_code": "Claude Code", "openclaw": "OpenClaw", "nemoclaw": "NemoClaw",
    "codex": "Codex", "cursor": "Cursor", "copilot": "Copilot", "hermes": "Hermes",
    "gemini_cli": "Gemini CLI", "goose": "Goose", "aider": "Aider",
    "opencode": "OpenCode", "qwen_code": "Qwen Code", "cline": "Cline",
    "devin": "Devin", "grok_bot": "Grok Bot", "pi": "Pi", "exo": "Exo",
    "picoclaw": "PicoClaw", "nanoclaw": "NanoClaw", "antigravity": "Antigravity",
    "kimi": "Kimi", "n8n": "n8n", "openhands": "OpenHands", "deepagents": "DeepAgents",
    "lovable": "Lovable", "replit": "Replit", "openworker": "OpenWorker",
}


def runtime_label(rt: str) -> str:
    rt = str(rt or "")
    return _RUNTIME_LABELS.get(rt, rt.replace("_", " ").title() if rt else "all runtimes")


def headline(rates: dict, by_runtime: dict[str, dict] | None = None) -> dict:
    """The one sentence the tab leads with: the signal that moved most.

    Plain words, no jargon, no em dashes. ``by_runtime`` (``{rt: rates}``)
    lets a node-wide view name the runtime that drove the move.
    """
    signals = (rates or {}).get("signals") or {}
    best = None
    for sig, s in signals.items():
        d = (s.get("trend") or {}).get("delta")
        if d is None:
            continue
        if best is None or abs(d) > abs(best[1]):
            best = (sig, d)
    measured = any((s.get("eligible") or 0) > 0 for s in signals.values())
    if not measured:
        return {"text": "Nothing measured yet. Signals appear once a session with readable turns lands.",
                "signal": None, "direction": None, "runtime": None}
    if best is None or abs(best[1]) < 0.005:
        win = (rates or {}).get("window") or "window"
        return {"text": f"No signal moved much in the last {win}.",
                "signal": None, "direction": "flat", "runtime": None}
    sig, delta = best
    label = SIGNALS.get(sig, {}).get("label", sig)
    direction = "up" if delta > 0 else "down"
    rt_name = (rates or {}).get("runtime") or "all"
    if rt_name == "all" and by_runtime:
        best_rt = None
        for rt, r in by_runtime.items():
            d = (((r or {}).get("signals") or {}).get(sig) or {}).get("trend", {}).get("delta")
            if d is None:
                continue
            if best_rt is None or abs(d) > abs(best_rt[1]):
                best_rt = (rt, d)
        if best_rt and (best_rt[1] > 0) == (delta > 0):
            rt_name = best_rt[0]
    since = _since_words(signals.get(sig) or {}, direction)
    where = f" on {runtime_label(rt_name)}" if rt_name != "all" else ""
    pct = abs(round(delta * 100, 1))
    text = f"{label} is {direction}{where} {since} ({pct} points vs the window before)."
    return {"text": text, "signal": sig, "direction": direction,
            "runtime": None if rt_name == "all" else rt_name, "delta": delta}


def _since_words(sig_rates: dict, direction: str) -> str:
    """'since Tuesday' style phrase: the first day of the window whose daily
    rate crossed the previous window's rate in the trend's direction."""
    prev = (sig_rates.get("trend") or {}).get("previous_rate")
    days = sig_rates.get("per_day") or []
    if prev is None or not days:
        return "this window"
    for d in days:
        r = d.get("rate")
        if r is None:
            continue
        if (direction == "up" and r > prev) or (direction == "down" and r < prev):
            try:
                dt = datetime.strptime(d["day"], "%Y-%m-%d")
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                if d["day"] == today:
                    return "since today"
                return f"since {dt.strftime('%A')}"
            except Exception:
                return "this window"
    return "this window"


# ── store-facing helpers (called by LocalStore and the snapshot) ──────────

def rates_for(store, window_days: int, runtime: str | None = None,
              now_ms: int | None = None) -> dict:
    """``shape_rates`` over the store's grouped rows for ``window_days``.
    Empty shape (rates ``None``) on any store failure, never an exception."""
    try:
        now_ms = now_ms or int(time.time() * 1000)
        since_ms = now_ms - 2 * window_days * _DAY_MS
        grouped = store.query_signal_grouped(since_ms=since_ms, runtime=runtime) or {}
        return shape_rates(grouped.get("turns") or [], grouped.get("matches") or [],
                           window_days=window_days, now_ms=now_ms, runtime=runtime)
    except Exception as e:  # noqa: BLE001
        log.debug("behaviour signals: rates_for failed: %s", e)
        return shape_rates([], [], window_days=window_days, now_ms=now_ms, runtime=runtime)


def coverage_for(store, days: int = 30) -> dict[str, dict]:
    try:
        inferred = store.query_signal_coverage(days=days) or {}
    except Exception:
        inferred = {}
    return shape_coverage(inferred, adapter_coverage_overrides())


def full_report(store, window_days: int, runtime: str | None = None) -> dict:
    """The /api/signals body: rates + coverage + headline, for one window."""
    rates = rates_for(store, window_days, runtime)
    cov = coverage_for(store, days=max(window_days, 7))
    by_rt = None
    if not runtime or runtime == "all":
        by_rt = {}
        for rt in list(cov.keys())[:40]:
            by_rt[rt] = rates_for(store, window_days, rt)
    rates["coverage"] = cov
    rates["headline"] = headline(rates, by_rt)
    if runtime and runtime != "all":
        c = cov.get(runtime)
        rates["runtime_coverage"] = c or {"state": "unknown", "user_text": False,
                                         "assistant_text": False, "source": "none"}
    return rates


def build_snapshot_slices(store) -> tuple[dict, dict]:
    """``(signals, signalsByRuntime)`` for ``sync_system_snapshot``.

    Same shape as /api/signals per window (1d / 7d / 30d), minus anything
    per session, so the hosted dashboard renders the identical numbers.
    Small by construction: six signals x three windows x a handful of
    buckets. Never raises: an empty dict is an honest "nothing measured".
    """
    node: dict = {}
    per_rt: dict = {}
    try:
        cov = coverage_for(store)
        runtimes = list(cov.keys())[:40]
        for key, days in WINDOWS_DAYS.items():
            rates = rates_for(store, days, None)
            by_rt = {rt: rates_for(store, days, rt) for rt in runtimes}
            rates["coverage"] = cov
            rates["headline"] = headline(rates, by_rt)
            node[key] = rates
            for rt, r in by_rt.items():
                r["coverage"] = {rt: cov.get(rt)} if cov.get(rt) else {}
                r["runtime_coverage"] = cov.get(rt) or {}
                r["headline"] = headline(r)
                per_rt.setdefault(rt, {})[key] = r
        node["coverage"] = cov
    except Exception as e:  # noqa: BLE001
        log.debug("behaviour signals: snapshot slice failed: %s", e)
        return {}, {}
    return node, per_rt
