"""Agent self-diagnostics: reports an agent files about its own trouble, and
the independent check on whether the tool stream agrees (WO-59, REQ-SELF).

An agent given a plain reporting tool, framed as notes to the people who run
it, will say that a tool kept failing, that it lacked context or a permission,
that it could not finish, or that it worked around a block. ClawMetry already
watches the same session from outside, so every such note can be placed next
to what the detectors and the approval hooks recorded on their own:

* **Corroborated** means an independent record (a detector incident or a
  permission denial) exists for the same session within
  :data:`CORROBORATION_WINDOW_SECS` of the report.
* **Uncorroborated** means no such record was found. That is not the same as
  false; the detectors do not see everything.
* **Honesty**, per runtime and model, is the share of detector incidents in a
  window that the agent also reported. Below :data:`MIN_INCIDENTS` incidents
  the figure is withheld with a reason, because a ratio over three events is
  noise dressed as a number.

Everything here is pure or store-mediated; nothing in this module touches an
agent process. Self-reports are a signal, never an actuator.
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ── Constants ────────────────────────────────────────────────────────────────

#: The six default categories. Operators may add more via
#: ``~/.clawmetry/config.json`` -> ``{"self_diagnostics": {"categories": [...]}}``.
DEFAULT_CATEGORIES: Tuple[str, ...] = (
    "missing_context",
    "repeatedly_broken_tool",
    "capability_gap",
    "task_failure",
    "bypassed_block",
    "noteworthy",
)

#: A report is corroborated by evidence within this many seconds either side.
#: Too narrow and true reports look uncorroborated; too wide and unrelated
#: incidents corroborate. Override: ``CLAWMETRY_SELFDIAG_WINDOW_SECS``.
CORROBORATION_WINDOW_SECS = 600

#: Below this many detector incidents the honesty figure is withheld.
#: Override: ``CLAWMETRY_SELFDIAG_MIN_INCIDENTS``.
MIN_INCIDENTS = 5

#: Free-text summary cap, in characters. Anything longer is truncated, never
#: rejected: a long note is still a note.
SUMMARY_MAX_CHARS = 500

#: Default lookback for the honesty rollup and the Guard-tab counts.
DEFAULT_WINDOW_SECS = 7 * 86400

_CATEGORY_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")

_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")


def _env_int(name: str, default: int, floor: int = 0) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return max(floor, int(raw))
    except (TypeError, ValueError):
        return default


def corroboration_window_secs() -> int:
    """The active corroboration window (env override wins)."""
    return _env_int("CLAWMETRY_SELFDIAG_WINDOW_SECS", CORROBORATION_WINDOW_SECS, 1)


def min_incidents() -> int:
    """The active honesty floor (env override wins)."""
    return _env_int("CLAWMETRY_SELFDIAG_MIN_INCIDENTS", MIN_INCIDENTS, 1)


def _read_config(path: Optional[str] = None) -> dict:
    p = path or _CONFIG_PATH
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def allowed_categories(config_path: Optional[str] = None) -> Tuple[str, ...]:
    """Default categories plus any the operator added in config.json.

    Operator additions must look like identifiers (``snake_case``); anything
    else is ignored rather than raised, because a typo in a config file must
    not take the reporting tool down.
    """
    extra: List[str] = []
    cfg = _read_config(config_path).get("self_diagnostics")
    if isinstance(cfg, dict):
        raw = cfg.get("categories")
        if isinstance(raw, (list, tuple)):
            for item in raw:
                if isinstance(item, str):
                    cat = item.strip().lower()
                    if _CATEGORY_RE.match(cat) and cat not in DEFAULT_CATEGORIES \
                            and cat not in extra:
                        extra.append(cat)
    return tuple(DEFAULT_CATEGORIES) + tuple(extra)


def normalize_category(value: Any, config_path: Optional[str] = None) -> Optional[str]:
    """Return the canonical category or ``None`` when it is not allowed."""
    cat = str(value or "").strip().lower()
    return cat if cat in allowed_categories(config_path) else None


def clip_summary(value: Any) -> str:
    """One line, whitespace-collapsed, capped at :data:`SUMMARY_MAX_CHARS`."""
    text = " ".join(str(value or "").split())
    return text[:SUMMARY_MAX_CHARS]


# ── Windows ──────────────────────────────────────────────────────────────────

# No optional whitespace inside the pattern: the input is stripped first, so
# there is no ambiguous ``\s*`` pair for a long run of spaces to backtrack on.
_WINDOW_RE = re.compile(r"^(\d{1,12})([smhdw]?)$")
_WINDOW_UNITS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 7 * 86400}


def parse_window_secs(value: Any, default: int = DEFAULT_WINDOW_SECS) -> int:
    """``"24h"`` / ``"7d"`` / ``"30m"`` / ``3600`` -> seconds. Bad input ->
    ``default``. Clamped to at least one second."""
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(1, int(value))
    m = _WINDOW_RE.match(str(value).strip().lower()[:32])
    if not m:
        return default
    n = int(m.group(1))
    unit = m.group(2)
    return max(1, n * _WINDOW_UNITS.get(unit, 1))


# ── Time coercion ────────────────────────────────────────────────────────────

def to_epoch(value: Any) -> Optional[float]:
    """Best-effort conversion of a store timestamp to epoch seconds.

    Accepts epoch seconds or milliseconds (numbers), ``datetime`` objects
    (naive ones are read as local wall-clock, which is how the loop-signal
    writer stamps them), and ISO-8601 strings with or without an offset.
    Returns ``None`` for anything unreadable.
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        # Epoch milliseconds are ~1e12 today; seconds are ~1e9.
        return v / 1000.0 if v > 1e11 else v
    if isinstance(value, datetime):
        try:
            return value.timestamp()
        except Exception:
            return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text) / 1000.0 if float(text) > 1e11 else float(text)
    except ValueError:
        pass
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text).timestamp()
    except Exception:
        return None


# ── Session identity ─────────────────────────────────────────────────────────

def bare_session_id(session_id: Any) -> str:
    """``claude_code:abc`` and ``abc`` name the same session. Family
    adapters store the prefixed form; an agent reporting from inside the
    session usually only knows the bare id."""
    sid = str(session_id or "").strip()
    if ":" in sid:
        head, tail = sid.split(":", 1)
        if head and tail and _CATEGORY_RE.match(head.lower()):
            return tail
    return sid


def same_session(a: Any, b: Any) -> bool:
    sa, sb = str(a or "").strip(), str(b or "").strip()
    if not sa or not sb:
        return False
    return sa == sb or bare_session_id(sa) == bare_session_id(sb)


def runtime_from_session_id(session_id: Any) -> str:
    """The runtime prefix of a family session id, or ``""``."""
    sid = str(session_id or "").strip()
    if ":" in sid:
        head = sid.split(":", 1)[0].lower()
        if _CATEGORY_RE.match(head):
            return head
    return ""


# Environment clues an MCP server process may inherit from its host agent.
# Best-effort only: a runtime that exports nothing is inferred from the
# working directory instead (see the MCP server), and an unresolvable
# session is stored as unknown rather than refused.
_SESSION_ENV_VARS: Tuple[str, ...] = (
    "CLAWMETRY_SESSION_ID",
    "CLAUDE_SESSION_ID",
    "CODEX_SESSION_ID",
    "GEMINI_SESSION_ID",
    "CURSOR_SESSION_ID",
    "OPENCODE_SESSION_ID",
)
_RUNTIME_ENV_HINTS: Tuple[Tuple[str, str], ...] = (
    ("CLAWMETRY_RUNTIME", ""),          # explicit override, value is the runtime
    ("CLAUDECODE", "claude_code"),
    ("CLAUDE_CODE_ENTRYPOINT", "claude_code"),
    ("CLAUDE_SESSION_ID", "claude_code"),
    ("CODEX_SESSION_ID", "codex"),
    ("CODEX_HOME", "codex"),
    ("GEMINI_SESSION_ID", "gemini_cli"),
    ("GEMINI_CLI", "gemini_cli"),
    ("CURSOR_SESSION_ID", "cursor"),
    ("CURSOR_TRACE_ID", "cursor"),
    ("OPENCODE_SESSION_ID", "opencode"),
    ("OPENCODE", "opencode"),
)


def infer_session_from_env(environ: Optional[Dict[str, str]] = None) -> str:
    env = os.environ if environ is None else environ
    for name in _SESSION_ENV_VARS:
        val = (env.get(name) or "").strip()
        if val:
            return val[:128]
    return ""


def infer_runtime_from_env(environ: Optional[Dict[str, str]] = None) -> str:
    env = os.environ if environ is None else environ
    for name, runtime in _RUNTIME_ENV_HINTS:
        val = (env.get(name) or "").strip()
        if not val:
            continue
        if not runtime:
            rt = val.lower()
            return rt if _CATEGORY_RE.match(rt) else ""
        return runtime
    return ""


# ── Corroboration (pure) ─────────────────────────────────────────────────────

def _incident_bounds(inc: dict) -> Tuple[Optional[float], Optional[float]]:
    first = to_epoch(inc.get("first_seen") or inc.get("ts"))
    last = to_epoch(inc.get("last_seen") or inc.get("ts"))
    if first is None and last is None:
        return None, None
    if first is None:
        first = last
    if last is None:
        last = first
    return min(first, last), max(first, last)


def incident_matches(report_ts: float, inc: dict, window_secs: int) -> bool:
    """True when a detector incident's flagged stretch, widened by
    ``window_secs`` on both sides, contains the report time."""
    first, last = _incident_bounds(inc)
    if first is None or last is None:
        return False
    return (first - window_secs) <= report_ts <= (last + window_secs)


def denial_matches(report_ts: float, denial: dict, window_secs: int) -> bool:
    """True when a permission denial happened within ``window_secs`` of the
    report. A denial is a point in time, so the test is symmetric."""
    t = to_epoch(denial.get("resolved_at") or denial.get("ts") or denial.get("created_at"))
    if t is None:
        return False
    return abs(report_ts - t) <= window_secs


def incident_ref(inc: dict) -> str:
    sid = str(inc.get("session_id") or "")
    sig = str(inc.get("signature") or inc.get("kind") or "incident")
    return f"incident:{sid}:{sig}"


def denial_ref(denial: dict) -> str:
    return f"denial:{denial.get('id') or denial.get('approval_id') or ''}"


def find_evidence(report: dict, incidents: Iterable[dict], denials: Iterable[dict],
                  window_secs: Optional[int] = None) -> Optional[str]:
    """The reference of the first independent record that corroborates
    ``report``, or ``None``. Incidents are checked before denials; among
    incidents the one whose stretch ends nearest the report wins, so a
    ``bypassed_block`` report links to the block it worked around rather
    than to an older loop in the same session.
    """
    window = corroboration_window_secs() if window_secs is None else int(window_secs)
    ts = to_epoch(report.get("ts"))
    if ts is None:
        return None
    sid = report.get("session_id")
    best: Optional[Tuple[float, str]] = None
    for inc in incidents or []:
        if not isinstance(inc, dict) or not same_session(sid, inc.get("session_id")):
            continue
        if incident_matches(ts, inc, window):
            _first, last = _incident_bounds(inc)
            dist = abs((last or ts) - ts)
            if best is None or dist < best[0]:
                best = (dist, incident_ref(inc))
    if best is not None:
        return best[1]
    for d in denials or []:
        if not isinstance(d, dict):
            continue
        dsid = d.get("session_id") or d.get("requestor_session_id")
        if not same_session(sid, dsid):
            continue
        if denial_matches(ts, d, window):
            return denial_ref(d)
    return None


# ── Honesty rollup (pure) ────────────────────────────────────────────────────

def honesty_rollup(incidents: Iterable[dict], reports: Iterable[dict],
                   window_secs: Optional[int] = None,
                   min_count: Optional[int] = None) -> List[dict]:
    """Per (runtime, model): how many detector incidents the agent also
    reported.

    An incident counts as reported when a self-report for the same session
    falls inside the incident's stretch widened by the corroboration window.
    Cohorts under ``min_count`` incidents return ``honesty: None`` with
    ``withheld: True`` and a plain reason, never a ratio.
    """
    window = corroboration_window_secs() if window_secs is None else int(window_secs)
    floor = min_incidents() if min_count is None else int(min_count)
    reps = [r for r in (reports or []) if isinstance(r, dict)]
    buckets: Dict[Tuple[str, str], Dict[str, int]] = {}
    for inc in incidents or []:
        if not isinstance(inc, dict):
            continue
        runtime = str(inc.get("runtime") or inc.get("agent_type") or "unknown").lower()
        model = str(inc.get("model") or "unknown")
        key = (runtime, model)
        b = buckets.setdefault(key, {"incidents": 0, "reported": 0})
        b["incidents"] += 1
        sid = inc.get("session_id")
        for r in reps:
            if not same_session(sid, r.get("session_id")):
                continue
            rts = to_epoch(r.get("ts"))
            if rts is not None and incident_matches(rts, inc, window):
                b["reported"] += 1
                break
    out: List[dict] = []
    for (runtime, model), b in sorted(buckets.items()):
        n, k = b["incidents"], b["reported"]
        row = {"runtime": runtime, "model": model, "incidents": n, "reported": k}
        if n < floor:
            row.update({
                "honesty": None,
                "withheld": True,
                "reason": (f"Only {n} detector incident{'s' if n != 1 else ''} "
                           f"in this window; at least {floor} needed before the "
                           f"figure means anything."),
            })
        else:
            row.update({"honesty": round(k / n, 3), "withheld": False, "reason": ""})
        out.append(row)
    return out


def count_by_runtime_category(reports: Iterable[dict]) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}
    for r in reports or []:
        if not isinstance(r, dict):
            continue
        rt = str(r.get("agent_type") or r.get("runtime") or "unknown").lower()
        cat = str(r.get("category") or "unknown")
        counts.setdefault(rt, {})
        counts[rt][cat] = counts[rt].get(cat, 0) + 1
    return counts


# ── Daemon-side passes (store-mediated) ──────────────────────────────────────

#: How far back the corroboration pass looks for pending reports. Wide
#: enough to survive a daemon restart, narrow enough to stay cheap.
PENDING_LOOKBACK_SECS = 6 * 3600


def corroborate_pending(store, now: Optional[float] = None) -> int:
    """One daemon tick: attach evidence to reports that have none yet.

    Reads pending reports and the incidents/denials around them through
    the store the daemon already holds (never a second handle), marks each
    corroborated one, and returns how many it marked. Never raises into the
    daemon loop.
    """
    try:
        now_ts = time.time() if now is None else float(now)
        window = corroboration_window_secs()
        pending = store.query_self_reports(
            since_secs=PENDING_LOOKBACK_SECS, uncorroborated_only=True, limit=500,
        ) or []
        if not pending:
            return 0
        lookback = PENDING_LOOKBACK_SECS + window
        incidents = store.query_guard_incidents(since_secs=lookback, limit=2000) or []
        denials = store.query_session_denials(since_secs=lookback, limit=2000) or []
        marked = 0
        for rep in pending:
            ref = find_evidence(rep, incidents, denials, window)
            if not ref:
                continue
            try:
                if store.mark_self_report_corroborated(rep.get("id"), ref):
                    marked += 1
            except Exception:
                continue
        _ = now_ts
        return marked
    except Exception:
        return 0


def snapshot_slice(store, window_secs: int = DEFAULT_WINDOW_SECS) -> dict:
    """The ``selfReports`` snapshot slice: counts per category per runtime
    plus the honesty rollup. No summaries; those stay on the node."""
    reports = store.query_self_reports(since_secs=window_secs, limit=5000) or []
    honesty = store.query_self_report_honesty(since_secs=window_secs) or []
    corroborated = sum(1 for r in reports if isinstance(r, dict) and r.get("corroborated"))
    return {
        "window_secs": int(window_secs),
        "total": len(reports),
        "corroborated": corroborated,
        "byRuntime": count_by_runtime_category(reports),
        "honesty": honesty,
        "min_incidents": min_incidents(),
        "corroboration_window_secs": corroboration_window_secs(),
    }
