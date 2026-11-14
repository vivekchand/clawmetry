"""clawmetry/attribution.py: link an agent session to what it DELIVERED.

ClawMetry has always answered "what are my agents doing, and what did they
cost". It could not answer "what did we get for the money", because every
number it stores is keyed on a session, a runtime, a model or a node, and
none is keyed on a *delivered artifact* (a pull request, a repo, a branch,
a file). This module supplies the missing edge.

It is **pure**: events in, artifact refs + a cost split out. No DuckDB, no
network, no filesystem, no clock. The daemon (``sync.py``) orchestrates it
and ``local_store`` persists the result, exactly as ``policy_engine.py``
is driven by ``sync.py`` and ``detector_money.py`` prices incidents.

Why the tool stream and not a git integration (phase 1)
-------------------------------------------------------
An agent that works on a pull request *names* it. Measured on a real node
(201 sessions, $3,843.33 of spend): 2,113 tool calls carried a literal
``gh pr <verb> <number>`` and 48 sessions holding **76% of the node's
spend** referenced a specific PR. The repo comes along for free in
``--repo owner/name`` and in every ``github.com/owner/repo/pull/N`` URL.
So the first and largest slice of attribution needs no GitHub App, no new
ingest path and no new dependency: it is a read over events already in
DuckDB, which also means it **backfills the whole existing history** on
installs that are already running.

Relationship to ``pr_provenance.py`` (read this before extending either)
------------------------------------------------------------------------
``clawmetry/pr_provenance.py`` (#5946) already links sessions to a pull
request for the **compliance** path: it needs a git checkout, a
``--base``/``--head`` commit range and a PR you already know, and it emits
a bundle / SARIF / a PR comment for CI. Its two bases are
``commit_trailer`` (a ``Clawmetry-Session:`` trailer the session wrote) and
``observed_write`` (a write tool call on a changed path).

This module is the **discovery** half and deliberately needs none of that:
no git, no checkout, no trailer, no CI runner, no PR known in advance. It
answers "which pull requests did this session touch, and what did each
cost", which is why it can run inside the daemon, backfill history that is
already in DuckDB, and work on the hosted dashboard where no repository
exists. It adds one basis, ``pr_reference``, and reuses that module's
vocabulary so the two features describe the same world. Extend, do not
duplicate: linking that needs a repository belongs there, linking that
reads only the event stream belongs here.

Honesty rules this module will not break
----------------------------------------
- **A reference is an association, not proof.** Every row carries
  ``confidence`` plus ``evidence`` (the literal text that produced the
  match), so a reader can always see *why* we think a session touched a
  PR. ``confidence`` is 1.0 only when the PR number is literally present.
- **Cost is split, never duplicated.** One session routinely touches many
  PRs: a naive session-to-PR join on the measured node produced a
  $106,946 pull request on a $3,843 machine. Attribution therefore runs
  at event level (see :func:`split_cost`) and the per-artifact amounts
  plus ``unattributed_usd`` always sum to the session's own cost.
- **No invented numbers.** Where no cost is known the amount is ``0.0``
  with basis ``unknown``, the same contract ``detector_money`` holds for
  ``spend_at_risk_usd``.
"""
from __future__ import annotations

import html
import json
import logging
import re
from typing import Any, Iterable, Optional

log = logging.getLogger("clawmetry.attribution")

# ── Bounds (the daemon stays light: FLYWHEEL section 1e) ────────────────────
# Per-event text we are willing to regex-scan. Tool payloads can carry a
# whole file; the refs we look for live in the command line, never in a
# 400 kB diff body.
MAX_EVENT_TEXT = 20_000
#: Argument strings scanned per event before we stop. One tool call has a
#: handful of arguments; a pathological payload will not turn the pass into a
#: regex benchmark.
MAX_TEXTS_PER_EVENT = 12

#: Bump whenever extraction, role or cost-split SEMANTICS change, so stored
#: rows computed under the old rules are recomputed instead of persisting
#: forever. Without it the watermark only notices a session that GREW, and a
#: dormant session keeps its old answer: the table would hold a mix of
#: semantics with nothing to tell them apart. Bumped to 2 when role stopped
#: being promoted session-wide and a bare URL stopped counting as a review,
#: and to 3 when the runtime stopped being read from ``events.agent_type``
#: (which says 'openclaw' for almost everything) and started coming from the
#: session id prefix, so every stored row is refiled under the runtime the
#: switcher actually offers.
RULES_VERSION = "9"
# Per-session caps. A session that names 500 PRs is a digest cron, not a
# delivery; truncating keeps one pathological row from dominating the table.
MAX_PRS_PER_SESSION = 64
MAX_FILES_PER_SESSION = 200
MAX_BRANCHES_PER_SESSION = 32
MAX_COMMITS_PER_SESSION = 64
# Evidence is shown to a human in a table cell.
MAX_EVIDENCE_CHARS = 160

# ── Artifact kinds ──────────────────────────────────────────────────────────
KIND_PR = "pr"
KIND_REPO = "repo"
KIND_BRANCH = "branch"
KIND_COMMIT = "commit"
KIND_FILE = "file"

# ── Basis: HOW we know, shared with pr_provenance ───────────────────────────
# ``pr_provenance`` owns ``commit_trailer`` and ``observed_write``. This
# module contributes the one basis that needs no repository: the session's
# own tool stream named the pull request. Imported rather than re-spelled so
# a rename there cannot silently fork the vocabulary.
BASIS_PR_REFERENCE = "pr_reference"
try:  # pragma: no cover - import guard, the names are stable
    from clawmetry.pr_provenance import BASIS_TRAILER, BASIS_WRITE
except Exception:  # pragma: no cover
    BASIS_TRAILER = "commit_trailer"
    BASIS_WRITE = "observed_write"

# ── Roles (what the session did to the artifact) ────────────────────────────
ROLE_AUTHORED = "authored"
ROLE_REVIEWED = "reviewed"
ROLE_EXPLORED = "explored"

# Rank for "the strongest role wins" when one session both reviews and
# authors the same PR.
_ROLE_RANK = {ROLE_EXPLORED: 0, ROLE_REVIEWED: 1, ROLE_AUTHORED: 2}

# ``gh pr <verb>`` verbs that mean the session was CHANGING the PR, versus
# merely looking at it. Derived from the gh CLI's own command list rather
# than guessed, so a reader can check it against `gh pr --help`.
_GH_PR_AUTHOR_VERBS = frozenset({
    "create", "merge", "edit", "ready", "comment", "close", "reopen",
})
_GH_PR_REVIEW_VERBS = frozenset({
    "view", "checks", "diff", "review",
})
# ``gh pr list`` and ``gh pr status`` take NO pull-request argument, so any
# number following them belongs to a flag (``--limit 20``). Leaving them out
# of the verb set is what stops ``gh pr list --limit 20`` being recorded as
# "this session worked on PR 20" (measured false positive, 2026-10-15).
_GH_PR_VERBS = _GH_PR_AUTHOR_VERBS | _GH_PR_REVIEW_VERBS

# ── Patterns ────────────────────────────────────────────────────────────────
# A PR URL is unambiguous: it carries BOTH the repo and the number.
_RE_PR_URL = re.compile(
    r"github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)/pull/(\d{1,7})"
)
# ``gh pr checks 6275``. The verb is required so a bare "pr 6275" in prose
# never counts, and the number must be the FIRST positional token after the
# verb. Allowing flags in between (``gh pr view --json x 6275``) let a flag's
# own value be read as the PR number, which is how ``gh pr list --limit 20``
# became "PR 20". Missing an unusual argument order is strictly better than
# recording a wrong pull request.
_RE_GH_PR = re.compile(r"\bgh\s+pr\s+([a-z]+)\s+(\d{1,7})(?![\d.])")
# ``--repo owner/name`` / ``-R owner/name``.
_RE_REPO_FLAG = re.compile(
    r"(?:--repo|-R)[= ]([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)"
)
# A git remote: ``git@github.com:owner/name.git`` or the https form.
# Only the bare ``github.com`` host (and ``api.github.com/repos/``) names a
# repository. The lookbehind is what stops a subdomain from qualifying:
# ``docs.github.com/site-policy/github-terms`` and ``docs.github.com/en/rest/
# branches`` used to be read as the repositories ``site-policy/github-terms``
# and ``rest/branches``, and five of them reached the live tab.
_RE_REPO_REMOTE = re.compile(
    r"(?<![\w.\-])(?:www\.)?github\.com[:/]"
    r"([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+?)(?:\.git)?(?=[\s\"'/]|$)"
)
_RE_REPO_API = re.compile(
    r"(?<![\w.\-])api\.github\.com/repos/"
    r"([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+?)(?=[\s\"'/]|$)"
)

#: First path segments on github.com that are GitHub's own pages, not an
#: account. Reading one as an owner invents a repository that does not exist;
#: ``settings/personal-access-tokens`` and ``repos/vivekchand`` both shipped.
#: A checkable list of GitHub's reserved namespace, not a heuristic.
RESERVED_GITHUB_OWNERS = frozenset((
    "about", "account", "apps", "blog", "codespaces", "collections", "contact",
    "customer-stories", "dashboard", "en", "enterprise", "events", "explore",
    "features", "issues", "join", "login", "logout", "marketplace", "new",
    "notifications", "organizations", "orgs", "pricing", "pulls", "readme",
    "repos", "rest", "search", "security", "security-advisories", "sessions",
    "settings", "site-policy", "sponsors", "stars", "topics", "trending",
    "users", "watching",
    # GitHub's own service namespaces on github.com, which look exactly like
    # an account in a URL. ``user-attachments/assets`` (the image CDN path)
    # and ``assets-cdn/worker`` both reached the live tab as repositories.
    "assets-cdn", "codeload", "user-attachments",
    # GitHub's own product and marketing pages. ``github.com/resources/
    # insights/<slug>`` is an article, and it reached the live tab as the
    # repository ``resources/insights``.
    "copilot", "education", "git-guides", "mobile", "models", "newsroom",
    "nonprofit", "premium-support", "resources", "shop", "social-impact",
    "solutions", "why-github",
))

#: The git config variable ``actions/checkout`` writes on every CI run, so a
#: build log carries
#: ``GIT_CONFIG_KEY_0='http.https://github.com/OWNER/NAME.extraheader'`` and the
#: repository arrives with a config variable glued onto its name. The whole
#: string is a config KEY, but the repository inside it is REAL, so the
#: variable is removed and the sighting kept rather than dropped.
#:
#: A vocabulary of one, deliberately. git documents many variables for the
#: ``http.<url>.<variable>`` section, but ``version``, ``proxy`` and
#: ``sslverify`` are all words a real repository name could end with, and
#: silently rewriting ``someone/app.version`` to ``someone/app`` would invent
#: a repository: the failure this whole tab has been fixed four times to
#: avoid. ``extraheader`` is git's own word and names no repository.
GIT_HTTP_CONFIG_VARS = frozenset(("extraheader",))

#: Owner halves that documentation, help text and test fixtures use as a
#: stand-in for a real account. ``own/repo`` carried 14 pull-request rows and
#: $11.85 of real money on the live node: the agent had been editing and
#: RUNNING this repository's own tests, and the extractor read the fixtures in
#: them as delivered work. They are well-formed, so every shape test passes
#: them.
#:
#: Checked on the OWNER half only, which is what makes this a fact rather than
#: a guess: no real account is called ``owner`` or ``example``, while plenty of
#: real repositories are named ``repo``, ``cli`` or ``docs``.
PLACEHOLDER_REPO_OWNERS = frozenset((
    "acme", "alice", "bar", "baz", "bob", "carol", "demo", "example",
    "example-org", "foo", "gone", "me", "my-org", "myorg", "octocat", "org",
    "organization", "other", "own", "owner", "placeholder", "sample",
    "someone", "test", "testing", "user", "username", "you", "your-org",
    "your-organization", "yourorg",
))

#: Characters a repository name uses to join two tokens. Where a longer name
#: RESUMES a shorter one decides whether the short one was cut short or is a
#: different repository: see :func:`_extends_without_separator`.
_NAME_SEPARATORS = "-_."
# Branch creation / push. ``-b``/``-c`` means the agent MADE the branch.
_RE_BRANCH_NEW = re.compile(
    r"\bgit\s+(?:checkout|switch)\s+(?:-b|-c|-B)\s+([A-Za-z0-9._/\-]{1,120})"
)
# The remote is a remote NAME, not any non-space run: ``\S+`` let
# ``git push -q 2>&1 | tail -3`` nominate ``2`` as a branch, and it reached
# the tab.
_RE_BRANCH_PUSH = re.compile(
    r"\bgit\s+push\s+(?:--?[A-Za-z0-9-]+\s+)*[A-Za-z0-9_.\-]+\s+"
    r"(?:HEAD:)?([A-Za-z0-9._/\-]{1,120})"
)
# ``git commit`` prints ``[branch-name a1b2c3d] subject``. That is the only
# place a commit sha we CAUSED appears, so we read it from result text and
# never from a command line (where a sha is usually something being read).
#
# The sha must contain a hex LETTER. An all-digit run of the right length is
# almost always something else in brackets (a timestamp, a run id) and we
# measured exactly that false positive. The cost is the ~3.7% of 7-char short
# shas that happen to be all digits; a missing commit row is recoverable, a
# wrong one teaches the user the table lies.
_RE_COMMIT_OUT = re.compile(
    r"\[([A-Za-z0-9._/\-]{1,120})\s+((?=[0-9a-f]{7,40}\])[0-9a-f]*[a-f][0-9a-f]*)\]"
)

# Shell command separators, including the ``\n`` that survives as two literal
# characters inside a JSON-serialized tool payload. Used to bound "the same
# command" when resolving which ``--repo`` a ``gh pr`` call meant.
_RE_CMD_BOUNDARY = re.compile(r";|&&|\|\||\n|\\+n")
# Hosts that are version-control forges but not GitHub. Phase 1 reads
# GitHub only; naming them keeps the gap explicit instead of silently
# mis-attributing a GitLab MR.
UNSUPPORTED_FORGE_HOSTS = ("gitlab.com", "bitbucket.org", "dev.azure.com")


def _as_dict(value: Any) -> dict:
    """Coerce an event's ``data`` (dict, JSON string, or bytes) to a dict."""
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8", "replace")
        except Exception:
            return {}
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _event_text(event: dict) -> str:
    """Bounded, searchable text for one event.

    We serialize ``data`` rather than hunting for specific keys because the
    supported runtimes disagree on where a command lives (``input.command``,
    ``arguments``, ``toolMetas[].args``, a ``tool_use`` content block). The
    refs we want are short and appear verbatim in all of them.
    """
    data = event.get("data")
    if isinstance(data, (bytes, bytearray)):
        try:
            text = data.decode("utf-8", "replace")
        except Exception:
            return ""
    elif isinstance(data, str):
        text = data
    elif isinstance(data, dict):
        try:
            text = json.dumps(data, default=str)
        except Exception:
            return ""
    else:
        return ""
    return text[:MAX_EVENT_TEXT]


def _event_texts(event: dict) -> list[str]:
    """Texts to scan for one event, most legible first.

    The structured tool arguments come first and the whole serialized payload
    last. Both are needed: a ``gh pr`` call lives in an argument, while a
    pull-request URL often arrives in result text that no argument holds.
    Order is what makes the evidence column readable, because the first
    sighting of an artifact is the one whose snippet is kept, and a snippet
    cut from a bare command string cannot contain neighbouring JSON.
    """
    texts: list[str] = []
    try:
        from clawmetry import detectors as _dt
        et = str(event.get("event_type") or "").strip().lower()
        for call in _dt._iter_tool_calls_from_data(et, _as_dict(event.get("data"))):
            args = call.get("args")
            if isinstance(args, dict):
                for value in args.values():
                    if isinstance(value, str) and value.strip():
                        texts.append(value[:MAX_EVENT_TEXT])
            elif isinstance(args, str) and args.strip():
                texts.append(args[:MAX_EVENT_TEXT])
            if len(texts) >= MAX_TEXTS_PER_EVENT:
                break
    except Exception:
        # Degrade to the serialized payload: fewer legible snippets, same
        # artifacts found.
        pass
    whole = _event_text(event)
    if whole:
        texts.append(whole)
    return texts[:MAX_TEXTS_PER_EVENT + 1]


def _clean_evidence(text: str) -> str:
    """One-line, bounded snippet safe to store and render.

    Evidence is a slice of a real command line, so it can carry a token that
    happened to sit next to the pull-request argument (``GH_TOKEN=... gh pr
    view 1``). It therefore goes through the store's redaction chokepoint
    before it is ever persisted, shown, or carried in a snapshot. Fails
    closed: if redaction itself breaks we withhold the text rather than
    print an unscanned command.
    """
    out = " ".join(str(text or "").split())
    if out:
        try:
            from clawmetry import redaction
            out = redaction.redact_text(out)
        except Exception:
            log.warning("attribution: evidence redaction failed")
            return "[redacted]"
    if len(out) > MAX_EVIDENCE_CHARS:
        out = out[:MAX_EVIDENCE_CHARS - 1] + "…"
    # The cut itself can create markup: trimming to the cell length landed
    # inside a second anchor and left `· <a href` on the end of an otherwise
    # clean row, which no tag pattern can match because the `>` is gone.
    out = _RE_DANGLING_TAG.sub("", out)
    return out


#: JSON-escape sequences that survive serializing a tool payload and make
#: evidence unreadable in a table cell.
_UNESCAPE = (("\\\\n", " "), ("\\n", " "), ("\\\\t", " "), ("\\t", " "),
             ('\\"', '"'), ("\\\\", "\\"), ("\\u0027", "'"), ("\\x27", "'"),
             ("\\x22", '"'))

#: HTML that came in with the text. Evidence is read by a person in a table
#: cell, and ``· <a href="https://github.com/own/repo/pull/6420">Correction
#: release</a>`` is the reference buried in markup rather than shown. Four
#: live rows carried one.
#:
#: The anchor is replaced by its href, NOT merely deleted: the href is where
#: the pull-request number lives, so stripping tags alone removed the very
#: reference the row is evidence for. Every other tag goes, keeping its text.
_RE_HTML_ANCHOR = re.compile(
    r"""<a\s[^<>]{0,400}?href=["']([^"'<>]{1,400})["'][^<>]{0,400}?>""",
    re.IGNORECASE)
_RE_HTML_TAG = re.compile(r"<[^<>]{0,400}>")

#: The start of a tag with no end, which only a LENGTH cut can produce.
_RE_DANGLING_TAG = re.compile(r"\s*·?\s*<[^<>]{0,400}$")

#: A ``\uXXXX`` escape that survived the same serialization. Decoded so
#: evidence reads ``— all green`` rather than ``\u2014 all green`` (17 live
#: rows carried one). Bounded to one pass and to printable codepoints: an
#: escape that decodes to a control character becomes a space rather than
#: something that could break the cell it is rendered in.
_RE_UESCAPE = re.compile(r"\\+u([0-9a-fA-F]{4})")


#: Punctuation that only ever appears at the edge of a snippet because the
#: cut landed mid-structure. Stripped so a snippet starts and ends on
#: something a person can read.
_EDGE_JUNK = '"\'\\{}[],:;=<>|&' + " \t"

#: The same list minus ``[``, for the LEFT edge only. Once the cut is snapped
#: to a word boundary a leading ``[`` is the opening bracket of a markdown
#: link, not the debris of a cut, and stripping it turned
#: ``[vivekchand/clawmetry#6186](...`` into ``vivekchand/clawmetry#6186](...``
#: on every prose row.
_EDGE_JUNK_LEAD = _EDGE_JUNK.replace("[", "")


#: A tool payload wraps the real command in a key-and-quote opener:
#: ``tools.exec_command({cmd:"gh pr view 1"``, ``"content": "https://...``,
#: ``url: 'https://...``. The command starts AFTER the last such opener that
#: precedes the match, so anchoring there is what makes evidence read as the
#: command rather than as the harness that ran it.
#:
#: The quotes carry a backslash run, because the payload the text came out of
#: was serialized at least once: live data reads ``{cmd:\\"gh pr view 6350``,
#: not ``{cmd:"gh pr view 6350``. A pattern that insisted on a bare quote
#: matched nothing on a real node, which is how the first version of this fix
#: measured as a no-op.
_QUOTE = r"""(?:\\*["'])"""
_RE_WRAPPER_OPEN = re.compile(
    _QUOTE + r"?([A-Za-z_][A-Za-z0-9_]*)" + _QUOTE + r"?\s*:\s*" + _QUOTE)

#: The tail the same wrapper leaves once the command ends:
#: ``--json url",max_output_tokens:3000}))`` or ``",workdir":"/tmp"``. Cut
#: there so the snippet ends on the command and not on the harness's own
#: keyword arguments.
_RE_WRAPPER_TAIL = re.compile(
    _QUOTE + r"[\s}\]),{]*" + _QUOTE + r"?[A-Za-z_][A-Za-z0-9_]*" + _QUOTE + r"?\s*:")

#: Characters a readable snippet is allowed to begin on.
_SNIPPET_BOUNDARY = " \t\n"

#: How far back a snippet may reach to finish the word it was cut inside.
#: Small on purpose: this buys back ``2026-09-25`` from ``026-09-25``, not a
#: paragraph of run-up.
_SNAP_BACK_BUDGET = 24


def _decode_uescape(match: "re.Match") -> str:
    """One ``\\uXXXX`` escape as the character it stands for.

    Anything that is not printable becomes a space: evidence lands in a table
    cell and in a snapshot, and a decoded control character belongs in
    neither.
    """
    try:
        ch = chr(int(match.group(1), 16))
    except Exception:  # pragma: no cover - the regex already bounds this
        return " "
    return ch if ch.isprintable() else " "


def _readable(text: str) -> str:
    """Undo the JSON escaping a serialized tool payload leaves behind.

    Evidence is shown to a human under a column headed "How we know", so it
    has to read as the command that ran. Taken raw out of the serialized
    payload it reads as ``g8K1dkHAfbFFR3s9ods", "name": "Bash", "input": {``
    or ``ionGroups\\\\\\":[],\\\\\\"url\\\\\\":...`` (both measured on live
    data).

    Escaping is undone repeatedly because a payload that was serialized more
    than once (a tool result quoting a tool result) carries ``\\\\\\"`` and
    deeper. Bounded to three passes: enough for every real nesting depth, and
    not a loop whose cost depends on hostile input.
    """
    out = str(text or "")
    for _ in range(3):
        before = out
        for src, dst in _UNESCAPE:
            out = out.replace(src, dst)
        if out == before:
            break
    out = _RE_UESCAPE.sub(_decode_uescape, out)
    # Entities first, so `&middot;` becomes a character rather than the
    # stray `middot;` that edge-trimming the `&` would leave behind.
    try:
        out = html.unescape(out)
    except Exception:  # pragma: no cover - unescape does not raise in practice
        pass
    out = _RE_HTML_ANCHOR.sub(r" \1 ", out)
    out = _RE_HTML_TAG.sub(" ", out)
    return out.lstrip(_EDGE_JUNK_LEAD).rstrip(_EDGE_JUNK)


def _unwrap_start(text: str, lo: int, start: int) -> int:
    """Move *lo* past the wrapper that encloses the command at *start*.

    Measured on live data: Codex records a shell call as
    ``text(await tools.exec_command({cmd:"gh pr edit 6248 --repo ...`` and a
    tool result as ``"role": "tool", "content": "https://.../pull/6367``. The
    reference and the command were both legible, but the row opened on the
    harness instead of on the work, so a reader had to parse past it on every
    line. Only openers BEFORE the match are considered, so the reference can
    never be cut away.
    """
    best = lo
    for m in _RE_WRAPPER_OPEN.finditer(text, lo, start):
        if m.end() > best:
            best = m.end()
    return best


def _snap_start(text: str, lo: int, floor: int, start: int) -> int:
    """Put *lo* on a word boundary so the snippet opens on a whole token.

    A fixed run-up lands wherever it lands: live rows opened on ``026-09-25``
    (from ``2026-09-25``), ``ll/975), [#978](`` and ``clawmetry#6186](``.
    Finishing the word backwards is preferred because it keeps the context
    that was already there; when that would cost more than
    ``_SNAP_BACK_BUDGET`` the cut moves forward to the next boundary instead.
    Never crosses *start*, so the reference stays in the snippet either way.
    """
    if lo <= floor or lo >= start:
        return lo
    if text[lo - 1] in _SNIPPET_BOUNDARY or text[lo] in _SNIPPET_BOUNDARY:
        return lo
    back = max(text.rfind(c, max(floor, lo - _SNAP_BACK_BUDGET), lo)
               for c in _SNIPPET_BOUNDARY)
    if back >= 0:
        return back + 1
    fwd = min((p for p in (text.find(c, lo, start) for c in _SNIPPET_BOUNDARY)
               if p >= 0), default=-1)
    if fwd >= 0:
        return fwd + 1
    return lo


def _snippet_around(text: str, start: int, end: int, width: int = 60) -> str:
    """Evidence snippet: the command the match sits in.

    Bounded to the match's own command (see :func:`_command_window`) rather
    than a fixed character window, because a fixed window lands in whatever
    JSON happened to be adjacent. When the command is longer than the cell,
    the match stays centred so the pull-request number is always visible.

    The window is then tightened to the command itself: past the wrapper that
    a tool payload puts in front of it (:func:`_unwrap_start`), before the
    keyword arguments it leaves behind (``_RE_WRAPPER_TAIL``), and onto a word
    boundary (:func:`_snap_start`). None of this can move the cut across the
    match, so every snippet still contains the reference it is evidence for.
    """
    lo, hi = _command_window(text, start)
    if lo > start or hi < end:  # pragma: no cover - defensive
        lo, hi = max(0, start - width), min(len(text), end + width)
    lo = _unwrap_start(text, lo, start)
    tail = _RE_WRAPPER_TAIL.search(text, end, hi)
    if tail is not None:
        hi = tail.start() + 1
    floor = lo
    if (hi - lo) > MAX_EVIDENCE_CHARS:
        # Lead with the reference itself, keeping a short run-up so a command
        # still shows its verb. Centring put the claim in the middle of
        # whatever JSON happened to surround it.
        lead = 24
        lo = max(lo, start - lead)
        hi = min(hi, lo + MAX_EVIDENCE_CHARS)
    lo = _snap_start(text, lo, floor, start)
    return _clean_evidence(_readable(text[lo:hi]))


def _ts_of(event: dict) -> str:
    """The event's timestamp as a sortable string ('' when absent)."""
    ts = event.get("ts")
    return str(ts) if ts not in (None, "") else ""


def _cost_of(event: dict) -> float:
    """Cost in USD for one event, from the column or the usage payload.

    The store's ``events.cost_usd`` column is authoritative when present.
    Family adapters additionally carry it at ``data.extra.costUsd`` (the
    shape ``usage`` events use), so we fall back to that before giving up.
    Never raises: a malformed number is 0.0, not a crash.
    """
    raw = event.get("cost_usd")
    if raw in (None, ""):
        extra = _as_dict(event.get("data")).get("extra")
        if isinstance(extra, dict):
            raw = extra.get("costUsd", extra.get("cost_usd"))
    try:
        value = float(raw or 0.0)
    except (TypeError, ValueError):
        return 0.0
    # A negative or non-finite cost is bad input, not a credit.
    if value != value or value in (float("inf"), float("-inf")) or value < 0:
        return 0.0
    return value


def chronological(events: Iterable[dict]) -> list[dict]:
    """Oldest-first event list.

    ``local_store.query_events`` returns newest-first. We sort on ``ts``
    when every event has one (robust against a caller that already
    reversed), and otherwise fall back to reversing the input, which is the
    convention ``detectors.normalize_events`` relies on.
    """
    evlist = [e for e in events if isinstance(e, dict)]
    if not evlist:
        return []
    stamps = [_ts_of(e) for e in evlist]
    if all(stamps):
        # Stable sort: equal timestamps keep their relative input order.
        order = sorted(range(len(evlist)), key=lambda i: stamps[i])
        ascending = order == list(range(len(evlist)))
        descending = order == list(reversed(range(len(evlist))))
        if ascending:
            return evlist
        if descending:
            return list(reversed(evlist))
        return [evlist[i] for i in order]
    return list(reversed(evlist))


def _command_window(text: str, pos: int) -> tuple[int, int]:
    """Bounds of the single shell command containing offset *pos*.

    One tool call routinely chains several commands against DIFFERENT repos
    (``gh run list --repo A; gh pr checks 2566 --repo B``). Resolving a
    ``--repo`` flag against the whole payload therefore attributed PR 2566
    to repo A, which showed up as the same pull request appearing under two
    repositories. Scoping the lookup to one command is the fix.
    """
    lo = 0
    hi = len(text)
    for m in _RE_CMD_BOUNDARY.finditer(text):
        if m.end() <= pos:
            lo = m.end()
        elif m.start() >= pos:
            hi = m.start()
            break
    return lo, hi


def _extends_without_separator(short_tail: str, long_tail: str) -> bool:
    """True when *long_tail* continues *short_tail* in the MIDDLE of a token.

    This is the whole difference between a name that arrived cut short and a
    different repository that merely starts the same way:

    * ``clawm`` -> ``clawmetry`` resumes at ``e``, inside a word. A cut.
    * ``clawmetry`` -> ``clawmetry-cloud`` resumes at ``-``, a token
      boundary. Two repositories.

    A plain prefix test cannot tell them apart, and shipping one deleted
    ``vivekchand/clawmetry`` -- the busiest repository on the node -- from 49
    sessions' Repositories lists, and re-labelled 71 pull requests and $348.74
    as ``vivekchand/clawmetry-cloud`` while the evidence on the very same row
    read ``--repo vivekchand/clawmetry``. A wrong repository is worse than a
    blank one: it reads as an answer.
    """
    if long_tail == short_tail or not long_tail.startswith(short_tail):
        return False
    return long_tail[len(short_tail)] not in _NAME_SEPARATORS


def _line_bounds(text: str, start: int) -> tuple[int, int]:
    """The line *start* sits on, for a guard that reads one line only.

    An event's text does not always arrive as the agent saw it. A tool_call
    hands over the command verbatim, newlines intact, but a tool_result is
    read out of the event's JSON, where a newline is the two characters
    ``\\n``. Splitting on the real character alone therefore made a whole
    multi-line tool result ONE line, and a documentation example at the top
    of a long output reached down and deleted a real repository named on a
    later line. Both forms are treated as a break.
    """
    real = text.rfind("\n", 0, start)
    escaped = text.rfind("\\n", 0, start)
    lo = 0
    if real != -1:
        lo = real + 1
    if escaped != -1:
        lo = max(lo, escaped + 2)
    ends = [e for e in (text.find("\n", start), text.find("\\n", start))
            if e != -1]
    return lo, (min(ends) if ends else len(text))


#: A pytest node id: ``path::test_name[the parameter]``. What follows is a
#: SPECIMEN a test was parametrised with, not a command anyone ran.
_RE_TEST_NODE_ID = re.compile(r"::test_[A-Za-z0-9_]+\[")


def _inside_test_node_id(text: str, start: int) -> bool:
    """True when the match sits inside a pytest node id's parameter.

    Four live branch rows read ``feat/x-feat/x`` and
    ``fix/home-session-activity-fix/home-session-activity``: a node id repeats
    the parameter after the test name, so the doubled name is the id's own
    shape rather than anything a session pushed. The agent runs this
    repository's tests all day, so its output is in the stream it reads.

    Only the match's own line is examined, so a test id elsewhere in the
    snippet cannot disqualify a real command.
    """
    line_start, _ = _line_bounds(text, start)
    return bool(_RE_TEST_NODE_ID.search(text, line_start, start))


#: A line that announces its own contents as an illustration.
_RE_EXAMPLE_ANNOUNCE = re.compile(
    r"\b(?:examples?\b|e\.g\.|for\s+example\b)", re.I)

#: A domain RFC 2606 reserves for documentation. Nobody serves a repository
#: from one, so its presence says the line is written to be read, not run.
_RE_RESERVED_EXAMPLE_DOMAIN = re.compile(r"\bexample\.(?:com|org|net)\b", re.I)


def _inside_example_list(text: str, start: int) -> bool:
    """True when the match sits in a line that declares itself an example.

    A documentation line reading::

        URL. Examples: `https://github.com/openai/openai/pulls/123`,
        `https://api.github.com/repos/openai/openai`,
        `https://github.example.com/api/v3/repos/octo/repo`.

    put ``openai/openai`` -- an account nobody has -- on the live tab in two
    sessions, and in one of them that phantom gave the session a second
    repository, so the fold could no longer tell which repository a real
    pull request belonged to and the row lost its label.

    **Two signals are required, and the second one is the point.** Measured
    over the 1120 repository and pull-request rows on a live node, the word
    ``example`` alone also appears on the evidence of four REAL repositories:
    ``Tavus-Engineering/tavus-examples`` carries it in its own name, and
    ``CopilotKit/OpenBot`` and ``CopilotKit/OpenTag`` were each sighted
    through a path ending ``.env.example``. Requiring a reserved
    documentation domain on the same line leaves all four standing and
    removes only the two phantoms. A filter's half that matters is what it
    does NOT remove.

    Only the match's own line is examined, so an example elsewhere in a long
    snippet cannot disqualify a real command. The announcement is required
    to come before the match, because a sentence cannot illustrate something
    it has not reached yet; the reserved domain may sit anywhere on the line,
    since it is the line as a whole that it marks as specimen text.
    """
    line_start, line_end = _line_bounds(text, start)
    if not _RE_RESERVED_EXAMPLE_DOMAIN.search(text, line_start, line_end):
        return False
    # ``example.com`` contains the word ``example``, so left alone the
    # reserved domain answers BOTH halves by itself and the rule collapses
    # into a single signal: a line reading "mirror at example.com of
    # <a real repository URL>" lost its repository. Mask the domains out of
    # the text before the match, then look for a real announcement in what
    # is left.
    head = _RE_RESERVED_EXAMPLE_DOMAIN.sub(" ", text[line_start:start])
    return bool(_RE_EXAMPLE_ANNOUNCE.search(head))


def _is_placeholder_repo(name: str) -> bool:
    """True when *name* is a stand-in for an account rather than one."""
    name = str(name or "").strip().strip("/").rstrip(".,;:!?)]}\"'")
    owner, _, repo = name.partition("/")
    if not owner or not repo:
        return False
    if owner.lower() in PLACEHOLDER_REPO_OWNERS:
        return True
    return len(owner) <= 2 and len(repo) <= 2


def _evidence_contradicts(evidence: str, repo: str) -> bool:
    """True when the snippet names a DIFFERENT repository than its own row.

    The evidence column exists for a reader to check the row against, so a
    snippet reading ``--repo vivekchand/c`` under a row filed to
    ``vivekchand/clawmetry`` fails at the one job it has.
    """
    if not evidence or not repo:
        return False
    named = set(_RE_REPO_FLAG.findall(evidence))
    return bool(named) and repo not in named


def _clean_repo(name: str) -> str:
    """A repository name, or ``""`` when what arrived is not one.

    Three shapes reached the live tab as repositories after the reserved-owner
    fix, each well-formed enough that no shape test could object:

    * **A placeholder** -- ``owner/repo``, ``OWNER/REPO``, ``own/repo``,
      ``octocat/Hello-World``. Out of help text, docs and this repository's own
      test fixtures. See :data:`PLACEHOLDER_REPO_OWNERS`.
    * **A sentence's full stop glued on** -- ``vivekchand/clawmetry.`` and
      ``julienXX/terminal-notifier.``, which GitHub will not accept as a name.
      Left alone it also SPLITS one real repository across two rows.
    * **A display truncation** -- ``mitre-atlas/atlas-...e``, cut in the
      middle by whatever rendered it, so there is no name here to recover.
    """
    name = str(name or "").strip().strip("/")
    # Prose punctuation, never an interior character: a name cannot end in
    # any of these, so removing them loses nothing real.
    name = name.rstrip(".,;:!?)]}\"'")
    if "..." in name or "\u2026" in name:
        return ""
    owner, _, repo = name.partition("/")
    if not owner or not repo or "/" in repo:
        return ""
    # A git config KEY, not a repository: ``actions/checkout`` writes
    # ``http.https://github.com/OWNER/NAME.extraheader`` on every CI run. The
    # repository inside the key is real, so the variable is removed and a
    # ``.git`` it was sitting behind goes with it, rather than the sighting
    # being dropped.
    head, dot, tail = repo.rpartition(".")
    if dot and tail.lower() in GIT_HTTP_CONFIG_VARS:
        repo = head[:-4] if head.lower().endswith(".git") else head
        if not repo:
            return ""
        name = f"{owner}/{repo}"
    low = owner.lower()
    if low in RESERVED_GITHUB_OWNERS or low in PLACEHOLDER_REPO_OWNERS:
        return ""
    # ``o/n``, ``a/b``, ``x/y``: a shape nobody ships real work under.
    if len(owner) <= 2 and len(repo) <= 2:
        return ""
    return name


def _repo_for_match(text: str, start: int, end: int) -> str:
    """The ``--repo owner/name`` that belongs to the command at this match.

    Looked up inside the match's own command window only, so a neighbouring
    command's repo can never leak in.
    """
    lo, hi = _command_window(text, start)
    window = text[lo:hi]
    best = ""
    best_distance = None
    for m in _RE_REPO_FLAG.finditer(window):
        # Distance from the pull-request token, so the nearest flag wins when
        # one command somehow carries two.
        distance = abs((lo + m.start()) - end)
        if best_distance is None or distance < best_distance:
            best, best_distance = m.group(1), distance
    # RAW on purpose: the caller has to see a placeholder to know the whole
    # command is a specimen, which cleaning here would hide.
    return best


def _find_pr_refs(text: str) -> list[dict]:
    """Every pull-request reference in one event's text.

    Two independent patterns, and the URL form is strongest because it
    carries the repo with the number:

    - ``github.com/owner/repo/pull/6275`` -> confidence 1.0, repo known
    - ``gh pr checks 6275 --repo owner/repo`` -> confidence 1.0, repo taken
      from the ``--repo`` flag in that same command (see
      :func:`_repo_for_match`)

    Returns ``[{pr, repo, role, confidence, evidence, source}, ...]``.
    """
    refs: list[dict] = []

    for m in _RE_PR_URL.finditer(text):
        if _inside_example_list(text, m.start()):
            continue
        refs.append({
            "pr": m.group(2),
            "repo": _clean_repo(m.group(1)),
            "role": ROLE_EXPLORED,
            "confidence": 1.0,
            "evidence": _snippet_around(text, m.start(), m.end()),
            "source": "pr_url",
        })

    for m in _RE_GH_PR.finditer(text):
        verb = m.group(1).lower()
        if verb not in _GH_PR_VERBS:
            continue
        if _inside_test_node_id(text, m.start()):
            continue
        if _inside_example_list(text, m.start()):
            continue
        role = ROLE_AUTHORED if verb in _GH_PR_AUTHOR_VERBS else ROLE_REVIEWED
        raw_repo = _repo_for_match(text, m.start(), m.end())
        if _is_placeholder_repo(raw_repo):
            # A command naming a placeholder repository is a specimen out of
            # help text, documentation or a test fixture, so the NUMBER in it
            # is not a pull request either. Blanking only the repository left
            # the number behind, and the fold then dressed it in a real
            # repository: a line of this repo's own test source became a
            # $0.27 pull request "#2" in ``vivekchand/clawmetry-pro``. A
            # number that the session also names for real keeps its row,
            # because that sighting arrives by its own route.
            continue
        refs.append({
            "pr": m.group(2),
            "repo": _clean_repo(raw_repo),
            "role": role,
            "confidence": 1.0,
            "evidence": _snippet_around(text, m.start(), m.end()),
            "source": f"gh_pr_{verb}",
        })
    return refs


def _find_repo_refs(text: str) -> list[dict]:
    """Every repository named in one event's text.

    A match whose first path segment is one of GitHub's own pages
    (:data:`RESERVED_GITHUB_OWNERS`) is dropped rather than filed: a row
    reading ``site-policy/github-terms`` tells the reader the session worked
    on a repository nobody has.
    """
    out: list[dict] = []
    for pattern, source in ((_RE_REPO_FLAG, "repo_flag"),
                            (_RE_REPO_REMOTE, "remote_url"),
                            (_RE_REPO_API, "api_url")):
        for m in pattern.finditer(text):
            if _inside_example_list(text, m.start()):
                continue
            name = _clean_repo(m.group(1))
            if not name:
                continue
            out.append({
                "repo": name,
                "role": ROLE_EXPLORED,
                "confidence": 0.9 if source == "repo_flag" else 0.7,
                "source": source,
                "evidence": _snippet_around(text, m.start(), m.end()),
            })
    return out


def _find_branch_refs(text: str) -> list[dict]:
    """Branches the session created or pushed.

    Creation (``-b``) is authoring; a push is authoring too. We deliberately
    skip a plain ``git checkout <name>``: moving onto an existing branch is
    not evidence the session produced anything on it.
    """
    refs: list[dict] = []
    for pattern, source, conf in ((_RE_BRANCH_NEW, "branch_created", 1.0),
                                  (_RE_BRANCH_PUSH, "branch_pushed", 0.9)):
        for m in pattern.finditer(text):
            if _inside_test_node_id(text, m.start()):
                continue
            # _clean_branch sees the RAW capture: the trailing "/" is the
            # signal that this was ``release/<slug>`` in a doc, and stripping
            # it first turned the placeholder into the branch "release".
            name = _clean_branch(m.group(1)).strip(".")
            if not name or name in ("HEAD", "origin", "main", "master"):
                # main/master are shared trunks, not a unit of delivery.
                continue
            refs.append({
                "branch": name,
                "role": ROLE_AUTHORED,
                "confidence": conf,
                "evidence": _snippet_around(text, m.start(), m.end()),
                "source": source,
            })
    return refs


def _find_commit_refs(text: str) -> list[dict]:
    """Commits this session actually created, read from ``git commit`` output."""
    refs: list[dict] = []
    for m in _RE_COMMIT_OUT.finditer(text):
        branch, sha = m.group(1), m.group(2)
        # ``[main 0123abc]`` from a *log* read would be a false positive, but
        # git only prints this bracket form on commit, so the shape is the
        # proof. Keep the branch alongside: it is how a commit joins a PR.
        refs.append({
            "commit": sha,
            "branch": branch,
            "role": ROLE_AUTHORED,
            "confidence": 0.9,
            "evidence": _snippet_around(text, m.start(), m.end()),
            "source": "git_commit_output",
        })
    return refs


def _merge_ref(bucket: dict, key: tuple, row: dict, ts: str) -> None:
    """Accumulate one artifact row, keeping the strongest claim.

    First and last sighting bound the stretch of the session that touched
    the artifact; role and confidence only ever ratchet up, so a session
    that reviews a PR and later merges it ends up ``authored``.
    """
    existing = bucket.get(key)
    if existing is None:
        row = dict(row)
        row["first_ts"] = ts
        row["last_ts"] = ts
        row["mentions"] = 1
        bucket[key] = row
        return
    existing["mentions"] = int(existing.get("mentions") or 0) + 1
    if ts:
        if not existing.get("first_ts") or ts < existing["first_ts"]:
            existing["first_ts"] = ts
        if not existing.get("last_ts") or ts > existing["last_ts"]:
            existing["last_ts"] = ts
    new_role = row.get("role") or ROLE_EXPLORED
    old_role = existing.get("role") or ROLE_EXPLORED
    if _ROLE_RANK.get(new_role, 0) > _ROLE_RANK.get(old_role, 0):
        existing["role"] = new_role
        existing["evidence"] = row.get("evidence") or existing.get("evidence")
        existing["source"] = row.get("source") or existing.get("source")
    try:
        if float(row.get("confidence") or 0) > float(existing.get("confidence") or 0):
            existing["confidence"] = float(row["confidence"])
    except (TypeError, ValueError):
        pass
    # Backfill a repo we learned later (a bare ``gh pr view 6275`` followed
    # by a ``--repo`` form in the same session).
    if not existing.get("repo") and row.get("repo"):
        existing["repo"] = row["repo"]


def _fold_bare_pr_rows(prs: dict, repos: dict) -> dict:
    """Collapse the same pull request held under a bare and a repo-qualified key.

    A session names a pull request both ways — ``gh pr checks 6283`` early,
    ``gh pr merge 6283 --repo vivekchand/clawmetry`` later — and each spelling
    gets its own key. On the live node that put 81 pull requests on the tab
    TWICE, once with a repository and once with the cell blank, and (before
    the cost distribution below) charged the same money to both.

    Two passes, neither of which guesses:

    * **Sole repo.** One repository in the whole session owns a pull request
      that never carried a ``--repo`` flag. Confidence drops, because the
      repository is inferred rather than observed.
    * **Unique sibling.** A bare row folds into the one repo-qualified row
      with the same number. With two such rows (``clawmetry#302`` and
      ``clawmetry-pro#302`` both named) the bare row is left alone: a wrong
      repository is worse than a blank one.
    """
    only_repo = next(iter(repos))[0] if len(repos) == 1 else ""
    folded: dict[tuple, dict] = {}
    for (repo, pr), row in prs.items():
        if not repo and only_repo:
            row["repo"] = only_repo
            row["confidence"] = min(float(row.get("confidence") or 1.0), 0.8)
            row["source"] = f"{row.get('source') or 'pr'}+sole_repo"
        _fold_into(folded, (row.get("repo") or "", pr), row)
    # Second pass: a bare row whose number appears under exactly one repo.
    qualified: dict[str, list[tuple]] = {}
    for key in folded:
        if key[0]:
            qualified.setdefault(key[1], []).append(key)
    out: dict[tuple, dict] = {}
    for key, row in folded.items():
        target = key
        if not key[0]:
            siblings = qualified.get(key[1]) or []
            if len(siblings) == 1:
                target = siblings[0]
                row = dict(row)
                row["repo"] = target[0]
                row["confidence"] = min(float(row.get("confidence") or 1.0), 0.8)
                row["source"] = f"{row.get('source') or 'pr'}+same_number"
        _fold_into(out, target, row)
    return out


def _fold_into(bucket: dict, key: tuple, row: dict) -> None:
    """Merge *row* into ``bucket[key]``, or seat it there if the key is free.

    Confidence takes the WEAKER of the two, because part of a folded row
    rests on an inferred repository; everything else ratchets up the way
    :func:`_merge_ref` already defines.
    """
    if key not in bucket:
        bucket[key] = row
        return
    # Picked BEFORE the merge, and from both sides, because :func:`_merge_ref`
    # installs the strongest ROLE's snippet and that can be the one naming the
    # name we just rejected. Which side seats first decides whether it wins,
    # so checking only afterwards fixed one fold order and not the other.
    keeper = ""
    for candidate in (bucket[key].get("evidence"), row.get("evidence")):
        if candidate and not _evidence_contradicts(candidate, key[0]):
            keeper = candidate
            break
    _merge_ref(bucket, key, row, row.get("first_ts") or "")
    existing = bucket[key]
    existing["last_ts"] = max(existing.get("last_ts") or "",
                              row.get("last_ts") or "")
    existing["confidence"] = min(float(existing.get("confidence") or 1.0),
                                 float(row.get("confidence") or 1.0))
    # Five live rows were filed correctly and evidenced by ``--repo
    # vivekchand/c``, the name that had just been rejected. The column exists
    # to be checked against the row, so it has to agree with it.
    if keeper and _evidence_contradicts(existing.get("evidence") or "", key[0]):
        existing["evidence"] = keeper


def _distribute_pr_cost(per_pr: dict, prs: dict) -> tuple[dict, float]:
    """Charge every segment of the cost split to exactly one artifact row.

    :func:`split_cost` keys a segment on the repository it could see AT THE
    TIME it walked the stream, so its keys and the folded artifact keys do
    not line up one for one. The previous mapping was a lookup with a
    fallback — ``per_pr[repo#pr]`` or else ``per_pr[#pr]`` — and it was wrong
    in both directions on live data:

    * the fallback fired for a repo-qualified row while a bare row was
      *also* emitted, so both rows claimed the same segment and the node's
      attributed total over-reported by **$327.92**;
    * where the two keys were folded into one row only one key was read, so
      the other segment's money was reported nowhere at all (**$5.00** lost
      in one session alone).

    This walks the segments instead of the rows, so each segment lands once
    and nothing is read twice. Whatever cannot be placed on a single row is
    returned as the remainder, which the caller reports as unattributed:
    under-claiming is honest, double-counting is not.
    """
    by_number: dict[str, list[tuple]] = {}
    for key in prs:
        by_number.setdefault(key[1], []).append(key)
    charged: dict[tuple, float] = {}
    leftover = 0.0
    for key, usd in per_pr.items():
        repo, _, pr = key.rpartition("#")
        target = (repo, pr) if (repo, pr) in prs else None
        if target is None:
            siblings = by_number.get(pr) or []
            if len(siblings) == 1:
                target = siblings[0]
        if target is None:
            leftover += usd
            continue
        charged[target] = charged.get(target, 0.0) + usd
    return charged, round(leftover, 6)


def split_cost(chron_events: list[dict], *, pr_key_of=None) -> dict:
    """Attribute each cost-bearing event to the PR that was in play.

    **The problem this solves.** One session touches many pull requests, so
    joining a session's total cost to each PR it mentions multiplies the
    money: on a real $3,843 node that join reported a single $106,946 pull
    request. Cost has to be divided, not copied.

    **The rule.** Walk the session forward in time carrying "the PR most
    recently referenced". Every event's cost belongs to that PR; cost
    before the first PR reference (and in sessions that never name one) is
    ``unattributed_usd``. This is last-touch segment attribution, declared
    as ``basis="last_touch_segment"``, and it is exact in the sense that
    matters: the parts always sum to the whole.

    Returns ``{"per_pr": {key: usd}, "unattributed_usd": float,
    "total_usd": float, "basis": str}``.
    """
    per_pr: dict[str, float] = {}
    unattributed = 0.0
    total = 0.0
    current: Optional[str] = None
    for event in chron_events:
        # Same candidate texts the extraction pass uses, so the PR a cost is
        # charged to is always one the artifact list also contains.
        for text in _event_texts(event):
            if not text:
                continue
            refs = _find_pr_refs(text)
            if refs:
                last = refs[-1]
                current = (pr_key_of(last) if pr_key_of
                           else f"{last.get('repo') or ''}#{last['pr']}")
        cost = _cost_of(event)
        if cost <= 0:
            continue
        total += cost
        if current is None:
            unattributed += cost
        else:
            per_pr[current] = per_pr.get(current, 0.0) + cost
    basis = "last_touch_segment" if total > 0 else "unknown"
    return {
        "per_pr": {k: round(v, 6) for k, v in per_pr.items()},
        "unattributed_usd": round(unattributed, 6),
        "total_usd": round(total, 6),
        "basis": basis,
    }


#: Characters a path we are willing to PRINT may contain. Everything else
#: ends the path: the step normalizer hands back whatever sat next to the
#: match, so a Codex payload yields ``.claude/sf_client.py\\",\\"max_output_
#: tokens\\":10000}))`` and an HTML edit yields ``<tr><td>Vapi</td><td>Voice``.
#: 52% of the file rows on the live tab were not paths at all.
_RE_PATH_STOP = re.compile(r"[^A-Za-z0-9_./+@~\-]")

#: Conventional files that carry no extension. Without them a ``Makefile``
#: write is dropped by the dot-or-slash test below.
_EXTENSIONLESS = frozenset((
    "makefile", "dockerfile", "license", "licence", "readme", "changelog",
    "notice", "procfile", "jenkinsfile", "codeowners", "authors", "contributing",
))


def _clean_path(name: str) -> str:
    """A written path we are prepared to show, or ``""``.

    Trimmed at the first character that cannot be in a path, which recovers
    the real path from a serialized payload's tail, and then held to a shape
    test: a flag is not a path, a glob is not a path, and an HTML fragment is
    not a path. Dropping a row is the honest failure here — a fabricated
    filename teaches the reader that the table invents things.
    """
    raw = str(name or "").strip()
    stop = _RE_PATH_STOP.search(raw)
    if stop is not None and stop.group(0) in "*?[":
        # A glob is a pattern, not a file the session wrote. Trimming it would
        # turn ``/admin/*`` into the directory ``/admin``, which is a claim
        # nobody made.
        return ""
    out = raw[:stop.start()] if stop else raw
    out = out.strip().rstrip("/")
    if not out or len(out) > 512 or out.startswith("-"):
        return ""
    base = out.rsplit("/", 1)[-1]
    if not base or base in (".", ".."):
        return ""
    if base.lower() in _EXTENSIONLESS:
        return out
    stem, dot, ext = base.rpartition(".")
    if dot and stem and ext and ext.isalnum() and len(ext) <= 12:
        return out
    # No extension. Only an explicitly rooted path is still credible, and
    # only with more than one segment: ``origin/main`` and
    # ``vivekchand/clawmetry-cloud`` are a git ref and a repository, not
    # files, and ``/search`` / ``/heading`` are an ARIA role and a URL path.
    # All four were listed as files the session wrote.
    rooted = out.startswith(("/", "./", "../", "~/"))
    if rooted and out.strip("/").count("/") >= 1:
        return out
    return ""


def _whole_repo_name(name: str, known) -> str:
    """The full form of *name* when the session also saw it uncut.

    A pull request carries its OWN repository string, resolved from the
    ``--repo`` flag in its command, not the repository bucket. So dropping a
    truncated name from that bucket left the pull-request rows still filed
    under it: ``vivekchand/clawm`` was gone from Repositories and still on
    the Pull requests tab. Repairing is better than dropping here, because
    the whole name is known — the row is real, only its label was cut.

    Ambiguous (two known names extend it) means leave it alone rather than
    pick one.
    """
    owner, _, tail = str(name or "").partition("/")
    if not tail:
        return name
    # It survived :func:`_drop_truncated_repos`, so it is a repository in its
    # own right and there is nothing to repair. Without this, a pull request
    # in ``clawmetry`` was re-filed under ``clawmetry-cloud``.
    if name in known:
        return name
    matches = {k for k in known
               if k != name
               and k.partition("/")[0] == owner
               and _extends_without_separator(tail, k.partition("/")[2])}
    return matches.pop() if len(matches) == 1 else name


def _is_cut_short(name: str, known) -> bool:
    """True when *name* is some known repository with its end missing.

    ``name in known`` settles it first: the bucket has already had its cut
    names removed, so anything still in it is real.
    """
    if not name or name in known:
        return False
    owner, _, tail = name.partition("/")
    if not tail:
        return False
    return any(k != name and k.partition("/")[0] == owner
               and _extends_without_separator(tail, k.partition("/")[2])
               for k in known)


def _repair_pr_repos(prs: dict, repos: dict) -> dict:
    """Re-key pull-request rows whose repository name arrived cut short.

    Repair when the whole name is known. When it is NOT -- ``vivekchand/c``
    extends to five known names, so no single one can be chosen -- the row
    keeps its number and LOSES the repository. Leaving the cut name in place
    is what put six rows reading ``vivekchand/c`` on the live tab: the
    ambiguous case was treated as nothing to do.
    """
    known = {k[0] for k in repos}
    out: dict = {}
    for (repo, pr), row in prs.items():
        whole = _whole_repo_name(repo, known) if repo else repo
        if whole != repo:
            row = dict(row)
            row["repo"] = whole
            row["source"] = f"{row.get('source') or 'pr'}+whole_name"
        elif _is_cut_short(whole, known):
            whole = ""
            row = dict(row)
            row["repo"] = ""
            row["confidence"] = min(float(row.get("confidence") or 1.0), 0.6)
            row["source"] = f"{row.get('source') or 'pr'}+cut_name_dropped"
        _fold_into(out, (whole, pr), row)
    return out


def _fold_repo_case(repos: dict, prs: dict) -> tuple[dict, dict]:
    """One repository spelled two ways is one row.

    GitHub treats an owner and a name case-insensitively, so a session that
    reads ``NVIDIA/OpenShell`` from a URL and ``nvidia/openshell`` from a
    clone path has seen one repository, and the live tab listed it twice.
    The spelling with the most sightings wins, because the one a session
    mentions most is the one its author typed; ties keep the first seen, so
    the choice never depends on dict ordering.

    Pull-request rows are re-spelled to match, or the two halves of the tab
    would disagree about the same repository's name.
    """
    best: dict[str, str] = {}
    score: dict[str, int] = {}
    for key, row in repos.items():
        low = str(key[0]).lower()
        mentions = int(row.get("mentions") or 1)
        if low not in best or mentions > score[low]:
            best[low], score[low] = key[0], mentions
    folded: dict = {}
    for key, row in repos.items():
        canon = best[str(key[0]).lower()]
        if canon != key[0]:
            row = dict(row)
            row["repo"] = canon
            row["source"] = f"{row.get('source') or 'repo'}+case"
        _fold_into(folded, (canon,) + tuple(key[1:]), row)
    out_prs: dict = {}
    for (repo, pr), row in prs.items():
        canon = best.get(str(repo).lower(), repo)
        if canon != repo:
            row = dict(row)
            row["repo"] = canon
        _fold_into(out_prs, (canon, pr), row)
    return folded, out_prs


def _drop_truncated_repos(repos: dict) -> dict:
    """Remove a repository name that is a cut-short form of another one here.

    Live rows carried ``vivekchand/c`` and ``vivekchand/clawm``, which are no
    repositories at all. The cause is upstream: the text we read had already
    been cut mid-token by whatever produced it
    (``gh pr view 6354 --repo vivekchand/c`` then a line break), so there is
    nothing in the command itself to tell a complete value from a cut one.

    What CAN be checked is the rest of the session: if a longer name was also
    seen and the short one is a prefix of it under the same owner, the short
    one is that name with its end missing. Two genuinely distinct repositories
    where one name prefixes the other (``own/claw`` beside ``own/clawmetry``)
    would lose the shorter row, which is the right way round — the tab
    claiming a repository nobody has is the failure that matters.
    """
    names = [k[0] for k in repos]
    drop = set()
    for short in names:
        owner, _, tail = short.partition("/")
        if not tail:
            continue
        for other in names:
            if other == short:
                continue
            o_owner, _, o_tail = other.partition("/")
            if o_owner == owner and _extends_without_separator(tail, o_tail):
                drop.add(short)
                break
    return {k: v for k, v in repos.items() if k[0] not in drop}


def _clean_branch(name: str) -> str:
    """A branch we are prepared to name, or ``""``.

    Measured on the live tab, where the five most common "branches" were
    ``refs/tags``, ``from``, ``feat``, ``2`` and ``release`` — a tag prefix,
    two words of prose, a shell redirect and a documentation placeholder
    (``git checkout -b release/<slug>`` captures ``release/``, because ``<``
    cannot be in a branch name). Every branch on that node that was real
    carried a ``/``.

    So: a tag is not a branch, a trailing ``/`` is a placeholder, and a name
    with no separator at all is a word that happened to follow ``git push``.
    A branch like ``staging`` is dropped by that last rule; a missing row is
    recoverable and a fabricated one teaches the reader that the table
    guesses.
    """
    out = str(name or "").strip()
    if out.startswith("refs/tags/") or out == "refs/tags":
        return ""        # a tag is not a unit of delivery
    if out.startswith("refs/heads/"):
        out = out[len("refs/heads/"):]
    if not out or out.endswith("/") or out.startswith("-"):
        return ""
    if "/" in out:
        return out
    # No path separator: accept only something that still reads as a branch
    # name rather than as the next word in a sentence.
    if len(out) >= 4 and "-" in out and out[0].isalpha():
        return out
    return ""


def _file_refs_from_steps(events: Iterable[dict]) -> dict:
    """Files the session WROTE, via the detector step normalizer.

    Reuses ``detectors.normalize_events`` rather than re-deriving path
    extraction: it already understands every runtime's tool-call envelope
    and already pulls paths out of both structured args (``file_path``)
    and shell commands (``sed -i file``), which matters because most edits
    on a real node go through Bash, not a typed Edit tool. Import is local
    and guarded so attribution degrades to "no files" instead of raising if
    the detector module is unavailable.
    """
    out: dict[str, dict] = {}
    try:
        from clawmetry import detectors as _dt
        steps = _dt.normalize_events(events)
    except Exception:
        return out
    for step in steps or []:
        if not isinstance(step, dict) or step.get("kind") != "tool_call":
            continue
        try:
            mutates = _dt._step_mutates(step)
        except Exception:
            mutates = False
        if not mutates:
            continue
        for path in step.get("paths") or ():
            name = _clean_path(path)
            if not name or name in out:
                continue
            out[name] = {
                "role": ROLE_AUTHORED,
                "confidence": 0.9,
                "evidence": _clean_evidence(
                    f"{step.get('tool') or 'tool'} wrote {name}"),
                "source": "write_tool",
            }
            if len(out) >= MAX_FILES_PER_SESSION:
                return out
    return out


def _scan_text(text: str, ts: str, prs: dict, repos: dict,
               branches: dict, commits: dict) -> None:
    """Fold every artifact reference in one text into the accumulators.

    Split out of :func:`extract_session_delivery` so each event can be
    scanned once per candidate text (structured arguments first, then the
    serialized payload) without duplicating the per-kind cap logic four
    times. The caps refuse only NEW keys, so an artifact already being
    tracked keeps accumulating mentions after the cap is reached.
    """
    for ref in _find_pr_refs(text):
        key = (ref.get("repo") or "", ref["pr"])
        if len(prs) >= MAX_PRS_PER_SESSION and key not in prs:
            continue
        _merge_ref(prs, key, ref, ts)
    for ref in _find_repo_refs(text):
        key = (ref["repo"],)
        if len(repos) >= MAX_PRS_PER_SESSION and key not in repos:
            continue
        _merge_ref(repos, key, dict(ref, role=ROLE_EXPLORED), ts)
    for ref in _find_branch_refs(text):
        key = (ref["branch"],)
        if len(branches) >= MAX_BRANCHES_PER_SESSION and key not in branches:
            continue
        _merge_ref(branches, key, ref, ts)
    for ref in _find_commit_refs(text):
        key = (ref["commit"],)
        if len(commits) >= MAX_COMMITS_PER_SESSION and key not in commits:
            continue
        _merge_ref(commits, key, ref, ts)


def extract_session_delivery(
    events: Iterable[dict],
    session_id: str,
    runtime: Optional[str] = None,
) -> dict:
    """Everything one session delivered, plus how its cost divides.

    Pure and never raises: a malformed event stream yields an empty result,
    which reads as "nothing attributed" rather than taking the daemon down
    (the never-crash-on-bad-input rule).

    Returns::

        {"session_id", "runtime", "artifacts": [...],
         "unattributed_usd", "total_usd", "basis"}

    where each artifact is ``{kind, ref, repo, role, confidence, evidence,
    source, first_ts, last_ts, mentions, cost_usd}``. ``cost_usd`` is set
    for ``pr`` rows only: a PR is the unit teams budget and review by, and
    inventing a per-file split of a model call would be a fabricated
    number.
    """
    # ``agent_type`` is the store's column name for the runtime and is what
    # ``persist_session_attribution`` keys rows on. Both spellings are set
    # here so the caller cannot accidentally file a Codex session's delivery
    # under the 'openclaw' default.
    result = {
        "session_id": str(session_id or ""),
        "runtime": str(runtime or "") or None,
        "agent_type": str(runtime or "") or "openclaw",
        "artifacts": [],
        "unattributed_usd": 0.0,
        "total_usd": 0.0,
        "basis": "unknown",
        "event_count": 0,
    }
    try:
        chron = chronological(events)
    except Exception:
        log.warning("attribution: cannot order events for %s", session_id)
        return result
    if not chron:
        return result
    # Reported so a caller can tell a complete read from a truncated one:
    # ``total_usd`` only equals the session's real cost when every event was
    # passed in. The daemon reads the whole session; a hand-made call with a
    # low limit sees a smaller total and this number says so.
    result["event_count"] = len(chron)

    prs: dict[tuple, dict] = {}
    repos: dict[tuple, dict] = {}
    branches: dict[tuple, dict] = {}
    commits: dict[tuple, dict] = {}

    try:
        for event in chron:
            ts = _ts_of(event)
            for text in _event_texts(event):
                if not text:
                    continue
                _scan_text(text, ts, prs, repos, branches, commits)
    except Exception:
        log.warning("attribution: extraction failed for %s", session_id,
                    exc_info=True)
        return result

    # NOTE: role is decided per pull request, from what the session did TO
    # THAT pull request, and nothing else. An earlier version promoted every
    # referenced PR to "authored" whenever the session ran any git write
    # anywhere, on the theory that viewing your own PR while committing is
    # authoring work. On a real node almost every session commits something,
    # so the column read "authored" on all 100 rows: it claimed authorship of
    # pull requests the session had only looked at, and a column whose value
    # never varies tells a reader nothing. A commit in a session is not
    # evidence about which of the several pull requests that session touched
    # it belongs to. Linking a commit to its pull request needs the head
    # branch, which only a repository scan knows (REQ-OBS-CEA-022).

    # A name cut short by the tool that printed it is not a repository, and
    # the rest of the session is what shows that. Done BEFORE the fold below,
    # so a truncated name can never become a pull request's repository.
    # One repository spelled two ways is one repository: GitHub is
    # case-insensitive, and the live tab listed ``NVIDIA/OpenShell`` beside
    # ``nvidia/openshell``. Done BEFORE the truncation pass, so prefixes are
    # compared in one spelling rather than across two.
    repos, prs = _fold_repo_case(repos, prs)

    repos = _drop_truncated_repos(repos)

    # The same cut-short name reaches a pull request by its own route, so the
    # repository bucket being clean is not enough: repair the rows too.
    prs = _repair_pr_repos(prs, repos)

    # A pull request named both bare and with ``--repo`` arrives under two
    # keys; fold them so the tab shows one row per pull request.
    prs = _fold_bare_pr_rows(prs, repos)

    try:
        split = split_cost(chron)
    except Exception:
        log.warning("attribution: cost split failed for %s", session_id)
        split = {"per_pr": {}, "unattributed_usd": 0.0, "total_usd": 0.0,
                 "basis": "unknown"}

    artifacts: list[dict] = []

    # A pull request or repo is known because the session NAMED it; a branch,
    # commit or file is known because we watched the session write it. The
    # two bases carry different weight for a reviewer, so they are recorded
    # rather than flattened.
    _BASIS_BY_KIND = {
        KIND_PR: BASIS_PR_REFERENCE,
        KIND_REPO: BASIS_PR_REFERENCE,
        KIND_BRANCH: BASIS_WRITE,
        KIND_COMMIT: BASIS_WRITE,
        KIND_FILE: BASIS_WRITE,
    }

    def _emit(kind: str, ref: str, row: dict, cost: Optional[float] = None):
        artifacts.append({
            "kind": kind,
            "ref": ref,
            "repo": row.get("repo") or "",
            "basis": _BASIS_BY_KIND.get(kind, BASIS_PR_REFERENCE),
            "role": row.get("role") or ROLE_EXPLORED,
            "confidence": round(float(row.get("confidence") or 0.0), 3),
            "evidence": row.get("evidence") or "",
            "source": row.get("source") or "",
            "first_ts": row.get("first_ts") or "",
            "last_ts": row.get("last_ts") or "",
            "mentions": int(row.get("mentions") or 1),
            "cost_usd": round(float(cost), 6) if cost is not None else None,
        })

    charged, unplaced = _distribute_pr_cost(split["per_pr"], prs)
    for key, row in prs.items():
        _emit(KIND_PR, key[1], row, charged.get(key, 0.0))
    for (name,), row in repos.items():
        _emit(KIND_REPO, name, row)
    for (name,), row in branches.items():
        _emit(KIND_BRANCH, name, row)
    for (sha,), row in commits.items():
        _emit(KIND_COMMIT, sha, row)
    for name, row in _file_refs_from_steps(events).items():
        _emit(KIND_FILE, name, row)

    result["artifacts"] = artifacts
    # The remainder carries both the cost that preceded any pull-request
    # reference and any segment that could not be placed on exactly one row,
    # so ``sum(cost_usd) + unattributed_usd == total_usd`` always holds.
    result["unattributed_usd"] = round(
        split["unattributed_usd"] + unplaced, 6)
    result["total_usd"] = split["total_usd"]
    result["basis"] = split["basis"]
    return result


__all__ = [
    "extract_session_delivery",
    "split_cost",
    "chronological",
    "KIND_PR", "KIND_REPO", "KIND_BRANCH", "KIND_COMMIT", "KIND_FILE",
    "ROLE_AUTHORED", "ROLE_REVIEWED", "ROLE_EXPLORED",
    "BASIS_PR_REFERENCE", "BASIS_TRAILER", "BASIS_WRITE",
    "UNSUPPORTED_FORGE_HOSTS",
    "MAX_PRS_PER_SESSION", "MAX_FILES_PER_SESSION",
]
