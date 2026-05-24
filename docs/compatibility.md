# Runtime Compatibility

ClawMetry monitors any runtime that writes session JSONL using the
OpenClaw on-disk layout (`~/.<runtime>/agents/main/sessions/<id>.jsonl`
with v3 event records). The matrix below tracks which OpenClaw-family
runtimes are explicitly verified via fixture-backed tests in CI.

| Runtime    | Status        | Notes                                                                       |
| ---------- | ------------- | --------------------------------------------------------------------------- |
| OpenClaw   | ✅ Native     | Reference runtime. Auto-detected from `~/.openclaw/`.                       |
| NanoClaw   | ✅ Verified  | Container runtime; same layout as OpenClaw. See workaround below.            |
| PicoClaw   | ✅ Verified  | $10 hardware runtime; same layout as OpenClaw. See workaround below.         |
| ZeroClaw   | ⏳ Not yet   | Needs fixture + audit. Open an issue if you run it.                          |
| TrustClaw  | ⏳ Not yet   | Needs fixture + audit. Open an issue if you run it.                          |
| Nanobot    | ⏳ Not yet   | Needs fixture + audit. Open an issue if you run it.                          |

"Verified" means the runtime has session fixtures in
`tests/fixtures/runtimes/<runtime>/` and a CI test
(`tests/test_runtime_compat.py`) that fails if any change to ClawMetry
breaks the parse path for that runtime's session shape.

## Pointing ClawMetry at NanoClaw or PicoClaw

NanoClaw and PicoClaw use the same wire format as OpenClaw but a
different home directory (`~/.nanoclaw/`, `~/.picoclaw/`). Auto-detection
of those paths is tracked separately; until that ships, point ClawMetry
at the sessions directory explicitly:

```bash
# NanoClaw
clawmetry --sessions-dir ~/.nanoclaw/agents/main/sessions

# PicoClaw
clawmetry --sessions-dir ~/.picoclaw/agents/main/sessions
```

Or via env var (useful for systemd / Docker):

```bash
export OPENCLAW_SESSIONS_DIR=~/.nanoclaw/agents/main/sessions
clawmetry
```

Everything else — cost extraction, sub-agent rendering, tool-call
transcripts — works out of the box because the wire format is identical
to OpenClaw's.

## Adding a new runtime

1. Capture a real session JSONL from the runtime and drop it under
   `tests/fixtures/runtimes/<runtime>/agents/main/sessions/<id>.jsonl`.
   The minimum viable fixture contains at least one `session`,
   `model_change`, user `message`, assistant `message` with `usage`,
   `tool_use_result`, and a final assistant `message` event (see
   `tests/fixtures/runtimes/_make_fixtures.py` for the canonical shape).
2. Add the runtime tuple to the `RUNTIMES` list in
   `tests/test_runtime_compat.py`.
3. Add a row to the matrix above.
4. If the runtime uses a non-`~/.openclaw` home directory, file a
   follow-up issue for auto-discovery (depends on multi-profile
   workspace discovery work).

## What "shared OpenClaw layout" means

A runtime is in-scope for ClawMetry monitoring iff it writes session
files matching all of:

- One JSONL per session, named `<session_id>.jsonl`
- Located under `<root>/agents/<agent_id>/sessions/`
- First line is a `{"type": "session", "version": 3, ...}` record
- Assistant turns carry `message.usage.totalTokens` and (optionally)
  `message.usage.cost.total`
- Model identity surfaces via `model_change` events and/or
  `message.model` on assistant turns

Runtimes that diverge from this layout (e.g. a runtime that stores
sessions in SQLite) need a dedicated adapter — see
`clawmetry/adapters/` for the existing OpenClaw / Claude Code / Hermes
adapter pattern.
