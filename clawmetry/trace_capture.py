"""Build a PR trace bundle from local session data (PRD-pr-trace.md §4b).

This module owns the half of PR Trace that must run **on the machine the agent
ran on**, because that is the only place the data exists (§4j): resolve a commit
range to the sessions that produced it, pull those sessions out of the local
store, redact them for publication, and emit a self-contained bundle.

Everything server-side — the ``trace.clawmetry.com`` resolver, the hosted
viewer, the directory and the GitHub App — lives in **clawmetry-cloud**. This
module's output is the contract between the two: a JSON bundle the cloud stores
and renders, and which ``render_html`` can also render locally with no server
at all.

Attribution honesty (§2b, §3c) is not optional here. Every bundle carries an
``attribution`` field:

``exact``      every commit in the range named its session via the
               ``Clawmetry-Session`` trailer.
``shared``     resolved exactly, but the session also produced work outside
               this commit range, so the cost is an upper bound.
``heuristic``  no trailer; sessions were guessed from ``Co-Authored-By`` plus
               time overlap. Measured at 5-8 candidate sessions per PR on a
               real repo — never render this as a headline number.
"""

from __future__ import annotations

import ast
import json
import logging
import re
import subprocess

from clawmetry import redaction, trace_stamp

logger = logging.getLogger("clawmetry.trace_capture")

BUNDLE_VERSION = 1

ATTR_EXACT = "exact"
ATTR_SHARED = "shared"
ATTR_HEURISTIC = "heuristic"

#: Sessions whose activity overlaps a commit by more than this are considered
#: candidates in the heuristic tier. Deliberately generous: the tier is a
#: coverage signal, not an attribution mechanism.
HEURISTIC_WINDOW_S = 7200

_COAUTH = re.compile(r"^Co-Authored-By:\s*Claude", re.MULTILINE | re.IGNORECASE)


# ── git ────────────────────────────────────────────────────────────────────

def _git(repo: str, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True,
            timeout=30, check=False
        )
        return out.stdout or ""
    except Exception as exc:
        logger.warning("git %s failed: %s", " ".join(args), exc)
        return ""


def read_commits(repo: str, commit_range: str) -> list[dict]:
    """Return commits in ``commit_range`` with their session trailers."""
    raw = _git(repo, "log", commit_range, "--pretty=format:%H%x1f%ct%x1f%an%x1f%s%x1f%b%x1e")
    commits = []
    for rec in raw.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        parts = (rec.split("\x1f") + ["", "", "", ""])[:5]
        sha, ct, author, subject, body = parts
        commits.append({
            "sha": sha,
            "short_sha": sha[:9],
            "ts": int(ct) if ct.isdigit() else 0,
            "author": author,
            "subject": subject,
            "session_id": trace_stamp.existing_trailer(body),
            "ai_coauthored": bool(_COAUTH.search(body)),
        })
    return list(reversed(commits))  # oldest first


def project_from_remote(repo: str) -> str | None:
    """``owner/repo`` from the git remote, for the trace URL (§4c)."""
    configured = _git(repo, "config", "--get", "clawmetry.project").strip()
    if configured:
        return configured
    url = _git(repo, "remote", "get-url", "origin").strip()
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


# ── session resolution ─────────────────────────────────────────────────────

def resolve_sessions(commits: list[dict], all_sessions: list[dict]) -> tuple[list[str], str]:
    """Resolve commits to session ids. Returns ``(session_ids, attribution)``."""
    known = {s.get("session_id") for s in all_sessions if s.get("session_id")}

    stamped = [c["session_id"] for c in commits if c.get("session_id")]
    resolved = [sid for sid in dict.fromkeys(stamped) if sid in known]
    if resolved and len(stamped) == len(commits):
        return resolved, ATTR_EXACT
    if resolved:
        # Some commits stamped, some not -- still exact for what we have, but
        # the range is not fully accounted for.
        return resolved, ATTR_SHARED

    # Heuristic tier: AI-coauthored commits + session activity overlap.
    if not any(c.get("ai_coauthored") for c in commits):
        return [], ATTR_HEURISTIC
    lo = min((c["ts"] for c in commits if c["ts"]), default=0)
    hi = max((c["ts"] for c in commits if c["ts"]), default=0)
    cands = []
    for s in all_sessions:
        start, end = _epoch(s.get("started_at")), _epoch(s.get("updated_at"))
        if start is None:
            continue
        end = end or start
        if start - HEURISTIC_WINDOW_S <= hi and end + HEURISTIC_WINDOW_S >= lo:
            cands.append(s["session_id"])
    return cands, ATTR_HEURISTIC


def _epoch(value) -> float | None:
    if not value:
        return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _as_dict(value) -> dict:
    """Event ``data`` arrives as a dict, a JSON string, or a repr string."""
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    for parse in (json.loads, ast.literal_eval):
        try:
            out = parse(value)
            if isinstance(out, dict):
                return out
        except Exception:
            continue
    return {}


# ── publish-time redaction (§4f) ───────────────────────────────────────────

#: Publication is a wider exposure than local storage, so this pass is stricter
#: than ``redaction.redact_event``: it also removes things that are merely
#: private rather than secret. Ingest redaction still runs first.
_HOME = re.compile(r"/(?:home|Users)/[^/\s\"']+")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

#: Identifiers that are not secrets but should not be handed out. Found on the
#: first real publish attempt: a trace of a session that had merely READ
#: deploy.yml carried eight live Stripe price ids, because an agent session
#: sees everything the developer's terminal saw. Secret redaction had nothing
#: to say about them -- they are not credentials -- and that is the gap this
#: closes. The rule is narrow on purpose: provider-issued identifiers with a
#: recognisable shape, not an attempt to guess at commercial sensitivity,
#: which is what the human review gate is for.
_VENDOR_IDS = (
    re.compile(r"\bprice_1[A-Za-z0-9]{16,}"),          # Stripe price
    re.compile(r"\b(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{16,}"),  # Stripe key
    re.compile(r"\bcus_[A-Za-z0-9]{14,}"),             # Stripe customer
    re.compile(r"\bsub_[A-Za-z0-9]{14,}"),             # Stripe subscription
    re.compile(r"\bacct_[A-Za-z0-9]{16,}"),            # Stripe account
    re.compile(r"\bprod_[A-Za-z0-9]{14,}"),            # Stripe product
)


def redact_for_publication(text: str) -> str:
    """Scrub secrets (via :mod:`clawmetry.redaction`) then private detail."""
    if not isinstance(text, str) or not text:
        return text
    try:
        out = redaction.redact_text(text)
        for pat in _VENDOR_IDS:
            out = pat.sub("[vendor-id]", out)
        out = _HOME.sub("~", out)
        out = _EMAIL.sub("[email]", out)
        out = _IPV4.sub("[ip]", out)
        return out
    except Exception as exc:
        logger.warning("publication redaction failed: %s", exc)
        # Fail CLOSED: publication is the one path where dropping the content
        # is safer than shipping it unredacted.
        return "[REDACTION FAILED - CONTENT WITHHELD]"


# ── bundle ─────────────────────────────────────────────────────────────────

def build_bundle(
    *,
    repo: str,
    commit_range: str,
    commits: list[dict],
    session_ids: list[str],
    attribution: str,
    events_by_session: dict[str, list[dict]],
    sessions_meta: dict[str, dict],
    pr: str | None = None,
    project: str | None = None,
) -> dict:
    """Assemble the publishable bundle. Pure — no I/O, so it is easy to test."""
    last_commit_ts = max((c["ts"] for c in commits if c["ts"]), default=0)

    prompts: list[dict] = []
    turns: list[dict] = []
    tokens = cost = 0.0
    tools = 0
    models: dict[str, int] = {}
    spans_outside = False

    for sid in session_ids:
        for ev in events_by_session.get(sid, []):
            ts = _epoch(ev.get("ts")) or 0
            if last_commit_ts and ts > last_commit_ts:
                spans_outside = True
                continue  # work that happened after this PR's last commit
            data = _as_dict(ev.get("data"))
            etype = ev.get("event_type") or ""
            try:
                tokens += float(ev.get("token_count") or 0)
                cost += float(ev.get("cost_usd") or 0)
            except (TypeError, ValueError):
                pass
            if ev.get("model"):
                models[ev["model"]] = models.get(ev["model"], 0) + 1
            if etype == "tool_call":
                tools += 1
            if etype == "message" and data.get("role") == "user":
                prompts.append({
                    "ts": ev.get("ts"),
                    "session_id": sid,
                    "text": redact_for_publication(data.get("content") or ""),
                })
            turns.append({
                "ts": ev.get("ts"),
                "type": etype,
                "role": data.get("role"),
                "tool": data.get("tool_name"),
                "model": ev.get("model"),
                "tokens": ev.get("token_count") or 0,
                "cost_usd": ev.get("cost_usd") or 0,
                "text": redact_for_publication(data.get("content") or ""),
            })

    # §3c: a session that also produced work outside this range makes the cost
    # an upper bound, not a figure. Say so rather than quietly summing.
    if attribution == ATTR_EXACT and spans_outside:
        attribution = ATTR_SHARED

    return {
        "bundle_version": BUNDLE_VERSION,
        "project": project or project_from_remote(repo),
        "pr": pr,
        "commit_range": commit_range,
        "commits": [
            {k: c[k] for k in ("short_sha", "subject", "author", "ts", "session_id")}
            for c in commits
        ],
        "sessions": [
            {
                "session_id": sid,
                "cost_usd": (sessions_meta.get(sid) or {}).get("cost_usd"),
                "started_at": (sessions_meta.get(sid) or {}).get("started_at"),
            }
            for sid in session_ids
        ],
        "attribution": attribution,
        "summary": {
            "prompts": len(prompts),
            "turns": len(turns),
            "tools": tools,
            "tokens": int(tokens),
            "cost_usd": round(cost, 4),
            "models": models,
            "cost_is_upper_bound": attribution != ATTR_EXACT,
        },
        # Lenses. `trace`/`agent_graph`/`workflows` stay empty until
        # iter_replay_events lands in the adapters (PRD §3b) -- an honest
        # empty beats a fabricated one.
        "lenses": {
            "prompts": prompts,
            "trace": turns,
            "agent_graph": {"nodes": [], "edges": []},
            "workflows": [],
        },
    }


# ── publish (PRD §4b step 4) ───────────────────────────────────────────────

def publish(bundle: dict, *, app_url: str | None = None,
            api_key: str | None = None, timeout: int = 60) -> dict:
    """Upload a bundle and return ``{"ok", "url"}`` or ``{"ok": False, "error"}``.

    Publishing is deliberately a SEPARATE step from capture. Capture writes to
    disk and stops; a human looks at the review page and decides. Publication
    is a write in the CLAUDE.md sense (user-initiated, scoped, reversible,
    attributed), and the thing being written is a public web page containing
    the contents of somebody's terminal.

    Requires an account key: the server rejects anonymous publishes because
    otherwise anyone could put a fabricated trace at any pull request's URL.
    """
    import json as _json
    import urllib.error
    import urllib.request

    if not isinstance(bundle, dict) or not bundle.get("project") or not bundle.get("pr"):
        return {"ok": False, "error": "bundle needs a project and a pr to publish"}

    if api_key is None:
        try:
            with open(os.path.expanduser("~/.clawmetry/config.json")) as fh:
                api_key = (_json.load(fh) or {}).get("api_key")
        except Exception:
            api_key = None
    if not api_key:
        return {"ok": False,
                "error": "no account key found; run `clawmetry connect` first"}

    if app_url is None:
        try:
            from clawmetry.endpoints import app_url as _au
            app_url = _au()
        except Exception:
            app_url = "https://app.clawmetry.com"

    body = _json.dumps(bundle, default=str).encode("utf-8")
    req = urllib.request.Request(
        app_url.rstrip("/") + "/api/pr-trace/publish",
        data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {exc.code}", "detail": detail}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


# ── inference: nobody should type a revision range ─────────────────────────

def default_branch(repo: str) -> str:
    """The branch a pull request would target. Asks the remote, not a guess."""
    head = _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD").strip()
    if head:
        return head.rsplit("/", 1)[-1]
    for cand in ("main", "master"):
        if _git(repo, "rev-parse", "--verify", f"origin/{cand}").strip():
            return cand
    return "main"


def infer_range(repo: str) -> str | None:
    """The commits this branch adds, as a pull request would see them.

    Uses the merge base rather than ``origin/main..HEAD`` so a branch that has
    not been rebased does not sweep in everything that landed on the default
    branch meanwhile.
    """
    base = default_branch(repo)
    ref = f"origin/{base}"
    if not _git(repo, "rev-parse", "--verify", ref).strip():
        ref = base
    mb = _git(repo, "merge-base", ref, "HEAD").strip()
    if not mb:
        return None
    if _git(repo, "rev-parse", "HEAD").strip() == mb:
        return None  # nothing on this branch yet
    return f"{mb}..HEAD"


def infer_pr(repo: str, timeout: int = 15) -> str | None:
    """The open pull request for this branch, if there is one.

    Asks the forge's public API for the branch's PR. Unauthenticated, because
    this must work before anyone has connected anything; a private repo simply
    returns nothing and the caller falls back to asking.
    """
    import json as _json
    import urllib.request

    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    project = project_from_remote(repo)
    if not branch or branch == "HEAD" or not project or "/" not in project:
        return None
    owner = project.split("/")[0]
    url = (f"https://api.github.com/repos/{project}/pulls"
           f"?head={owner}:{branch}&state=open&per_page=1")
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "clawmetry-trace",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rows = _json.loads(resp.read().decode("utf-8", "replace"))
        if isinstance(rows, list) and rows:
            return str(rows[0].get("number") or "") or None
    except Exception as exc:
        logger.debug("PR lookup failed: %s", exc)
    return None
