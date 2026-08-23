# PRD — PR Trace: a shareable public URL for "how the AI built this PR"

> Status: **P0 implemented, rest proposed.** Every number below was measured against
> this repo on 2026-08-22 with `scripts/pr_trace_join.py`. Nothing here is an estimate.

## 1. The ask

Attach a **public, shareable ClawMetry URL to a GitHub PR** showing everything the
agent did to produce it — the prompts, the tool calls, the subagents it spawned, the
workflows it spanned, the cost — viewable as a normal trace, an agent graph, or a
turn-by-turn replay, in one place.

The framing that matters (Steipete's point, and what makes this different from every
cost tool): the audience is **another developer reviewing your PR**, not a CFO
reading a spend report. They want to answer *"what did you actually ask the model,
and what did it actually do?"* — which nothing on the market answers, because
everything on the market is built around dollars.

Two consequences that drive the whole design:
- The headline artifact is the **prompt chain**, not the cost figure.
- The natural channel is **open source**, where the review is already public, so the
  artifact can be published without asking anyone to expose anything new.

## 2. Measured reality — the join does not exist yet, and cannot be backfilled

`scripts/pr_trace_join.py`, 800 commits of this repo:

```
commits with a PR number                :  658
TIER A  our trailer, resolves in store  :    0    <- the trailer does not exist yet
TIER B  Co-Authored-By + time overlap   :  110    <- heuristic
unjoinable                              :  690
sessions in store                       :  196

TIER-B CANDIDATE PRs: 96
  94/96 match MORE THAN ONE session   (5-8 candidates each)
```

### 2a. The false start worth documenting

The obvious idea is to use the vendor trailer Claude Code already writes:

```
Claude-Session: https://claude.ai/code/session_016Svswf2MmVyyzxqMcVJtSj
```

**It is unusable.** That is a *cloud* session id, and it appears nowhere as
structured metadata in the local transcript. A scan of 200 transcripts found
`session_01…` strings only in these positions:

```
17  .message.content[].input.content     <- tool inputs
17  .toolUseResult.content               <- tool output
14  .message.content[].input.command     <- shell commands
 4  .toolUseResult.stdout
```

i.e. only ever as **incidental text someone printed**, never as identity. (Confirming
this took one wrong turn: an early prototype "bridged" the ids by grepping
transcripts, and matched only the session that had just *printed* those ids while
investigating — a self-inflicted false positive.)

There is no on-disk mapping from the vendor's cloud id to a local session. The local
transcript knows itself only as a UUID (`sessionId: 36f12caf-…`), which is what the
store keys on (`claude_code:36f12caf-…`).

> **Consequence:** we cannot ride the vendor's trailer. **ClawMetry must write its
> own**, carrying the id it already owns.

### 2b. The heuristic tier is a coverage signal, not an attribution mechanism

`Co-Authored-By: Claude*` covers far more history (110/800 commits here, and ~70% of
recent history by that trailer alone), but joining it to a session by time overlap
gives **5–8 candidate sessions per PR, ambiguous for 94 of 96 PRs.**

That is fine for *"was this PR AI-assisted, and roughly what did it cost?"* and
useless for *"show me the trace."* It ships **labeled**, and never as a headline
number — the same two-tier confidence rule we already apply to `sessions.outcome`.

## 3. The other two blockers

### 3a. Coverage cannot be backfilled — capture must be at commit time

Beyond the id problem, the raw data evaporates. For this repo only **2 transcript
files survive on disk**, out of hundreds of sessions. Two independent, permanent
causes:

- Claude Code rotates and cleans project transcripts.
- `CLAWMETRY_FAMILY_SESSION_LIMIT` defaults to **50** most-recent sessions per
  runtime (`sync.py:337`) — the store deliberately forgets older ones.

> **Decision:** the trace bundle is **snapshotted and pinned at PR-open time**, while
> the transcript still exists. The share URL serves a frozen, immutable bundle, never
> a live query. Reproducibility comes free: the trace cannot drift after review.
>
> And stated plainly: **coverage starts the day the hook is installed.** There is no
> retroactive story. This is a property to design around, not a bug to fix.

### 3b. The multi-view payload has an API contract but no data producer

`/api/replay-tree/<sid>` is specified to return
`turns[{turn_id, events, delegations, approvals}]` + `workflows[{span_id, kind, events}]`
— precisely the "trace / workflows / subagents in one go" shape the ask describes. On
a real session it returns:

```json
{"turns": 0, "workflows": 0, "row_count": 0, "runtime": null}
```

because `iter_replay_events` is implemented in **zero adapters** — the mappers its
docstring references (#4815 Claude Code, #4816 OpenClaw) never landed. Next door:
`/api/local/agent-graph` returns 2 nodes and **0 edges**; `/api/subagents` returns 0.

**This is the real cost of the feature.** The join is a weekend. The replay-event
mappers are the actual project. No multi-view trace renders until `iter_replay_events`
exists for at least `claude_code` and `openclaw`.

### 3c. One session produces many PRs

Even with a perfect trailer, a single session commonly spans several PRs (#4625,
#4635 and #4637 here came from one). Attributing full session cost to each
triple-counts.

> **Decision:** the bundle carries a `commit_range`; cost is split by turn boundaries
> falling inside it. Where the split is ambiguous the bundle reports
> `attribution: "shared"` plus the sibling PR list, rather than a confident number.

## 4. Architecture

**Repo split.** This repository owns the half that must run on the machine the agent
ran on: the commit trailer, bundle capture, publication redaction, and the local
review renderer. Everything served from `trace.clawmetry.com` — the resolver, the
hosted viewer, the directory, the GitHub App — lives in **clawmetry-cloud**, which is
why its criteria carry the `AC-CLOUD-` prefix the manifest already routes there. The
JSON bundle is the contract between the two.

### 4a. The trailer — foundation, not detail

A `prepare-commit-msg` hook (and, for Claude Code, an addition to the existing hook
installer in `clawmetry/hooks_claude_code.py`) stamps every agent-authored commit:

```
Clawmetry-Session: claude_code:36f12caf-56e7-4d1d-9db2-89808ad3d03a
```

Writing our own is strictly better than depending on a vendor footer:
- it is the **store's primary key**, so there is zero bridging;
- it works for **every runtime**, not just Claude Code;
- it does not break when a vendor changes its footer format.

`clawmetry trace init` installs it. Tier A coverage is 0% before that and ~100% of
agent commits after.

**What the trailer claims, precisely.** It says *this commit was made inside session
X* — not "an AI wrote every line." A human who edits by hand and commits from a
terminal inside an agent session gets stamped, and that is correct: the session is
the context the reviewer wants. The viewer must word it as *"made during"*, never
*"generated by"*. A commit made with no agent runtime present carries no trailer and
makes no claim at all.

> **Status: implemented.** `clawmetry/trace_stamp.py`, wired as a CLI fast path in
> `cli.py` (alongside `hooks`, for the same reason — `trace stamp` runs on every
> commit and must not pay the ~300 ms dashboard import). 23 tests in
> `tests/test_trace_stamp.py`. Verified end to end: an agent commit is stamped, a
> commit with no runtime env is not.

### 4b. Capture — `clawmetry trace capture`

Runs from a git hook or GitHub Action at PR-open, in the environment where the data
lives:

1. Resolve `commit_range` → session ids from the Tier-A trailer; fall back to the
   labeled Tier-B heuristic (§2b) when absent.
2. Pull `transcript`, `replay-tree`, `agent-graph`, `subagents`, cost rollup.
3. Run publish-time redaction (§4f), then **hold for review** — never auto-publish.
4. Encrypt, upload, print the share URL.

### 4c. URL scheme — mirror the forge URL, make every PR addressable

The trace lives at a URL derived mechanically from the PR's own URL:

```
https://trace.clawmetry.com/github.com/vivekchand/clawmetry/pull/5100
                            └── forge host ──┘└─ owner ─┘└ repo ┘└ pr ┘
```

Keeping the **forge host as a path segment** is what makes this extend without a
redesign — `trace.clawmetry.com/gitlab.com/…`, `/bitbucket.org/…`, and a
`/jira/<site>/browse/<KEY>` shape later all resolve through the same router. Accept
both `/pull/<n>` and `/pulls/<n>`; people will paste either.

Three properties fall out of this, and they are the reason to prefer it over an
opaque id:

1. **Editable.** Change `5100` to `5099` and you get that PR's trace. The URL is a
   query, not a token.
2. **Every PR is an entry point.** Any GitHub PR URL in the world rewrites to a
   ClawMetry URL. That is a growth loop no opaque-id scheme can produce.
3. **A miss is a product surface, not a 404.** See §4d.

### 4d. What an un-traced URL does — the onboarding wedge

A URL that resolves to nothing is the most valuable page in this design, because
someone arriving there is holding a specific PR they wanted traced.

| State | Response |
|---|---|
| Repo public, no trace | Landing page naming the actual repo and PR (title/author from the public GitHub API), explaining what a trace would show here, and a one-command install. **This is the wedge.** |
| Repo public, traced | The viewer (§4g). |
| Viewer owns the repo | Same, plus "claim this repo" → enable auto-trace on future PRs. |
| Repo private or non-existent | **One indistinguishable response.** |

That last row is a hard requirement, not a nicety. If a private repo with a trace
renders differently from a repo that does not exist, the resolver becomes an oracle
for private repository names and for which companies use ClawMetry. Same body, same
status, same timing.

### 4e. Key model — two share modes, honestly labeled

The forge-mirrored URL is guessable by design, so pretending it is end-to-end
encrypted would be theatre. Two modes, and the difference is stated plainly in the
publish UI:

- **Public** (`trace.clawmetry.com/github.com/…`) — served to anyone. Deliberately
  world-readable; the E2E property does not apply and we do not claim it. Intended
  for OSS, where the PR is public anyway.
- **Unlisted** (`trace.clawmetry.com/t/9f3a2b7c#k=<base64url-key>`) — the bundle is
  encrypted with `sync.encrypt_payload` (AES-256-GCM) under a fresh per-bundle key
  carried in the **URL fragment**, which never reaches the server. Readable by anyone
  with the link and **unreadable by us**. This is the mode for private repos and for
  review-before-publish.

Both revoke by deleting the object; unlisted additionally revokes by rotating the key.

Unlisted mode is the honest answer to OptScale's contradiction — they sell PII
redaction on one page and "No Token Masking: full prompts, full responses" on
another. We can offer full fidelity *and* zero vendor readability, because the viewer
decrypts. Public mode makes no such claim, and the UI must not imply one.

### 4f. Redaction and consent — the gate that must not be skipped

Publishing a raw agent transcript is a data-exfiltration event waiting to happen: env
vars echoed into tool output, contents of private files, customer data, internal
hostnames. `clawmetry/redaction.py` already scrubs **secret shapes** at the ingest
chokepoint (provider key formats, bearer tokens, `key=value` pairs, private-key
blocks, sensitive field names → stable `[REDACTED:<sha8>]` fingerprints).

Necessary, **not sufficient** — it targets credentials, not confidential *content*.
Publishing adds:

1. **A stricter publish-time pass** — absolute paths → `~/…`, hostnames, emails,
   contents of files outside the repo, anything matching a `.gitignore`d path.
2. **Mandatory human review before first publish** — a diff-style "this is what the
   world will see" screen. Default is *not published*.
3. **Per-repo policy** — a public repo may opt into auto-publish; a private repo never
   publishes without explicit per-bundle confirmation.

This is the CLAUDE.md control-plane rule on a new surface: a publish is a write, so it
must be user-initiated, scoped, reversible, and attributed.

### 4g. The viewer — GitHub-shaped, prompts first

Borrow GitHub's chrome deliberately. A reviewer arrives here **from** a PR page, and
the less they have to relearn, the faster they get the answer. Same page width, same
sticky header, same tab strip, same file-diff-style expandable blocks, same
monospace/prose balance. It should read as a tab GitHub forgot to build.

**Header — immediate context, above the fold.** Before any interaction, the reviewer
sees what this PR cost and who did it:

```
 vivekchand/clawmetry  #5100                                    [ Open in GitHub ]
 feat(trace): PR trace bundles

 $4.12        183,402 tokens      47 turns      6 tools      2 subagents      38m
 claude-opus-5 (91%) · claude-haiku-4-5 (9%)          attribution: exact ▸
```

Every figure links to the lens that explains it — tokens to Trace, subagents to Agent
graph, cost to the per-turn breakdown. `attribution: exact | shared | heuristic` is
always present and always honest (§2b, §3c); on `shared` it names the sibling PRs, on
`heuristic` it says so in the chip rather than in a footnote nobody reads.

**Four lenses, one frozen bundle:**

| Lens | Answers | Source | Blocked by |
|---|---|---|---|
| **Prompts** *(default)* | "What did you ask it?" — human turns only, in order | transcript | — |
| **Trace** | Turn by turn: prompt → thinking → tools → output → tokens | replay-tree `turns[]` | §3b |
| **Agent graph** | Who delegated to whom; the subagent tree | agent-graph, delegation-tree | §3b |
| **Workflows** | Spans across the session; what ran in parallel | replay-tree `workflows[]` | §3b |

**Prompts is the default**, and it is deliberately the plainest view in the product:
just the human turns, in sequence, with nothing between them. That is the artifact
Steipete was asking for, it is the cheapest to build, and it is the only lens that
works before §3b lands.

**Reading the AI's thinking.** In the Trace lens each turn expands into
`prompt → thinking → tool calls → result`, with reasoning blocks rendered as a
collapsed-by-default band the reader opens per turn — visible enough to be honest
about how the answer was reached, quiet enough that scanning 47 turns stays possible.
Two navigation aids do most of the work at that length: a left rail listing every
human prompt as a jump target, and per-turn cost/token chips so the expensive turns
are findable by eye. Deep-link every turn (`…/pull/5100#turn-23`) so a reviewer can
cite one in a PR comment — that is how this spreads.

Redaction is visible, never silent: a `[REDACTED:a1b2c3d4]` chip renders inline with
a tooltip explaining a secret was removed and that the fingerprint is stable. A
reviewer must never wonder whether they are seeing the whole story.

### 4h. GitHub surface

`clawmetry/actions/pr-trace` — a published Action following this repo's existing
`pr-screenshots.yml` precedent:

- One PR comment: cost, model mix, turn count, subagent count, and the link.
- A check-run so the link is reachable from the PR header.
- Optional README badge.
- **Silent no-op when no session is found** — a human-authored PR must never get a
  broken comment.

Jira and GitLab reuse the same bundle; only the posting adapter changes. GitHub first,
and well.

### 4i. Discovery — browse any OSS project's PRs and see what is traced

`trace.clawmetry.com` is not only a resolver. A signed-in user can search any public
GitHub project, list its recent PRs, and see which carry traces. This turns the site
from a link target into a directory, and the directory is what gets indexed.

**Default view is not a search box.** Once GitHub is connected we know which repos the
user contributes to, so the landing state is *their* projects with coverage already
filled in — never an empty field waiting for input. (The empty dashboard is exactly
the failure mode worth avoiding; a first screen that reads `0 / 0 / $0` is what makes
a product feel dead.)

```
  openclaw/openclaw          14 of 30 recent PRs traced   ▓▓▓▓▓▓░░░░░░░
  vivekchand/clawmetry       28 of 30                     ▓▓▓▓▓▓▓▓▓▓▓▓░
  block/goose                 0 of 30   — not set up yet  ░░░░░░░░░░░░░
```

Coverage is the unit of display, and the gap is the call to action. A repo at `0 of 30`
is not a dead end — it is the §4d landing page with a specific, named set of PRs that
*could* be traced.

**Where the data comes from, and the constraints that shape it:**

| Need | Source | Constraint |
|---|---|---|
| Repo search | GitHub Search API | 30 req/min **authenticated** — this is why search requires login |
| Recent PRs for a repo | `GET /repos/{o}/{r}/pulls` | 5,000/hr per token; one call per 100 PRs; cache hard |
| Which PRs have traces | **our own index**, one batched lookup | never ask GitHub this |

That last row matters: checking trace existence must be a single query against our
index keyed by `(forge, owner, repo, pr)` — never N calls to anyone. GitHub is asked
only what GitHub uniquely knows.

Cache repo and PR listings server-side and share the cache across users; popular repos
should cost one upstream call per window regardless of how many people look. Use the
signed-in user's token for search so rate budget scales with users rather than
throttling everyone against one app-level ceiling.

**Logged-out still works for pages, not for search.** Repo and PR pages must render
without auth so they are indexable and so a cold reviewer can follow a link. Search
requires login, because of the rate limit and because an open search endpoint is an
abuse magnet.

**Public-only, always.** Search results and repo pages show public repositories only,
regardless of what the signed-in user can see. Surfacing a private repo the viewer
happens to have access to would turn the directory into the same oracle §4d exists to
prevent.

### 4j. What the GitHub App can and cannot do

The App is a real surface — it carries verification (§5a), the PR comment and
check-run (§4h), and repo metadata for the directory (§4i). It is not, and cannot
become, the thing that produces a trace.

**The App cannot see the agent session.** Transcripts and the DuckDB store live on the
machine where the agent ran. GitHub has no access to any of it, and no permission
scope would change that. So the system is two-sided by necessity:

| Side | Runs where | Job |
|---|---|---|
| `clawmetry trace capture` | the machine the agent ran on | resolve session → build bundle → redact → publish |
| GitHub App | GitHub | verify admin, post comment + check-run, read repo metadata, receive webhooks |

The App's webhook (`pull_request.opened`) is the coordination point, not a data source:
it tells us a PR exists so we can post a comment once a bundle arrives, or render the
"not traced yet" state (§4d) when none does.

**One case where GitHub genuinely is the machine.** When the agent runs *inside CI* —
a Claude Code / agent Action on a GitHub runner — the runner is where the session
lives, so `clawmetry trace capture` in the workflow captures it there directly. For
projects that run agents in CI this is a cleaner path than a contributor's laptop:
capture is reproducible, the environment is known, and nothing depends on an individual
developer having installed anything. Worth treating as a first-class path rather than
an afterthought, because it is where a lot of OSS agent work is heading.

**The failure mode to avoid** is designing as though the App could backfill traces for
PRs it sees. It cannot. A PR opened from a machine with no ClawMetry install has no
trace and never will — that is §3a restated at the org level, and the honest answer is
the un-traced landing page, not a synthesised approximation.

### 4k. Contributor onboarding — one command, per project

A maintainer installs the App once (§5a). Every *contributor* gets set up with a single
command the project can paste into its `CONTRIBUTING.md`:

```
curl -fsSL https://trace.clawmetry.com/i/openclaw/openclaw | bash
```

It installs ClawMetry if absent (reusing the existing `install.sh` path), binds this
clone to the named project, and runs `clawmetry trace init` so commits start carrying
the `Clawmetry-Session` trailer. Re-running it is a no-op.

**The grant belongs to the project, not the contributor.** A contributor needs no
account, no admin rights, and no plan of their own — they inherit the project's Pro
grant for work on that repo. Requiring every contributor to qualify separately would
kill the feature on contact; the whole point is that one maintainer enables it and
everyone downstream just works.

#### Constraints this command has to satisfy

**It must be safe to paste into a public README.** That rules out putting a token,
key, or one-time secret in the URL — anything embedded there is leaked the moment the
project publishes the line, and rotating it breaks every fork and every stale copy.
The URL carries a public repo slug and nothing else. Authentication, where publishing
later needs it, is a separate explicit step, never baked into a public install line.

**Exactly one line of variance.** Serve the *same* script bytes to everyone, with a
single prepended assignment:

```sh
CLAWMETRY_PROJECT=openclaw/openclaw   # <- the only line that differs per repo
```

Publish the canonical script's hash so anyone can diff what they were served against
what everyone else was served. A per-repo *generated* script is unauditable by
construction and should never ship — the customisation is a parameter, not code.
`curl … | bash -s -- openclaw/openclaw` is the stricter alternative if the pretty URL
is ever not worth the variance.

**Print before acting.** The script states the project it is binding, the repo it is
in, and what it will change, before it changes anything.

**Bind per clone, not globally.** Record the association in the repo:

```
git config clawmetry.project openclaw/openclaw
```

It travels with the clone, is scoped to one checkout, is trivially inspectable, and
leaves no global state behind on a machine that works on twenty projects. It also sits
naturally beside the hook, which already lives in `.git/hooks`.

**Never clobber.** `trace_stamp.install()` already refuses to overwrite a foreign
`prepare-commit-msg` hook and prints the one line to add manually instead. The
installer inherits that behaviour rather than forcing its way in.

## 5. Distribution and entitlement

The open-source grant programme that funds free access for maintainers, its
qualification and revalidation rules, the outreach motion and the upsell path are
**monetization strategy and live in the private repo**:
`clawmetry-cloud/docs/PRD_PR_TRACE_OSS_PROGRAM.md` (FLYWHEEL §2, "keep business
internals out of this public repo").

What is in scope here, because it is a code contract rather than a commercial one:

- Entitlement resolution stays in `clawmetry/entitlements.py`, and any grant source
  is ranked **behind** every paid source, so an account holding a paid plan is never
  re-evaluated against a grant.
- Resolution **fails open** (CLAUDE.md control-plane rule): a verification error, an
  outage, or an ambiguous lookup keeps the current entitlement. A billing check must
  never be the reason someone's agent stops.
- Reading a published trace requires **no authentication**, on any plan.

## 6. Build order

| Phase | Ships | Notes |
|---|---|---|
| **P0** ✅ | `clawmetry trace init` — the `Clawmetry-Session` commit hook. | **Done.** `clawmetry/trace_stamp.py` + CLI fast path + 23 tests. Nothing else works without it, and every day it is not installed is coverage permanently lost. |
| **P1** 🟡 | `clawmetry trace capture` — bundle, publish-time redaction, local review renderer. | **Local half done**: `trace_capture.py` + `trace_viewer.py` + 22 tests. Verified `exact` on a stamped commit (1 session, $8.50) vs `heuristic` (6 sessions, $67.54 upper bound). Encrypted upload + share URL are clawmetry-cloud. |
| **P2** | GitHub Action, PR comment, check-run, badge. Dogfood on this repo. | |
| **P2b** | `trace.clawmetry.com/i/<owner>/<repo>` installer endpoint (§4k) — one static script, one line of variance, published hash. | Cheap, and it is what a maintainer actually pastes into CONTRIBUTING.md. |
| **P3** | `iter_replay_events` for `claude_code` + `openclaw` → unlocks Trace / Workflows / Agent-graph lenses. | **The bulk of the work.** |
| **P4** | GitHub App + `oss_grant` entitlement source (§5a), ranked behind both paid sources, with activity renewal + warning (§5c). | |
| **P5** | Discovery directory (§4i) — search, coverage view, shared cache. | |
| **P6** | Jira/GitLab adapters; cost-attribution split refinement. | |

P0 is urgent in a way the rest is not: it is the only item whose delay destroys data
that cannot be recovered.

## 7. Acceptance criteria

Per FLYWHEEL §1g each must be declared by a test under `tests/` before merge.

- **AC-TRACE-001.1** — When a commit carries a `Clawmetry-Session` trailer naming a
  session in the store, the system shall resolve that commit to that session.
- **AC-TRACE-001.2** — When a commit cannot be resolved deterministically, the system
  shall label the attribution heuristic and exclude it from headline figures.
- **AC-TRACE-002.1** — When a bundle is published, the system shall apply secret
  redaction and shall not transmit any value matching a known secret shape.
- **AC-TRACE-002.2** — When the repository is not public, the system shall require
  explicit per-bundle confirmation before publishing.
- **AC-TRACE-003.1** — When a bundle is published, the decryption key shall not be
  transmitted to the server.
- **AC-TRACE-004.1** — When one session maps to multiple pull requests, the system
  shall report shared attribution rather than a full per-PR cost.
- **AC-TRACE-005.1** — When an entitlement lookup fails, the system shall permit the
  publish (fail open on entitlement).
- **AC-TRACE-006.1** — When a published trace is requested, the system shall serve it
  without requiring authentication.
- **AC-TRACE-006.2** — When the GitHub App is installed on a public OSI-licensed
  repository by a user with admin rights, the system shall grant that account the Pro
  entitlement.
- **AC-TRACE-006.3** — When a granted repository is no longer public or no longer
  carries an OSI licence, the system shall lapse the grant at the next revalidation
  and not before.
- **AC-TRACE-006.4** — When repository verification fails or is unavailable, the
  system shall keep the existing entitlement active (fail open).
- **AC-TRACE-006.5** — When an account holds a paid entitlement, the system shall
  resolve that entitlement without evaluating open-source activity, and open-source
  inactivity shall never downgrade it.
- **AC-TRACE-006.6** — When no qualifying activity occurs within the 90-day window,
  the system shall lapse the grant only at a revalidation boundary and only after a
  warning issued at 14 days remaining.
- **AC-TRACE-006.7** — When qualifying activity resumes on a granted repository, the
  system shall restore the grant without requiring reapplication.
- **AC-TRACE-007.1** — When repository search or a directory page is rendered, the
  system shall include public repositories only, irrespective of the viewer's access.

## 8. Risks

| Risk | Mitigation |
|---|---|
| **A secret gets published.** The one failure that ends the feature. | Two-stage redaction, mandatory human review on first publish, private repos gated, account-wide kill switch that revokes every bundle. |
| Zero coverage until the hook is installed, and no backfill. | Ship P0 first and separately; make `trace init` part of onboarding; ship Tier B labeled so early adopters see *something*. |
| §3b is a larger project than the join. | Ship P1 with the Prompts lens; do not block the product on the mappers. |
| Public traces expose prompt engineering people consider proprietary. | Opt-in per bundle, revocable, default unpublished. |
| We publish our own traces and they look bad. | That is the point, and it is the most honest marketing available. |
