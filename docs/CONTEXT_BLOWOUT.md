# Context-window blowout across runtimes

Context blowout is where agent comparisons quietly go wrong. Every runtime
fills a window, every runtime deals with filling it differently, and most
tooling measures all of them with one vendor's ruler and reports a zero
wherever it cannot see.

This page is what ClawMetry actually knows, per runtime. More importantly, it
is also what ClawMetry *doesn't* know.

## Three independent signals

ClawMetry sees context pressure three ways. They are independent, and
runtimes support different subsets:

| Signal | What it is | Where it comes from |
|---|---|---|
| **Utilization** | How full the window got, per turn | The usage envelope on assistant turns (`input + cache_read + cache_write`) over the model's real window |
| **Compaction** | The harness summarised and dropped history | An explicit compaction event, where the runtime writes one |
| **Overflow** | The provider rejected the prompt as too long | Error text: `request_too_large`, `prompt is too long`, `context length exceeded`, … |

Overflow is the one that matters most and the one most tools miss: it is the
difference between *the agent tidied up* and *the agent hit the wall and had
to retry*. A session with two or more compactions where at least one was
overflow-triggered is flagged as **overflow-then-retry**, the pattern that
burns money without making progress.

## The denominator problem

A utilization percentage is only as honest as what it divides by. Until
recently ClawMetry's resolver knew exactly two numbers, both Anthropic's:
200K, and 1M for the `[1m]` variants. It used them for all 28 runtimes.
The failures were symmetric, and both looked plausible on screen:

- a **300K-token GPT-5 turn** rendered as *">100%, blown"*. GPT-5's window is
  400K; the turn was at 75%.
- a genuinely blown **130K DeepSeek turn** rendered as a comfortable *65%*.
  DeepSeek's window is 128K. It had already overflowed.

The fix is [`clawmetry/context_windows.py`](../clawmetry/context_windows.py):
a per-provider table you can read and send a PR to, covering Anthropic,
OpenAI, Google, xAI, DeepSeek, Moonshot/Kimi, Qwen, Mistral, Meta and GLM.

### Every window says where it came from

Sizing is *resolved, not hard-coded*, and each answer carries its provenance,
the same contract Guard thresholds follow. Four sources, each overriding the
last:

| `source` | Meaning | `confidence` |
|---|---|---|
| `default` | Nothing matched. We are guessing, and say so. | `fallback` |
| `model_table` | A table entry matched the model string. | `inferred` |
| `explicit_marker` | The model string named its window (`[1m]`), or `CLAWMETRY_CONTEXT_WINDOW` pinned it. | `exact` |
| `observed_floor` | We measured a prompt *larger* than the resolved window. A prompt the provider accepted cannot exceed that provider's window, so the measurement wins. | `exact` |

`/api/context-economics` ships `window_source` and `window_confidence`
alongside every point, so a gauge built on a guess never renders with the
same authority as one built on a lookup.

The `observed_floor` ladder is **vendor-aware**. A 323K Claude prompt snaps
to 1M, not to some 400K rung Anthropic has never sold. Inventing a
denominator from a tier that does not exist is the same class of bug in a
new costume.

An unknown model falls back to 200K and is reported as `default`. That is
deliberate: an honest "we don't know this model" is a one-line PR someone can
send, whereas a confident wrong number is a silent lie in a dashboard.

## Coverage: what a zero actually means

Here is the part most comparison tools skip. ClawMetry emits compaction
events for a **minority** of its adapters, because only some runtimes write
one down. So "Compactions: 0" is two completely different statements wearing
the same clothes:

- this runtime ran clean, nothing compacted; or
- we have no way to observe compaction on this runtime at all.

Rendering those identically is worse than not shipping the tile. A user
comparing runtimes reads the second as the first and concludes their Codex
sessions never blow out, when the truth is our Codex adapter emits no
compaction event and we were never going to see one.

`GET /api/context-coverage` answers it, per runtime, per signal:

| Verdict | Meaning |
|---|---|
| `observed` | We have this signal in the window. The count is real. |
| `supported_none_seen` | The runtime can produce it; none occurred. **A zero is a real zero.** |
| `unsupported` | The adapter emits no such signal. **A zero means blind**, and the UI must say so. |

```json
{
  "runtime": "codex",
  "sessions": 12,
  "utilization": { "count": 300, "verdict": "observed",    "note": "" },
  "compaction":  { "count": 0,   "verdict": "unsupported",
                   "note": "codex does not record compaction events. A zero
                            here means ClawMetry cannot see them, not that
                            none happened. Window utilization below is still
                            measured." },
  "overflow":    { "count": 2,   "verdict": "observed",    "note": "" }
}
```

Two rules keep this from rotting:

**Measurement beats declaration.** Coverage is computed from *your* store
first. If the data shows a runtime reporting compactions, it does, whatever
[`context_coverage.py`](../clawmetry/context_coverage.py) believes. A stale
list can never hide real data.

**The blind list is a denylist, not an allowlist.** Getting it wrong degrades
a runtime to an honest `supported_none_seen`; an allowlist that went stale
would claim blindness for a runtime that had started reporting. Failure lands
on the cautious side.

### Known blind spots

- **Compaction**: not recorded by `aider`, `claude_code`, `cline`, `codex`,
  `cursor`, `deepagents`, `deepseek_harness`, `devin`, `exo`, `gemini_cli`,
  `goose`, `grok`, `hermes`, `n8n`, `nanoclaw`, `opencode`, `openhands`,
  `picoclaw`, `qm`, `qwen_code`. Utilization and overflow still work for all
  of them, so context pressure is visible. Only the explicit "the harness
  compacted here" marker is missing.
- **Utilization**: `cursor` (tokens live behind a proprietary backend) and
  `picoclaw` (writes no usage envelope). Cost for these arrives via the
  hosted VM usage log, which carries no per-turn context size.

Closing a compaction blind spot is a small PR against the runtime's adapter
plus deleting one line from `UNSUPPORTED_COMPACTION`.

## Overriding the window

For a private or air-gapped model our table can never be right about:

```bash
CLAWMETRY_CONTEXT_WINDOW=512000 clawmetry
```

The operator gets the last word; it reports as `explicit_marker`/`exact`.

## Related

- [`docs/OVERHEAD.md`](./OVERHEAD.md): what measuring all this costs
- [`clawmetry/context_windows.py`](../clawmetry/context_windows.py): the table
- [`clawmetry/context_coverage.py`](../clawmetry/context_coverage.py): the coverage rules
