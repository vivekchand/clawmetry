# PRD — PR Trace: a shareable public URL for "how the AI built this PR"

> Status: **proposal**. Every number below was measured against this repo on
> 2026-08-22 with `scripts/pr_trace_join.py`. Nothing here is an estimate.

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
- The natural channel is **open source**, where review is already public — which
  makes free-Pro-for-OSS a distribution strategy rather than a giveaway.

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

## 5. Free Pro for open source

Full paid tier, free, for any public OSI-licensed repo.

Same argument the repo already accepted when `goose` moved into `FREE_RUNTIMES`:
revenue exposure is ~zero (these maintainers were never going to buy) and the
placement is worth more than the licence. It is stronger here, because **the artifact
is public by construction** — every traced OSS PR puts a ClawMetry link on a page
other developers already read. The giveaway *is* the distribution.

Mechanically it rides `entitlements.py` as an `oss_repo` resolution source alongside
the licence file and cloud plan, verified from public visibility + licence. It must
**fail open**: an entitlement lookup failure never blocks a publish.

Dogfood first — trace links on ClawMetry's own PRs. If we won't publish ours, nobody
will publish theirs.

## 6. Build order

| Phase | Ships | Notes |
|---|---|---|
| **P0** | `clawmetry trace init` — the `Clawmetry-Session` commit hook. | Nothing works without it, and every day it is not installed is coverage permanently lost. Ship first, alone if need be. |
| **P1** | `clawmetry trace capture` — bundle, publish-time redaction, review gate, encrypted upload, share URL. Viewer with **Prompts lens only**. | Shippable product by itself. |
| **P2** | GitHub Action, PR comment, check-run, badge. Dogfood on this repo. | |
| **P3** | `iter_replay_events` for `claude_code` + `openclaw` → unlocks Trace / Workflows / Agent-graph lenses. | **The bulk of the work.** |
| **P4** | `oss_repo` entitlement source. | |
| **P5** | Jira/GitLab adapters; cost-attribution split refinement. | |

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

## 8. Risks

| Risk | Mitigation |
|---|---|
| **A secret gets published.** The one failure that ends the feature. | Two-stage redaction, mandatory human review on first publish, private repos gated, account-wide kill switch that revokes every bundle. |
| Zero coverage until the hook is installed, and no backfill. | Ship P0 first and separately; make `trace init` part of onboarding; ship Tier B labeled so early adopters see *something*. |
| §3b is a larger project than the join. | Ship P1 with the Prompts lens; do not block the product on the mappers. |
| Public traces expose prompt engineering people consider proprietary. | Opt-in per bundle, revocable, default unpublished. |
| We publish our own traces and they look bad. | That is the point, and it is the most honest marketing available. |
