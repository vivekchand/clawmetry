"""routes/attention.py — "which of my agents needs me right now".

The one question the dashboard exists to answer before any chart. Serves the
attention state the daemon computed and persisted onto the session rows
(``clawmetry/sync.py::_refresh_attention_cache`` ->
``local_store.apply_session_attention``), so this handler does ONE read and
never runs detection itself.

THE HONESTY CONTRACT (the reason this module is more than a filter):

    signal="hook"      the runtime told us it opened a prompt -> "Waiting for you"
    signal="inferred"  a tool call has hung with no result   -> "Looks like it's waiting"
    daemon stale       nobody has computed this recently      -> "Can't tell right now"

Those are three different sentences and the UI renders all three. An empty
list from a wedged detector must NEVER read as "nothing needs you" -- a badge
that cries wolf, or a calm all-clear that is wrong, teaches people to stop
trusting the list, and an ignored list is worth less than no list at all.

Freshness is derived from the daemon's own heartbeat rather than a separate
attention timestamp, because the honest question is "is the thing that
computes this alive?" -- and if the daemon is down, we genuinely cannot tell.

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

#: A daemon quieter than this is treated as "no signal", never "all clear".
_DAEMON_FRESH_SECONDS = 300

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


def _daemon_age_seconds() -> int:
    """Seconds since the daemon last checked in; -1 when unknown."""
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
            # Anything still live but not blocked counts as quietly working —
            # the number that makes "nothing needs you" reassuring instead of
            # ambiguous (nothing waiting because nothing is running at all).
            if not r.get("ended_at") and str(
                r.get("status") or "").lower() not in (
                    "ended", "completed", "stopped", "failed"):
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
    items.sort(key=lambda i: (i["signal"] != "hook", -i["waiting_seconds"]))

    age = _daemon_age_seconds()
    fresh = age >= 0 and age <= _DAEMON_FRESH_SECONDS
    return {
        "items":   items if fresh else [],
        "waiting": len(items) if fresh else 0,
        "working": working,
        "fresh":   fresh,
        "reason":  "" if fresh else ("stale" if age >= 0 else "no_heartbeat"),
        "daemon_age_seconds": age,
        # Surfaced so the UI can say "Pi doesn't ask" rather than implying
        # we checked it and found nothing.
        "runtimes_without_approval": sorted(
            seen_runtimes & RUNTIMES_WITHOUT_APPROVAL),
    }


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
