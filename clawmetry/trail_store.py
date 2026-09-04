"""Trail store methods: session intent, typed-event back-fill, per-session git join.

These are the read/write methods behind the Session Trail's "What it was
asked" and "How it ended" panels. They live in their own mixin, mixed into
:class:`clawmetry.local_store.LocalStore`, so the store module (already the
largest file in the package) does not grow further and so the whole feature
is readable in one place.

Everything here runs on the store's own connection (``self._conn``) under
``self._write_lock`` / ``self._txn``; nothing opens a second handle. The
methods are allow-listed for the daemon proxy in ``routes/local_query.py`` so
the dashboard process reads them without touching DuckDB directly.
"""
from __future__ import annotations

import logging
from typing import Any

from clawmetry import ccr as _ccr
from clawmetry import event_shape as _event_shape

log = logging.getLogger("clawmetry.trail_store")


def _clean_intent(value: Any) -> str | None:
    """Redact + cap a prompt for ``sessions.intent`` (delegates to the store
    module so ingest and back-fill apply one definition)."""
    from clawmetry.local_store import _clean_intent as _impl  # late: avoids a cycle
    return _impl(value)


def _txn(conn):
    """Store transaction context manager (delegates to the store module)."""
    from clawmetry.local_store import _txn as _impl  # late: avoids a cycle
    return _impl(conn)


class TrailStoreMixin:
    """Session-intent, typed-event back-fill and per-session git-outcome reads.

    Mixed into ``LocalStore``; expects ``self._conn``, ``self._write_lock``,
    ``self._txn``, ``self._fetch``, ``self._read_only`` and
    ``self.query_git_repos`` from the host class.
    """

    def update_session_intent(
        self,
        session_id: str,
        intent: str | None,
        *,
        source: str = "events",
    ) -> bool:
        """Set ``sessions.intent`` for a session that has none yet.

        First wins: a row whose intent is already set is left alone, so a
        re-ingest can never swap the opening prompt for a later one. The
        text is redacted + capped by ``_clean_intent``. Returns True when a
        row changed. No row / empty intent returns False rather than
        raising (the caller is an ingest loop).
        """
        text = _clean_intent(intent)
        if not session_id or not text:
            return False
        if self._read_only:
            raise RuntimeError(
                "local_store: update_session_intent() called on read-only store"
            )
        with self._write_lock, _txn(self._conn):
            before = self._conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE session_id = ? "
                "AND intent IS NULL", [str(session_id)],
            ).fetchone()[0]
            if not before:
                return False
            self._conn.execute(
                "UPDATE sessions SET intent = ?, intent_source = ? "
                "WHERE session_id = ? AND intent IS NULL",
                [text, str(source or "events")[:32], str(session_id)],
            )
        return True

    def get_session_intent(self, session_id: str) -> dict[str, Any]:
        """``{session_id, intent, intent_source}`` for one session (empty
        strings when unknown). Read by the transcript API."""
        out = {"session_id": str(session_id or ""), "intent": "",
               "intent_source": ""}
        if not session_id:
            return out
        try:
            rows = self._fetch(
                "SELECT intent, intent_source FROM sessions "
                "WHERE session_id = ? LIMIT 1", [str(session_id)])
        except Exception:
            return out
        if rows:
            out["intent"] = str(rows[0][0] or "")
            out["intent_source"] = str(rows[0][1] or "")
        return out

    def query_session_intents(self, *, limit: int = 2000) -> dict[str, str]:
        """``{session_id: intent}`` for the most recently active sessions
        that have one. Used by the cloud snapshot builder to seal the intent
        into the encrypted sessions slice in one query per pass."""
        try:
            rows = self._fetch(
                "SELECT session_id, intent FROM sessions "
                "WHERE intent IS NOT NULL AND intent <> '' "
                "ORDER BY COALESCE(last_active_at, started_at) DESC NULLS LAST "
                "LIMIT ?", [int(limit)])
        except Exception:
            return {}
        return {str(r[0]): str(r[1]) for r in rows if r[0]}

    def backfill_event_shapes(self, *, limit: int = 500) -> int:
        """Classify up to ``limit`` events whose typed columns are still
        NULL (rows written before schema v15). One bounded batch per call
        so the daemon tick stays inside the FLYWHEEL 1e CPU budget; newest
        rows first because those are the ones on screen. Every visited row
        gets a non-NULL ``block_kind`` (``other`` when nothing fits), so the
        scan never revisits a row. Returns rows updated.
        """
        if self._read_only:
            return 0
        limit = max(1, min(int(limit), 5000))
        with self._write_lock:
            try:
                rows = self._conn.execute(
                    "SELECT id, event_type, data FROM events "
                    "WHERE block_kind IS NULL "
                    "ORDER BY created_at DESC LIMIT ?", [limit],
                ).fetchall()
            except Exception:
                log.debug("local store: typed-event back-fill read failed",
                          exc_info=True)
                return 0
            if not rows:
                return 0
            params: list[list[Any]] = []
            for eid, et, raw in rows:
                data: Any = raw
                if raw is not None:
                    try:
                        data = _ccr.maybe_decompress(raw)
                    except Exception:
                        data = raw
                shape = _event_shape.classify(et, data)
                params.append([
                    shape["role"] or None,
                    shape["block_kind"] or "other",
                    shape["tool_name"] or None,
                    bool(shape["is_error"]),
                    str(eid),
                ])
            try:
                with _txn(self._conn):
                    self._conn.executemany(
                        "UPDATE events SET role = ?, block_kind = ?, "
                        "tool_name = ?, is_error = ? WHERE id = ?", params,
                    )
            except Exception:
                log.debug("local store: typed-event back-fill write failed",
                          exc_info=True)
                return 0
        return len(params)

    def backfill_session_intents(self, *, limit: int = 25) -> int:
        """Fill ``sessions.intent`` for up to ``limit`` sessions that have
        events but no intent yet. Reads the earliest user turns of each
        (bounded), takes the first real human prompt, redacts + caps it.
        A session with events and no human prompt is stamped
        ``intent_source='none'`` so it is not re-scanned every tick; a
        session with no events at all is skipped (it may still arrive).
        Returns sessions updated.
        """
        if self._read_only:
            return 0
        limit = max(1, min(int(limit), 500))
        with self._write_lock:
            try:
                sids = self._conn.execute(
                    "SELECT s.session_id FROM sessions s "
                    "WHERE s.intent IS NULL AND s.intent_source IS NULL "
                    "  AND EXISTS (SELECT 1 FROM events e "
                    "              WHERE e.session_id = s.session_id) "
                    "ORDER BY COALESCE(s.last_active_at, s.started_at) "
                    "         DESC NULLS LAST LIMIT ?", [limit],
                ).fetchall()
            except Exception:
                log.debug("local store: intent back-fill read failed",
                          exc_info=True)
                return 0
            if not sids:
                return 0
            updates: list[list[Any]] = []
            for (sid,) in sids:
                sid = str(sid or "")
                if not sid:
                    continue
                try:
                    evs = self._conn.execute(
                        "SELECT event_type, data, ts FROM events "
                        "WHERE session_id = ? "
                        "  AND (role = 'user' OR role IS NULL) "
                        "ORDER BY ts ASC LIMIT 60", [sid],
                    ).fetchall()
                except Exception:
                    continue
                rows = []
                for et, raw, ts in evs:
                    data: Any = raw
                    if raw is not None:
                        try:
                            data = _ccr.maybe_decompress(raw)
                        except Exception:
                            data = raw
                    rows.append({"event_type": et, "data": data, "ts": ts})
                text = _clean_intent(_event_shape.first_user_prompt(rows))
                if text:
                    updates.append([text, "events", sid])
                else:
                    updates.append([None, "none", sid])
            if not updates:
                return 0
            try:
                with _txn(self._conn):
                    self._conn.executemany(
                        "UPDATE sessions SET intent = ?, intent_source = ? "
                        "WHERE session_id = ? AND intent IS NULL", updates,
                    )
            except Exception:
                log.debug("local store: intent back-fill write failed",
                          exc_info=True)
                return 0
        return sum(1 for u in updates if u[0])

    def query_session_git_outcomes(self, *, session_id: str) -> dict[str, Any]:
        """Per-session view of the git outcome tables: the commits the
        correlator linked to this session, each with its merged verdict, the
        pull request that carried it when the code host answered, and the
        confidence + basis the link rests on.

        Reads only what ``ingest_git_scan`` already persisted; no git command
        runs here. ``available`` is False when no scan has reached a
        repository yet (distinct from "scanned, nothing linked").
        """
        sid = str(session_id or "").strip()
        out: dict[str, Any] = {
            "session_id": sid, "available": False, "commits": [], "prs": [],
            "counts": {"commits": 0, "merged": 0, "prs": 0, "prs_merged": 0},
            "repos": [],
        }
        if not sid:
            return out
        try:
            repos = self.query_git_repos()
        except Exception:
            repos = []
        if not repos:
            out["reason"] = "no_repositories_scanned"
            return out
        out["available"] = True
        try:
            lrows = self._fetch(
                "SELECT l.repo_root, l.sha, l.confidence, l.basis, "
                "       l.matched_branch, c.subject, c.authored_at, "
                "       c.author_name, c.merged, c.branch_hint, c.is_revert, "
                "       c.insertions, c.deletions, c.files_changed "
                "FROM git_session_commits l "
                "LEFT JOIN git_commits c "
                "  ON c.repo_root = l.repo_root AND c.sha = l.sha "
                "WHERE l.session_id = ? "
                "ORDER BY c.authored_at ASC NULLS LAST, l.sha", [sid])
        except Exception:
            lrows = []
        if not lrows:
            return out
        roots = sorted({str(r[0]) for r in lrows if r[0]})
        repo_meta = {r["repo_root"]: r for r in repos}
        out["repos"] = [
            {"repo_root": root,
             "name": str((repo_meta.get(root) or {}).get("name") or ""),
             "default_branch": str((repo_meta.get(root) or {}).get("default_branch") or ""),
             "merge_basis": str((repo_meta.get(root) or {}).get("merge_basis") or ""),
             "pr_basis": str((repo_meta.get(root) or {}).get("pr_basis") or "")}
            for root in roots
        ]
        prrows: list = []
        if roots:
            ph = ", ".join("?" * len(roots))
            try:
                prrows = self._fetch(
                    "SELECT repo_root, number, state, title, url, merged_at, "
                    "       head_branch, base_branch, merge_commit, basis "
                    f"FROM git_pull_requests WHERE repo_root IN ({ph})", roots)
            except Exception:
                prrows = []
        pr_by_commit: dict[tuple, dict] = {}
        pr_by_branch: dict[tuple, dict] = {}
        for root, num, state, title, url, merged_at, head, base, mc, basis in prrows:
            pr = {"number": int(num), "state": str(state or ""),
                  "title": str(title or ""), "url": str(url or ""),
                  "merged_at": int(merged_at or 0),
                  "head_branch": str(head or ""), "base_branch": str(base or ""),
                  "merge_commit": str(mc or ""), "basis": str(basis or ""),
                  "repo_root": str(root)}
            if mc:
                pr_by_commit[(str(root), str(mc))] = pr
            if head:
                pr_by_branch[(str(root), str(head))] = pr
        commits: list[dict[str, Any]] = []
        prs: dict[tuple, dict] = {}
        for (root, sha, conf, basis, mbranch, subject, authored, author,
             merged, bhint, revert, ins, dels, files) in lrows:
            root, sha = str(root or ""), str(sha or "")
            pr = pr_by_commit.get((root, sha))
            if pr is None and bhint:
                pr = pr_by_branch.get((root, str(bhint)))
            if pr is not None:
                prs.setdefault((root, pr["number"]), dict(pr))
            commits.append({
                "repo_root": root,
                "sha": sha,
                "subject": str(subject or ""),
                "authored_at": int(authored or 0),
                "author": str(author or ""),
                # None stays None: "could not judge" is not "did not ship".
                "merged": (bool(merged) if merged is not None else None),
                "branch": str(bhint or mbranch or ""),
                "is_revert": bool(revert),
                "insertions": int(ins or 0),
                "deletions": int(dels or 0),
                "files_changed": int(files or 0),
                "confidence": str(conf or ""),
                "basis": str(basis or ""),
                "pr_number": (pr["number"] if pr else None),
                "pr_state": (pr["state"] if pr else ""),
            })
        out["commits"] = commits
        out["prs"] = sorted(prs.values(), key=lambda p: p["number"])
        out["counts"] = {
            "commits": len(commits),
            "merged": sum(1 for c in commits if c["merged"] is True),
            "prs": len(out["prs"]),
            "prs_merged": sum(1 for p in out["prs"] if p.get("merged_at")),
        }
        return out

    def query_session_git_counts(self, *, limit: int = 5000) -> dict[str, dict[str, int]]:
        """``{session_id: {commits, prs}}`` for every linked session, one
        query. Plaintext counts only (no subjects), safe for the cloud row."""
        try:
            rows = self._fetch(
                "SELECT l.session_id, COUNT(DISTINCT l.sha), "
                "       COUNT(DISTINCT p.number) "
                "FROM git_session_commits l "
                "LEFT JOIN git_commits c "
                "  ON c.repo_root = l.repo_root AND c.sha = l.sha "
                "LEFT JOIN git_pull_requests p "
                "  ON p.repo_root = l.repo_root "
                " AND (p.merge_commit = l.sha "
                "      OR (c.branch_hint IS NOT NULL AND c.branch_hint <> '' "
                "          AND p.head_branch = c.branch_hint)) "
                "GROUP BY l.session_id LIMIT ?", [int(limit)])
        except Exception:
            return {}
        return {str(r[0]): {"commits": int(r[1] or 0), "prs": int(r[2] or 0)}
                for r in rows if r[0]}
