"""clawmetry/local_store_projects.py — ProjectsMixin for LocalStore (REQ-OBS-PRJ-001).

Store surface for project attribution and per-project budgets. Kept in its
own short module (mixed into ``LocalStore`` in ``clawmetry/local_store.py``,
which holds the three table definitions) so a reader, and Drift Bot, find the
whole surface in one place instead of at line 20,000 of the store.

Tables (defined in ``clawmetry/local_store.py``):

* ``project_assignments``   -- operator assignments. Append-only: a correction
                               is a new row, never an UPDATE, so history and
                               provenance (who, when, why) survive.
* ``project_budgets``       -- one budget per project: amount, currency,
                               period, timezone, basis.
* ``project_budget_alerts`` -- the once-per-threshold-per-period latch,
                               primary key ``(budget_id, period_start,
                               threshold_pct)``. Restart-safe by construction.

Nothing is written to ``sessions`` or ``events``. A session's project is
derived when read by ``clawmetry/project_attribution.py``.

Public API:
  - query_project_usage(days, now)           -> projects with spend + totals
  - add_project_assignment(...)              -> {ok, assignment | error}
  - query_project_assignments()              -> history, superseded marked
  - upsert_project_budget(...)               -> {ok, budget | error}
  - delete_project_budget(budget_id)         -> {ok, deleted}
  - query_project_budgets()                  -> budgets
  - project_budget_status(now)               -> budgets with period burn
  - evaluate_project_budgets(now)            -> newly latched alerts
  - query_project_budget_alerts(limit)       -> recorded alerts

Requires the consuming class to supply ``self._write_lock``, ``self._conn``,
``self._fetch`` and ``self._read_only`` (all provided by LocalStore).
"""
from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from clawmetry import project_attribution as _pa

log = logging.getLogger("clawmetry.local_store.projects")

_BUCKET_CACHE: dict = {}
_BUCKET_CACHE_LOCK = threading.Lock()
_IN_CHUNK = 500


def _cache_ttl() -> float:
    try:
        return float(os.environ.get("CLAWMETRY_AGG_CACHE_TTL", "20"))
    except ValueError:
        return 20.0


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def _fail(msg: str) -> dict:
    return {"ok": False, "error": msg}


class ProjectsMixin:

    # ── raw reads ─────────────────────────────────────────────────────────

    def _project_usage_buckets(self, since_epoch: float, until_epoch: float) -> list[dict]:
        """Deduped spend per (session, 15-minute UTC bucket) in the window.

        Same envelope dedupe as ``query_aggregates``: an ``assistant`` /
        ``message`` row and its ``model.completed`` sibling in the same
        second carry the same cost, so the sibling is dropped. Usage with
        tokens and no price is counted separately as unpriced, never as $0.
        """
        since_b = int(since_epoch // _pa.BUCKET_SECS * _pa.BUCKET_SECS)
        # Both ends snap to bucket edges so the cache key is stable between
        # daemon ticks (a key holding the exact second never hit). Rounding
        # the upper end up only admits rows stamped after ``until_epoch``
        # (clock skew); budget status re-filters by its own period bounds.
        until_i = int(-(-int(until_epoch) // _pa.BUCKET_SECS) * _pa.BUCKET_SECS)
        key = (since_b, until_i)
        ttl = _cache_ttl()
        if ttl > 0:
            with _BUCKET_CACHE_LOCK:
                hit = _BUCKET_CACHE.get(key)
                if hit is not None and time.monotonic() - hit[0] < ttl:
                    return hit[1]
        # The string floor lets zone maps skip old row groups; it is widened
        # by a day so a timestamp written with a different offset is not cut
        # before the exact epoch filter sees it.
        raw_floor = datetime.fromtimestamp(since_b - 86400, timezone.utc).strftime("%Y-%m-%d")
        sql = f"""
            WITH ranked AS (
              SELECT session_id, cost_usd, token_count,
                     CASE event_type
                       WHEN 'assistant'       THEN 2
                       WHEN 'message'         THEN 2
                       WHEN 'model.completed' THEN 1
                       ELSE 0
                     END AS envelope_rank,
                     CAST(epoch(TRY_CAST(ts AS TIMESTAMPTZ)) AS BIGINT) AS ts_sec
              FROM events
              WHERE ts >= ?
            ),
            bucket_max AS (
              SELECT session_id, ts_sec, MAX(envelope_rank) AS max_rank
              FROM ranked GROUP BY session_id, ts_sec
            ),
            deduped AS (
              SELECT r.* FROM ranked r
              JOIN bucket_max bm USING (session_id, ts_sec)
              WHERE NOT (r.envelope_rank = 1 AND bm.max_rank = 2)
                AND r.ts_sec >= ? AND r.ts_sec < ?
            )
            SELECT session_id,
                   (ts_sec // {_pa.BUCKET_SECS}) * {_pa.BUCKET_SECS} AS bucket,
                   COALESCE(SUM(cost_usd), 0) AS cost_usd,
                   COALESCE(SUM(CASE WHEN cost_usd IS NOT NULL THEN token_count END), 0) AS priced_tokens,
                   COALESCE(SUM(CASE WHEN cost_usd IS NULL AND token_count > 0 THEN token_count END), 0) AS unpriced_tokens,
                   COUNT(CASE WHEN cost_usd IS NULL AND token_count > 0 THEN 1 END) AS unpriced_events
            FROM deduped
            GROUP BY 1, 2
        """
        try:
            rows = self._fetch(sql, [raw_floor, since_b, until_i])
        except Exception as e:  # noqa: BLE001 - never raise into a read path
            log.warning("projects: usage bucket query failed: %s", e)
            raise
        out = [{"session_id": r[0], "bucket": int(r[1]), "cost_usd": float(r[2] or 0.0),
                "priced_tokens": int(r[3] or 0), "unpriced_tokens": int(r[4] or 0),
                "unpriced_events": int(r[5] or 0)} for r in rows]
        if ttl > 0:
            with _BUCKET_CACHE_LOCK:
                if len(_BUCKET_CACHE) > 64:
                    _BUCKET_CACHE.clear()
                _BUCKET_CACHE[key] = (time.monotonic(), out)
        return out

    def _project_repo_roots(self) -> list[tuple]:
        try:
            return [(r[0], r[1] or "") for r in self._fetch(
                "SELECT repo_root, name FROM git_repos WHERE repo_root IS NOT NULL", [])]
        except Exception:  # noqa: BLE001 - repository reader switched off / fresh store
            return []

    def _project_assignment_rows(self) -> list[dict]:
        try:
            rows = self._fetch(
                "SELECT assignment_id, match_type, match_value, project_name, "
                "effective_from, effective_to, actor, reason, created_at "
                "FROM project_assignments ORDER BY created_at, assignment_id", [])
        except Exception:  # noqa: BLE001
            return []
        cols = ["assignment_id", "match_type", "match_value", "project_name",
                "effective_from", "effective_to", "actor", "reason", "created_at"]
        return [dict(zip(cols, r)) for r in rows]

    def _project_sessions(self, session_ids: list) -> dict[str, dict]:
        out: dict[str, dict] = {}
        ids = [s for s in dict.fromkeys(session_ids) if s]
        for i in range(0, len(ids), _IN_CHUNK):
            chunk = ids[i:i + _IN_CHUNK]
            marks = ",".join("?" * len(chunk))
            for sid, cwd, started, last in self._fetch(
                    f"SELECT session_id, cwd, started_at, last_active_at FROM sessions "
                    f"WHERE session_id IN ({marks})", chunk):
                cur = out.get(sid)
                if cur is None or (not cur["cwd"] and cwd):
                    out[str(sid)] = {"cwd": cwd or "", "started_at": started or last}
        return out

    def _resolve_projects(self, session_ids: list) -> dict[str, dict]:
        roots = self._project_repo_roots()
        assignments = self._project_assignment_rows()
        meta = self._project_sessions(session_ids)
        home = os.path.expanduser("~")
        derived_cache: dict[str, dict] = {}
        out: dict[str, dict] = {}
        for sid in session_ids:
            m = meta.get(sid) or {"cwd": "", "started_at": None}
            cwd = m["cwd"]
            if cwd not in derived_cache:
                derived_cache[cwd] = _pa.derive_project(cwd, roots, home=home)
            out[sid] = _pa.resolve_project(derived_cache[cwd], sid, m["started_at"], assignments)
        return out

    def _project_catalog(self) -> dict[str, dict]:
        """Every project id this store can name: derived from any session's
        working directory, plus every operator-named project."""
        roots = self._project_repo_roots()
        home = os.path.expanduser("~")
        cat: dict[str, dict] = {}
        try:
            cwds = [r[0] for r in self._fetch(
                "SELECT DISTINCT cwd FROM sessions WHERE cwd IS NOT NULL AND cwd <> ''", [])]
        except Exception:  # noqa: BLE001
            cwds = []
        for cwd in cwds:
            d = _pa.derive_project(cwd, roots, home=home)
            cat.setdefault(d["project_id"], d)
        for a in self._project_assignment_rows():
            name = str(a.get("project_name") or "").strip()
            if name:
                cat[_pa.assigned_project_id(name)] = {
                    "project_id": _pa.assigned_project_id(name), "label": name,
                    "source": "assigned", "confidence": "high"}
        return cat

    # ── attribution ───────────────────────────────────────────────────────

    def query_project_usage(self, days: int = 30, now: float | None = None) -> dict[str, Any]:
        """Spend per project over the last ``days``, with totals that
        reconcile: derived + assigned + unassigned = the node total for the
        window, and unpriced usage is reported beside it rather than as $0."""
        try:
            n_days = max(1, min(366, int(days)))
        except (TypeError, ValueError):
            n_days = 30
        now_e = float(now) if now is not None else time.time()
        since_e = now_e - n_days * 86400
        try:
            buckets = self._project_usage_buckets(since_e, now_e)
        except Exception:  # noqa: BLE001
            return {"available": False, "reason": "store_query_failed",
                    "projects": [], "totals": {}}
        per_session: dict[str, dict] = {}
        for b in buckets:
            s = per_session.setdefault(b["session_id"], {"cost_usd": 0.0, "priced_tokens": 0,
                                                         "unpriced_tokens": 0, "unpriced_events": 0})
            for k in ("cost_usd", "priced_tokens", "unpriced_tokens", "unpriced_events"):
                s[k] += b[k]
        projects_of = self._resolve_projects(list(per_session))
        try:
            from clawmetry.local_store import _runtime_of_session_id
        except Exception:  # noqa: BLE001
            def _runtime_of_session_id(sid, fallback="openclaw"):
                return fallback
        by_project: dict[str, dict] = {}
        totals = {"cost_usd": 0.0, "derived_cost_usd": 0.0, "assigned_cost_usd": 0.0,
                  "unassigned_cost_usd": 0.0, "priced_tokens": 0, "unpriced_tokens": 0,
                  "unpriced_events": 0, "sessions": 0, "unassigned_sessions": 0}
        for sid, s in per_session.items():
            p = projects_of.get(sid) or {"project_id": _pa.UNASSIGNED_ID,
                                         "label": _pa.UNASSIGNED_LABEL,
                                         "source": "none", "confidence": "none"}
            row = by_project.setdefault(p["project_id"], {
                "project_id": p["project_id"], "label": p["label"],
                "source": p["source"], "confidence": p["confidence"],
                "cost_usd": 0.0, "priced_tokens": 0, "unpriced_tokens": 0,
                "unpriced_events": 0, "sessions": 0, "runtimes": []})
            for k in ("cost_usd", "priced_tokens", "unpriced_tokens", "unpriced_events"):
                row[k] += s[k]
                totals[k] += s[k]
            row["sessions"] += 1
            totals["sessions"] += 1
            rt = _runtime_of_session_id(str(sid or ""), "openclaw")
            if rt not in row["runtimes"]:
                row["runtimes"].append(rt)
            if p["source"] == "assigned":
                totals["assigned_cost_usd"] += s["cost_usd"]
            elif p["project_id"] == _pa.UNASSIGNED_ID:
                totals["unassigned_cost_usd"] += s["cost_usd"]
                totals["unassigned_sessions"] += 1
            else:
                totals["derived_cost_usd"] += s["cost_usd"]
        rows = list(by_project.values())
        seen: dict[str, int] = {}
        for r in rows:
            seen[r["label"]] = seen.get(r["label"], 0) + 1
        for r in rows:
            r["cost_usd"] = round(r["cost_usd"], 6)
            r["runtimes"].sort()
            if seen[r["label"]] > 1 and r["project_id"] != _pa.UNASSIGNED_ID:
                # Same last path segment, different repositories: keep them
                # visibly apart instead of letting two rows read as one.
                r["label"] = f"{r['label']} ({r['project_id'][-4:]})"
        rows.sort(key=lambda r: (r["project_id"] == _pa.UNASSIGNED_ID, -r["cost_usd"], r["label"]))
        for k in ("cost_usd", "derived_cost_usd", "assigned_cost_usd", "unassigned_cost_usd"):
            totals[k] = round(totals[k], 6)
        all_tokens = totals["priced_tokens"] + totals["unpriced_tokens"]
        totals["completeness"] = {
            # Share of tokens that carried a price. Below 1.0 the cost totals
            # are a floor, not a total.
            "priced_token_share": (round(totals["priced_tokens"] / all_tokens, 4)
                                   if all_tokens else None),
            # Share of spend attributed to some project rather than Unassigned.
            "attributed_cost_share": (round(1 - totals["unassigned_cost_usd"] / totals["cost_usd"], 4)
                                      if totals["cost_usd"] > 0 else None),
        }
        return {"available": True, "basis": _pa.BASIS_ESTIMATED, "currency": "USD",
                "window": {"days": n_days, "since": _iso(since_e), "until": _iso(now_e)},
                "projects": rows, "totals": totals}

    # ── assignments ───────────────────────────────────────────────────────

    def add_project_assignment(self, match_type: str = "", match_value: str = "",
                               project_name: str = "", reason: str = "",
                               effective_from: str | None = None,
                               effective_to: str | None = None,
                               actor: str = "") -> dict[str, Any]:
        """Record one assignment. Never updates or deletes an earlier one."""
        clean, err = _pa.validate_assignment({
            "match_type": match_type, "match_value": match_value,
            "project_name": project_name, "reason": reason,
            "effective_from": effective_from, "effective_to": effective_to})
        if err:
            return _fail(err)
        if clean["match_type"] == "project":
            if clean["match_value"] not in self._project_catalog():
                return _fail("unknown project: no session on this machine belongs to it")
        else:
            try:
                found = self._fetch("SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1",
                                    [clean["match_value"]])
            except Exception:  # noqa: BLE001
                found = []
            if not found:
                return _fail("unknown session")
        if getattr(self, "_read_only", False):
            return _fail("store is read-only in this process")
        row = dict(clean, assignment_id="pa_" + uuid.uuid4().hex[:16],
                   actor=str(actor or "")[:120], created_at=int(time.time() * 1000))
        with self._write_lock:
            self._conn.execute(
                "INSERT INTO project_assignments (assignment_id, match_type, match_value, "
                "project_name, effective_from, effective_to, actor, reason, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [row["assignment_id"], row["match_type"], row["match_value"],
                 row["project_name"], row["effective_from"], row["effective_to"],
                 row["actor"], row["reason"], row["created_at"]])
        row["project_id"] = _pa.assigned_project_id(row["project_name"])
        return {"ok": True, "assignment": row}

    def query_project_assignments(self) -> list[dict]:
        rows = _pa.annotate_superseded(self._project_assignment_rows())
        for r in rows:
            r["project_id"] = _pa.assigned_project_id(r.get("project_name"))
        rows.sort(key=lambda r: (-(r.get("created_at") or 0), r.get("assignment_id") or ""))
        return rows

    # ── budgets ───────────────────────────────────────────────────────────

    def upsert_project_budget(self, project_id: str = "", amount: Any = None,
                              currency: str = "", period: str = "",
                              timezone_name: str = "", basis: str = "",
                              actor: str = "") -> dict[str, Any]:
        """One budget per project. Re-posting replaces its terms; alerts
        already recorded for a period stay recorded."""
        clean, err = _pa.validate_budget({
            "project_id": project_id, "amount": amount, "currency": currency,
            "period": period, "timezone": timezone_name, "basis": basis})
        if err:
            return _fail(err)
        if clean["project_id"] not in self._project_catalog():
            return _fail("unknown project: no session on this machine belongs to it")
        if getattr(self, "_read_only", False):
            return _fail("store is read-only in this process")
        now_ms = int(time.time() * 1000)
        budget_id = "pb_" + clean["project_id"].split("_", 1)[1]
        with self._write_lock:
            self._conn.execute("""
                INSERT INTO project_budgets (budget_id, project_id, amount, currency,
                    period, timezone, basis, actor, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (budget_id) DO UPDATE SET
                    amount = excluded.amount, currency = excluded.currency,
                    period = excluded.period, timezone = excluded.timezone,
                    basis = excluded.basis, actor = excluded.actor,
                    updated_at = excluded.updated_at
            """, [budget_id, clean["project_id"], clean["amount"], clean["currency"],
                  clean["period"], clean["timezone"], clean["basis"],
                  str(actor or "")[:120], now_ms, now_ms])
        budgets = {b["budget_id"]: b for b in self.query_project_budgets()}
        return {"ok": True, "budget": budgets.get(budget_id)}

    def delete_project_budget(self, budget_id: str = "") -> dict[str, Any]:
        bid = str(budget_id or "").strip()
        if not bid:
            return _fail("budget_id is required")
        if getattr(self, "_read_only", False):
            return _fail("store is read-only in this process")
        with self._write_lock:
            n = self._conn.execute(
                "SELECT COUNT(*) FROM project_budgets WHERE budget_id = ?", [bid]).fetchone()[0]
            self._conn.execute("DELETE FROM project_budgets WHERE budget_id = ?", [bid])
        return {"ok": True, "deleted": int(n or 0)}

    def query_project_budgets(self) -> list[dict]:
        try:
            rows = self._fetch(
                "SELECT budget_id, project_id, amount, currency, period, timezone, basis, "
                "actor, created_at, updated_at FROM project_budgets ORDER BY budget_id", [])
        except Exception:  # noqa: BLE001
            return []
        cols = ["budget_id", "project_id", "amount", "currency", "period", "timezone",
                "basis", "actor", "created_at", "updated_at"]
        return [dict(zip(cols, r)) for r in rows]

    def _budget_periods(self, budget: dict, now_e: float):
        tz = _pa.resolve_timezone(budget["timezone"])
        cur = _pa.period_bounds(budget["period"], tz, now_e)
        prev = _pa.previous_period_bounds(budget["period"], tz, now_e)
        return tz, cur, prev

    def project_budget_status(self, now: float | None = None) -> dict[str, Any]:
        """Each budget with its current period's spend, percentage, thresholds
        crossed, daily burn and recorded alerts."""
        now_e = float(now) if now is not None else time.time()
        budgets = self.query_project_budgets()
        if not budgets:
            return {"available": True, "budgets": [], "notice": _pa.ENFORCEMENT_NOTICE}
        prepared = []
        earliest = now_e
        for b in budgets:
            try:
                tz, cur, prev = self._budget_periods(b, now_e)
            except ValueError:
                prepared.append((b, None, None, None))
                continue
            prepared.append((b, tz, cur, prev))
            earliest = min(earliest, prev[0].timestamp())
        try:
            buckets = self._project_usage_buckets(earliest, now_e + 1)
        except Exception:  # noqa: BLE001
            return {"available": False, "reason": "store_query_failed", "budgets": []}
        projects_of = self._resolve_projects(list({b["session_id"] for b in buckets}))
        # A session belongs to the project it resolves to AND to the
        # repository/directory it ran in. Otherwise a budget set on a
        # repository silently reads $0 (and never alerts) the moment that
        # repository is assigned to a named project. A session is still
        # counted at most once per budget: membership is a set.
        sessions_by_project: dict[str, set] = {}
        for sid, p in projects_of.items():
            sessions_by_project.setdefault(p["project_id"], set()).add(sid)
            derived_id = p.get("derived_project_id")
            if derived_id and derived_id != p["project_id"]:
                sessions_by_project.setdefault(derived_id, set()).add(sid)
        catalog = self._project_catalog()
        alerts = self.query_project_budget_alerts(limit=1000)
        out = []
        for b, tz, cur, prev in prepared:
            label = (catalog.get(b["project_id"]) or {}).get("label") or b["project_id"]
            row = dict(b, label=label, enforcement="none", notice=_pa.ENFORCEMENT_NOTICE)
            if tz is None:
                row.update(available=False, reason="timezone_unresolvable")
                out.append(row)
                continue
            members = sessions_by_project.get(b["project_id"], set())
            cur_sum = _pa.summarize_buckets(buckets, cur[0], cur[1], tz, sessions=members)
            prev_sum = _pa.summarize_buckets(buckets, prev[0], prev[1], tz, sessions=members)
            spent = cur_sum["spent_usd"]
            amount = float(b["amount"] or 0.0)
            period_start = cur[0].isoformat()
            # Named projects this budget's spend is now reported under, so a
            # repository budget next to a "Billing" row explains itself.
            reported_under = sorted({
                projects_of[s]["label"] for s in members
                if s in projects_of and projects_of[s]["project_id"] != b["project_id"]})
            row.update(
                available=True,
                reported_under=reported_under,
                period_start=period_start, period_end=cur[1].isoformat(),
                spent_usd=spent,
                pct_used=round(spent / amount * 100.0, 2) if amount > 0 else None,
                thresholds=list(_pa.THRESHOLDS),
                thresholds_crossed=_pa.crossed_thresholds(spent, amount),
                unpriced_tokens=cur_sum["unpriced_tokens"],
                unpriced_events=cur_sum["unpriced_events"],
                burn=_pa.burn_series(cur_sum["by_day"], cur[0],
                                     datetime.fromtimestamp(now_e, timezone.utc), tz),
                previous_period={"period_start": prev[0].isoformat(),
                                 "period_end": prev[1].isoformat(),
                                 "spent_usd": prev_sum["spent_usd"],
                                 "thresholds_crossed": _pa.crossed_thresholds(prev_sum["spent_usd"], amount)},
                alerts=[a for a in alerts if a["budget_id"] == b["budget_id"]
                        and a["period_start"] == period_start],
            )
            out.append(row)
        return {"available": True, "budgets": out, "notice": _pa.ENFORCEMENT_NOTICE}

    def evaluate_project_budgets(self, now: float | None = None) -> list[dict]:
        """Latch every threshold newly crossed. Returns only the alerts this
        call recorded, so a caller delivers each exactly once.

        The previous period is re-checked so a record that arrived late still
        raises the alert for the period it belongs to (marked ``late``), but
        only when the budget already existed during that period: a budget
        created today does not retroactively alert on last month."""
        if getattr(self, "_read_only", False):
            return []
        status = self.project_budget_status(now=now)
        fired: list[dict] = []
        for b in status.get("budgets") or []:
            if not b.get("available"):
                continue
            amount = float(b.get("amount") or 0.0)
            checks = [(b["period_start"], b["spent_usd"], b["thresholds_crossed"], False)]
            prev = b.get("previous_period") or {}
            created_e = (b.get("created_at") or 0) / 1000.0
            prev_end_e = _pa.to_epoch(prev.get("period_end"))
            if prev and prev_end_e is not None and created_e < prev_end_e:
                checks.append((prev["period_start"], prev["spent_usd"],
                               prev["thresholds_crossed"], True))
            for period_start, spent, crossed, late in checks:
                for pct in crossed:
                    with self._write_lock:
                        exists = self._conn.execute(
                            "SELECT 1 FROM project_budget_alerts WHERE budget_id = ? "
                            "AND period_start = ? AND threshold_pct = ?",
                            [b["budget_id"], period_start, pct]).fetchone()
                        if exists:
                            continue
                        self._conn.execute(
                            "INSERT INTO project_budget_alerts (budget_id, period_start, "
                            "threshold_pct, project_id, spent_usd, amount, fired_at, late) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            [b["budget_id"], period_start, pct, b["project_id"],
                             round(spent, 6), amount, int(time.time() * 1000), late])
                    fired.append({
                        "budget_id": b["budget_id"], "project_id": b["project_id"],
                        "label": b.get("label"), "period": b["period"],
                        "period_start": period_start, "threshold_pct": pct,
                        "spent_usd": round(spent, 6), "amount": amount,
                        "currency": b["currency"], "basis": b["basis"], "late": late,
                        "message": budget_alert_message(b.get("label"), pct, spent,
                                                        amount, b["period"], late),
                    })
        return fired

    def query_project_budget_alerts(self, limit: int = 200) -> list[dict]:
        try:
            lim = max(1, min(5000, int(limit)))
        except (TypeError, ValueError):
            lim = 200
        try:
            rows = self._fetch(
                "SELECT budget_id, period_start, threshold_pct, project_id, spent_usd, "
                "amount, fired_at, late FROM project_budget_alerts "
                "ORDER BY fired_at DESC, threshold_pct DESC LIMIT ?", [lim])
        except Exception:  # noqa: BLE001
            return []
        cols = ["budget_id", "period_start", "threshold_pct", "project_id",
                "spent_usd", "amount", "fired_at", "late"]
        return [dict(zip(cols, r)) for r in rows]


_PERIOD_WORD = {"day": "daily", "week": "weekly", "month": "monthly"}


def budget_alert_message(label: Any, pct: int, spent: float, amount: float,
                         period: str, late: bool) -> str:
    when = "last " + period if late else "this " + period
    return (f"Project {label or 'unnamed'} has used {int(pct)}% of its "
            f"${amount:,.2f} {_PERIOD_WORD.get(period, period)} budget "
            f"(${spent:,.2f} at published rates {when}). {_pa.ENFORCEMENT_NOTICE}")
