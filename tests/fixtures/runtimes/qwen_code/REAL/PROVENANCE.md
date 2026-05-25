# Qwen Code REAL capture — provenance

These are **real, unmodified** bytes written by Qwen Code during live agent
sessions driven by a local Ollama model. They are NOT synthetic fixtures.

## Capture environment
- Qwen Code: `@qwen-code/qwen-code` **v0.16.1**, installed via
  `npm install -g @qwen-code/qwen-code` (CLI binary `qwen`). Node v22.22.0.
- Provider: local **Ollama** serving `qwen3:8b` at its OpenAI-compatible
  endpoint `http://localhost:11434/v1`. Routed via the env vars Qwen Code
  reads for OpenAI-compatible providers:
  `OPENAI_API_KEY=ollama`, `OPENAI_BASE_URL=http://localhost:11434/v1`,
  `OPENAI_MODEL=qwen3:8b`. Zero cost, no cloud key.
- Runs invoked with `qwen --chat-recording --approval-mode yolo -m qwen3:8b
  -p "<prompt>"` from `/private/tmp/qwen-real-run`. `--chat-recording` is what
  makes Qwen Code persist the conversation to disk.

## On-disk location
Qwen Code (Gemini-CLI lineage) writes chat recording under a per-project dir:

    ~/.qwen/projects/<project-hash>/chats/<sessionId>.jsonl

`<project-hash>` is the cwd path with `/` -> `-`, here
`-private-tmp-qwen-real-run`. One `.jsonl` per session, one JSON record/line.

## What generated each file
- `chats/e90bc008-...jsonl` — one real turn:
  prompt "Write a one-line Python hello world and explain it briefly."
  -> a `thought` reasoning part + final answer, with real `usageMetadata`
  (16628 prompt / 213 candidate / 16841 total tokens).
- `chats/f9f7f80f-...jsonl` — one real turn:
  prompt "Use a tool to list the files in the current directory, then tell me
  what you found." -> a real `functionCall` to the native `list_directory`
  tool, a `tool_result` record with the `functionResponse`, and a final
  answer. This locks in the real tool-call + tool-result shape.

Both `.jsonl` files here are byte-identical (sha256 verified) to what Qwen
Code wrote to `~/.qwen/projects/-private-tmp-qwen-real-run/chats/`:

    6e493b6f9a355f9ec8e5143b6e0812c1ea431659d44af211991cac4768da0398  e90bc008-...jsonl
    f17481f38138953de4139252a27ddaf41ecfc72c62ac2329700081c168eecf98  f9f7f80f-...jsonl

## Real record shape (one line, pretty-printed)
```json
{
  "uuid": "...",
  "parentUuid": "..." | null,
  "sessionId": "f9f7f80f-...",
  "timestamp": "2026-05-25T20:49:34.214Z",
  "type": "assistant",
  "cwd": "/private/tmp/qwen-real-run",
  "version": "0.16.1",
  "model": "qwen3:8b",
  "message": {
    "role": "model",
    "parts": [
      {"text": "...reasoning...", "thought": true},
      {"functionCall": {"id": "call_t78osgwd", "name": "list_directory",
                        "args": {"path": "/private/tmp/qwen-real-run"}}}
    ]
  },
  "usageMetadata": {"promptTokenCount": 16640, "candidatesTokenCount": 167,
                    "thoughtsTokenCount": 0, "totalTokenCount": 16807,
                    "cachedContentTokenCount": 0}
}
```
- `type`: `user` | `assistant` | `tool_result` | `system`. The assistant role
  on disk is the Gemini `"model"` string (normalised to `assistant`).
- `system` records (`subtype` = `attribution_snapshot` / `ui_telemetry`) are
  control/telemetry, NOT conversation — skipped for events.
- Tool result records have `type:"tool_result"`, `message.role:"user"`, and a
  `functionResponse` part `{id, name, response:{output}}`.
- Tokens ARE present (`usageMetadata`); USD cost is NOT (free local Ollama).
