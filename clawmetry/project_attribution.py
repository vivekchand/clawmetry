"""Project attribution and per-project budget arithmetic (REQ-OBS-PRJ-001).

Pure: no I/O, no store, no clock unless one is passed in. The store surface in
``clawmetry/local_store_projects.py`` feeds it rows and persists what it
decides; ``routes/projects.py`` serves the result.

What a "project" is
-------------------
A session's project is DERIVED when read, never stamped on the session row
(the trade REQ-OBS-004 made for ownership, for the same reasons: no migration,
no re-stamp inside the write lock when an assignment changes, and a new
assignment applies to history already collected).

Resolution, most authoritative first:

1. ``assigned``   -- an operator assignment in force at the session's start.
                     A session-level assignment beats a project-level one; a
                     later assignment for the same target supersedes an
                     earlier one without erasing it.
2. ``repository`` -- the longest known repository root (``git_repos``, which
                     the read-only git reader records) containing the
                     session's working directory.
3. ``directory``  -- the working directory itself, low confidence.
4. ``none``       -- no working directory recorded: the visible Unassigned
                     group, never a default project.

A project or tenant name carried inside the agent's own activity is never
consulted. The identifier is a hash of the normalised root path, so two
repositories that share a directory name stay two projects, and the same path
yields the same identifier whichever rung produced it. Published labels are a
last path segment or an operator-chosen name, never the full local path.

Budgets
-------
A budget declares amount, period, timezone, currency and basis. Spend is
bucketed into 15-minute UTC buckets by the store; every real timezone offset is
a multiple of 15 minutes, so a local-midnight period boundary always falls on a
bucket edge and a session running across it is split exactly. Alerts at
50/80/100% are notifications only (``ENFORCEMENT_NOTICE``).
"""
from __future__ import annotations

import hashlib
import math
import ntpath
import posixpath
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

UNASSIGNED_ID = "unassigned"
UNASSIGNED_LABEL = "Unassigned"

THRESHOLDS = (50, 80, 100)
PERIODS = ("day", "week", "month")
# ClawMetry records spend in US dollars only. A budget in another currency
# would compare a EUR amount against a USD figure, so it is refused.
CURRENCIES = ("USD",)
# The only spend figure a node records: its own estimate from published list
# prices (or what a runtime reported). Negotiated rates are the Price Book.
BASIS_ESTIMATED = "estimated_spend"
BASES = (BASIS_ESTIMATED,)
BUCKET_SECS = 900

ENFORCEMENT_NOTICE = (
    "Budget alerts are notifications based on usage value at published rates, "
    "which is not an invoice. They do not pause, stop or reverse any charge."
)

_PROJECT_ID_RE = re.compile(r"^(prj|prjn)_[0-9a-f]{16}$")
_MATCH_TYPES = ("project", "session")
_MAX_NAME = 120
_MAX_REASON = 500


# ── paths and identifiers ────────────────────────────────────────────────


def _is_windows_path(s: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", s)) or s.startswith("\\\\")


def normalize_path(path: Any) -> str:
    """Comparable form of a working directory or repository root.

    Windows paths are case-insensitive and use either separator, so they are
    folded; POSIX paths keep their case. Trailing separators are dropped.
    ``""`` for anything empty.
    """
    s = str(path or "").strip()
    if not s:
        return ""
    if _is_windows_path(s):
        s = ntpath.normpath(s).replace("\\", "/").lower()
    else:
        s = posixpath.normpath(s)
    if len(s) > 1:
        s = s.rstrip("/")
    return s or "/"


def _last_segment(path: Any) -> str:
    s = str(path or "").strip().replace("\\", "/").rstrip("/")
    return s.rsplit("/", 1)[-1] if s else ""


def project_id_for_root(root: Any) -> str:
    """Opaque, stable identifier for a derived project root."""
    norm = normalize_path(root)
    if not norm:
        return UNASSIGNED_ID
    return "prj_" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def assigned_project_id(name: Any) -> str:
    """Identifier for an operator-named project. Case-insensitive on the name
    so "Billing" and "billing" are one project."""
    n = " ".join(str(name or "").split()).lower()
    return "prjn_" + hashlib.sha256(n.encode("utf-8")).hexdigest()[:16]


def is_project_id(value: Any) -> bool:
    return bool(_PROJECT_ID_RE.match(str(value or "")))


def _within(child: str, root: str) -> bool:
    if child == root:
        return True
    if root == "/":
        return child.startswith("/")
    return child.startswith(root + "/")


def _directory_label(root: Any, home: Any = None) -> str:
    norm = normalize_path(root)
    if norm in ("/",) or re.match(r"^[a-z]:/?$", norm):
        return "Filesystem root"
    if home and norm == normalize_path(home):
        # The last segment of a home directory is the OS account name, which
        # is not a project and should not be published as one.
        return "Home directory"
    return _last_segment(root) or "Project"


def derive_project(cwd: Any, repo_roots: Iterable[tuple] = (), *,
                   home: Any = None) -> dict[str, str]:
    """The project a working directory belongs to, before any assignment.

    ``repo_roots`` is ``(repo_root, name)`` pairs from the repository reader.
    The longest root containing ``cwd`` wins, so a nested repository is its
    own project rather than part of its parent.
    """
    c = normalize_path(cwd)
    if not c:
        return {"project_id": UNASSIGNED_ID, "label": UNASSIGNED_LABEL,
                "source": "none", "confidence": "none"}
    best = None
    for pair in repo_roots or ():
        try:
            root, name = pair[0], (pair[1] if len(pair) > 1 else "")
        except (TypeError, IndexError):
            continue
        r = normalize_path(root)
        if r and _within(c, r) and (best is None or len(r) > len(best[0])):
            best = (r, root, name)
    if best is not None:
        _, root, name = best
        return {"project_id": project_id_for_root(root),
                "label": str(name or "").strip()[:_MAX_NAME]
                or _directory_label(root, home),
                "source": "repository", "confidence": "high"}
    return {"project_id": project_id_for_root(cwd),
            "label": _directory_label(cwd, home),
            "source": "directory", "confidence": "low"}


# ── time ─────────────────────────────────────────────────────────────────


def to_epoch(ts: Any) -> float | None:
    """POSIX seconds for an ISO-8601 string, epoch number, or aware datetime.

    A naive string is the node's own wall clock, matching the store's day
    buckets (ADR-046). ``None`` when nothing can be parsed.
    """
    if ts is None or ts == "":
        return None
    if isinstance(ts, datetime):
        return (ts if ts.tzinfo else ts.astimezone()).timestamp()
    if isinstance(ts, (int, float)) and not isinstance(ts, bool):
        v = float(ts)
        return v / 1000.0 if v > 1e12 else v
    s = str(ts).strip()
    try:
        from clawmetry.cost_windows import _normalize_ts
        dt = datetime.fromisoformat(_normalize_ts(s))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt.timestamp()


def resolve_timezone(name: Any):
    """A tzinfo for an IANA name. Raises ``ValueError`` for a name this
    machine cannot resolve rather than silently substituting UTC."""
    n = str(name or "").strip()
    if not n:
        raise ValueError("timezone is required")
    if n.upper() in ("UTC", "ETC/UTC", "Z", "GMT", "ETC/GMT"):
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+
        return ZoneInfo(n)
    except Exception as exc:  # noqa: BLE001 - unknown name, no tzdata, py3.8
        raise ValueError(
            f"timezone {n!r} cannot be resolved on this machine") from exc


def canonical_timezone_name(name: Any) -> str:
    n = str(name or "").strip()
    return "UTC" if n.upper() in ("UTC", "ETC/UTC", "Z", "GMT", "ETC/GMT") else n


def _local_midnight(d: date, tz) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=tz)


def period_bounds(period: str, tz, at: float | datetime) -> tuple[datetime, datetime]:
    """``[start, end)`` of the ``period`` containing ``at``, on ``tz``'s
    calendar. Weeks start Monday, matching ``clawmetry/cost_windows.py``."""
    moment = at if isinstance(at, datetime) else datetime.fromtimestamp(float(at), tz)
    local = moment.astimezone(tz)
    d = local.date()
    if period == "day":
        s, e = d, d + timedelta(days=1)
    elif period == "week":
        s = d - timedelta(days=local.weekday())
        e = s + timedelta(days=7)
    elif period == "month":
        s = d.replace(day=1)
        e = (s.replace(year=s.year + 1, month=1) if s.month == 12
             else s.replace(month=s.month + 1))
    else:
        raise ValueError(f"unknown period {period!r}")
    return _local_midnight(s, tz), _local_midnight(e, tz)


def previous_period_bounds(period: str, tz, at: float | datetime) -> tuple[datetime, datetime]:
    start, _ = period_bounds(period, tz, at)
    return period_bounds(period, tz, start - timedelta(seconds=1))


def local_day(epoch: float, tz) -> str:
    return datetime.fromtimestamp(float(epoch), tz).strftime("%Y-%m-%d")


# ── assignments ──────────────────────────────────────────────────────────


def _in_effect(a: dict, at: float | None) -> bool:
    frm, to = to_epoch(a.get("effective_from")), to_epoch(a.get("effective_to"))
    if at is None:
        # A session with no known start can only be covered by an assignment
        # that is not bounded in time.
        return frm is None and to is None
    return (frm is None or at >= frm) and (to is None or at < to)


def _created(a: dict) -> tuple:
    return (int(a.get("created_at") or 0), str(a.get("assignment_id") or ""))


def resolve_project(derived: dict, session_id: str, session_started: Any,
                    assignments: Iterable[dict]) -> dict:
    """Apply operator assignments to a derived project.

    Session-level assignments beat project-level ones; within a level the most
    recently created assignment in force wins, which is how a correction
    supersedes an earlier assignment without deleting it.
    """
    at = to_epoch(session_started)
    pid = derived.get("project_id")
    best_by_level: dict[str, dict] = {}
    for a in assignments or ():
        mt, mv = a.get("match_type"), a.get("match_value")
        if mt == "session":
            if not session_id or mv != session_id:
                continue
        elif mt == "project":
            if mv != pid:
                continue
        else:
            continue
        if not _in_effect(a, at):
            continue
        cur = best_by_level.get(mt)
        if cur is None or _created(a) > _created(cur):
            best_by_level[mt] = a
    chosen = best_by_level.get("session") or best_by_level.get("project")
    if chosen is None:
        return dict(derived)
    name = str(chosen.get("project_name") or "").strip()
    return {"project_id": assigned_project_id(name), "label": name,
            "source": "assigned", "confidence": "high",
            "assignment_id": chosen.get("assignment_id"),
            "derived_project_id": pid}


def annotate_superseded(assignments: list[dict]) -> list[dict]:
    """Mark each assignment with the later assignment (same target, overlapping
    effective period) that supersedes it. History is kept, never rewritten."""
    out = [dict(a) for a in assignments]
    for a in out:
        a["superseded_by"] = None
        a_from = to_epoch(a.get("effective_from")) or -math.inf
        a_to = to_epoch(a.get("effective_to")) or math.inf
        later = None
        for b in out:
            if b is a or (b.get("match_type"), b.get("match_value")) != (
                    a.get("match_type"), a.get("match_value")):
                continue
            if _created(b) <= _created(a):
                continue
            b_from = to_epoch(b.get("effective_from")) or -math.inf
            b_to = to_epoch(b.get("effective_to")) or math.inf
            if b_from < a_to and a_from < b_to and (later is None or _created(b) < _created(later)):
                later = b
        if later is not None:
            a["superseded_by"] = later.get("assignment_id")
    return out


def validate_assignment(body: Any) -> tuple[dict | None, str | None]:
    """Clean an assignment request, or return a plain-words error."""
    if not isinstance(body, dict):
        return None, "request body must be a JSON object"
    mt = str(body.get("match_type") or "").strip().lower()
    mv = str(body.get("match_value") or "").strip()
    name = " ".join(str(body.get("project_name") or "").split())
    reason = str(body.get("reason") or "").strip()
    if mt not in _MATCH_TYPES:
        return None, "match_type must be 'project' or 'session'"
    if not mv:
        return None, "match_value is required"
    if mt == "project" and not is_project_id(mv):
        return None, "match_value must be a project id from /api/projects"
    if not name:
        return None, "project_name is required"
    if len(name) > _MAX_NAME:
        return None, f"project_name must be at most {_MAX_NAME} characters"
    if not reason:
        return None, "reason is required, so the assignment's history explains itself"
    frm, to = body.get("effective_from"), body.get("effective_to")
    frm_e, to_e = to_epoch(frm), to_epoch(to)
    if frm not in (None, "") and frm_e is None:
        return None, "effective_from must be an ISO-8601 timestamp"
    if to not in (None, "") and to_e is None:
        return None, "effective_to must be an ISO-8601 timestamp"
    if frm_e is not None and to_e is not None and to_e <= frm_e:
        return None, "effective_to must be later than effective_from"
    return {"match_type": mt, "match_value": mv[:200], "project_name": name,
            "reason": reason[:_MAX_REASON],
            "effective_from": str(frm) if frm_e is not None else None,
            "effective_to": str(to) if to_e is not None else None}, None


# ── budgets ──────────────────────────────────────────────────────────────


def validate_budget(body: Any) -> tuple[dict | None, str | None]:
    """Clean a budget request, or return a plain-words error. Every budget
    declares its period, timezone, currency and basis; nothing is defaulted
    silently except the basis, which has exactly one honest value."""
    if not isinstance(body, dict):
        return None, "request body must be a JSON object"
    pid = str(body.get("project_id") or "").strip()
    if not is_project_id(pid):
        return None, "project_id must be a project id from /api/projects"
    try:
        amount = float(body.get("amount"))
    except (TypeError, ValueError):
        return None, "amount must be a number"
    if not math.isfinite(amount) or amount <= 0:
        return None, "amount must be greater than zero"
    currency = str(body.get("currency") or "").strip().upper()
    if not currency:
        return None, "currency is required"
    if currency not in CURRENCIES:
        return None, (f"currency {currency} is not supported: spend on this "
                      "machine is recorded in USD only")
    period = str(body.get("period") or "").strip().lower()
    if period not in PERIODS:
        return None, "period must be one of day, week or month"
    tz_name = body.get("timezone")
    try:
        resolve_timezone(tz_name)
    except ValueError as exc:
        return None, str(exc)
    basis = str(body.get("basis") or BASIS_ESTIMATED).strip().lower()
    if basis not in BASES:
        return None, (f"basis {basis!r} is not available: the only spend this "
                      f"machine records is {BASIS_ESTIMATED}")
    return {"project_id": pid, "amount": round(amount, 6), "currency": currency,
            "period": period, "timezone": canonical_timezone_name(tz_name),
            "basis": basis}, None


def crossed_thresholds(spent: float, amount: float,
                       thresholds: Iterable[int] = THRESHOLDS) -> list[int]:
    if not amount or amount <= 0:
        return []
    return [int(t) for t in thresholds if spent >= amount * (float(t) / 100.0) - 1e-9]


def summarize_buckets(buckets: Iterable[dict], start: datetime, end: datetime,
                      tz, *, sessions: set | None = None) -> dict[str, Any]:
    """Sum bucket rows falling in ``[start, end)``, optionally only for the
    given session ids, with a per-local-day burn series covering the whole
    period so far (days with no spend are present as zero)."""
    s_e, e_e = start.timestamp(), end.timestamp()
    cost = 0.0
    unpriced_tokens = 0
    unpriced_events = 0
    by_day: dict[str, float] = {}
    for b in buckets:
        if sessions is not None and b.get("session_id") not in sessions:
            continue
        t = b.get("bucket")
        if t is None or not (s_e <= t < e_e):
            continue
        c = float(b.get("cost_usd") or 0.0)
        cost += c
        unpriced_tokens += int(b.get("unpriced_tokens") or 0)
        unpriced_events += int(b.get("unpriced_events") or 0)
        day = local_day(t, tz)
        by_day[day] = by_day.get(day, 0.0) + c
    return {"spent_usd": round(cost, 6), "unpriced_tokens": unpriced_tokens,
            "unpriced_events": unpriced_events, "by_day": by_day}


def burn_series(by_day: dict[str, float], start: datetime, until: datetime,
                tz) -> list[dict[str, Any]]:
    out = []
    d = start.astimezone(tz).date()
    last = until.astimezone(tz).date()
    guard = 0
    while d <= last and guard < 400:
        key = d.strftime("%Y-%m-%d")
        out.append({"day": key, "spent_usd": round(by_day.get(key, 0.0), 6)})
        d += timedelta(days=1)
        guard += 1
    return out
