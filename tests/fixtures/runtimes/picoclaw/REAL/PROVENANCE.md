# PicoClaw REAL capture — provenance

These are **real, unmodified** bytes written by PicoClaw during a live agent
session driven by a local Ollama model. They are NOT synthetic fixtures.

## Capture environment
- PicoClaw: built from source `github.com/sipeed/picoclaw` @ git `ab6d3946`
  (== release v0.2.9), `go build` via `make build` on darwin/arm64, Go 1.26.3.
  (`go install ...@latest` FAILS: the module's go.mod has a `replace`
  directive, so a source build is required.)
- Model: local **Ollama** `llama3.2` served at `http://localhost:11434/v1`
  (config `model_name: "llama3"` -> `model: "llama3.2"`, provider `ollama`).
  Zero cost, no API key.
- PICOCLAW_HOME was set to a throwaway dir inside the worktree
  (`.picoclaw-real/`), so the real `~/.picoclaw` was never touched.

## What generated each file
- `sessions/sk_v1_cb10fea2…jsonl` + `.meta.json` — two real `picoclaw agent -m`
  turns. Turn 1: "Use the exec tool to run `echo hello-from-picoclaw` …" ->
  real `exec` tool call + tool result. Turn 2: "Say hello in one short
  sentence." -> real `message` tool call + tool result. 8 messages total.
  Both turns hashed to the same session key (chat dimension).
- `cron/cron jobs.json` — one real `picoclaw cron add -n daily-echo -c "0 9 * * *"`.

The session `.jsonl` here is byte-identical (sha256 verified) to what PicoClaw
wrote to `.picoclaw-real/workspace/sessions/`.

## Adapter under test
`picoclaw_adapter_under_test.py` is `clawmetry/adapters/picoclaw.py` from branch
`feat/nanoclaw-picoclaw-real-adapters`, copied for reference. See the agent
report for the full divergence list and required fixes.
