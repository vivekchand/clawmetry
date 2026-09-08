"""Signal shifts (WO-62): notice when a behaviour-signal rate moves, explain
what moved it, and open an issue the operator can resolve or ignore.

Behaviour Signals (:mod:`clawmetry.behaviour_signals`) produce rates: what
share of user turns read as frustration, what share of assistant turns read
as a refusal, and so on, per runtime. This module reads those rates and
asks one question per (signal, runtime): **is the last 24 hours outside the
band this runtime's own 28-day history taught us?** When it is, an issue
row opens in ``signal_issues`` carrying the rate before, the rate during,
the sample sizes and a ranked breakdown (model, runtime version, tool,
repository) of where the shift concentrated. No model reads anything here.

The band is learned the way Guard thresholds are
(:mod:`clawmetry.detector_calibration`): ``mean + k * spread`` over the
daily history rates, then clamped. The floor keeps a flat history with zero
spread from firing on noise (a threshold never sits closer than
``SHIFT_MIN_DELTA`` above the mean); the ceiling keeps a wildly noisy history
from pushing the threshold so high that nothing ever fires. Every issue
records which of the three (``learned`` / ``floor`` / ``ceiling``) produced
the threshold it crossed.

Minimum samples apply on both sides. A solo developer with twenty turns a
day may never see an issue, and the surface says so rather than inventing
one from three turns.

Issue lifecycle (one open issue per (signal, runtime)):

* no row, shift            -> ``opened``      (delivered)
* open row, still shifting -> ``updated``     (rates refreshed, silent)
* resolved row, shifts     -> ``reopened``    (delivered, ``reopen_count`` + 1),
                              but only once the resolved window has fully
                              aged out, so resolving a live shift does not
                              reopen it on the next tick
* ignored row, shifts      -> ``ignored``     (silent until the operator
                              reopens it by hand)

Delivery goes through the daemon's existing local alert path: the issue
becomes a match for the built-in rule kind ``signal_shift`` and rides the
same banner row + generic webhook + cooldown that user rules use. The
payload names the signal, the runtime, the rates, the sample sizes and the
top breakdown line. It never carries matched text: nothing here has any.

Entry points:

    detect_shift(short, history, ...)      -> dict | None    (pure)
    rank_breakdown(rows, cwd_of, tool_of)  -> dict           (pure)
    issue_headline(issue)                  -> str            (pure)
    shift_alert_match(issue, ...)          -> dict           (pure)
    run_shift_tick(store)                  -> dict           (daemon)
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import math
import os
import time
from collections.abc import Iterable
from typing import Any

log = logging.getLogger("clawmetry.signal_shifts")

__all__ = [
    "learned_band", "detect_shift", "rank_breakdown", "issue_headline",
    "shift_alert_match", "evaluate_pairs", "run_shift_tick", "build_snapshot_slice",
]

# ── tunables (env-overridable) ──────────────────────────────────────────────
# The short window the rate is compared over, and the history it is compared
# against. History always EXCLUDES the short window.
SHORT_HOURS = int(os.environ.get("CLAWMETRY_SHIFT_SHORT_HOURS", "24"))
HISTORY_DAYS = int(os.environ.get("CLAWMETRY_SHIFT_HISTORY_DAYS", "28"))
# Minimum eligible turns in the short window / in the history before a band
# is allowed to say anything. Both apply; below either the pair is skipped.
MIN_SHORT = int(os.environ.get("CLAWMETRY_SHIFT_MIN_SHORT", "30"))
MIN_HISTORY = int(os.environ.get("CLAWMETRY_SHIFT_MIN_HISTORY", "200"))
# How many spreads above the history mean counts as a shift.
K = float(os.environ.get("CLAWMETRY_SHIFT_K", "2.0"))
# Clamps on the learned threshold (see the module docstring).
SHIFT_MIN_DELTA = float(os.environ.get("CLAWMETRY_SHIFT_MIN_DELTA", "0.02"))
SHIFT_CEIL_RATIO = float(os.environ.get("CLAWMETRY_SHIFT_CEIL_RATIO", "5.0"))
# Delivery cooldown for the built-in ``signal_shift`` rule kind (per signal +
# runtime): a reopen inside this window is recorded but not re-sent.
SHIFT_ALERT_COOLDOWN_SEC = int(os.environ.get("CLAWMETRY_SHIFT_COOLDOWN_SEC", str(6 * 3600)))
# Breakdown: how many values per dimension the issue keeps.
BREAKDOWN_TOP_N = 3
BREAKDOWN_DIMENSIONS = ("model", "runtime_version", "tool", "cwd")

ISSUE_STATUSES = ("open", "resolved", "ignored")

_HOUR_MS = 3600 * 1000
_DAY_MS = 86400 * 1000


# ── band math ───────────────────────────────────────────────────────────────

def _mean_spread(rates: list[float]) -> tuple[float, float]:
    if not rates:
        return 0.0, 0.0
    mean = sum(rates) / len(rates)
    if len(rates) < 2:
        return mean, 0.0
    var = sum((r - mean) ** 2 for r in rates) / len(rates)
    return mean, math.sqrt(max(var, 0.0))


def learned_band(history: Iterable[dict], *, k: float | None = None,
                 min_delta: float | None = None,
                 ceil_ratio: float | None = None) -> dict:
    """The upper band for a (signal, runtime) from its daily history.

    ``history`` rows are ``{day, matches, turns}``; days with no eligible
    turn carry no information and are skipped. The history mean is the
    pooled rate (total matches over total turns) so a quiet day does not
    weigh as much as a busy one; the spread is over the per-day rates,
    which is what "how much does this runtime wobble day to day" means.

    Returns ``{mean, spread, threshold, raw, source, n_turns, n_days}``
    where ``source`` says which clamp (if any) set the threshold.
    """
    k = K if k is None else float(k)
    min_delta = SHIFT_MIN_DELTA if min_delta is None else float(min_delta)
    ceil_ratio = SHIFT_CEIL_RATIO if ceil_ratio is None else float(ceil_ratio)
    day_rates: list[float] = []
    tot_m = 0
    tot_t = 0
    for row in history or []:
        try:
            t = int(row.get("turns") or 0)
            m = int(row.get("matches") or 0)
        except (AttributeError, TypeError, ValueError):
            continue
        if t <= 0:
            continue
        tot_t += t
        tot_m += min(m, t)
        day_rates.append(min(m, t) / t)
    mean = (tot_m / tot_t) if tot_t else 0.0
    _, spread = _mean_spread(day_rates)
    raw = mean + k * spread
    lo = mean + min_delta
    hi = max(lo, mean * ceil_ratio)
    if raw < lo:
        threshold, source = lo, "floor"
    elif raw > hi:
        threshold, source = hi, "ceiling"
    else:
        threshold, source = raw, "learned"
    return {
        "mean": round(mean, 6), "spread": round(spread, 6),
        "threshold": round(min(threshold, 1.0), 6), "raw": round(raw, 6),
        "source": source, "n_turns": tot_t, "n_days": len(day_rates),
    }


def detect_shift(short: dict, history: Iterable[dict], *,
                 k: float | None = None,
                 min_short: int | None = None,
                 min_history: int | None = None,
                 min_delta: float | None = None,
                 ceil_ratio: float | None = None) -> dict | None:
    """``None`` when the short window is inside the band or either side is
    under its minimum sample; otherwise the shift record::

        {rate_before, rate_during, n_before, n_during, threshold,
         threshold_source, mean, spread, k}

    ``short`` is ``{matches, turns}`` for the last ``SHORT_HOURS``.
    """
    min_short = MIN_SHORT if min_short is None else int(min_short)
    min_history = MIN_HISTORY if min_history is None else int(min_history)
    try:
        n_during = int((short or {}).get("turns") or 0)
        m_during = int((short or {}).get("matches") or 0)
    except (AttributeError, TypeError, ValueError):
        return None
    if n_during < max(1, min_short):
        return None
    band = learned_band(history, k=k, min_delta=min_delta, ceil_ratio=ceil_ratio)
    if band["n_turns"] < max(1, min_history):
        return None
    rate_during = min(m_during, n_during) / n_during
    if rate_during <= band["threshold"]:
        return None
    return {
        "rate_before": band["mean"], "rate_during": round(rate_during, 6),
        "n_before": band["n_turns"], "n_during": n_during,
        "m_during": m_during,
        "threshold": band["threshold"], "threshold_source": band["source"],
        "mean": band["mean"], "spread": band["spread"],
        "k": K if k is None else float(k),
    }


# ── breakdown ───────────────────────────────────────────────────────────────

def _basename(path: str | None) -> str:
    p = str(path or "").replace("\\", "/").rstrip("/")
    if not p:
        return ""
    return p.rsplit("/", 1)[-1][:64]


def rank_breakdown(turn_rows: Iterable[dict], match_rows: Iterable[dict], *,
                   cwd_of: dict[str, str] | None = None,
                   tool_of: dict[str, str] | None = None,
                   top_n: int = BREAKDOWN_TOP_N,
                   threshold: float | None = None,
                   threshold_source: str | None = None) -> dict:
    """Rank, per dimension, which value explains most of the shift.

    ``turn_rows`` / ``match_rows`` are per-session counts for the signal's
    side: ``{session_id, model, runtime_version, period, n}`` with ``period``
    ``"during"`` or ``"before"``. ``cwd_of`` and ``tool_of`` map a session
    to its working directory and its most-used tool (both optional).

    A value's *excess* is the matches it produced during the shift beyond
    what its own before-rate predicts for its during-turns; its *share* is
    that excess over the total excess. A value that got worse explains the
    shift; a value that merely got busier does not. Shares are clamped to
    [0, 1] and the per-dimension lists are sorted by share.

    Returns ``{"model": [...], "runtime_version": [...], "tool": [...],
    "cwd": [...], "top": {...} | None}`` where each entry is
    ``{value, rate_before, rate_during, n_before, n_during, share}``. When
    the shift verdict's ``threshold`` and ``threshold_source`` (learned /
    floor / ceiling) are given they are carried in the result too, so the
    stored ``breakdown_json`` records which clamp the issue crossed.
    """
    cwd_of = cwd_of or {}
    tool_of = tool_of or {}

    def _key(row: dict, dim: str) -> str:
        sid = str(row.get("session_id") or "")
        if dim == "model":
            return str(row.get("model") or "unknown")[:96]
        if dim == "runtime_version":
            return str(row.get("runtime_version") or "unknown")[:32]
        if dim == "tool":
            return str(tool_of.get(sid) or "unknown")[:64]
        if dim == "cwd":
            return _basename(cwd_of.get(sid)) or "unknown"
        return "unknown"

    def _acc(rows: Iterable[dict], dim: str) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for r in rows or []:
            if not isinstance(r, dict):
                continue
            period = "during" if str(r.get("period") or "") == "during" else "before"
            try:
                n = int(r.get("n") or 0)
            except (TypeError, ValueError):
                continue
            bucket = out.setdefault(_key(r, dim), {"during": 0, "before": 0})
            bucket[period] += n
        return out

    turn_list = [r for r in (turn_rows or []) if isinstance(r, dict)]
    match_list = [r for r in (match_rows or []) if isinstance(r, dict)]
    tot_t_during = sum(int(r.get("n") or 0) for r in turn_list if r.get("period") == "during")
    tot_t_before = sum(int(r.get("n") or 0) for r in turn_list if r.get("period") != "during")
    tot_m_during = sum(int(r.get("n") or 0) for r in match_list if r.get("period") == "during")
    tot_m_before = sum(int(r.get("n") or 0) for r in match_list if r.get("period") != "during")
    rate_before_all = (tot_m_before / tot_t_before) if tot_t_before else 0.0
    total_excess = tot_m_during - rate_before_all * tot_t_during

    result: dict[str, Any] = {}
    best: dict | None = None
    for dim in BREAKDOWN_DIMENSIONS:
        t_by = _acc(turn_list, dim)
        m_by = _acc(match_list, dim)
        entries = []
        for value, t in t_by.items():
            m = m_by.get(value, {"during": 0, "before": 0})
            n_d, n_b = t["during"], t["before"]
            if n_d <= 0:
                continue
            r_d = min(m["during"], n_d) / n_d
            r_b = (min(m["before"], n_b) / n_b) if n_b else rate_before_all
            excess = m["during"] - r_b * n_d
            share = (excess / total_excess) if total_excess > 0 else 0.0
            share = max(0.0, min(1.0, share))
            entries.append({
                "value": value, "rate_before": round(r_b, 4), "rate_during": round(r_d, 4),
                "n_before": n_b, "n_during": n_d, "share": round(share, 4),
            })
        entries.sort(key=lambda e: (-e["share"], -e["n_during"], e["value"]))
        entries = entries[:max(1, top_n)]
        result[dim] = entries
        if entries and entries[0]["value"] != "unknown":
            cand = dict(entries[0], dim=dim)
            if best is None or cand["share"] > best["share"]:
                best = cand
    result["top"] = best
    if threshold is not None:
        result["threshold"] = threshold
    if threshold_source is not None:
        result["threshold_source"] = str(threshold_source)
    return result


# ── plain words ─────────────────────────────────────────────────────────────

_DIM_WORDS = {"model": "on {v}", "runtime_version": "on version {v}",
              "tool": "around the {v} tool", "cwd": "in {v}"}


def _pct(rate: float | None) -> str:
    try:
        return f"{float(rate or 0.0) * 100:.0f}%"
    except (TypeError, ValueError):
        return "0%"


def _since_words(opened_at_ms: int | None, now_ms: int | None = None) -> str:
    try:
        opened = int(opened_at_ms or 0)
    except (TypeError, ValueError):
        opened = 0
    if not opened:
        return "today"
    now = int(now_ms or time.time() * 1000)
    age_days = (now - opened) / _DAY_MS
    if age_days < 1:
        return "today"
    if age_days < 7:
        return "since " + _dt.datetime.fromtimestamp(opened / 1000, tz=_dt.timezone.utc).strftime("%A")
    return "since " + _dt.datetime.fromtimestamp(opened / 1000, tz=_dt.timezone.utc).strftime("%b %d")


def issue_headline(issue: dict, now_ms: int | None = None) -> str:
    """One plain sentence: ``Frustration on Cursor jumped from 4% to 11%
    since Tuesday, mostly on claude-x``. No em dashes; no matched text."""
    from clawmetry import behaviour_signals as _bs
    sig = str(issue.get("signal") or "")
    label = (_bs.SIGNALS.get(sig) or {}).get("label") or sig.replace("_", " ")
    rt = _bs.runtime_label(str(issue.get("agent_type") or ""))
    head = (f"{label} on {rt} jumped from {_pct(issue.get('rate_before'))} "
            f"to {_pct(issue.get('rate_during'))} {_since_words(issue.get('opened_at'), now_ms)}")
    bd = issue.get("breakdown") or {}
    if isinstance(bd, str):
        try:
            bd = json.loads(bd)
        except Exception:  # noqa: BLE001
            bd = {}
    top = bd.get("top") if isinstance(bd, dict) else None
    if isinstance(top, dict) and top.get("value") and top.get("share", 0) >= 0.2:
        tmpl = _DIM_WORDS.get(str(top.get("dim") or ""), "on {v}")
        head += ", mostly " + tmpl.format(v=str(top.get("value"))[:48])
    return head + "."


# ── snapshot slice ─────────────────────────────────────────────────────────

def build_snapshot_slice(store, *, resolved_limit: int = 20) -> dict:
    """``signalIssues`` for ``sync_system_snapshot``: every open issue plus
    the last ``resolved_limit`` resolved ones, each with its plain-words
    headline. No session ids, no text. ``{}`` on any failure."""
    try:
        opened = store.query_signal_issues(status="open", limit=200) or []
        resolved = store.query_signal_issues(status="resolved", limit=resolved_limit) or []
        ignored = store.query_signal_issues(status="ignored", limit=50) or []
        items = []
        for it in list(opened) + list(resolved) + list(ignored):
            if not isinstance(it, dict):
                continue
            it = dict(it)
            it["headline"] = issue_headline(it)
            items.append(it)
        return {"issues": items, "open": len(opened), "resolved": len(resolved),
                "ignored": len(ignored), "generated_at": int(time.time() * 1000)}
    except Exception as e:  # noqa: BLE001
        log.debug("signal shifts: snapshot slice failed: %s", e)
        return {}


# ── alert payload ───────────────────────────────────────────────────────────

SHIFT_RULE_KIND = "signal_shift"


def shift_alert_match(issue: dict, *, node_id: str = "", link: str = "",
                      action: str = "opened") -> dict:
    """The match dict the daemon's local alert path consumes: ``{rule,
    event, summary, metadata}``. ``rule.id`` keys the cooldown per (signal,
    runtime) so a flapping issue is not re-sent every tick."""
    sig = str(issue.get("signal") or "")
    rt = str(issue.get("agent_type") or "")
    bd = issue.get("breakdown") or {}
    if isinstance(bd, str):
        try:
            bd = json.loads(bd)
        except Exception:  # noqa: BLE001
            bd = {}
    top = bd.get("top") if isinstance(bd, dict) else None
    top_line = ""
    if isinstance(top, dict) and top.get("value"):
        top_line = (f"{top.get('dim')}={top.get('value')} explains "
                    f"{_pct(top.get('share'))} of the shift "
                    f"({_pct(top.get('rate_before'))} to {_pct(top.get('rate_during'))})")
    rule = {
        "id": f"builtin:{SHIFT_RULE_KIND}:{sig}:{rt}",
        "name": f"Signal shift: {sig} on {rt}",
        "enabled": True,
        "condition_json": {
            "type": SHIFT_RULE_KIND, "alert_type": SHIFT_RULE_KIND,
            "signal": sig, "runtime": rt,
            "cooldown_sec": SHIFT_ALERT_COOLDOWN_SEC,
            "channels": ["banner", "webhook"],
        },
    }
    summary = issue_headline(issue)
    if action == "reopened":
        summary = "Reopened: " + summary
    return {
        "rule": rule,
        "event": {"id": f"signal_issue:{issue.get('id')}", "type": SHIFT_RULE_KIND},
        "summary": summary,
        "metadata": {
            "kind": SHIFT_RULE_KIND, "action": action,
            "issue_id": issue.get("id"),
            "signal": sig, "runtime": rt, "node_id": node_id,
            "rate_before": issue.get("rate_before"), "rate_during": issue.get("rate_during"),
            "n_before": issue.get("n_before"), "n_during": issue.get("n_during"),
            "reopen_count": issue.get("reopen_count") or 0,
            "top_breakdown": top_line,
            "link": link or "",
        },
    }


# ── daemon tick ─────────────────────────────────────────────────────────────

def dashboard_link(fragment: str = "signals") -> str:
    base = (os.environ.get("CLAWMETRY_DASHBOARD_URL") or "http://localhost:8900").rstrip("/")
    return f"{base}/#{fragment}"


def evaluate_pairs(pairs: Iterable[dict], **kw) -> list[dict]:
    """Pure: ``[{signal, agent_type, node_id, shift}]`` for every pair whose
    short window left its band. ``pairs`` rows are
    ``{signal, agent_type, node_id, short: {matches, turns}, history: [...]}``."""
    out = []
    for p in pairs or []:
        if not isinstance(p, dict):
            continue
        shift = detect_shift(p.get("short") or {}, p.get("history") or [], **kw)
        if shift:
            out.append({"signal": p.get("signal"), "agent_type": p.get("agent_type"),
                        "node_id": p.get("node_id"), "shift": shift})
    return out


def run_shift_tick(store, *, now_ms: int | None = None, deliver=None,
                   node_id: str = "") -> dict:
    """One daemon pass. Reads the per-(signal, runtime) windows from the
    store, opens / updates / reopens issues, and hands each *opened* or
    *reopened* issue to ``deliver(match)`` (the daemon's local alert path).
    Never raises; returns ``{checked, opened, reopened, updated}``."""
    stats = {"checked": 0, "opened": 0, "reopened": 0, "updated": 0, "ignored": 0,
             "none": 0, "errors": 0}
    try:
        now_ms = int(now_ms or time.time() * 1000)
        inputs = store.query_signal_shift_inputs(
            now_ms=now_ms, short_hours=SHORT_HOURS, history_days=HISTORY_DAYS) or {}
        pairs = inputs.get("pairs") or []
        stats["checked"] = len(pairs)
        for hit in evaluate_pairs(pairs):
            sig, rt = str(hit["signal"] or ""), str(hit["agent_type"] or "")
            shift = hit["shift"]
            try:
                rows = store.query_signal_shift_breakdown(
                    signal=sig, runtime=rt, now_ms=now_ms,
                    short_hours=SHORT_HOURS, history_days=HISTORY_DAYS) or {}
                breakdown = rank_breakdown(rows.get("turns") or [], rows.get("matches") or [],
                                           cwd_of=rows.get("cwd") or {},
                                           tool_of=rows.get("tool") or {},
                                           threshold=shift["threshold"],
                                           threshold_source=shift["threshold_source"])
            except Exception as e:  # noqa: BLE001
                log.debug("signal shifts: breakdown failed for %s/%s: %s", sig, rt, e)
                breakdown = {d: [] for d in BREAKDOWN_DIMENSIONS}
                breakdown["top"] = None
                breakdown["threshold"] = shift["threshold"]
                breakdown["threshold_source"] = shift["threshold_source"]
            res = store.upsert_signal_issue(
                signal=sig, agent_type=rt, node_id=hit.get("node_id") or node_id or "",
                rate_before=shift["rate_before"], rate_during=shift["rate_during"],
                n_before=shift["n_before"], n_during=shift["n_during"],
                breakdown_json=json.dumps(breakdown),
                now_ms=now_ms, reopen_after_ms=SHORT_HOURS * _HOUR_MS,
            ) or {}
            action = str(res.get("action") or "none")
            if action in stats:
                stats[action] += 1
            if action in ("opened", "reopened") and deliver is not None:
                try:
                    deliver(shift_alert_match(res.get("issue") or {}, node_id=node_id,
                                              link=dashboard_link(), action=action))
                except Exception as e:  # noqa: BLE001
                    log.warning("signal shifts: delivery failed: %s", e)
                    stats["errors"] += 1
    except Exception as e:  # noqa: BLE001
        log.warning("signal shifts: tick failed: %s", e)
        stats["errors"] += 1
    return stats
