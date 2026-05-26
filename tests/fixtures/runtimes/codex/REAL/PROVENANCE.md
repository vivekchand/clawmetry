# Codex REAL capture — provenance

These bytes come from a **real** Codex CLI rollout written to `~/.codex` on a
darwin/arm64 machine, then lightly redacted (see below). They are NOT synthetic.

## Capture environment
- Codex CLI `cli_version: 0.125.0` (`originator: codex_exec`, `source: exec`).
- Model: `gpt-5.4`, provider `openai`, reasoning effort `low`.
- The capturing run was a non-interactive `codex exec` driven by an external
  harness in a throwaway temp workdir; the rollout lives at
  `~/.codex/sessions/2026/05/15/rollout-2026-05-15T01-11-31-019e28c2-...jsonl`.

## Redactions applied to `REAL/sessions/.../rollout-*.jsonl`
The on-disk bytes were modified ONLY to remove machine-specific / oversized data;
every line type and key is preserved:
- absolute temp `cwd` `/private/var/folders/.../workdir` -> `/workspace/codex-demo`
  (in `session_meta.cwd`, `turn_context.cwd`, and inside the developer/user
  `<environment_context>` text).
- the multi-KB `session_meta.base_instructions.text` blob trimmed to one line
  (the `{"text": ...}` structure is kept).
- the long `<permissions instructions>` / `<skills_instructions>` developer
  boilerplate trimmed to its first ~160 chars.

This real capture is a MINIMAL session: it was cut off after the user prompt and
BEFORE the model responded, so it contains only `session_meta`, `event_msg`
(`task_started`, `user_message`), `turn_context`, and `response_item` (message)
lines — no assistant reply, no tool calls, no `token_count` usage line.

## Why `sessions/` (the test fixture) has extra lines
The adapter test fixture at `../sessions/2026/05/15/rollout-*.jsonl` starts from
these 7 real lines and APPENDS the remaining documented rollout line types that
this particular short capture lacked (assistant `message`, `reasoning`,
`function_call`, `function_call_output`, and a `token_count` usage `event_msg`).
Those appended lines use the EXACT serde wire shapes defined in
`openai/codex` `codex-rs/protocol/src/models.rs` (`ResponseItem`, `ContentItem`,
`ReasoningItemReasoningSummary`) and `.../protocol.rs` (`EventMsg::TokenCount`,
`TokenUsage`, `TokenUsageInfo`), so the test exercises every event-type mapping
against the true format even though one local capture could not.

## Adapter under test
`clawmetry/adapters/codex.py`.
