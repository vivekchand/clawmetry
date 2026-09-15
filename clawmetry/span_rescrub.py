"""Operator-run rescrub of stored spans (REQ-OBS-OTG-001, AC-OBS-OTG-001.10).

Spans written before 0.12.878 were stored exactly as received: prompts, tool
arguments, attributes and exception events with any secret or personal data
still in them. Scrubbing now happens on the write path, and hashes stored
before it existed still match, so an upgrade does not rewrite those rows.
That is deliberate: nothing rewrites stored history on its own.

``clawmetry maintenance rescrub-spans`` is the explicit way to change that.

* **Dry run by default.** It pages through the spans table, runs today's
  span scrubber on each stored row, and reports how many would change and how
  many would have a value withheld. Nothing is written.
* **``--apply`` rewrites content columns only**: ``name``, ``status``,
  ``status_message``, ``input``, ``output``, ``attributes``, ``events``,
  ``links``. Ids, times, cost, tokens, model, tool name and the stored content
  hash are left alone, so a span a runtime re-sends unchanged is still
  skipped rather than rewritten.
* **Refuses with redaction off** (``CLAWMETRY_REDACT=0``): there is nothing to
  scrub with.
* **Says what it cannot reach.** Copies already sent in an encrypted cloud
  snapshot, forwarded to a SIEM or exported elsewhere are not changed.
* **Does not apply the content profile** (clawmetry/otlp_content.py): a
  stored span cannot be told apart from one a runtime adapter reconstructed,
  so withholding content retroactively could strip data the operator did not
  ask to lose.

It runs through the sync daemon when one holds the store's writer lock (the
store method ``rescrub_spans``, allowlisted in ``routes/local_query.py``) and
against the store directly when no daemon is running.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

log = logging.getLogger("clawmetry.span_rescrub")

# Positions in ``local_store._span_row``'s output.
_CONTENT_COLUMNS = (
    ("name", 8), ("status_message", 11), ("status", 12), ("input", 23),
    ("output", 24), ("attributes", 25), ("events", 26), ("links", 27),
)
_SELECT_COLS = (
    "span_id", "trace_id", "parent_span_id", "agent_type", "agent_id",
    "node_id", "session_id", "service_name", "name", "kind", "status_code",
    "status_message", "status", "start_ts", "end_ts", "duration_ms",
    "duration_ns", "model", "tool_name", "cost_usd", "token_count",
    "tokens_input", "tokens_output", "input", "output", "attributes",
    "events", "links",
)
_BLOB_COLS = ("input", "output", "attributes", "events", "links")
MAX_BATCH = 1000

REFUSED_REDACTION_OFF = "redaction_disabled"


def rescrub_batch(store, *, apply: bool = False, after: str = "",
                  limit: int = 200) -> dict:
    """Scrub one page of stored spans (``span_id > after``). Never raises.

    Returns ``{"scanned", "changed", "withheld", "applied", "next_after",
    "done"}``; ``changed`` counts spans that differ from their scrubbed form
    (rewritten only when ``applied``).
    """
    from clawmetry import local_store as _ls
    from clawmetry import redaction as _r

    out = {"scanned": 0, "changed": 0, "withheld": 0, "applied": bool(apply),
           "next_after": str(after or ""), "done": True}
    if _r._disabled():
        out.update(error=REFUSED_REDACTION_OFF, applied=False)
        return out
    try:
        limit = max(1, min(int(limit or 200), MAX_BATCH))
    except (TypeError, ValueError):
        limit = 200
    rows = store._fetch(
        "SELECT " + ", ".join(_SELECT_COLS) + " FROM spans "
        "WHERE span_id > ? ORDER BY span_id LIMIT ?",
        [str(after or ""), limit],
    )
    updates: list = []
    for row in rows:
        span = dict(zip(_SELECT_COLS, row))
        for col in _BLOB_COLS:
            span[col] = _ls._from_blob(span[col])
        out["scanned"] += 1
        out["next_after"] = str(span["span_id"])
        try:
            before = _ls._span_row(span)
            scrubbed = _r.redact_span(span)
            after_row = _ls._span_row(scrubbed)
        except Exception:
            log.warning("rescrub: span %s could not be scrubbed; left as stored",
                        str(span.get("span_id"))[:64], exc_info=True)
            continue
        if all(before[i] == after_row[i] for _, i in _CONTENT_COLUMNS):
            continue
        out["changed"] += 1
        attrs = scrubbed.get("attributes")
        if isinstance(attrs, dict) and _r.REDACTION_MARKER_KEY in attrs:
            out["withheld"] += 1
        updates.append([after_row[i] for _, i in _CONTENT_COLUMNS] + [before[0]])
    out["done"] = len(rows) < limit
    if apply and updates:
        sql = ("UPDATE spans SET " + ", ".join(c + " = ?" for c, _ in _CONTENT_COLUMNS)
               + " WHERE span_id = ?")
        with store._write_lock:
            with _ls._txn(store._conn):
                store._conn.executemany(sql, updates)
        log.warning("rescrub: operator rewrote the content of %d stored spans", len(updates))
    return out


def run(call: Callable[..., Any], *, apply: bool = False, batch: int = 200,
        max_steps: Optional[int] = None) -> dict:
    """Page through every stored span with ``call(apply=, after=, limit=)``."""
    totals = {"scanned": 0, "changed": 0, "withheld": 0, "applied": bool(apply)}
    after = ""
    steps = 0
    while True:
        res = call(apply=bool(apply), after=after, limit=int(batch))
        if not isinstance(res, dict):
            totals["error"] = "store_unavailable"
            return totals
        if res.get("error"):
            totals["error"] = res["error"]
            totals["applied"] = False
            return totals
        for key in ("scanned", "changed", "withheld"):
            totals[key] += int(res.get(key) or 0)
        steps += 1
        nxt = str(res.get("next_after") or "")
        if res.get("done") or not nxt or nxt == after:
            return totals
        if max_steps is not None and steps >= max_steps:
            totals["error"] = "stopped_early"
            return totals
        after = nxt


def summary(totals: dict) -> str:
    """What happened, in plain words. No em dashes: users read this."""
    err = totals.get("error")
    if err == REFUSED_REDACTION_OFF:
        return ("Redaction is turned off (CLAWMETRY_REDACT=0), so there is nothing "
                "to rescrub with. Nothing was changed.")
    if err == "store_unavailable":
        return ("Could not reach the store. If the sync daemon is running an older "
                "version, update it and try again. Nothing was changed.")
    if err:
        return "Stopped before finishing (%s). Nothing further was changed." % err
    scanned = "{:,}".format(totals["scanned"])
    changed = "{:,}".format(totals["changed"])
    withheld = totals["withheld"]
    held = (" (%s with a value withheld because it could not be scanned)" % "{:,}".format(withheld)
            if withheld else "")
    if not totals.get("applied"):
        if not totals["changed"]:
            return ("Dry run: %s stored spans scanned, none would change. "
                    "Nothing was changed." % scanned)
        return ("Dry run: %s stored spans scanned, %s would be rescrubbed%s. Nothing "
                "was changed. Run again with --apply to rewrite them." % (scanned, changed, held))
    return ("Rescrubbed %s of %s stored spans%s. Only content fields changed. Copies "
            "already sent in a cloud snapshot, forwarded or exported are not "
            "affected." % (changed, scanned, held))


def _caller() -> Callable[..., Any]:
    """Through the daemon when it holds the store, else the store directly."""
    def _direct(**kw):
        from clawmetry import local_store as _ls
        return _ls.get_store().rescrub_spans(**kw)

    try:
        from routes.local_query import PROXY_UNAVAILABLE, local_store_call_via_daemon
    except Exception:
        return _direct

    state = {"via": None}

    def _call(**kw):
        if state["via"] == "direct":
            return _direct(**kw)
        res = local_store_call_via_daemon("rescrub_spans", **kw)
        if res is PROXY_UNAVAILABLE:
            if state["via"] == "daemon":
                return None
            try:
                res = _direct(**kw)
            except Exception as exc:  # the daemon holds the lock but did not answer
                log.debug("rescrub: direct store open failed: %s", exc)
                return None
            state["via"] = "direct"
            return res
        state["via"] = "daemon"
        return res

    return _call


def cmd_maintenance(args) -> int:
    """``clawmetry maintenance <subcommand>``. Returns an exit code."""
    sub = getattr(args, "maintenance_cmd", None)
    if sub != "rescrub-spans":
        print("Usage: clawmetry maintenance rescrub-spans [--apply] [--batch N] [--json]")
        return 2
    totals = run(_caller(), apply=bool(getattr(args, "apply", False)),
                 batch=int(getattr(args, "batch", 200) or 200))
    if getattr(args, "as_json", False):
        print(json.dumps(dict(totals, message=summary(totals)), indent=2, sort_keys=True))
    else:
        print(summary(totals))
    return 1 if totals.get("error") else 0
