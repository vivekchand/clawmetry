# Hook coexistence

ClawMetry is not the only thing that writes `~/.claude/settings.json`.

- **GitKraken / GitLens** shells out to `gk ai hook install claude-code --force`
  on a very large install base. Its merge behaviour lives inside a closed
  binary we cannot read.
- **numbat** is already co-resident on developer machines and writes eight
  events into the same file.
- **The user** may hand-write entries of their own.
- **ClawMetry itself writes from three places**: the manual installer
  (`clawmetry hooks install`), the daemon's runtime gate
  (`clawmetry/claude_code_gate.py`, which reinstalls every ~2s), and the
  mirror hook.

Everything below is about the half of that we control: what ClawMetry does to
a hook it did not write.

## The rule

**Never delete a hook you did not write.**

`clawmetry/hook_ownership.py` is the single implementation. Every removal path
goes through `prune_our_hooks()`, which works at **hook** granularity, not
entry granularity.

## Why entry granularity was wrong

A foreign writer lands in one of two shapes:

| Shape | What it does | Seen in the wild |
|---|---|---|
| `separate` | appends its own `{matcher, hooks}` entry | numbat, today |
| `merged` | appends its command into the hooks list of an entry that **already exists** | the `--force` hazard |

Co-installation appeared to work only because every foreign writer observed so
far uses the `separate` shape. Against the `merged` shape, asking *"is this
entry ours?"* answers yes for an entry that is half somebody else's, and the
pre-fix code destroyed the foreign hook twice over:

- `clawmetry hooks uninstall` dropped the whole entry, taking the foreign hook.
- The daemon gate's reinstall dropped it too — and that path runs **every ~2
  seconds**, so a merged foreign hook disappeared within seconds of landing,
  silently, with no uninstall involved.

Both are regression-locked in `tests/test_hook_collision.py`.

## Timeouts

A hook timeout is how long the *runtime* sits on a tool call waiting for us.
On GitHub Copilot CLI, whose `preToolUse` gate is **fail-closed** on crash or
non-zero exit, a hook that never answers denies the call.

Deriving the timeout from the longest policy window produced an installed
timeout of **604860s — seven days**. Anything that wedged our client wedged
the user's agent for a week.

Installed timeouts are now clamped by
`hook_ownership.clamp_hook_timeout()`:

| | Value |
|---|---|
| Default ceiling | `28800` (8 hours) |
| Override | `CLAWMETRY_HOOK_TIMEOUT_MAX_S=<seconds>` |
| Opt out (restore unbounded) | `CLAWMETRY_HOOK_TIMEOUT_MAX_S=0` |

Past the ceiling the runtime times out first, so that one call is blocked by
the runtime instead of resolving through the policy's `on_timeout`. That is
the deliberate trade: a bounded block beats an unbounded wait.

## What happens when ClawMetry is not running

The hook client bounds itself independently of the installed timeout. With
nothing listening it makes a connect attempt with a 3s budget, retries up to
`_MAX_TRANSIENT_FAILURES` (3), then **fails open**:

```
exit code 0, empty stdout  ->  no opinion  ->  the runtime's normal permission flow
```

Measured cost of an unreachable ClawMetry, both clients, on a dead port:

| Client | Elapsed | Exit | stdout |
|---|---|---|---|
| `clawmetry hook claude-code` | ~2.0s | 0 | empty |
| `clawmetry hook copilot` (fail-closed runtime) | ~2.0s | 0 | empty |

So a stopped daemon costs about two seconds per gated tool call and never
blocks one. This is asserted in `tests/test_hook_collision.py`.

## Reproducing

`scripts/hook_collision_matrix.py` runs both ClawMetry installers against a
foreign installer, in both orders, for both shapes, and diffs settings.json at
every step. It exits non-zero if any foreign hook was lost.

```bash
python3 scripts/hook_collision_matrix.py          # human-readable
python3 scripts/hook_collision_matrix.py --json   # machine-readable
```

If a real `gk` binary is on PATH the harness adds it as a third, **live**
shape. When it is not, the report says so explicitly rather than implying
GitLens itself was exercised:

```
real `gk` binary on PATH: False  (shapes below are modelled, GitLens itself was NOT run)
```

### The limit of this work

The other side is a closed binary. Nothing here proves what `gk --force` does
to *our* hook — only that we do not damage *its* hook, in every shape and
order we can construct. Confirming the reverse direction needs a machine with
GitLens actually installed. Our gate reinstalls every ~2s and therefore
self-heals if it is clobbered; the manual installer does not, and would need
`clawmetry hooks install` re-run.
