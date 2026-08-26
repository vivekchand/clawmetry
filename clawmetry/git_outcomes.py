"""Read a repository and say whether the agent's work shipped (REQ-OBS-CEA-022).

ClawMetry knows what an agent did and what it cost. It does not know whether
any of it reached the product, so every figure on the cost surfaces is an
input with no output to divide it by. The directory a session ran in is
already recorded per session, and it is already a Git repository on the same
disk the daemon runs on. This module reads that repository.

What it derives, all of it locally:

  * which commits exist in a bounded window, what they touched, and whether
    they are reachable from the repository's default branch (= merged);
  * pull-request state, when the code host's command-line tool is installed
    and authenticated, and an explicit "unavailable" when it is not;
  * how many of the lines a commit added still exist at the current tip
    (line survival -> rework);
  * which sessions plausibly produced which commits, with the basis and the
    confidence of every link.

**This module never writes to a user repository.** Every subprocess it runs is
checked against :data:`_READ_ONLY_SUBCOMMANDS` before it is executed, so a
``fetch``/``checkout``/``config``/``gc`` cannot be added later by accident;
``tests/test_git_outcomes.py`` asserts the guard rejects them. It also never
prompts: ``GIT_TERMINAL_PROMPT=0`` plus a per-command timeout means a
credential-less remote fails fast instead of hanging the daemon tick.

Everything here is bounded, because it runs on a daemon that has a CPU budget:
a history window, a commit cap, a blame-file cap, a per-file size cap, a
per-command timeout and a per-repository wall-clock budget. ``CLAWMETRY_GIT_OUTCOMES=0``
switches the whole thing off on a node.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

log = logging.getLogger("clawmetry.git_outcomes")


# ── Bounds ─────────────────────────────────────────────────────────────────
#
# Every one of these is a ceiling on work done inside a daemon tick. They are
# env-overridable because a monorepo and a hobby repo do not want the same
# numbers, and because an operator who finds this expensive needs a dial that
# is not "uninstall".

def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(os.environ.get(name, "").strip() or default)))
    except (TypeError, ValueError):
        return default


def is_enabled() -> bool:
    """False when the operator has switched repository reading off."""
    return os.environ.get("CLAWMETRY_GIT_OUTCOMES", "1").strip().lower() not in (
        "0", "false", "no",
    )


#: How far back a scan reads history. Also the window commits are retained for.
LOOKBACK_DAYS = _env_int("CLAWMETRY_GIT_LOOKBACK_DAYS", 90, 1, 730)
#: Most commits read from one repository in one scan.
MAX_COMMITS = _env_int("CLAWMETRY_GIT_MAX_COMMITS", 500, 10, 5000)
#: Most files blamed for line survival in one scan. Small on purpose: a blame
#: costs about half a second per file on a repository with real history, so
#: this is the difference between a tick that fits in its budget and one that
#: does not. The files chosen are the ones the agent added the most lines to,
#: and the response reports how much of the total it actually measured.
MAX_BLAME_FILES = _env_int("CLAWMETRY_GIT_MAX_BLAME_FILES", 40, 0, 2000)
#: Seconds the whole line-survival pass may take, inside the repository's
#: budget. Separate from that budget so a slow blame cannot starve the cheap
#: local facts, which are the ones every figure depends on.
BLAME_BUDGET_SECS = _env_int("CLAWMETRY_GIT_BLAME_BUDGET", 10, 1, 300)
#: Seconds one file's blame may take before it is abandoned.
BLAME_FILE_TIMEOUT_SECS = _env_int("CLAWMETRY_GIT_BLAME_FILE_TIMEOUT", 4, 1, 60)
#: Files larger than this are not blamed. Blame cost is superlinear in a way
#: that a generated lockfile will happily demonstrate.
MAX_BLAME_FILE_BYTES = _env_int("CLAWMETRY_GIT_MAX_BLAME_BYTES", 512_000, 1024, 8_000_000)
#: Seconds any single git/gh invocation may take.
CMD_TIMEOUT_SECS = _env_int("CLAWMETRY_GIT_CMD_TIMEOUT", 10, 1, 120)
#: Seconds one repository's whole scan may take, checked between steps.
REPO_BUDGET_SECS = _env_int("CLAWMETRY_GIT_REPO_BUDGET", 25, 5, 600)
#: Most pull requests requested from the code host in one scan.
MAX_PULL_REQUESTS = _env_int("CLAWMETRY_GIT_MAX_PRS", 100, 10, 1000)
#: Seconds the code host's tool may take. Separate from the git timeout: this
#: one crosses a network and a slow answer is normal, where a slow local git
#: is not.
GH_TIMEOUT_SECS = _env_int("CLAWMETRY_GIT_GH_TIMEOUT", 20, 3, 120)
#: Most commits a diff-stat pass will read. The stat pass only ever runs on
#: commits that correlated to a session, so this is a ceiling on a list that
#: is normally small.
MAX_STAT_COMMITS = _env_int("CLAWMETRY_GIT_MAX_STAT_COMMITS", 300, 10, 2000)
#: Most commits one session may be linked to. A session that ran for hours in
#: a busy shared repository overlaps in time with work it had nothing to do
#: with; this stops one such session dominating every figure.
MAX_LINKS_PER_SESSION = _env_int("CLAWMETRY_GIT_MAX_LINKS_PER_SESSION", 50, 1, 500)
#: Minutes either side of a session's active span in which a commit may still
#: be attributed to it. A commit is written after the work, sometimes well
#: after; a window this size covers "finished the change, then committed"
#: without swallowing the next session's work.
CORRELATION_GRACE_MINS = _env_int("CLAWMETRY_GIT_GRACE_MINS", 30, 0, 720)


# ── The read-only guarantee ────────────────────────────────────────────────
#
# AC-OBS-CEA-022.2 is "never modifies a repository it reads". That promise is
# only worth what enforces it, so it is enforced here rather than asserted in
# a docstring: one chokepoint, an allowlist of plumbing subcommands, and a
# refusal (not a silent skip) for anything else.

_READ_ONLY_SUBCOMMANDS = frozenset({
    "rev-parse",
    "rev-list",
    "log",
    "blame",
    "cat-file",
    "symbolic-ref",
    "for-each-ref",
    "show-ref",
    "config",       # only ever with --get; see _git()
    "remote",       # only ever with get-url; see _git()
    "ls-files",
})

#: Second-word restrictions for subcommands that have both readers and
#: writers under the same name. ``git config x y`` writes; ``git config --get x``
#: does not. ``git remote add`` writes; ``git remote get-url`` does not.
_READ_ONLY_FIRST_ARG = {
    "config": frozenset({"--get", "--get-all", "--get-regexp", "--list", "-l"}),
    "remote": frozenset({"get-url", "-v", "--verbose"}),
}


class UnsafeGitCommand(RuntimeError):
    """Raised when a command that could write reaches the git chokepoint."""


def _assert_read_only(args: Sequence[str]) -> None:
    """Raise unless ``args`` is a read-only git invocation.

    Called for every subprocess this module runs. A future edit that adds a
    ``fetch`` to freshen state fails loudly here rather than quietly breaking
    the promise the feature is sold on.
    """
    if not args:
        raise UnsafeGitCommand("empty git command")
    sub = args[0]
    if sub not in _READ_ONLY_SUBCOMMANDS:
        raise UnsafeGitCommand(f"git {sub}: not a read-only subcommand")
    allowed_first = _READ_ONLY_FIRST_ARG.get(sub)
    if allowed_first is not None:
        first = args[1] if len(args) > 1 else ""
        if first not in allowed_first:
            raise UnsafeGitCommand(f"git {sub} {first}: not a read-only form")


def _git_env() -> Dict[str, str]:
    """Environment for a git child: never prompt, never take a lock.

    ``GIT_TERMINAL_PROMPT``/``GIT_ASKPASS``/``GCM_INTERACTIVE`` stop a
    credential helper turning a background tick into a hang. ``GIT_OPTIONAL_LOCKS=0``
    keeps a read from touching ``index.lock``, which matters because the
    operator is very likely using this repository at the same time we are.
    """
    env = dict(os.environ)
    env.update({
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "",
        "SSH_ASKPASS": "",
        "GCM_INTERACTIVE": "never",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "LC_ALL": "C",
    })
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def _git(repo: str, *args: str, timeout: Optional[int] = None) -> Optional[str]:
    """Run read-only git in ``repo``; stdout on success, ``None`` on failure.

    Never raises for an ordinary failure (missing git, not a repository, a
    timeout, a non-zero exit). It *does* raise :class:`UnsafeGitCommand` for a
    command that could write, because that is a programming error and
    swallowing it would defeat the guard.
    """
    _assert_read_only(args)
    try:
        proc = subprocess.run(
            ["git", "--no-pager", "-C", repo, *args],
            capture_output=True, text=True, errors="replace",
            timeout=timeout or CMD_TIMEOUT_SECS, env=_git_env(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


# ── Repository discovery ───────────────────────────────────────────────────

def repo_root(path: str) -> Optional[str]:
    """Absolute root of the work tree containing ``path``, or ``None``.

    Handles the worktree case correctly by asking git rather than walking up
    looking for a ``.git`` directory: in a linked worktree ``.git`` is a file,
    and in a submodule the naive walk finds the wrong root.
    """
    p = str(path or "").strip()
    if not p or not os.path.isdir(p):
        return None
    out = _git(p, "rev-parse", "--show-toplevel")
    if not out:
        return None
    root = out.strip()
    return root or None


def discover_repos(cwds: Iterable[str]) -> Dict[str, List[str]]:
    """Map repository root -> the candidate directories that resolved to it.

    Deduplicates the work: a dozen sessions in a dozen subdirectories of one
    repository cost one ``rev-parse`` each and produce one repository.
    """
    found: Dict[str, List[str]] = {}
    seen: Dict[str, Optional[str]] = {}
    for cwd in cwds:
        c = str(cwd or "").strip()
        if not c:
            continue
        if c not in seen:
            seen[c] = repo_root(c)
        root = seen[c]
        if root:
            found.setdefault(root, []).append(c)
    return found


_REMOTE_RE = re.compile(
    r"^(?:(?:https?|ssh|git)://)?(?:[^@/]+@)?(?P<host>[^/:]+)[/:]"
    r"(?P<owner>[^/]+)/(?P<name>.+?)(?:\.git)?/?$"
)


def remote_identity(repo: str) -> Dict[str, str]:
    """``{"remote_url", "host", "owner", "name"}`` for origin; blanks if none.

    A repository with no remote is a perfectly good repository — it just has
    no pull requests, which the caller reports rather than treats as an error.
    """
    out = _git(repo, "remote", "get-url", "origin")
    url = (out or "").strip().splitlines()[0].strip() if out else ""
    ident = {"remote_url": url, "host": "", "owner": "", "name": ""}
    if not url:
        return ident
    m = _REMOTE_RE.match(url)
    if m:
        ident["host"] = m.group("host").lower()
        ident["owner"] = m.group("owner")
        ident["name"] = m.group("name")
    return ident


#: Names tried, in order, when the remote does not declare a default branch.
_DEFAULT_BRANCH_GUESSES = ("main", "master", "trunk", "develop", "default")


def default_branch(repo: str) -> Tuple[str, str]:
    """(ref, basis) for the branch that means "shipped" in this repository.

    ``basis`` distinguishes an answer the repository told us (``remote_head``,
    the symbolic ref origin publishes) from one we guessed by name
    (``name_guess``) or fell back to (``current_head``). It travels with every
    merged/unmerged verdict downstream, because "merged" derived from a guess
    is a weaker claim than one derived from the remote's own HEAD.
    """
    out = _git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if out and out.strip():
        return out.strip(), "remote_head"
    for name in _DEFAULT_BRANCH_GUESSES:
        for ref in (f"refs/remotes/origin/{name}", f"refs/heads/{name}"):
            if _git(repo, "show-ref", "--verify", "--quiet", ref) is not None:
                short = ref.split("refs/remotes/", 1)[-1]
                short = short.replace("refs/heads/", "")
                return short, "name_guess"
    out = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    head = (out or "").strip()
    if head and head != "HEAD":
        return head, "current_head"
    return "", "unknown"


# ── Commits ────────────────────────────────────────────────────────────────

# One record per commit, fields separated by US (0x1f), records by RS (0x1e),
# so a subject containing tabs, pipes or newlines cannot break the parse. The
# --numstat block follows each record's header on its own lines.
#
# ``%S`` (with ``--source``) is the ref the traversal reached the commit by. It
# costs nothing on top of a walk we are doing anyway, which is why the branch a
# commit sits on is read here rather than by asking ``--contains`` per sha —
# that is one O(refs) command per commit and would blow the tick's budget on
# its own.
_LOG_FORMAT = "%x1e%H%x1f%ct%x1f%ae%x1f%an%x1f%S%x1f%s"
_REVERT_RE = re.compile(r'^Revert\s+"', re.I)


def read_commit_index(repo: str, since_epoch: int,
                      until_epoch: Optional[int] = None,
                      limit: int = MAX_COMMITS) -> List[Dict[str, Any]]:
    """Commits in ``[since_epoch, until_epoch]``, newest first, WITHOUT diff stats.

    Both ends matter. ``--max-count`` keeps the NEWEST commits, so on a
    repository taking hundreds of commits a week an unbounded window silently
    collapses to "the last few days" and a session from last month can never
    correlate to anything. Bounding the far end to the span the sessions
    actually cover is what makes older work reachable at all.

    Deliberately cheap. ``--numstat`` is what makes a log expensive — on a
    repository taking 500 commits a week it is most of the scan's whole time
    budget — and it is only needed for the handful of commits that turn out to
    correlate to a session. So the walk that finds candidates does not pay for
    it; :func:`read_commit_stats` pays for it afterwards, for a bounded list.

    Merge commits are excluded: they carry no authored change of their own,
    and counting their diff would double every line in a merged branch.
    """
    args = [
        "log", "--no-merges", "--all", "--source",
        f"--since={_since_arg(since_epoch)}",
    ]
    if until_epoch:
        args.append(f"--until={_since_arg(until_epoch)}")
    args += [f"--max-count={int(limit)}", f"--format={_LOG_FORMAT}"]
    return _parse_log(_git(repo, *args, timeout=max(CMD_TIMEOUT_SECS, 20)))


def read_commit_stats(repo: str, shas: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """``sha -> {insertions, deletions, files}`` for specific commits.

    ``--no-walk`` so git reports exactly the commits named rather than their
    ancestry. Bounded by the caller; a list longer than
    :data:`MAX_STAT_COMMITS` is truncated and the caller says so.
    """
    wanted = [s for s in list(dict.fromkeys(shas))[:MAX_STAT_COMMITS] if s]
    if not wanted:
        return {}
    stats: Dict[str, Dict[str, Any]] = {}
    # Chunked so the argument list cannot outgrow the platform's exec limit.
    for i in range(0, len(wanted), 100):
        out = _git(
            repo, "log", "--no-walk", "--numstat", f"--format={_LOG_FORMAT}",
            *wanted[i:i + 100],
            timeout=max(CMD_TIMEOUT_SECS, 20),
        )
        for c in _parse_log(out, want_stats=True):
            stats[c["sha"]] = {
                "insertions": c["insertions"],
                "deletions": c["deletions"],
                "files": c["files"],
            }
    return stats


def _parse_log(out: Optional[str], want_stats: bool = False) -> List[Dict[str, Any]]:
    """Parse the record stream both log passes emit. ``[]`` on no output."""
    if not out:
        return []
    commits: List[Dict[str, Any]] = []
    for chunk in out.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head, _, body = chunk.partition("\n")
        parts = head.split("\x1f")
        if len(parts) < 6:
            continue
        sha, ct, email, name, source_ref, subject = parts[:6]
        try:
            authored_at = int(ct)
        except (TypeError, ValueError):
            continue
        ins = dels = 0
        files: List[str] = []
        if want_stats:
            for line in body.splitlines():
                cols = line.split("\t")
                if len(cols) < 3:
                    continue
                a, d, path = cols[0], cols[1], cols[2]
                # "-" in both columns is git's marker for a binary file.
                # Counting it as zero lines is right: a binary blob has no
                # lines to survive.
                if a.isdigit():
                    ins += int(a)
                if d.isdigit():
                    dels += int(d)
                if path:
                    files.append([path,
                                  int(a) if a.isdigit() else 0,
                                  int(d) if d.isdigit() else 0])
        commits.append({
            "sha": sha,
            "authored_at": authored_at,
            "author_email": email,
            "author_name": name,
            "subject": subject,
            "source_ref": source_ref,
            "insertions": ins,
            "deletions": dels,
            "files": files,
            "is_revert": bool(_REVERT_RE.match(subject or "")),
        })
    return commits


def merged_shas(repo: str, branch: str, since_epoch: int,
                until_epoch: Optional[int] = None) -> Optional[set]:
    """Shas reachable from ``branch``, i.e. the ones that shipped.

    ``None`` (not an empty set) when the branch cannot be resolved, so a
    caller can tell "nothing merged" from "we could not tell".
    """
    if not branch:
        return None
    args = ["rev-list", branch, f"--since={_since_arg(since_epoch)}",
            "--no-merges"]
    if until_epoch:
        args.append(f"--until={_since_arg(until_epoch)}")
    out = _git(repo, *args, timeout=max(CMD_TIMEOUT_SECS, 20))
    if out is None:
        return None
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


# ── Pull requests ──────────────────────────────────────────────────────────

# Deliberately omits ``additions``/``deletions``: those are the fields that
# turn one listing into a per-pull-request diff computation on the host, and
# they cost more than the whole rest of the scan. The line counts we report
# come from local numstat, which is the same data and free.
_PR_FIELDS = "number,state,title,url,mergedAt,headRefName,baseRefName,mergeCommit"


def read_pull_requests(repo: str) -> Tuple[Optional[List[Dict[str, Any]]], str]:
    """(pull requests, basis) — ``(None, reason)`` when the host is unreachable.

    AC-OBS-CEA-022.3: no ``gh``, no authentication, no network, or a private
    repository we cannot see must all degrade to local branch state and *say*
    so. They must never fail the scan, and they must never be reported as
    "zero pull requests", which is a different and false statement.
    """
    if not shutil.which("gh"):
        return None, "gh_not_installed"
    env = dict(os.environ)
    env.update({"GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1",
                "NO_COLOR": "1", "CLICOLOR": "0"})
    try:
        proc = subprocess.run(
            ["gh", "pr", "list", "--state", "all",
             "--limit", str(MAX_PULL_REQUESTS), "--json", _PR_FIELDS],
            cwd=repo, capture_output=True, text=True, errors="replace",
            timeout=max(CMD_TIMEOUT_SECS, GH_TIMEOUT_SECS), env=env,
        )
    except subprocess.TimeoutExpired:
        return None, "gh_timeout"
    except (OSError, subprocess.SubprocessError):
        return None, "gh_failed"
    if proc.returncode != 0:
        err = (proc.stderr or "").lower()
        if "auth" in err or "logged" in err or "token" in err:
            return None, "gh_not_authenticated"
        if "no git remote" in err or "not a git repository" in err:
            return None, "no_code_host_remote"
        return None, "gh_failed"
    import json as _json
    try:
        rows = _json.loads(proc.stdout or "[]")
    except ValueError:
        return None, "gh_bad_output"
    if not isinstance(rows, list):
        return None, "gh_bad_output"
    prs: List[Dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        merge_commit = r.get("mergeCommit") or {}
        prs.append({
            "number": int(r.get("number") or 0),
            "state": str(r.get("state") or "").upper(),
            "title": str(r.get("title") or "")[:400],
            "url": str(r.get("url") or "")[:500],
            "merged_at": _iso_to_epoch(r.get("mergedAt")),
            "head_branch": str(r.get("headRefName") or "")[:255],
            "base_branch": str(r.get("baseRefName") or "")[:255],
            "merge_commit": str((merge_commit or {}).get("oid") or "")[:40],
        })
    return prs, "gh_cli"


def _since_arg(epoch: int) -> str:
    """``--since`` value for an epoch, as an explicit UTC timestamp.

    Git's approxidate parser accepts a bare integer, but what it decides that
    integer means is not something to bet a history window on.
    """
    from datetime import datetime, timezone
    return datetime.fromtimestamp(int(epoch), timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S+00:00")


def _iso_to_epoch(value: Any) -> int:
    """Epoch seconds for an ISO-8601 string; 0 when absent or unparseable.

    0 here means "no merge timestamp", which for a pull request that is not
    merged is the truth rather than a missing value.
    """
    s = str(value or "").strip()
    if not s:
        return 0
    from datetime import datetime
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    try:
        return int(datetime.fromisoformat(s).timestamp())
    except (TypeError, ValueError):
        return 0


# ── Line survival (rework) ─────────────────────────────────────────────────

_BLAME_CHUNK_RE = re.compile(r"^([0-9a-f]{40}) \d+ \d+ (\d+)$")


def line_survival(repo: str, files: Sequence[Sequence[Any]], branch: str,
                  deadline: Optional[float] = None
                  ) -> Tuple[Dict[str, int], List[str]]:
    """Surviving line count per commit sha, and the files actually measured.

    One blame pass per FILE, not per commit: a blame attributes every current
    line of a file to whichever commit last touched it, so a single pass
    answers the question for every commit that ever touched that file. That is
    what keeps rework affordable — see ADR-052.

    ``--incremental`` because its output is one short header line per
    contiguous chunk (``<sha> <orig> <final> <nlines>``) rather than a full
    copy of the file, which for a large file is the difference between
    kilobytes and megabytes crossing a pipe. ``-w`` ignores whitespace-only
    changes, so a reformat does not read as the original author's work being
    thrown away. A moved line still reads as not surviving; that limitation is
    named in the basis the caller reports.

    ``files`` is ``(path, added_lines)`` pairs. They are visited in descending
    order of lines added, so when the cap or the budget stops the pass early it
    has covered the changes that carry the most weight rather than an arbitrary
    prefix. The second return value is the list of paths that were measured —
    the caller needs it to compute the rate against the lines it actually
    looked at, rather than against a total it did not.
    """
    survived: Dict[str, int] = {}
    measured: List[str] = []
    if not branch:
        return survived, measured
    budget_end = time.monotonic() + BLAME_BUDGET_SECS
    if deadline is not None:
        budget_end = min(budget_end, deadline)
    ranked = sorted(
        ((str(f[0]), int(f[1]) if len(f) > 1 else 0) for f in files if f),
        key=lambda pair: -pair[1],
    )
    for path, added in ranked:
        if len(measured) >= MAX_BLAME_FILES or time.monotonic() > budget_end:
            break
        if added <= 0:
            # Nothing was added here, so nothing of ours can survive in it.
            # Binary files land here too: numstat reports them as "-".
            continue
        # Only blame what still exists at the tip. A deleted file contributes
        # zero surviving lines, which is already the default.
        if _git(repo, "cat-file", "-e", f"{branch}:{path}") is None:
            measured.append(path)
            continue
        try:
            size = os.path.getsize(os.path.join(repo, path))
        except OSError:
            size = 0
        if size > MAX_BLAME_FILE_BYTES:
            continue
        out = _git(repo, "blame", "--incremental", "-w", branch, "--", path,
                   timeout=BLAME_FILE_TIMEOUT_SECS)
        if out is None:
            continue
        measured.append(path)
        for line in out.splitlines():
            m = _BLAME_CHUNK_RE.match(line)
            if m:
                survived[m.group(1)] = survived.get(m.group(1), 0) + int(m.group(2))
    return survived, measured


# ── Correlation ────────────────────────────────────────────────────────────
#
# The heuristic, and the reason every link it makes carries its confidence:
# nothing in a commit records which agent session produced it. What we have is
# the repository the session ran in, when it was active, and sometimes the
# branch it was on. Repository plus time is a real signal and a weak one;
# adding an agreeing branch makes it a strong one. Presenting both as the same
# thing is the failure mode this field exists to prevent.

def correlate(sessions: Sequence[Dict[str, Any]],
              commits: Sequence[Dict[str, Any]]
              ) -> Tuple[List[Dict[str, Any]], int]:
    """Link rows joining sessions to commits within one repository.

    Returns ``(links, sessions_truncated)``.

    Each row is ``{sha, session_id, confidence, basis, matched_branch}``.
    ``confidence`` is ``"high"`` when the session's recorded branch is the one
    the commit is on, ``"medium"`` when only the repository and the time
    window agree, and ``"low"`` when both branches are known and disagree.
    Sessions carrying no timestamps are skipped rather than matched loosely —
    a session we cannot place in time is not evidence.
    """
    grace = CORRELATION_GRACE_MINS * 60
    links: List[Dict[str, Any]] = []
    truncated = 0
    for s in sessions:
        started = int(s.get("started_epoch") or 0)
        ended = int(s.get("last_active_epoch") or 0)
        if not started and not ended:
            continue
        lo = (started or ended) - grace
        hi = (ended or started) + grace
        sid = str(s.get("session_id") or "")
        sbranch = str(s.get("git_branch") or "").strip()
        mine: List[Dict[str, Any]] = []
        for c in commits:
            at = int(c.get("authored_at") or 0)
            if at < lo or at > hi:
                continue
            cbranch = str(c.get("branch_hint") or "").strip()
            if sbranch and cbranch and _branch_eq(sbranch, cbranch):
                conf, basis = "high", "repo_time_branch"
            elif sbranch and cbranch:
                # Both branches are known and they disagree. The link is kept
                # and marked, not dropped: the commit's branch is the ref a
                # traversal happened to reach it by, so a disagreement is a
                # weaker signal than an agreement is. Dropping on it would
                # silently delete real work; recording it lets a reader
                # exclude these and see how many they excluded.
                conf, basis = "low", "repo_time_branch_mismatch"
            else:
                conf, basis = "medium", "repo_time"
            mine.append({
                "sha": c["sha"],
                "session_id": sid,
                "confidence": conf,
                "basis": basis,
                "matched_branch": cbranch or sbranch,
            })
        if len(mine) > MAX_LINKS_PER_SESSION:
            truncated += 1
            # Keep the strongest evidence rather than the first N found: a
            # session with a branch has high-confidence links and those are
            # the ones a figure should rest on.
            rank = {"high": 0, "medium": 1, "low": 2}
            mine.sort(key=lambda ln: rank.get(ln["confidence"], 3))
            mine = mine[:MAX_LINKS_PER_SESSION]
        links.extend(mine)
    return links, truncated


def _branch_eq(a: str, b: str) -> bool:
    """Compare branch names ignoring a remote prefix.

    A session records ``feat/x``; a commit decoration may say ``origin/feat/x``
    or ``refs/heads/feat/x``. Those are the same branch and a string compare
    would say otherwise.
    """
    def norm(x: str) -> str:
        x = x.strip()
        for prefix in ("refs/remotes/", "refs/heads/", "origin/", "remotes/origin/"):
            if x.startswith(prefix):
                x = x[len(prefix):]
        return x.strip().lower()
    return bool(a) and norm(a) == norm(b)


def session_span(sessions: Sequence[Dict[str, Any]],
                 floor_epoch: int) -> Tuple[int, Optional[int]]:
    """``(since, until)`` covering every session, padded by the grace window.

    ``floor_epoch`` clamps how far back the answer may reach, so one very old
    session cannot turn a tick into a full-history walk. ``(floor, None)`` when
    no session carries a usable timestamp — an unbounded far end, because with
    nothing to correlate to there is nothing to miss.
    """
    grace = CORRELATION_GRACE_MINS * 60
    starts, ends = [], []
    for s in sessions:
        a = int(s.get("started_epoch") or 0)
        b = int(s.get("last_active_epoch") or 0)
        if a or b:
            starts.append(min(x for x in (a, b) if x))
            ends.append(max(a, b))
    if not starts:
        return floor_epoch, None
    return max(floor_epoch, min(starts) - grace), max(ends) + grace


# ── One repository, one scan ───────────────────────────────────────────────

def scan_repo(repo: str, sessions: Sequence[Dict[str, Any]],
              since_epoch: Optional[int] = None) -> Dict[str, Any]:
    """Everything derivable about one repository, inside one time budget.

    The order is chosen so that the cheap, local, always-available facts are
    established before anything that can be slow or absent:

      1. default branch and remote identity (three tiny commands);
      2. the commit index and which shas are reachable from the default
         branch — the merged/not-merged verdict, which needs no network;
      3. correlation, which is pure computation over what is already read;
      4. diff stats, but only for commits that correlated;
      5. line survival for the files those commits touched;
      6. pull-request state, last, with whatever budget is left, because it is
         enrichment and every figure below degrades honestly without it.

    Partial results are normal and are labelled. A scan that runs out of
    budget before blaming reports rework as incomplete rather than reporting a
    rate measured from half the files.
    """
    started = time.monotonic()
    deadline = started + REPO_BUDGET_SECS
    floor = int(since_epoch if since_epoch is not None
                else time.time() - LOOKBACK_DAYS * 86400)
    since, until = session_span(sessions, floor)

    branch, branch_basis = default_branch(repo)
    ident = remote_identity(repo)
    commits = read_commit_index(repo, since, until)
    merged = merged_shas(repo, branch, since, until) if branch else None

    for c in commits:
        # None, not False: "we could not resolve a default branch" and "this
        # did not ship" are different answers and must not render the same.
        c["merged"] = None if merged is None else (c["sha"] in merged)
        # A commit that shipped belongs to the default branch, whatever ref
        # the traversal reached it by first — with --all that is often a stale
        # remote copy of the same work. For the rest, the traversal's own ref
        # is the best hint available and cost nothing.
        c["branch_hint"] = (branch if c.get("merged")
                            else str(c.get("source_ref") or "").strip())

    links, links_truncated = correlate(sessions, commits)

    # Diff stats only for what correlated (step 4).
    by_sha = {c["sha"]: c for c in commits}
    linked_shas = [sh for sh in dict.fromkeys(ln["sha"] for ln in links)
                   if sh in by_sha]
    stats_truncated = len(linked_shas) > MAX_STAT_COMMITS
    stats = ({} if time.monotonic() > deadline
             else read_commit_stats(repo, linked_shas))
    for sha, st in stats.items():
        by_sha[sha].update(st)

    # Line survival for the files those commits touched (step 5).
    # Only MERGED commits are candidates for rework. A commit sitting on an
    # unmerged branch has no lines at the default branch's tip by definition,
    # so blaming it would report every line of work-in-progress as thrown
    # away — the metric would say "rework" and mean "not merged yet".
    survival_shas = [sh for sh in linked_shas if by_sha[sh].get("merged")]
    added_by_file: Dict[str, int] = {}
    for sha in survival_shas:
        for f in by_sha[sha].get("files") or []:
            path = str(f[0]) if f else ""
            if path:
                added_by_file[path] = added_by_file.get(path, 0) + (
                    int(f[1]) if len(f) > 1 else 0)
    files = sorted(added_by_file.items(), key=lambda kv: -kv[1])
    survival: Dict[str, int] = {}
    measured_files: List[str] = []
    if files and branch and time.monotonic() <= deadline:
        survival, measured_files = line_survival(repo, files, branch, deadline)
    rework_complete = bool(
        branch and not stats_truncated and len(measured_files) >= sum(
            1 for _, added in files if added > 0)
    )

    # Pull-request state last, with whatever budget is left (step 6).
    prs: Optional[List[Dict[str, Any]]] = None
    if not ident.get("host"):
        pr_basis = "no_code_host_remote"
    elif time.monotonic() > deadline:
        pr_basis = "budget_exhausted"
    else:
        prs, pr_basis = read_pull_requests(repo)

    return {
        "repo_root": repo,
        "remote_url": ident["remote_url"],
        "host": ident["host"],
        "owner": ident["owner"],
        "name": ident["name"],
        "default_branch": branch,
        "branch_basis": branch_basis,
        "merge_basis": "unknown" if merged is None else "reachability",
        "pr_basis": pr_basis,
        "commits": [by_sha[sh] for sh in linked_shas],
        "pull_requests": prs,
        "links": links,
        "survival": survival,
        "measured_files": measured_files,
        "candidate_files": len(files),
        "rework_complete": rework_complete,
        "links_truncated": links_truncated,
        "stats_truncated": stats_truncated,
        "commits_seen": len(commits),
        # The cap keeps the NEWEST commits, so a truncated window is narrower
        # at its far end than the caller asked for. Saying so is the
        # difference between "nothing correlated" and "we did not look".
        "commits_truncated": len(commits) >= MAX_COMMITS,
        "window_since": since,
        "window_until": until,
        "merged_commits_in_window": sum(1 for c in commits if c.get("merged")),
        "scanned_at": int(time.time()),
        "scan_secs": round(time.monotonic() - started, 3),
    }
