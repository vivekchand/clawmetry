# ChatGPT desktop coverage

ClawMetry observes **local ChatGPT Work tasks and Codex sessions** through their shared native runtime. Choose **Codex / ChatGPT Work** in the runtime selector. Both use the existing `codex` runtime identity, so a session is collected once and existing history stays under the same filter.

## What is observed

For tasks with a readable native rollout on the same machine, ClawMetry reads recorded user messages, assistant replies, tool calls and results, readable reasoning, model identifiers and token usage. A published-rate usage estimate is not a ChatGPT subscription bill. Encrypted reasoning or missing usage remains unavailable.

The adapter automatically uses `CODEX_HOME`, defaulting to `~/.codex`. Native thread indexes supply recent rollout paths and desktop titles; active and archived rollout directories remain a fallback. ClawMetry copies the native database and its WAL to a private temporary directory, checks that the source did not change during copying, then queries that copy. It never opens the original with SQLite or creates native lock files. Copies are limited to 64 MiB and two attempts. A changing source, rollback journal, large index or unsupported schema falls back to rollout discovery with a warning.

Recent tasks are selected by recorded activity rather than file modification time, so restoring an old file does not make it displace a resumed task. Bounded caches survive daemon polling and are isolated by native home. Native title changes refresh the stored session without counting its transcript or usage twice.

Local Work and Codex currently share native threads without a dependable per-thread mode marker. ClawMetry therefore does not guess which experience launched a historical thread from its model, directory or current composer setting.

## Coverage limits

**Regular Chat and cloud Work conversations are not monitored by this integration.** The desktop catalogue caches titles and timestamps, but those do not provide messages, tools, models, tokens or current execution state. The current app caches hosted transcripts in encrypted browser storage; this adapter does not decrypt that cache or collect authentication credentials.

The reader follows the upstream home-directory convention and `CODEX_HOME`. Native storage was inspected on macOS. Windows desktop verification remains pending. A Linux Codex installation can use the same reader, but that does not imply an official ChatGPT desktop application for Linux.

Cloud ClawMetry views consume the same daemon-ingested records through the existing encrypted sync. Opening a hosted-only ChatGPT conversation on the desktop does not make its transcript local or observable.

## Delivery status

This document describes a candidate implementation. Released availability requires the paired Pro wheel, OSS release, licensed delivery and served local/hosted verification. A code change or support label alone is not proof of complete ChatGPT desktop support.

Primary references: [ChatGPT experiences](https://learn.chatgpt.com/docs/use-chatgpt), [local Work data boundaries](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security), and [OpenAI's native protocol](https://github.com/openai/codex/blob/main/codex-rs/protocol/src/protocol.rs). Native-storage research used desktop version 26.915.31945 on macOS; Windows live verification remains pending.
