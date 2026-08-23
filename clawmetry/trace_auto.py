"""Automatic PR tracing: capture, publish and comment, with no command.

CLAUDE.md: "users should never need to configure anything manually." A trace
that requires somebody to remember a command is a trace that does not happen,
and because coverage cannot be backfilled, a trace that does not happen is
gone permanently. So the only manual act is `clawmetry trace init --auto`,
once per repository. After that `git push` does the rest.

The trigger is a ``pre-push`` hook rather than the sync daemon. The daemon is
the more natural home and may take this over later, but push is the moment
where everything needed is already true: the commits exist, the branch is
known, and the pull request either exists or is about to. Watching for it from
a background process would add a polling loop to learn something git already
tells us at exactly the right instant.

What is automatic and what is not
---------------------------------
Capture is automatic. Publishing is automatic **only where the repository
owner declared it**, because publishing writes a public page containing the
contents of somebody's terminal. That distinction is the CLAUDE.md control
plane rule: a write is fine when it is "user-initiated or declared in a policy
the user wrote". Opting in once per repository is such a policy. Publishing
silently on a repository nobody opted in would be a surprise write.

This is not theoretical caution. The first real bundle captured during
development carried the project's pricing strategy and eight live Stripe
identifiers, from a session that had merely read a deploy file. Silent
publishing would have put that on the open internet with nobody looking.

The comment
-----------
A trace nobody sees is not worth capturing, so the run posts a comment on the
pull request carrying the link. It follows the convention Drift Bot already
established in this project: a hidden marker identifies the comment, and
subsequent runs EDIT it rather than appending. A bot that comments on every
push is a bot people mute.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess

from clawmetry import trace_capture

logger = logging.getLogger("clawmetry.trace_auto")

#: Identifies our comment so repeat runs update rather than append, the same
#: way `<!-- sofa-driftbot -->` does.
COMMENT_MARKER = "<!-- clawmetry-trace -->"

#: git-config keys. Per repository, travelling with the clone, inspectable
#: with `git config --get`, and leaving no global state behind on a machine
#: that works on twenty projects.
CFG_AUTO = "clawmetry.autopublish"
CFG_COMMENT = "clawmetry.autocomment"


def _git(repo: str, *args: str) -> str:
    try:
        out = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                             text=True, timeout=30, check=False)
        return out.stdout or ""
    except Exception as exc:
        logger.debug("git %s failed: %s", " ".join(args), exc)
        return ""


def _flag(repo: str, key: str, default: bool = False) -> bool:
    val = _git(repo, "config", "--get", key).strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


def set_policy(repo: str, *, publish: bool, comment: bool = True) -> None:
    """Record the per-repository policy. This is the one manual act."""
    subprocess.run(["git", "config", CFG_AUTO, "true" if publish else "false"],
                   cwd=repo, check=False, timeout=30)
    subprocess.run(["git", "config", CFG_COMMENT, "true" if comment else "false"],
                   cwd=repo, check=False, timeout=30)


# ── the comment ────────────────────────────────────────────────────────────

def _gh_available() -> bool:
    try:
        out = subprocess.run(["gh", "auth", "status"], capture_output=True,
                             text=True, timeout=25, check=False)
        return out.returncode == 0
    except Exception:
        return False


def render_comment(bundle: dict, url: str) -> str:
    """The comment body. Short on purpose: a reviewer wants the link and
    enough context to decide whether to click, not a report."""
    s = bundle.get("summary") or {}
    attr = bundle.get("attribution") or "heuristic"
    cost = s.get("cost_usd") or 0
    cost_txt = f"${cost:,.2f}"
    if s.get("cost_is_upper_bound"):
        cost_txt += " (upper bound)"
    models = s.get("models") or {}
    total = sum(models.values()) or 1
    model_txt = " · ".join(
        f"{n} ({round(100 * c / total)}%)"
        for n, c in sorted(models.items(), key=lambda kv: -kv[1])[:3]
    ) or "no model recorded"

    note = {
        "exact": "",
        "shared": ("\n\n> This session also produced work outside this pull "
                   "request, so the cost above is an upper bound rather than a "
                   "figure."),
        "heuristic": ("\n\n> No commit here named its session, so the sessions "
                      "were inferred from authorship and timing. Treat this as "
                      "a hint, not a measurement."),
    }.get(attr, "")

    return (
        f"**🦞 ClawMetry: what the agent was asked to do**\n\n"
        f"[View the trace]({url})\n\n"
        f"| prompts | turns | tools | cost | attribution |\n"
        f"|---|---|---|---|---|\n"
        f"| {s.get('prompts', 0)} | {s.get('turns', 0)} | {s.get('tools', 0)} "
        f"| {cost_txt} | `{attr}` |\n\n"
        f"{model_txt}{note}\n\n"
        f"{COMMENT_MARKER}"
    )


def post_comment(repo: str, pr: str, body: str) -> dict:
    """Post or update the trace comment on ``pr``.

    Uses the developer's own ``gh`` credentials. The GitHub App will take this
    over and post as a bot, which is better (revocable, legible, not attributed
    to a human who did not write it), but the App is not required for this to
    work today and waiting for it would mean the link goes nowhere.

    Updates in place via the marker rather than appending, so a branch pushed
    ten times has one comment and not ten.
    """
    if not _gh_available():
        return {"ok": False, "error": "gh is not installed or not authenticated"}
    try:
        listing = subprocess.run(
            ["gh", "pr", "view", str(pr), "--json", "comments"],
            cwd=repo, capture_output=True, text=True, timeout=60, check=False)
        existing = None
        if listing.returncode == 0:
            for c in (json.loads(listing.stdout or "{}").get("comments") or []):
                if COMMENT_MARKER in (c.get("body") or ""):
                    existing = c.get("url")
                    break
        if existing:
            out = subprocess.run(
                ["gh", "pr", "comment", str(pr), "--edit-last", "--body", body],
                cwd=repo, capture_output=True, text=True, timeout=60, check=False)
        else:
            out = subprocess.run(
                ["gh", "pr", "comment", str(pr), "--body", body],
                cwd=repo, capture_output=True, text=True, timeout=60, check=False)
        if out.returncode != 0:
            return {"ok": False, "error": (out.stderr or "")[:200]}
        return {"ok": True, "updated": bool(existing),
                "url": (out.stdout or "").strip()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


# ── the run ────────────────────────────────────────────────────────────────

def run(repo: str | None = None, *, force_publish: bool | None = None,
        store=None) -> dict:
    """Capture, publish if permitted, comment if there is a pull request.

    Never raises and never returns non-zero to its caller's caller: this runs
    from a ``pre-push`` hook, and an observability tool must not be able to
    stop somebody pushing code.
    """
    repo = repo or os.getcwd()
    result: dict = {"ok": False, "steps": []}
    try:
        commit_range = trace_capture.infer_range(repo)
        if not commit_range:
            return {"ok": True, "skipped": "branch adds no commits"}
        commits = trace_capture.read_commits(repo, commit_range)
        if not commits:
            return {"ok": True, "skipped": "no commits in range"}
        if not any(c.get("session_id") for c in commits):
            # Nothing agent-authored here. Silence is right: a human's branch
            # should not grow a bot comment saying an AI was not involved.
            return {"ok": True, "skipped": "no agent commits"}

        pr = trace_capture.infer_pr(repo)
        if not pr:
            return {"ok": True, "skipped": "no open pull request yet",
                    "hint": "the next push after the PR exists will pick it up"}

        if store is None:
            from clawmetry.cli_cmds._common import get_read_store
            store, _src = get_read_store()
        sessions = [dict(r) for r in (store.query_sessions(limit=1000) or [])]
        session_ids, attribution = trace_capture.resolve_sessions(commits, sessions)
        if not session_ids:
            return {"ok": True, "skipped": "no sessions resolved"}

        events = {}
        for sid in session_ids:
            try:
                events[sid] = [dict(r) for r in
                               (store.query_events(session_id=sid, limit=5000) or [])]
            except Exception:
                events[sid] = []
        if not any(events.values()):
            return {"ok": True, "skipped": "sessions aged out of the local store"}

        bundle = trace_capture.build_bundle(
            repo=repo, commit_range=commit_range, commits=commits,
            session_ids=session_ids, attribution=attribution,
            events_by_session=events,
            sessions_meta={s["session_id"]: s for s in sessions if s.get("session_id")},
            pr=pr)
        result["bundle"] = {"pr": pr, "attribution": bundle["attribution"],
                            **bundle["summary"]}
        result["steps"].append("captured")

        allowed = _flag(repo, CFG_AUTO) if force_publish is None else force_publish
        if not allowed:
            result.update(ok=True, published=False,
                          hint="run `clawmetry trace init --auto` to publish "
                               "automatically on this repository")
            return result

        pub = trace_capture.publish(bundle)
        if not pub.get("ok"):
            result.update(ok=False, error=pub.get("error"))
            return result
        url = pub.get("url")
        result.update(published=True, url=url)
        result["steps"].append("published")

        if _flag(repo, CFG_COMMENT, default=True):
            com = post_comment(repo, pr, render_comment(bundle, url))
            result["comment"] = com
            if com.get("ok"):
                result["steps"].append("updated comment" if com.get("updated")
                                       else "commented")
        result["ok"] = True
        return result
    except Exception as exc:
        logger.warning("auto trace failed: %s", exc, exc_info=True)
        return {"ok": False, "error": str(exc)[:200]}
