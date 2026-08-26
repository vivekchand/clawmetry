"""``bp_readiness`` — repo AI-readiness.

Before you blame the agent, look at what you handed it.

One read-only endpoint scores a code repository on how legible it is to an
agent (instruction file, test command, build command, lint gate, CI config,
skills) and pairs the grade with the stuck-loop and repeated-tool-failure
counts the detectors recorded for sessions that actually ran in that repo.

    GET /api/repo-readiness[?path=<dir>][&runtime=<rt>][&days=30]

Free and ungated on purpose: this is the cheapest honest thing ClawMetry can
tell a first-time user about their own repo, and every input is a filesystem
fact plus data already in DuckDB. No entitlement gate, no network call.

Repo discovery comes from ``sessions.cwd`` (the directory each session
actually ran in) folded up to the nearest git root, so the list is "repos your
agents worked in", never a filesystem crawl of the user's home directory.
"""
from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, request

logger = logging.getLogger("clawmetry.routes.readiness")

bp_readiness = Blueprint("readiness", __name__)

#: Default correlation window. Long enough that a weekly-cadence repo has
#: history, short enough that a repo you fixed three months ago is not still
#: being judged by its old stuck rate.
_DEFAULT_DAYS = 30

#: How many repos the picker offers. The scorer only ever runs on ONE of
#: them per request (scoring is cheap but not free, and a 200-repo machine
#: should not pay for 200 scans to render one card).
_MAX_REPOS = 25


def _repo_activity(days: int) -> list:
    """Session/loop-signal rows from DuckDB. ``[]`` when unavailable.

    Routed through the daemon HTTP proxy first: the daemon owns the DuckDB
    writer lock, so a direct open from the dashboard process contends with
    it. The direct read is a single-process fallback for tests and dev.
    """
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon(
            "query_repo_activity", since_days=days, limit=5000)
        if isinstance(rows, list):
            return rows
    except Exception as exc:
        logger.debug("repo-readiness: daemon proxy unavailable: %s", exc)
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        if store is None:
            return []
        return store.query_repo_activity(since_days=days, limit=5000) or []
    except Exception as exc:
        logger.debug("repo-readiness: direct store read failed: %s", exc)
        return []


def _fallback_repo() -> "str | None":
    """A repo to score when no session recorded a cwd yet.

    Acceptance criterion: the score must render for a repo with no ClawMetry
    history at all. On a fresh install ``sessions.cwd`` is empty, so we fall
    back to the git root of the directory the dashboard itself is running in.
    Returns ``None`` rather than a guess when that is not a repo.

    NEVER on the hosted dashboard. The cloud container runs from ClawMetry's
    OWN checkout, so this fallback there would score our source tree and
    label it as the user's repo -- a fabricated card about a repo they have
    never seen. On cloud the honest answer is "this machine has not uploaded
    a scan yet"; the card is served from the daemon's ``repoReadiness``
    snapshot slice, scanned where the agents actually run.
    """
    if os.environ.get("CLAWMETRY_CLOUD", "").strip():
        return None
    from clawmetry import repo_readiness
    try:
        cwd = os.getcwd()
    except OSError:
        return None
    return repo_readiness.git_root(cwd)


def readiness_payload(path: str = "", runtime: str = "",
                      days: int = _DEFAULT_DAYS) -> dict:
    """Build the endpoint body. Shared with the daemon snapshot builder so
    the hosted dashboard renders the same card. Never raises."""
    from clawmetry import repo_readiness

    try:
        days = max(0, min(int(days), 365))
    except (TypeError, ValueError):
        days = _DEFAULT_DAYS
    runtime = (runtime or "").strip().lower()
    if runtime in ("", "all", "any"):
        runtime = ""

    rows = _repo_activity(days)
    repos = repo_readiness.rank_repos(rows, window_days=days, limit=_MAX_REPOS)

    requested = (path or "").strip()
    selected_path = ""
    if requested:
        selected_path = os.path.abspath(os.path.expanduser(requested))
    elif repos:
        # The busiest repo that still exists on this machine; a deleted
        # checkout keeps its history row but cannot be scored.
        live = [r for r in repos if r["exists"]]
        selected_path = (live or repos)[0]["path"]
    else:
        selected_path = _fallback_repo() or ""

    signals = None
    for r in repos:
        if r["path"] == selected_path:
            signals = r["signals"]
            break
    if signals is None and selected_path:
        # A repo with no ClawMetry history: an explicit empty pairing, not a
        # fabricated zero stuck rate.
        signals = repo_readiness.pair_signals([], window_days=days)

    if not selected_path:
        return {
            "status": "no_repo",
            "detail": "No agent session on this machine has recorded the "
                      "directory it ran in yet, and the dashboard is not "
                      "running inside a git repo either.",
            "repos": [], "report": None, "window_days": days,
            "runtime": runtime or "all",
        }

    report = repo_readiness.score_repo(
        selected_path, runtime=runtime or None, signals=signals)
    return {
        "status": "ok",
        "repos": repos,
        "report": report,
        "window_days": days,
        "runtime": runtime or "all",
        # Local scans honour the runtime switcher, so the card needs no
        # "all runtimes" caveat. The DAEMON's snapshot slice sets
        # scope="all_runtimes" instead, and the renderer labels that.
        "scope": runtime or "all_runtimes",
        "discovery": "sessions" if repos else "cwd",
    }


@bp_readiness.route("/api/repo-readiness", methods=["GET"])
def http_repo_readiness():
    """Score one repo and list the repos this machine's agents work in.

    Free and ungated: no ``@gate``, by design (WO-5). Never 500s -- an
    honest empty state beats a broken card on a first-run dashboard.
    """
    try:
        return jsonify(readiness_payload(
            path=request.args.get("path") or "",
            runtime=request.args.get("runtime") or "",
            days=request.args.get("days") or _DEFAULT_DAYS,
        ))
    except Exception as exc:  # noqa: BLE001 — never break the tab
        logger.warning("repo-readiness failed: %s", exc)
        return jsonify({
            "status": "error", "detail": str(exc), "repos": [],
            "report": None, "window_days": _DEFAULT_DAYS, "runtime": "all",
        })
