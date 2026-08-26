"""routes/attention.py — "which of my agents needs me right now".

The one question the dashboard exists to answer before any chart. Serves the
attention state the daemon computed and persisted onto the session rows
(``clawmetry/sync.py::_refresh_attention_cache`` ->
``local_store.apply_session_attention``), so this handler does ONE read and
never runs detection itself.

THE HONESTY CONTRACT (the reason this module is more than a filter):

    signal="hook"      the runtime told us it opened a prompt -> "Waiting for you"
    signal="queue"     a real approval sits unanswered here   -> "Waiting for you"
    signal="inferred"  a tool call has hung with no result    -> "Looks like it's waiting"
    daemon stale       nobody has computed this recently      -> "Can't tell right now"

``hook`` and ``queue`` are equally CERTAIN and differ only in PROVENANCE,
which decides who clears the row: a hook row belongs to the hook receiver and
survives the daemon's replace, a queue row is re-derived every tick and
vanishes the moment the approval is answered.

Those are three different sentences and the UI renders all three. An empty
list from a wedged detector must NEVER read as "nothing needs you" -- a badge
that cries wolf, or a calm all-clear that is wrong, teaches people to stop
trusting the list, and an ignored list is worth less than no list at all.

Freshness asks the honest question -- "is the thing that computes this
alive?" -- and answers it DIRECTLY, by checking the daemon's registered pid.
An earlier version inferred it from heartbeat age, which a real machine
disproved: a daemon serving queries normally with a ten-hour-old heartbeat
row made the page say "can't tell right now" about a node it could have
answered for. Wrong in the safe direction, but permanently wrong on any node
whose heartbeat writer has stalled.

Cloud parity: every field here rides the session rows that are already in the
snapshot, so the cloud interceptor reads the same slice. No new ingest.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime

from flask import Blueprint, jsonify, request

log = logging.getLogger("clawmetry-attention")

bp_attention = Blueprint("attention", __name__)

#: Signals we KNOW rather than deduce. One definition, so a new source cannot
#: end up rendering as certain on one surface and hedged on another.
CONFIRMED_SIGNALS = frozenset({"hook", "queue"})

#: How recently a session must have moved to count as "working".
#:
#: Not merely "not ended". Sessions routinely never receive an ``ended_at`` --
#: the process is killed, the machine sleeps, the runtime crashes -- so a
#: status-only test counts long-dead sessions as busy. Measured on a real
#: install mid-build: all 6 sessions that a status-only test called "working"
#: had last moved between 30 minutes and 24 hours earlier. "6 agents working"
#: under a reassuring "nothing needs you" would have been confidently wrong
#: in the one place this feature must not be.
WORKING_RECENT_MINUTES = 15

#: Runtimes with no per-tool approval gate at all. Saying "none waiting" for
#: these would imply we looked and found nothing, when in truth there is
#: nothing to look for. The UI says "this runtime doesn't ask" instead.
#: Pi's own design: its trust machinery guards loading settings and
#: extensions, not running tools.
RUNTIMES_WITHOUT_APPROVAL = frozenset({"pi"})


def _iso_age_seconds(ts) -> int:
    """Seconds since an ISO-ish timestamp; -1 when unparseable/absent."""
    if not ts:
        return -1
    try:
        s = str(ts).strip().replace("Z", "")
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            dt = datetime.fromisoformat(s.split(".")[0].split("+")[0])
        ref = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        return max(0, int((ref - dt).total_seconds()))
    except Exception:
        return -1


def _sessions():
    """Session rows via the daemon proxy, falling back to a local read.

    Same two-step every other route uses: the daemon owns the writer lock, so
    a direct open here would fight it.
    """
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_sessions_table", limit=300)
        if rows is not None:
            return rows
    except Exception:
        pass
    try:
        from clawmetry import local_store
        return local_store.get_store(read_only=True).query_sessions_table(limit=300)
    except Exception:
        return None


def _daemon_is_live() -> bool:
    """Is the process that computes attention state actually running?

    Checked DIRECTLY — the daemon registers a query server and we confirm its
    pid is alive — rather than inferred from heartbeat age.

    Heartbeat age was the first implementation and it is a PROXY, which a real
    machine disproved: a daemon here was serving queries normally while its
    newest heartbeat row was ten hours old, so the strip reported "can't tell
    right now" on a node it could perfectly well have answered for. Erring
    toward "can't tell" is the right direction to be wrong in, but a node with
    a stalled heartbeat writer would have shown that state permanently, which
    makes the feature useless exactly where nothing else is obviously broken.

    The attention pass runs on the daemon's own loop, in this process, so
    "the daemon is alive" is the direct answer to "is this list current".
    """
    try:
        from routes.local_query import _read_discovery
        # _read_discovery already verifies the recorded pid is alive and
        # returns None otherwise, which is exactly the question here.
        return _read_discovery() is not None
    except Exception:
        return False


def _daemon_age_seconds() -> int:
    """Seconds since the daemon last wrote a heartbeat; -1 when unknown.

    Retained for the ``daemon_age_seconds`` field (operators asked for the
    number, and a large value is a genuine signal that the heartbeat writer
    has stalled) but NO LONGER decides freshness — see :func:`_daemon_is_live`.
    """
    try:
        from routes.local_query import local_store_via_daemon
        beats = local_store_via_daemon("query_heartbeats", limit=1)
        if beats is None:
            from clawmetry import local_store
            beats = local_store.get_store(read_only=True).query_heartbeats(limit=1)
        if beats:
            return _iso_age_seconds(beats[0].get("ts"))
    except Exception:
        pass
    return -1


def _project_of(row: dict) -> str:
    """Human-facing project label. Late import so the sessions module's
    helper stays the single definition."""
    try:
        from routes.sessions import _project_name
        return _project_name(row.get("cwd") or "")
    except Exception:
        return ""


def build_attention(runtime: str = "") -> dict:
    """The payload behind GET /api/attention. Importable so the overview
    path and any future consumer share one shape."""
    rows = _sessions()
    if rows is None:
        # We could not read at all — that is "can't tell", not "all clear".
        return {
            "items": [], "waiting": 0, "working": 0,
            "fresh": False, "reason": "unavailable",
            "daemon_age_seconds": -1, "runtimes_without_approval": [],
        }

    rt = (runtime or "").strip().lower()
    items, working, seen_runtimes = [], 0, set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        row_rt = str(r.get("agent_type") or "").lower()
        if rt and rt != "all" and row_rt != rt:
            continue
        seen_runtimes.add(row_rt)
        state = r.get("attention_state") or ""
        if not state:
            # Sessions that are RECENTLY ACTIVE and not blocked are quietly
            # working — the number that makes "nothing needs you" reassuring
            # instead of ambiguous (nothing waiting because nothing is
            # running at all). The recency test is load-bearing: a session
            # that was killed, slept, or crashed often keeps status='active'
            # forever, so counting on status alone reports long-dead sessions
            # as busy.
            if not r.get("ended_at") and str(
                r.get("status") or "").lower() not in (
                    "ended", "completed", "stopped", "failed"):
                idle = _iso_age_seconds(
                    r.get("last_active_at") or r.get("started_at"))
                if 0 <= idle <= WORKING_RECENT_MINUTES * 60:
                    working += 1
            continue
        since_ms = r.get("attention_since")
        waiting_s = 0
        if since_ms:
            try:
                waiting_s = max(0, int(time.time() - int(since_ms) / 1000))
            except (TypeError, ValueError):
                waiting_s = 0
        items.append({
            "session_id": r.get("session_id") or "",
            "runtime":    row_rt,
            "state":      state,
            # "hook" = the runtime told us. "inferred" = we deduced it from a
            # hung tool call. The UI must render these differently.
            "signal":     r.get("attention_signal") or "inferred",
            "tool":       r.get("attention_tool") or "",
            "waiting_seconds": waiting_s,
            "title":      r.get("title") or "",
            "project":    _project_of(r),
            "git_branch": r.get("git_branch") or "",
        })

    # Hook-confirmed first, then longest wait: certainty outranks duration,
    # because a row we are sure about deserves the eye before a guess.
    items.sort(key=lambda i: (i["signal"] not in CONFIRMED_SIGNALS,
                              -i["waiting_seconds"]))

    # Freshness = "is the process that computes this alive", answered
    # directly. Heartbeat age is reported alongside because a big number is a
    # real signal, but it does NOT gate the answer — see _daemon_is_live.
    fresh = _daemon_is_live()
    age = _daemon_age_seconds()
    return {
        "items":   items if fresh else [],
        "waiting": len(items) if fresh else 0,
        "working": working,
        "fresh":   fresh,
        "reason":  "" if fresh else "daemon_not_running",
        "daemon_age_seconds": age,
        # Surfaced so the UI can say "Pi doesn't ask" rather than implying
        # we checked it and found nothing.
        "runtimes_without_approval": sorted(
            seen_runtimes & RUNTIMES_WITHOUT_APPROVAL),
    }


#: Keys each runtime uses for the session id, in priority order. One tolerant
#: extractor beats a per-runtime parser: the payloads differ only in spelling.
_SESSION_KEYS = ("session_id", "sessionId", "session", "conversation_id",
                 "conversationId", "id")
_TOOL_KEYS = ("tool_name", "toolName", "tool", "name", "command")

#: Runtimes we will accept a hook from. Bounded so a typo cannot silently
#: create rows under a runtime the rest of the app has never heard of.
_KNOWN_RUNTIMES = frozenset({
    "claude_code", "codex", "cursor", "openclaw", "nemoclaw", "qwen_code",
    "opencode", "aider", "goose", "hermes", "picoclaw", "nanoclaw",
    "antigravity", "copilot", "grok", "deepagents", "n8n", "pi", "qm",
    "deepseek_harness", "exo", "kimi", "devin", "gemini_cli", "cline", "openhands",
    "openworker",
})


def _first(body: dict, keys) -> str:
    for k in keys:
        v = body.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


@bp_attention.route("/api/hooks/attention", methods=["POST"])
def api_hook_attention():
    """Generic "my agent is waiting on a human" receiver, any runtime.

    OBSERVE ONLY. This endpoint records that a prompt is open and returns
    immediately; it never answers the prompt, never blocks the agent, and
    shares no code path with the approvals gate. That separation is
    deliberate — nothing an observability feature does should be able to
    delay a decision a human is being asked to make.

    Why generic: Claude Code, Copilot and Qwen Code all fire a
    ``PermissionRequest``; Gemini CLI fires ``Notification`` when the agent
    needs attention. The payloads differ only in spelling, so one tolerant
    extractor covers them all, and wiring a new runtime is a line in its own
    hook config rather than an installer we have to ship and verify first:

        {"command": "curl -s -X POST -H 'Content-Type: application/json' \\
            --data-binary @- http://127.0.0.1:8900/api/hooks/attention?runtime=qwen_code"}

    Body: the runtime's own hook JSON, unmodified. ``?runtime=`` names the
    runtime (or a ``runtime`` key in the body). ``?event=resolved`` clears.

    ALWAYS 200, always fast, never authoritative about anything else. A hook
    that errors could stall someone's agent, so this one cannot error.
    """
    if request.remote_addr not in ("127.0.0.1", "::1", None):
        return jsonify({"ok": False, "error": "loopback only"}), 403
    try:
        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            body = {}
        runtime = (request.args.get("runtime")
                   or str(body.get("runtime") or "")).strip().lower()
        if runtime not in _KNOWN_RUNTIMES:
            return jsonify({"ok": False, "error": "unknown runtime"}), 400

        sid = _first(body, _SESSION_KEYS)
        if not sid:
            return jsonify({"ok": False, "error": "no session id"}), 400
        # Family runtimes are stored namespaced (`claude_code:<uuid>`); accept
        # either form so a hook can send the runtime's own bare id.
        if runtime != "openclaw" and not sid.startswith(runtime + ":"):
            sid = f"{runtime}:{sid}"

        event = (request.args.get("event")
                 or str(body.get("event") or "waiting")).strip().lower()
        # Report what ACTUALLY happened. A write can silently no-op — the
        # commonest cause being an older daemon whose proxy allowlist has no
        # set_session_attention — and answering "ok" regardless would leave
        # someone wiring up a hook with no way to tell it through. The hook
        # still never fails: `stored:false` is information, not an error.
        from routes.hooks import _ls_write
        if event in ("resolved", "answered", "clear", "done"):
            stored = _ls_write("clear_session_attention",
                               session_id=sid, agent_type=runtime)
            return jsonify({"ok": True, "state": "cleared",
                            "stored": bool(stored)})
        stored = _ls_write("set_session_attention", session_id=sid,
                           agent_type=runtime, state="waiting_approval",
                           signal="hook",
                           tool=_first(body, _TOOL_KEYS)[:80] or None)
        return jsonify({"ok": True, "state": "waiting",
                        "stored": bool(stored)})
    except Exception as e:  # noqa: BLE001
        # Fail open, loudly in the log and quietly on the wire. A hook that
        # 500s is a hook that might make someone's agent hesitate.
        log.warning("attention hook failed: %s", e)
        return jsonify({"ok": False}), 200


@bp_attention.route("/api/attention", methods=["GET"])
def api_attention():
    """Sessions blocked on a human, newest signal first.

    Query params: ``runtime`` scopes to one adapter (the dashboard's runtime
    switcher passes it) so a filtered view never shows node-wide numbers.
    """
    try:
        return jsonify(build_attention(request.args.get("runtime", "")))
    except Exception as e:  # noqa: BLE001
        log.warning("attention: build failed: %s", e)
        # Degrade to "can't tell", never to a confident empty list.
        return jsonify({
            "items": [], "waiting": 0, "working": 0, "fresh": False,
            "reason": "error", "daemon_age_seconds": -1,
            "runtimes_without_approval": [],
        })
