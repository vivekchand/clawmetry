"""
routes/quality.py — the Quality tab endpoint.

One endpoint, one question: "is my agent doing good work?" — answered with
evidence the user can inspect, or not answered at all.

Rewritten 2026-08-15 after an audit found the previous implementation
fabricating both halves of its answer:

  * **The runtime label was a loop variable.** It swept 17 hardcoded
    ``agent_type`` values and stamped each returned row with whichever one the
    loop was on. Since ``upsert_sessions`` hardcodes ``agent_type="openclaw"``
    for every row, only the openclaw pass ever returned anything — so every
    session displayed "openclaw" regardless of runtime, and the other 16
    iterations were dead code. Fixed by scoping on the session-id prefix and
    reading the true label from ``metadata.runtime``.

  * **The verdict was uncorrelated with reality.** Grading ran off a single
    text-similarity heuristic that was structurally blind to family-runtime
    tool calls. Fixed by ``clawmetry.quality_signals``, where no verdict can
    exist without exhibits.

Performance (FLYWHEEL §"Performance is a feature"): grading every session by
replaying its events would be tens of thousands of rows per request. Instead
this runs two tiers — a cheap screen over the per-session tool health the
ingest path already persisted, then a bounded deep scan that reads events only
for the sessions that could actually be shown. The payload reports both counts
so a capped scan is never mistaken for full coverage.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

bp_quality = Blueprint("quality", __name__)

# How many sessions get their events replayed for evidence. Ordered by cost
# desc, so the deep scan always covers what the tab ranks highest. Reported in
# the payload as ``deep_scanned`` — no silent caps.
DEEP_SCAN_LIMIT = 40

# Events read per session during the deep scan. Generous enough to cover a
# long coding session end to end; the old classifier's 200-event tail was a
# root cause (it never saw the 266 tool calls in an 824-event session).
EVENTS_PER_SESSION = 4000


def _store_via_daemon_or_direct(method_name: str, **kwargs):
    """Daemon HTTP proxy first (it owns the writer lock), direct read-only
    DuckDB second, None on miss. Never opens a writer handle from here — a
    cached read-only handle bricks the daemon's writes (the #1771 lock trap).
    """
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _parse_window(raw: str, default_hours: int = 168) -> int:
    """Human-readable window → hours. 1d, 6h, 7d, 30m all work.
    Bounded to [1, 30*24]. Defaults to 7d (the report-card cadence)."""
    raw = (raw or "").strip().lower()
    if not raw:
        return default_hours
    try:
        if raw.endswith("d"):
            hours = int(float(raw[:-1]) * 24)
        elif raw.endswith("h"):
            hours = int(float(raw[:-1]))
        elif raw.endswith("m"):
            hours = max(1, int(float(raw[:-1]) // 60))
        else:
            hours = int(float(raw))
    except (TypeError, ValueError):
        hours = default_hours
    return max(1, min(24 * 30, hours))


def _iso_cutoff(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def compose_report_card(
    rows: list,
    prior_rows: list,
    hist_rows: list,
    *,
    window_hours: int = 168,
    runtime: str | None = None,
    assessments: dict | None = None,
    prior_assessments: dict | None = None,
) -> dict:
    """Build the Quality payload from rows already read out of the store.

    Split out of the request handler so the sync daemon can build the SAME
    payload for the cloud snapshot without re-querying per runtime (founder
    live-hit 2026-08-22: the hosted Quality tab said "Nothing to grade yet"
    for a machine showing an A and 119 graded runs locally — the hosted
    container answered from its own empty DuckDB, because nothing ever put
    quality in the snapshot).

    Taking rows as arguments rather than a fetch callable is deliberate: the
    daemon reads the node's sessions ONCE and groups them in Python, so
    emitting a card per runtime costs no extra queries.
    """
    from clawmetry import quality as _q
    from clawmetry import quality_thresholds as _qt

    by_runtime_hist: dict = {}
    for h in hist_rows or []:
        by_runtime_hist.setdefault(h.get("runtime") or "openclaw", []).append(h)
    thresholds = _qt.calibrate_all(by_runtime_hist)

    # Pre-computed assessments are how the daemon emits a card PER RUNTIME
    # without paying for a deep scan per runtime: it assesses the node's rows
    # once and hands the same map to every card, which then reads only the
    # sessions it contains. Passing none keeps the request-path behaviour.
    if assessments is None:
        assessments = _assess_rows(rows, thresholds)
    if prior_assessments is None:
        prior_assessments = _assess_rows(prior_rows or [], thresholds, deep_limit=0)

    payload = _q.compute_report_card(
        rows, assessments,
        prior_rows=prior_rows or [], prior_assessments=prior_assessments,
    )
    payload["window_hours"] = window_hours
    payload["runtime"] = runtime or "all"
    payload["week"] = _bucket_week(rows, assessments, window_hours)
    payload["judge_key_set"] = _judge_key_present()
    payload["thresholds"] = {
        rt: {k: v for k, v in t.items() if not k.startswith("_")}
            | {"source": t.get("_source", "")}
        for rt, t in thresholds.items()
    }
    payload["coverage"] = {
        "sessions":     len(rows),
        "deep_scanned": sum(1 for a in assessments.values() if a.get("_deep")),
        "screened":     sum(1 for a in assessments.values() if not a.get("_deep")),
        "deep_scan_limit": DEEP_SCAN_LIMIT,
        "note": (
            "Deep scan replays a session's events to collect evidence. "
            "Sessions past the limit are screened on their recorded tool "
            "health only and are never reported as rough without evidence."
        ),
    }
    payload["benign_filter"] = _benign_filter_state()
    payload["store_available"] = True
    return payload


def unavailable_report_card(window_hours: int = 168, runtime: str | None = None) -> dict:
    """The honest answer when this process cannot see the run history.

    Never an empty grade: "nothing to grade" and "I cannot see your machine
    from here" look identical on screen and mean opposite things. The hosted
    dashboard hit exactly that — it has a DuckDB file, it is simply empty, so
    the store answered [] and the tab reported a working machine as having
    produced nothing.
    """
    from clawmetry import quality as _q

    payload = _q.compute_report_card([], {})
    payload.update({
        "window_hours": window_hours,
        "runtime": runtime or "all",
        "store_available": False,
        "headline": "Quality is graded on your own machine.",
        "subline": (
            "This view reads the run history stored locally by the "
            "collector, which isn't reachable from here right now. "
            "Open ClawMetry on the machine your agents run on, or start "
            "the collector there, and the grade appears."
        ),
    })
    return payload


@bp_quality.route("/api/quality/report-card", methods=["GET"])
def quality_report_card():
    """Everything the Quality tab renders, in one fetch.

    ``?window=7d`` (default), ``?runtime=<id>`` (optional scope). No auth gate
    — this is the free-tier home for the "is my agent OK?" answer, same
    rationale as /api/evaluators and /api/evals/metrics.
    """
    window_hours = _parse_window(request.args.get("window", "7d"))
    runtime = (request.args.get("runtime") or "").strip() or None
    if runtime == "all":
        runtime = None

    # The hosted dashboard has no run history of its own — it ships with an
    # EMPTY DuckDB, which answers queries rather than failing them. Reading it
    # here produced "Nothing to grade yet" for machines that were grading
    # fine, so the hosted process refuses to answer from it at all. The real
    # grade reaches the cloud through the daemon's encrypted snapshot; when
    # that slice is missing (older daemon) this honest message is what shows.
    if os.environ.get("CLAWMETRY_CLOUD", "").strip():
        return jsonify(unavailable_report_card(window_hours, runtime))

    since = _iso_cutoff(window_hours)
    prior_since = _iso_cutoff(window_hours * 2)

    raw_rows = _store_via_daemon_or_direct(
        "query_quality_sessions",
        runtime=runtime, since=since, limit=400,
    )
    # None means the store could not be reached at all; [] means it answered
    # and there is nothing there. Collapsing the two would tell a user
    # "nothing to grade yet" about a machine that is in fact working fine.
    if raw_rows is None:
        return jsonify(unavailable_report_card(window_hours, runtime))

    prior_rows = _store_via_daemon_or_direct(
        "query_quality_sessions",
        runtime=runtime, since=prior_since, until=since, limit=400,
    ) or []
    # Calibrate per runtime off a 30-day history of the SAME runtime, so
    # "rough" means unusual for this runtime on this install.
    hist = _store_via_daemon_or_direct(
        "query_quality_sessions",
        runtime=runtime, since=_iso_cutoff(24 * 30), limit=1500,
    ) or []
    return jsonify(compose_report_card(
        raw_rows, prior_rows, hist,
        window_hours=window_hours, runtime=runtime,
    ))


def _assess_rows(
    rows: list[dict],
    thresholds: dict[str, dict],
    *,
    deep_limit: int = DEEP_SCAN_LIMIT,
) -> dict[str, dict]:
    """Assessment per session, read from what the daemon already persisted.

    The daemon grades each session at ingest (``sync.py:_session_quality``)
    off the same events it is about to write, and stores the verdicts in
    ``sessions.metadata.quality``. So the normal path here is a dict lookup —
    no event replay, no request storm.

    The fallback exists for one real case: a session ingested before this
    version shipped, or an install whose daemon has not yet re-swept. Those
    get an on-demand assessment, bounded by ``deep_limit`` and ordered by cost
    so the sessions the tab actually ranks are the ones we spend reads on.

    A session we could neither read nor replay is reported ``measurable:
    false`` — never as a pass. And a session with no evidence can never carry
    a verdict, because ``Verdict`` refuses to exist without exhibits. The cap
    degrades coverage, never honesty.
    """
    from clawmetry.quality_signals import assess_session

    out: dict[str, dict] = {}
    replayed = 0
    # rows arrive cost-desc from the store, so the head is what the tab ranks.
    for r in rows:
        sid = str(r.get("session_id") or "")
        if not sid:
            continue
        rt = r.get("runtime") or "openclaw"

        stored = (r.get("metadata") or {}).get("quality")
        if isinstance(stored, dict) and "measurable" in stored:
            d = dict(stored)
            d["_deep"] = True
            d.setdefault("runtime", rt)
            out[sid] = d
            continue

        if replayed >= deep_limit:
            out[sid] = {
                "session_id": sid, "runtime": rt, "measurable": False,
                "reason": "Not graded yet — the collector will pick this up.",
                "verdicts": [], "_deep": False,
            }
            continue

        replayed += 1
        th = thresholds.get(rt) or thresholds.get("openclaw") or {}
        events = _store_via_daemon_or_direct(
            "query_events", session_id=sid, limit=EVENTS_PER_SESSION,
        ) or []
        try:
            d = assess_session(events, runtime=rt, session_id=sid,
                               thresholds=th).as_dict()
        except Exception:
            d = {"session_id": sid, "runtime": rt, "measurable": False,
                 "reason": "Could not read this session's events.",
                 "verdicts": []}
        d["_deep"] = True
        out[sid] = d
    return out


def _bucket_week(rows, assessments, window_hours: int) -> list[dict]:
    """Per-day dots. A day with no MEASURABLE session shows no grade rather
    than an invented one."""
    from collections import defaultdict
    from clawmetry.quality import grade_for, session_score

    days = min(7, max(1, window_hours // 24 or 1))
    now = datetime.now(timezone.utc).date()
    buckets: dict[str, list[float]] = defaultdict(list)

    for r in rows:
        ts = (r.get("last_active_at") or r.get("ended_at")
              or r.get("started_at") or "")
        if not ts:
            continue
        try:
            d = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            continue
        a = assessments.get(str(r.get("session_id") or "")) or {}
        s = session_score(a)
        if s is None:
            continue
        buckets[d.isoformat()].append(s)

    out: list[dict] = []
    for i in range(days - 1, -1, -1):
        d = now - timedelta(days=i)
        scores = buckets.get(d.isoformat(), [])
        avg = sum(scores) / len(scores) if scores else None
        out.append({
            "date":  d.isoformat(),
            "label": ("Today" if i == 0
                      else ("Yesterday" if i == 1 else d.strftime("%a"))),
            "grade": grade_for(avg) if avg is not None else "—",
            "runs":  len(scores),
        })
    return out


@bp_quality.route("/api/quality/capabilities", methods=["GET"])
def quality_capabilities():
    """What each runtime on this install can actually be graded on.

    Phase 0 of the rebuild, kept as a live endpoint rather than a one-off
    research artifact: capability is OBSERVED from the events a runtime
    really emitted here, so it stays true as adapters change. A runtime we
    have no data for reports ``observed: false`` instead of a guess.
    """
    from clawmetry.quality_signals import (
        SIGNALS, normalize_events, probe_capabilities,
    )

    rows = _store_via_daemon_or_direct(
        "query_quality_sessions", since=_iso_cutoff(24 * 30), limit=600,
    ) or []
    by_runtime: dict[str, list[dict]] = {}
    for r in rows:
        by_runtime.setdefault(r.get("runtime") or "openclaw", []).append(r)

    out: list[dict] = []
    for rt, rrows in sorted(by_runtime.items()):
        # One representative session per runtime — the most active one, so the
        # probe sees the richest event vocabulary that runtime produces.
        best = max(rrows, key=lambda r: float(r.get("total_tokens") or 0))
        events = _store_via_daemon_or_direct(
            "query_events", session_id=best.get("session_id"), limit=1500,
        ) or []
        caps = probe_capabilities(normalize_events(events), runtime=rt)
        d = caps.as_dict()
        d["observed"] = True
        d["sessions_seen"] = len(rrows)
        d["unsupported_signals"] = sorted(
            n for n in SIGNALS if n not in d["supported_signals"]
        )
        out.append(d)

    return jsonify({
        "runtimes": out,
        "signals": {
            n: {"label": s.label, "min_sample": s.min_sample}
            for n, s in SIGNALS.items()
        },
        "note": (
            "Capabilities are observed from events this install actually "
            "recorded. A runtime with no sessions here is absent from this "
            "list rather than assumed."
        ),
    })


def _benign_filter_state() -> dict:
    """Whether benign tool errors are being filtered out of the error rate.

    ``clawmetry.error_signal`` is an OSS shim: without clawmetry-pro it
    reports nothing benign, so an OSS install computes a HIGHER error rate
    than a Pro install on identical data. Surfacing which filter produced the
    number keeps the two from looking like a contradiction.
    """
    try:
        from clawmetry import error_signal as _es
        active = _es.is_benign_tool_error(
            "<tool_use_error>File has not been read yet. "
            "Read it first before writing to it.</tool_use_error>"
        )
    except Exception:
        active = False
    return {
        "active": bool(active),
        "label": ("Recoverable tool errors (like a re-read guard) are "
                  "excluded from these rates."
                  if active else
                  "All tool errors are counted, including recoverable ones."),
    }


@bp_quality.route("/api/quality/checks", methods=["POST"])
def quality_checks_save():
    """Save a check built from a real rough run.

    v1 scope: validate + persist to ``~/.clawmetry/quality_checks.jsonl``
    (append-only, chmod 600) and return ``deferred_enforcement: true``. The
    runner that acts on saved checks lands separately; the UI says so.
    """
    body = request.get_json(silent=True) or {}
    fail_when = (body.get("fail_when") or "").strip()
    name = (body.get("name") or "").strip()
    session_id = (body.get("session_id") or "").strip()
    if not fail_when:
        return jsonify({"ok": False, "error": "fail_when required"}), 400
    if not name:
        name = " ".join(fail_when.split()[:4]).rstrip(",.") or "Untitled check"

    import hashlib
    ts = datetime.now(timezone.utc).isoformat()
    stable_id = hashlib.sha256(
        (name + "|" + fail_when).encode("utf-8")
    ).hexdigest()[:12]

    record = {
        "id":                   stable_id,
        "name":                 name[:120],
        "fail_when":            fail_when[:500],
        "source_session_id":    session_id[:200],
        "created_at":           ts,
        "deferred_enforcement": True,
    }
    try:
        _append_check_record(record)
    except Exception as e:
        return jsonify({"ok": False, "error": f"persist failed: {e}"}), 500
    return jsonify({
        "ok":                   True,
        "id":                   stable_id,
        "deferred_enforcement": True,
        "message": "Saved locally. Live enforcement lands in the next release.",
    })


def _append_check_record(record: dict) -> None:
    """chmod-600 append to ~/.clawmetry/quality_checks.jsonl."""
    import json
    import os
    from pathlib import Path
    home = Path(os.environ.get("HOME") or os.path.expanduser("~"))
    d = home / ".clawmetry"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "quality_checks.jsonl"
    exists = p.exists()
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
    if not exists:
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass


def _judge_key_present() -> bool:
    """Cheap check for judge-key presence so the footer nudge can hide."""
    try:
        from clawmetry import eval_runner
        keys = eval_runner.judge_keys_present() or {}
        return any(bool(v) for v in keys.values())
    except Exception:
        return False
